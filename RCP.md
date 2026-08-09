# RCP — Remotix Control Protocol, versione 1

*Scritto il 9 agosto 2026, prima di qualunque riga di codice.*
*Completato il 9 agosto 2026, dopo il censimento di §0-bis — sempre prima di qualunque riga di codice.*

> ## ⛔ Perché questo documento esiste, e perché viene prima
>
> In v1 l'arbitro era **mstsc**: se disegnava, era giusto. Quando il nostro server sbagliava a
> capire la specifica RDP, un client altrui lo diceva subito, gratis.
>
> In V2 client e server sono **nostri**. Se il server emette una sciocchezza, il nostro client la
> accetterà volentieri — perché lo stesso fraintendimento è compilato in tutti e due. **Due
> programmi scritti dalla stessa mano che vanno d'accordo non confermano niente**: ripetono lo
> stesso presupposto.
>
> Da cui il mestiere di questo documento: **è lui l'arbitro**. Non descrive quel che il codice fa,
> stabilisce quel che il codice deve fare, ed è scritto abbastanza preciso da poter **dare torto**
> a un'implementazione. Se una riga qui è ambigua, è un difetto di questo file, non
> un'interpretazione del programmatore.
>
> **Che cosa è normativo**: tutto ciò che è scritto con **DEVE**, **NON DEVE**, **PUÒ**. Il resto è
> spiegazione, e non vincola.

---

## 0-bis. ⭐ Il censimento del 9 agosto, e che cosa ha chiuso

*Fatto all'apertura della fase 1, rileggendo il documento con una domanda sola: **due persone che
lo leggono da sole scrivono lo stesso byte?***

La risposta era **no**, e non per una sfumatura. La prima stesura definiva **il fotogramma** (28
byte esatti) e **il datagram audio** (12), cioè le due cose che portano i pixel e il suono — e dei
**venti messaggi di controllo, di input e di appunti** dava il **nome** e una descrizione a parole.
Il canale che porta la stretta di mano, cioè quello che la fase 1 deve scrivere, era il meno
specificato di tutti.

| | Prima | Adesso |
|---|---|---|
| corpi di messaggio definiti byte per byte | 2 su 22 | **22 su 22** (§6, §7) |
| tipi elementari (numeri, stringhe, elenchi) | — | §6.0 |
| come si riconosce a quale canale appartiene uno stream | — | §2.5 |
| che cosa pretende il trasporto (finestre, stream, migrazione, 0-RTT) | 3 parametri | §2.3 |
| la porta | — | §2.4 |
| che cosa fa un'implementazione dopo `ERRORE_PROTOCOLLO` | «chiude» | §3.1 |
| il recupero dopo un fotogramma abbandonato | ⛔ **non esisteva** | §5.2 |
| il formato dell'audio | «Opus, PCM» | §5.3 |
| la limitazione dei tentativi | `[?]` in `SPECIFICHE.md` §4.2 | §4.4-bis |

⛔ **E un buco che non era una lacuna ma un difetto di disegno**: §5.1 concede al server di
**abbandonare** un fotogramma con `RESET_STREAM`, e il video è compresso con predizione fra
fotogrammi. Abbandonarne uno da cui i successivi dipendono lascia il decodificatore rotto **finché
non arriva un fotogramma chiave** — e non c'era modo né di dire che un fotogramma è chiave, né di
chiederne uno. La cura sta in §5.2 e costa **zero byte** all'intestazione: entra nei valori del
campo `tipo`, che erano indefiniti.

⚠ **Le chiusure sono marcate 🔸 in `DECISIONI.md` §1.5**: sono conseguenze scritte da me, non
pronunciate dall'utente, e si correggono senza discussione. Quel che resta volutamente aperto sta
in §12, dichiarato invece che dimenticato.

⭐ **E la finestra per farlo è adesso**: §9 vieta di aggiungere tipi di messaggio dentro una
versione maggiore. Quel divieto protegge le implementazioni esistenti, e **oggi non ne esiste
nessuna**. Dal primo byte scritto in poi, questo documento si tocca solo come dice §9.

---

## 1. Il modello, in una pagina

```
        CLIENT                                            SERVER
          │                                                 │
          │  ①  QUIC + TLS 1.3        UDP 7447               │
          │────────────────────────────────────────────────▶│
          │◀──── certificato ───────────────────────────────│
          │  ② il client CONFRONTA col ricordo               │
          │                                                 │
          │  ③  CIAO  (versione, capacità del client)        │
          │────────────────────────────────────────────────▶│
          │◀──── ECCOMI (versione, capacità del server) ─────│
          │                                                 │
          │  ④  CREDENZIALI                        ── PAM ──▶│
          │◀──── AMMESSO  /  RESPINTO(motivo) ───────────────│
          │                                                 │
          │  ⑤  ATTACCA (tela, disposizione, vista)          │
          │◀──── SESSIONE (stato, tela concessa) ────────────│
          │                                                 │
          │        ══════ da qui i canali scorrono ══════    │
          │◀═══ video: uno stream per fotogramma ═══════════ │
          │◀═══ audio: datagram ════════════════════════════ │
          │═══▶ input: uno stream riservato ════════════════ │
          │◀══▶ controllo · appunti ════════════════════════ │
```

Tre cose che questo disegno dice e che vanno lette:

1. **il server dimostra chi è prima che la password parta** — invariante I3 applicata
   all'ordine (`SPECIFICHE.md` §4.1);
2. **l'autenticazione precede l'attacco**: chi non è ammesso non nomina nemmeno una sessione;
3. **la tela si concorda all'attacco**, e da lì non cambia finché il client resta
   (`SPECIFICHE.md` §6.1).

⛔ **L'ordine dei cinque passi non ammette permute.** Un messaggio che arriva in uno stato in cui
non è previsto è `ERRORE_PROTOCOLLO` (§3). È la trappola 1 di `LEZIONI.md` §4, dove ogni permuta
era punita con un errore diverso e nessuno diceva «hai sbagliato l'ordine»: qui lo dice.

---

## 2. Il trasporto

**WebTransport su HTTP/3**, cioè **QUIC** versione 1 (RFC 9000) con **TLS 1.3 obbligatorio**. Non
esiste un modo in chiaro, e RCP non scorre mai su TCP.

> ### ⭐ Cambiato il 9 agosto 2026 — e il protocollo non ha perso una riga
>
> `DECISIONI.md` §1.6: **niente client dedicati, il client è il browser**. Una pagina non può
> aprire una connessione QUIC nuda, ma **WebTransport le dà gli stessi mattoni** su cui §5.1 era
> stato disegnato: stream unidirezionali indipendenti, l'abbandono di uno stream, i datagram,
> la migrazione della connessione.
>
> ⭐ **Quel che cambia sta tutto in questo capitolo e in §4.1**: come si arriva alla connessione e
> chi si fida di chi. **I messaggi, l'inquadratura, i canali e i corpi non cambiano di un byte** —
> §3 e da §5 in poi valgono identici.
>
> ⚠ **E il server acquista un mestiere**: prima ascoltava QUIC e basta, adesso **serve anche la
> pagina**. Sono due ascoltatori con lo stesso numero di porta — **UDP** per HTTP/3 e WebTransport,
> **TCP** per il primo caricamento — perché un browser che apre `https://…` parte in TCP e passa a
> QUIC solo se il server glielo annuncia con `Alt-Svc`.

### 2.1 Come si usano i pezzi di QUIC

QUIC non è «TCP che va più veloce»: porta quattro cose che questo protocollo usa
deliberatamente, e che vanno usate **invece** di reimplementarle (`SPECIFICHE.md` §2.3).

| Pezzo di QUIC | A che serve qui |
|---|---|
| **stream indipendenti** | un fotogramma in ritardo non blocca il successivo: il blocco di testa è per stream, non per connessione |
| **`RESET_STREAM`** | ⭐ **abbandonare un fotogramma** che non serve più, invece di spedirlo tardi |
| **datagram** | l'audio, che è piccolo e preferisce perdere un pacchetto che aspettarlo |
| **migrazione della connessione** | il telefono passa da WiFi a rete mobile senza che la sessione se ne accorga |
| **controllo di congestione** | la misura di quanto porta la linea, che in v1 andava ricavata a mano |
| **tempo di inattività** | i 30 secondi di silenzio di `SPECIFICHE.md` §5.3 |

### 2.2 Parametri obbligatori

