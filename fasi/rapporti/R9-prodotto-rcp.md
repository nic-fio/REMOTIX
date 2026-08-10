# R9 — revisione avversariale del PRODOTTO: il protocollo in C

*10 agosto 2026. Area: `banchi/rcp/rcp.c` (1292 righe), `banchi/rcp/rcp.h`,
`banchi/rcp/autenticazione.c`. Arbitro: `RCP.md`. Regole: `REVIEWER.md`,
mandato `fasi/rapporti/MANDATO-10-agosto.md` (con la rettifica al §3 punto 1
arrivata durante il lavoro).*

⚠ **Questa non è un'approvazione di quel che non è elencato qui.** `REVIEWER.md`
§0: una review che non trova niente non assolve il prodotto, e una review che
trova diciotto cose non assolve la diciannovesima. In fondo, §C, sta l'elenco di
**che cosa ho provato a rompere senza riuscirci** — che è informazione anche
quella (`PIANO.md` §0.4).

⛔ Non ho misurato, non ho compilato, non ho toccato nessun file all'infuori di
questo. Ogni «come si dimostra» è un **ingresso concreto** costruito leggendo il
codice e l'arbitro, non un'ipotesi sul comportamento.

---

## A. I rilievi `[R]` — contraddizioni confermate da una regola già scritta

---

### R9.1 — Il limitatore dei tentativi si apre da solo quando la sua tabella è piena, e non lo scrive da nessuna parte

```
DOVE:             banchi/rcp/rcp.c:214-236 (`trova_o_crea`, `bloccato`),
                  :238-259 (`segna_fallito`), :174 (`MAX_TENTATIVI 64`),
                  usati da :723-736
COSA CONTRADDICE: RCP.md §4.4-bis (il server «tiene due contatori» e «applica il
                  più severo»: è un DEVE di §4.4), invariante I3 «la guardia
                  parte da negato», forma E8 «il silenzio scambiato per zero»,
                  LEZIONI.md §1.9
MARCA:            [R]
```

**Che cosa fa il codice.** `bloccato()` chiama `trova_o_crea()`, che **crea una
voce** anche per una chiave che non ha mai fallito niente. La tabella ha 64
posti, **non ha sfratto, non ha scadenza e non ha una riga di registro**. Quando
è piena, `trova_o_crea()` restituisce `-1` e da quel momento:

- `bloccato()` restituisce **`false`** — cioè *«non è bloccato»* — per ogni
  chiave nuova. La guardia non parte da negato: parte da **ammesso**;
- `segna_fallito()` esce in silenzio (`if (i < 0) return;`): il tentativo
  fallito **non viene contato da nessuno**;
- nessuna riga nel registro dice che è successo.

**Come si dimostra.** Sessantaquattro connessioni con sessantaquattro nomi
utente distinti e mai visti (`a0`…`a63`), ciascuna con una `CREDENZIALI`
sbagliata: ogni giro consuma un posto per il nome (l'indirizzo ne consuma uno
solo, condiviso). Alla sessantacinquesima connessione la tabella è piena. Da lì
in poi, contro **qualunque** nome non già in tabella — per esempio l'utente vero
della macchina — `bloccato()` dice `false` e `segna_fallito()` non conta:
**parole d'ordine all'infinito, senza soglia, senza blocco e senza una riga nel
registro**.

⚠ È la stessa forma del difetto che il riquadro di `rcp.c:185-203` dichiara di
aver appena pagato: *«il codice c'era, sembrava giusto, si leggeva bene, e non
faceva niente»*. Lì la chiave misurava la cosa sbagliata; qui la tabella smette
di esistere. ⛔ E il controllo di B5 non lo vede **per costruzione**: usa sette
nomi, non sessantacinque, e la sua previsione scritta riguarda la chiave, non la
capienza.

---

### R9.2 — Dopo l'orologio del silenzio restano DUE sessioni «attiva» per lo stesso utente

```
DOVE:             banchi/rcp/rcp.c:1263-1271 (`rcp_tempo`, il ramo del silenzio)
                  in combinazione con :850-873 (`tratta_attacca`)
COSA CONTRADDICE: invariante I2 «una sessione grafica per utente»
                  (REVIEWER.md §3), RCP.md §8.2 motivo 0x0F
MARCA:            [R]
```

**Che cosa fa il codice.** Passati trenta secondi senza un byte, il ramo del
silenzio fa **solo due cose**: `posto_lascia()` e `s->attaccata = false`. Lo
**stato resta `S_ATTIVA`**. E dalla macchina a stati non esiste nessun arco che
riporti a `S_ATTESA_ATTACCA`: quella sessione non potrà mai più riprendersi il
posto, ma continua a essere servita come attiva — è `rcp_stato_nome()` che
l'ospite interroga (`01-b3-rcp-innesta.py:470-474`) per decidere il battito, ed
è `s->stato != S_ATTIVA` la sola guardia di `BANCO_MARCA`.

**Come si dimostra.**

1. il client A completa la stretta di mano per l'utente `u`: posto PRESO,
   `S_ATTIVA`;
2. A tace 31 secondi. Alla prima chiamata di `rcp_tempo()` il posto è
   LASCIATO, A resta `attiva`;
3. il client B, stesso utente `u`, si attacca: `posto_prendi("u")` riesce, B è
   `attiva`;
4. A manda un byte qualsiasi — per esempio `BANCO_MARCA` —: `rcp_ricevi()`
   aggiorna `ultimo_byte`, lo stato è `S_ATTIVA`, il messaggio **viene servito**
   e riceve `BANCO_ESITO`.

Da qui in avanti il server ha **due sessioni `attiva` per un solo utente**, che
è precisamente ciò che I2 vieta, e A non ha mai ricevuto niente che gliel'abbia
detto: nessun `CONGEDO`, nessun motivo, nessun codice di chiusura. §8.2 dice che
«nessun client attaccato e vivo viene mai spodestato»: qui A **viene spodestato
in silenzio** e continua a credersi attaccato.

