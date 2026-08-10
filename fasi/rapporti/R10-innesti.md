# R10 — Gli INNESTI: il C++ che vive dentro l'esempio di ngtcp2

*Revisione avversariale del 10 agosto 2026. Area: `banchi/01-b2-ngtcp2-wt-innesta.py`,
`banchi/01-b3-rcp-innesta.py`, `banchi/01-b2-quiche-wt-innesta.py` — e, dove il filo lo porta,
`banchi/01-b11-guasto-innesta.py` e `banchi/01-b11-guasto.sh`.*

Forma di ogni rilievo: `REVIEWER.md` §4, senza varianti. I `[R]` prima dei `[?]`.

⚠ **Questa revisione non è un'assoluzione di quel che non elenca.** `REVIEWER.md` §0: una review
che non trova niente in un punto è «non ho trovato niente in quel punto», non «quel punto è
giusto». In fondo, §Z, c'è l'elenco di quel che **ho provato a rompere e non sono riuscito a
rompere** — che è informazione anche quella (`PIANO.md` §0.4).

⛔ **I sei difetti già noti del mandato §3 non sono qui**: dove ne ho trovato un'altra faccia, lo
dico esplicitamente e il rilievo è sulla faccia nuova, non su quella dichiarata.

---

## R10.1 `[R]` — La capsula si **legge** dentro un frame DATA e si **scrive** fuori: le due direzioni non usano la stessa inquadratura

```
DOVE:             01-b2-ngtcp2-wt-innesta.py:369-377 (innesto «la capsula di chiusura in
                  lettura») e :659-691 (`ProtoCodec::wt_capsula`)
                  01-b3-rcp-innesta.py:646-661 (`ProtoCodec::wt_chiudi_adesso`)
                  01-b2-ngtcp2-wt-innesta.py:216-223 (la coda d'uscita nel ciclo di scrittura)
COSA CONTRADDICE: l'altro pezzo di codice — il proprio lato di lettura; e per conseguenza
                  RCP.md §3.1 punto 3 («chiudere la sessione WebTransport con il codice
                  d'errore applicativo pari al codice del motivo»)
```

**COME SI DIMOSTRA.** In lettura la capsula entra da qui:

```
  pc->wt_capsula(stream_id, {data, datalen});      // dentro http_recv_data
```

`http_recv_data` è la richiamata di **nghttp3** per il **carico utile di un frame DATA**: nghttp3
consegna lì solo byte che ha già estratto da `DATA`. Se il client non incapsulasse le capsule in
frame `DATA`, nghttp3 leggerebbe `0x68 0x43` come un tipo di frame HTTP/3 sconosciuto, lo
salterebbe, e `wt_capsula` non verrebbe **mai** chiamata con niente. Che sia stata chiamata
davvero è quel che `01-b2-ngtcp2-wt-innesta.py:364-367` dichiara di aver misurato su Firefox.
⇒ **il client incapsula in `DATA`, e il codice di lettura lo dà per acquisito.**

In scrittura, la stessa capsula esce da un'altra strada:

```
  wt_uscita_.push_back(WtUscita{wt_sessione_, {0x68,0x43,4,0,0,0,motivo}, 0, true});
```

e la coda `wt_uscita_` viene consegnata **direttamente a `ngtcp2_conn_writev_stream`**
(`01-b2-...:216-223`), cioè **saltando nghttp3** — quindi **senza intestazione `DATA`**. I sette
byte finiscono grezzi sullo stream della CONNECT.

Il client li legge con il proprio strato HTTP/3, non con quello WebTransport:
`0x68` ha i due bit alti a `01` ⇒ intero variabile di 2 byte ⇒ tipo di frame
`((0x68 & 0x3f) << 8) | 0x43 = 0x2843`; lunghezza `0x04`; corpo `00 00 00 <motivo>`. **`0x2843`
non è un tipo di frame HTTP/3 noto**, e RFC 9114 §9 impone di ignorarlo. La pagina quindi non
vede nessuna capsula: vede solo il **FIN** che arriva subito dopo, e un FIN sullo stream della
CONNECT senza `CLOSE_WEBTRANSPORT_SESSION` chiude la sessione con **codice 0**.

⭐ **E il sintomo è già a verbale**: il mandato §3 punto 6 registra `congedo:0x00` invece di
`0x0b`, e il mandato dichiara che *«non è dimostrato che [le due cause curate] fossero le sole»*.
`0x00` è **esattamente** il codice che questa strada produce, in ogni giro, non uno su cinque.
Le due spiegazioni sono distinguibili con una misura: far chiudere il server con `0x0b`
**senza** nessuna corsa (nessun `RESPINTO` in coda) e leggere `wt.closed` dalla pagina.

⛔ Le due direzioni non possono essere tutt'e due giuste: o le capsule stanno dentro `DATA` — e
allora la scrittura è muta — o non ci stanno, e allora la lettura non riceve mai niente e il
punto 3 di §3.1 non ha mai funzionato in nessuna delle due direzioni.

`MARCA: [R]`

---

## R10.2 `[R]` — `rcp_canale_chiuso()` è raggiungibile **solo sul server che mente**

```
DOVE:             01-b3-rcp-innesta.py:357-373 (innesto «il posto che si libera quando chiude il
                  server»), condizione `if (u.fin && rcp_ && u.stream_id == rcp_stream_)`
COSA CONTRADDICE: il commento che gli sta sopra (:342-356), il commento di
                  `banchi/rcp/rcp.c:1206-1220`, e `fasi/01-filo-nudo.md` §B11 — che dichiarano
                  quella riga la **cura** del difetto «il posto non si libera con Chrome».
                  E LEZIONI.md §1.3: un banco che non riproduce il difetto non assolve il codice.
```

**COME SI DIMOSTRA.** `u.fin` è vero solo per gli elementi di `wt_uscita_` costruiti col quarto
campo a `true`. In tutto il progetto ci sono **due** costruzioni di `WtUscita`:

| dove | stream | `fin` |
|---|---|---|
| `01-b2-...:697-700` (`wt_accoda`), poi `01-b3-...:325-327` | qualunque | **`false`**, sempre |
| `01-b3-...:656-657` (`wt_chiudi_adesso`) | **`wt_sessione_`** | `true` |

`wt_sessione_` è lo stream della **CONNECT estesa** (`01-b2-...:796`); `rcp_stream_` è il primo
stream **bidirezionale WebTransport dentro** la sessione (`01-b3-...:421-422`). Sono due stream
diversi per costruzione — lo stream della CONNECT viene marcato `wt_nonwt_` in `wt_smista` e non
può mai diventare `rcp_stream_`. Quindi `u.fin && u.stream_id == rcp_stream_` è **sempre falso**.

L'unica riga di tutto l'albero che mette `fin=true` su `rcp_stream_` è:

```
banchi/01-b11-guasto-innesta.py:228
    wt_uscita_.push_back(WtUscita{rcp_stream_, {}, 0, true});
```

cioè il guasto **`fin-sul-controllo`**, che esiste solo quando è innestato
`01-b11-guasto-innesta.py`, cioè **solo sul server che mente di proposito** e che
`01-b11-guasto.sh spegni` è scritto per far sparire.

⇒ Sul server vero `rcp_canale_chiuso()` non viene chiamata **mai**. La cura del difetto trovato
da B11 con Chrome vive dentro il banco che l'ha trovato, e nel prodotto non c'è. ⛔ È la forma
E10 letta al contrario: non una prova verde sul client sbagliato, ma **una cura verde solo sul
server sbagliato**.

`MARCA: [R]`

---

## R10.3 `[R]` — Il FIN del client sul canale di controllo non lo guarda nessuno

```
DOVE:             01-b2-ngtcp2-wt-innesta.py:110-111 — la firma
                  `WtEsito wt_smista(int64_t, std::span<const uint8_t>, std::vector<uint8_t>&)`
                  01-b2-...:702-765 (corpo), 01-b3-...:189-208 (`wt_smista_uni`)
COSA CONTRADDICE: RCP.md §4.2 — «un FIN su quello stream, **da una qualunque delle due parti**,
                  chiude la sessione. Chi lo riceve **DEVE** considerarla finita»
```

**COME SI DIMOSTRA.** `wt_smista` **non ha un parametro `fin`**: l'informazione non le arriva, e
non c'è modo di farla arrivare senza cambiarne la firma. Per gli stream già riconosciuti
(`01-b2-...:715-726`) la funzione ritorna `MIO`, e con `MIO` l'innesto in lettura
(`01-b2-...:342-346`) fa `return {}` **prima** di `nghttp3_conn_read_stream2`: nemmeno nghttp3
vede il FIN.

L'unica strada rimasta per accorgersene è `on_stream_close` (`01-b3-...:280-319`). Ma
`on_stream_close` scatta quando lo stream è chiuso **nelle due direzioni**, e il server sul
canale di controllo non manda mai il FIN (R10.2: l'unico `fin=true` è del guasto B11, e sta su un
altro stream).

**Ingresso concreto**: la pagina chiude la parte scrivente del canale di controllo
(`writable.close()` → FIN) e **tiene aperta la sessione WebTransport e la connessione QUIC**.
Risultato: nessuna riga «la sessione è finita», nessun `rcp_libera()`, il posto del registro
resta occupato finché non muore la connessione — e un browser la tiene viva. ⛔ È **la stessa
forma** del difetto che B11 ha appena curato nella direzione opposta
(`fasi/01-filo-nudo.md`:973-977), nell'unica direzione che nessuno ha percorso.

`MARCA: [R]`

---

## R10.4 `[R]` — `STREAM_DATA_BLOCKED` butta un buffer **già scritto a metà**: lo stream affidabile si sfalda

```
DOVE:             01-b2-ngtcp2-wt-innesta.py:283-296 (innesto «i due rami del blocco»)
COSA CONTRADDICE: RCP.md §6.1 («`lunghezza` DEVE essere il numero esatto dei byte del corpo»),
                  e l'altro pezzo di codice — `wt_avanza` (:258-268), che per la **stessa** coda
                  gestisce la scrittura parziale con `u.off` invece di buttare
```

**COME SI DIMOSTRA.**

```cpp
      case NGTCP2_ERR_STREAM_DATA_BLOCKED:
        if (wt_mio) {
          std::println(stderr, "REMOTIX B2: stream {} bloccato, byte buttati", stream_id);
          wt_uscita_.pop_front();
          continue;
        }
```

`pop_front()` scarta **tutto l'elemento**, compreso il caso in cui `u.off > 0`, cioè quando una
parte di quel buffer è **già uscita sul filo**. L'elemento successivo per lo stesso stream viene
poi scritto **attaccato** ai byte parziali.

**Ingresso concreto**: un client che annuncia `initial_max_stream_data_bidi_remote` piccolo (per
esempio 4 KiB) e non legge dal canale di controllo. Il server accoda `SESSIONE` (o un `CONGEDO`);
ngtcp2 ne scrive i primi *k* byte, poi il credito finisce e il ramo scatta. Sul filo il client
riceve `k` byte di un messaggio e poi la testa del messaggio dopo, cioè un `tipo`/`lunghezza`
inventato — che `RCP.md` §3 gli impone di trattare come `ERRORE_PROTOCOLLO`. Il server ha
prodotto lui la violazione, e nel registro c'è scritto «byte buttati», non «ho corrotto lo
stream».

⛔ E `STREAM_DATA_BLOCKED` **non è un guasto**: è la condizione normale e transitoria che si
risolve col primo `MAX_STREAM_DATA`. Dirlo nel registro (`E SI DICE`, dice il commento) non
rende lecito troncare uno stream affidabile: il commento descrive la perdita, non la rende
recuperabile, e nessuno avvisa RCP che un messaggio non è partito. È I1 letta sul filo — la
degradazione c'è, ed è silenziosa **per chi la subisce**.

`MARCA: [R]`

---

## R10.5 `[R]` — Una scrittura parziale del SETTINGS riscritto **uccide la connessione**, mentre la stessa scrittura parziale sulla coda nostra viene gestita

```
DOVE:             01-b2-ngtcp2-wt-innesta.py:242-256 (`wt_conta`) e :186-192 (la guardia
                  `wt_guasto_` in cima al ciclo)
COSA CONTRADDICE: l'invariante I1 — «ogni percorso che, quando la linea non porta, **chiuda la
                  connessione** invece di continuare»; e l'altro pezzo di codice, `wt_avanza`
                  (:258-268), che per la coda `wt_uscita_` avanza `u.off` e riprova
```

**COME SI DIMOSTRA.**

```cpp
      if (c != wt_impbuf_len_) {
        std::println(stderr, "REMOTIX B2: impostazioni scritte a meta' ({} di {})", c, wt_impbuf_len_);
        wt_guasto_ = true;
        return 0;
      }
```

e in cima al ciclo `if (wt_guasto_) { return NGTCP2_ERR_CALLBACK_FAILURE; }`, che nel loro
esempio è fatale.

`ndatalen` **minore della lunghezza offerta è un esito normale** di
`ngtcp2_conn_writev_stream`: ngtcp2 mette nello stream frame quel che avanza nel pacchetto.