| Parametro | Valore | Perché |
|---|---|---|
| `max_idle_timeout` | **30 s**, imposto dal server | è l'orologio del silenzio: scaduto, il client è staccato |
| datagram | **DEVONO** essere abilitati sulla connessione HTTP/3 | l'audio |
| ALPN | `h3` | ⛔ lo negozia il browser, non noi: una pagina non sceglie l'ALPN |
| **l'indirizzo della sessione** | `https://<host>:<porta>/rcp/1` | ⭐ **è qui che vive l'identità del protocollo**, al posto dell'ALPN: il numero dopo la barra è la **versione maggiore** |

⛔ **Il server NON DEVE accettare una sessione WebTransport su un percorso diverso.** Un percorso
sconosciuto si rifiuta con lo stato HTTP di rifiuto, e si scrive nel registro: è §3 applicata al
primo byte, prima ancora che RCP cominci.

⚠ **Perché la versione sta nel percorso e non solo nel `CIAO`.** Con l'ALPN il rifiuto arrivava
prima di spendere una connessione; qui l'ALPN è `h3` e non è nostro, quindi il posto più a monte in
cui possiamo dire «questa versione non la parlo» è il percorso. ⛔ Resta comunque obbligatorio il
controllo di versione in `CIAO`/`ECCOMI` (§9): **il percorso non lo sostituisce** — un percorso si
può digitare a mano, e un controllo che si può aggirare digitando non è un controllo.

⛔ **NON DEVE esistere un battito applicativo.** Il tempo di inattività di QUIC fa già quel
mestiere, e un secondo meccanismo produrrebbe due verità sullo stesso fatto.

### 2.3 ⭐ Il credito degli stream, e che cosa non possiamo più pretendere

*Aggiunta il 9 agosto 2026 e riscritta lo stesso giorno, dopo `DECISIONI.md` §1.6.*

⛔ **La prima stesura di questo paragrafo dettava al client i parametri di trasporto QUIC** —
quanti stream, quanta finestra, niente 0-RTT, niente `disable_active_migration`. **Con un browser
non si può: quei parametri li sceglie lui**, e nessuna riga di questo documento glieli cambia. Ciò
che resta normativo è quel che tocca a **noi** — il server — e quel che va **misurato invece che
preteso**.

| | |
|---|---|
| **il server DEVE concedere credito** al client per i suoi stream unidirezionali: almeno **16** disponibili in ogni momento | il client apre uno stream di input e uno per ogni trasferimento di appunti. Se il credito finisse, **l'input non partirebbe affatto** e il sintomo sarebbe «il desktop non risponde» |
| **il server DEVE reggere il rifiuto di aprire uno stream** invece di considerarlo un errore fatale | il video consuma **uno stream per fotogramma**: a 60 al secondo, il credito che il browser concede si consuma in fretta e viene rinnovato mano a mano che gli stream si chiudono |
| ⛔ **e quando il credito manca, si BUTTA il fotogramma, non si aspetta** | aspettare un posto libero è una coda, e ogni coda **compra fluidità e vende risposta** (`SPECIFICHE.md` §3.2). Il fotogramma vecchio non serve più: ne sta già arrivando uno nuovo. È §5.1 applicata a monte |
| **il server NON DEVE offrire 0-RTT** | i dati 0-RTT si possono **ripetere**, e il secondo messaggio è `CREDENZIALI`. Il guadagno è un giro di rete su una sessione che dura ore |
| **il server NON DEVE disabilitare la migrazione** | è la ragione per cui QUIC è stato scelto (`SPECIFICHE.md` §8.4): il telefono che passa da WiFi a rete mobile |

`[?]` **Quanti stream al secondo regga davvero ciascun browser non lo sa nessuno**, e non si legge:
si misura. ⚠ È la forma di difetto che un banco corto **non vede** — funziona per i primi secondi e
si ferma dopo (`LEZIONI.md` §1.4) — ed è per questo che §11 ha un banco apposta, che tiene la
sessione viva **oltre i primi 256 fotogrammi**.

### 2.4 🔸 La porta

**7447**, e sono **due ascoltatori con lo stesso numero**: **UDP** per HTTP/3 e WebTransport,
**TCP** per il primo caricamento della pagina. È il valore predefinito, e **PUÒ** essere cambiato
dalla configurazione del server: l'utente digita `https://indirizzo:7447` nel browser, e poi utente
e password nella pagina.

⛔ **Il server DEVE annunciare `Alt-Svc: h3=":7447"` sulla risposta TCP**, o il browser non passerà
mai a QUIC e la pagina resterà su TCP — dove RCP non scorre. ⚠ Il sintomo di quella riga dimenticata
non è un errore: è **una pagina che si apre e un desktop che non arriva mai**.

⚠ Scelta il 9 agosto 2026 verificando che sia libera in `/etc/services` di Debian Trixie `[M]`.
`[?]` **Non è stata verificata la registrazione IANA**: se un giorno servisse un numero
registrato, questa riga si cambia senza toccare nient'altro.

### 2.5 ⛔ Gli stream: chi apre che cosa, e come si riconoscono

*Questo paragrafo chiude il buco più insidioso del censimento: chi riceve uno stream
unidirezionale deve sapere **che cosa** c'è dentro prima di leggerlo, e non c'era scritto da
nessuna parte.*

| Stream | Chi lo apre | Quanti |
|---|---|---|
| **controllo** — il **primo** stream bidirezionale della sessione | il client | uno solo, per tutta la connessione |
| **video** — unidirezionale | il server | uno **per fotogramma** |
| **input** — unidirezionale | il client | **uno solo**, aperto all'attacco e tenuto aperto |
| **appunti** — unidirezionale | entrambi | uno **per trasferimento** |

⛔ **Il client NON DEVE aprire stream bidirezionali oltre lo 0. Il server NON DEVE aprire stream
bidirezionali.** Chi ne riceve uno chiude con `ERRORE_PROTOCOLLO`.

⭐ **Come si riconosce il canale**: si leggono i **primi due byte** dello stream, che sono in ogni
caso un campo `tipo` (§6). Il byte alto dice il canale:

| Byte alto di `tipo` | Canale | Che cosa segue |
|---|---|---|
| `0x00` | controllo | l'inquadratura di §6.1 — e su uno stream unidirezionale è `ERRORE_PROTOCOLLO`: il controllo vive solo sullo stream 0 |
| `0x01` | input | l'inquadratura di §6.1, un messaggio dopo l'altro |
| `0x02` | appunti | l'inquadratura di §6.1 |
| `0x03` | video | l'intestazione di 28 byte di §6.2, **senza** inquadratura |
| `0x04` | audio | ⛔ solo su datagram (§6.3). Su uno stream è `ERRORE_PROTOCOLLO` |

⛔ Un byte alto diverso da questi cinque è `ERRORE_PROTOCOLLO`. E un canale usato **nel verso
sbagliato** — un `0x01` che arriva dal server, un `0x03` che arriva dal client — lo è a sua volta.

---

## 3. ⛔ La regola di rigore

> **Un'implementazione RCP che riceve qualcosa che non capisce DEVE chiudere la connessione con
> `ERRORE_PROTOCOLLO` e scrivere nel registro che cosa non ha capito. NON DEVE ignorarlo, NON DEVE
> indovinare, NON DEVE proseguire.**

Vale per: un tipo di messaggio sconosciuto, una lunghezza che non torna, un campo fuori intervallo,
un messaggio arrivato nello stato sbagliato della macchina, un canale usato nel verso sbagliato.

**Perché è scritta come prima regola e non fra le note.** Un parser indulgente è comodissimo il
primo giorno e velenoso per sempre: se il server comincia a emettere un campo sbagliato e il client
lo ignora educatamente, il difetto **non si vede** — e siccome non c'è più un client altrui che
protesti (§0), non lo vedrà nessuno finché non produrrà un sintomo lontano e incomprensibile.

È `REVIEWER.md` §5 applicata al filo: *«l'indulgenza che nasconde è esattamente ciò che devi
togliere»*.

⚠ **L'unica eccezione, e ha una forma precisa**: le **capacità** dichiarate nella stretta di mano
(§4.3). Lì una voce sconosciuta si ignora, perché è il meccanismo con cui le versioni future si
capiscono. Ma è ignorare *un'offerta*, non *un comando*.

### 3.1 Che cosa vuol dire «chiudere», in byte

*Aggiunta il 9 agosto 2026: «chiude la connessione» ammetteva almeno tre implementazioni diverse,
e due di esse fanno sparire il motivo proprio quando serve.*