⚠ Il riquadro di `rcp.c:53-70` dichiara una scelta — *lasciare la connessione
aperta* — e quella scelta è dichiarata e difendibile. ⛔ **Ma non copre lo
stato**: «non chiudere la connessione» e «restare `attiva`» sono due cose
diverse, e la seconda non è dichiarata da nessuna parte.

---

### R9.3 — Il diciassettesimo utente si sente dire «sei già collegato», e non è vero

```
DOVE:             banchi/rcp/rcp.c:132-145 (`posto_prendi`), :118
                  (`MAX_ATTACCATE 16`), :850-856 (chi lo chiama)
COSA CONTRADDICE: RCP.md §8.2 motivo 0x0F («c'è già un client attaccato a
                  QUESTA sessione»), §8.2 «ogni motivo DEVE essere mostrabile
                  all'utente in una frase comprensibile», forme E1 ed E6
MARCA:            [R]
```

**Che cosa fa il codice.** `posto_prendi()` restituisce `false` per **due fatti
diversi**: «il posto di questo utente è occupato» e «la tabella è piena». Il
chiamante ne deduce uno solo, e congeda con `GIA_ATTIVA_REMOTA` e il dettaglio
*«c'è già un client attaccato a questa sessione»*.

**Come si dimostra.** Sedici utenti distinti attaccati (la macchina è
multi-tenant, `SPECIFICHE.md` §5.5, ed è il caso per cui `autenticazione.c` ha
tolto il confronto con l'utente del processo). Il diciassettesimo utente — che
non ha mai aperto niente da nessuna parte — manda `ATTACCA` e riceve
`CONGEDO(0x0F)` con quel dettaglio. Il client, come §8.2 gli impone, costruisce
dal codice la frase *«hai già una sessione attiva altrove»*. **È falsa.** E il
registro scrive `posto NEGATO a <lui> (occupati: 16)`, che è vero e non nomina
la causa.

⛔ È letteralmente il sintomo che il riquadro di `rcp.c:982-994` dichiara di
essere andato a curare: *«mi dice che sono già collegato, e non è vero»*. La
cura ha tolto una delle due strade che ci portavano; questa è rimasta.

---

### R9.4 — Il messaggio si esegue, e SOLO DOPO si controlla che la lunghezza dichiarata torni

```
DOVE:             banchi/rcp/rcp.c:1166-1175 (il controllo `l.i != lung` dopo
                  lo `switch`)
COSA CONTRADDICE: RCP.md §3 («NON DEVE proseguire»), §6.1 («un ricevente che
                  legge una lunghezza incoerente con quel che il tipo prevede
                  DEVE chiudere con ERRORE_PROTOCOLLO»)
MARCA:            [R]
```

**Che cosa fa il codice.** Il commento sopra il controllo è esatto — si avanza
della lunghezza dichiarata — ma il controllo sta **dopo** `avanti = tratta_*()`.
Quando il corpo ha byte in più dei campi previsti, il messaggio è già stato
**eseguito per intero, con tutti i suoi effetti sul filo e sullo stato**.

**Come si dimostra**, tre ingressi, in ordine di danno crescente:

- `CIAO` con quattro byte di riempimento in coda — è il caso
  `lunghezza-in-piu` **già scritto in B5** (`01-b5-violazioni.py:275`): il
  server manda **`ECCOMI`**, passa a `attesa-credenziali`, e solo allora
  congeda. B5 guarda il motivo del congedo, lo trova giusto, ed è **verde su un
  server che ha risposto a un messaggio malformato**;
- `ATTACCA` ben formato con **un byte** di riempimento in coda: il server
  **prende il posto** nel registro delle sessioni, spedisce **`SESSIONE`**,
  scrive `sessione aperta …` nel registro, passa a `attiva`, e poi congeda con
  `ERRORE_PROTOCOLLO`. Sul filo, in quest'ordine: `SESSIONE`, `CONGEDO(0x0B)`.
  Un client che ha ricevuto `SESSIONE` è **autorizzato da §2.5** ad aprire il
  suo stream di input: lo aprirà su una sessione che sta morendo;
- `CREDENZIALI` con un byte di riempimento: **PAM viene interrogata**, i
  contatori di §4.4-bis vengono mossi, e poi la connessione cade per errore di
  protocollo. Un messaggio che §6.1 dichiara malformato **muove il limitatore**,
  che è esattamente la proprietà che B5 verifica con
  `malformati-non-contano` — e la verifica con l'altra metà dei malformati,
  quelli fuori intervallo, che invece cadono prima.

---

### R9.5 — `CONGEDO`: il motivo si deduce quando manca, non si chiede — e si rispedisce senza guardarlo

```
DOVE:             banchi/rcp/rcp.c:1131-1141 (`case T_CONGEDO`)
COSA CONTRADDICE: RCP.md §7.1 (il corpo di `CONGEDO`: `u8 motivo` +
                  `stringa dettaglio`), §6.1 («lunghezza DEVE essere il numero
                  esatto dei byte del corpo»), §3.1 punto 3 («il codice
                  d'errore applicativo pari al codice del motivo **di §8.2**»),
                  §3.1 («il codice 0 … NON DEVE essere usato»), forma E6
MARCA:            [R]
```

Quattro difetti nello stesso ramo di nove righe:

1. **`lung` non viene mai controllata.** `le_u8()` su un corpo vuoto mette
   `corto = true` e **restituisce 0**, e nessuno guarda `corto`;
2. **lo zero che ne esce viene tappato**: `motivo ? motivo : RCP_CHIUSO_DALL_UTENTE`.
   Il server **inventa** `0x01` per un motivo che il client non ha mandato;
3. **il `dettaglio` non viene mai letto** — né come stringa, né come UTF-8
   (§6.0), né come lunghezza. Il `case` esce con `return false` **prima** del
   controllo `l.i != lung` di R9.4: 65 000 byte di spazzatura dopo il motivo
   passano senza che nessuno li guardi;
4. **il motivo viene rispedito senza convalida** dentro `s->g.chiudi()`, cioè
   nel codice d'errore applicativo della chiusura della sessione WebTransport.

**Come si dimostra**, due ingressi:

- `00 0C 00 00 00 00` — sei byte, `CONGEDO` con corpo vuoto. Il registro del
  server scrive `il client si congeda, motivo=0x00`, e sul filo la sessione si
  chiude con **`0x01`**. ⛔ **Due verità sullo stesso fatto**: chi legge il
  registro e chi legge il codice di chiusura non leggono lo stesso numero, ed è
  la forma per cui §3.1 punto 3 esiste. ⚠ Ed è la faccia mancante del difetto
  noto n. 6 del mandato — *«`congedo:0x00` invece di `0x0b`»*;
- `00 0C 00 00 00 01 42` — `CONGEDO(0x42)`. `0x42` non è nessuno dei quindici
  motivi di §8.2; il server lo prende e lo mette **lui** nel codice di chiusura
  della sessione. §3 vieta di proseguire su ciò che non si capisce, e §3.1
  punto 3 vuole un codice **di §8.2**.

---

### R9.6 — Oltre la trentaduesima capacità il nome ripetuto non viene più visto, e «vince l'ultimo»

```
DOVE:             banchi/rcp/rcp.c:601 (`char visti[32][65]`), :631
                  (`if (n_visti < 32)`), :639-644
COSA CONTRADDICE: RCP.md §4.3 ⛔ «un nome ripetuto due volte è
                  ERRORE_PROTOCOLLO. "Vince l'ultimo" e "vince il primo" sono
                  due implementazioni diverse dello stesso documento»
MARCA:            [R]
```

**Che cosa fa il codice.** `quante` è un `u16`: il client può dichiarare fino a
65 535 capacità. La memoria dei nomi già visti si ferma a **32**, e oltre quel
numero il nome **non viene registrato** — silenziosamente, con un `if` senza
`else` e senza una riga nel registro. Il confronto per il duplicato scorre solo
i primi 32.

**Come si dimostra.** Un `CIAO` con 32 capacità dal nome sconosciuto e lecito
(`x00`…`x31`, che §3 eccezione 1 impone di ignorare), seguite da:

```
video.codec = hevc
video.codec = av1
```

Il server **non** congeda: `snprintf(c_codec, …)` viene eseguito due volte e la
seconda vince. Il registro scrive `negoziato video.codec=av1`, e la
negoziazione riuscita contiene il contrario di quel che il client aveva messo
per primo — la trappola 4 di `LEZIONI.md` §4, con un `ERRORE_PROTOCOLLO`
obbligatorio saltato. ⚠ Il caso `capacita-ripetuta` di B5 usa **tre** capacità:
resta verde per sempre.

---

### R9.7 — Quattro messaggi che §7.1 definisce e manda dal client sono trattati come «tipo sconosciuto»

```
DOVE:             banchi/rcp/rcp.c:1142-1164 (il ramo `default`)
COSA CONTRADDICE: RCP.md §7.1 (`0x0008 VISTA`, `0x0009 DISPOSIZIONE`,
                  `0x000B ADATTA_TELA`, `0x000D RICHIEDI_CHIAVE` — tutti «→»),
                  §7.1 ⛔ «a ogni ADATTA_TELA il server DEVE rispondere con un
                  TELA», §7.1 riquadro R1.17, §5.2, §3.1 punto 1
MARCA:            [R]
```

**Che cosa fa il codice.** Lo `switch` conosce cinque tipi. Il `default`
distingue con cura i **sette** tipi «del server» dal resto — ed è una
distinzione giusta e ben motivata nel commento — ma **i quattro tipi del client
rimasti fuori dallo switch finiscono nell'altro ramo**, quello che scrive nel
registro `tipo 0x0008 sconosciuto sul controllo`. §3.1 punto 1 chiede di
scrivere **che cosa** non si è capito; quella riga dice una cosa **falsa** su un
tipo che `RCP.md` §7.1 definisce, con lo stesso identico difetto che il commento
sopra dichiara di aver corretto per i tipi del server.

**Come si dimostra**, e il primo caso è quello che fa il danno:

- sessione `attiva`, l'utente stringe la finestra del browser. Il client fa quel
  che §7.1 gli permette e manda `VISTA(300×801)`. Il server **congeda con
  `ERRORE_PROTOCOLLO`**. ⛔ È alla lettera il sintomo che il riquadro R1.17 di
  §7.1 è stato scritto per rendere impossibile — *«farsi chiudere la sessione
  perché ha ridimensionato una finestra»* — e B5 ha un caso apposta
  (`vista-300x801`) che passa **solo perché la misura viaggia dentro `ATTACCA`**,
  cioè per la strada che questo difetto non tocca;
- `ADATTA_TELA`: §7.1 dice ⛔ **DEVE** rispondere con un `TELA`, e in fase 1 la
  risposta giusta e disponibile è `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)`. Il
  server chiude la sessione;
- `RICHIEDI_CHIAVE`: §5.2 dice che il client **DEVE** mandarlo quando vede un
  buco. Un client conforme viene chiuso per errore di protocollo.

⚠ Se la scelta era *«in fase 1 questi quattro non si servono»*, allora è una
scelta che va dichiarata e detta con il motivo giusto — non con la parola
«sconosciuto» su tipi che il documento numera.

---

### R9.8 — La parola d'ordine resta nell'accumulo per tutta la sessione, e nella memoria liberata dopo

```
DOVE:             banchi/rcp/rcp.c:103 (`uint8_t acc[MAX_ACCUMULO]` dentro
                  `struct rcp_sessione`), :740 (`memset(parola, …)`),
                  :1176-1177 (`memmove` che non ripulisce la coda),
                  :968-978 (`rcp_libera`, `free(s)` senza azzerare)
COSA CONTRADDICE: RCP.md §4.4 ⚠ «va azzerata appena PAM ha risposto, e non deve
                  comparire in nessun registro a nessun livello»; e il commento
                  di rcp.c:738-739, che dichiara fatto quel che non è fatto
MARCA:            [R]
```

**Che cosa fa il codice.** `memset(parola, 0, sizeof parola)` azzera **la copia
locale**. L'originale è arrivato dentro `s->acc`, che è un campo della sessione,
e ci resta:

- `memmove(s->acc, s->acc + 6 + lung, s->acc_len - 6 - lung)` fa scorrere in
  giù il residuo e **non ripulisce la coda**: i byte della `CREDENZIALI`
  restano dove sono;
- niente li tocca più fino a `free(s)` in `rcp_libera()`, che **non azzera**. La
  parola d'ordine in chiaro finisce nel mucchio liberato, disponibile a
  qualunque allocazione successiva del processo — che serve **tutti** gli utenti
  della macchina (`SPECIFICHE.md` §5.5);
- e su ogni cammino d'errore che congeda **dopo** `le_str` — utente non UTF-8,
  utente o parola fuori intervallo — nemmeno la copia locale viene azzerata: il
  `memset` sta dopo il `return false`.

**Come si dimostra.** `CREDENZIALI` con una parola di 1024 byte e un utente di
zero byte (è il caso `utente-vuoto` **già in B5**): si congeda a `rcp.c:705`,
`parola[1025]` non viene azzerata e resta sullo stack, e i 1024 byte veri
restano in `s->acc` fino alla fine della connessione.

⚠ E `rcp.c:717` scrive nel registro `(parola di %zu byte)`. La parola non
compare — il commento su questo ha ragione — ma **la sua lunghezza esatta sì**,
per ogni tentativo riuscito e fallito, in un registro che §11.1 tratta come un
file che si conserva.

---

### R9.9 — Il tetto fra `AMMESSO` e `ATTACCA` è sei volte quello che dice §4.6

```
DOVE:             banchi/rcp/rcp.c:49 (`#define TETTO_ATTACCA 60000`),
                  usato a :1281-1289
COSA CONTRADDICE: RCP.md §4.6, tabella: «`AMMESSO` spedito → `ATTACCA` ricevuto
                  → **10 s**»
MARCA:            [R]
```

**Che cosa fa il codice.** I tre tetti sono scritti in fila sotto il commento
«I tetti di §4.6, in millisecondi». Due combaciano (5 000 e 60 000); il terzo
vale **60 000 al posto di 10 000**.

**Come si dimostra.** Un client che arriva fino ad `AMMESSO` e poi tace: al
decimo secondo §4.6 impone `CONGEDO(TEMPO_SCADUTO)`; questo server aspetta fino
al sessantesimo. Il tetto esiste perché *«una connessione che si ferma a metà
stretta di mano tiene un posto e non lo dichiara a nessuno»* (§4.6): qui il
posto — quello di §4.4-bis e quello del registro delle sessioni non ancora
preso — si tiene sei volte più a lungo di quel che il documento concede.

⛔ **E nessun banco lo vede.** §11 elenca *«i tempi della stretta di mano: si
apre una connessione e si tace, per ciascuno dei tre tetti di §4.6»*, e in
`01-b5-violazioni.py` non c'è **nessun** caso sui tetti: `grep -n
"tetto\|TEMPO_SCADUTO\|scaduto"` non trova niente. Il difetto sta esattamente
dove il banco non guarda.

---

### R9.10 — Il blocco per indirizzo non scade mai, e raddoppia fra prove separate da settimane

```
DOVE:             banchi/rcp/rcp.c:238-259 (`segna_fallito`), :252-257
                  (`blocco_corrente`)
COSA CONTRADDICE: RCP.md §4.4-bis, riga «azzeramento»: «il contatore per
                  indirizzo **scade da sé dopo 30 minuti di quiete**»
MARCA:            [R]
```

**Che cosa fa il codice.** C'è una finestra di conteggio di 5 minuti che azzera
`falliti`, e non c'è **nessuna** scadenza. In particolare `blocco_corrente` —
la durata corrente del blocco — non viene mai riportato a zero se non da un
`azzera_tentativi()`, che si chiama **solo su un'autenticazione riuscita di quel
nome**, mai per un indirizzo.

**Come si dimostra.**

1. cinque tentativi falliti dall'indirizzo `X`: blocco di 30 s;
2. **un mese** di silenzio da `X`;
3. altri cinque tentativi falliti da `X`: `ora - primo_fallito` supera la
   finestra, `falliti` riparte da 0 — ma `blocco_corrente` vale ancora 30 000, e
   il nuovo blocco è di **60 secondi**. Al giro dopo 120, e così via fino a 15
   minuti, per sempre.

⚠ **E c'è un secondo effetto, che tocca il difetto noto n. 6 del mandato**
(*«B11 ha dato verdetti diversi fra giri identici»*). Il controllo `limitatore`
di B5 (`01-b5-violazioni.py:719-796`) fa **sette** fallimenti dallo stesso
indirizzo: al termine, quell'indirizzo — che è quello del banco — resta bloccato
con una finestra che il giro successivo **raddoppia invece di ripartire**. Due
esecuzioni consecutive di B5 non partono dallo stesso stato: nella seconda, ogni
caso che passa da `fino_ad_ammesso()` riceve `TROPPI_TENTATIVI` invece di
`AMMESSO`. ⛔ Due giri identici, due verdetti diversi, e la causa non è nel
banco.

---

### R9.11 — Un byte nullo dentro una stringa: la lunghezza dice una cosa, quel che si usa ne dice un'altra

```
DOVE:             banchi/rcp/rcp.c:340-356 (`le_str`), :620 (`utf8_valido` su
                  `lv`), :639-644 e :712 (`snprintf(… "%s" …)`)
COSA CONTRADDICE: RCP.md §6.0 (una stringa è «esattamente `lunghezza` byte»),
                  §4.3 («un valore è testo UTF-8 **stampabile**»), forma E8
MARCA:            [R]
```

**Che cosa fa il codice.** `le_str()` copia `n` byte e mette il terminatore
dopo. Tutte le convalide lavorano sulla **lunghezza dichiarata** (`lv`, `lu`);
tutti gli usi lavorano sulla **stringa C** (`%s`, `strcmp`, `voce_presente`,
`strchr`). Un `0x00` in mezzo separa le due letture, e `utf8_valido()` lo
accetta (`c < 0x80`).

**Come si dimostra**, due ingressi:

- `audio.codec` con valore di 8 byte `opus\0pcm`: `lv = 8` — dentro il limite —,
  UTF-8 «valido», nessun errore. Poi `voce_presente(c_audio, "pcm")` guarda
  `"opus"` e **congeda con `NIENTE_IN_COMUNE` un client che ha dichiarato
  `pcm`**. §4.3 fa del PCM il controllo positivo di Opus: il ripiego viene
  negato a chi non l'aveva rifiutato;
- `CREDENZIALI` con utente di 9 byte `root\0nemo`: passa gli intervalli di §4.4,
  passa `utf8_valido`, e **PAM viene interrogata su `root`** mentre sul filo
  c'erano nove byte. Il registro scrive `root`. La chiave del contatore di
  §4.4-bis è `root`. Ciò che è arrivato e ciò che si è giudicato sono due
  stringhe diverse, e nessuna riga lo dice.

---

### R9.12 — Voci scartate senza una riga nel registro, dentro una funzione che il registro lo cura

```
DOVE:             banchi/rcp/rcp.c:496-537 (`prima_comune`), in particolare :508
                  (`n && n < sizeof voce && n + 1 < cap`) e :529
                  (`g + n + 2 < cap_scarti`)
COSA CONTRADDICE: RCP.md §3 ⛔ «ogni tolleranza va scritta nel registro. Una
                  tolleranza silenziosa è indistinguibile da un difetto», §4.3
MARCA:            [R]
```

**Che cosa fa il codice.** Il commento sopra la funzione ha ragione su tutto — e
poi la funzione ha **tre** scarti che non passano da `scarti`:

- una voce lunga ≥ 31 byte: `n + 1 < cap` è falso perché `cap` è
  `sizeof s->codec` = 32. La voce **non viene confrontata, non viene scelta e
  non viene messa negli scarti**;
- una voce vuota (`n == 0`), cioè `hevc,,av1`: idem;
- le voci che non entrano più nel buffer degli scarti (`cap_scarti` = 257):
  scartate due volte, e la seconda in silenzio.

**Come si dimostra.** `video.codec = av1,questo.codec.ha.un.nome.lunghissimo`
(la seconda voce di 38 byte): il server sceglie `av1` e scrive
`negoziato video.codec=av1`, **senza** la riga `scartate voci sconosciute`. Il
giorno in cui un client di domani offrirà un codec dal nome lungo, il registro —
che §4.3 dichiara *«l'unico posto in cui quel fatto compare»* — non lo conterrà.

---

### R9.13 — Un messaggio conforme fra 64 KiB e 1 MiB viene ucciso come errore di protocollo

```
DOVE:             banchi/rcp/rcp.c:73-74 (`MAX_MESSAGGIO` 1 MiB / `MAX_ACCUMULO`
                  64 KiB), :1069-1072
COSA CONTRADDICE: RCP.md §6.1 «Nessun messaggio DEVE superare 1 MiB»
                  (e quindi: fino a 1 MiB è conforme), §3
MARCA:            [R]
```

**Che cosa fa il codice.** Il tetto del protocollo è dichiarato con tanto di
riferimento (`#define MAX_MESSAGGIO (1024u*1024u) /* §6.1 */`) e poi **non è mai
quello che decide**: l'accumulo si ferma a 64 KiB e ogni messaggio più lungo
muore prima ancora che la sua intestazione venga guardata, con il motivo
`ERRORE_PROTOCOLLO` e il dettaglio «troppi byte in attesa di un corpo».

**Come si dimostra.** Un `CIAO` con 400 capacità dal nome lecito e sconosciuto e
dal valore di 200 byte (≈ 82 KiB): è conforme a §6.1 e a §4.3 in ogni sua parte,
e §3 eccezione 1 impone di ignorare i nomi sconosciuti e proseguire. Il server
congeda. ⚠ Un secondo effetto: il controllo `lung > MAX_MESSAGGIO` di
`rcp.c:1084` è raggiungibile **solo** dalla dichiarazione nell'intestazione, mai
dai byte — cioè il tetto di §6.1 non è il tetto di questo server, e i due numeri
scritti a due righe di distanza non concordano.

---

### R9.14 — `banco.marca` si accende in un posto e si dichiara in un altro, e i due non si parlano

```
DOVE:             banchi/rcp/rcp.c:42 (`#define BANCO_ACCESO 0`), :561-562
                  (`ECCOMI` dichiara `banco.marca = no`), :919-932
COSA CONTRADDICE: RCP.md §7.5 regola 3 («il server DEVE dichiararla»), regola 5
                  («ogni accensione … si scrive nel registro»), §4.3 («un
                  server che la dichiarasse per errore lo scrive nel registro a
                  ogni avvio»), invariante I6
MARCA:            [R]
```

**Come si dimostra.** Si porta `BANCO_ACCESO` a 1 — che è l'unico modo previsto
oggi per accenderla, e il commento lo dichiara. Risultato: il server **accetta**
`BANCO_MARCA` e dipinge sul desktop di qualcuno, mentre il suo `ECCOMI`
continua a dichiarare `banco.marca = no` (stringa costante) e **nessuna riga
compare nel registro all'avvio**. Un client conforme, che legge la capacità, non
ha modo di sapere che è accesa; chi diagnostica il quadratino colorato non ha la
riga che §7.5 regola 5 esiste per garantirgli. ⛔ Due luoghi che devono cambiare
insieme e nessun legame fra i due: è la forma esatta per cui §4.3 ha scritto
quella capacità.

---

### R9.15 — Dopo la fine si giudica «commiato o violazione» sui primi sei byte del pezzo, non sui messaggi

```
DOVE:             banchi/rcp/rcp.c:1052-1065
COSA CONTRADDICE: RCP.md §4.4 ⛔ «qualunque **altro** messaggio, e in
                  particolare un secondo `CREDENZIALI`, è la violazione che
                  §4.4 vieta»; forma E6 «il mittente dedotto invece che chiesto»
MARCA:            [R]
```

**Che cosa fa il codice.** La distinzione fra il congedo conforme di §8.1 e il
tentativo vietato da §4.4 è giusta e ben argomentata — ma è fatta **su un pezzo
di byte, non su un messaggio**: si leggono i primi due byte di `dati`, e se sono
`0x000C` **tutto il pezzo** viene assolto con la riga «e non sono di troppo».

**Come si dimostra**, due ingressi:

- dopo `RESPINTO`, il client scrive in **una sola volta** `CONGEDO(0x01)`
  seguito da una seconda `CREDENZIALI`. Il server legge il primo tipo, dichiara
  il commiato conforme, e **la violazione che B11 esiste per accusare non
  compare in nessuna riga**;
- il client aveva mandato tre byte di un messaggio, il server chiude, e il
  resto arriva dopo: i primi due byte di quella coda sono byte di corpo. Se
  valgono `00 0C` — per esempio la coda di una stringa che contiene `\x00\x0c` —
  il server scrive «⭐ CONGEDO di commiato» per byte che non sono un congedo.

⚠ La cura del 10 agosto ha spostato il difetto dal falso rosso (accusare la
pagina che obbediva a §8.1) al falso verde (assolvere chi viola §4.4). Le due
sono la stessa forma, e il documento su cui ci si appoggia — §4.4 — parla di
**messaggi**, non di pezzi.

---

### R9.16 — Una violazione rilevata a sessione finita non lascia nessuna traccia

```
DOVE:             banchi/rcp/rcp.c:1195-1200 (`rcp_violazione`) e :425-426
                  (la guardia `if (s->stato == S_FINITA) return;` di `congeda`)
COSA CONTRADDICE: RCP.md §3.1 punto 1 («DEVE scrivere nel registro *che cosa*
                  non ha capito»), §3
MARCA:            [R]
```

**Che cosa fa il codice.** `rcp_violazione()` è l'unica strada che l'ospite ha
per raccontare quel che solo lui vede — uno stream in più, un canale nel verso
sbagliato (§2.5). Passa tutto e solo per `congeda()`, che se lo stato è
`S_FINITA` **esce alla prima riga**: niente registro, niente `CONGEDO`, niente
codice di chiusura.

**Come si dimostra.** Il client si congeda regolarmente (`S_FINITA`), e **poi**
apre uno stream unidirezionale col byte alto `0x03` — il canale video nel verso
sbagliato. L'ospite lo rileva (`wt_smista_uni`), stampa la sua riga e chiama
`rcp_violazione()`: dal registro di RCP **non esce niente**. ⚠ Il confronto è
interno al modulo: sette righe sopra, `rcp_ricevi()` scrive `⛔ %zu byte
arrivati DOPO la fine della sessione` proprio perché *«l'unico posto da cui si
possono osservare è qui»*. Per gli stream quel posto è `rcp_violazione()`, e lì
si tace.

---

### R9.17 — `01-b3-rcp-innesta.py --togli`: una condizione necessaria dell'innesto usata come sufficiente, e un albero che non compila con uscita 0

```
DOVE:             banchi/01-b3-rcp-innesta.py:667-678 (il ramo `--togli`),
                  :681-685 (la guardia di idempotenza)
COSA CONTRADDICE: forma E1 «necessario scambiato per sufficiente»
                  (REVIEWER.md §2), REVIEWER.md §1 domanda 4 «distingue lo zero
                  dal fallimento?», LEZIONI.md §1.9
MARCA:            [R]
```

*(Rilievo scritto dopo la rettifica del coordinatore al MANDATO §3 punto 1: il
fatto misurato è che dopo `--togli` da solo la riapplicazione stampa «l'innesto
c'è già: non si tocca niente».)*

L'innesto è fatto di **quattro** cose: i tre file copiati in `examples/`, le due
righe di `CMakeLists.txt`, gli innesti nei `.cc/.h`, e la marca `REMOTIX B3`.
`--togli` ne toglie **due** (i file e il `CMakeLists`) e lo dichiara
onestamente. ⛔ Ma la guardia di idempotenza interroga **solo la quarta**, che
vive nel `.cc` che `--togli` non tocca.

**Come si dimostra**, ed è il fatto misurato:

1. `--togli` — esce **0**. Stato dell'albero: `http3_server_proto_codec.cc`
   contiene `#include "rcp.h"` e le chiamate a `rcp_apri`/`rcp_ricevi`/…;
   `examples/rcp.c`, `rcp.h`, `autenticazione.c` **non esistono più**;
   `CMakeLists.txt` non li nomina e non lega `pam`. ⛔ **Quell'albero non
   compila**, e l'uscita è 0;
2. si riapplica: `MARCA in f.read()` è vero, stampa *«l'innesto c'è già: non si
   tocca niente»* ed esce **0**. Il programma dichiara presente un innesto di cui
   ha appena cancellato metà.

⚠ **Perché conta**, ed è `REVIEWER.md` §1: `ricostruisci()` di
`01-b11-guasto.sh:47-50` chiama i quattro passi nell'ordine giusto — ed è per
quell'ordine, non per una verifica, che oggi funziona: è `01-b2-…--togli` a
ripulire il `.cc` e a portarsi via la marca. **La correttezza dipende da un
effetto collaterale di un altro programma, che nessuna riga dichiara**: chi
scambiasse le due righe, o chiamasse solo la prima, otterrebbe un albero che non
compila, un'uscita 0, e — se un binario di prima è già lì — **una misura verde
su un server vecchio**, che è `LEZIONI.md` §1.3 nella sua forma peggiore.

**E il secondo fatto, che è la domanda 4 di `REVIEWER.md` §1:**

```python
subprocess.run(["git", "-C", "/srv/src/b2/ngtcp2", "checkout", "--",
                "examples/CMakeLists.txt"])
```

Nessun `check=True`, nessuna lettura di `returncode`. Se il `checkout`
fallisce — albero non pulito, percorso spostato, permessi — `--togli` stampa le
stesse identiche righe e restituisce **0**. E in `ricostruisci()` la chiamata è
avvolta in `> /dev/null`: **l'unico segnale rimasto viene buttato via**. «Ho
rimesso l'esempio com'era» e «non sono riuscito a rimettere niente» hanno lo
stesso aspetto e lo stesso stato d'uscita.

---

## B. I sospetti `[?]` — da misurare, non da correggere sulla parola

### R9.18 — `le_str()` restituisce una lunghezza per un buffer che non ha scritto

`rcp.c:340-356`: quando la stringa non ci sta (`n + 1u > cap`), la funzione
avanza l'indice, **non copia niente**, e restituisce comunque `n`. Il buffer del
chiamante resta con quel che c'era prima. Oggi tutti e quattro i chiamanti sono
salvi perché controllano la lunghezza **prima** di guardare il contenuto — e in
`tratta_ciao` la salvezza dipende dal corto circuito di `lv > 256 ||
!utf8_valido(valore, lv)`, cioè dall'ordine di due termini di un `||`. `[?]`
Non ho trovato un ingresso che lo rompa oggi; è la forma E3 (una funzione che fa
meno di quel che il nome dice) e il primo chiamante distratto legge memoria
altrui per `n` byte con `n` fino a 65 535.

### R9.19 — `rcp_azzera_registro_sessioni()` non la chiama nessuno, e se la si chiamasse come dichiarato romperebbe I2

`rcp.c:270-274`. `grep` su tutti i banchi: **zero chiamate**. La funzione azzera
`attaccate` senza toccare il campo `attaccata` delle sessioni vive: se il banco
la usasse davvero «fra una prova e l'altra» con una sessione ancora aperta, quella
sessione crederebbe di avere un posto che non ha, e alla sua chiusura
`posto_lascia()` **libererebbe il posto di un'altra** — un posto lasciato da chi
non l'aveva preso. `[?]` Oggi non è raggiungibile perché nessuno la chiama; è un
punto d'ingresso dichiarato nell'intestazione pubblica e non esercitato da niente.

### R9.20 — `memset()` sulla parola d'ordine può essere tolto dal compilatore

`rcp.c:740`. `parola` è locale e non viene più letta: un compilatore che
ottimizza è **autorizzato** a togliere quel `memset`. La cura conosciuta è
`explicit_bzero()`. `[?]` Non posso compilare né guardare l'assembly — è
esattamente una misura del coder, e va fatta sul binario che gira, non sul
sorgente.

### R9.21 — I due `enum` della funzione di banco hanno gli stessi valori

`rcp.c:30-35`: `BANCO_ACCETTATA = 1` / `BANCO_FUNZIONE_SPENTA = 1`,
`BANCO_RIFIUTATA = 2` / `BANCO_RITARDO_FUORI_LIMITI = 2`. Sono due spazi di nomi
diversi (`esito` e `motivo`, §7.5) collassati negli stessi numeri: uno scambio
dei due `sc_byte()` a `rcp.c:937-938` produrrebbe un `BANCO_ESITO` **ancora
sintatticamente valido**. `[?]` Oggi il codice è giusto e B5 lo verifica; la
segnalo perché è un difetto che il giorno in cui comparirà non avrà sintomi.

### R9.22 — `manda` e `chiudi` non sono controllati, `registra` e `verifica` sì

`rcp.c:398` e `:727` controllano il puntatore prima di chiamare; `rcp.c:415` e
`:441` no. `[?]` Un ospite che dimentichi `chiudi` non ottiene un rifiuto: ottiene
un crash del server, cioè «la connessione è caduta» che si porta via le sessioni
di tutti gli altri (è il rilievo R3.3 citato in B5).

### R9.23 — `conversazione()` risponde con la parola d'ordine a ogni domanda a eco spento

`autenticazione.c:53-62`: risponde a **tutte** le `PAM_PROMPT_ECHO_OFF`, fino a
sedici per chiamata, e PAM può chiamare la conversazione più volte. Con lo stack
`login` di Debian oggi la domanda è una sola; con un modulo a due fattori la
stessa parola verrebbe consegnata **anche al secondo fattore**. `[?]` Va misurato
su uno stack reale, non dedotto. ⚠ E sul cammino d'errore (`strdup` che
fallisce) il `free(out)` a `autenticazione.c:59` lascia le risposte già
duplicate — cioè **copie in chiaro della parola** — nel mucchio, senza azzerarle.

