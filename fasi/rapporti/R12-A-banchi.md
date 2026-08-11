# R12-A — Il banco come strumento

*Revisione avversariale della notte del 10-11 agosto 2026, **lente A** del
`fasi/rapporti/MANDATO-10-agosto-notte.md`. Bersaglio: `01-b6-*`, `01-b8-*`, `01-b9-letture.py`,
`01-b12-*`, `01-b13-*`, `01-c2-*`, `01-s*`, `web/rapporti/S-esiti-sonda.md`.*

⛔ **Ho ricevuto il codice e la specifica, non il ragionamento di chi li ha scritti**: non ho chiesto
niente a nessuno (`PIANO.md` §0.4). Non ho riscritto una riga; le uniche esecuzioni sono in sola
lettura o su copie in una cartella temporanea, e sono marcate `[M]`.

**30 rilievi** (A1-A30): 15 `[R]`, 11 `[?]`, 4 `[M]`. La sezione §7 dice che cosa ho provato a
rompere senza riuscirci.

---

## 0. La risposta alla domanda che vale doppio

> *«Guarda `banchi/01-b12-registro.jsonl` e verifica se quel che dichiara certificato lo è davvero,
> e se quel che dichiara non certificato è dichiarato con quelle parole o arrotondato.»*

Il registro ha due righe, e la **seconda in ordine di scrittura è la più vecchia** (23:01 sta sopra
21:19):

| ora | certificati | non certificati | mai provati |
|---|---|---|---|
| 23:01:46 | **B4, B9** | *(nessuno)* | B10 B11 **B13** B2 B3 B5 B6 **B7** B8 **C2** |
| 21:19:09 | **B7, C2** | **B13, B4** | B10 B11 B2 B3 B5 B6 B8 B9 |

Le due righe hanno **la stessa `impronta_rcp_c`**, cioè parlano dello stesso codice. Quindi:

- **quattro banchi sono dichiarati certificati** (B4, B9, B7, C2), e **due delle quattro
  certificazioni non valgono quel che la parola dice**: B4 è certificato **senza marca** (A3), B7 ha
  una marca che compare **anche nel giro sano** (A3);
- **quel che è non certificato è arrotondato**, e nella direzione che nasconde: B13, che alle 21:19
  era **`non_certificati`** — cioè *provato e non riuscito* — alle 23:01 è **`mai_provati`**. E B7 e
  C2, certificati alle 21:19, alle 23:01 sono **`mai_provati`**. La parola *«mai»* è **falsa**: sono
  stati provati due ore prima, sullo stesso `rcp.c` (A4);
- e **B13 non può essere certificato affatto** da questo orchestratore: il suo guasto è di tipo
  `riga-di-comando`, e `--applica` rifiuta i guasti che non hanno un appiglio. `[M]`, verificato
  eseguendolo (A1). Il ramo `B13)` di `gira()` che accende il server con `pagina.pem` è **codice
  morto**.
- Anche se ci arrivasse, **il guasto di B13 non è quello giusto**: costruisce un difetto che
  `B13.1` non guarda (A2).

⛔ **Il conto vero, oggi**: dei dodici banchi del catalogo, **due** hanno una certificazione che
regge la propria definizione (**B9** e **C2**) — e su B9 vedi A8, che ne restringe ulteriormente il
significato.

---

## 1. B12 — il banco che certifica gli altri

```
DOVE:              banchi/01-b12-guasti.py:490-496 (applica) + 456-462 (verifica)
                   banchi/01-b12-lancia.sh:84, 196-205, 299-306
COSA CONTRADDICE:  fasi/01-filo-nudo.md B12-C1 («un guasto costruito a mano PER OGNI BANCO»)
                   e il commento di 01-b12-lancia.sh:13-25 («il giro è tre esecuzioni»)
COME SI DIMOSTRA:  `python3 01-b12-guasti.py --applica B13`
                     →  «NO  «B13»: l'appiglio non e' unico — il guasto NON si innesta»
                        «[?] «B13» non ha un appiglio: e' un guasto di tipo «riga-di-comando»»
                        uscita 1
                   `applica()` non guarda `g["costa"]`: chiama `verifica()`, che per i tipi
                   `riga-di-comando` e `gia-fatto` esce SUBITO con 0, e `0 != 1` porta al ramo
                   «l'appiglio non e' unico».  In `01-b12-lancia.sh:301` l'uscita ≠ 0 fa
                   `continue`: i passi 2/3 e 3/3 di B13 NON si eseguono mai.  B13 è nella lista
                   predefinita `leggeri` (riga 84), e il ramo `B13)` di `gira()` che commuta
                   `base=pagina` quando `passo=guasto` (righe 196-199) non è raggiungibile.
MARCA:             [M]
```
**A1**

```
DOVE:              banchi/01-b12-guasti.py:326-352 (il guasto B13) contro
                   banchi/01-b13-proprieta.py:215-238 (proprieta_1)
COSA CONTRADDICE:  REVIEWER.md §1 domanda 2 e il MANDATO §4.2 — «il guasto era QUELLO GIUSTO,
                   cioè avrebbe prodotto il difetto che il banco cerca?»
COME SI DIMOSTRA:  il guasto è «si accende il server con `pagina.pem` al posto di `sessione.pem`»,
                   e la marca pretesa è «LE IMPRONTE COMBACIANO».  Ma `proprieta_1` legge le
                   impronte dei DUE FILE su disco (`impronta_der(pagina.pem)` e
                   `impronta_der(sessione.pem)`), non quel che il server presenta sul filo:
                   cambiare la riga di comando **non tocca nessuno dei due file**, quindi
                   `imp_p == imp_s` resta falso e la stringa «LE IMPRONTE COMBACIANO» non viene
                   mai stampata.  A vedere quel guasto è `proprieta_3` («il certificato PRESENTATO
                   sul filo non è sessione.pem»), che è un'altra proprietà e un altro difetto.
                   Conseguenza: anche innestandolo a mano, `giudica()` scriverebbe «il banco è
                   rosso ma la sua uscita non nomina «LE IMPRONTE COMBACIANO»» — cioè
                   NON CERTIFICATO su un guasto che ha funzionato.
                   ⛔ E il difetto che B13.1 esiste per trovare — «un server che genera UN
                   certificato solo a scadenza breve» — resta senza guasto: si costruirebbe
                   copiando `sessione.pem` su `pagina.pem`, non cambiando la riga di comando.
MARCA:             [R]
```
**A2**

