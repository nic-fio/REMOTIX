# RCP — Remotix Control Protocol, versione 1

*Scritto il 9 agosto 2026, prima di qualunque riga di codice.*

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

## 1. Il modello, in una pagina

```
        CLIENT                                            SERVER
          │                                                 │
          │  ①  QUIC + TLS 1.3                              │
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
          │  ⑤  ATTACCA (tela, disposizione, capacità)       │
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

---

## 2. Il trasporto

**QUIC**, con **TLS 1.3 obbligatorio**. Non esiste un modo in chiaro e non esiste un ripiego su
TCP.

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
| `max_idle_timeout` | **30 s** | è l'orologio del silenzio: scaduto, il client è staccato |
| `max_datagram_frame_size` | ≥ 1200 | l'audio |
| ALPN | `rcp/1` | ⛔ **DEVE** essere negoziato; una connessione senza è rifiutata |

⛔ **NON DEVE esistere un battito applicativo.** Il tempo di inattività di QUIC fa già quel
mestiere, e un secondo meccanismo produrrebbe due verità sullo stesso fatto.

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

---

## 4. La stretta di mano

### 4.1 Prima ancora: il certificato

Terminata la stretta di mano TLS, e **prima di aprire qualunque stream**, il client:

1. calcola l'impronta SHA-256 della chiave pubblica del server;
2. se ha un ricordo per quell'indirizzo e **coincide** → prosegue;
3. se ha un ricordo e **non coincide** → ⛔ **DEVE** interrompere e avvisare l'utente. NON DEVE
   proseguire da sé;
4. se non ha un ricordo → **PUÒ** proseguire in silenzio e annotare l'impronta.

Il punto 4 è la fiducia al primo incontro, con il rischio dichiarato e accettato in
`SPECIFICHE.md` §4.1.

### 4.2 Il canale di controllo

Il client apre il **primo stream bidirezionale** (identificatore 0). Quello è il canale di
controllo, resta aperto per tutta la connessione, e il suo chiudersi **è** la fine della
connessione.

### 4.3 `CIAO` e `ECCOMI`

| | |
|---|---|
| **CIAO** | client → server. Versione maggiore del protocollo, capacità del client |
| **ECCOMI** | server → client. Versione scelta, capacità del server |

Le **capacità** sono coppie nome-valore. Un nome sconosciuto si ignora (§3, eccezione). I nomi
definiti in RCP/1:

| Nome | Chi lo dichiara | Valori |
|---|---|---|
| `video.codec` | entrambi | elenco fra `hevc`, `av1`, in ordine di preferenza |
| `video.profondita` | entrambi | `8`, `10` |
| `audio.codec` | entrambi | elenco fra `opus`, `pcm` |
| `input.tocco` | client | `si`, `no` — riservato, in RCP/1 vale sempre `no` |
| `appunti.testo` | entrambi | `si`, `no` |

⛔ Se l'intersezione di `video.codec` è **vuota**, il server **DEVE** congedare con
`NIENTE_IN_COMUNE`. NON DEVE ripiegare su un codec non dichiarato.

⚠ `pcm` **DEVE** essere dichiarato da entrambi: è la base sempre disponibile, e serve da controllo
positivo quando Opus non si negozia.

### 4.4 Le credenziali

Un solo messaggio `CREDENZIALI` con utente e parola d'ordine. Il server le passa a PAM.

| Esito | Messaggio |
|---|---|
| ammesso | `AMMESSO` |
| respinto | `RESPINTO` con motivo |

⛔ Il server **NON DEVE** distinguere nel motivo fra «utente inesistente» e «parola d'ordine
sbagliata»: entrambi sono `CREDENZIALI_ERRATE`. E **DEVE** applicare la limitazione della
frequenza dei tentativi prima di rispondere.

### 4.5 `ATTACCA`

| Campo | | |
|---|---|---|
| `tela_larghezza`, `tela_altezza` | pixel | la misura che il client chiede |
| `disposizione` | stringa | la disposizione di tastiera, es. `it` |
| `vista_larghezza`, `vista_altezza` | pixel | la misura in cui il client disegnerà |

Il server risponde `SESSIONE`:

| Campo | |
|---|---|
| `stato` | `NUOVA` oppure `RIPRESA` |
| `tela_larghezza`, `tela_altezza` | ⚠ la tela **concessa**, che può differire da quella chiesta |
| `desktop` | quale compositore, per diagnosi |

⭐ **La tela concessa può essere diversa da quella chiesta**, ed è il caso del ripiego su KDE
< 6.8 (`SPECIFICHE.md` §6.3): la sessione era già viva con un'altra misura e non può cambiarla. Il
client **DEVE** adattarsi riscalando, e il server **DEVE** aver scritto il ripiego nel registro.

Se l'attacco non si può servire, il server congeda con uno dei motivi di §8.2 — mai con un
silenzio, mai con una sessione a metà.

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

---

## 6. Il formato dei messaggi

**Ordine dei byte: rete (big-endian).** Nessun campo a lunghezza variabile fuori da quelli
dichiarati con una lunghezza esplicita.

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

### 6.2 Sugli stream del video

Uno stream, un fotogramma. Nessuna lunghezza: **la fine dello stream è la fine del fotogramma**.

```
 0        2        4        8        12       16       24       32   32+…
 ├────────┼────────┼────────┼────────┼────────┼────────┼────────┼─────┤
 │ tipo   │ codec  │ largh. │ altezza│ numero │ istante│ input  │ dati│
 │ u16    │ u16    │ u32    │ u32    │ u32    │ u64    │ u32    │     │