### R9.24 — `solo_indirizzo()` su un indirizzo senza porta taglia dentro l'indirizzo

`rcp.c:204-212`. Il taglio all'ultimo `:` è giusto e il riquadro sopra spiega
bene perché. `[?]` Ma se l'ospite passasse un IPv6 **senza** porta — la
`straddr()` dell'esempio ngtcp2 la mette sempre, oggi — la chiave diventerebbe un
prefisso (`fe80::1` → `fe80:`), e due indirizzi diversi condividerebbero il
contatore di §4.4-bis. Va chiesto all'ospite, non dedotto dal codice
dell'esempio.

---

## C. ⛔ Che cosa ho provato a rompere e NON sono riuscito a rompere

`PIANO.md` §0.4 e `REVIEWER.md` §6: si dichiara anche questo.

| Ingresso costruito | Perché non rompe |
|---|---|
| `CIAO` con `quante = 65535` e corpo corto | `le_str` mette `corto`, e il controllo è dentro il ciclo prima di ogni uso: `ERRORE_PROTOCOLLO`, giusto |
| lunghezza dichiarata 4 GiB e 2 MiB | controllate **prima** di qualunque allocazione (`rcp.c:1084`), come vuole §6.1 |
| lunghezza dichiarata minore del corpo dei campi | `l->corto` scatta dentro `le_str`/`le_u32`, e ogni `tratta_*` lo guarda prima di usare i valori |
| nome di capacità di 65 e di 65 535 byte | `nome_lecito` controlla `len > 64` **prima** del ciclo: nessuna lettura fuori dal buffer |
| valore di capacità di 65 535 byte | il corto circuito di `lv > 256 \|\|` impedisce a `utf8_valido` di leggere fuori (⚠ vedi R9.18: regge per l'ordine dei termini) |
| UTF-8 troncato in fondo alla stringa | `utf8_valido` pretende i byte di continuazione (`i + extra >= n`): rifiutato |
| sovralunga `0xC0 0x80`, `0xF5…`, surrogati | rifiutati dai limiti `c >= 0xC2` e `c <= 0xF4` |
| accumulo: `acc_len + len` esattamente = 64 KiB | il `memcpy` riempie fino all'ultimo byte, senza traboccare |
| `memmove` del residuo con `lung` massimo | `acc_len >= 6 + lung` è garantito dal `return` sopra: la sottrazione non passa sotto zero |
| due `ATTACCA`, due `CIAO`, due `CREDENZIALI` | fermati dalla guardia di stato di ciascun `case`: `ERRORE_PROTOCOLLO` |
| `ATTACCA` prima di `AMMESSO`, `BANCO_MARCA` prima di `SESSIONE` | idem |
| tela `1x1`, `319x240`, `7682x4320`, dispari | i limiti e la parità di §4.5 sono applicati; la **vista** non è controllata, ed è giusto (§7.1 R1.17) |
| due sessioni per lo stesso utente, **senza** silenzio di mezzo | `posto_prendi` rifiuta la seconda: `GIA_ATTIVA_REMOTA` a chi arriva, e chi c'era resta. §8.2 rispettata |
| posto lasciato due volte (`congeda` poi `rcp_libera`; `rcp_canale_chiuso` poi `rcp_chiusa_dal_client`; ogni coppia delle cinque strade) | il campo `attaccata` è azzerato in tutte e cinque, e regge: **non sono riuscito a far liberare due volte lo stesso posto** per le vie normali (⚠ ma vedi R9.19 per la via del banco) |
| posto tenuto dopo un errore fra `posto_prendi` e `S_ATTIVA` | fra i due non c'è nessun cammino d'errore; e `congeda` lo libera comunque |
| `RESPINTO` seguito da un posto occupato | `respingi()` è raggiungibile solo da `S_ATTESA_VERDETTO`, dove nessun posto è mai stato preso |
| ritardo fisso saltato per la via dell'`AMMESSO` | il ritardo è nello stesso ramo per tutt'e due gli esiti (`rcp.c:1245-1258`): §4.4-bis rispettata, ed è la riga che §11 dice che nessun altro banco vede |
| `CREDENZIALI` vuote per non muovere i contatori | gli intervalli di §4.4 le fermano prima: il buco dichiarato da R1.28 è chiuso |
| tipo con byte alto ≠ `0x00` sul canale di controllo | `rcp.c:1092`: `ERRORE_PROTOCOLLO`, §2.5 rispettata |
| `CIAO(2)` e `CIAO(0)` su `/rcp/1` | `VERSIONE_INCOMPATIBILE`: vince §2.4, ed è la lettura giusta della contraddizione di §9 |
| ordine dei campi di `BANCO_ESITO`, `ritardo` = 10 000 esatti | conformi a §7.5 |
| `sc_*` con buffer pieno | `w.pieno` impedisce di spedire un messaggio troncato; ⚠ non ho trovato nessun ingresso che lo faccia scattare — i quattro buffer sono sovradimensionati rispetto al peggiore dei corpi |

---

## D. Riepilogo per il coder

| # | Dove | Contraddice |
|---|---|---|
| R9.1 | `rcp.c:214-236` | §4.4-bis, I3, E8 |
| R9.2 | `rcp.c:1263-1271` | I2, §8.2 0x0F |
| R9.3 | `rcp.c:132-145`, `:850` | §8.2 0x0F, E1/E6 |
| R9.4 | `rcp.c:1166-1175` | §3, §6.1 |
| R9.5 | `rcp.c:1131-1141` | §7.1, §6.1, §3.1 |
| R9.6 | `rcp.c:601`, `:631` | §4.3 |
| R9.7 | `rcp.c:1142-1164` | §7.1, §5.2, §3.1 punto 1 |
| R9.8 | `rcp.c:103`, `:740`, `:1176` | §4.4 |
| R9.9 | `rcp.c:49` | §4.6 |
| R9.10 | `rcp.c:238-259` | §4.4-bis |
| R9.11 | `rcp.c:340-356`, `:620` | §6.0, §4.3 |
| R9.12 | `rcp.c:496-537` | §3 |
| R9.13 | `rcp.c:73-74`, `:1069` | §6.1 |
| R9.14 | `rcp.c:42`, `:561` | §7.5 regole 3 e 5, I6 |
| R9.15 | `rcp.c:1052-1065` | §4.4, E6 |
| R9.16 | `rcp.c:1195-1200` | §3.1 punto 1 |
| R9.17 | `01-b3-rcp-innesta.py:667-685` | E1, `REVIEWER.md` §1 domanda 4 |

⛔ **La cura è del coder, e la misura che chiude ogni `[?]` è sua.** Questo
documento non approva niente: dice dove ho trovato contraddizioni, e in §C dove
non ne ho trovate.