Chi rileva la violazione, **in quest'ordine**:

1. **DEVE** scrivere nel registro *che cosa* non ha capito — il tipo ricevuto, la lunghezza, lo
   stato in cui si trovava. Non «errore di protocollo»;
2. **DEVE** mandare `CONGEDO` (§8) con il motivo, sul canale di controllo, **se il canale di
   controllo è ancora utilizzabile**;
3. **DEVE** chiudere la connessione QUIC con `CONNECTION_CLOSE` di tipo applicativo, e il codice
   d'errore applicativo **DEVE** essere il **codice del motivo** di §8.2.

⭐ **Il terzo punto è quello che salva le diagnosi**: se il congedo non arriva — perché lo stream
era rotto, perché il messaggio era illeggibile — il motivo viaggia comunque, dentro la chiusura
QUIC. In v1 il server scriveva «congedo il client» e il client leggeva «errore di rete» per **tre
fasi** (`LEZIONI.md` §1.7): qui i due lati hanno due strade per dirsi la stessa cosa, e il collaudo
di §11 verifica **dal lato che riceve** che almeno una delle due sia arrivata.

⚠ Il codice d'errore applicativo **0** significa «chiusura senza motivo» e **NON DEVE** essere
usato: ogni chiusura ha un motivo di §8.2.

---

## 4. La stretta di mano

### 4.1 Prima ancora: il certificato

> ### ⭐ Riscritta il 9 agosto 2026 — questa parte **non la implementiamo più**
>
> La prima stesura dettava al client i quattro passi della fiducia al primo incontro: calcola
> l'impronta, confronta col ricordo, interrompi se cambia, accetta in silenzio se non c'è.
>
> ⭐ **Con un browser quei quattro passi ci sono già, e li fa lui**: accetta per quell'indirizzo,
> se lo ricorda, e riavvisa se il certificato cambia. **Il modello era giusto — semplicemente non
> è più codice nostro.** Quel che cambia è il prezzo: l'accettazione **non è silenziosa**, è un
> avviso con un clic, la prima volta su ogni dispositivo (`DECISIONI.md` §1.7).

**Quel che resta normativo, ed è tutto dalla parte del server:**

| | |
|---|---|
| **la chiave** | **DEVE** essere **ECDSA P-256**. ⛔ Non Ed25519 e **mai RSA**: P-256 è l'unica che tiene aperta anche la strada di `serverCertificateHashes` `[S]`, e una chiave scelta oggi per comodità chiuderebbe quella porta senza che nessuno se ne accorga |
| **la generazione** | il server se lo genera all'installazione, e tiene la chiave privata con permessi `0600` |
| **il nome** | il certificato **DEVE** portare come `subjectAltName` l'indirizzo su cui il server risponde — nome o indirizzo IP. ⚠ Un browser che trova un `SAN` che non combacia mostra **un avviso diverso**, e alcuni non offrono nemmeno il clic per proseguire |
| **il certificato vero** | se l'amministratore ne installa uno emesso da un'autorità, il server **DEVE** usarlo e **non DEVE** rigenerare il proprio. È la strada senza avvisi (`SPECIFICHE.md` §4.1) |

⛔ **E una cosa che il server DEVE fare e che con un client nostro non esisteva**: la pagina e la
sessione WebTransport **devono presentare lo stesso certificato**. Sono due connessioni — una TCP e
una UDP (§2.4) — e se portassero due certificati diversi l'utente si troverebbe **due avvisi**, o
un avviso e un fallimento muto.

`[?]` **La misura che decide la forma del predefinito**, e non si risponde leggendo: l'eccezione
che l'utente concede sul caricamento della pagina **copre anche la sessione WebTransport**? Se non
la coprisse, servirebbe `serverCertificateHashes` — che WebKit **ha dichiarato che non
implementerà** `[S]`, e su Safari resterebbe solo il certificato vero. È la prima domanda della
sonda del browser.

### 4.1-bis Se un giorno servisse `serverCertificateHashes`

*Tenuto qui perché la scelta della chiave in §4.1 è già fatta per non chiudere questa porta.*

| | |
|---|---|
| **che cos'è** | l'impronta SHA-256 del certificato viaggia **dentro la pagina**, e il browser si fida senza avvisi — cioè il nostro modello, fatto bene |
| **il vincolo** | `[S]` certificato valido **meno di 14 giorni**, chiave **ECDSA P-256**, niente RSA, e `allowPooling` a `false` |
| ⭐ **perché la rotazione non si vede** | è **il server stesso a servire la pagina**: rigenera il certificato quando scade e ci scrive dentro l'impronta corrente. L'utente non tocca niente |
| ⛔ **che cosa non copre** | **il caricamento della pagina**. Vale solo per la sessione WebTransport, quindi da sola questa strada non basta mai: il primo `https://` resta da risolvere con l'avviso o con il certificato vero |
| ⛔ **chi resta fuori** | Safari e tutto ciò che è WebKit — **iPhone e iPad compresi** |

⚠ **E la conseguenza sul collaudo, che vale in ogni caso**: un banco che prova la fiducia **DEVE**
provare anche il **secondo** collegamento, e un terzo con la chiave cambiata. La prova a
collegamento singolo resta verde per sempre (`LEZIONI.md` §2.1).

### 4.2 Il canale di controllo

Il client apre il **primo stream bidirezionale** (identificatore 0). Quello è il canale di
controllo, resta aperto per tutta la connessione, e il suo chiudersi **è** la fine della
connessione.

⛔ **In byte**: un FIN sullo stream 0, da una qualunque delle due parti, chiude la connessione.
Chi lo riceve **DEVE** considerare finita la connessione e chiudere quella QUIC; **NON DEVE**
continuare a spedire sugli altri canali.

### 4.3 `CIAO` e `ECCOMI`

| | |
|---|---|
| **CIAO** | client → server. Versione maggiore del protocollo, capacità del client |
| **ECCOMI** | server → client. Versione scelta, capacità del server |

**Il corpo, in byte** (i tipi elementari sono in §6.0):

```
CIAO / ECCOMI
 ├── u16   versione
 └── elenco di capacità:
       u16  quante
       per ciascuna:  stringa nome  ·  stringa valore
```

In `CIAO` la `versione` è **la maggiore che il client sa parlare**; in `ECCOMI` è **quella scelta
dal server** (§9). RCP/1 vale **1**.

Le **capacità** sono coppie nome-valore. Un nome sconosciuto si ignora (§3, eccezione). I nomi
definiti in RCP/1:

| Nome | Chi lo dichiara | Valori |
|---|---|---|
| `video.codec` | entrambi | elenco fra `hevc`, `av1`, in ordine di preferenza |
| `video.profondita` | entrambi | elenco fra `8`, `10` |
| `video.misura_massima` | client | `LARGHEZZAxALTEZZA` che sa decodificare, es. `3840x2160` |
| `audio.codec` | entrambi | elenco fra `opus`, `pcm` |
| `input.tocco` | client | `si`, `no` — riservato, in RCP/1 vale sempre `no` |
| `appunti.testo` | entrambi | `si`, `no` |
| `client.nome` | client | testo libero per il registro, es. `remotix-linux 0.1.0` |

⛔ **La forma dei nomi e dei valori è vincolata**, o «ignorare quel che non si conosce» diventa
«indovinare»:

- un **nome** è fatto di `a-z`, `0-9` e `.`, da 1 a 64 byte;
- un **valore** è testo UTF-8 stampabile, al massimo 256 byte;
- un **elenco** dentro un valore si scrive separato da virgole, senza spazi: `hevc,av1`;
- ⛔ **un nome ripetuto due volte è `ERRORE_PROTOCOLLO`.** «Vince l'ultimo» e «vince il primo» sono
  due implementazioni diverse dello stesso documento, che è precisamente ciò che questo documento
  esiste per impedire;
- ⛔ un valore **vuoto** è `ERRORE_PROTOCOLLO`: chi non ha niente da dire non manda la capacità.

⛔ Se l'intersezione di `video.codec` è **vuota**, il server **DEVE** congedare con
`NIENTE_IN_COMUNE`. NON DEVE ripiegare su un codec non dichiarato. Lo stesso vale per
`video.profondita` e per `audio.codec`.

⚠ `pcm` **DEVE** essere dichiarato da entrambi: è la base sempre disponibile, e serve da controllo
positivo quando Opus non si negozia. Allo stesso modo `8` **DEVE** comparire in
`video.profondita` di entrambi.