**Ingresso concreto**: il SETTINGS riscritto è ~24 byte (i ~10 di nghttp3 più i 14 nostri, cfr.
:610-615); viene offerto nella prima passata di scrittura dopo la stretta di mano, cioè nel volo
che porta anche `HANDSHAKE_DONE`, uno o più `NEW_CONNECTION_ID` e l'eventuale `NEW_TOKEN`. Un
client che annunci un `max_udp_payload_size` vicino al minimo (1200) e una connection id di 20
byte lascia in quel pacchetto meno di 24 byte per lo stream di controllo. `c` vale allora, per
dire, 12, e **la connessione muore**, con un registro che dice «impostazioni scritte a metà» e
nient'altro. I 12 byte mancanti sarebbero usciti alla passata dopo: lo si fa già, dieci righe
sotto, per `wt_uscita_`.

⚠ E lo stesso modulo ha **due politiche diverse** per la stessa classe di guasto: qui la
connessione muore; in `wt_riscrivi_impostazioni` (R10.13) davanti a un SETTINGS che non riconosce
tira dritto e serve un server senza WebTransport.

`MARCA: [R]`

---

## R10.6 `[R]` — `wt_capsbuf_` non ha un tetto, e `lung` non viene mai controllata

```
DOVE:             01-b2-ngtcp2-wt-innesta.py:659-691 (`ProtoCodec::wt_capsula`), righe 663 e 672
COSA CONTRADDICE: RCP.md §6.1 — «⛔ **E la lunghezza si controlla prima di allocare.** Un
                  ricevente che alloca `lunghezza` byte e poi verifica ha già regalato un
                  megabyte a chiunque sappia scrivere sei byte» — e §6.1, «Nessun messaggio DEVE
                  superare 1 MiB»
```

**COME SI DIMOSTRA.**

```cpp
  wt_capsbuf_.insert(wt_capsbuf_.end(), dati.begin(), dati.end());   // :663 — nessun tetto
  ...
  if (b == 0 || wt_capsbuf_.size() < a + b + lung) {
    return;                                                          // :672 — si aspetta, e basta
  }
```

**Ingresso concreto**: la pagina, sullo stream della CONNECT, manda **due byte e mezzo**: tipo di
capsula `0x00` (una capsula sconosciuta, che RFC 9297 §3.2 dice di ignorare) e lunghezza
`0xBF FF FF FF FF FF FF FF` = 2⁶²−1. Poi manda dati, all'infinito. `wt_capsula` non riconosce mai
una capsula intera, quindi **non chiama mai `erase`**, e `wt_capsbuf_` cresce di ogni byte che
arriva. Nel frattempo `pc->http_consume(stream_id, datalen)` (`:375`) continua ad allargare il
credito, quindi il client può spedire senza fine: **la memoria del server cresce quanto il client
vuole**, su una connessione che non ha ancora superato la stretta di mano di RCP.

⚠ E la variante non ostile è altrettanto vera: una capsula legittima ma sconosciuta di 512 MiB
viene **interamente bufferizzata** prima di essere scartata; RFC 9297 permette di saltarla senza
tenerla.

`MARCA: [R]`

---

## R10.7 `[R]` — Il codice di chiusura viene troncato da 32 a 8 bit, e lo `0` che §3.1 vieta viene accettato

```
DOVE:             01-b2-ngtcp2-wt-innesta.py:676-686 (`wt_capsula`), riga 686
                  `wt_chiusa_dal_client(static_cast<uint8_t>(codice));`
                  01-b3-rcp-innesta.py:388-404 (`wt_chiusa_dal_client`)
COSA CONTRADDICE: RCP.md §3.1 — «⚠ Il codice **0** significa "chiusura senza motivo" e **NON
                  DEVE** essere usato: ogni chiusura ha un motivo di §8.2»; e RCP.md §3, la
                  regola di rigore («un campo fuori intervallo»)
```

**COME SI DIMOSTRA.** `codice` è ricomposto correttamente su 32 bit (:677-680), stampato su 32
bit (:684), e poi **troncato al byte basso** prima di essere consegnato a RCP. Nessuno controlla
che il valore risultante sia uno dei motivi di §8.2.

**Ingresso concreto n. 1** — la pagina chiama `close({closeCode: 0x0100})`. Il registro stampa
`codice 0x100`; RCP riceve `0x00`; `rcp_chiusa_dal_client` (`banchi/rcp/rcp.c:995`) scrive a
verbale «motivo 0x00» e lascia il posto. Un motivo che §3.1 vieta esplicitamente entra nel
registro come se fosse regolare, e i due registri della **stessa** chiusura si contraddicono a
distanza di due righe.

**Ingresso concreto n. 2** — la pagina chiama `close()` senza codice: il codice è `0`,
`wt_chiusa_dal_client(0)` viene chiamata, e nessuno rileva la violazione di §3.1. È l'indulgenza
che `RCP.md` §3 e `REVIEWER.md` §5 («non supplisci») esistono per togliere: il caso è
indistinguibile da una chiusura regolare.

⚠ E si intreccia con R10.1: quando è **il server** a chiudere, la pagina legge `0` per un'altra
ragione ancora. Tre strade diverse producono lo stesso `0x00`, e il registro non le distingue.

`MARCA: [R]`

---

## R10.8 `[R]` — I byte dei canali **leciti** `0x01` (input) e `0x02` (appunti) vengono buttati, con un commento che dice il contrario

```
DOVE:             01-b3-rcp-innesta.py:529-537 (`wt_smista_uni`, il ramo
                  `if (wt_uni_.contains(stream_id))`) e :577-579 (i due `case` senza guasto)
COSA CONTRADDICE: il commento immediatamente sopra («la sessione e' gia' caduta»), che è falso
                  per i due canali leciti; e RCP.md §2.5, che dichiara `0x01` **«l'unico
                  unidirezionale che il client apre»** e `0x02` legale
```

**COME SI DIMOSTRA.**

```cpp
  if (wt_uni_.contains(stream_id)) {
    // Gia' giudicato.  I byte che continuano ad arrivare si contano nel
    // credito e non si guardano: la sessione e' gia' caduta.
    ...
    return WtEsito::MIO;
  }
```

Ma `wt_uni_[stream_id] = true` viene scritto a :559 **per tutti e cinque i valori di `canale`**,
prima dello `switch` che decide se c'è un guasto — quindi anche per `0x01` e `0x02`, dove
`guasto == nullptr` e nella riga di registro compare **«lecito»**.

**Ingresso concreto**: un client conforme apre, dopo `SESSIONE`, l'unico stream unidirezionale
che §2.5 gli concede — canale `0x01`, input — e ci manda i messaggi di §7.3. Il server scrive
«lecito», poi **scarta ogni byte successivo, per sempre, senza una riga di registro**. Il
commento afferma uno stato («la sessione è già caduta») che in quel ramo non è vero, e la caduta
non c'è.

⛔ È E3 (una funzione fa più — qui meno — di quel che il nome e il commento dicono) più il
divieto di `REVIEWER.md` §5: l'omissione è supplita in silenzio dal fatto che in questa fase
l'input non è ancora collaudato, ed è precisamente il caso in cui un difetto resta invisibile
finché non produce un sintomo lontano.

