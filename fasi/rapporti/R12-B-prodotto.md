# R12-B — il prodotto contro l'arbitro

*Revisione avversariale della notte del 10 agosto 2026, **lente B** del mandato
`fasi/rapporti/MANDATO-10-agosto-notte.md`. Bersaglio: tutto `src/` e `banchi/rcp/rcp.c`.
Arbitro: `RCP.md`. Non ho letto gli altri rapporti di questa notte, né chiesto a nessuno perché
una cosa sia fatta così (`PIANO.md` §0.4).*

---

## 0. Il denominatore, prima dei rilievi

Senza questo, «quindici rilievi» non è una misura.

| | |
|---|---|
| **letto per intero** | `RCP.md` (1719 righe), `src/rcp.c` (2339), `src/rcp.h`, `src/webtransport.c` (1810), `src/trasporto.c` (975), `src/main.c`, `src/pagina.c`, `src/pagina.html`, `src/certificati.c`, `src/tls.c`, `src/registro.c`, `src/autenticazione.c`, i quattro `.h` restanti, `Makefile`, `costruisci.sh`. Più `CODER.md` §2, `SPECIFICHE.md` §4 e §11.5 |
| **`src/` e `banchi/rcp/` sono la stessa cosa** | `[M]` `md5sum`: `rcp.c`, `rcp.h`, `autenticazione.c` hanno impronta identica nelle due cartelle. La copia non è divergente |
| **eseguito** | `src/rcp.c` compilato **isolato** (dipende solo dalla libc) contro un driver mio nello scratchpad, con `-Wall -Wextra`: **zero avvisi**. Sei ingressi provati, byte per byte. Non ho toccato un file del progetto |
| ⛔ **NON eseguito** | il server intero: su questa macchina mancano `ngtcp2`, `nghttp3`, `libssl-dev` e `libpam0g-dev` (`make dipendenze` dà cinque `NO`). ⚠ Quindi **tutto ciò che riguarda `trasporto.c`, `webtransport.c`, `pagina.c`, `certificati.c` è letto, non misurato**, e le marche lo dicono. Non ho usato la macchina di prova: non serviva a nessuno di questi rilievi, e §4.4-bis la banna per dodici ore a chi sbaglia tre volte |
| ⛔ **quel che questa lente NON copre** | i banchi (lente A), la coerenza dei `.md` (lente C), le cuciture fra i cinque agenti (lente D). Un rilievo che qui non c'è **non è un'assoluzione**: è fuori campo o non l'ho trovato |

**Rilievi: 15.** Otto `[R]`, di cui **due dimostrati eseguendo** `[M]`; cinque `[?]`; due minori in
coda. Tre toccano la **pagina**, che è metà del prodotto e che nessuna riga di `RCP.md` esenta dai
suoi DEVE.

---

## 1. I rilievi, in ordine di quel che costano

### B-1 ⛔ `[R]` `[M]` — la tela concessa ignora `video.misura_massima`

**DOVE**
`src/rcp.c:1413-1502` (`tratta_attacca`), e `src/rcp.c:1195-1200`: nel `CIAO` si conservano
`video.codec`, `video.profondita` e `audio.codec` — **`video.misura_massima` no**. `grep` su tutto
`src/` la trova in un posto solo, l'elenco `NOMI_NOTI` di `rcp.c:1125`: viene riconosciuta come
nome lecito e poi buttata.

**COSA CONTRADDICE**
`RCP.md` §4.5: *«La tela concessa **DEVE** rispettare `video.misura_massima` se il client l'ha
dichiarata»*. E §4.3: *«`video.misura_massima` **non** cambia la tela: è un tetto che il server
**DEVE** rispettare quando concede la tela (§4.5). Esiste perché il decodificatore di un telefono
ha limiti che il suo schermo non dichiara.»*

**COME SI DIMOSTRA** — `[M]`, eseguito, byte veri sul filo:

```
CIAO   … video.misura_massima = "1280x720" …
ATTACCA  tela 1920x1080, vista 800x600, disposizione "it"
SESSIONE che esce:  00 07 00 00 00 16 01 00 00 07 80 00 00 04 38 00 0b 73 63 …
                                          └ 0x0780 = 1920 ┘└ 0x0438 = 1080 ┘
```

Il server concede **esattamente quel che il client ha chiesto**, cioè il doppio del tetto che il
client ha dichiarato di saper decodificare. E il registro non porta una riga che nomini il tetto:
`grep` di `misura_massima` nel registro non darebbe niente.

⚠ **Il sintomo previsto da §4.3 riga `video.livello` vale identico qui**: non è un errore di rete,
è *«il browser non apre il flusso»* alla fase 2 — e la diagnosi punterà sul codificatore.
⛔ E il difetto è **muto in tutt'e due i lati**, perché la pagina manda quel campo e il server non
lo legge: è la forma esatta di §0 — *«due programmi scritti dalla stessa mano che vanno d'accordo
non confermano niente»*.

**MARCA** `[R]` `[M]`

---

### B-2 ⛔ `[R]` — niente PING: i 60 secondi della parola d'ordine sono di nuovo irraggiungibili