⛔ **Chi sceglie è il server**, dentro l'intersezione, seguendo l'ordine di preferenza **del
client**. La scelta **DEVE** essere scritta nel registro del server: una negoziazione riuscita con
dentro il contrario di quel che si voleva è la trappola 4 di `LEZIONI.md` §4, e si vede solo se
qualcuno la scrive.

⚠ `video.misura_massima` **non** cambia la tela: è un tetto che il server **DEVE** rispettare
quando concede la tela (§4.5). Esiste perché il decodificatore di un telefono ha limiti che il suo
schermo non dichiara.

### 4.4 Le credenziali

Un solo messaggio `CREDENZIALI` con utente e parola d'ordine. Il server le passa a PAM.

```
CREDENZIALI
 ├── stringa utente         (≤ 256 byte)
 └── stringa parola         (≤ 1024 byte)

AMMESSO      corpo vuoto
RESPINTO
 └── u8      motivo         (dallo spazio dei motivi di §8.2)
```

| Esito | Messaggio |
|---|---|
| ammesso | `AMMESSO` |
| respinto | `RESPINTO` con motivo |

⛔ Il server **NON DEVE** distinguere nel motivo fra «utente inesistente» e «parola d'ordine
sbagliata»: entrambi sono `CREDENZIALI_ERRATE`. E **DEVE** applicare la limitazione della
frequenza dei tentativi prima di rispondere (§4.4-bis).

⛔ **`RESPINTO` è il congedo dell'autenticazione.** Dopo averlo mandato il server **DEVE** chiudere
la connessione come dice §3.1 — con lo stesso motivo nel `CONNECTION_CLOSE` — e **NON DEVE**
mandare anche `CONGEDO`. Il client **NON DEVE** riprovare sulla stessa connessione: per un secondo
tentativo se ne apre una nuova.

> ⚠ *Chiarita il 9 agosto 2026.* La prima stesura aveva `RESPINTO(motivo)` in §4.4 e
> `CREDENZIALI_ERRATE` fra i motivi di congedo di §8.2, senza dire se dopo il primo arrivasse anche
> il secondo. Due implementazioni potevano indovinare diverso — o, peggio, **indovinare uguale
> perché scritte dalla stessa mano**, che è il difetto muto contro cui questo documento esiste.

⚠ **Una nota che non è normativa e che vale il tempo di scriverla**: la parola d'ordine sta in
chiaro nella memoria di chi la riceve. Va azzerata appena PAM ha risposto, e **non** deve comparire
in nessun registro a nessun livello — nemmeno in `traccia`, che in v1 è un registratore di battitura
(`v1/remotix-c/src/registro.h`).

### 4.4-bis 🔸 La limitazione dei tentativi

*Chiude la `[?]` di `SPECIFICHE.md` §4.2, aperta l'8 agosto e ancora aperta il 9. La forma è mia,
non pronunciata dall'utente: si corregge senza discussione.*

Il server tiene due contatori dei **tentativi falliti**, uno per **nome utente** e uno per
**indirizzo di provenienza**, e applica il più severo dei due:

| | |
|---|---|
| **soglia** | 5 tentativi falliti in 5 minuti |
| **oltre la soglia** | ogni nuovo tentativo riceve `TROPPI_TENTATIVI` **senza che PAM venga interrogata**, per un'attesa che parte da **30 secondi** e **raddoppia** a ogni tentativo fino a un tetto di **15 minuti** |
| **azzeramento** | un'autenticazione riuscita azzera entrambi i contatori di quel nome; il contatore per indirizzo scade da sé dopo 30 minuti di quiete |
| ⛔ **il ritardo fisso** | il server **NON DEVE** rispondere a `CREDENZIALI` prima che sia passato **un secondo** dalla ricezione, **anche quando la risposta è `AMMESSO`** |

⭐ **Il ritardo fisso è la riga che conta**, e non serve a rallentare chi indovina: serve a togliere
il **tempismo** come canale. Senza, «utente inesistente» risponde in un millisecondo e «password
sbagliata» in cinquanta, e la distinzione che §4.4 vieta di scrivere nel motivo la si legge
comunque col cronometro. Applicarlo solo ai rifiuti la rimetterebbe dall'altra parte.

⚠ **E il conto per indirizzo va tenuto sapendo che cosa non protegge**: dietro un NAT gli indirizzi
si condividono, quindi un utente maldestro può bloccare i vicini. È il motivo per cui il contatore
per nome esiste ed è quello che si azzera con un successo.

### 4.5 `ATTACCA`

```
ATTACCA
 ├── u32     tela_larghezza
 ├── u32     tela_altezza
 ├── u32     vista_larghezza
 ├── u32     vista_altezza
 └── stringa disposizione        (≤ 64 byte)
```

| Campo | | |
|---|---|---|
| `tela_larghezza`, `tela_altezza` | pixel | la misura che il client chiede |
| `disposizione` | stringa | la disposizione di tastiera, es. `it` |
| `vista_larghezza`, `vista_altezza` | pixel | la misura in cui il client disegnerà |

⛔ **I limiti, e sono normativi**: larghezza e altezza della tela **DEVONO** stare fra **320×240** e
**7680×4320**, ed **entrambe DEVONO essere pari**. Fuori da lì è `ERRORE_PROTOCOLLO`.

⭐ **Il vincolo dei numeri pari non è pignoleria**: i codificatori video lavorano su blocchi, e una
misura dispari viene arrotondata **da chi codifica, in silenzio** — due misure diverse sotto la
stessa etichetta, cioè la forma d'errore **E2** di `REVIEWER.md`. Meglio rifiutarla qui, dove si
può dire perché.

⚠ La `disposizione` **DEVE** essere un nome di disposizione XKB, eventualmente con la variante fra
parentesi: `it`, `us`, `de(neo)`. Il server **DEVE** rifiutare con `ERRORE_PROTOCOLLO` una stringa
che non ha questa forma, e **DEVE** congedare con `SESSIONE_NON_SERVIBILE` una disposizione ben
formata che il sistema non conosce — sono due guasti diversi, e vanno distinti.

Il server risponde `SESSIONE`:

```
SESSIONE
 ├── u8      stato               1 = NUOVA, 2 = RIPRESA
 ├── u32     tela_larghezza      ⚠ la tela CONCESSA
 ├── u32     tela_altezza
 └── stringa desktop             uno fra: gnome · kde · xfce · lxqt · cinnamon · sconosciuto
```

⭐ **La tela concessa può essere diversa da quella chiesta**, ed è il caso del ripiego su KDE
< 6.8 (`SPECIFICHE.md` §6.3): la sessione era già viva con un'altra misura e non può cambiarla. Il
client **DEVE** adattarsi riscalando, e il server **DEVE** aver scritto il ripiego nel registro.

⚠ La tela concessa **DEVE** rispettare `video.misura_massima` se il client l'ha dichiarata, e
rispettare comunque i limiti e la parità di sopra. Il campo `desktop` è per la diagnosi: il client
**NON DEVE** cambiare comportamento in base al suo valore, o si scrive una compatibilità per
desktop che nessuno ha chiesto e che nessun banco prova.

Se l'attacco non si può servire, il server congeda con uno dei motivi di §8.2 — mai con un
silenzio, mai con una sessione a metà.

### 4.6 ⛔ I tempi della stretta di mano

*Aggiunta il 9 agosto 2026: una connessione che si ferma a metà stretta di mano tiene un posto e
non lo dichiara a nessuno.*

| Da | A | Tetto |
|---|---|---|
| stretta di mano TLS finita | `CIAO` ricevuto | **5 s** |
| `ECCOMI` spedito | `CREDENZIALI` ricevute | **60 s** — è il tempo in cui una persona digita la parola d'ordine |
| `AMMESSO` spedito | `ATTACCA` ricevuto | **10 s** |

⛔ Scaduto un tetto, il server **DEVE** congedare con `TEMPO_SCADUTO`. **NON DEVE** aspettare i 30
secondi del tempo di inattività di QUIC: quello misura il **silenzio della rete**, questo misura un
**client che non fa il suo mestiere**, e confonderli fa sembrare un difetto nostro una rete lenta.

---

## 5. Il quadro dei canali

| Canale | Trasporto | Verso | Affidabile? |
|---|---|---|---|
| **controllo** | stream bidirezionale 0 | ↔ | sì |
| **video** | **uno stream unidirezionale per fotogramma** | server → client | sì, ma abbandonabile |
| **audio** | datagram | server → client, e ↑ per il microfono | no |
| **input** | uno stream unidirezionale riservato | client → server | sì |
| **appunti** | uno stream unidirezionale per trasferimento | ↔ | sì |
| **cursore** | sul canale di controllo | server → client | sì |