`MARCA: [R]`

---

## R10.9 `[R]` — `01-b3-rcp-innesta.py` **scrive tre file prima** di controllare gli appigli, e poi dichiara «non si scrive niente»

```
DOVE:             01-b3-rcp-innesta.py:690-692 (la copia) contro :733-735 (il messaggio)
COSA CONTRADDICE: sé stesso — il messaggio «non si scrive niente» è falso; e LEZIONI.md §1.9,
                  perché l'esito d'errore lascia l'albero in uno stato che l'esito d'errore nega
```

**COME SI DIMOSTRA.**

```python
    for f in FILE_NOSTRI:                                   # :690  ← già scritto
        shutil.copyfile(os.path.join(SORGENTI, f), os.path.join(ESEMPI, f))
    ...
    if guasti:
        print(f"\n   ⛔ {guasti} appigli non sono UNO: non si scrive niente.")   # :734
        return 2
```

**Ingresso concreto**: si lancia `01-b3-rcp-innesta.py` su un albero **senza** l'innesto di B2
(per esempio subito dopo `01-b2-ngtcp2-wt-innesta.py --togli`). Gli appigli di :81-108, :131-151,
:191-206, :210-220, :322-341, :358-372 vengono tutti da testo che ha introdotto B2: contano tutti
`0`. Lo script stampa `⛔ ... non si scrive niente` ed esce con 2 — **mentre
`examples/rcp.c`, `examples/rcp.h`, `examples/autenticazione.c` sono già stati scritti**, e
`--togli` li toglie ma nessuno lo sa.

⚠ E lo script **non dice** che manca B2: non cerca mai la marca `REMOTIX B2`, e l'unica diagnosi
disponibile è quella di B2 (`L'esempio di ngtcp2 e' cambiato`), che qui sarebbe sbagliata. È E6 —
il mittente dedotto invece che chiesto — su un denominatore che è la sola cosa che rende onesto
tutto il resto.

`MARCA: [R]`

---

## R10.10 `[R]` — Nessuno dei due `--togli` verifica di aver tolto, e chi li chiama getta via anche lo stato d'uscita

```
DOVE:             01-b2-ngtcp2-wt-innesta.py:819-824
                  01-b3-rcp-innesta.py:667-678
                  01-b11-guasto.sh:45-68 (`ricostruisci`)
COSA CONTRADDICE: LEZIONI.md §1.9 quarta regola (una misura che può dire «zero» deve poter dire
                  «sono fallita»), REVIEWER.md §1 domande 4 e 5 (lo zero distinto dal
                  fallimento, il controllo positivo); e l'altro pezzo di codice —
                  `01-b11-guasto.sh:102-109`, che per la **propria** marca fa esattamente il
                  controllo che qui manca
```

**COME SI DIMOSTRA.** `01-b11-guasto.sh` sa come si fa, e lo scrive nella propria intestazione
(:17-19): dopo `spegni` conta `REMOTIX B11 GUASTO` nel sorgente e grida se ne resta. Ma:

1. `01-b2-...:819-824` esegue `git checkout -- examples` e restituisce il codice d'uscita di git
   **senza mai rileggere il file per vedere se `REMOTIX B2` è sparita**;
2. `01-b3-...:667-678` non controlla niente e **restituisce `0` sempre** (`return 0` a :678),
   qualunque cosa sia successa;
3. `ricostruisci()` (`01-b11-guasto.sh:47-50`) lancia i quattro comandi con `> /dev/null` e
   **non guarda nessuno dei quattro stati d'uscita**: il `2` di «non si scrive niente» finisce
   nel nulla insieme alle righe `NO ... appiglio trovato 0 volta/e`.

**Ingresso concreto**: si aggiorna ngtcp2 e un solo appiglio di B2 sparisce.
`01-b2-ngtcp2-wt-innesta.py` fa il suo mestiere — stampa `NO`, esce con 2, non scrive niente.
`ricostruisci` non lo vede; `ninja` compila **l'esempio di ngtcp2 senza innesti**, e riesce.
Poi `spegni` esegue il suo controllo:

```sh
QUANTI=$(... grep -c 'REMOTIX B11 GUASTO' $SORG || true ...)
if [ "${QUANTI:-0}" -eq 0 ]; then ok "⭐ nessuna traccia di B11 nel sorgente: il server e' quello vero"
```

`0` occorrenze ⇒ **«il server è quello vero»**, su un binario che non ha né WebTransport né RCP.
⛔ Lo zero e il fallimento totale hanno lo stesso aspetto, ed è la quarta regola di §1.9 nel punto
in cui il progetto se l'era scritta per un'altra marca. Il controllo positivo che manca è di una
riga: contare anche `REMOTIX B2` e `REMOTIX B3` e pretendere che ci **siano**.

⚠ Questa è la faccia **accanto** al difetto noto n. 1 del mandato, non il difetto noto: lì il
guasto è che `--togli` non toglie; qui è che **nessuno lo controlla**, in tutt'e due gli script
e nel chiamante, e che l'assenza della marca giusta viene letta come salute.

`MARCA: [R]`

---

## R10.11 `[R]` — Il canale di controllo è eletto per **ordine d'arrivo**, non per numero di stream — e la stessa scrittura dice due cose opposte su che cosa siano gli altri stream

```
DOVE:             01-b3-rcp-innesta.py:153-181 (innesto «il primo stream è il controllo»)
COSA CONTRADDICE: RCP.md §2.5 e §4.2 — «il **primo** stream bidirezionale della sessione»; e il
                  commento fratello a :139-141 dello stesso file, «sugli altri stream resta
                  l'eco di B2, che serve al banco del trasporto». Forma E4.
```

**COME SI DIMOSTRA.** L'elezione avviene dentro `wt_smista`, nel punto in cui uno stream viene
**riconosciuto**, cioè quando arrivano i suoi primi due byte:

```cpp
    if (rcp_stream_ == -1) {
      rcp_avvia(stream_id);
    } else {
      ... rcp_violazione(rcp_, "un secondo stream bidirezionale dal client (§2.5)");
    }
```

«Il primo riconosciuto» e «il primo aperto» sono due cose diverse: i due stream viaggiano in
pacchetti diversi, e la rete li può consegnare in qualunque ordine. **Ingresso concreto**: il
client apre lo stream 4 (controllo) e poi lo stream 8; il pacchetto con i primi byte dello
stream 8 arriva per primo (riordino, o semplicemente perdita e ritrasmissione del primo). Lo
stream 8 diventa il canale di controllo, e lo stream 4 — quello **giusto** — riceve
`rcp_violazione` e la sessione muore. Nel registro c'è scritto «secondo stream bidirezionale»,
cioè una diagnosi che punta sul client: è E4 alla lettera — la permuta è punita con un errore che
non dice «hai sbagliato l'ordine», e qui l'ordine non l'ha sbagliato nessuno.