```

| Campo | |
|---|---|
| `numero` | contatore del fotogramma, crescente, senza buchi voluti |
| `istante` | microsecondi dell'orologio monotono del server alla cattura |
| `input` | ⭐ **l'identificatore dell'ultimo input iniettato prima della cattura** |

⚠ **Che cosa il campo `input` dice davvero**, e va scritto qui perché nessuno gli attribuisca di
più: dice quale input era stato **iniettato**, non quale era stato **disegnato**. Che il
compositore l'avesse già reso non è garantito da nessuno. È una stima utile e gratuita — non la
misura del ritardo. Quella la dà il banco ad anello chiuso di `DECISIONI.md` §2.6.

### 6.3 Sui datagram — l'audio

```
 0        2        4        12                12+…
 ├────────┼────────┼────────┼──────────────────┤
 │ tipo   │ codec  │ istante│ campioni         │
 │ u16    │ u16    │ u64    │                  │
```

Un datagram, un blocco di Opus (o di PCM). Nessuna ritrasmissione, nessun riordino: chi riceve
scarta i datagram arrivati in ritardo rispetto a quelli già consumati.

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

⚠ `VISTA` **NON DEVE** far cambiare la tela. È solo l'informazione che serve al server per sapere
a che misura codificare (`SPECIFICHE.md` §6.1). L'unico messaggio che cambia la tela è
`ADATTA_TELA`, ed è una scelta esplicita dell'utente.

⛔ Se il compositore non sa ridimensionare, il server **DEVE** rispondere ad `ADATTA_TELA` con un
rifiuto motivato, e il client **DEVE** mostrare la voce come spenta. NON DEVE fingere che sia
riuscito.

### 7.2 Cursore

`CURSORE_FORMA` porta la forma che il client deve disegnare:

| Campo | |
|---|---|
| `larghezza`, `altezza` | pixel |
| `attivo_x`, `attivo_y` | il punto che «punta» |
| `immagine` | BGRA premoltiplicato |

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

Ogni messaggio di input porta **`id`** (u32 crescente) e **`istante`** (u64, orologio del client).
L'`id` è quello che torna nel campo `input` dei fotogrammi (§6.2).

⛔ **Le coordinate sono sulla tela.** Il client conosce la tela (§4.5) e sa dov'è la sua vista
dentro di essa: la conversione è sua. Il server **NON DEVE** applicare nessuna trasformazione alle
coordinate ricevute.

⛔ **`LETTERA` si usa quando si scrive del testo; `POSIZIONE_TASTO` quando è premuto un
modificatore di comando** — Ctrl, Alt, Super. Maiusc e AltGr **non** contano come comando: servono
a fare la lettera, e restano nel percorso di `LETTERA` (`SPECIFICHE.md` §7.3).

⛔ Se una `LETTERA` non è producibile nella disposizione della sessione, il server **DEVE**
scriverlo nel registro e **NON DEVE** mandare un carattere diverso né tacere.

### 7.4 Appunti

| Tipo | Nome | |
|---|---|---|
| `0x0201` | `APPUNTI_ANNUNCIO` | «ho del testo nuovo» |
| `0x0202` | `APPUNTI_CHIEDI` | «mandamelo» |
| `0x0203` | `APPUNTI_TESTO` | UTF-8 |

Bidirezionale. Si annuncia e si chiede, invece di spingere: chi copia un documento intero non lo
spedisce a nessuno finché qualcuno non incolla.

⛔ Solo `text/plain;charset=utf-8`. Un tipo diverso è `ERRORE_PROTOCOLLO`.

---

## 8. Il congedo

### 8.1 Si dice, e si verifica dal lato che riceve

⛔ Chi chiude **DEVE** mandare `CONGEDO` con un motivo **prima** di chiudere la connessione QUIC.

⚠ **E questa riga ha un prezzo già pagato.** In v1, per **tre fasi**, il server scriveva compìto
«congedo il client» mentre il client, alla stessa ora, scriveva «errore di rete»: mancava una
seconda chiamata di libreria che nessuno sospettava (`LEZIONI.md` §1.7). Da cui l'obbligo di
collaudo: **il congedo si verifica dal lato che lo riceve**, mai dal registro di chi lo manda.

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
| `0x08` | `TROPPI_TENTATIVI` | limitazione della frequenza |
| `0x09` | `NIENTE_IN_COMUNE` | nessun codec condiviso |
| `0x0A` | `VERSIONE_INCOMPATIBILE` | |
| `0x0B` | `ERRORE_PROTOCOLLO` | §3 |
| `0x0C` | `SERVER_IN_CHIUSURA` | |

⛔ Ogni motivo **DEVE** essere mostrabile all'utente in una frase comprensibile. `BUDGET_PIENO`
non è «errore 6»: è «questa macchina non ha più capacità di codifica».

---

## 9. Le versioni

`CIAO` porta la versione maggiore che il client sa parlare; `ECCOMI` quella scelta dal server.
Se non c'è una versione comune, `VERSIONE_INCOMPATIBILE`.

**Dentro una versione maggiore si cresce solo per capacità** (§4.3), mai aggiungendo campi a
messaggi esistenti né tipi nuovi che il vecchio dovrebbe ignorare — perché ignorare è vietato
(§3). Un tipo nuovo obbligatorio è una versione maggiore nuova.

⚠ **In pratica, finché client e server si aggiornano insieme, la versione serve a poco.** Serve il
giorno in cui un telefono resta indietro — e quel giorno o si è scritta bene, o si scopre che il
campo in più lo si era aggiunto «tanto è compatibile».

---

## 10. Che cosa RCP non fa

| | Dove sta scritto |
|---|---|
| non trasporta file, dischi, stampanti, porte | `SPECIFICHE.md` §12 |
| non trasporta immagini negli appunti | §7.4 |
| non ha un canale per il puntatore **relativo** | riservato, non definito in RCP/1 |
| non ha un canale per lo stilo né per il tocco multi-dito | `input.tocco` esiste come capacità e vale sempre `no` |
| non ha compressione propria | la fa il codec, e QUIC cifra |
| non ha un battito applicativo | §2.2 |
| non ha modalità in chiaro | §2 |

---

## 11. Come si collauda contro questa specifica

Il punto che rende utile tutto il resto. **Client e server NON si collaudano l'uno contro
l'altro**: si collaudano contro questo documento.

| Banco | Che cosa prova |
|---|---|
| **il validatore del filo** | un terzo programma che legge una registrazione della connessione e dice quale byte non è conforme. È l'unico arbitro esterno che avremo |
| **la stretta di mano su due connessioni** | ⛔ **due, mai una**: in v1 un certificato condiviso uccideva il server **alla seconda** connessione, e una prova a connessione singola resta verde per sempre (`LEZIONI.md` §2.1) |
| **il congedo** | verificato **dal lato che riceve**, per ciascuno dei dodici motivi |
| **l'anello del ritardo** | il client manda un input che cambia colore allo schermo e guarda i fotogrammi decodificati finché non lo vede (`DECISIONI.md` §2.6) |
| **il rigore** | si manda di proposito un tipo sconosciuto, una lunghezza sbagliata, un messaggio nello stato sbagliato: ⛔ **la connessione deve cadere ogni volta**. Un banco che non prova a violare il protocollo non prova il protocollo |

⚠ **E il controllo positivo, che qui è facile da dimenticare**: prima di concludere che il
validatore non trova errori, gli si dà una registrazione **con un errore dentro** e si verifica che
lo veda. Uno strumento che non ha mai trovato niente non è uno strumento pulito: è uno strumento
non certificato (`LEZIONI.md` §1.9).