⚠ Il microfono è nella tabella perché il verso è previsto, **ma RCP/1 non lo definisce**: vedi §12.

### 5.1 ⭐ Perché un fotogramma è uno stream

È la scelta di disegno più importante del protocollo.

Se il video viaggiasse su **un solo** stream, un fotogramma lento bloccherebbe tutti quelli dopo —
il blocco di testa — e su una rete mobile la sessione si accumulerebbe addosso il proprio
passato. Se viaggiasse su **datagram**, dovremmo riscrivere frammentazione e ritrasmissione, cioè
rifare QUIC dentro QUIC.

Con uno stream per fotogramma: gli stream sono indipendenti, quindi un fotogramma in ritardo non
tocca i successivi; e soprattutto il server **PUÒ** chiamare `RESET_STREAM` su un fotogramma che
non serve più — perché ne è già partito uno più recente — e i byte non ancora spediti non partono
affatto.

⛔ **È così che si onora l'invariante I1 senza tradirla**: non si *riduce la qualità* per prudenza,
si *butta il passato* quando è passato. E ogni abbandono **DEVE** essere scritto nel registro:
un fotogramma perso in silenzio e uno abbandonato di proposito hanno lo stesso aspetto dal lato che
riceve.

### 5.2 ⛔ Il prezzo dell'abbandono, e come si paga

*Aggiunta il 9 agosto 2026, ed è il difetto di disegno che il censimento ha trovato — non una
lacuna di scrittura.*

Il video è compresso **con predizione fra fotogrammi**: un fotogramma *delta* è la differenza da
quelli precedenti. Abbandonarne uno, o perderne uno, non rovina **quel** fotogramma: rovina **tutti
quelli che vengono dopo**, finché non arriva un fotogramma **chiave** — che si decodifica da solo.

§5.1 concede l'abbandono e non diceva né come si riconosce un fotogramma chiave, né come se ne
chiede uno. Le due cose, e la prima costa **zero byte**:

1. ⛔ **il tipo del fotogramma lo dice l'intestazione**: `0x0301` è un fotogramma **chiave**,
   `0x0302` un **delta** (§6.2). Il campo `tipo` c'era già e i suoi valori non erano definiti;
2. ⛔ **il client chiede una chiave** con `RICHIEDI_CHIAVE` (`0x000D`, §7.1) sul canale di
   controllo.

**Le regole:**

- ⛔ il server **NON DEVE** abbandonare un fotogramma **chiave**. Abbandonare la cura non è una cura;
- ⛔ quando il server abbandona un delta, **DEVE** mandare un fotogramma chiave **appena può** —
  senza aspettare che il client lo chieda, perché il client se ne accorge un giro di rete più tardi;
- ⛔ il client **DEVE** mandare `RICHIEDI_CHIAVE` quando si accorge di un **buco** nella successione
  dei `numero`, o quando il decodificatore rifiuta un fotogramma;
- ⛔ finché non arriva una chiave, il client **NON DEVE** mostrare fotogrammi che sa incompleti:
  tiene l'ultimo buono. Un'immagine sfasciata è peggio di un'immagine ferma per un decimo di secondo;
- ⚠ il server **PUÒ** ignorare `RICHIEDI_CHIAVE` ripetute entro **200 ms** l'una dall'altra: durante
  una raffica di perdite ne arriverebbero decine, e ogni chiave costa dieci volte un delta — cioè
  peggiorerebbe esattamente la condizione che l'ha provocata.

⚠ **E una conseguenza che tocca la fase 9**: se la linea è così cattiva da far abbandonare in
continuazione, il rimedio **non** è mandare chiavi in continuazione — è **calare i fotogrammi**,
come dice `SPECIFICHE.md` §8.3. Un fotogramma chiave per ogni delta abbandonato è la spirale.

### 5.3 L'audio: il formato è fisso, non negoziato

*Aggiunta il 9 agosto 2026: «Opus, con PCM come base» dice il codec e non dice il formato, e due
implementazioni che scelgono due frequenze diverse producono un rumore che sembra un difetto di
rete.*

| | |
|---|---|
| frequenza | **48 000 Hz**, sempre, per entrambi i codec |
| canali | **2**, interlacciati |
| **Opus** | un pacchetto Opus per datagram, blocchi da **20 ms** |
| **PCM** | campioni **s16, little-endian**, 20 ms per datagram (1920 campioni, 3840 byte) |

⛔ **Il little-endian del PCM è l'unica eccezione all'ordine di rete di §6, ed è deliberata**: sono
un carico utile, come i byte di HEVC, non un campo di protocollo. Scritta qui perché un'eccezione
non dichiarata è una divergenza silenziosa fra due implementazioni.

⚠ Il volume **non viaggia**: appartiene alla sessione ed è al massimo (invariante I5,
`SPECIFICHE.md` §10).

### 5.4 Gli appunti: i limiti

| | |
|---|---|
| tetto di un trasferimento | **1 000 000 byte** ⚠ — non 1 MiB: il messaggio che lo porta ha sei byte di inquadratura e quattro di lunghezza, e un tetto uguale a quello del messaggio (§6.1) renderebbe **illegale il testo grande esattamente quanto il tetto** |
| testo più grande | ⛔ **non si annuncia affatto**, e il mittente lo **scrive nel registro**. NON DEVE essere troncato: un testo troncato incollato in un terminale è peggio di un testo mancante |
| tipo | ⛔ solo `text/plain;charset=utf-8`, e il testo **DEVE** essere UTF-8 valido |

### 5.5 Il cursore: i limiti

| | |
|---|---|
| misura massima | **256×256** |
| formato | **BGRA premoltiplicato**, riga per riga senza riempimento: `larghezza × altezza × 4` byte |
| cursore nascosto | `larghezza = altezza = 0`, e nessun byte d'immagine |

---

## 6. Il formato dei messaggi

**Ordine dei byte: rete (big-endian).** Nessun campo a lunghezza variabile fuori da quelli
dichiarati con una lunghezza esplicita.

### 6.0 I tipi elementari

*Aggiunta il 9 agosto 2026. Erano usati in tutto il documento e definiti da nessuna parte.*

| Tipo | | |
|---|---|---|
| `u8`, `u16`, `u32`, `u64` | interi senza segno, big-endian | |
| `i16`, `i32` | interi con segno, **complemento a due**, big-endian | |
| **stringa** | `u16 lunghezza` + esattamente `lunghezza` byte di **UTF-8**, **senza terminatore** | ⛔ UTF-8 non valido è `ERRORE_PROTOCOLLO`. Una stringa vuota è `lunghezza = 0` |
| **elenco** | `u16 quante` + gli elementi in fila | |

⛔ **Nessun campo è allineato e nessun riempimento è ammesso.** I campi si leggono e si scrivono in
sequenza, uno dopo l'altro. Un byte in più che «fa tornare i conti» in una struttura C è la forma
esatta del difetto corretto in §6.2 il 9 agosto.

⛔ **Ogni intero ha un solo significato di «assente»**, e va dichiarato dove serve: non esistono
valori sentinella impliciti.

### 6.1 Sui canali affidabili — controllo, input, appunti

```
 0        2        6                    6+lunghezza
 ├────────┼────────┼─────────────────────┤
 │ tipo   │ lungh. │ corpo               │
 │ u16    │ u32    │                     │
```

⛔ `lunghezza` **DEVE** essere il numero esatto dei byte del corpo. Un ricevente che legge una
lunghezza incoerente con quel che il tipo prevede **DEVE** chiudere con `ERRORE_PROTOCOLLO`.

⛔ Nessun messaggio **DEVE** superare **1 MiB**. Chi ne annuncia uno più grande viola il protocollo.

⛔ **E la lunghezza si controlla prima di allocare.** Un ricevente che alloca `lunghezza` byte e poi
verifica ha già regalato un megabyte a chiunque sappia scrivere sei byte.

### 6.2 Sugli stream del video

Uno stream, un fotogramma. Nessuna lunghezza: **la fine dello stream è la fine del fotogramma**.

```
 0        2        4        8        12       16       24       28   28+…
 ├────────┼────────┼────────┼────────┼────────┼────────┼────────┼─────┤
 │ tipo   │ codec  │ largh. │ altezza│ numero │ istante│ input  │ dati│
 │ u16    │ u16    │ u32    │ u32    │ u32    │ u64    │ u32    │     │
```