⚠ E la seconda contraddizione è interna alla stessa lista di innesti: :139-141 dichiara che
«sugli altri stream resta **l'eco di B2**, che serve al banco del trasporto», mentre :164-179
dichiara che ogni altro stream bidirezionale è **una violazione che congeda**. Le due righe
descrivono due server diversi, e con B3 innestato il banco del trasporto di B2 non può più aprire
un secondo stream senza far cadere la sessione.

`MARCA: [R]`

---

## R10.12 `[R]` — Il conto delle «righe nostre» si fa con **tre regole diverse** in tre script, e una di esse conta come commento del C++ vero

```
DOVE:             01-b2-ngtcp2-wt-innesta.py:877-888
                  01-b3-rcp-innesta.py:744-751
                  01-b2-quiche-wt-innesta.py:135-142
COSA CONTRADDICE: sé stessi — la stessa grandezza («righe di CODICE») è definita in tre modi
                  incompatibili; e il commento di 01-b2-...:867-872, che presenta il numero come
                  un dato e non come una stima
```

**COME SI DIMOSTRA.** Le tre regole di classificazione, sullo **stesso** insieme di righe aggiunte:

| script | «commento» è una riga che, tolti gli spazi, comincia per |
|---|---|
| `01-b2-ngtcp2-wt-innesta.py:884` | `//` |
| `01-b3-rcp-innesta.py:745` | `//` **oppure** `/*` **oppure** `*` |
| `01-b2-quiche-wt-innesta.py:137` | `*` **oppure** `/*` (mai `//`) |

La regola di B3 classifica come commento delle righe di C++ che stanno **nel corpo innestato da
B2**, in `01-b2-ngtcp2-wt-innesta.py`:

```
:522    *v = src[0] & 0x3f;
:524    *v = (*v << 8) | src[i];
```

Sono due dereferenziazioni, e cominciano per `*`. ⇒ **il numero «di codice» stampato da B3 è
strettamente minore di quello che B2 stamperebbe sulle stesse righe**, e i due si presentano con
la stessa etichetta.

E gli arbitri riportano già due coppie diverse per la stessa misura:

| dove | righe aggiunte | di codice |
|---|---|---|
| `DECISIONI.md`:1892 e `fasi/01-filo-nudo.md`:601 | 456 | **329** |
| `README.md`:23 e :89 | 482 | **333** |
| `01-b2-quiche-wt-innesta.py`:141 (il paragone di §6.4) | — | **329** |

Il mandato §3 punto 2 dichiara **482/333** invecchiato; non dichiara che ne circola un secondo,
**456/329**, ed è quello su cui `DECISIONI.md` §6.4 ha **chiuso la decisione** (:1610). Due numeri
diversi per la stessa grandezza, in due arbitri, e uno dei due nella riga che sceglie la libreria.

⚠ Due difetti minori dello stesso conto, che valgono per tutt'e tre gli script:
- si contano **solo le righe `+`**: una riga *modificata* (per esempio
  `SSL_set_early_data_enabled(ssl_, 1)` → `0`, `01-b2-...:464-478`) entra come riga **aggiunta**,
  quindi «righe aggiunte» non è «righe nostre»;
- il commento di `01-b2-...:18-19` afferma «*`git diff --stat` dice **esattamente** quante righe
  sono nostre. Non è una stima*», ma `git diff -- examples` misura **tutto** quel che è cambiato
  in quella cartella, da chiunque — non ha modo di attribuire una riga. È E5: un fatto che era
  una deduzione, scritta accanto al numero che la decisione ha usato.

E `01-b3-...:747-751` stampa l'etichetta `banchi/rcp/<file>` mentre legge
`SORGENTI = /srv/src/rcp/<file>` (:40): il conto è vero, il nome del posto no.

`MARCA: [R]`

---

## R10.13 `[R]` — `--togli` di B2 smonta **anche B3**, in silenzio, e ne annuncia un altro

```
DOVE:             01-b2-ngtcp2-wt-innesta.py:819-824; 01-b3-rcp-innesta.py:668 e :676-677
COSA CONTRADDICE: E3 — una funzione fa più di quel che dice il nome; e le due righe stampate,
                  che descrivono due comportamenti che il codice non ha
```

**COME SI DIMOSTRA.**

- `01-b2-...:820` stampa `== Si rimette l'esempio com'era` e poi esegue
  `git -C /srv/src/b2/ngtcp2 checkout -- examples`: **tutta la cartella**. Se B3 è innestato, i
  suoi fili spariscono insieme a quelli di B2, e lo script non lo dice. Se qualcuno ha una
  modifica legittima sotto `examples/` — un altro banco, una prova a mano — sparisce anche
  quella. `git checkout` inoltre **non** rimuove i file non tracciati, quindi `examples/rcp.c`,
  `rcp.h`, `autenticazione.c` restano lì, orfani, dopo che «l'esempio è com'era».
- `01-b3-...:668` stampa `(resta l'innesto di B2)`. È vero per `CMakeLists.txt`; è **falso** per
  `http3_server_proto_codec.cc` e `.h`, dove resta anche tutto l'innesto **di B3** (difetto noto
  n. 1). Ma la faccia nuova è un'altra: lo stato che quel `--togli` lascia **non compila**. Il
  `.cc` continua a contenere `#include "rcp.h"` (`:52-59`) e le chiamate `rcp_apri`, `rcp_ricevi`,
  `rcp_tempo`, `rcp_libera`; `examples/rcp.h` è stato cancellato (`:672-675`) e `CMakeLists.txt`
  è tornato senza `rcp.c`, `autenticazione.c` e senza `pam`. **Ingresso concreto**: `b3 --togli`
  e poi `ninja bsslserver` ⇒ errore di compilazione su un file che nessuno ha toccato, con exit
  status 0 stampato dallo script che ha prodotto lo stato.

`MARCA: [R]`

---

## R10.14 `[?]` — La chiusura della sessione può restare **armata per sempre** quando la violazione arriva prima del canale di controllo

```
DOVE:             01-b3-rcp-innesta.py:588-601 (`wt_smista_uni`, il ramo `else` con
                  `wt_chiudi_sessione(0x0B)`), contro :236-251 (l'attesa delle cinque passate) e
                  :470-479 (l'unico punto che arma il keep-alive)
COSA CONTRADDICE: RCP.md §3.1 punto 3 — la chiusura della sessione col motivo è un **DEVE**
```

**COME SI DIMOSTRA (ipotesi, va misurata).** Il keep-alive di QUIC viene armato **solo** dentro
`rcp_passa` (:470-479), che ritorna subito se `rcp_` è nullo (:445-447). Nel ramo di :592-600
`rcp_` è nullo per costruzione — è il caso «nessun canale di controllo ancora aperto». Quindi
`wt_chiusura_` viene armato **senza che nessun battito sia stato acceso**.