**DOVE**
`src/trasporto.c:31` (`IDLE_MS 30000`), `src/trasporto.c:846-866`, `src/webtransport.c:493-527` e
`src/webtransport.h` (il riquadro «che cosa è cambiato passando dall'innesto al prodotto»).
`grep -rn "keep_alive\|PING" src/` → **nessuna occorrenza**. Il commento di `trasporto.c:846-849`
lo dice a chiare lettere: *«Nell'innesto lo faceva il keep-alive, cioè byte sul filo; qui non esce
niente»*.

**COSA CONTRADDICE**
`RCP.md` §4.6, il riquadro del rilievo **R1.8**, che è normativo e comincia con un ⛔:

> ⛔ **La cura, ed è del server**: finché aspetta le credenziali, il server **DEVE** tenere viva la
> connessione con i **PING del trasporto**, che non sono un battito applicativo […] ⚠ Senza questa
> riga un'implementazione li manda e l'altra no, e la seconda **perde gli utenti che digitano
> piano**.

**COME SI DIMOSTRA**
L'utente digita una parola d'ordine lunga sulla tastiera di un telefono e ci mette 35 secondi.
Fra `ECCOMI` spedito e `CREDENZIALI` ricevute **sul filo non passa niente**: §2.2 vieta il battito
applicativo, e prima dell'attacco non c'è nessun altro canale attivo — lo dice §4.6 stessa. Al
trentesimo secondo `ngtcp2_conn_get_expiry2()` matura, `trasporto.c:854` chiama
`ngtcp2_conn_handle_expiry()`, che restituisce `NGTCP2_ERR_IDLE_CLOSE`, e `trasporto.c:864` mette
`c->morta = true`. La connessione muore **in silenzio**: nessun `CONGEDO`, nessun codice nella
chiusura della sessione, nessun motivo di §8.2. E `TETTO_CREDENZIALI` (`rcp.c:53`, 60 000 ms) non
scade **mai**, perché la sessione RCP è già stata liberata trenta secondi prima.

⚠ **`wt_battito_ns()` non è la cura, ed è il punto**: fa scorrere l'orologio *nostro* ogni 100 ms,
e per i tetti di §4.6 va benissimo — ma **non mette un byte sul filo**, e l'orologio che uccide la
connessione è quello di QUIC, che guarda i byte. `webtransport.h` presenta l'assenza del keep-alive
come un miglioramento sull'innesto, citando §2.2 (il divieto del battito applicativo): ⛔ §4.6
distingue esplicitamente le due cose — *«i PING del trasporto … non portano informazione, non hanno
una risposta da interpretare, e non creano una seconda verità sul silenzio (§2.2)»* — e il divieto
di §2.2 **non copre** i PING.

⛔ È il difetto che `RCP.md` §4.6 descrive parola per parola: *«Il banco di §11 avrebbe misurato 30
dove il documento dice 60, e il programmatore avrebbe dato la colpa al banco.»*
⚠ E B6, che secondo `rcp.c:64-67` non era ancora scritto quando il tetto di `ATTACCA` è stato
corretto, misurerà **30** sul tetto delle credenziali.

**MARCA** `[R]` — la regola è scritta con un DEVE, il codice ha l'assenza dichiarata come scelta
opposta. Non l'ho eseguito perché il server non si costruisce su questa macchina; per farlo rosso
basta un client che apre il canale, manda `CIAO` e tace 35 secondi.

---

### B-3 ⛔ `[R]` — dopo `ERRORE_PROTOCOLLO` il server rimanda al client i suoi stessi byte, e la sessione non si chiude più

**DOVE**
`src/webtransport.c:960-977` — il ramo di `smista()` per uno stream già riconosciuto `G_WT`:

```c
if (g && g->genere == G_WT) {
        if (len > 0) {
                if (stream_id == w->rcp_stream)  rcp_passa(w, dati, len);
                else                             accoda(w, stream_id, dati, len);
                conta_credito(w, stream_id, len);
        }
```

e `src/webtransport.c:1572-1583` (`wt_batti`): `if (!coda_vuota(w)) { w->chiusura_da = 0; }`.

**COSA CONTRADDICE**
§3: *«**NON DEVE** proseguire»*. §3.1 punto 3: *«**DEVE** chiudere la **sessione WebTransport** con
il codice d'errore applicativo pari al **codice del motivo** di §8.2»* — che §3.1 dichiara essere
*«quello che salva le diagnosi»*.

**COME SI DIMOSTRA**
Il client apre il canale di controllo (primo bidirezionale), poi **un secondo** stream
bidirezionale WebTransport — prefisso `40 41` + varint della sessione. `smista()` lo giudica `G_WT`
(`webtransport.c:1010`), vede `w->rcp_stream != -1` e chiama `rcp_violazione()`
(`webtransport.c:1047`) → `congeda(ERRORE_PROTOCOLLO)` → `chiudi_sessione()`, che **rimanda** la
capsula (`webtransport.c:636`). Da quell'istante in poi:

1. ogni byte che il client scrive su quel secondo stream entra in `accoda(w, stream_id, …)`, cioè
   **il server glielo rispedisce indietro** — un'eco che nessuna riga di `RCP.md` prevede, su un
   canale che §2.5 dichiara essere una violazione;
2. `coda_vuota(w)` **non torna mai vera**, quindi `wt_batti()` riazzera `chiusura_da` a ogni
   battito e la capsula `CLOSE_WEBTRANSPORT_SESSION` — cioè il punto 3 di §3.1 — **non parte mai**;
3. `conta_credito()` riapre la finestra a ogni giro, quindi il client può continuare senza fine, e
   l'inattività di 30 s non scatta perché sta scrivendo;
4. la coda non ha tetto (`coda_metti` e `bytes_aggiungi` raddoppiano senza limite): la memoria del
   processo cresce quanto il client vuole, **su una sessione già dichiarata morta**.

⚠ Nessuna guardia sullo stato di RCP protegge quel ramo: `rcp_e_finita()` esiste
(`rcp.c:1629`) e lì non è consultata.

⛔ Il caso non è di laboratorio: è la stessa condizione — *«due stream bidirezionali dal client»* —
che il codice a due righe di distanza (`webtransport.c:1021-1051`) riconosce, registra e giudica
correttamente. Il giudizio c'è; l'esecuzione del giudizio no.

**MARCA** `[R]`

---

### B-4 ⛔ `[R]` — la pagina non manda mai `CONGEDO`, e non chiude mai la sessione con un codice

**DOVE**
`src/pagina.html`, funzione `collega()`: righe 292, 293, 294, 308, 319, 320, 335, 336, 337 — ogni
ramo d'errore è un `esito(…); return;`. E riga 157: `if (lung > 1024*1024) throw new Error(…)`.
In tutto il file **non c'è** un `TIPO.CONGEDO` in scrittura, né una chiamata a `wt.close(…)`:
`TIPO.CONGEDO` compare solo in lettura.

**COSA CONTRADDICE**
§8.1: *«⛔ Chi chiude **DEVE** mandare `CONGEDO` con un motivo **prima** di chiudere la sessione
WebTransport, e **DEVE** ripetere il motivo nel codice d'errore applicativo della chiusura
(§3.1).»* E §3: *«Un'implementazione RCP che riceve qualcosa che non capisce **DEVE** chiudere la
connessione con `ERRORE_PROTOCOLLO` e scrivere nel registro che cosa non ha capito.»*
⚠ Il condizionale di §3.1 punto 2 (*«se il canale di controllo è ancora utilizzabile»*) qui **non
scusa niente**: in tutti quei rami il canale è aperto e la pagina ci ha appena letto sopra.

**COME SI DIMOSTRA**
Il server manda `SESSIONE` (`0x0007`) al posto di `ECCOMI`, cioè i sei byte
`00 07 00 00 00 00`. La pagina esegue la riga 294 —
`esito("Il server ha risposto 0x7 invece di ECCOMI.", false); return;` — e **sul filo non esce
niente**: né i byte di `CONGEDO(0x0B)`, né la capsula di chiusura con `0x0B`. La sessione
WebTransport resta aperta, e a chiuderla sarà il server dopo trenta secondi, per silenzio, con un
motivo che non ha niente a che vedere con quel che è successo.

⛔ E c'è un secondo lato, che è quello caro: `rcp.c:1795-1853` (`giudica_dopo_la_fine`) è stato
scritto — con un riquadro di venti righe e il rilievo R9.15 — **per non dare rosso alla pagina che
manda il `CONGEDO` di commiato dopo `RESPINTO`**, quello che §8.1 le impone. Quella cura protegge
un comportamento che **questa pagina non ha**: nel ramo `RESPINTO` (riga 313-317) il commento dice
*«qui chiude il server, quindi si tace»*, che è conforme; ma in tutti gli altri chiude la pagina, e
tace lo stesso.

**MARCA** `[R]`

---

### B-5 ⛔ `[R]` — la pagina non verifica la versione di `ECCOMI`

**DOVE** `src/pagina.html:295-301`.

```js
const ver = l.u16(), quante = l.u16();
…
nota("ECCOMI: versione " + ver + " — " + scelte.join(" · "));
```

`ver` viene stampato in una nota diagnostica e **mai confrontato con 1**.

**COSA CONTRADDICE**
§9: *«Il client **DEVE** verificare che la versione di `ECCOMI` sia una che sa parlare, e congedare
con `VERSIONE_INCOMPATIBILE` se non lo è — un server che risponde con una versione più alta di
quella chiesta sta sbagliando, e **accettarla in silenzio è l'indulgenza che §3 vieta**.»*

**COME SI DIMOSTRA**
Un `ECCOMI` che comincia con `00 02 00 00 00 XX 00 02 …` — versione **2** — fa proseguire la
pagina, che al messaggio dopo manda **la parola d'ordine dell'utente** a un server che parla un
protocollo che lei non conosce. Nessun `CONGEDO(0x0A)`, nessuna chiusura.

⚠ È il **caso simmetrico** di quello che B5 aveva trovato nel server: `rcp.c:1068-1092` porta un
riquadro intero sul fatto che la prima stesura *«accettava un `CIAO(2)` e rispondeva `ECCOMI(1)`»*.
La cura è stata applicata a un lato solo del filo — ed è la forma che `RCP.md` §4.4-bis chiama
*«una cura applicata in un posto solo»*, *«la forma che questo progetto paga più spesso»*.

**MARCA** `[R]`

---

### B-6 ⛔ `[R]` — `video.misura_massima` esce con i decimali

**DOVE** `src/pagina.html:278`.

```js
["video.misura_massima", screen.width * devicePixelRatio + "x" + screen.height * devicePixelRatio],
```

**COSA CONTRADDICE**
§4.3, tabella delle capacità: `video.misura_massima` = *«`LARGHEZZAxALTEZZA` che sa decodificare,
es. `3840x2160`»* — e sono **pixel**, cioè interi.

**COME SI DIMOSTRA**
Un telefono con fattore di scala **2,75** — l'esempio che questo progetto cita due volte, in
`RCP.md` §7.1 riquadro R1.17 (*«393 pixel logici valgono 1080,75 fisici»*) e in `rcp.c:1416-1425` —
ha `screen.width = 393`, `screen.height = 851`. Il valore che parte sul filo è:

```
video.misura_massima = "1080.75x2340.25"
```

Non è `LARGHEZZAxALTEZZA`. Un server che lo convalidasse come §4.3 lo definisce lo rifiuterebbe;
questo server non se ne accorge **perché quel campo non lo legge affatto** (B-1). Due difetti che
si coprono a vicenda, ed è per questo che nessun banco funzionale li vede.

**MARCA** `[R]`

---

### B-7 ⛔ `[R]` — alla chiusura del server nessuno riceve `SERVER_IN_CHIUSURA`

**DOVE**
`src/main.c:272-278` e `src/trasporto.c:960-975`. `grep -rn RCP_SERVER_IN_CHIUSURA src/*.c` →
**nessuna occorrenza**: il motivo `0x0C` è definito in `rcp.h:52` e non è emesso da nessuna riga
del prodotto.

**COSA CONTRADDICE**
§8.1 (chi chiude DEVE mandare `CONGEDO` col motivo e ripeterlo nel codice della chiusura) e §8.2
`0x0C SERVER_IN_CHIUSURA`, che esiste apposta.
`RCP.md` §4.5 dice la stessa cosa in generale: *«mai con un silenzio»*.

**COME SI DIMOSTRA**
`systemctl stop` o Ctrl-C con una sessione attiva. Il ciclo esce, `main.c:272` scrive
*«chiusura richiesta: 1 connessioni QUIC vive»*, e `trasporto_chiudi()` chiama
`connessione_libera()` in fila su tutte: nessun `CONGEDO(0x0C)` (che sarebbe
`00 0c 00 00 00 03 0c 00 00`), nessuna capsula di chiusura con `0x0C`, e nemmeno un
`CONNECTION_CLOSE` di QUIC. Il client resta ad aspettare i 30 secondi dell'inattività e mostra
*«errore di rete»*.

⛔ È alla lettera il difetto di `LEZIONI.md` §1.7 che §3.1 esiste per togliere — *«il server
scriveva "congedo il client" e il client leggeva "errore di rete" per tre fasi»* — e qui il server
non scrive nemmeno «congedo».

**MARCA** `[R]`

---

### B-8 ⛔ `[R]` `[M]` — `rcp_bannato()` e `rcp_sblocca()` non normalizzano la chiave che la loro intestazione promette di normalizzare

**DOVE**
`src/rcp.c:582-604`: tutt'e due passano per `solo_indirizzo()`, che **toglie la porta e basta**,
non per `rcp_chiave_indirizzo()`, che è la funzione scritta apposta per mettere le quadre.
Il contratto scritto in `src/rcp.h:145-150` dice invece:

> ⛔ «Questo indirizzo è bannato?» […] La chiama **chi serve la pagina in TCP** […]
> `provenienza` **può portare la porta: viene tagliata qui dentro**.

**COSA CONTRADDICE**
L'intestazione qui sopra, e §4.4-bis: *«⛔ Chi digita `192.168.0.2` al comando di sblocco **deve
arrivare alla stessa chiave**: la normalizzazione è del server, non di chi comanda. Senza, il
comando risponde «non era bannato» a ogni indirizzo, **per sempre e senza sintomo**.»*

**COME SI DIMOSTRA** — `[M]`, eseguito. Tre autenticazioni fallite da `[192.168.0.2]:100`, il ban
scatta (`⛔ BANNATO l'indirizzo [192.168.0.2] per 12 ore`), e poi:

```
rcp_bannato("192.168.0.2")   = 0     ← «non è bannato»
rcp_bannato("[192.168.0.2]") = 1
```

⛔ E la forma che restituisce **falso** è esattamente quella che `pagina.c:430-434` costruisce per
IPv4:

```c
snprintf(c->provenienza, …, da.ss_family == AF_INET6 ? "[%s]:%s" : "%s:%s", host, serv);
                                                       └── senza quadre ──┘
```

Oggi non fa danno **solo** perché `pagina.c:214` e `main.c:183` chiamano `rcp_chiave_indirizzo()`
un attimo prima — cioè perché la normalizzazione è di **chi chiama**, che è precisamente quel che
§4.4-bis vieta con un ⛔. Chiunque creda all'intestazione — un secondo comando di sblocco, un banco,
la fase 2 — ottiene «non era bannato» per ogni indirizzo, in silenzio e per sempre.

⚠ È **la stessa forma** del difetto che B5 ha già trovato una volta in questo file (la porta dentro
la chiave, `rcp.c:325-361`): *«il codice c'era, sembrava giusto, si leggeva bene, e non faceva
niente»*. La cura di allora ha messo la funzione giusta; non l'ha messa **dentro** le due funzioni
pubbliche che ne hanno bisogno.

**MARCA** `[R]` `[M]`

---

### B-9 ⛔ `[R]` — l'avviso del ban esce con una sequenza di escape JavaScript dentro l'HTML

**DOVE**
`src/pagina.c:257-262` compone la frase; `src/pagina.html:55` (`<div id="avviso" hidden>__AVVISO__</div>`)
e `:75` (`const AVVISO = "__AVVISO__";`) sono **due** luoghi in cui `sostituisci()` la mette, con
due sintassi diverse.

**COSA CONTRADDICE**
§4.4-bis, i tre punti di *«che cosa vede un indirizzo bannato»*: *«la pagina si serve lo stesso, e
mostra il rifiuto — "tentativi esauriti" […] chi è stato bannato per errore è quasi sempre il
proprietario, e deve poter capire che cosa gli è successo»*, e il punto 3 sulle ore che mancano.
E la forma **E2** di `REVIEWER.md`: due comportamenti sotto la stessa etichetta.

**COME SI DIMOSTRA**
La frase composta in `pagina.c:260` contiene, in byte, `sblocca l` seguito da **backslash-u-0-0-2-7**
e poi `indirizzo dal server.` — cioè un escape **JavaScript** per l'apostrofo (nel sorgente C è
scritto `l\\u0027indirizzo`, e il doppio backslash lascia il backslash nella stringa).
Nella stringa JS di riga 75 quell'escape diventa un apostrofo; nel `<div>` di riga 55 **no**, perché
l'HTML non conosce gli escape `\uXXXX`. Il proprietario bannato — quello per cui §4.4-bis ha scritto
tre punti normativi — legge sullo schermo, alla lettera:

> I tentativi di accesso da questo indirizzo sono esauriti. Riprova fra 11 ore e 58 minuti, oppure
> sblocca l⟨backslash⟩u0027indirizzo dal server.

*(le parentesi angolari sono mie: sullo schermo compaiono i sei caratteri
`\` `u` `0` `0` `2` `7`, uno dopo l'altro, in mezzo alla parola.)*

⚠ E le due sostituzioni sono la **stessa** stringa messa in due sintassi diverse: l'escape è giusto
per una e sbagliato per l'altra, quindi non esiste un testo che vada bene per tutt'e due — la cura è
separare i due segni, non aggiustare la frase.

⚠ E la stessa costruzione è fragile per la ragione peggiore: la stringa viene inserita **dentro una
stringa JS** senza nessuna neutralizzazione. Oggi il testo è fisso e non contiene virgolette; il
giorno in cui ci finisse dentro un dato che non decidiamo noi, quella riga è un'iniezione.

**MARCA** `[R]`

---

### B-10 ⛔ `[R]` — i datagram sono annunciati, e chi ne manda uno sparisce senza una riga

**DOVE**
`src/trasporto.c:514` (`params.max_datagram_frame_size = 65536`) e `src/webtransport.c:1347`
(`settings.h3_datagram = 1`) li **annunciano**, come §2.2 impone. Fra i `ngtcp2_callbacks` di
`src/trasporto.c:446-469` **non c'è** `recv_datagram`: `grep -rn recv_datagram src/` → niente.

**COSA CONTRADDICE**
§6.3: *«⛔ Un datagram più corto di 12 byte, o con un `tipo` diverso da `0x0401`, si **scarta
scrivendolo nel registro**»*. E §3, che chiude l'elenco delle cinque eccezioni con: *«⛔ **E ogni
tolleranza va scritta nel registro.** Una tolleranza silenziosa è indistinguibile da un difetto, ed
è precisamente l'indulgenza che questa sezione esiste per togliere.»*

**COME SI DIMOSTRA**
Il server dichiara i datagram, quindi il browser può mandarli **oggi**. Tre byte dalla pagina —
`wt.datagrams.writable.getWriter().write(new Uint8Array([0,0,0]))` — producono un frame `DATAGRAM`
che ngtcp2 consegna a un callback non registrato: il pacchetto sparisce, e nel registro non c'è
nessuna riga. La seconda eccezione dichiarata di §3 è *«si scarta»*, non *«si scarta in silenzio»*,
e la differenza è tutto il punto di quella sezione.

⚠ Non è rinviabile alla fase dell'audio: il buco esiste dal primo avvio, ed è il buco che rende
indistinguibile *«l'audio non arriva»* da *«l'audio arriva e lo butto»* il giorno in cui l'audio ci
sarà — cioè la forma di `LEZIONI.md` §2.2 citata in §5.3.

**MARCA** `[R]`

---

### B-11 ⛔ `[R]` — il servizio PAM è `login`, e la specifica dice `remotix`

**DOVE** `src/autenticazione.c:89`: `pam_start("login", utente, &conv, &pam)`.

**COSA CONTRADDICE**
`SPECIFICHE.md` §4.2, prima riga: *«**PAM locale**, servizio `remotix`, con il **ban
dell'indirizzo** dopo tre tentativi falliti.»* Non è una `[?]`: è la riga che descrive
l'autenticazione del prodotto.

**COME SI DIMOSTRA**
Il commento di `autenticazione.c:85-88` dichiara la scelta e la motiva («un servizio dedicato sarà
meglio nel prodotto»), ma la dichiarazione non toglie la contraddizione — la sposta.
E il prezzo non è di forma: su Debian `/etc/pam.d/login` è la pila della **console locale**, con
`pam_securetty`, `pam_lastlog`, `pam_motd`, `pam_limits`; un accesso di rete che passa di lì eredita
politiche pensate per un'altra cosa. ⚠ *Quale* comportamento cambi è una misura che non ho fatto e
che non è mia; la contraddizione con §4.2 è certa e sta in una riga.

⚠ E c'è una conseguenza sul banco B8, che questa notte ha misurato **2636 ms** di mediana sui
tentativi respinti (`RCP.md` §4.4-bis, riquadro): quel numero è la mediana **di `login`**, non del
servizio che il prodotto userà. Il giorno in cui il servizio diventa `remotix`, la misura va rifatta
e il `[?]` sul secondo fisso non si chiude con questa.

**MARCA** `[R]`

---

### B-12 `[?]` — §2.3: sedici stream unidirezionali **in tutto**, non «sedici disponibili in ogni momento»

**DOVE**
`src/trasporto.c:508`: `params.initial_max_streams_uni = 16;`. E in tutto `src/` **non c'è**
nessuna chiamata a `ngtcp2_conn_extend_max_streams_uni()`.

**COSA CONTRADDICE**
§2.3: *«il server **DEVE** concedere credito al client per i suoi stream unidirezionali: **almeno
16 disponibili in ogni momento**»*.

**COME SI DIMOSTRA** — in due metà, e pesano diverso.

**La prima è certa.** Appena HTTP/3 si apre, il browser apre **tre** stream unidirezionali suoi —
il canale di controllo di HTTP/3 e i due di QPACK — e restano aperti per tutta la connessione. Lo dà
per scontato il codice stesso: `webtransport.c:1335` controlla il credito speculare
(`ngtcp2_conn_get_streams_uni_left2(w->conn) < 3`) e `webtransport.c:1361-1366` apre i tre nostri.
Quindi al client restano **13** crediti, non 16, **dal primo secondo**. Il numero 16 è stato messo
come totale, mentre §2.3 lo chiede come disponibilità.

**La seconda è un sospetto.** `ngtcp2.h`, sulla funzione che qui non si chiama, dice:
*«The library does not increase maximum stream limit automatically. The exception is when a stream
is closed without `stream_open` callback being called.»* Questo codice **non** registra
`stream_open` (l'elenco dei callback di `trasporto.c:446-469` non lo contiene), quindi cade
probabilmente nell'eccezione e il rinnovo è automatico — ⚠ **ma nessuna riga del prodotto lo
dichiara**, e §2.3 è l'unico posto in cui il numero 16 è normativo. Appoggiarsi a un ramo interno di
una libreria senza scriverlo è la forma **E1**: *il parametro c'è ⇒ il credito c'è*. Se l'eccezione
non si applicasse, il quattordicesimo stream unidirezionale del client — cioè il tredicesimo
trasferimento di appunti di §5.4 — non si aprirebbe più, con il sintomo che §2.3 nomina:
*«il desktop non risponde»*.

**MARCA** `[?]` sul rinnovo; `[R]` sui tre stream mangiati dal credito, che è aritmetica e non
dipende da ngtcp2.

---

### B-13 `[?]` — la parola d'ordine in una `strdup` che il programma non azzera

**DOVE** `src/autenticazione.c:57`: `out[i].resp = strdup(r->parola ? r->parola : "");`

**COSA CONTRADDICE**
§4.4: *«la parola d'ordine sta in chiaro nella memoria di chi la riceve. **Va azzerata appena PAM ha
risposto**»*. E l'invariante **I7** di `CODER.md` §2: *«la protezione di un difetto noto sta nel
programma»*.

**COME SI DIMOSTRA**
`rcp.c` ha ricevuto una cura intera per questo (rilievo R9.8): azzera la copia locale su **ogni**
strada d'uscita (`rcp.c:1256-1350`), azzera la coda dell'accumulo dopo il `memmove`
(`rcp.c:2072-2077`), azzera `s->acc` prima di liberarlo (`rcp.c:1615-1624`) e rinuncia a `realloc`
apposta (`rcp.c:1670-1676`). ⛔ **La quarta copia — quella che va effettivamente a PAM — non è
toccata da nessuna di quelle righe**: nasce qui e viene liberata da libpam.

Che Linux-PAM sovrascriva `pam_response.resp` prima di liberarlo è vero **oggi e in
quell'implementazione**, ed è fuori dal nostro programma: è la definizione di I7 rovesciata. Nessun
commento di questo file dichiara di appoggiarsi a quel comportamento, quindi chi lo cambiasse — o
chi portasse il codice su un'altra libreria PAM — non troverebbe qui la riga da rileggere.

⚠ Lo marco `[?]` e non `[R]` perché non ho guardato la memoria del processo: è una misura, e la
misura è del coder. Il sospetto è che la cura sia stata applicata **in tre posti su quattro**.

**MARCA** `[?]`

---

### B-14 `[?]` — §6.1: il tetto di 1 MiB è del **messaggio**, e qui è del **corpo**

**DOVE** `src/rcp.c:92` (`#define MAX_MESSAGGIO (1024u * 1024u)`) e `rcp.c:1867`
(`if (lung > MAX_MESSAGGIO)`), dove `lung` è la lunghezza del **corpo**.

**COSA CONTRADDICE**
§6.1 dice *«Nessun **messaggio** DEVE superare 1 MiB»*. Che «messaggio» includa i sei byte
d'inquadratura lo stabilisce §5.4, che sceglie 1 000 000 e non 1 MiB per gli appunti proprio perché
*«il messaggio che lo porta ha sei byte di inquadratura e quattro di lunghezza, e un tetto uguale a
quello del messaggio (§6.1) renderebbe illegale il testo grande esattamente quanto il tetto»*.

**COME SI DIMOSTRA**
Un `CIAO` con `lunghezza = 0x00100000` e un elenco di capacità coerente con quella lunghezza viene
accettato: sul filo sono **1 048 582** byte, sei oltre il tetto. `MAX_ACCUMULO` (`rcp.c:112`) è
definito come `6u + MAX_MESSAGGIO`, quindi la scelta è deliberata e coerente con sé stessa — ⚠ ma
**non è dichiarata**, e le due letture danno byte diversi per lo stesso ingresso, che è quel che §0
esiste per impedire. Un validatore del filo scritto leggendo §6.1 e §5.4 marcherebbe rosso un
messaggio che questo server accetta.

**MARCA** `[?]` — sei byte non fanno danno; la divergenza silenziosa fra due letture sì.

---

### B-15 `[?]` — la coda d'uscita che non entra si **butta**, su un canale affidabile

**DOVE** `src/webtransport.c:340-346`:

```c
static void accoda(wt *w, int64_t id, const uint8_t *d, size_t n)
{
        if (!coda_metti(w, id, d, n, false))
                registro_dice(REG_WT, "⛔ memoria esaurita: … non entrano in coda", …);
}
```

**COSA CONTRADDICE**
Il riquadro di `webtransport.c:1687-1697`, scritto per la strada gemella:

> ⛔⭐ **E I BYTE NON SI BUTTANO: QUESTO È UN CANALE AFFIDABILE.** […] il messaggio dopo si saldava a
> quei byte monchi e il client leggeva un `tipo`/`lunghezza` inventato. ⛔ Era il **SERVER** a
> fabbricare la violazione del client.

**COME SI DIMOSTRA**
`bytes_aggiungi()` fallisce a metà di un `ECCOMI` per esaurimento di memoria: `manda_messaggio()` in
`rcp.c:833-848` ha già consegnato **un unico blocco** di 6+n byte, quindi o entra tutto o non entra
niente — ma nella catena `chiudi_sessione` → `manda_controllo` → `accoda` la sessione **prosegue**
lo stesso: RCP crede di aver mandato `ECCOMI`, passa a `attesa-credenziali`, e il messaggio
successivo che il server scriverà si salderà al nulla lasciato dal primo. Il client leggerà
un'inquadratura che il server non ha mai voluto scrivere. La cura di `STREAM_DATA_BLOCKED` è stata
applicata a **una** delle due strade per cui i byte si possono perdere.

**MARCA** `[?]` — serve un OOM per arrivarci, e non l'ho provocato.

---

### I due minori, per completezza

| | |
|---|---|
| ⚠ `[?]` **l'interruttore di §7.5 è una costante di compilazione** | `src/rcp.c:47`: `#define BANCO_ACCESO 0`. §7.5 regola 1 dice *«spenta salvo che l'amministratore non l'accenda **nella configurazione del server**»*. L'invariante **I6** è rispettata — è spenta di suo, e `ECCOMI` legge dall'interruttore (cura R9.14) — ⛔ ma accenderla richiede di **ricompilare**, e §7.5 la vuole in configurazione. Di fase 1, ma va detto perché il giorno in cui la configurazione ci sarà, questa riga è il posto da cambiare e non lo nomina nessun `.md` |
| ⚠ **`Makefile`** | manca la riga di dipendenza per `autenticazione.o` (le altre otto ci sono). Innocuo — quel file non include nessuna intestazione nostra — ma è l'unica delle nove a non averla, e un'omissione uniforme si legge meglio di una sola eccezione |

---

## 2. ⭐ Che cosa ho provato a rompere senza riuscirci

*Perché il prossimo non rifaccia la stessa caccia. Le voci `[M]` sono state eseguite contro
`src/rcp.c` compilato isolato.*

| Che cosa ho provato | Esito |
|---|---|
| ⛔ **un carico che dichiara 4 GiB** — `00 01 ff ff ff ff` | `[M]` **regge**. `drena()` guarda `lung > MAX_MESSAGGIO` **prima** di qualunque allocazione (`rcp.c:1865-1870`): registro *«congedo motivo=0x0b dettaglio=messaggio oltre 1 MiB»*, `CONGEDO` sul filo (30 byte), chiusura col motivo. §6.1 *«la lunghezza si controlla prima di allocare»* è onorata alla lettera, e l'accumulo cresce a richiesta invece di essere preso all'apertura |
| **un messaggio nello stato sbagliato** — `CREDENZIALI` in `attesa-ciao` | `[M]` **regge**: *«CREDENZIALI nello stato sbagliato»*, `CONGEDO(0x0B)` di 42 byte, chiusura. Lo stesso per `CIAO`, `ATTACCA`, `BANCO_MARCA` (`rcp.c:1893-1925`) |
| **il byte alto del tipo sbagliato sul controllo** — `0x0101` (input) sul canale di controllo | `[M]` **regge**: *«byte alto del tipo non e' controllo»*, `CONGEDO(0x0B)` di 44 byte. §2.5 onorata |
| ⛔ **il ban, per intero** | `[M]` **regge**. Tre `RESPINTO(0x07)` dallo stesso indirizzo dentro cinque minuti → *«⛔ BANNATO l'indirizzo [192.168.0.2] per 12 ore»*; la finestra è **scorrevole** (il ring di `falliti_t`, `rcp.c:536-548`), il nome utente **non** conta, il ban è consultato **prima** di PAM (`rcp.c:1317`) quindi il quarto tentativo con la parola giusta è rifiutato, e il rifiuto passa comunque dal **secondo fisso** (`rcp.c:2277-2290`), come §4.4-bis pretende dopo la correzione della notte del 10 |
| **il secondo fisso su `AMMESSO`** | `[M]` **regge**: `rcp_tempo` non manda `AMMESSO` prima di 1000 ms dall'arrivo di `CREDENZIALI`. §4.4-bis *«anche quando la risposta è AMMESSO»* |
| **una capacità ripetuta oltre la memoria dei nomi visti** | **regge**. I nove nomi di §4.3 stanno in una maschera di bit e si ricordano **sempre**; oltre `MAX_VISTI` sconosciuti si scrive nel registro che la rilevazione non è più possibile (`rcp.c:1094-1188`). Non ho trovato il modo di far vincere «l'ultimo» su un nome noto |
| **un `\0` in mezzo a una stringa** (`root\0nemo`, `opus\0pcm`) | **regge**: `testo_stampabile()` rifiuta i comandi C0 per le capacità e per l'utente, e per la parola c'è `strlen(parola) != lp`. Quel che arriva e quel che si giudica sono la stessa stringa |
| **UTF-8 troncato in coda** a una stringa | **regge**: `utf8_valido()` pretende che i byte di continuazione ci siano tutti (`rcp.c:773`), e rifiuta gli overlong `C0`/`C1` e i `F5..FF` |
| **una lunghezza incoerente coi campi** (`CIAO` con 4 byte di riempimento in coda) | **regge**, e **prima** degli effetti: `misura_campi()` è consultata prima dello `switch` (`rcp.c:1879-1890`), quindi non esce nessun `ECCOMI` prima del congedo. La cura R9.4 tiene |
| **la vista dispari e 1×1** in `ATTACCA` | **regge**: `tratta_attacca` non convalida la vista, ed è giusto — §7.1 *«qualunque misura da 1×1 in su è legale, dispari compresa»* |
| **il posto della sessione, preso e lasciato** su cinque strade (congedo, violazione, FIN del client, FIN del server, chiusura dal client) | **regge**: `posto_lascia()` è chiamata da `congeda`, `rcp_libera`, `rcp_canale_chiuso`, `rcp_chiusa_dal_client` e dal ramo `T_CONGEDO`, e `attaccata` impedisce di lasciarlo due volte |
| ⛔ **il percorso della sessione WebTransport** | **regge**: `apri_sessione()` confronta `strcmp(r->uri, "/rcp/1")` e risponde **404** con una riga di registro (`webtransport.c:1214-1220`), come §2.2 impone dopo R1.24. Una `CONNECT` estesa su `/rcp/2` non arriva a RCP |
| **`CIAO(2)` su `/rcp/1`** | **regge**: `VERSIONE_INCOMPATIBILE`, non `ECCOMI(1)` (`rcp.c:1088-1092`). §2.2 vince su §9, che è la lettura giusta |
| **i due certificati** | **regge**, e con un controllo positivo: `certificati_prepara()` rifiuta di partire se le due impronte coincidono (`certificati.c:364-388`); il breve è a **13 giorni** con un'ora di margine indietro — sotto il tetto di 14 di §4.1-bis — e ruota quando ne restano due; l'impronta è `X509_digest(EVP_sha256())`, cioè **SHA-256 del DER**, non della chiave pubblica; `/impronta` c'è ed è servito con `no-store`; il certificato dell'amministratore si riconosce da un file di marca e non si rigenera **nemmeno se scaduto** |
| **0-RTT** | **regge**: `SSL_CTX_set_max_early_data(ctx, 0)` a livello di **contesto** (`tls.c:105`), dove nessuna sessione lo può riaccendere, e `SSL_set_quic_tls_early_data_enabled` non compare da nessuna parte |
| **la migrazione** | **regge**: `disable_active_migration` non è toccato, e c'è una riga di commento che lo dichiara perché non sembri una dimenticanza (`trasporto.c:520-524`) |
| **la pagina servita a un indirizzo bannato** | **regge**: stato **200**, la pagina intera, e l'avviso con le ore che mancano (§4.4-bis punti 1 e 3) — ⛔ salvo il modo in cui la frase è scritta, che è B-9 |
| **l'isolamento fra origini** | **regge**: COOP, COEP e CORP su **ogni** risposta, non solo sulla pagina (`pagina.c:32-35`, e `componi()` le mette anche sui 404 e sui 500). `SPECIFICHE.md` §11.5 |
| ⭐ **il controllo positivo del segno `__IMPRONTA__`** | **regge**, ed è il controllo che questo progetto chiede a sé stesso: `pagina_apri()` rifiuta di partire se la pagina non contiene il segno (`pagina.c:531-538`), perché una sostituzione che «riesce senza fare niente» servirebbe per sempre una pagina senza impronta |
| **il file dei ban che c'è e non si legge** | **regge**: `rcp_ban_carica()` distingue `ENOENT` da ogni altro `errno` e da `ferror()`, restituisce `-1`, e `main.c:155-167` **non parte**. «Zero ban» e «non ho potuto guardare» sono due fatti diversi |
| **la parola d'ordine nel registro** | **regge** in `rcp.c`: passa da un imbuto solo, e nemmeno la sua **lunghezza** compare (cura R9.8). ⛔ Ma vedi B-13 per la copia che va a PAM |
| **avvisi del compilatore su `rcp.c`** | `[M]` `-Wall -Wextra`: **zero** |

---

## 3. Che cosa vale la pena di dire su tutto l'insieme

Tre osservazioni, e nessuna è un rilievo.

**La prima.** Otto degli otto `[R]` stanno **dove il codice non guarda**: la pagina (tre), la
chiusura del server, i datagram, i PING, il campo che nessuno legge. `rcp.c` — il modulo che i
banchi hanno preso a martellate per due giorni — regge a tutto quel che gli ho tirato addosso, e le
sue cure sono scritte con la ragione accanto. ⛔ Le contraddizioni con l'arbitro si sono spostate
**fuori** dal pezzo che i banchi guardano, ed è esattamente dove `RCP.md` §4.6, §8.1 e §6.3 mettono
i loro DEVE.

**La seconda.** Quattro rilievi su quindici — B-3, B-5, B-8, B-13 — hanno la stessa forma: **una
cura applicata in un posto solo**. `RCP.md` §4.4-bis la chiama *«la forma che questo progetto paga
più spesso»* e la dichiara commessa *«da chi scriveva la regola nuova, poche ore dopo averne curata
una uguale»*. È successo di nuovo, e stavolta nel codice.

**La terza, ed è quella che pesa.** La **pagina** porta metà dei DEVE di `RCP.md` — §3, §3.1, §8.1,
§9, §5.2, §6.2 — e in questa stesura non ne implementa nessuno dei quattro che le toccano già alla
fase 1. ⚠ Il rischio non è che sia incompleta: è che **il server sia stato collaudato contro di
lei**. §11 lo vieta con una riga sola: *«client e server NON si collaudano l'uno contro l'altro: si
collaudano contro questo documento»*.

---

*Fine. ⛔ Questo non è un verdetto verde e non è un'assoluzione: è quel che ho trovato con la lente
che mi è stata data, nel tempo che avevo, senza poter costruire il binario.*