```
DOVE:              banchi/01-b12-guasti.py:104, 122-135, 596-600 (il criterio della marca)
COSA CONTRADDICE:  01-b12-guasti.py:29-38 trappola 1 («ogni guasto dichiara la MARCA … e senza
                   quella marca la certificazione NON vale»), e la nota del guasto C2
                   (righe 374-378): «una marca che compare in tutt'e due i giri non è una marca,
                   è un modo di certificare senza guardare»
COME SI DIMOSTRA:  `for s in …; do python3 01-b12-guasti.py --marca $s; done` dà, sui dodici:
                     · SENZA marca (campo vuoto)             B3 B4 B5 B8 B10 B11   → 6
                     · marca che compare ANCHE nel giro sano B2 B6 B7              → 3
                     · marca che il banco non può produrre   B13                   → 1
                     · marca discriminante                   B9 C2                 → 2
                   B6: marca «ciao-presto», che è il NOME DI UN CASO e `01-b6-tetti.py:1177`
                   lo stampa con `riga(ok, c["nome"], …)` a ogni giro, sano compreso.
                   B7: marca «CONGEDO», e `01-b7-congedo.py` nomina `CONGEDO` 37 volte: è il
                   soggetto del banco.  B2: «initial_max_streams_uni», che la sonda del trasporto
                   stampa sempre.
                   ⛔ E `giudica()` verifica solo `rotto["marca_vista"]`: **non verifica mai che il
                   giro SANO non la dicesse già**.  La seconda metà del criterio esiste, scritta
                   la stessa notte, in `01-b8-cronometro.py:1571`
                   (`gia = frase in testo_sano` … «⛔ ma il giro SANO lo diceva gia': non prova
                   niente»).  Due mani, due criteri, e quello più debole è nel banco che
                   certifica gli altri undici.
                   Caso concreto: B7 col guasto innestato è rosso per una compilazione fallita —
                   la trappola 1 che B12 dichiara di chiudere — e `marca_vista` sarebbe `true`
                   lo stesso, perché `tail -25` dell'uscita di B7 contiene «CONGEDO».
MARCA:             [R]
```
**A3**

```
DOVE:              banchi/01-b12-guasti.py:630-643 (il campo `mai_provati`) e 666-678
                   (`mostra_registro`) · banchi/01-b12-registro.jsonl
COSA CONTRADDICE:  01-b12-guasti.py:61-64 («la certificazione si scrive su file, con la data …
                   un banco certificato tre giorni fa su un codice che nel frattempo è cambiato
                   non è certificato oggi») e LEZIONI.md §1.9 regola 4 (il denominatore dichiarato)
COME SI DIMOSTRA:  `mai = sorted(set(GUASTI) - set(per_sigla))` è **per giro**, e la stampa lo dice
                   («banchi MAI PROVATI in questo giro»); il campo scritto nel JSON si chiama
                   `mai_provati` senza il «in questo giro», e `mostra_registro` lo ristampa come
                   «mai provati».  Nel file: alle 21:19 C2 e B7 sono `certificati`, alle 23:01
                   sono `mai_provati` — con la stessa `impronta_rcp_c`.  Chi legge l'ultima riga,
                   che è quel che fa chiunque legga un registro, conclude che C2 e B7 non sono
                   mai stati provati.
                   ⛔ E l'arrotondamento peggiore è B13: `non_certificati` alle 21:19 →
                   `mai_provati` alle 23:01.  «Provato e non riuscito» e «mai provato» hanno due
                   cure diverse, e il registro le fonde nella più innocente.
MARCA:             [M]
```
**A4**

```
DOVE:              banchi/01-b12-guasti.py:636-642
COSA CONTRADDICE:  LEZIONI.md §1.9 corollario 5 («un denominatore si legge dove la cosa succede»)
COME SI DIMOSTRA:  il registro annota `impronta_rcp_c` = sha256 di `banchi/rcp/rcp.c`.  Ma i tre
                   guasti «leggeri» — gli unici che sono stati eseguiti — si innestano su
                   `01-b12-copie/01-b4-validatore.py` (B4), `01-b12-copie/01-b3-cliente.py` (B9),
                   `01-b12-copie/01-c2-diagnosi.py` (C2), e i banchi che devono diventare rossi
                   sono `01-b4-lancia.py`, `01-b9-letture.py`, `01-c2-diagnosi.py`.
                   **Nessuno di questi file entra nell'impronta.**  `rcp.c` non partecipa alla
                   certificazione di B4 e di B9 in nessun modo.
                   Caso concreto: domani si riscrive `01-b4-validatore.py` da capo e non si tocca
                   `rcp.c`; il registro continua a dire «B4 certificato, impronta d839839f…» e la
                   riga resta valida a vista, mentre il banco certificato non esiste più.
                   L'impronta è un denominatore che promette una cosa e ne misura un'altra: è
                   **peggio di nessuna impronta**, perché dà alla riga l'aria di essere già stata
                   controllata.
MARCA:             [R]
```
**A5**

```
DOVE:              banchi/01-b12-lancia.sh:155-166 (`ripulisci`) contro il commento alle
                   righe 53-54
COSA CONTRADDICE:  il commento del file stesso — «il guasto si toglie anche se il giro muore: il
                   `trap` lo rimette a posto **e ricostruisce**» — e la trappola 3 di
                   01-b12-guasti.py:39-42 («il guasto che sopravvive … avvelena ogni misura
                   successiva, e nessuno saprà che c'era»)
COME SI DIMOSTRA:  `ripulisci()` fa `spegni` e `--togli`, e **non chiama mai `ricostruisci`**.  La
                   ricostruzione c'è solo nel cammino normale (righe 309-311 e 323-325).
                   Caso concreto: `bash 01-b12-lancia.sh tutti`, Ctrl-C durante il passo 2/3 di
                   B7 (che è `costa=ricostruisce`).  Il `trap` rimette a posto `examples/rcp.c` e
                   lascia `build/examples/bsslserver` **compilato col `CONGEDO` tolto**.  Il
                   banco successivo legge un sorgente sano — B6 riga 219-249 confronta proprio i
                   `#define` fra sorgente e copia compilata, e li trova d'accordo — e misura un
                   server che mente.  ⛔ È il caso che il commento in cima promette di coprire.
MARCA:             [R]
```
**A6**

```
DOVE:              banchi/01-b12-lancia.sh:271 · 01-c2-lancia.sh:93,94,156,174,175 ·
                   01-b6-lancia.sh:274 · 01-b13-lancia.sh:111,122