⛔ **L'intestazione è di 28 byte esatti, senza riempimento**, e i dati del fotogramma cominciano
all'offset 28. Nessun campo è allineato: si legge e si scrive in sequenza.

> ⚠ *Corretta il 9 agosto 2026, prima di qualunque implementazione.* Il disegno dava `… 24 │ 32`,
> cioè otto byte a un campo dichiarato `u32`: quattro byte di riempimento non dichiarati, e due
> implementazioni che potevano indovinare uguale senza che nessuno se ne accorgesse — il difetto
> muto contro cui questo documento è stato scritto (§0). Scelto **28** dall'utente: un riempimento
> va giustificato, e qui non lo giustificava niente.

| Campo | |
|---|---|
| `tipo` | ⭐ `0x0301` **fotogramma chiave**, `0x0302` **fotogramma delta** (§5.2). Altri valori: `ERRORE_PROTOCOLLO` |
| `codec` | `1` = HEVC, `2` = AV1. **DEVE** essere quello negoziato in §4.3 |
| `largh.`, `altezza` | la misura di **questo** fotogramma. ⛔ In RCP/1 è **sempre quella della tela**, e il client riscala (`SPECIFICHE.md` §6.1). Il campo esiste lo stesso perché il giorno in cui si decidesse di codificare più piccolo quando la finestra è piccola — `DECISIONI.md` §5.0-ter, che è una `[?]` volutamente fuori dal modello — **il protocollo non cambia** |
| `numero` | contatore del fotogramma, crescente, senza buchi voluti |
| `istante` | microsecondi dell'orologio **monotono del server** alla cattura |
| `input` | ⭐ **l'identificatore dell'ultimo input iniettato prima della cattura**; **0** se nessuno |

⛔ **Il tetto**: un fotogramma **NON DEVE** superare **16 MiB**. Chi ne riceve uno più lungo chiude
con `ERRORE_PROTOCOLLO` invece di continuare ad accumulare.

⛔ **L'ordine, e chi lo rimette a posto.** Gli stream sono indipendenti, quindi i fotogrammi
**possono arrivare fuori ordine**. Il client:

- **DEVE** scartare un fotogramma il cui `numero` è **precedente** all'ultimo già consegnato al
  decodificatore;
- **DEVE** trattare `numero` come aritmetica **modulo 2³²**, confrontando le differenze con segno —
  a 60 fotogrammi al secondo il contatore gira dopo due anni e due mesi, e una sessione può durare
  di più;
- **DEVE** riconoscere un **buco** e chiedere una chiave (§5.2).

⚠ **Che cosa il campo `input` dice davvero**, e va scritto qui perché nessuno gli attribuisca di
più: dice quale input era stato **iniettato**, non quale era stato **disegnato**. Che il
compositore l'avesse già reso non è garantito da nessuno. È una stima utile e gratuita — non la
misura del ritardo. Quella la dà il banco ad anello chiuso di `DECISIONI.md` §2.6.

⚠ **E `istante` non è un'ora**: è un orologio monotono che parte da un punto qualunque. Il client
**NON DEVE** confrontarlo con il proprio: solo con altri `istante` dello stesso server.

### 6.3 Sui datagram — l'audio

```
 0        2        4        12                12+…
 ├────────┼────────┼────────┼──────────────────┤
 │ tipo   │ codec  │ istante│ campioni         │
 │ u16    │ u16    │ u64    │                  │
```

| Campo | |
|---|---|
| `tipo` | `0x0401` — l'unico definito in RCP/1 |
| `codec` | `1` = Opus, `2` = PCM (§5.3) |
| `istante` | microsecondi dell'orologio monotono del server, del **primo** campione del blocco |

Un datagram, un blocco di Opus (o di PCM). Nessuna ritrasmissione, nessun riordino: chi riceve
scarta i datagram arrivati in ritardo rispetto a quelli già consumati.

⛔ Un datagram più corto di 12 byte, o con un `tipo` diverso da `0x0401`, si **scarta scrivendolo
nel registro**: ⚠ ed è la seconda eccezione dichiarata a §3, perché un datagram è per definizione
inaffidabile e chiudere la connessione per un pacchetto corrotto sarebbe una punizione della rete,
non del mittente.

---

## 7. I messaggi

### 7.1 Controllo

| Tipo | Nome | Verso | |
|---|---|---|---|
| `0x0001` | `CIAO` | → | versione e capacità del client |
| `0x0002` | `ECCOMI` | ← | versione e capacità del server |
| `0x0003` | `CREDENZIALI` | → | utente, parola d'ordine |
| `0x0004` | `AMMESSO` | ← | |
| `0x0005` | `RESPINTO` | ← | motivo |
| `0x0006` | `ATTACCA` | → | tela, disposizione, vista |
| `0x0007` | `SESSIONE` | ← | stato, tela concessa, desktop |
| `0x0008` | `VISTA` | → | la vista è cambiata: nuove larghezza e altezza |
| `0x0009` | `DISPOSIZIONE` | → | la disposizione di tastiera è cambiata |
| `0x000A` | `CURSORE_FORMA` | ← | forma e punto attivo del puntatore |
| `0x000B` | `ADATTA_TELA` | → | l'utente ha chiesto «adatta il desktop a questa finestra» |
| `0x000C` | `CONGEDO` | ↔ | motivo |
| `0x000D` | `RICHIEDI_CHIAVE` | → | ⭐ *nuovo, 9 ago*: serve un fotogramma chiave (§5.2) |
| `0x000E` | `TELA` | ← | ⭐ *nuovo, 9 ago*: l'esito di `ADATTA_TELA` |

**I corpi** (`CIAO`, `ECCOMI`, `CREDENZIALI`, `AMMESSO`, `RESPINTO`, `ATTACCA`, `SESSIONE` stanno
in §4.3-4.5):

```
VISTA
 ├── u32 larghezza
 └── u32 altezza

DISPOSIZIONE
 └── stringa disposizione            (la forma è quella di §4.5)

ADATTA_TELA
 ├── u32 larghezza
 └── u32 altezza

TELA
 ├── u8  esito        1 = ADATTATA, 2 = RIFIUTATA
 ├── u8  motivo       0 se adattata; altrimenti:
 │                      1 = COMPOSITORE_INCAPACE
 │                      2 = MISURA_FUORI_LIMITI
 │                      3 = NON_ORA
 ├── u32 tela_larghezza      ⚠ la tela in vigore DOPO questo messaggio
 └── u32 tela_altezza

RICHIEDI_CHIAVE
 └── u32 ultimo_numero        l'ultimo fotogramma decodificato, 0 se nessuno

CONGEDO
 ├── u8      motivo           §8.2
 └── stringa dettaglio        per il registro, non per l'utente; può essere vuota
```

⚠ `VISTA` **NON DEVE** far cambiare la tela, e ⛔ **in RCP/1 non cambia nemmeno la misura di quel
che si codifica**: i fotogrammi restano della misura della tela e il client riscala
(`SPECIFICHE.md` §6.1). Serve a due cose — a scegliere quanti bit spendere, perché una finestra
piccola guardata su uno schermo piccolo non ne merita quanti una grande; e a rendere gratuito il
giorno in cui `DECISIONI.md` §5.0-ter venisse chiusa. L'unico messaggio che cambia la tela è
`ADATTA_TELA`, ed è una scelta esplicita dell'utente.

> ⚠ *Chiarito il 9 agosto 2026, e non era una sfumatura.* Questa riga diceva «serve al server per
> sapere **a che misura codificare**», e ci sono due voci di `DECISIONI.md` che si contraddicono
> sullo stesso punto: §5.2 dice che *«il codificatore lavora alla misura della finestra, non della
> tela»*, §5.0-ter dice che *«il server continua a codificare la tela intera e il client la
> rimpicciolisce»* e mette il contrario **volutamente fuori dal modello**, come `[?]`. Vince la
> seconda, perché è quella che regge insieme a `SPECIFICHE.md` §6.1 e §6.3 — dove il ripiego su
> KDE *«non costa una riga in più, perché è lo stesso codice del punto durante la sessione»*, e
> quel codice è la **riscalatura nel client**. La correzione è in `DECISIONI.md` §5.2.

⛔ Se il compositore non sa ridimensionare, il server **DEVE** rispondere ad `ADATTA_TELA` con
`TELA(RIFIUTATA, COMPOSITORE_INCAPACE)`, e il client **DEVE** mostrare la voce come spenta. NON
DEVE fingere che sia riuscito.