L'invio dipende poi da `wt_chiusura_attesa_ >= 5`, cioè da **cinque ulteriori passate del
percorso di scrittura** (:245-250).

**Ingresso concreto**: il client apre la sessione WebTransport, apre **subito** uno stream
unidirezionale di canale `0x03` (video, verso sbagliato) e poi **tace**. Il server rileva la
violazione, arma la chiusura, e da quel momento non ha più niente da spedire né un timer
applicativo: le passate del ciclo di scrittura restano quelle indotte dai timer di ritrasmissione
di ngtcp2, che si esauriscono appena tutto è confermato. Se sono meno di cinque, la capsula non
parte mai e la sessione resta aperta fino al `max_idle_timeout` — cioè §3.1 punto 3 non viene
eseguito, in un caso che l'innesto ha scritto apposta per eseguirlo.

⚠ È `[?]` perché quante passate produca ngtcp2 in quella finestra si sa solo misurandolo. Il
banco che lo misura è a portata: B5 con la violazione mandata **prima** del canale di controllo.

`MARCA: [?]`

---

## R10.15 `[?]` — L'attesa delle cinque passate si verifica **dal lato che invia**, e il suo stesso commento lo ammette

```
DOVE:             01-b3-rcp-innesta.py:236-251
COSA CONTRADDICE: LEZIONI.md §1.7 e la forma E7 — «il registro dice "ho chiamato la funzione",
                  non "il byte è arrivato"»; e RCP.md §8.1, «si dice, e si **verifica dal lato
                  che riceve**»
```

**COME SI DIMOSTRA.** Il commento scrive la regola giusta e poi ne usa una sostitutiva:

```
    // ⚠ Non basta che la coda sia vuota UNA VOLTA: «consegnato a
    //   ngtcp2» non e' «uscito sul filo».  Si aspettano cinque passate
```

Cinque passate di `write_streams` non sono «uscito sul filo» più di quanto lo sia una: sono la
stessa grandezza contata cinque volte, dal lato del mittente. Il criterio che il commento cerca
esiste ed è dall'altro lato del contatore — i byte **confermati** dal peer — ed è quel che ngtcp2
sa già.

**Ingresso concreto**: una linea con 300 ms di ritardo e una perdita sul volo che porta il
`CONGEDO`. Le cinque passate scadono in ~500 ms (keep-alive a 100 ms) mentre i byte del `CONGEDO`
sono ancora in ritrasmissione; la capsula parte prima, e con essa il FIN. È **esattamente** il
difetto che questo innesto dichiara di curare, riprodotto con un ritardo invece che con un carico
di macchina — e il mandato §3 punto 6 avverte che non è dimostrato che le cause curate fossero le
sole.

⚠ Va accanto a: `wt_chiusura_attesa_` **non viene rimesso a zero** quando la chiusura parte
(:247-249, si azzera solo `wt_chiusura_`). Una seconda `wt_chiudi_sessione` nella stessa
connessione trova il contatore già a 5 e spedisce **alla prima passata**, senza nessuna attesa.

`MARCA: [?]`

---

## R10.16 `[?]` — Davanti a un SETTINGS che non riconosce, la riscrittura tira dritto **per sempre**, e lo dice solo su `stderr`

```
DOVE:             01-b2-ngtcp2-wt-innesta.py:561-646 (`wt_riscrivi_impostazioni`), i tre `return
                  0` di :575-581, :587-590, :600-608 e :623-626, contro :211-214 (la condizione
                  che la richiama)
COSA CONTRADDICE: il commento di apertura dello stesso file, :50-57 — «⚠ Un innesto che "non
                  trova l'appiglio" e tira dritto produrrebbe un server che compila, non fa
                  WebTransport, e non lo dice»; e la politica opposta di `wt_conta` (R10.5)
```

**COME SI DIMOSTRA.** `wt_impostazioni_scritte_` viene messo a `true` **solo** in caso di
successo (:254). La condizione di richiamo è

```cpp
    if (sveccnt > 0 && stream_id == wt_ctrl_id_ && !wt_impostazioni_scritte_) {
```

**Ingresso concreto**: nghttp3 cambia — è la cosa che `DECISIONI.md` §6.4:1612 dichiara di dover
riprovare a ogni aggiornamento — e mette un secondo frame nella stessa passata, oppure spezza il
SETTINGS in due vettori. Il controllo `p + lung != orig.size()` (:600) scatta, si stampa
`SETTINGS non e' tutto qui`, e si ritorna 0. Da quel momento in poi **ogni** scrittura sullo
stream di controllo rientra nella condizione, richiama la funzione, e ristampa la riga; il server
resta acceso, serve HTTP/3 senza WebTransport, e l'unico segnale è una riga su `stderr` che
nessun banco legge come denominatore.

⛔ La contraddizione è con la regola che questo file si è dato per gli **appigli**: là zero
occorrenze fermano tutto («non si scrive niente»), qui zero riconoscimenti lasciano andare avanti.
E con `wt_conta` (R10.5), che per un guasto **meno** grave — una scrittura parziale, recuperabile
alla passata dopo — uccide la connessione. Due politiche opposte per la stessa classe di guasto,
a quaranta righe di distanza.

⚠ `[?]` e non `[R]` perché non posso misurare quale forma abbia oggi il SETTINGS di nghttp3 1.8:
serve il banco che §6.4 dichiara di avere.

`MARCA: [?]`

---

## R10.17 `[?]` — `ATTENDI` non restituisce credito, e il credito non torna mai

```
DOVE:             01-b2-ngtcp2-wt-innesta.py:728-734 e :342-346;
                  01-b3-rcp-innesta.py:539-543
COSA CONTRADDICE: l'invariante I1 (il ritmo cala solo per misura) letto sul credito di
                  connessione; e RCP.md §2.3
```

**COME SI DIMOSTRA (da misurare).** Nel ramo `ATTENDI` i byte vengono accumulati in
`wt_incerti_[stream_id]` e **non** vengono contati con
`ngtcp2_conn_extend_max_offset` — per una ragione dichiarata e giusta (:731-733: contarli adesso
e poi di nuovo falserebbe il credito). Ma se lo stream non arriva **mai** a due byte, quei byte
non vengono contati **mai**: il credito di connessione consumato non torna, e `wt_incerti_` non
viene ripulito da nessuna parte (né a `on_stream_close`, né alla chiusura della sessione).

**Ingresso concreto**: un client apre *N* stream bidirezionali dentro la sessione e su ciascuno
manda **un solo byte**. Ogni stream sottrae permanentemente un byte al
`initial_max_data` della connessione e lascia una voce in `wt_incerti_`. Con abbastanza stream il
credito di connessione si esaurisce e il client non può più spedire niente, su una connessione
che sembra viva: il ritmo cala, e non c'è una riga nel registro che lo dica.