COSA CONTRADDICE:  il rilievo R8.15 (già `[R]`, già curato in casa) e LEZIONI.md §1.9 regole 1 e 2
COME SI DIMOSTRA:  `CHI=$(bash "$ENTRA" --root "ss -ulnp | grep ':$PORTA '")` — «porta libera» e
                   «il comando non è stato eseguito» sono **la stessa stringa vuota**.  E la cura
                   è già scritta, in questa stessa cartella, da una revisione precedente:
                   `01-b11-guasto.sh:92-129` ha `dentro()` (che si fa stampare lo stato d'uscita
                   dal comando remoto, «B11-FINE=%s») e `chi_tiene_la_porta()` col **controllo
                   positivo dello strumento** («`ss -ulnp` stampa sempre almeno la propria
                   intestazione: se non stampa niente non ha guardato niente»), con tre esiti —
                   occupata · libera · **non si sa** — e la riga «non si sa non si arrotonda a
                   libera».  Quattro banchi nuovi riscrivono la forma non curata.
                   ⛔ E in `01-b12-lancia.sh` la riga 271 è **una sostituzione di comando attorno a
                   `enter.sh`**, cioè esattamente la trappola che lo stesso file descrive venticinque
                   righe più su (236-247: «il giro delle 22:50 si è fermato esattamente lì, subito
                   dopo aver innestato il guasto — cioè col guasto addosso al codice»).
                   ⛔ E in `01-c2-lancia.sh:174-175` la forma cieca sta nella **ripulitura finale**,
                   che è l'unica cosa che impedisce a C2 di lasciare due prese sulla 7447 addosso
                   al banco successivo: se `ss` non risponde, C2 stampa «la porta è tornata libera»
                   e esce 0.
MARCA:             [R]
```
**A7**

```
DOVE:              banchi/01-b12-guasti.py:264-288 (il guasto B9) contro
                   banchi/01-b9-letture.py:68-81 e la voce L4 (righe 321-358)
COSA CONTRADDICE:  fasi/01-filo-nudo.md B12-C1 («B9 — il cliente di prova che ha letto il C») e
                   REVIEWER.md §2 E2 (due misure diverse sotto la stessa etichetta)
COME SI DIMOSTRA:  ho rifatto in `…/scratchpad/b9/` l'albero minimo (RCP.md + i due file) e:
                     1. sano                                              → uscita **0**, 12 su 12
                     2. cliente cambiato alla **lettura A** — la coda in più si TAGLIA — MA
                        lasciando **intatta, riga per riga, la stringa che L4 cita**
                        (`corpo = bytes(self.arrivati[6:6 + lung])`) e aggiungendo il troncamento
                        nelle righe successive                            → uscita **0**, 12 su 12
                   e la voce L4 continua a stampare «⭐ SCELTO … il cliente di prova legge
                   `lunghezza` byte e passa il corpo così com'è … (lettura B, tollerante)»,
                   che a quel punto è **falso**.
                   ⛔ Quindi il guasto di B12 diventa rosso perché **cancella una citazione**, non
                   perché il secondo lettore si è allineato al primo: la certificazione di B9
                   dimostra che B9 sa vedere *un testo cambiato*, che è la cosa che B9 dichiara
                   apertamente di saper fare (riga 45-46), e **non** quel che il catalogo di B12
                   scrive di aver certificato.