⛔ **A ogni `ADATTA_TELA` il server DEVE rispondere con un `TELA`**, riuscito o no. Un silenzio
lascia il client ad aspettare per sempre una risposta che non arriverà, e il sintomo è
«l'applicazione si è piantata».

⛔ **La vista DEVE stare dentro i limiti di §4.5** — pari, e fra 320×240 e 7680×4320 — e la sua
misura non ha nessun vincolo di proporzione con la tela: se le proporzioni non combaciano, si
impagina con le bande (`SPECIFICHE.md` §6.2).

⚠ **Il cambio di tela e le coordinate in volo.** Dopo aver mandato `TELA(ADATTATA)` il server
**DEVE** accettare per **un secondo** coordinate di input valide sulla tela **precedente**,
saturandole alla nuova e scrivendolo nel registro; passato quel secondo, sono
`ERRORE_PROTOCOLLO`. ⭐ È la terza eccezione dichiarata a §3, e c'è perché il cambio di tela è
l'unico momento in cui i due lati hanno legittimamente due verità diverse: gli input partiti prima
che la risposta arrivasse non sono un difetto del client.

### 7.2 Cursore

`CURSORE_FORMA` porta la forma che il client deve disegnare:

```
CURSORE_FORMA
 ├── u16 larghezza          0 = cursore nascosto
 ├── u16 altezza
 ├── i16 attivo_x           il punto che «punta»; può essere negativo
 ├── i16 attivo_y
 └── immagine               larghezza × altezza × 4 byte, BGRA premoltiplicato
```

⛔ `larghezza` e `altezza` **NON DEVONO** superare 256 (§5.5), e la lunghezza del messaggio **DEVE**
valere esattamente `8 + larghezza × altezza × 4`. Una lunghezza che non torna è
`ERRORE_PROTOCOLLO`: è il caso in cui «leggo quel che c'è e vado avanti» produce un cursore fatto
di memoria altrui.

⚠ **La posizione non viaggia mai in questo verso.** La posizione del puntatore è del client, che
lo disegna da sé (`SPECIFICHE.md` §7.1). Qui viaggia solo la **forma**, e il ritardo di un giro di
rete sulla forma è il compromesso accettato.

### 7.3 Input

| Tipo | Nome | |
|---|---|---|
| `0x0101` | `PUNTATORE` | posizione assoluta sulla **tela**, non sulla vista |
| `0x0102` | `PULSANTE` | quale, premuto o rilasciato |
| `0x0103` | `ROTELLA` | assi, in scatti |
| `0x0104` | `LETTERA` | un carattere Unicode |
| `0x0105` | `POSIZIONE_TASTO` | codice di posizione, premuto o rilasciato |

⛔ **Ogni messaggio di input comincia con gli stessi due campi**, e poi ha i suoi:

```
 ├── u32 id             crescente, comincia da 1.  ⛔ 0 è riservato e vuol dire «nessun input»
 └── u64 istante        microsecondi dell'orologio monotono del CLIENT

PUNTATORE          + u32 x  · u32 y            coordinate sulla tela
PULSANTE           + u16 codice · u8 premuto   1 = premuto, 0 = rilasciato
ROTELLA            + i32 asse_x · i32 asse_y   unità da 120 per scatto
LETTERA            + u32 carattere             valore scalare Unicode
POSIZIONE_TASTO    + u16 codice · u8 premuto
```

| | |
|---|---|
| **i codici dei pulsanti e dei tasti** | ⛔ sono quelli di **evdev** (`linux/input-event-codes.h`): `BTN_LEFT` = `0x110`, `KEY_A` = `30`. ⭐ Non è una scelta di comodo: `libei` — cioè l'unico modo che abbiamo di iniettare input in un compositore Wayland — lavora in evdev, e ogni altra convenzione aggiungerebbe una tabella di traduzione che sbaglia in silenzio |
| **la rotella** | ⛔ unità da **120 per scatto**, positive verso l'alto e verso sinistra. È l'unità di `wl_pointer.axis_value120`, quindi non si converte niente. ⚠ E i mezzi scatti esistono: `60` è mezzo scatto e **non DEVE** essere arrotondato a zero |
| **il carattere** | ⛔ un **valore scalare Unicode**: da `0` a `0x10FFFF`, esclusi i surrogati `0xD800`-`0xDFFF`. Fuori intervallo è `ERRORE_PROTOCOLLO` |
| **l'identificatore** | ⛔ cresce di **almeno uno** a ogni messaggio, su tutto il canale di input — non uno per tipo. È quello che torna nel campo `input` dei fotogrammi (§6.2), e con contatori separati non tornerebbe niente |

⛔ **Le coordinate sono sulla tela.** Il client conosce la tela (§4.5) e sa dov'è la sua vista
dentro di essa: la conversione è sua. Il server **NON DEVE** applicare nessuna trasformazione alle
coordinate ricevute, e **DEVE** rifiutare con `ERRORE_PROTOCOLLO` una coordinata fuori dalla tela —
salvo il secondo di grazia di §7.1.

⛔ **`LETTERA` si usa quando si scrive del testo; `POSIZIONE_TASTO` quando è premuto un
modificatore di comando** — Ctrl, Alt, Super. Maiusc e AltGr **non** contano come comando: servono
a fare la lettera, e restano nel percorso di `LETTERA` (`SPECIFICHE.md` §7.3).

⛔ Se una `LETTERA` non è producibile nella disposizione della sessione, il server **DEVE**
scriverlo nel registro e **NON DEVE** mandare un carattere diverso né tacere.

⛔ **Al distacco si rilascia tutto.** Quando una connessione finisce — per congedo, per silenzio,
per errore — il server **DEVE** rilasciare **ogni tasto e ogni pulsante che risultano premuti**.
⭐ È la trappola 11 di `LEZIONI.md` §4 nella sua forma peggiore: un Ctrl rimasto giù in una sessione
che sopravvive al client rende il desktop inservibile al riattacco, e nessuno collega le due cose.

### 7.4 Appunti

| Tipo | Nome | |
|---|---|---|
| `0x0201` | `APPUNTI_ANNUNCIO` | «ho del testo nuovo» |
| `0x0202` | `APPUNTI_CHIEDI` | «mandamelo» |
| `0x0203` | `APPUNTI_TESTO` | UTF-8 |

```
APPUNTI_ANNUNCIO
 └── u32 lunghezza          quanti byte ha il testo disponibile

APPUNTI_CHIEDI               corpo vuoto

APPUNTI_TESTO
 ├── u32 lunghezza
 └── byte                    esattamente `lunghezza` byte di UTF-8 valido
```

Bidirezionale. Si annuncia e si chiede, invece di spingere: chi copia un documento intero non lo
spedisce a nessuno finché qualcuno non incolla.

⛔ Solo `text/plain;charset=utf-8`. Un tipo diverso è `ERRORE_PROTOCOLLO`.

⛔ **Ogni trasferimento va sul suo stream**, e i tre messaggi **non DEVONO** essere mescolati con
quelli di un altro trasferimento. ⚠ Un `APPUNTI_CHIEDI` che arriva quando l'annuncio è già stato
superato da uno più recente si serve **con il testo attuale**, e il mittente lo scrive nel registro:
è la corsa normale fra due persone che copiano, non un errore.

⛔ Un `APPUNTI_TESTO` che nessuno ha chiesto è `ERRORE_PROTOCOLLO`: gli appunti si tirano, non si
spingono.

---

## 8. Il congedo

### 8.1 Si dice, e si verifica dal lato che riceve

⛔ Chi chiude **DEVE** mandare `CONGEDO` con un motivo **prima** di chiudere la connessione QUIC, e
**DEVE** ripetere il motivo nel codice d'errore applicativo della chiusura (§3.1).

⚠ **E questa riga ha un prezzo già pagato.** In v1, per **tre fasi**, il server scriveva compìto
«congedo il client» mentre il client, alla stessa ora, scriveva «errore di rete»: mancava una
seconda chiamata di libreria che nessuno sospettava (`LEZIONI.md` §1.7). Da cui l'obbligo di
collaudo: **il congedo si verifica dal lato che lo riceve**, mai dal registro di chi lo manda.

⚠ **L'unica eccezione è `RESPINTO`** (§4.4), che *è* il congedo dell'autenticazione.

### 8.2 I motivi