⚠ Il numero di stream necessario dipende da `initial_max_data` e dal tetto di stream concorrenti,
che non posso leggere da qui: per questo è `[?]`.

`MARCA: [?]`

---

## R10.18 `[?]` — Il riconoscimento di WebTransport dà per acquisita la codifica **minima** del varint

```
DOVE:             01-b2-ngtcp2-wt-innesta.py:736-740 (`pref[0] == 0x40 && pref[1] == 0x41`);
                  01-b3-rcp-innesta.py:544 (`pref[0] == 0x40 && pref[1] == 0x54`)
COSA CONTRADDICE: E5 — un «fatto» che è una deduzione mai misurata; il commento di :736-739 la
                  scrive come una certezza sul filo
```

**COME SI DIMOSTRA (da misurare).** Il commento dichiara: «*Sul filo sono DUE byte, 0x40 0x41, ed
è per questo che due bastano a decidere*». Che siano due byte è vero **solo se** il mittente usa
la codifica minima. RFC 9000 §16 ammette per un intero variabile quattro lunghezze, e per i tipi
di frame non c'è un DEVE di minimalità che copra ogni mittente: `0x41` è codificabile anche come
`0x80 0x00 0x00 0x41`.

**Ingresso concreto**: un client (o una libreria futura) che scriva il tipo
`WEBTRANSPORT_STREAM` in quattro byte. `wt_smista` non riconosce lo stream, lo marca
`wt_nonwt_`, e lo consegna a nghttp3 — che è **precisamente** il guasto che l'innesto n. 9 esiste
per evitare (:338-340: «*leggerebbe 0x41 come un tipo di frame sconosciuto e poi il numero della
sessione come una LUNGHEZZA, sballando tutto il resto*»). Il sintomo non sarebbe «codifica non
minima»: sarebbe una connessione HTTP/3 che si rompe con un errore di inquadratura.

⚠ `[?]`: nessuno dei motori misurati lo fa **oggi**. La lettura corretta è quella di
`wt_leggi_varint`, che c'è già a venti righe di distanza e non viene usata per questi due byte.

`MARCA: [?]`

---

## R10.19 `[?]` — `rcp_stream_` viene fissato **prima** di sapere se la sessione RCP è nata

```
DOVE:             01-b3-rcp-innesta.py:421-442 (`rcp_avvia`): `rcp_stream_ = stream_id;` a :422,
                  `rcp_ = rcp_apri(...)` a :439
COSA CONTRADDICE: E8 — il silenzio scambiato per zero; e `banchi/rcp/rcp.c:950-955`, dove
                  `rcp_apri` può restituire `NULL`
```

**COME SI DIMOSTRA (da misurare).** Se `rcp_apri` restituisce `NULL` (calloc fallita), lo stato
resta `rcp_stream_ = <stream>` e `rcp_ = nullptr`. Da quel momento `rcp_passa` ritorna subito
(:445-447) e **ogni byte del canale di controllo viene scartato senza una riga di registro**: la
pagina manda `CIAO`, non riceve `ECCOMI`, e va in timeout. Il registro contiene «canale di
controllo = stream N» (:441, stampato **dopo** `rcp_apri`, quindi presente) e poi silenzio — cioè
la diagnosi punterebbe sulla pagina.

⚠ `[?]` perché l'ingresso concreto è una calloc fallita, che non so provocare da qui. Ma la
forma è quella già pagata, e la cura è di una riga: non fissare `rcp_stream_` se `rcp_` è nullo,
oppure dirlo.

`MARCA: [?]`

---

## R10.20 `[?]` — Il numero di sessione del guasto `bidi-dal-server` è scritto come varint di un byte

```
DOVE:             01-b11-guasto-innesta.py:226-231:
                  `t[2] = static_cast<uint8_t>(wt_sessione_);`
COSA CONTRADDICE: RFC 9000 §16 e il commento di 01-b2-ngtcp2-wt-innesta.py:736-739, che nella
                  direzione opposta spiega esattamente perché 65 non sta in un byte
```

**COME SI DIMOSTRA (da misurare).** Il guasto scrive `{0x40, 0x41, (uint8_t)wt_sessione_}`: il
numero di sessione occupa **un** byte, cioè è un intero variabile valido solo per valori < 64.
`wt_sessione_` è il numero dello stream della CONNECT: con dodici casi su un solo caricamento di
pagina i valori sono 0, 4, 8, … 44 e il guasto funziona; **al diciassettesimo** stream
bidirezionale del client il numero diventa 64 e i byte sul filo non dicono più quel che il banco
crede — il client leggerebbe una sessione `0x40`.

⚠ `[?]` perché oggi i casi sono dodici. Ma è un banco che si rompe **aggiungendo casi**, cioè
esattamente quando lo si usa di più, e il commento di `01-b11-guasto.sh`:89-91 dichiara che il
tetto «sta sopra a quel che il banco produce» — questo tetto sta a diciassette, e nessuno lo
conta.

`MARCA: [?]`

---

## Z. Che cosa ho provato a rompere **senza riuscirci**

`PIANO.md` §0.4: dichiarare l'ingresso costruito che non ha rotto niente è informazione.