MARCA:             [M]
```
**A8**

---

## 2. C2 — le tre diagnosi

```
DOVE:              banchi/01-c2-diagnosi.py:469-479
COSA CONTRADDICE:  B0.1 («ogni banco dichiara e VERIFICA il proprio stato iniziale») e B0.4
                   («l'atteso lo confronta il banco, non chi legge»)
COME SI DIMOSTRA:  la fase `senza-server` misura `tcp0`, `udp0` e `completa0`, li **stampa tutti e
                   tre** e ne confronta **uno solo** (`if completa0: return 5`).  Ma il dato che
                   dice «c'è ancora qualcuno legato alla porta UDP» è `udp0`: a server spento la
                   sonda UDP deve ricevere l'ICMP «porta irraggiungibile», cioè `"rifiutato"`; se
                   torna `"silenzio"` **qualcuno tiene ancora quella presa**.
                   Caso concreto: il server è stato ucciso ma non è ancora uscito (`01-c2-lancia.sh`
                   aspetta il processo, ma la fase python può essere lanciata da sola, ed è così
                   che B12 la usa).  La stretta QUIC non si completa → `completa0` falso →
                   «OK nessuno parla QUIC (TCP «rifiutato», UDP «silenzio»)» → si aprono le prese
                   della scena 2 su una porta già tenuta.  La riga che l'avrebbe detto è stampata
                   sullo schermo.
MARCA:             [R]
```
**A9**

```
DOVE:              banchi/01-c2-diagnosi.py:315-317 (`ScenaUdpFiltrato.__enter__`)
COSA CONTRADDICE:  il commento del file stesso, righe 86-89: «due cose in ascolto sulla stessa
                   porta darebbero una scena che non è nessuna delle quattro»
COME SI DIMOSTRA:  `self.udp.setsockopt(SO_REUSEADDR, 1)` prima del `bind`.  Su Linux, due prese
                   UDP che dichiarano entrambe `SO_REUSEADDR` **possono legarsi allo stesso
                   indirizzo:porta**, e i pacchetti vanno all'una o all'altra.  Cioè l'opzione
                   toglie l'unico meccanismo che avrebbe fatto fallire il `bind` quando lo stato
                   iniziale non è quello dichiarato — e il fallimento del `bind` sarebbe stato il
                   testimone che A9 non chiede.  Su una presa che non deve essere riavviata in
                   fretta, `SO_REUSEADDR` non serve a niente e costa quella difesa.
MARCA:             [?]
```
**A10**

```
DOVE:              banchi/01-c2-lancia.sh:131-135
COSA CONTRADDICE:  B0.5 e il commento del file stesso alle righe 33-39
COME SI DIMOSTRA:  se la fase `con-server` esce ≠ 0, lo script fa `kill $PID` e **esce subito**,
                   senza aspettare che il processo muoia e senza controllare che la porta si sia
                   liberata — mentre il cammino normale (righe 139-162) lo fa con cura.  Il banco
                   successivo trova la 7447 occupata e, per A7, potrebbe non vederlo.
MARCA:             [?]
```
**A11**

---

## 3. B13 — le sei proprietà

```
DOVE:              banchi/01-b13-proprieta.py:439-460 e 466-474 (proprieta_3)
COSA CONTRADDICE:  il commento del file stesso, righe 46-65 («la proprietà che non si può misurare
                   va DETTA, non saltata … si segnano `[?] non misurabile — manca l'imputato»)
COME SI DIMOSTRA:  la logica è invertita rispetto a quel che dichiara:
                     · se **non** si trova nessun generatore → `aperti` cresce → esito
                       `SENZA_IMPUTATO` (giallo, giusto);
                     · se **si trova** un generatore → si stampa solo «⚠ c'è un imputato, e va
                       guardato», `aperti` resta vuoto → e se non ci sono altri guasti l'esito è
                       **`PASSA`**, con il testo «permessi, nome e certificato presentato: tutto
                       al suo posto».
                   Cioè: più prove ci sono che qualcuno genera certificati, più la proprietà è
                   verde.  Oggi la ricerca non trova niente (`grep -nEi "x509|genera.*certificat|
                   newkey|req -"` su `rcp/rcp.c`, `01-b3-rcp-innesta.py`,
                   `01-b2-ngtcp2-wt-innesta.py` dà **0 righe su tutti e tre**, `[M]`), quindi il
                   difetto non morde ancora — morde il giorno in cui il server imparerà a
                   generarsi il certificato, che è precisamente il giorno in cui §4.1 comincia a
                   voler dire qualcosa.
MARCA:             [R]
```
**A12**

```
DOVE:              banchi/01-b13-proprieta.py:322-325
COSA CONTRADDICE:  LEZIONI.md §1.9 regola 1 e il commento del file, righe 30-44 («un `grep`
                   puntato sulla cartella sbagliata, un file mai aperto … danno la stessa faccia
                   di una proprietà rispettata, e danno verde»)
COME SI DIMOSTRA:  `u, t = corri(["grep", "-rl", …])` e poi **`u` non viene mai guardato**.  `grep`
                   esce **2** quando non ha potuto leggere qualcosa, e `corri()` fonde stdout e
                   stderr in una stringa sola; le righe «grep: …: Permission denied» sono poi
                   scartate da `os.path.isfile(r)`.  Il denominatore stampato — `quanti_file`,
                   contato con `os.walk` — **conta anche i file che il `grep` non ha potuto
                   leggere**, e li presenta come guardati.
                   Caso concreto: sotto `/srv/src` compare un registro `0600` di un altro utente
                   con dentro la parola d'ordine.  `grep` non lo apre, esce 2, la riga di errore
                   sparisce, `colpiti` è vuoto → «la parola non compare in nessuno dei N registri
                   e registrazioni, e il `grep` sa trovarla quando c'è».  Il controllo positivo
                   c'è ed è buono, ma certifica che il `grep` **sa trovare**, non che **abbia
                   potuto leggere tutto**.
MARCA:             [R]
```
**A13**

```
DOVE:              banchi/01-b13-lancia.sh:120-128
COSA CONTRADDICE:  B0.1 (dichiara **e verifica**) e B0.4, e il commento della riga 120-121 del
                   file stesso: «se qualcuno ascoltasse già in TCP su 7447, la proprietà 4 lo
                   prenderebbe per il nostro server»
COME SI DIMOSTRA:  lo script scrive la diagnosi giusta e poi, nel ramo «c'è qualcuno», usa `inf`
                   (una nota) invece di `ko`+`exit`: **il giro prosegue**.  La proprietà 4
                   (`01-b13-proprieta.py:486-565`) apre una connessione TCP a `192.168.0.2:7447`,
                   chiede `GET /` e, se un altro processo risponde, stampa «la pagina si carica:
                   stato 200, N byte» e poi giudica se contiene l'impronta corrente.  Il rosso o
                   il verde che ne esce **parla del server di un altro banco**.  Il caso è
                   nominato e non fermato: è la forma «l'indulgenza che nasconde» di REVIEWER.md
                   §5.
MARCA:             [R]
```
**A14**

```
DOVE:              banchi/01-b13-proprieta.py:658-673 e 694-713 (proprieta_5)
COSA CONTRADDICE:  LEZIONI.md §1.11 regola 1 («per ogni prova indiretta si scrive cosa mostrerebbe
                   il caso opposto») e LEZIONI.md §2.3 (una prova che boccia il codice giusto)
COME SI DIMOSTRA:  la prova «aprirne sedici» gira **dopo** che aioquic ha già aperto i propri
                   stream unidirezionali di HTTP/3 (controllo + i due di QPACK: tre), che
                   consumano lo stesso credito.  Con un server che concede esattamente 16 — cioè
                   quel che l'innesto di B2 mette (`params.initial_max_streams_uni = 16`) — il
                   client può aprirne al massimo 13, e il banco stampa «⛔ il parametro iniziale
                   dice 16 ma se ne aprono solo 13», cioè **un rosso su un server conforme alla
                   riga che sta misurando**.
                   ⚠ E il ramo opposto è altrettanto cieco: se `create_webtransport_stream()` non
                   solleva niente oltre il limite (si limita ad allocare un identificatore),
                   `aperti` vale 16 sempre e il controllo non può dire *no* in nessun caso.  Non
                   so quale dei due sia — e **è questo il punto**: il file non dichiara che cosa
                   mostrerebbe il caso opposto, e senza quella riga il numero «16 su 16» non
                   distingue le due situazioni.
MARCA:             [?]
```
**A15**

```
DOVE:              banchi/01-b13-lancia.sh:98-105
COSA CONTRADDICE:  LEZIONI.md §1.9 ottava veste («il file c'è» e «il file è quello che ho appena
                   costruito» sono due domande diverse) — e `01-b6-lancia.sh:198-249`, che nella
                   stessa notte pone la domanda forte
COME SI DIMOSTRA:  B13 verifica `[ "$FUORI/rcp/rcp.c" -nt "$SERVER_FUORI" ]`, cioè **le date**.
                   B6 invece legge i `#define` **da tutti e due** i file — `rcp/rcp.c` e la copia
                   compilata `b2/ngtcp2/examples/rcp.c` — e pretende che combacino, «perché una
                   copia stantia darebbe un numero che nel binario non c'è».
                   Caso concreto: si esegue `01-b3-rcp-innesta.py --togli` (cosa che
                   `01-b6-lancia.sh:170` e `01-b8-lancia.sh:112` fanno a ogni giro) e poi si
                   ricompila.  Il binario è **più nuovo** di `rcp/rcp.c` e non contiene una riga
                   di `rcp/rcp.c`.  B13 dice «il binario è più nuovo del sorgente» e la
                   proprietà 6 confronta un sorgente che il server non esegue.  Due banchi della
                   stessa notte rispondono alla stessa domanda con due forze diverse.
MARCA:             [?]
```
**A16**

```
DOVE:              banchi/01-b13-proprieta.py:744-762 (proprieta_6, seconda metà)
COSA CONTRADDICE:  LEZIONI.md §1.9 regola 2 (il controllo positivo dev'essere sullo STESSO tipo di
                   cosa che si cerca)
COME SI DIMOSTRA:  la conclusione è «nel codice il ramo RIPRESA non esiste», e la prova è
                   `"RIPRESA" in r` riga per riga.  Il controllo positivo verifica che nel file
                   compaia la parola «SESSIONE» — cioè che il file sia leggibile e sia quello
                   giusto — non che una **diramazione** si possa trovare cercandone il nome.
                   Caso concreto: `corpo[0] = ripresa_possibile ? 2 : 1;` non contiene la stringa
                   `RIPRESA`, e B13.6 stampa «nessuna riga di rcp.c nomina RIPRESA … il ramo
                   RIPRESA non esiste».  L'unica cosa che fa diventare rossa questa metà è che
                   qualcuno abbia scritto **la parola**.
MARCA:             [?]
```
**A17**

---

## 4. B8 — il secondo fisso e il ban

*Premessa: è il file più curato del lotto — il modello di §4.4-bis verificato prima di eseguire il
piano, la terza guardia sul filo, il seme fisso del bootstrap, i cinque esiti separati. I rilievi
che seguono non lo contraddicono in blocco: colpiscono i punti in cui il verdetto dice più di quel
che ha misurato.*

```
DOVE:              banchi/01-b8-cronometro.py:1355-1375 (il ramo `guasti_mediane`)
COSA CONTRADDICE:  REVIEWER.md §2 E5 («un fatto che era una deduzione mai misurata») e
                   LEZIONI.md §1.9 settima veste (il rosso puntato sull'imputato sbagliato)
COME SI DIMOSTRA:  quando una coppia di mediane si separa e non è quella del segreto, il verdetto
                   stampa **sempre** «⛔ A governare i tempi è **PAM** — `pam_faildelay` ritarda i
                   FALLIMENTI e non i successi — e la cura sta in `banchi/rcp/autenticazione.c` e
                   nella pila PAM, non in `rcp.c`».  L'attribuzione è **nel testo**, non nel dato:
                   il numero che dovrebbe sostenerla (`pam`, la mediana dei respinti nel registro
                   del server) è calcolato due righe prima e **non condiziona niente**; se il
                   registro non si legge, `pam` vale `None` e la frase stampata diventa «dopo una
                   mediana di None ms … A governare i tempi è PAM».
                   Caso concreto: domani qualcuno aggiunge nel percorso dell'`AMMESSO` un lavoro
                   che costa due secondi (un `getpwnam` lento, una scrittura sincrona).  La coppia
                   `sbagliata − giusta` si separa **per colpa nostra**, B8 esce 5, e consegna al
                   lettore la diagnosi «è PAM, la cura sta altrove».  È il rosso mandato a
                   cercare dove non c'è niente.
MARCA:             [R]
```
**A18**

```
DOVE:              banchi/01-b8-lancia.sh:371-379 e 403-408 · banchi/01-b8-cronometro.py:1520-1600
COSA CONTRADDICE:  LEZIONI.md §1.2 e il senso della parola «certificato» usata in
                   banchi/01-b12-guasti.py:48-59
COME SI DIMOSTRA:  `--certifica` guasta **i fatti già registrati** e verifica che `verdetto()`
                   diventi rosso: è una prova di mutazione sul **giudice**, ed è dichiarata come
                   tale nel file (riga 1367-1370, «si guasta quel che il giro ha appena
                   prodotto»).  Ma `01-b8-lancia.sh:406` la traduce in «⛔ …ma il banco NON è
                   certificato», e simmetricamente quando passa nessuno dice che cosa **non** è
                   stato certificato.
                   Caso concreto: si sposta `t0 = time.perf_counter()` di `un_tentativo` (riga
                   305) **dopo** `await b3.attendi(...)` invece che prima di `cli.manda(...)`.
                   Tutti i millisecondi registrati diventano ~0, il primo criterio («nessuna
                   risposta prima di 1000 ms») diventa rosso — ma se invece lo si spostasse in un
                   punto che tiene i numeri plausibili (per esempio includendo la stretta di mano
                   QUIC), **nessuno dei tredici guasti se ne accorgerebbe**, perché tutti e
                   tredici lavorano sui numeri già scritti.  Il guasto che coprirebbe
                   l'acquisizione — togliere `RITARDO_CREDENZIALI` dal server — sta nel catalogo
                   di B12 ed è **catalogato e non eseguito**.  Le due cose vanno dette insieme,
                   e stanno in due file di due mani diverse.
MARCA:             [?]
```
**A19**

```
DOVE:              banchi/01-b8-prova-ban.c:37-51 e 253-255
COSA CONTRADDICE:  il commento del file stesso alle righe 45-47 («Il denominatore di ogni sezione
                   si stampa: quanti controlli, e su che cosa.  Un elenco di OK senza il numero
                   di quel che ha guardato non è una misura, `LEZIONI.md` §1.9 regola 4») e
                   LEZIONI.md §1.9 regola 6 («anche un verdetto ha un denominatore, ed è quante
                   cose ha approvato, e se è zero non si dà nessun esito»)
COME SI DIMOSTRA:  `sezione()` stampa **solo il titolo**; `esige()` conta i falliti e **non conta i
                   passati**; il verdetto finale è `printf("\n  %s: %d controlli falliti", …)` —
                   zero denominatore.
                   Caso concreto: si mette un `return 0;` dopo la sezione 1 (o una `#if 0` attorno
                   alle sezioni 2-4, o si sbaglia un `#include` che fa saltare un blocco).
                   L'uscita finisce con «VERDE: 0 controlli falliti» e uscita 0.  È il verde su
                   insieme vuoto, dentro il file che certifica il ban.
                   ⚠ E in più: `grep -rn "01-b8-prova-ban"` su tutto l'albero non trova **nessun
                   chiamante** — né `01-b8-lancia.sh` né B12 lo eseguono.  È una certificazione che
                   nessuno esegue, quindi non è una certificazione (`[M]`).
MARCA:             [R]
```
**A20**

```
DOVE:              banchi/01-b8-lancia.sh:237-243
COSA CONTRADDICE:  il commento immediatamente sopra («si guarda che cosa ha DETTO all'avvio sul
                   ban: «zero ban» e «non ho potuto leggere il file» sono due fatti diversi, e la
                   riga che li distingue è l'unica prova che la persistenza è accesa») e B0.4
COME SI DIMOSTRA:  la riga è `grep -E "ban caricati|…" "$FUORI/b2-wt.log" | sed 's/^/        /'` —
                   si **stampa** e non si confronta niente, e se il registro non esiste `grep`
                   scrive su stderr e lo script prosegue senza una parola.  Le due cose che il
                   commento dichiara di distinguere restano indistinte proprio lì.
                   ⚠ Il verdetto poi legge il registro (`leggi_registro`) e controlla `carichi` e
                   `illeggibili`, quindi il difetto non passa; ma l'accensione dichiara di aver
                   fatto un controllo che non fa, e chi legge il giro dal vivo crede a quella riga.
MARCA:             [R]
```
**A21**

```
DOVE:              banchi/01-b8-sblocca.py:163-166 e banchi/01-b8-cronometro.py:466-471 (`simula`)
COSA CONTRADDICE:  REVIEWER.md §2 E5
COME SI DIMOSTRA:  su `NON-BANNATO` il comando stampa «⚠ e il conto dei tentativi di
                   quell'indirizzo riparte comunque da zero», e `simula()` modella lo sblocco come
                   `falliti[ind] = 0` **sempre**.  Nessuno dei due lo verifica, e su quel
                   comportamento poggia l'intera strategia dei campioni («sbloccare fra un blocco
                   e l'altro»): se `rcp_sblocca()` azzerasse la voce **solo quando un ban c'è**, i
                   fallimenti si accumulerebbero fra blocchi.  Il banco se ne accorgerebbe (i
                   campioni tornerebbero `limitatore`), ma la frase resta un fatto scritto senza
                   misura, in un file che è «lo strumento di B0.3» per tutti gli altri banchi.
MARCA:             [?]
```
**A22**

---

## 5. B6 — i tre tetti

*Anche qui: il controllo del tetto del trasporto letto dal pari, il confronto documento/codice/filo
a tre voci, i tre casi `-presto`, i tre esiti separati e il B0.5 dopo ogni caso sono la cosa meglio
costruita del lotto. Restano tre punti.*

```
DOVE:              banchi/01-b6-lancia.sh:274
COSA CONTRADDICE:  R8.15 — vedi A7, che vale identico qui
COME SI DIMOSTRA:  vedi A7.  ⚠ Aggravante: B6 è l'unico dei quattro a **non** ricontrollare la
                   porta fra le due fasi (`spegni()` alle righe 306-311 manda il `kill` e non
                   aspetta nessuno), quindi la lettura della riga 274 è l'unica che esista, e
                   avviene una volta sola all'inizio.
MARCA:             [R]
```
**A23**

```
DOVE:              banchi/01-b6-lancia.sh:306-311 (`spegni`) contro 01-c2-lancia.sh:139-155
COSA CONTRADDICE:  LEZIONI.md §2.3-ter («un banco che rifà lo stesso ambiente due volte fallisce
                   la seconda») e, di nuovo, due mani sullo stesso problema
COME SI DIMOSTRA:  `spegni()` fa `kill` e azzera `PID` **subito**; `fase ping` chiama `accendi`
                   pochi millisecondi dopo, sulla stessa porta.  C2, nella stessa notte, aspetta
                   la sparizione del processo con un ciclo su `/proc/$PID` **e** verifica con `ss`
                   che la porta si sia liberata, e scrive perché: «fra la morte del processo e il
                   rilascio della porta passa un istante che, se non si aspetta, fa misurare alla
                   scena 1 una porta ancora tenuta».  Il sintomo qui sarebbe «il server non è
                   partito» all'inizio della fase `ping`, cioè un uscita 4 («lo strumento non è
                   certificato») su un server sano.
MARCA:             [?]
```
**A24**

```
DOVE:              banchi/01-b6-tetti.py:1113-1149 (il ramo dei casi `atteso="risposta"`) e
                   1257, 1267-1271
COSA CONTRADDICE:  il commento del file/della fase — «una morte a 30 s **senza motivo** è il PING
                   che manca» — e LEZIONI.md §1.9 punto 3
COME SI DIMOSTRA:  nei due casi che rispondono alla `[?]` R3.27 (`ciao-senza-controllo`,
                   `ciao-sessione-tardiva`) la classificazione ha tre rami: congedo/chiusura ·
                   `niente` · **`else` con `verso="?"`**.  `esito == "morte-silenziosa"` — cioè
                   proprio la firma del PING mancante — cade nell'`else`, **non incrementa
                   `guasti`**, e finisce in `risposte` con `verso="?"`; poi
                   `fuori_dal_documento = [r for r in risposte if r[1] != "TLS"]` lo raccoglie e
                   lo script esce **3**, stampando «i tetti si comportano come il CODICE dice, ma
                   §4.6 riga 1 dice un'altra cosa … la cura sta in RCP.md, non nel server».
                   Cioè: un esito che il banco non ha saputo classificare viene consegnato come
                   prova che **il documento è sbagliato**.  ⚠ Nella fase `sani` il tetto del
                   trasporto è 120 s e il caso è difficile da raggiungere; il ramo però è quello
                   che decide fra «cura nel documento» e «cura nel server», ed è il ramo che non
                   ha un «non lo so».
MARCA:             [?]
```
**A25**

---

## 6. Le misure della sonda, e il rapporto `S-esiti-sonda.md`

```
DOVE:              banchi/01-s1b-stato.jsonl riga 1 · web/rapporti/S-esiti-sonda.md §2.2 e la
                   riga S1b della tabella iniziale · banchi/01-s1b-eccezione.sh:416-419 e 450
COSA CONTRADDICE:  LEZIONI.md §1.9 regola 5 (il denominatore si legge dove la cosa succede) e
                   REVIEWER.md §2 E5
COME SI DIMOSTRA:  l'unico giro «avvia» registrato dice, testualmente:
                     "scadenza_memorizzata": "valore non interpretabile: '13431474587889370'"
                   cioè **lo strumento ha dichiarato di non aver saputo leggere il valore**.  Il
                   rapporto pubblica invece, come fatto misurato con la stella,
                   «⭐ la scadenza che Chrome si è segnato: **2026-08-17T21:09:47.889Z**, cioè
                   604 800 s esatti dalla concessione», e la tabella d'apertura ne fa la riga di
                   esito di S1b.
                   La conversione **è giusta** (`13431474587889370/1e6 − 11644473600` →
                   2026-08-17T21:09:47.889370+00:00, `[M]`), e il codice di oggi la fa
                   (righe 288-295): ma è stata aggiunta **dopo** il giro che sta nel registro, e
                   **nessun giro successivo la riscrive** — `registra` nel ramo `oggi` (riga 450)
                   non porta il campo `scadenza_memorizzata` affatto.
                   ⛔ Quindi il numero più citato di S1b non ha, su disco, nessuna riga che lo
                   sostenga, e l'unica riga che c'è dice il contrario.  Il giro «avvia» non si può
                   nemmeno rifare senza far ripartire l'orologio da capo (riga 393-396).
MARCA:             [M]
```
**A26**

```
DOVE:              banchi/01-s1b-eccezione.sh:228-233 (`visita`) e 429-459
COSA CONTRADDICE:  LEZIONI.md §1.9 regola 2 (il controllo positivo sullo strumento) e regola 1
COME SI DIMOSTRA:  `visita()` risponde **SI** se il token del giro compare nel registro delle
                   visite sul server, **NO** in ogni altro caso — compresi: ssh caduto, credenziali
                   rifiutate, `01-s1b-visite.jsonl` cancellato o rinominato, il sito acceso da un
                   percorso diverso.  Il «controllo che dice no» (un profilo nuovo deve NON
                   arrivare) legge **lo stesso canale**: quando il canale è rotto, il profilo nuovo
                   dà NO — e il controllo si dichiara **passato**.
                   Caso concreto: qualcuno ripulisce `/media/REMOTIX/src/01-s1b-visite.jsonl`.  Il
                   giro di domani stampa: «un profilo appena nato NON arriva alla pagina: lo
                   strumento distingue», poi «la pagina NON si apre», e chiude con
                   **`OK  a 1.00 giorni l'eccezione NON c'è più: è questo il numero di S1b»** —
                   il numero della misura, in verde, da uno strumento muto.
                   ⛔ Manca il controllo positivo che chiuderebbe il buco: **una visita che è
                   certamente avvenuta deve comparire nel registro**.  Gli altri tre controlli
                   dichiarati (impronta, profilo nuovo, sito vivo) coprono il certificato e il
                   server, nessuno copre il canale di lettura, che è quello su cui poggia il
                   verdetto.
MARCA:             [R]
```
**A27**

```
DOVE:              banchi/01-s-telefono.sh:202 e 215-217
COSA CONTRADDICE:  LEZIONI.md §1.9 (il `2>/dev/null` nominato per nome) e B0.4
COME SI DIMOSTRA:  `ssh_ "cat $SRC/01-s1b-visite.jsonl" >/tmp/s3a-registro.jsonl 2>/dev/null` —
                   se ssh non parte, il file locale è vuoto e **la ragione è stata buttata**.  Il
                   testo che segue è onesto («nessuno ha misurato», non «nessuna scorciatoia
                   arriva»), ma la riga dopo è `sys.exit(0)`: lo **stato d'uscita dice riuscito**.
                   E anche nel cammino buono `analizza` non confronta niente e non esce mai ≠ 0:
                   trovare uno stato **B — CONSEGNATA E RISERVATA**, che è il caso pericoloso per
                   cui S3a esiste, produce una riga di testo e uscita 0.  B0.4 vuole che lo stato
                   d'uscita sia quello del confronto.
MARCA:             [R]
```
**A28**

```
DOVE:              banchi/01-s1b-eccezione.sh:150-152
COSA CONTRADDICE:  B0.1 (dichiara **e verifica**) e B0.2 (lo stato che sopravvive)
COME SI DIMOSTRA:  «se `/tmp/.X11-unix/X77` esiste, uso quello» — e non si verifica di che
                   geometria sia né chi l'abbia acceso.  `01-s5-tela.sh` usa lo **stesso numero di
                   schermo** predefinito e lo apre a `1920x1080`, S1b lo vuole `1280x1024`.  Un
                   giro di S5 rimasto appeso lascia lì uno schermo di un'altra misura, e la
                   finestra di Chrome — che è quel che `xdotool` deve trovare e cliccare a
                   coordinate fisse (`mousemove 640 500`) — nasce su una scena diversa da quella
                   dichiarata nel rapporto.
MARCA:             [?]
```
**A29**

```
DOVE:              web/rapporti/S-esiti-sonda.md, tabella d'apertura, riga S7
COSA CONTRADDICE:  B0.6 e la regola del rapporto stesso («la scena accanto a ogni numero»)
COME SI DIMOSTRA:  la riga rimanda a `banchi/01-s7-esiti.jsonl` «(sul server, in
                   /media/REMOTIX/src/)», e quel file **non esiste in questo albero**: dei banchi
                   della sonda solo `01-s5-esiti.jsonl` e `01-s1b-stato.jsonl` sono qui.  Il
                   numero che chiude la `[?]` di `RCP.md` §7.3 — la sola misura dichiarata
                   completa della notte — non ha, da questa parte, nessun dato a cui un revisore
                   possa risalire; e il rapporto §10 dice che la sessione GNOME è stata riavviata
                   e il drop-in tolto, cioè la scena non c'è più.  ⚠ Non contesto il numero:
                   contesto che sia **riverificabile**, che è la ragione per cui i registri si
                   tengono.
MARCA:             [?]
```
**A30**

---

## 7. ⭐ Che cosa ho provato a rompere senza riuscirci

*Perché il prossimo non rifaccia la stessa caccia.*

| Che cosa ho cercato | Che cosa ho trovato |
|---|---|
| **Il verdetto su zero cose**, in tutti i verdetti nuovi | ⭐ **c'è la guardia dappertutto**, e in cinque forme diverse: `01-b12-guasti.py:655-658` (`if not per_sigla: return 2`), `01-b8-cronometro.py:888-891` («ZERO tentativi: «tutti quelli provati sono andati bene» è vero anche quando i provati sono zero»), `01-c2-diagnosi.py:537-540`, `01-b9-letture.py:768-772`, `01-b13-proprieta.py:834-838`, `01-b6-tetti.py:942-948`, `01-s5-tela.sh` verdetto (`if provati == 0`). B8 ne fa perfino un **guasto di certificazione** (`nessun_tentativo`, che toglie i tentativi e lascia le pagine, «perché un file vuoto lo nota chiunque»). Non ho trovato un verdetto che concluda su zero cose — **con l'eccezione di A20** (`01-b8-prova-ban.c`) e **di A28** (`analizza` esce 0). |
| **Un guasto di B12 rimasto addosso al codice** | `md5sum` di ognuno dei sei file di `01-b12-copie/` contro il rispettivo originale: **tutti identici**; `grep -rl "REMOTIX B12 GUASTO"` su tutto l'albero trova **solo `01-b12-guasti.py`** (il catalogo). `togli()` riverifica davvero: prima la marca residua, poi che l'appiglio sia tornato **esattamente una volta**. `[M]` |
| **`kill -0` su processi di root** (la quinta veste di §1.9) | non ce n'è **nessuno** nei banchi nuovi: tutti e cinque gli script usano `[ -d /proc/$PID ]`, e tutti e cinque spiegano perché. La lezione è stata applicata. |
| **`pkill -f`** | non compare in nessuno; tre file lo nominano solo per vietarlo. |
| **Il PID letto fuori dal contenitore** (il numero di uno spazio dei nomi diverso) | non è un difetto: `v1/banco/enter.sh` usa `chroot`, non uno spazio dei nomi dei PID — i numeri sono gli stessi dai due lati (già stabilito in R8, tabella di chiusura). |
| **Il token del giro che rientra dall'uscita di `ssh`** (che farebbe dire «SI» a `visita()` sempre) | `v1/strumenti/sshpw.py` **non riecheggia** il comando remoto, e `ssh` con un comando non alloca un tty remoto: l'unica cosa che stampa in più sono i suoi avvisi, che non contengono il token. La strada è chiusa. Il buco di `visita()` è un altro, ed è A27. |
| **Il seme del bootstrap di B8** | fisso (`SEME = 20260811`) e dichiarato: due verdetti sugli stessi campioni danno la stessa riga. E la regola delle mediane è **l'unica forma che non si può soddisfare misurando di meno** — guardare meno allarga l'intervallo e porta al *sospeso*. Non sono riuscito a costruire un caso in cui misurare di meno produca un verde. |
| **La rotazione dei tre casi di B8** | copre la deriva dentro il blocco (sei permutazioni, e l'indirizzo alterna **fra i fallimenti**, non fra i passi). Non ho trovato un ordine che leghi sistematicamente un caso a un indirizzo o a una posizione. |
| **B9: due letture che producono gli stessi byte** | il banco lo verifica da sé (`controlla_byte`, e una voce «UGUALI» è un rosso **di B9**), e la voce L6 dichiara di non cambiare nessun byte invece di inventarne uno per far tornare la colonna. Eseguito: **12 su 12**, e le tre colonne non coincidono, come deve essere. `[M]` |
| **C2: la tabella di decisione** | ha sette nomi più `NON_SO`, e nessun ramo predefinito che indovina. Ho provato a costruire una coppia (tcp, udp) che finisca nel nome sbagliato: le combinazioni non coperte cadono tutte in `NON_SO`. Il difetto di C2 non è nella tabella, è nello stato iniziale (A9). |
| **B13: il controllo positivo del `grep` della parola d'ordine** | è fatto bene e nel punto giusto — l'esca ha **l'estensione dei prodotti**, non un'estensione qualunque, «o certificherebbe un `grep` puntato sull'insieme sbagliato», e si toglie in un `finally`. Il buco è lo stato d'uscita (A13), non il controllo. |
| **S5: lo zoom applicato davvero** | verificato con `devicePixelRatio` riletto dalla pagina a ogni `resize`, non contando i tasti, e con un ramo esplicito «non sono riuscito a portare lo zoom a 150 %» che **non registra un esito**. Non ho trovato il modo di far passare «i due numeri sono uguali» senza aver cambiato niente. |
| **S7: il denominatore prima di ogni serie** | `il_puntatore_arriva()` è un controllo positivo dello strumento che questo banco ha pagato tre giri per imparare, e c'è. Anche i due controlli positivi della pagina (documento a 8000 px, schermo = monitor virtuale) sono confrontati, non stampati. |
| **Un `2>/dev/null` che nasconda una diagnosi** nei nuovi banchi | quasi tutti sono su `kill`/`wait` (innocui). L'unico che nasconde qualcosa che conta è `01-s-telefono.sh:202` → A28. |

---

## 8. Il verdetto

⛔ **Non è un'assoluzione, ed è la parte che si legge male se si legge in fretta.**

**Non ho trovato niente** su: la struttura dei verdetti di B8 e B6 (i cinque e i tre esiti separati,
col colpevole nominato e il denominatore accanto), la tabella di decisione di C2, l'inventario di
B9, il controllo positivo di B13.2, la certificazione a tredici mutazioni del giudice di B8, e la
disciplina di `01-b8-sblocca.py` sui tre esiti. Sono le parti in cui ho cercato più a lungo.

**Ho trovato**, in ordine di quel che avvelena di più le misure che verranno:

1. **A1 + A2 + A3 + A4**: B12, il banco che dà fiducia a tutti gli altri, oggi certifica **due**
   banchi su dodici nel senso pieno della propria definizione, ne dichiara **quattro**, e il suo
   registro arrotonda «provato e non riuscito» in «mai provato». Un banco che non è mai diventato
   rosso non è pulito; un banco che il registro dice certificato **e non lo è** è peggio, perché
   quella riga è precisamente ciò su cui gli altri poggeranno.
2. **A6 + A7**: due modi diversi in cui un guasto o un secondo server sopravvivono al giro **senza
   che nessuno lo sappia** — e per A7 la cura è già scritta, dalla revisione precedente, nello
   stesso indirizzario.
3. **A18 + A26 + A27**: tre punti in cui un verdetto o un rapporto **dice più di quel che ha
   misurato** — l'imputato nominato per costruzione, una data pubblicata contro il proprio registro,
   e un numero di misura che uno strumento muto può produrre in verde.

Il resto sono buchi dichiarabili: si chiudono con una riga di codice ciascuno, e la loro utilità è
che adesso hanno un nome.

*Nessun file toccato fuori da questo. Nessun commit. `/media/REMOTIX/s1b-certificato/` e
`~/.remotix-s1b/` non sono stati né letti né sfiorati; la macchina di prova `192.168.0.2` non è
stata contattata, quindi nessun tentativo di autenticazione è stato consumato.*