| Codice | Nome | Quando |
|---|---|---|
| `0x01` | `CHIUSO_DALL_UTENTE` | l'utente ha chiuso il client |
| `0x02` | `INATTIVITA` | 30 minuti senza input (`SPECIFICHE.md` §5.3) |
| `0x03` | `SESSIONE_ABBANDONATA` | 6 ore senza attacchi |
| `0x04` | `SESSIONE_LOCALE_PREVALSA` | l'utente ha aperto una sessione grafica locale |
| `0x05` | `GIA_ATTIVA_LOCALE` | c'è già una sessione grafica locale |
| `0x06` | `BUDGET_PIENO` | la macchina non ha più capacità di codifica |
| `0x07` | `CREDENZIALI_ERRATE` | |
| `0x08` | `TROPPI_TENTATIVI` | limitazione della frequenza (§4.4-bis) |
| `0x09` | `NIENTE_IN_COMUNE` | nessun codec condiviso |
| `0x0A` | `VERSIONE_INCOMPATIBILE` | |
| `0x0B` | `ERRORE_PROTOCOLLO` | §3 |
| `0x0C` | `SERVER_IN_CHIUSURA` | |
| `0x0D` | `TEMPO_SCADUTO` | ⭐ *nuovo, 9 ago*: un tetto di §4.6 è scaduto |
| `0x0E` | `SESSIONE_NON_SERVIBILE` | ⭐ *nuovo, 9 ago*: l'attacco è ben formato ma non si può servire — un compositore che non parte, una disposizione che il sistema non conosce. **DEVE** portare il dettaglio nel corpo |

⛔ Ogni motivo **DEVE** essere mostrabile all'utente in una frase comprensibile. `BUDGET_PIENO`
non è «errore 6»: è «questa macchina non ha più capacità di codifica».

⛔ **La frase la costruisce il client**, dal codice. Il campo `dettaglio` **NON DEVE** essere
mostrato all'utente: è per il registro, e contiene quel che serve a chi diagnostica.

---

## 9. Le versioni

`CIAO` porta la versione maggiore che il client sa parlare; `ECCOMI` quella scelta dal server.
Se non c'è una versione comune, `VERSIONE_INCOMPATIBILE`.

⛔ **In concreto**: il server sceglie la versione più alta che sa parlare e che non superi quella
del `CIAO`. Se non ne ha nessuna, congeda. Il client **DEVE** verificare che la versione di
`ECCOMI` sia una che sa parlare, e congedare con `VERSIONE_INCOMPATIBILE` se non lo è — un server
che risponde con una versione più alta di quella chiesta sta sbagliando, e accettarla in silenzio
è l'indulgenza che §3 vieta.

**Dentro una versione maggiore si cresce solo per capacità** (§4.3), mai aggiungendo campi a
messaggi esistenti né tipi nuovi che il vecchio dovrebbe ignorare — perché ignorare è vietato
(§3). Un tipo nuovo obbligatorio è una versione maggiore nuova.

⚠ **In pratica, finché client e server si aggiornano insieme, la versione serve a poco.** Serve il
giorno in cui un telefono resta indietro — e quel giorno o si è scritta bene, o si scopre che il
campo in più lo si era aggiunto «tanto è compatibile».

⭐ **E la finestra in cui questo documento si può ancora completare è adesso**: il divieto qui sopra
protegge le implementazioni esistenti, e **oggi non ne esiste nessuna**. I due tipi aggiunti il 9
agosto (`0x000D`, `0x000E`) sono entrati sotto questa clausola. **Dal primo byte scritto in poi
vale la regola senza sconti.**

---

## 10. Che cosa RCP non fa

| | Dove sta scritto |
|---|---|
| non trasporta file, dischi, stampanti, porte | `SPECIFICHE.md` §12 |
| non trasporta immagini negli appunti | §7.4 |
| non ha un canale per il puntatore **relativo** | riservato, non definito in RCP/1 |
| non ha un canale per lo stilo né per il tocco multi-dito | `input.tocco` esiste come capacità e vale sempre `no` |
| non porta l'**audio del microfono** | il verso è previsto in §5, il formato non è definito: `SPECIFICHE.md` §10 lo dà per non urgente |
| non ha compressione propria | la fa il codec, e QUIC cifra |
| non ha un battito applicativo | §2.2 |
| non ha modalità in chiaro | §2 |
| non trasporta il volume | è della sessione, invariante I5 |
| non descrive più di **uno schermo** | il multi-monitor è fuori scope come funzione (`SPECIFICHE.md` §6.5); la tela è una sola, e più grande della vista |

---

## 11. Come si collauda contro questa specifica

Il punto che rende utile tutto il resto. **Client e server NON si collaudano l'uno contro
l'altro**: si collaudano contro questo documento.

| Banco | Che cosa prova |
|---|---|
| **il validatore del filo** | un terzo programma che legge una registrazione della connessione e dice quale byte non è conforme. È l'unico arbitro esterno che avremo |
| **la stretta di mano su due connessioni** | ⛔ **due, mai una**: in v1 un certificato condiviso uccideva il server **alla seconda** connessione, e una prova a connessione singola resta verde per sempre (`LEZIONI.md` §2.1) |
| **il congedo** | verificato **dal lato che riceve**, per ciascuno dei **quattordici** motivi — e per ciascuno si verifica **anche il codice nella chiusura QUIC** (§3.1) |
| **l'anello del ritardo** | il client manda un input che cambia colore allo schermo e guarda i fotogrammi decodificati finché non lo vede (`DECISIONI.md` §2.6) |
| **il rigore** | si manda di proposito un tipo sconosciuto, una lunghezza sbagliata, un messaggio nello stato sbagliato: ⛔ **la connessione deve cadere ogni volta**. Un banco che non prova a violare il protocollo non prova il protocollo |
| ⭐ **il fotogramma abbandonato** | si abbandona un delta di proposito e si verifica che **arrivi una chiave** e che il client non mostri niente di rotto nel frattempo (§5.2). ⚠ Senza questo banco l'abbandono si prova solo su una rete cattiva, cioè quando non lo si sta guardando |
| ⭐ **il credito degli stream** | si tiene una sessione viva **oltre i primi 256 fotogrammi** — cioè oltre i primi quattro secondi — e si verifica che il video non si fermi (§2.3) |
| ⭐ **i tempi della stretta di mano** | si apre una connessione e si tace, per ciascuno dei tre tetti di §4.6 |

⚠ **E il controllo positivo, che qui è facile da dimenticare**: prima di concludere che il
validatore non trova errori, gli si dà una registrazione **con un errore dentro** e si verifica che
lo veda. Uno strumento che non ha mai trovato niente non è uno strumento pulito: è uno strumento
non certificato (`LEZIONI.md` §1.9).

---

## 12. ⏳ Quel che RCP/1 lascia aperto, dichiarato

*Non sono buchi: sono cose che non si chiudono adesso, e il motivo per cui non si chiudono.*

| | Perché non ora | Quando |
|---|---|---|
| **il microfono** | il verso è previsto, il formato no. Chiuderlo adesso significherebbe scrivere una negoziazione che nessuno esercita | quando `SPECIFICHE.md` §10 smetterà di dirlo «non urgente» — e sarà una **versione maggiore nuova**, perché è un canale in più (§9) |
| **il puntatore relativo** | serve alle applicazioni remote che **catturano** il puntatore, e quel caso lo segnala il server. Non è il caso di `Pointer Capture` su Android, che è già coperto (`DECISIONI.md` §5-bis.8) | quando si presenta un'applicazione che lo chiede |
| **il tocco multi-dito** | `input.tocco` esiste e vale `no`. Un posto riservato costa niente; una definizione mai esercitata costa un vincolo | fase A4, se il tocco nativo servirà davvero |
| **il 4:4:4** | è una capacità in più (`video.sottocampionamento`), e la decisione di prodotto è `[?]` (`DECISIONI.md` §2.3) | quando l'utente avrà guardato le due immagini |
| **più schermi** | la tela è una sola. La forma del multi-monitor è «due viste sulla stessa tela», che il protocollo già regge per la tela; mancherebbe solo dire **dove** sta ciascuna vista | mai, finché resta fuori scope |
| `[?]` **la registrazione IANA della porta** | §2.4 | se e quando servirà un numero registrato |

⛔ **E una cosa che non è aperta e va detta perché non venga riaperta per distrazione**: il
**battito applicativo** non manca, è **vietato** (§2.2). Chi lo trova assente e pensa di aggiungerlo
sta per creare due verità sullo stesso fatto.