| che cosa ho provato | perché non rompe |
|---|---|
| **`wt_capsula` che non avanza** — un flusso di byte che non componga mai una capsula | il ciclo `for(;;)` ritorna sempre quando i byte non bastano, e quando bastano `erase` toglie `a + b + lung ≥ 2` byte: `a ≥ 1` per costruzione (`wt_leggi_varint` non restituisce mai 0 con `len > 0`). **Non c'è ciclo che non avanzi.** ⚠ Resta R10.6, che è un altro guasto |
| **`wt_capsula` fuori dai limiti** — `lung` enorme, capsula a pezzi, corpo più corto della lunghezza | `wt_capsbuf_.size() < a + b + lung` è valutato in `uint64_t` con `a + b ≤ 16` e `lung ≤ 2⁶²−1`: **non trabocca**, e la `std::string ragione{corpo + 4, corpo + lung}` è raggiunta solo dopo quel controllo e con `lung ≥ 4`. `erase` non può superare `end()` per la stessa ragione |
| **`wt_leggi_varint` fuori dai limiti** | `n = 1 << (src[0] >> 6)` è 1, 2, 4 o 8 e `len < n` ritorna 0 prima di leggere. Il caso `len == 0` è il primo controllo |
| **`wt_scrivi_varint` che sfonda `aggiunta`/`testa`** | quattro varint di al più 8 byte in `std::array<uint8_t,64>`; tre in `std::array<uint8_t,16>`. `wt_impbuf_` è protetto da `t + lung + a > wt_impbuf_.size()` **prima** di scrivere |
| **`wt_smista_uni` fuori dai limiti** su `pref[2+n]` e `pref[2+n+1]` | `pref.size() < 2 + n + 2` ritorna `ATTENDI` prima |
| **riferimento pendente su `pref`** dopo `wt_incerti_.erase` | in tutt'e tre i punti (`01-b2-...:747-762`, `01-b3-...:546-560`) la copia (`resto`, `riunito`, `consumati`, `tipo`) è presa **prima** dell'`erase` |
| **riferimento pendente su `u`** in `wt_avanza` mentre `rcp_canale_chiuso` gira | `std::deque::push_back` non invalida i riferimenti agli elementi esistenti, e `rcp_canale_chiuso` non spedisce (`rcp.c:1221-1236`: solo `reg`) |
| **doppio conteggio del credito** fra il ramo `ATTENDI` e il ramo `HTTP3` con `riunito` | i byte di `ATTENDI` non vengono contati, e `riunito`/`consumati` li contano una volta sola. ⚠ Resta R10.17, che è il caso in cui non vengono contati **mai** |
| **`rcp_violazione(nullptr, …)`** dal ramo del secondo stream bidirezionale (`01-b3-...:177`), che non ha la guardia `if (rcp_)` che il ramo gemello di `wt_smista_uni` ha (`:589`) | `rcp.c:1195-1200` comincia con `if (!s) return;`. La guardia c'è, ma **dall'altra parte del confine**: le due chiamate fratelle restano scritte in due modi diversi |
| **appiglio non unico o mancante che passa lo stesso** in tutt'e tre gli script | il controllo `count(appiglio) != 1` è fatto **prima** di ogni scrittura, e i tre script sono tutti «o tutti o nessuno». ⚠ Resta R10.9 (i tre file copiati prima) e R10.10 (nessuno guarda l'esito) |
| **un innesto di B2 che distrugge l'appiglio di un innesto successivo di B2**, o che ne crea un secondo | ho ripercorso i 16 appigli di B2 e i 17 di B3 contro i testi introdotti prima di loro: l'unico appiglio condiviso è `std::array<nghttp3_vec, 16> vec;\n\n  for (;;) {\n` (B2 innesto 5 e B3 «il tempo che scorre»), e la sostituzione di B2 **ricomincia con lo stesso testo**, quindi B3 lo ritrova. La composizione, in quest'ordine, tiene |
| **B3 innestato prima di B2** | sei dei suoi appigli vengono da testo di B2, contano 0, e lo script si ferma. L'ordine è **imposto**, ma per collisione e non per controllo: nessuno dei due script cerca la marca dell'altro, e la diagnosi stampata (`L'esempio di ngtcp2 e' cambiato`) sarebbe falsa — R10.9 |
| **B2 innestato due volte** | `MARCA in leggi(...)` sul `.cc` lo blocca; e se qualcuno rimettesse a posto **solo** il `.cc`, gli appigli di `server.h` e `server.cc` conterebbero 0 e lo script si fermerebbe senza scrivere |
| **`wt_riscrivi_impostazioni` che riscrive alla cieca** un SETTINGS spezzato | i quattro controlli (`orig.size() < 3`, tipo di stream `0x00`, tipo di frame `0x04`, `p + lung == orig.size()`) chiudono tutte le strade che ho saputo costruire: un SETTINGS a pezzi **non** viene riscritto. ⚠ Resta R10.16, che è quel che succede **dopo** aver rinunciato |
| **conversioni di segno** nel C++ innestato | ho ripercorso ogni `static_cast` fra `int64_t`/`uint64_t`/`size_t`/`ngtcp2_ssize`: l'unico troncamento che perde informazione è quello di R10.7 (32→8 bit), e l'unico `as_unsigned` su un valore potenzialmente negativo è protetto dall'`assert(ndatalen >= 0)` già presente nell'esempio — ⚠ che con `NDEBUG` non c'è, ma è codice loro e non è cambiato dall'innesto |

---

## Riepilogo

| # | marca | in una riga |
|---|---|---|
| R10.1 | `[R]` | la capsula si legge dentro un `DATA` e si scrive fuori: il motivo della chiusura non arriva alla pagina |
| R10.2 | `[R]` | `rcp_canale_chiuso()` è raggiungibile solo col server guasto di B11 innestato |
| R10.3 | `[R]` | il FIN del client sul canale di controllo non lo vede nessuno: `wt_smista` non ha il parametro |
| R10.4 | `[R]` | `STREAM_DATA_BLOCKED` butta un buffer già scritto a metà e salda i byte del messaggio dopo |
| R10.5 | `[R]` | una scrittura parziale del SETTINGS uccide la connessione, mentre la coda nostra la gestisce |
| R10.6 | `[R]` | `wt_capsbuf_` senza tetto: una lunghezza dichiarata enorme fa crescere la memoria senza fine |
| R10.7 | `[R]` | il codice di chiusura troncato a 8 bit, e lo `0` che §3.1 vieta accettato in silenzio |
| R10.8 | `[R]` | i byte dei canali leciti `0x01` e `0x02` buttati, sotto un commento che dice il contrario |
| R10.9 | `[R]` | B3 copia tre file **prima** del controllo e poi stampa «non si scrive niente» |
| R10.10 | `[R]` | nessun `--togli` verifica di aver tolto, e `ricostruisci()` getta via i quattro stati d'uscita |
| R10.11 | `[R]` | il canale di controllo eletto per ordine d'arrivo (E4), e due commenti fratelli in contrasto |
| R10.12 | `[R]` | tre regole diverse per contare le «righe di codice», e due coppie di numeri negli arbitri |
| R10.13 | `[R]` | `b2 --togli` smonta anche B3 senza dirlo; `b3 --togli` lascia un albero che non compila |
| R10.14 | `[?]` | la chiusura armata senza canale di controllo può non partire mai |
| R10.15 | `[?]` | le cinque passate si verificano dal lato che invia, e il contatore non si azzera |
| R10.16 | `[?]` | un SETTINGS non riconosciuto lascia il server acceso senza WebTransport, per sempre |
| R10.17 | `[?]` | `ATTENDI` non restituisce credito, e `wt_incerti_` non si svuota mai |
| R10.18 | `[?]` | il riconoscimento di `0x41`/`0x54` dà per acquisita la codifica minima del varint |
| R10.19 | `[?]` | `rcp_stream_` fissato prima di sapere se `rcp_apri` è riuscita |
| R10.20 | `[?]` | il numero di sessione del guasto `bidi-dal-server` scritto come varint di un byte |

⛔ **E questo non è un verdetto verde su quel che non è elencato**: §Z dice che cosa ho provato a
rompere senza riuscirci, e tutto il resto è semplicemente **non guardato abbastanza**.
