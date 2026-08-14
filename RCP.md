# RCP — Remotix Control Protocol, versione 1

*Scritto il 9 agosto 2026, prima di qualunque riga di codice.*
*Completato il 9 agosto 2026, dopo il censimento di §0-bis — sempre prima di qualunque riga di codice.*

> ## 0. ⛔ Perché questo documento esiste, e perché viene prima
>
> *⚠ Il numero è del 10 agosto 2026, rilievo **R11.18**: quattro righe di questo documento
> (§3, §5.2, §7.5, §11.1) e una di `fasi/01-filo-nudo.md` citavano «§0» come l'argomento portante,
> e §0 non esisteva — la numerazione cominciava da §0-bis. Adesso esiste, e non cambia una parola
> del testo.*
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
| corpi di messaggio definiti byte per byte | 2 su 22 | **26 su 26** (§6, §7) — ⚠ *diceva «22 su 22», e il conto era della prima stesura: i due tipi aggiunti il 9 agosto portavano il totale a 24, e i **due della funzione di banco** (§7.5, la notte del 9) a **26**. Corretto dal rilievo **R1.29**, e non è pedanteria — quella casella è **l'unica prova che il documento porta di essere completo**, e chi la verificava contando ne trovava di più* |
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

> ### ⭐ Sette righe entrate il **12 agosto 2026**, dalla sotto-fase F2.4 della fase 2
>
> *Trovate scrivendo il banco del canale video **prima** del prodotto, e proposte in
> [`fasi/rapporti/F2-4-filo.md`](fasi/rapporti/F2-4-filo.md) col testo pronto; applicate qui dal
> coordinatore. ⛔ **Nessuna aggiunge un tipo di messaggio, un motivo di congedo o un campo a un
> messaggio esistente**: la clausola di §9 è consumata dal 10 agosto, e ogni riga sta dentro quel
> divieto.*
>
> ⚠ **Quattro sono letture doppie vere** — due implementazioni conformi producono **byte diversi per
> lo stesso ingresso** — e **tre sono regole derivate**, che si ricavano da §1 e §3 ma che nessuna
> riga scrive. Confonderle gonfierebbe il conto: una regola derivata non fa divergere due
> implementazioni attente, una lettura doppia sì.
>
> | | Dove | Che cosa chiude |
> |---|---|---|
> | ⭐ **P2** | §6.2 `numero` | *lettura doppia, la più grave*: il contatore non diceva **da dove parte**, e §7.1 dà allo `0` il significato «nessun fotogramma» ⇒ `RICHIEDI_CHIAVE(0)` voleva dire **due cose** — il valore sentinella implicito che §6.0 vieta |
> | ⭐ **P6** | §5.2 | *lettura doppia, e morde nella fase 2*: un **delta in apertura** era conforme a ogni riga, e il client **non aveva modo di accorgersene** — nessun buco nei `numero`, e il decodificatore non solleva errori |
> | ⭐ **P5** | §6.2 `largh.`/`altezza` | *lettura doppia*: *«è sempre quella della tela»* **descrive** e non comanda, e nessuna riga diceva che cosa fa **chi riceve** una misura diversa — chiudere o riscalare |
> | ⭐ **P3** | §2.5 riga `0x03` | *lettura doppia*: §2.5 vieta per nome il controllo su uno stream unidirezionale e l'audio su uno stream, ma **per il video non diceva su che stream viva** |
> | **P1** | §2.5 riga «video» | *derivata*: per chi **riceve** si ricava da §1 e §3; per chi **manda** non si ricavava da nessuna parte — ed è l'invariante **I3** lasciata senza una riga sul filo |
> | **P4** | §6.2 | *derivata*: un **FIN prima dei 28 byte** non è un fotogramma corto, è una lunghezza che non torna |
> | ⭐ **P7** | §11.1 | *trovata dall'**arbitro meccanico***, non da una rilettura: la registrazione non portava **come si è chiuso lo stream**, e senza quel byte un fotogramma abbandonato e uno troncato per errore sono identici — la forma **E8**, rientrata dalla finestra |
>
> ### ⛔⛔ E due ore dopo, DUE DI QUESTE SETTE ERANO SBAGLIATE — corrette lo stesso giorno
>
> *E non le ha trovate una rilettura: le ha trovate **chi doveva farle rispettare**, cioè l'agente che
> propagava le sette righe ai due arbitri. Applicare una regola è un modo di leggerla che rileggerla
> non è.*
>
> ⛔ **P5 uccideva una sessione sana.** La riga scriveva *«DEVONO valere la tela concessa in
> `SESSIONE`»*, ⚠ ma §7.1 ha `ADATTA_TELA`, e `TELA` risponde con *«la tela in vigore **dopo** questo
> messaggio»*. ⇒ `SESSIONE` concede 1920×1080 · l'utente trascina la finestra · il client manda
> `ADATTA_TELA(1280,720)` · il server risponde `TELA(ADATTATA…)` e cattura a quella misura · il
> fotogramma porta `largh. = 1280` · ⛔ **e il client lo rifiuta e chiude**. Un server conforme a §7.1
> ucciso da un client conforme a §6.2 — ed è **esattamente la scena che §7.1 protegge** con la sua
> eccezione 4: *«l'utente che trascina male una finestra non deve perdere la sessione»*. ⭐ La cura è
> **una parola**: «la tela **in vigore**» al posto di «la tela concessa in `SESSIONE`».
>
> ⚠ **E P2 riportava in circolo il valore che aveva appena riservato.** L'aritmetica di `numero` è
> **modulo 2³²** e §6.2 dichiara che una sessione può durare più di un giro del contatore: al giro,
> `0xFFFFFFFF` passa a **`0`**, che P2 aveva riservato due ore prima, e nessuna riga diceva di
> saltarlo. Curato: **da `0xFFFFFFFF` si passa a `1`**.
>
> ⇒ ⭐ **Cinque righe su sette erano giuste, due no — e il costo di scoprirlo è stato scriverne il
> banco.** È il momento 1 di `PIANO.md` §0.4 che funziona nel verso in cui nessuno se lo aspetta: il
> banco non ha trovato un difetto nel prodotto, ha trovato **un difetto nell'arbitro**.

⛔ **E la finestra per farlo È CHIUSA**: §9 vieta di aggiungere tipi di messaggio dentro una
versione maggiore, e quel divieto protegge le implementazioni esistenti. **Adesso esistono.** Da qui
in poi questo documento si tocca **solo** come dice §9, senza sconti.

> ⚠ *Questa riga diceva* «⭐ **E la finestra per farlo è adesso** … quel divieto protegge le
> implementazioni esistenti, e **oggi non ne esiste nessuna**» — *e §9 diceva la stessa cosa con le
> stesse parole. Era vero fino al 10 agosto 2026; il primo byte è stato scritto quel giorno, e le
> due righe sono rimaste indietro. **Chi le avesse lette dopo avrebbe aggiunto un tipo di messaggio
> con la benedizione scritta dell'arbitro**, cioè lo strappo che §12 dichiara di aver chiuso.
> Corrette l'11 agosto 2026, rilievo **R12C.2**.*
>
> ⛔ **Le implementazioni di RCP/1 che esistono, contate l'11 agosto 2026** `[M]` (`wc -l`,
> `md5sum`):
> · `src/rcp.c` + `rcp.h` — `[M]` **12 agosto 2026: 2.764 / 239 righe** (erano 2.592 / 197 l'11);
> · `banchi/rcp/rcp.c` + `rcp.h` — **identici byte per byte** (`md5` `6d858886…` e `62415feb…`,
>   erano `1adce15b…` e `0458f154…`);
>
> ⚠ *I numeri sono cresciuti per la cura di `DECISIONI.md` §1.10 — la verifica PAM fuori dal filo
> unico — e ⛔ **il filo non è cambiato di un byte**: questa è una casella di **censimento**, non una
> riga normativa, e va riallineata quando il codice cresce o diventa una misura che descrive il
> codice di ieri. Riallineata il 12 agosto 2026, su segnalazione dell'agente che ha fatto la cura.*
>   ⚠ *`rcp.c` diceva **2.566 righe** e `md5` `cb7af778…`: sono cambiati la tarda serata dell'11
>   agosto 2026, per la riga di registro del **posto lasciato** sulla strada del congedo — la cura
>   sta nel codice, commentata. ⛔ E i due numeri si aggiornano **insieme**, o la riga che dichiara
>   l'identità delle due copie diventa una promessa che nessuno verifica: a farla rispettare è il
>   `Makefile`, che confronta `src/` con `banchi/rcp/` e si ferma se divergono.*
> · `banchi/01-b3-cliente.py` — **il secondo lettore**, in un altro linguaggio;
> · `src/pagina.html` — il terzo, in JavaScript;
> · e due che leggono il formato senza parlarlo: `banchi/01-b4-validatore.py` (l'arbitro meccanico)
>   e `banchi/01-b11-pagina.html`.

---

## 1. Il modello, in una pagina

```
        CLIENT                                            SERVER
          │                                                 │
          │  ⓪  la PAGINA, in TCP     porta 7447             │
          │◀──── e qui l'utente vede l'avviso, una volta ────│
          │                                                 │
          │  ①  WebTransport su HTTP/3   UDP 7447            │
          │────────────────────────────────────────────────▶│
          │  ② il BROWSER verifica l'impronta che            │
          │     la pagina gli ha dichiarato                  │
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
deliberatamente, e che vanno usate **invece** di reimplementarle (`SPECIFICHE.md` §2 punto 3,
*«dipendere, non riscrivere»* — ⚠ *questa riga citava un «§2.3» che in `SPECIFICHE.md` non esiste:
§2 non ha sottosezioni. Corretto il 10 agosto 2026, rilievo **R11.18***).

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

⛔ **E le due DEVONO coincidere**: un `CIAO(versione=2)` su `/rcp/1` è `VERSIONE_INCOMPATIBILE`, non
una negoziazione da risolvere. Un percorso sconosciuto si rifiuta con **404**.

> ⚠ *Le due righe qui sopra sono della sera del 9 agosto 2026, rilievo **R1.24**.* Il documento
> diceva che il percorso «non sostituisce» il controllo, e **non diceva che i due dovessero
> concordare**: §9 fa scegliere al server la versione più alta che non superi quella del `CIAO`,
> quindi un `CIAO(2)` su `/rcp/1` produceva tre esiti tutti difendibili — `ECCOMI(2)`,
> `ERRORE_PROTOCOLLO`, `VERSIONE_INCOMPATIBILE`. E lo stato HTTP del rifiuto non era scritto: 404,
> 400 e 421 erano tutti leciti, e la pagina non li distingue.

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
| **il server DEVE concedere credito** al client per i suoi stream unidirezionali: almeno **16** disponibili in ogni momento — ⛔ **cioè almeno 19 dichiarati al livello QUIC** (vedi il riquadro) | il client apre uno stream di input e uno per ogni trasferimento di appunti. Se il credito finisse, **l'input non partirebbe affatto** e il sintomo sarebbe «il desktop non risponde» |

> ### ⛔ I 16 sono **disponibili a RCP**, non dichiarati sul filo — e la differenza è di tre
>
> *Aggiunto l'11 agosto 2026, rilievo **A** del punto 4 della sessione. La riga qui sopra diceva
> «almeno 16» e basta: ⛔ **chi la implementava alla lettera scriveva `initial_max_streams_uni = 16`
> ed era conforme al documento e in violazione della sua ragione.** È il difetto **B-12**, trovato
> nel prodotto la notte del 10 agosto e curato lì — e l'arbitro non lo diceva.*
>
> ⛔ **WebTransport non ha un credito suo.** Nelle bozze ≤ 07 ogni stream unidirezionale di
> WebTransport **è** uno stream unidirezionale di QUIC, sullo stesso contatore di HTTP/3. E HTTP/3
> se ne prende **tre** appena la connessione nasce — il suo stream di controllo e i due di QPACK —
> e ⛔ **non li chiude mai**.
>
> ⇒ **16 dichiarati = 13 disponibili a RCP**, e i tre stream mancanti si perdono in silenzio: il
> sintomo non è un errore ma *«il desktop non risponde»*, cioè il sintomo che questa riga esiste per
> impedire.
>
> | | |
> |---|---|
> | quel che il server **dichiara** in `initial_max_streams_uni` | ⛔ **almeno 19** |
> | quel che resta a RCP dopo i tre di HTTP/3 | **16**, che è il numero normativo |
> | ⚠ e il conto **non si crede, si misura** | la sonda del trasporto conta gli unidirezionali che il pari ha davvero aperto e giudica `dichiarati − contati ≥ 16`. `[?]` **su un browser i tre potrebbero essere di più** — uno stream di *grease*, per dire — e nessuno l'ha misurato |
>
> ⚠ **E il numero giusto è 19 anche quando sembra generoso**: le due parole che decidono in questa
> riga sono **«disponibili»** — non «dichiarati» — e **«in ogni momento»**. La lettura che salva il
> 16 rende parole morte tutt'e due.
| **il server DEVE reggere il rifiuto di aprire uno stream** invece di considerarlo un errore fatale | il video consuma **uno stream per fotogramma**: a 60 al secondo, il credito che il browser concede si consuma in fretta |

> ### ⛔ «Il credito viene rinnovato mano a mano che gli stream si chiudono» — **FALSO, e misurato**
>
> *13 agosto 2026, fase 3. La riga qui sopra finiva così, e chi la leggeva ne ricavava una
> garanzia: chiudi gli stream e il posto torna. ⛔ **Non torna per forza.***
>
> ⛔ **Il rinnovo del credito è POLITICA DEL PARI, non una conseguenza della chiusura.** Chiudere uno
> stream non restituisce niente da sé: il limite sale **solo** quando il pari decide di mandare un
> `MAX_STREAMS` più alto, e **quando** lo manda lo decide lui. `[M]` **con il rinnovo del pari
> spento, il credito resta fermo anche a stream tutti chiusi.** ⇒ La riga vecchia non descriveva il
> protocollo: descriveva un pari gentile.
>
> ⇒ **Che cosa resta normativo, e non cambia**: il server **DEVE reggere il rifiuto** di aprire uno
> stream (riga qui sopra) e **DEVE** buttare il fotogramma — mai una chiave (riga qui sotto). ⛔ Quel
> che cade è la **rassicurazione**: non si scrive codice che *aspetta* il posto contando sul rinnovo,
> perché il rinnovo non è nostro e può non arrivare.
>
> ⛔⛔ **E NON si scrive che il prodotto cade sotto credito basso: non è misurato.** *Un giro del 13
> agosto ha prodotto uno `STREAM_LIMIT_ERROR`, e per qualche ora è sembrato un difetto del prodotto.
> Non lo era: il **banco** annunciava il credito **dopo** la stretta di mano — cosa che RFC 9000 §4.6
> vieta — quindi il `6` **non è mai stato annunciato sul filo**. Il server aveva **128 posti
> concessi** e ne ha aperti **14**. ⇒ **`ngtcp2` non ha violato niente, e lì il prodotto non ha un
> difetto.** Quel che regge di quella giornata è la riga qui sopra, che è un'altra cosa.*
>
> ⭐ **E cercando il difetto falso ne è uscito uno vero, ed era peggiore: `B-18`.** Uno dei tre
> percorsi di abbandono di un delta — proprio quello **per mancanza di posto** — **non accendeva la
> richiesta di chiave**. ⛔ **Un solo delta saltato per credito esaurito sfasciava l'immagine per
> sempre e in silenzio**, e la catena del silenzio è questa: il fotogramma non è mai stato spedito
> ⇒ il `numero` **non è consumato** (§6.2) ⇒ **nessun buco** nella successione ⇒ il client non ha di
> che accorgersene e **non può chiedere la chiave** ⇒ e con un GOP infinito non ne arriva più una da
> sola. ⇒ **È la ragione per cui la riga qui sotto obbliga il server a produrre la chiave da sé**:
> in questo caso il client non ha nessun modo di chiederla.
| ⛔ **e quando il credito manca si butta il fotogramma — ma MAI una chiave** | aspettare un posto libero è una coda, e ogni coda **compra fluidità e vende risposta** (`SPECIFICHE.md` §3.2). Un **delta** vecchio non serve più: ne sta già arrivando uno nuovo. ⛔ Un fotogramma **chiave** invece si aspetta, perché è l'unica cosa che rimette in piedi il decodificatore (§5.2). E in tutt'e due i casi **si scrive nel registro** |

> ⛔ *Corretta la sera del 9 agosto 2026, rilievo **R1.9**, e la sequenza che la rompeva è questa.*
> La linea peggiora, il server abbandona un delta e — come §5.2 gli impone — prepara subito una
> **chiave**. In quel momento il credito è esaurito, perché è la stessa condizione che ha prodotto
> l'abbandono. La riga vecchia ordinava di **buttare**: il fotogramma buttato era la chiave, che
> §5.2 vieta di abbandonare con un ⛔. Due righe normative opposte, e nessuna citava l'altra.
>
> ⚠ E il caso si richiudeva su sé stesso: il client chiede una chiave, il server la produce, il
> credito manca ancora, la butta ancora — **schermo fermo, e nessuna riga nel registro che dica
> perché**, perché l'obbligo di registro di §5.1 parla di *abbandono* e lì lo stream non era mai
> nato. Ora l'obbligo copre tutt'e due i casi.
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

> ⛔ **Corretto il 9 agosto 2026 dalla misura S1** — questa riga diceva: *«il server DEVE annunciare
> `Alt-Svc: h3=":7447"` sulla risposta TCP, o il browser non passerà mai a QUIC»*. **È falsa**, ed
> era mia: **WebTransport non usa `Alt-Svc` affatto** — zero occorrenze nelle tre specifiche, con
> controllo positivo `[S]`. Una sessione WebTransport apre **la sua** connessione HTTP/3 verso
> l'indirizzo che le si dà, senza scoperta e senza negoziazione a monte.
>
> ⭐ **E toglie di mezzo un pericolo che avevo dichiarato**: il ripiego silenzioso su TCP — «la
> pagina si apre e il desktop non arriva mai» — **non può accadere**, perché non c'è nessun ripiego
> da fare.

⚠ **Il TCP serve solo a consegnare la pagina**, e le basta HTTP/1.1. Da lì in poi il browser apre
la sessione WebTransport per conto suo, sull'UDP.

⚠ Scelta il 9 agosto 2026 verificando che sia libera in `/etc/services` di Debian Trixie `[M]`.
`[?]` **Non è stata verificata la registrazione IANA**: se un giorno servisse un numero
registrato, questa riga si cambia senza toccare nient'altro.

### 2.5 ⛔ Gli stream: chi apre che cosa, e come si riconoscono

*Questo paragrafo chiude il buco più insidioso del censimento: chi riceve uno stream
unidirezionale deve sapere **che cosa** c'è dentro prima di leggerlo, e non c'era scritto da
nessuna parte.*

| Stream | Chi lo apre | Quanti |
|---|---|---|
| **controllo** — il **primo** stream bidirezionale della sessione | il client | uno solo, per tutta la sessione |
| **video** — unidirezionale | il server | uno **per fotogramma**, ⛔ e **nessuno prima di aver spedito `SESSIONE`**. ⚠ Il divieto vincola **chi manda**: chi riceve non lo può misurare sull'ordine in cui gli arrivano le cose, perché il canale di controllo e lo stream del fotogramma sono **due stream QUIC indipendenti** e niente ne ordina la consegna (§6.2). ⇒ Il client dichiara `ERRORE_PROTOCOLLO` **solo** se non ha ancora spedito `ATTACCA`: §4.5 fa di `SESSIONE` la risposta ad `ATTACCA`, quindi lì il server **non può** averla spedita, e il client lo sa **senza guardare la rete**. ⛔ Se `ATTACCA` è partito e `SESSIONE` non è ancora arrivata il client **NON DEVE chiudere**: **trattiene** il fotogramma e lo scrive nel registro, e lo giudica quando `SESSIONE` arriva — che arriva per forza, perché il canale di controllo è affidabile e ordinato e §4.5 vieta al server di rispondere con un silenzio. ⚠ E l'invariante **I3** resta intera: chi ha spedito `ATTACCA` è già passato da `AMMESSO`, cioè dal validatore |

> ### ⛔ La riga qui sopra è stata riscritta il **13 agosto 2026** — rilievo **P20**
>
> *Diceva:* «*chi ne riceve uno prima chiude con `ERRORE_PROTOCOLLO`*». ⛔ **E «chi ne riceve uno
> prima» è una grandezza sostitutiva**: chi riceve non ha altro da misurare che l'ordine in cui il
> proprio strato di rete gli consegna gli eventi, e i due stream sono indipendenti. ⇒ Bastava
> **perdere il pacchetto che porta `SESSIONE`** perché un client conforme uccidesse una sessione in
> cui il server aveva fatto tutto giusto — **I1 rotta perché la linea perde pacchetti**, cioè la
> condizione che I1 esiste per proteggere.
>
> ⚠ *È la **sesta** della famiglia* **P8 → P11 → P13 → P14 → P19 → P20** *(`LEZIONI.md` §1.13). E
> anche la prima cura proposta — «solo se, quando il fotogramma arriva, i byte di `SESSIONE` non sono
> ancora arrivati» — restava un sostituto: sposta la misura dal risveglio della coroutine ai byte, e
> **i byte li ritarda la rete**. Sarebbe stata la settima stesura.*
>
> ⭐ **La grandezza vera è quel che il client ha spedito LUI** — `ATTACCA` — ed è la forma generale
> del campo `numero` di P14: **locale, monotona, indipendente dalla consegna**. ⛔ E non l'ha trovata
> una rilettura: l'ha trovata il **cliente di prova** al suo primo giro contro un server che
> spedisce davvero.
| **input** — unidirezionale | il client | **uno solo**, aperto ⛔ **dopo aver ricevuto `SESSIONE`** e tenuto aperto |
| **appunti** — unidirezionale | entrambi | uno **per trasferimento** |

⛔ **Il client NON DEVE aprire stream bidirezionali oltre lo 0. Il server NON DEVE aprire stream
bidirezionali.** Chi ne riceve uno chiude con `ERRORE_PROTOCOLLO`.

> ### ⛔⛔ Prima di leggere: **i «primi due byte» non sono i primi byte dello stream** — rilievo P18
>
> *12 agosto 2026. Trovato dal **cliente di prova**, al suo primo giro dal vivo, e non da una
> rilettura: `[M]` il giro è finito rosso con «canale di controllo mai aperto», e la causa era che
> il cliente applicava questa riga **alla lettera**.*
>
> ⛔ Su WebTransport ogni stream porta un **preambolo**: il tipo di stream (`0x54` per gli
> unidirezionali, `0x41` per i bidirezionali, in codifica variabile — sul filo `40 54` e `40 41`)
> seguito dal **numero della sessione**. ⇒ Chi legge i «primi due byte» **dello stream** ricava
> canale `0x40`, che non è nessuno dei cinque, e **chiude ogni fotogramma con
> `ERRORE_PROTOCOLLO`**.
>
> ⇒ **I due byte sono i primi del carico RCP**, cioè quel che resta **dopo** il preambolo di
> WebTransport, che lo strato di trasporto consuma e non consegna.
>
> ⚠ **E questo è il difetto muto che §0 di questo documento esiste per impedire.** Il server e la
> pagina andavano d'accordo **perché li ha scritti la stessa mano**: nessuno dei due leggeva questa
> riga, e la riga era falsa. ⭐ A trovarlo è stato **l'unico lettore che RCP.md l'ha letto senza
> guardare il codice** — cioè precisamente il pezzo di arbitro che `PIANO.md` §1.1 dice di aver
> comprato al posto di `mstsc`, e che qui ha ripagato il proprio costo alla prima esecuzione.

⭐ **Come si riconosce il canale**: si leggono i **primi due byte del carico RCP** — cioè quel che
resta **dopo** il preambolo di WebTransport (§2.4), che il trasporto consuma — e sono in ogni
caso un campo `tipo` (§6). Il byte alto dice il canale:

| Byte alto di `tipo` | Canale | Che cosa segue |
|---|---|---|
| `0x00` | controllo | l'inquadratura di §6.1 — e su uno stream unidirezionale è `ERRORE_PROTOCOLLO`: il controllo vive solo sul **primo stream bidirezionale della sessione** (§4.2) |
| `0x01` | input | l'inquadratura di §6.1, un messaggio dopo l'altro |
| `0x02` | appunti | l'inquadratura di §6.1 |
| `0x03` | video | l'intestazione di 28 byte di §6.2, **senza** inquadratura — ⛔ e **solo su uno stream unidirezionale aperto dal server**: un `0x03` sul canale di controllo è `ERRORE_PROTOCOLLO`, come lo è un `0x00` su uno stream unidirezionale |
| `0x04` | audio | ⛔ solo su datagram (§6.3). Su uno stream è `ERRORE_PROTOCOLLO` |

⛔ Un byte alto diverso da questi cinque è `ERRORE_PROTOCOLLO`. E un canale usato **nel verso
sbagliato** — un `0x01` che arriva dal server, un `0x03` che arriva dal client — lo è a sua volta.

> ⛔ *Corretto il 10 agosto 2026, rilievo **R11.9**: la riga del `0x00` diceva «il controllo vive
> solo sullo **stream 0**», ed era il resto della stesura a QUIC nudo che §4.2 aveva già tolto la
> sera del 9 agosto (rilievo R1.5). Il rilievo R1.5 nominava **anche** questa sezione, e la cura
> era stata applicata a uno solo dei due luoghi.*
>
> ⛔ **Il canale si riconosce dal byte alto di `tipo`, mai dal numero dello stream**, e la seconda
> risposta alla stessa domanda era rimasta qui dentro — cioè nella sezione che §0-bis presenta come
> la cura del «buco più insidioso». Chi implementava §2.5 alla lettera scriveva un ricevente che
> cerca il canale di controllo per numero, e la diagnosi che ne usciva era *«il client non apre il
> canale»* **mentre il client lo aveva aperto**. ⚠ *La stessa parola sopravviveva nella tabella di
> §5, ed è stata tolta lì insieme a questa.*

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

⚠ **Le eccezioni sono otto, e sono tutte qui.** Fuori da questo elenco non se ne inventano:

| # | Dove | Che cosa si tollera, e perché |
|---|---|---|
| 1 | §4.3 | una **capacità** sconosciuta — nome o valore — si ignora: è il meccanismo con cui le versioni future si capiscono. ⚠ È ignorare *un'offerta*, non *un comando* |
| 2 | §6.3 | un **datagram** corrotto o troppo corto si scarta invece di chiudere: è per definizione inaffidabile, e punirlo punirebbe la rete |
| 3 | §7.1 | dopo un cambio di tela, **un secondo di grazia** sulle coordinate vecchie: è l'unico momento in cui i due lati hanno legittimamente due verità |
| 4 | §7.1 | una misura **fuori limiti** in `ADATTA_TELA` si rifiuta con `TELA(MISURA_FUORI_LIMITI)` invece di chiudere. ⚠ *Non era dichiarata (rilievo **R1.10**): lo stesso valore fuori intervallo uccide la connessione in `ATTACCA` e non in `ADATTA_TELA`, e la differenza è voluta — **l'utente che trascina male una finestra non deve perdere la sessione*** |
| 5 | §5.2 e §7.4 | una `RICHIEDI_CHIAVE` ripetuta entro 200 ms **si può ignorare**, e un `APPUNTI_CHIEDI` fuori tempo **si serve** invece di essere un errore. ⚠ *Nemmeno queste erano dichiarate (rilievo **R1.15**)* |
| 6 | §6.2 | dopo un cambio di tela si tollerano i fotogrammi che portano **una misura che è stata in vigore da quando la coda ha cominciato a svuotarsi**, e la tolleranza finisce quando arriva **la prima chiave alla misura nuova** (§5.2), non a orologio. Sono partiti prima che il `TELA` arrivasse, e gli stream sono indipendenti. ⚠ *È l'eccezione 3 scritta per l'altro verso del filo — quella copre le coordinate che salgono, questa i fotogrammi che scendono. Senza, la cura di **P5** del 12 agosto 2026 fa chiudere il client davanti a un server conforme a §7.1* |
| 7 | §2.5 | uno **stream video arrivato prima di `SESSIONE`** quando l'`ATTACCA` è già partito **non chiude**: si **trattiene** e si giudica quando `SESSIONE` arriva. ⚠ *L'ordine fra due stream QUIC non è quello del filo, e bastava un pacchetto perso perché un client conforme uccidesse una sessione sana — rilievo **P20*** |
| 8 | §6.2 | un fotogramma la cui misura **nessuna tela ha mai avuto** **non chiude** finché resta una **`ADATTA_TELA` senza risposta**: si **trattiene** e si rigiudica quando il `TELA` arriva, riuscito o rifiutato. ⚠ *Perché §4.5 permette al server di concedere una tela **diversa da quella chiesta** — rilievo **P21*** |

> ⛔ **Le righe 7 e 8 sono entrate il 13 agosto 2026, rilievo P22 — ed erano già comandate altrove.**
> §2.5 e §6.2 ordinavano quelle due tolleranze mentre **questo elenco dichiarava che le eccezioni
> erano sei e che fuori di qui non se ne inventano**. ⇒ Un client scritto leggendo §3 **chiudeva**
> proprio le sessioni sane che le altre due righe salvavano.
> ⚠ *È la seconda volta che questo elenco resta indietro: la prima fu **P12**, il 12 agosto. ⭐ Da qui
> la regola: **chi scrive una tolleranza altrove aggiunge la riga qui nello stesso momento**, o le due
> metà si separano — ed è la forma che questo documento paga più spesso.*

⛔ **E ogni tolleranza va scritta nel registro.** Una tolleranza silenziosa è indistinguibile da un
difetto, ed è precisamente l'indulgenza che questa sezione esiste per togliere.

### 3.1 Che cosa vuol dire «chiudere», in byte

*Aggiunta il 9 agosto 2026: «chiude la connessione» ammetteva almeno tre implementazioni diverse,
e due di esse fanno sparire il motivo proprio quando serve.*

Chi rileva la violazione, **in quest'ordine**:

1. **DEVE** scrivere nel registro *che cosa* non ha capito — il tipo ricevuto, la lunghezza, lo
   stato in cui si trovava. Non «errore di protocollo»;
2. **DEVE** mandare `CONGEDO` (§8) con il motivo, sul canale di controllo, **se il canale di
   controllo è ancora utilizzabile**;
3. **DEVE** chiudere la **sessione WebTransport** con il codice d'errore applicativo pari al
   **codice del motivo** di §8.2.

> ⛔ *Corretto la sera del 9 agosto 2026, rilievo **R1.4**.* Questa riga diceva «la connessione QUIC
> con `CONNECTION_CLOSE` di tipo applicativo». **Una pagina non lo può fare**: l'API espone la
> chiusura *della sessione*, con il proprio codice, non quella della connessione HTTP/3 sotto — che
> può reggere altro. Erano due piani diversi, e §8.1 imponeva la regola anche al client, cioè a chi
> non ha l'API. Un programmatore chiudeva la sessione e dichiarava assolta la regola; l'altro
> cercava l'API della connessione, non la trovava, e lasciava il punto 3 non implementato — **ed era
> conforme al testo quanto il primo**.

⭐ **Il terzo punto è quello che salva le diagnosi**: se il congedo non arriva — perché lo stream
era rotto, perché il messaggio era illeggibile — il motivo viaggia comunque, dentro la chiusura
della sessione. In v1 il server scriveva «congedo il client» e il client leggeva «errore di rete»
per **tre fasi** (`LEZIONI.md` §1.7): qui i due lati hanno due strade per dirsi la stessa cosa, e
il collaudo di §11 verifica **dal lato che riceve** che almeno una delle due sia arrivata.

⚠ Il codice **0** significa «chiusura senza motivo» e **NON DEVE** essere usato: ogni chiusura ha
un motivo di §8.2.

---

## 4. La stretta di mano

### 4.1 Prima ancora: il certificato

> ### ⭐ Riscritta due volte il 9 agosto 2026 — e la seconda volta da una misura
>
> **Prima stesura**: quattro passi che il client doveva implementare — calcola l'impronta,
> confronta col ricordo, interrompi se cambia, accetta in silenzio se non c'è.
>
> **Seconda**: «quei passi li fa già il browser, non è più codice nostro».
>
> ⛔ **Terza, ed è quella buona**: per il caricamento della **pagina** è vero, per la sessione
> **WebTransport no** — l'eccezione dell'utente non la copre né su Chrome né su Firefox `[R]`
> (misura **S1**, `web/rapporti/S1-certificato.md`). Quindi il certificato della sessione
> **si dichiara**, e il posto dove dichiararlo è la pagina.

**Quel che resta normativo, ed è tutto dalla parte del server:**

| | |
|---|---|
| **la chiave** | **DEVE** essere **ECDSA P-256**. ⛔ Non Ed25519 e **mai RSA**: P-256 è l'unica che tiene aperta anche la strada di `serverCertificateHashes` `[S]`, e una chiave scelta oggi per comodità chiuderebbe quella porta senza che nessuno se ne accorga |
| **la generazione** | il server se lo genera all'installazione, e tiene la chiave privata con permessi `0600` |
| **il nome** | il certificato **DEVE** portare come `subjectAltName` l'indirizzo su cui il server risponde — nome o indirizzo IP. ⚠ Un browser che trova un `SAN` che non combacia mostra **un avviso diverso**, e alcuni non offrono nemmeno il clic per proseguire |
| **il certificato vero** | se l'amministratore ne installa uno emesso da un'autorità, il server **DEVE** usarlo e **non DEVE** rigenerare il proprio. È la strada senza avvisi (`SPECIFICHE.md` §4.1) |

⛔ **E due certificati, non uno** — la regola sta in §4.1-bis, e va letta prima di scrivere il
server.

> ⛔ *Corretto la sera del 9 agosto 2026, rilievo **R1.2**.* Qui c'era scritto, con un ⛔, che *«la
> pagina e la sessione WebTransport devono presentare **lo stesso** certificato»*, mentre §4.1-bis
> ne impone **due** con un altro ⛔. Due righe normative che si contraddicono, e nessuna citava
> l'altra: chi obbediva a questa serviva alla pagina un certificato che l'altra obbliga a
> rigenerare ogni quattordici giorni, **facendo ricomparire l'avviso ogni due settimane** — cioè
> il sintomo che §4.1-bis dichiara come conseguenza dell'errore opposto.
>
> ⭐ **Il fatto che scioglie il nodo** era già in casa, in `web/rapporti/S1-certificato.md`: con
> `serverCertificateHashes` il browser **non guarda l'eccezione**, guarda l'impronta. Quindi i due
> certificati non devono essere «lo stesso» — devono essere **dichiarati in due modi diversi**, e
> l'utente vede un avviso solo, quello della pagina.

`[?]` **Quel che resta da misurare è solo Safari**: se lì l'eccezione basti da sola, cioè se si
possa fare a meno di pubblicare l'impronta. ⚠ *La domanda generale che stava qui — «l'eccezione
copre WebTransport?» — **ha già risposta per due motori su tre**, ed è no: la dà il riquadro in cima
a questa sezione. Tenerla aperta faceva pianificare una misura già fatta (rilievo **R1.25**).*

### 4.1-bis ⛔ `serverCertificateHashes` — **la strada normale**, non una rete di sicurezza

*Promossa da rete di sicurezza a strada principale la sera del 9 agosto 2026, dopo la misura S1:
non era un'alternativa, è **l'unico meccanismo** che i browser espongono per un server senza
dominio.*

> ⛔ *Corretta la notte del 9 agosto 2026, rilievo **R4.4** della revisione del banco della fase 1.*
> La riga «chi resta fuori» diceva *«`[S]` WebKit non lo implementa: su Safari, iPhone e iPad la
> strada è l'eccezione»*. **È falsa da ottobre 2025**, e `web.md` §3.1 e `DECISIONI.md` §1.7 erano
> già stati corretti **lo stesso 9 agosto**: questo documento no.
>
> ⛔ **E il danno era di quelli che non fanno rumore, perché questo file è l'arbitro.** Chi lo
> leggeva alla lettera scriveva il ramo *«su Safari l'impronta non serve, si va di eccezione o di
> certificato vero»* — e lo scriveva **conforme alla specifica**, mentre chi leggeva `web.md`
> pubblicava l'impronta per tutti e tre. Due implementazioni divergenti, entrambe con ragione.
> ⚠ E un banco che avesse applicato il criterio *«una libreria che va con Chrome e non con Safari
> non è una libreria che va»* avrebbe **bocciato entrambe le candidate**.

| | |
|---|---|
| **che cos'è** | l'impronta SHA-256 del certificato della sessione viaggia **dentro la pagina**, e il browser accetta senza avvisi. È il nostro modello di fiducia, fatto con la leva che i browser offrono apposta. ⛔ **Dei byte DER del certificato** — non della chiave pubblica e non dei byte PEM. ⚠ *Il DER mancava qui e c'era in `DECISIONI.md` §1.5 riga 7 dal 9 agosto (rilievo R1.14): allineato la notte del 10 agosto 2026, ed è lo stesso danno di allora — chi calcola l'impronta sull'involucro sbagliato ottiene un confronto che **non combacia mai**, col sintomo «WebTransport non si connette» e nessun errore che nomini l'impronta* |
| ⭐ **e non è più `[S]`** | `[M]` **9 agosto 2026**, su **due motori indipendenti**: una sessione WebTransport verso un certificato **autofirmato ECDSA P-256 di 13 giorni**, con l'impronta pubblicata nella pagina e **nessun avviso**, si è aperta su **Chrome 151** (30,2 ms) e su **Firefox 140** (52,0 ms), e i byte sono tornati identici da tutt'e due. Banco `banchi/01-b2-*`, documento `fasi/01-filo-nudo.md` |
| ⚠ **e quel che i due motori NON provano** | sono due squadre che non ci conoscono, quindi il loro accordo vale — ⛔ **ma chi serviva era `aioquic`, non una nostra implementazione**: questo misura **il modello di fiducia**, non il server. E **Safari resta fuori per decisione** (`DECISIONI.md` §1.8) |
| **il vincolo** | `[S]` certificato valido **meno di 14 giorni**, chiave **ECDSA P-256**, niente RSA, impronta **SHA-256**, e `allowPooling` a `false` |
| ⭐ **perché la rotazione non si vede** | è **il server stesso a servire la pagina**: rigenera il certificato prima che scada e ci scrive dentro l'impronta corrente. L'utente non tocca niente e non sa che esista |
| ⛔ **che cosa non copre** | **il caricamento della pagina**, che è una connessione TCP a sé. Lì resta l'avviso con il clic — o il certificato vero, per chi ha un dominio |
| ⭐ **e la stessa strada è DISPONIBILE su tutti e tre i motori** | `[R]` **WebKit lo ha implementato il 2 ottobre 2025** (bug 300057, `NetworkTransportSessionCocoa.mm`) ed è spedito in **Safari 26.4**: iPhone e iPad hanno **la stessa** strada degli altri due, non una da salvare. ⛔ **Disponibile, non verificata**: su Safari nessuno l'ha provata (riga sopra, `DECISIONI.md` §1.8), e *«vale su»* sarebbe un'affermazione di funzionamento sostenuta da `[R]`, cioè dalla lettura di un commit — forma **E1**. ⚠ *Corretto il 10 agosto 2026, rilievo **R11.16**: questa riga e quella sopra dicevano, nella stessa tabella, che vale su tre motori e che Safari resta fuori. Questo file è l'**arbitro**, cioè il posto in cui una deduzione pesa più che nella documentazione del prodotto* |

⛔ **Da cui due certificati, e vanno tenuti distinti nel codice**: uno **longevo** per la pagina, che
è quello su cui l'utente concede l'eccezione e che quindi **non deve cambiare** più spesso del
necessario; uno **a scadenza breve** per la sessione, che ruota da sé. ⚠ Confonderli fa ricomparire
l'avviso ogni due settimane, e nessuno collegherebbe le due cose.

⛔ **E l'impronta che la pagina ha in mano invecchia.** Una scheda lasciata aperta due settimane
tiene l'impronta di un certificato che nel frattempo è stato ruotato: alla riconnessione il browser
rifiuta, e il sintomo è *«non si collega più e non dice perché»*. Le due cure, e **la seconda è
quella scelta**:

| | |
|---|---|
| ricaricare la pagina | funziona e butta via lo stato: l'utente perde quel che stava guardando |
| ⭐ **chiedere l'impronta corrente** | ⛔ **e non passa da RCP**: la sessione non è ancora aperta, quindi non c'è un canale su cui chiedere. La pagina la ritira **dal server che l'ha servita**, con una richiesta ordinaria, e riprova |

⚠ *Riportata la sera del 9 agosto 2026 dal rapporto S1 (rilievo **O6**), che la dichiarava come
«va deciso dove sta questo aggiornamento in RCP». La risposta è: **fuori** da RCP.*

⚠ **E la conseguenza sul collaudo, che vale in ogni caso**: un banco che prova la fiducia **DEVE**
provare anche il **secondo** collegamento, e un terzo con la chiave cambiata. La prova a
collegamento singolo resta verde per sempre (`LEZIONI.md` §2.1).

### 4.2 Il canale di controllo

Il client apre il **primo stream bidirezionale della sessione WebTransport**. Quello è il canale di
controllo, resta aperto per tutta la sessione, e il suo chiudersi **è** la fine della sessione.

> ⛔ *Corretto la sera del 9 agosto 2026, rilievo **R1.5**: qui c'era «(identificatore 0)», ed è un
> resto della stesura a QUIC nudo.* In una connessione HTTP/3 lo stream QUIC numero 0 è già
> occupato — è quello della richiesta che **stabilisce la sessione WebTransport stessa** — e l'API
> non espone nessun numero: apre uno stream e restituisce un oggetto. Chi leggeva «0» alla lettera
> cercava il canale di controllo dove non arriverà mai, con la diagnosi «il client non apre il
> canale» **mentre il client lo ha aperto**.

⛔ **In byte**: un FIN su quello stream, da una qualunque delle due parti, chiude la sessione.
Chi lo riceve **DEVE** considerarla finita; **NON DEVE** continuare a spedire **su nessun canale,
compreso quello di controllo**.

> ### ✅ Deciso l'11 agosto 2026 dall'utente: **il silenzio** — `DECISIONI.md` §7.14
>
> *Fino a oggi questa riga vietava di spedire «sugli altri canali» e taceva sul controllo. Su uno
> stream bidirezionale il `FIN` di una parte non chiude il verso dell'altra, quindi chi lo riceveva
> **poteva** mandare il `CONGEDO` che §8.1 impone a chi chiude: **byte diversi per lo stesso
> ingresso** — nove contro zero — e due implementazioni divergenti senza che nessuna avesse torto
> (rilievo **R11.22**).*
>
> ⛔ **Chi riceve il `FIN` non spedisce più niente, nemmeno sul canale di controllo.** Il motivo
> viaggia per la **seconda strada** di §3.1 punto 3 — il codice d'errore applicativo della chiusura
> della sessione — che non ha bisogno di un canale vivo.
>
> ⭐ **E a decidere è stata una misura, non una lettura.** `[M]` 10 agosto 2026, difetto 2 di B11:
> **Chrome butta un messaggio spedito subito prima di chiudere la sessione.** Il `CONGEDO`
> dell'altra lettura sarebbe un **DEVE che un motore su due non può onorare** — la forma che il
> rilievo R1.4 ha già dichiarato difetto. La seconda strada di §3.1, invece, ha funzionato su
> tutt'e due i motori.
>
> ⚠ **Il prezzo è pagato in §8.1**, non qui: quella sezione impone il congedo a «chi chiude», e da
> oggi porta scritto che **chi ha ricevuto un `FIN` non è «chi chiude»**. Senza quella frase questa
> decisione lascerebbe in piedi la contraddizione invece di chiuderla.
>
> ⛔ **E una premessa che era falsa va detta, perché è quella con cui la decisione è stata presa**:
> *«il server non attacca mai di sua iniziativa»*. Attacca, ed è il comportamento più misurato
> della fase 1 — i tre tetti di §4.6 visti scattare da **B6** (5,0 · 60,1 · 10,0 s), le **36
> violazioni su 36** di **B5** dopo ciascuna delle quali il server chiude, `RESPINTO`,
> `TROPPI_TENTATIVI` e `GIA_ATTIVA_REMOTA`. ⭐ La decisione **non cambia**: proprio perché il
> server chiude spesso, quel che fa chi riceve conta — ed è la misura su Chrome a scegliere, non
> la rarità del caso.

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
| `video.livello` | client | il livello massimo che sa decodificare, es. `5.1`. ⛔ Il server **DEVE** emettere un flusso di livello non superiore, e **non lo indovina**: un livello dichiarato troppo basso non dà un errore di rete, **fa rifiutare la configurazione dal decodificatore** e il sintomo è «il browser non apre il flusso» *(rilievo **O12**)* |
| `video.misura_massima` | client | `LARGHEZZAxALTEZZA` che sa decodificare, es. `3840x2160` |
| `audio.codec` | entrambi | elenco fra `opus`, `pcm` |
| `input.tocco` | client | `si`, `no` — riservato, in RCP/1 vale sempre `no` |
| `appunti.testo` | entrambi | `si`, `no` |
| `client.nome` | client | testo libero per il registro, es. `remotix-linux 0.1.0` |
| `banco.marca` | server | `si`, `no` — ⭐ *nuova, 9 ago notte*: la **funzione di banco** di §7.5 è accesa. ⛔ Vale `no` in ogni installazione normale, e un server che la dichiarasse `si` per errore lo **scrive nel registro a ogni avvio** |

⛔ **La forma dei nomi e dei valori è vincolata**, o «ignorare quel che non si conosce» diventa
«indovinare»:

- un **nome** è fatto di `a-z`, `0-9`, `.` e `_`, da 1 a 64 byte;

> ### ⛔⭐ Il trattino basso è del 10 agosto 2026, e l'ha trovato **il validatore**
>
> Questa riga diceva *«`a-z`, `0-9` e `.`»* — e tre righe sotto la tabella definisce
> **`video.misura_massima`**, che quel carattere lo contiene. ⛔ **La specifica si contraddiceva
> da sola**: un'implementazione che avesse applicato la regola alla lettera avrebbe chiuso con
> `ERRORE_PROTOCOLLO` una capacità **definita da questo stesso documento**, e il sintomo — *«il
> client cade appena manda `CIAO`»* — non avrebbe nominato né la regola né il nome.
>
> ⭐ **L'ha trovata `banchi/01-b4-validatore.py` alla sua prima esecuzione**, cioè un programma
> scritto leggendo solo questo file, prima che esistesse un byte di server. È precisamente il
> mestiere che §11 gli assegna: *«client e server non si collaudano l'uno contro l'altro»*.
>
> ⚠ **Delle due cure si è scelta questa**, ed è 🔸 derivata: ammettere `_` invece di rinominare la
> capacità. Rinominare toccherebbe un nome già citato in `web.md` e in `SPECIFICHE.md`, e il
> trattino basso è la convenzione che il resto del documento usa nei nomi di campo
> (`tela_larghezza`, `max_idle_timeout`).
- un **valore** è testo UTF-8 stampabile, al massimo 256 byte;
- un **elenco** dentro un valore si scrive separato da virgole, senza spazi: `hevc,av1`;
- ⛔ **un nome ripetuto due volte è `ERRORE_PROTOCOLLO`.** «Vince l'ultimo» e «vince il primo» sono
  due implementazioni diverse dello stesso documento, che è precisamente ciò che questo documento
  esiste per impedire;
- ⛔ un valore **vuoto** è `ERRORE_PROTOCOLLO`: chi non ha niente da dire non manda la capacità;
- ⛔ **una voce sconosciuta DENTRO un elenco si scarta**, come si scarta un nome sconosciuto: un
  `video.codec` che vale `hevc,vp9` si legge come `hevc`. È la stessa eccezione di §3, ed è il
  meccanismo con cui un client di domani parlerà a un server di oggi. ⚠ Ma se **dopo lo scarto
  l'elenco resta vuoto**, si congeda con `NIENTE_IN_COMUNE`;
- ⛔ **una capacità mandata dal lato sbagliato** — `video.misura_massima` che arriva dal server — è
  `ERRORE_PROTOCOLLO`: il nome è conosciuto, quindi l'eccezione dei nomi non la copre;
- ⛔ e chi **non dichiara** `pcm` o `8`, che §4.3 impone a entrambi, si congeda con
  `NIENTE_IN_COMUNE`, non con `ERRORE_PROTOCOLLO`: non ha sbagliato a scrivere, non ha di che
  parlare.

> ⚠ *Le ultime tre righe sono della sera del 9 agosto 2026, rilievo **R1.12**.* La regola diceva
> «un **nome** sconosciuto si ignora» e taceva su tutto il resto: un valore sconosciuto dentro un
> nome conosciuto aveva **due letture entrambe difendibili** — si scarta, oppure è un campo fuori
> intervallo e la connessione cade — e le due producono **byte diversi sul filo per lo stesso
> ingresso**. Il giorno in cui esisterà un RCP/2 che parla un codec nuovo, il server vecchio o
> continua o cade, e il documento non diceva quale.

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
 ├── stringa utente         da 1 a 256 byte    ⛔ vuota = ERRORE_PROTOCOLLO
 └── stringa parola         da 1 a 1024 byte   ⛔ vuota = ERRORE_PROTOCOLLO

AMMESSO      corpo vuoto
RESPINTO
 └── u8      motivo         (dallo spazio dei motivi di §8.2)
```

| Esito | Messaggio |
|---|---|
| ammesso | `AMMESSO` |
| respinto | `RESPINTO` con motivo |

⛔ Il server **NON DEVE** distinguere nel motivo fra «utente inesistente» e «parola d'ordine
sbagliata»: entrambi sono `CREDENZIALI_ERRATE`. E **DEVE** applicare **il ban dell'indirizzo**
prima di rispondere (§4.4-bis). ⚠ *Questa riga diceva «la **limitazione della frequenza** dei
tentativi», che era la forma sostituita il 10 agosto 2026 da `DECISIONI.md` §1.9: dal ban non si
esce aspettando qualche secondo, e chiamarlo frequenza faceva scrivere un'attesa dove va scritto un
rifiuto. Allineata la notte del 10 agosto, come §8.2 riga `0x08` lo era già.*

⛔ **`RESPINTO` è il congedo dell'autenticazione.** Dopo averlo mandato il server **DEVE** chiudere
la **sessione WebTransport** come dice §3.1 — con lo stesso motivo nel **codice d'errore
applicativo della chiusura**, non in un `CONNECTION_CLOSE` di trasporto — e **NON DEVE** mandare
anche `CONGEDO`. Il client **NON DEVE** riprovare sulla stessa connessione: per un secondo
tentativo se ne apre una nuova.

⛔ **E dopo `RESPINTO` al client resta una cosa sola che può dire: `CONGEDO`.** Il divieto di §4.4
è di **riprovare**, non di congedarsi. Se il server sbaglia *dopo* aver mandato `RESPINTO` — un
altro messaggio sullo stesso canale di controllo — il client applica §3 e chiude, e §8.1 gli
**IMPONE** di dire perché: quel `CONGEDO` è **conforme**, anche se per il server la sessione era già
finita. ⛔ Qualunque **altro** messaggio, e in particolare un secondo `CREDENZIALI`, è la violazione
che §4.4 vieta.

> ⛔ 🔸 *Chiarita il 10 agosto 2026 dal banco **B11**, e la forma è mia: si corregge senza
> discussione.* La regola era già decidibile leggendo §4.4 e §8.1 insieme — ma il **server** non la
> leggeva così: contava come «byte spediti dopo la fine» **tutto** quel che arrivava, e il caso
> `respinto-poi-congedo` ha messo un rosso addosso alla pagina **mentre faceva quel che §8.1 le
> impone**. ⚠ Il canale di controllo non aveva nessun `FIN`: §4.2 non era in gioco, e la sola regola
> che lo era parla di **tentativi**, non di commiati. ⭐ Adesso il server nomina le due cose
> separatamente, e B11 pretende il congedo **una volta per motore** invece di limitarsi a non
> trovare byte di troppo — *un'assenza non è una prova* (`LEZIONI.md` §1.9).

> ⚠ *Chiarita il 9 agosto 2026.* La prima stesura aveva `RESPINTO(motivo)` in §4.4 e
> `CREDENZIALI_ERRATE` fra i motivi di congedo di §8.2, senza dire se dopo il primo arrivasse anche
> il secondo. Due implementazioni potevano indovinare diverso — o, peggio, **indovinare uguale
> perché scritte dalla stessa mano**, che è il difetto muto contro cui questo documento esiste.

> ⚠ *Gli intervalli sono della sera del 9 agosto 2026, rilievo **R1.28**: §6.0 dichiara legale la
> stringa vuota, quindi `CREDENZIALI` con utente e parola di zero byte era **conforme**. Le due
> letture — «si passa a PAM e si consuma un tentativo» contro «è errore di protocollo e la
> connessione cade» — danno due profili di robustezza diversi, perché nella seconda un attaccante
> che manda credenziali vuote **non incrementa il conto** di §4.4-bis. ⚠ *Diceva «nessuno dei due
> contatori», ed erano i due della forma precedente: dal 10 agosto 2026 il conto è **uno solo**, sul
> solo indirizzo. Il ragionamento non cambia — cambia il numero.*

⚠ **Una nota che non è normativa e che vale il tempo di scriverla**: la parola d'ordine sta in
chiaro nella memoria di chi la riceve. Va azzerata appena PAM ha risposto, e **non** deve comparire
in nessun registro a nessun livello — nemmeno in `traccia`, che in v1 è un registratore di battitura
(`v1/remotix-c/src/registro.h`).

### 4.4-bis ✅ Il ban dell'indirizzo — tre tentativi, poi dodici ore

*Deciso dall'utente il 10 agosto 2026, in due passaggi. Prima: «se l'utente sbaglia la password per
3 volte consecutive, non vengono più accettate connessioni da quell'IP per 12 ore (ban)». Poi, più
stretta: «3 tentativi di connessione fallita (perché user sbagliato o perché password sbagliata)
causano il ban di quell'IP».*

> ⛔ **Sostituisce per intero la forma precedente**, che era 🔸 mia e non pronunciata da nessuno: 5
> tentativi in 5 minuti, poi una finestra da 30 secondi che raddoppiava fino a 15 minuti, con **due**
> contatori — uno per nome utente e uno per indirizzo — e l'azzeramento su un accesso riuscito.
> Il contatore **per nome utente non esiste più**: il conto guarda l'indirizzo e nient'altro.
>
> ⭐ **E il filo non cambia di un byte**: `TROPPI_TENTATIVI` (`0x08`) esiste già in §8.2, nessun tipo
> nuovo, nessuna deroga alla regola di §9.

| | |
|---|---|
| **il conto** | **tre** autenticazioni fallite dallo stesso **indirizzo di provenienza**, ⛔ **dentro una finestra di 5 minuti**. Fuori dai cinque minuti il ban non scatta: chi sbaglia a digitare ogni tanto non è chi prova parole d'ordine. ⛔ E il nome utente **non conta**: tre nomi diversi contano tre |
| **la conseguenza** | quell'indirizzo è **bannato per 12 ore** |
| **che cosa azzera il conto** | un'autenticazione **riuscita** da quell'indirizzo — e il passare del tempo: ⚠ la finestra è **scorrevole**, cioè si guarda l'ora degli **ultimi tre** fallimenti, non si riparte da capo al primo. Ancorandola al primo, tre fallimenti a 0:00 · 4:59 · 5:01 farebbero ripartire il conto da uno, e chi prova a un ritmo appena più lento della finestra non verrebbe **mai** fermato |
| ⛔ **la chiave del conto** | **il solo indirizzo, senza la porta.** ⚠ È il difetto che il banco **B5** ha trovato nella forma precedente: la chiave conteneva la porta, e siccome §4.4 ammette **un solo tentativo per connessione** la porta cambia a ogni tentativo — quel contatore valeva **sempre 1**. Codice presente, che si leggeva bene, e che non faceva niente |

⛔ **Che cosa conta come tentativo fallito, e che cosa no.** Conta **soltanto** l'autenticazione: un
`CREDENZIALI` a cui il server risponde `RESPINTO(CREDENZIALI_ERRATE)`. ⭐ E si noti che il conto
**non sa** se il nome non esistesse o se la parola fosse sbagliata — §4.4 vieta al server di
distinguerle — che è esattamente la cosa che questa regola ha deciso di contare come una sola.

**NON contano**, e l'elenco è normativo perché ciascuno di questi bannerebbe qualcuno che non ha
sbagliato niente:

| | |
|---|---|
| `ERRORE_PROTOCOLLO` · `VERSIONE_INCOMPATIBILE` · `NIENTE_IN_COMUNE` | sono guasti dei **byte**, e possono nascere da un difetto **nostro** o da una scheda rimasta aperta su una versione vecchia (§13 di `PIANO.md`). Un difetto del server che bannasse l'utente per dodici ore sarebbe la peggiore diagnosi che questo progetto possa produrre |
| `TEMPO_SCADUTO` · le connessioni che cadono a metà stretta di mano | misurano una rete lenta o una persona che digita piano (§4.6), non un tentativo |
| ⛔ **`GIA_ATTIVA_REMOTA`** (`0x0F`) | è quel che riceve il **secondo dispositivo dello stesso utente** (§8.2): contarlo vorrebbe dire che chi prova a riattaccarsi tre volte dal telefono **si banna da sé**, mentre la sua sessione è viva |

⛔ **Che cosa vede un indirizzo bannato** *(deciso dall'utente: «viene visualizzata una pagina di
login rifiutato»)*:

1. **la pagina si serve lo stesso**, e mostra il rifiuto — *«tentativi esauriti»*. ⛔ Non un errore di
   rete, non un silenzio: chi è stato bannato per errore è quasi sempre il proprietario, e deve
   poter capire che cosa gli è successo invece di trovarsi davanti un server che sembra morto per
   mezza giornata;
2. **la sessione WebTransport si rifiuta**, con `TROPPI_TENTATIVI` nel codice d'errore applicativo
   della chiusura (§3.1 punto 3). ⚠ Serve alla **scheda già aperta**, che non ricarica la pagina e
   altrimenti resterebbe ad aspettare;
3. 🔸 la pagina dice anche **quante ore mancano**. *Derivata, correggibile senza discussione*: è la
   differenza fra un'informazione e mezza giornata di mistero.

⛔ **Il ban sopravvive al riavvio del server** *(deciso dall'utente)*: indirizzo e ora di scadenza su
file. Un ban che si azzera riavviando è una protezione che **si perde da sé** — invariante **I7** — e
chi riavvia il server per un altro motivo non saprebbe di averla tolta.

⛔ **E si esce in due modi, non uno** *(deciso dall'utente: «comando di sblocco oppure il trascorrere
delle 12 ore»)*: la scadenza naturale, oppure un **comando di sblocco sul server**. Quest'ultimo è la
via d'uscita di chi si banna dal proprio telefono, e chiede l'unica chiave che quel caso ammette —
l'accesso alla macchina. ⛔ **Ogni sblocco si scrive nel registro**, o un ban tolto e un ban mai
scattato hanno lo stesso aspetto.

> ⚠ **Il comando di sblocco NON è di RCP, e va detto qui perché non lo si cerchi sul filo.** Non
> passa un byte della sessione: è un meccanismo del server, e questo documento ne detta soltanto
> *che esista*, *che risponda distinguendo «tolto» da «non era bannato»* e *che scriva nel registro*.
> ⛔ **La forma non è indifferente, ed è stata pagata**: `remotix --sblocca IND` come **secondo
> processo** non funziona — il ban vive nella memoria del processo che serve, un secondo processo può
> solo riscrivere il file, il server continuerebbe a rispondere `TROPPI_TENTATIVI` fino al riavvio, e
> **chi ha dato il comando lo vede uscire con zero**. Dalla notte del 10 agosto 2026 le due
> implementazioni parlano lo stesso protocollo di **una riga su un socket Unix `0600`** — `SBLOCCA
> <indirizzo>` → `TOLTO` / `NON-BANNATO`, e `PING` → `PONG` per dire *«il comando c'è»*. Il racconto
> per esteso sta in `fasi/01-filo-nudo.md` («Che cosa NON ha funzionato»), non qui.

⭐ **Il ritardo fisso resta, e non è ridondante rispetto al ban.** Il server **NON DEVE** rispondere a
`CREDENZIALI` prima che sia passato **un secondo** dalla ricezione, **anche quando la risposta è
`AMMESSO`**. Il ban toglie di mezzo chi indovina; il secondo fisso toglie il **tempismo** come
canale — senza, «utente inesistente» risponde in un millisecondo e «parola sbagliata» in cinquanta,
e la distinzione che §4.4 vieta di scrivere nel motivo la si legge col cronometro.

> ⚠ **E su questo c'è una misura che non torna, dichiarata invece che nascosta.** `[M]` 10 agosto
> 2026, banco **B8**: la mediana dei tentativi respinti è **2636 ms** su 42 campioni, dove questa
> riga vuole ~1000. ⛔ A governare i tempi non è il nostro ritardo: è **PAM**. Finché quel ritardo
> non è costante, il secondo fisso **non nasconde quel che dichiara di nascondere** — cioè se un
> nome utente esista. Resta `[?]`, e **il ban non la chiude**: sono due proprietà diverse.

⛔ **E il rifiuto di un indirizzo bannato parte anch'esso NON PRIMA DI UN SECONDO.** La *decisione* si
prende senza interrogare PAM — guarda solo l'indirizzo, e nessun segreto ci entra — ma **la risposta
aspetta come tutte le altre**: `RESPINTO(TROPPI_TENTATIVI)` sul canale di controllo, dopo il secondo
fisso.

> ⛔ *Corretto la notte del 10 agosto 2026, e l'ha trovato il banco **B8** mentre lo si riscriveva.*
> Questo paragrafo diceva *«il rifiuto di un indirizzo bannato **non passa** dal secondo fisso: si
> decide **prima** di `CREDENZIALI`»*. ⛔ **Sono due righe incompatibili nella stessa sezione**: un
> rifiuto deciso *prima* di `CREDENZIALI` non ha nessun `RESPINTO` da mandare, perché `RESPINTO` è la
> risposta a un messaggio che non è ancora arrivato — e §8.2 fa viaggiare `TROPPI_TENTATIVI` proprio
> dentro un `RESPINTO`.
>
> ⛔ **E riapriva una contraddizione che il rilievo R11.10 aveva chiuso quello stesso giorno**, per la
> ragione che vale ancora: *«un rifiuto immediato dentro la finestra e uno ritardato fuori rimettono
> il **tempismo** come canale, dal lato opposto a quello che il ritardo fisso toglie»*. Un indirizzo
> che riceve la risposta in un millisecondo sa di essere bannato prima ancora di leggere il motivo.
>
> ⚠ È la forma che questo progetto paga più spesso — **una cura applicata in un posto solo** — e
> stavolta l'ha commessa chi scriveva la regola nuova, poche ore dopo averne curata una uguale.

⛔ **La pagina del rifiuto si serve con stato HTTP `200`**, non con un 4xx. ⚠ *Scelto la notte del 10
agosto 2026, 🔸 derivato:* con uno stato d'errore un intermediario o il browser stesso possono
**sostituire il corpo** con la propria pagina d'errore, e la frase che il proprietario **deve**
leggere — *«tentativi esauriti, restano N ore»* — sparirebbe proprio nel caso per cui esiste.

⚠ **E la chiave del conto ha una forma canonica**, che va detta perché sta in un solo posto del
codice e nessun documento la dichiarava: l'indirizzo viaggia fra **parentesi quadre anche quando è
IPv4** — `[192.168.0.2]` — perché è così che lo scrive chi ospita. ⛔ Chi digita `192.168.0.2` al
comando di sblocco **deve arrivare alla stessa chiave**: la normalizzazione è del server, non di chi
comanda. Senza, il comando risponde *«non era bannato»* a ogni indirizzo, **per sempre e senza
sintomo**.

⚠ **Il prezzo, dichiarato — e non lo paga chi indovina:**

| | |
|---|---|
| **dietro un NAT gli indirizzi si condividono** | tre errori di **una** persona chiudono la porta a tutti gli altri per dodici ore. Il contatore per nome utente della forma precedente esisteva proprio per questo, ed **è stato tolto sapendolo**: la scelta è dare all'indirizzo tre tentativi soli invece di distinguere chi sbaglia |
| **il primo a inciamparci è il proprietario** | parola lunga, tastiera di un telefono, maiuscole automatiche. È da qui che vengono l'obbligo della pagina che **dice** che cos'è successo e il comando di sblocco: senza quei due, la regola sarebbe indistinguibile da un guasto |
| ⛔ **e la parola d'ordine resta l'unica chiave** | tre tentativi **per indirizzo** alzano molto il costo di chi indovina, e non chiudono la partita: una rete di diecimila indirizzi ottiene comunque trentamila tentativi su un conto solo. Quella la chiude l'autenticazione forte rinviata a fine progetto (`DECISIONI.md` §1.7) |

⭐ **E una cosa che questa regola non può fare**, scritta perché nessuno gliela attribuisca: nessuno
può far bannare l'indirizzo **di qualcun altro**. Per arrivare a `CREDENZIALI` bisogna aver
completato la stretta di mano QUIC, che pretende che i pacchetti tornino davvero a quell'indirizzo:
il mittente non si falsifica. Il ban colpisce solo chi ha bussato per davvero.

⚠ **E una conseguenza sul collaudo, che morde subito**: i banchi partono **tutti dallo stesso
indirizzo**, e quello che prova questa regola fallisce di proposito. Con dodici ore, «si aspetta la
scadenza» non è una cura — il banco si serve del comando di sblocco, e il banco del limitatore **non
lo chiama dentro il proprio giro**, o non prova più niente. Il dettaglio sta in
`fasi/01-filo-nudo.md`, regola **B0.3** e banco **B8**.

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
| ⭐ **apertura del canale di controllo** *(il primo stream bidirezionale della sessione)* | `CIAO` ricevuto | **5 s** |
| `ECCOMI` spedito | `CREDENZIALI` ricevute | **60 s** — è il tempo in cui una persona digita la parola d'ordine |
| `AMMESSO` spedito | `ATTACCA` ricevuto | **10 s** |
| ⭐ **apertura della sessione WebTransport** | **apertura del canale di controllo** | **5 s** — ✅ deciso l'11 agosto 2026, `DECISIONI.md` §7.17 |

> ### ⭐ La riga che mancava, e l'ha trovata una misura — ✅ 11 agosto 2026
>
> *La tabella cominciava da `CIAO`, e prima del `CIAO` c'era uno stato in cui il server non contava
> niente: chi apriva la sessione e non apriva mai il canale **non aveva addosso nessun tetto**.
> Trovato dal banco **B6** (rilievo **R12-A.25**), deciso dall'utente lo stesso giorno.*
>
> ⛔ **Scaduti i 5 s, il server chiude con `TEMPO_SCADUTO`** `0x0D`. ⚠ Il canale di controllo non
> esiste, quindi il `CONGEDO` **non si manda** (§8.1, la condizione decisa in `DECISIONI.md` §7.15):
> il motivo viaggia **solo** nel codice d'errore applicativo della chiusura della sessione (§3.1
> punto 3). ⭐ Ed è il primo posto in cui le decisioni dell'11 agosto si incastrano: senza §7.15
> questa riga imporrebbe un byte su un canale che non è mai nato.
>
> ⭐ **Perché 5 s, cioè lo stesso numero della riga sotto**: aprire il canale di controllo è il
> **primo atto obbligatorio** della sessione (§2.5), non dipende da quanto è veloce a digitare una
> persona e non dipende dalla rete più di quanto ne dipenda il `CIAO`.
>
> ⛔ **E che cosa chiude davvero**: era l'ultimo modo, in questa fase, di **occupare un posto senza
> dire chi si è**. Il tempo di inattività di QUIC non lo copriva: quello conta il **silenzio**, e
> una sessione che scrive su un altro stream non è silenziosa — teneva il posto a tempo
> indeterminato.
>
> ⚠ **Non serve nessun tipo di messaggio nuovo**, e conta: la finestra di §9 è chiusa dal 10 agosto
> 2026. `TEMPO_SCADUTO` c'era già.

> ### ⭐ La prima riga è cambiata di una parola, e la seconda risposta dice che non basta
>
> ⚠ *La prima riga diceva* **«stretta di mano TLS finita»** *dal 9 agosto 2026. Era la `[?]` **R3.27**
> — «"stretta di mano TLS finita" non è un istante che i due lati condividono»: in WebTransport la
> connessione HTTP/3 e la sessione sono due cose separate, e fra i due istanti passa almeno un giro
> di rete. Corretta l'11 agosto 2026 su una misura del banco **B6**, rilievi **R12C.11** e
> **R12-A.25**.*
>
> **La prima risposta di B6, e cambia una parola.** Il cronometro del primo tetto parte
> dall'**apertura del canale di controllo**: è l'istante che il server osserva davvero, ed è quel che
> `src/rcp.c` fa (la sessione RCP nasce quando il canale si apre, e il tetto si conta da lì). ⛔ La
> fine del TLS **non** è utilizzabile: una seconda sessione su una connessione riusata partirebbe
> **col budget già consumato**, cioè si vedrebbe congedare per un tempo che non ha avuto.
>
> ⛔ **E la seconda risposta di B6 è più grave, perché dice che curare la parola NON CHIUDE il
> buco.** Se il cronometro parte dall'apertura del canale, chi apre la **sessione** WebTransport e
> **non apre mai il canale** non ha addosso **nessun tetto**: resta lì, viva e senza scadenza — cioè
> esattamente la connessione che *«tiene un posto e non lo dichiara a nessuno»*, che è la prima riga
> di questa sezione. La tabella comincia da `CIAO`, e **prima del `CIAO` c'è uno stato in cui il
> server non conta niente**.
>
> ⚠ **Che cosa lo copre oggi, e perché non basta**: solo il tempo di inattività di QUIC, che è **30
> secondi di silenzio** — ma chi tiene aperta la sessione mandando qualunque cosa su un altro stream
> non è silenzioso, e non scade mai. ⛔ **Quale sia il tetto giusto, e da che istante, è una domanda
> aperta e non una svista**: sta in `DECISIONI.md` §7.17, con le due letture e il caso concreto. Qui
> si dichiara il buco invece di riempirlo con un numero che nessuno ha scelto.

⛔ Scaduto un tetto, il server **DEVE** congedare con `TEMPO_SCADUTO`. **NON DEVE** aspettare i 30
secondi del tempo di inattività di QUIC: quello misura il **silenzio della rete**, questo misura un
**client che non fa il suo mestiere**, e confonderli fa sembrare un difetto nostro una rete lenta.

> ⛔ **E i 60 secondi della parola d'ordine erano irraggiungibili** — rilievo **R1.8**. Mentre
> l'utente digita, sul filo non passa **niente**: §2.2 vieta un battito applicativo e non c'è
> nessun altro canale attivo prima dell'attacco. Al trentesimo secondo scatta il tempo di
> inattività di QUIC e **la connessione muore in silenzio**, senza motivo, prima che il tetto dei
> 60 possa mai scadere. Il banco di §11 avrebbe misurato 30 dove il documento dice 60, e il
> programmatore avrebbe dato la colpa al banco.
>
> ⛔ **La cura, ed è del server**: finché aspetta le credenziali, il server **DEVE** tenere viva la
> connessione con i **PING del trasporto**, che non sono un battito applicativo — non portano
> informazione, non hanno una risposta da interpretare, e non creano una seconda verità sul silenzio
> (§2.2). ⚠ Senza questa riga un'implementazione li manda e l'altra no, e la seconda **perde gli
> utenti che digitano piano**: difetto intermittente, il peggiore da diagnosticare.

---

## 5. Il quadro dei canali

| Canale | Trasporto | Verso | Affidabile? |
|---|---|---|---|
| **controllo** | il **primo** stream bidirezionale della sessione (§4.2) | ↔ | sì |
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

> ### ⛔ L'abbandono ha **DUE forme osservabili**, non una — *13 agosto 2026, `[M]`*
>
> *Questo paragrafo, e §6.2 con lui, descrivevano una forma sola: lo stream **azzerato**. Alla fase
> 3 se n'è vista una seconda, e un client scritto sulla prima **non la riconosce**.*
>
> | forma | che cosa vede il client | quando succede |
> |---|---|---|
> | **A — lo stream azzerato** | uno stream aperto che finisce con `RESET_STREAM` invece che con FIN | il server aveva già **fatto uscire almeno un byte** di quel fotogramma |
> | ⛔ **B — il buco nei `numero`** | **nessuno stream**, e il `numero` successivo salta di uno | il server aveva **consumato il `numero`** e poi ha abbandonato **prima che un byte uscisse** |
>
> ⛔ **Quale delle due il client veda dipende da un dettaglio che nessuno dei due lati controlla:
> se un byte era già uscito.** Non è una scelta del server e non è un'informazione che il protocollo
> porti — è il momento in cui l'abbandono cade rispetto alla scrittura.
>
> ⇒ **Le conseguenze, e sono normative:**
>
> - il client **DEVE** trattare **tutt'e due** le forme come un buco, e in tutt'e due mandare
>   `RICHIEDI_CHIAVE` (§5.2). ⛔ Un client che guardi i soli `RESET_STREAM` **perde la forma B in
>   silenzio**, e il sintomo è quello che §5.2 esiste per evitare: immagini via via più sfasciate
>   senza nessun errore sollevato da nessuno;
> - il server **DEVE** scrivere nel registro **tutt'e due**, e distinguerle: sono la stessa
>   decisione, ma dal lato che riceve hanno **aspetti diversi**, e un registro che ne nomina una
>   sola non spiega quel che il client ha visto;
> - ⚠ e un banco che innesta l'abbandono **deve saper produrre tutt'e due**, o certifica metà della
>   regola credendo di certificarla tutta.
>
> ### ⛔⛔ E c'è un terzo caso, che **non è osservabile affatto** — ed è il più pericoloso
>
> Un fotogramma **buttato per mancanza di credito** (§2.3) non è nessuna delle due forme: non si apre
> nessuno stream **e il `numero` non viene consumato**, perché §6.2 lo fa crescere solo per i
> fotogrammi che il server **decide di spedire**. ⇒ ⛔ **Nessuno stream, nessun buco, nessun segnale:
> dal lato che riceve non è successo niente.**
>
> ⛔ **Quindi il client non può accorgersene, e non può chiedere la chiave.** Se il server non la
> produce **da sé**, l'immagine si sfascia **per sempre e in silenzio** — con un GOP lungo non ne
> arriva più una da sola. È il difetto **B-18**, trovato il 13 agosto 2026.
> ⇒ ⭐ **È la ragione per cui l'obbligo di §5.2 — «quando il server abbandona un delta DEVE mandare
> una chiave appena può, senza aspettare che il client la chieda» — non è una prudenza: in questo
> caso è l'unica cosa che esiste.** Il client non ha una domanda da fare.

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

- ⛔ **il primo fotogramma che il server spedisce dopo `SESSIONE` DEVE essere una chiave**
  (`0x0301`). ⚠ Senza questa riga un delta in apertura è conforme, e il client non ha modo di
  accorgersene: non c'è nessun buco nella successione dei `numero`, e il decodificatore non solleva
  errori. Il sintomo sarebbe *«il desktop compare a pezzi»*, e non nominerebbe né il protocollo né
  la chiave;
- ⛔ **e lo stesso vale a ogni cambio di tela**: il primo fotogramma spedito alla **misura nuova**,
  dopo un `TELA(ADATTATA…)` (§7.1), **DEVE** essere una chiave (`0x0301`) — e **DEVE** essere una
  chiave *vera*, cioè portare con sé tutto quel che serve a decodificarla da sola: per HEVC i suoi
  VPS/SPS/PPS davanti all'IDR. ⚠ Senza questa riga un delta alla misura nuova è **conforme**, e il
  client non ha modo di accorgersene: non c'è nessun buco nei `numero`, e — `[M]` 12 agosto 2026,
  Chrome 151 su Linux con VA-API, banco `banchi/02-pagina-tela-*` — **il decodificatore HEVC non
  solleva nessun errore**: continua a emettere fotogrammi alla misura **vecchia** e dipinge
  un'immagine sfasciata, diversa a ogni giro. Il sintomo sarebbe *«il desktop si strappa quando
  ridimensiono la finestra»*, e non nominerebbe né il protocollo né la tela. ⛔ E la stessa prova su
  **AV1** dà `EncodingError` su Chrome e su Firefox `[M]`: ⇒ **la regola serve perché sul codec
  principale il sintomo è muto**, e una regola non si scrive sul codec che si comporta bene;
- ⛔ **e il client riconfigura il decodificatore sulla prima CHIAVE alla misura nuova, non sul
  `TELA`.** ⚠ *Senza questa riga le due cure del 12 agosto si contraddicono sullo stesso fotogramma:
  §6.2 dice che un fotogramma in volo alla misura precedente **DEVE** essere accettato e dipinto,
  questa riga qui sotto dice che uno alla misura sbagliata **si butta** — e chi avesse riconfigurato
  sul `TELA` (la lettura naturale di §7.1, «la tela in vigore **dopo** questo messaggio») si
  troverebbe le due regole a comandare il contrario. Il documento non diceva **in nessun punto**
  quando si riconfigura, e le due letture erano tutt'e due conformi e divergevano sul filo. Rilievo
  **P10**, trovato applicando la cura di poche ore prima.* ⭐ E costa zero: `[M]` la chiave vera va
  bene **sia** riconfigurando **sia** senza;
- ⛔ il client, dal canto suo, **NON DEVE** consegnare al decodificatore un fotogramma la cui misura
  non è quella per cui il decodificatore è configurato **né quella tollerata da §6.2**: lo butta e lo
  tratta come un buco. ⚠ E non è una prudenza in più: `[M]` un `VideoDecoder` riconfigurato alla misura nuova pretende una chiave
  (`DataError: a key frame is required after configure()`), quindi senza la riga qui sopra quella
  chiave non arriverebbe mai e il cambio di tela costerebbe un `RICHIEDI_CHIAVE` e un fermo-immagine
  **ogni volta**. ⭐ Con la riga qui sopra, `[M]` la stessa chiave va bene **sia** riconfigurando
  **sia** senza: 8 celle su 8 su HEVC e su AV1, su Chrome e su Firefox, in tutt'e due i versi;
- ⛔ il server **NON DEVE** abbandonare un fotogramma **chiave**. Abbandonare la cura non è una cura;
- ⛔ quando il server abbandona un delta, **DEVE** mandare un fotogramma chiave **appena può** —
  senza aspettare che il client lo chieda, perché il client se ne accorge un giro di rete più tardi.
  ⭐ **E questo obbligo non è una prudenza: è l'unica cura che abbiamo** `[S]` — a un delta mancante
  il decodificatore **non solleva nessun errore**, si limita a produrre immagini via via più
  sfasciate fino alla chiave successiva. `[?]` L'alternativa vera sarebbero i **sotto-livelli
  temporali**, che permettono di buttare certi fotogrammi senza rompere niente: se `EncSliceLP`
  dell'Intel li sappia produrre **non lo sa nessuno**, ed è una misura della fase 8. Finché non lo
  si sa, **ogni abbandono costa una chiave**;
- ⛔ il client **DEVE** mandare `RICHIEDI_CHIAVE` quando si accorge di un **buco** nella successione
  dei `numero`, o quando il decodificatore rifiuta un fotogramma;
- ⛔ finché non arriva una chiave, il client **NON DEVE** mostrare fotogrammi che sa incompleti:
  tiene l'ultimo buono. Un'immagine sfasciata è peggio di un'immagine ferma per un decimo di secondo;
- ⚠ il server **PUÒ** ignorare una `RICHIEDI_CHIAVE` che arrivi entro **200 ms dall'ultima chiave
  che ha spedito** — ⛔ non dall'ultima richiesta ricevuta, e la differenza non è una sfumatura:
  contando dalle richieste, due client insistenti spostano l'orologio all'infinito e la chiave non
  parte mai. Durante una raffica di perdite le richieste arrivano a decine, e ogni chiave costa
  dieci volte un delta: assecondarle peggiorerebbe esattamente la condizione che le ha provocate.
  ⭐ **È l'eccezione 5 di §3, ed è dichiarata lì.**

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
| **PCM** | campioni **s16, little-endian**, ⛔ **5 ms per datagram** — 480 campioni, **960 byte**, che con i 12 dell'intestazione fanno **972** |

> ### ⛔ Corretto la sera del 9 agosto 2026 — rilievo **R1.1**, il più grave della revisione
>
> Questa riga diceva **20 ms anche per il PCM**: 1920 campioni, **3840 byte**, più 12 di
> intestazione = **3852**. ⛔ Un datagram QUIC **non è frammentabile** — deve stare in un pacchetto
> solo — e su un percorso vero il carico utile disponibile è **~1200 byte** `[S]`.
>
> **Quindi l'audio PCM non sarebbe partito mai, su nessuna rete.** E il danno era doppio, perché
> §4.3 fa del PCM **il controllo positivo di Opus**: il giorno in cui Opus non si negozia, si
> ripiega su una strada che non esiste — e il banco cercherebbe il difetto in Opus.
>
> ⚠ **La forma dell'errore è quella di `LEZIONI.md` §2.2**, dove il banco contava i blocchi mentre
> l'audio era rumore a fondo scala. Qui non sarebbe arrivato nemmeno il rumore.
>
> `[?]` **Quanto porti davvero un datagram su ciascun motore va misurato**, non dedotto: è una riga
> della sonda del browser, e la pagina lo sa chiedere in una chiamata. Se il numero fosse più basso
> di 972, il PCM scende ancora — è per questo che i 5 ms sono scritti qui e non dedotti altrove.

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
| cursore nascosto | ⛔ `larghezza = 0` **e** `altezza = 0`, tutt'e due, e nessun byte d'immagine. Una sola delle due a zero è `ERRORE_PROTOCOLLO` |
| il punto attivo | ⛔ **DEVE** stare dentro l'immagine: `0 ≤ attivo_x < larghezza`, `0 ≤ attivo_y < altezza`. ⛔ **Unica eccezione, il cursore nascosto**: con `larghezza = altezza = 0` l'intervallo è vuoto, e allora `attivo_x` e `attivo_y` **DEVONO** valere `0`; qualunque altro valore è `ERRORE_PROTOCOLLO`. ⚠ *Il tipo resta `i16` e la riga «può essere negativo» è caduta: senza un intervallo, `attivo_x = -32768` era legale secondo ogni riga del documento, e due client avrebbero disegnato il puntatore in due posti diversi (rilievo **R1.21**)* |

> ⛔ *L'eccezione è del 10 agosto 2026, rilievo **R11.11**, ed è 🔸 derivata: si corregge senza
> discussione.* La riga sopra dichiara **obbligatorio** `larghezza = 0` **e** `altezza = 0` per il
> cursore nascosto; la riga sotto pretende `0 ≤ attivo_x < larghezza`, e con `larghezza = 0`
> quell'intervallo è **vuoto**: nessun valore di un `i16` lo soddisfa. ⛔ **Un `CURSORE_FORMA` di
> cursore nascosto violava la riga accanto sempre, qualunque cosa il mittente ci mettesse** — e un
> ricevente che applicasse §5.5 alla lettera chiudeva con `ERRORE_PROTOCOLLO` ogni volta che il
> puntatore sparisce, con il sintomo *«la sessione cade quando entro in un campo di testo»*, che
> non nomina né il cursore né la regola.
>
> ⚠ È la stessa forma del trattino basso di §4.3 trovato dal validatore di B4: **una regola che
> vieta un caso che il documento stesso definisce**. E R1.21 dichiarava di aver chiuso proprio
> questo — *«larghezza 0 con altezza diversa da 0, e un punto attivo senza intervallo»*: l'intervallo
> era stato aggiunto **senza eccettuare il caso che la riga accanto rende obbligatorio**.

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

Uno stream, un fotogramma. Nessuna lunghezza: **la fine dello stream è la fine del fotogramma** —
⛔ **ma solo se lo stream è finito con un FIN**.

> ⛔ *Aggiunte due parole la sera del 9 agosto 2026, rilievo **R1.7**, e senza di esse il documento
> era rotto proprio dove §5.1 concede di abbandonare.* Il server apre lo stream del fotogramma 101,
> spedisce l'intestazione e 40 KB su 60, poi lo **azzera** perché è partito il 102. Il client ha in
> mano 40 KB e uno stream «finito»: consegnandoli al decodificatore ottiene un rifiuto o — peggio —
> mezza immagine. **Un fotogramma abbandonato e uno completo avevano lo stesso aspetto**, ed è la
> forma d'errore **E8**.

⛔ **La regola, in due righe:**

- uno stream chiuso con **FIN** porta un fotogramma **completo**;
- uno stream **azzerato** (`RESET_STREAM`) porta un fotogramma **incompleto**: il client **DEVE**
  buttare quel che ha ricevuto, **NON DEVE** consegnarlo al decodificatore, e **DEVE** trattarlo
  come un buco (§5.2);
- uno stream chiuso con **FIN prima dei 28 byte** dell'intestazione è `ERRORE_PROTOCOLLO`: non è un
  fotogramma corto, è una lunghezza che non torna (§3);
- ⛔ **e un fotogramma abbandonato può non presentarsi come stream affatto**: se il server ha
  consumato il `numero` e ha abbandonato **prima che un byte uscisse**, il client non vede nessuno
  stream — vede un **buco nella successione dei `numero`**. È la **forma B** dell'abbandono, e va
  trattata come un buco esattamente come l'azzeramento (§5.1, il riquadro delle due forme).

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
| `largh.`, `altezza` | la misura di **questo** fotogramma. ⛔ In RCP/1 **DEVONO** valere la **tela in vigore** — quella concessa in `SESSIONE` (§4.5), **oppure** l'ultima concessa da `TELA` se nel frattempo è stata adattata (§7.1) — e chi ne riceve altre chiude con `ERRORE_PROTOCOLLO`: il client riscala alla **vista**, non alla tela (`SPECIFICHE.md` §6.1). Il campo esiste lo stesso perché il giorno in cui si decidesse di codificare più piccolo quando la finestra è piccola — `DECISIONI.md` §5.0-ter, che è una `[?]` volutamente fuori dal modello — **il protocollo non cambia**: cambierebbe questa riga |
| `numero` | ⛔ contatore dei fotogrammi **che il server decide di spedire**, che cresce di uno per ciascuno — **compresi quelli che poi abbandona**, e ⛔ **NON** per quelli che non spedisce affatto. ⚠ *Diceva «dei fotogrammi **catturati**» e insieme «che il server decide di spedire»: **due letture nella stessa frase**, e alla fase 3 si separano — calando i fotogrammi quando la linea non porta (I1, §8.3), la prima lettura aprirebbe **un buco per ogni salto**, quindi una `RICHIEDI_CHIAVE` per ognuno, cioè **la spirale che §5.2 esiste per evitare** proprio quando la linea è cattiva. Corretto il 12 agosto 2026, rilievo **P16**, trovato scrivendo il prodotto.* Un buco nella successione è quindi normale e **significa qualcosa**: è il segnale su cui §5.2 fa chiedere una chiave. ⛔ **Il primo fotogramma di una sessione porta `numero = 1`, e lo `0` è riservato**: vuol dire «nessun fotogramma», che è il significato che §7.1 gli dà in `RICHIEDI_CHIAVE`. ⚠ È la stessa convenzione dell'`id` dell'input (§7.3), e per la stessa ragione: senza, `RICHIEDI_CHIAVE(0)` vuol dire due cose e il server non può scegliere — cioè il valore sentinella implicito che §6.0 vieta. ⛔ **E al giro del contatore lo `0` si salta**: l'aritmetica è modulo 2³², una sessione può durare più di un giro, e da `0xFFFFFFFF` si passa a **`1`** — senza questa riga il valore riservato tornerebbe in circolo da solo |
| `istante` | microsecondi dell'orologio **monotono del server** alla cattura |
| `input` | ⭐ **l'identificatore dell'ultimo input iniettato prima della cattura**; **0** se nessuno |

⛔ **Il tetto vincola prima di tutto chi spedisce**: il server **NON DEVE** produrre un fotogramma
più lungo di **16 MiB**. Se la codifica ne producesse uno più grande, **DEVE** ricodificarlo a
qualità inferiore e **scriverlo nel registro** — mai spedirlo. Chi ne riceve uno più lungo chiude
con `ERRORE_PROTOCOLLO` invece di continuare ad accumulare.

> ⚠ *La prima metà è della sera del 9 agosto 2026, rilievo **R1.23**: il tetto vincolava solo il
> **ricevente**, cioè era una punizione per chi subisce.* Una tela 7680×4320 è legale (§4.5) e il
> desiderato è a 10 bit: un fotogramma chiave di una scena complessa a quella misura può superare i
> 16 MiB. Il client avrebbe staccato la sessione perché il server ha fatto una cosa che §4.5 gli
> permette — e §5.2 gli vieta pure di abbandonare le chiavi, quindi non aveva vie d'uscita.
>
> `[?]` **Quanto pesi davvero una chiave 8K a 10 bit va misurato**, ed è una riga del banco della
> fase 8. Se stesse sempre sotto i 16 MiB il difetto di forma resterebbe comunque.

⛔ **L'ordine, e chi lo rimette a posto.** Gli stream sono indipendenti, quindi i fotogrammi
**possono arrivare fuori ordine**. Il client:

- **DEVE** scartare un fotogramma il cui `numero` è **precedente** all'ultimo già consegnato al
  decodificatore;
- **DEVE** trattare `numero` come aritmetica **modulo 2³²**, confrontando le differenze con segno —
  a 60 fotogrammi al secondo il contatore gira dopo due anni e due mesi, e una sessione può durare
  di più;
- **DEVE** riconoscere un **buco** e chiedere una chiave (§5.2).

⛔ **E c'è il verso opposto, che è il quinto della stessa famiglia**: un fotogramma alla misura
**nuova** può arrivare **prima** del `TELA` che la concede — il `TELA` viaggia sul canale di
controllo, il fotogramma su uno stream suo, e **niente ne ordina la consegna**. ⇒ Il client che
ricevesse una misura che «non è mai stata in vigore» chiuderebbe **una sessione in cui nessuno ha
sbagliato**.

⛔ **Il client NON DEVE chiudere: trattiene il fotogramma**, e lo scrive nel registro. ⭐ **E fino a
quando lo trattiene non è un numero: è una condizione** — finché resta una `ADATTA_TELA` che **il
client ha spedito** e a cui nessun `TELA` ha ancora risposto. Arrivato quel `TELA`, il fotogramma
trattenuto **si rigiudica** contro la tela che quel `TELA` dichiara in vigore, e da lì è un
fotogramma come tutti gli altri: prima la regola dell'ordine, poi quella della misura. ⛔ **E se
nessuna `ADATTA_TELA` è senza risposta non si trattiene niente**: una misura che il client non ha
nessun motivo di aspettarsi è `ERRORE_PROTOCOLLO` subito.

⚠ **E il `TELA` arriva per forza**, che è la ragione per cui questa è una fine e non un'attesa
aperta: §7.1 impone *«a ogni `ADATTA_TELA` il server DEVE rispondere con un `TELA`, riuscito o no»*,
e il canale di controllo è **uno solo, affidabile e ordinato** (§4.2) ⇒ l'n-esimo `TELA` risponde
all'n-esima `ADATTA_TELA`, e chi trascina una finestra ne manda due senza che il conto si perda.
⛔ Un `TELA(RIFIUTATA)` chiude l'attesa quanto un `TELA(ADATTATA)`: il trattenuto si rigiudica contro
la tela rimasta in vigore, e di norma **è `ERRORE_PROTOCOLLO`** — il server ha spedito una misura che
non ha mai avuto.

⭐ **E la grandezza è «una richiesta in volo», non «la misura che il client ha chiesto»**: §4.5 dice
che *«la tela concessa può essere diversa da quella chiesta»* — su KWin < 6.8 è la strada normale
(`SPECIFICHE.md` §6.3) e la negoziazione di §6.4 concede il modo che il compositore **ha**. ⇒ Un
client che trattenesse solo i numeri che ha nominato chiuderebbe una sessione in cui il server ha
fatto esattamente quel che §7.1 gli permette. ⚠ È la stessa grandezza di **P20** — *quel che il
client ha spedito lui*: locale, monotona, indipendente dalla consegna.

> ⚠ *Questo paragrafo diceva «trattiene **finché non sa decidere**», e accanto portava un riquadro
> `[?]` che dichiarava aperta la domanda «fino a quando». Il prodotto la chiudeva con **otto
> fotogrammi** — un fondo osservabile invece di un orologio, che era già la lezione di P13, ⛔ ma pur
> sempre **una grandezza sostitutiva**. Chiusa il 13 agosto 2026, rilievo **P21**. ⭐ E la prima cura
> proposta — «la misura che il client ha nominato» — è stata **bocciata da un caso**: §4.5 permette
> al server di concedere una tela diversa da quella chiesta, quindi sarebbe stata l'ottava stesura.*

> ### ⛔ E il trattenimento **non ha tetto in byte** — la riga mancava
>
> *13 agosto 2026. Il paragrafo qui sopra dice fino a **quando** si trattiene, e non dice **quanto**.
> Sono due domande diverse, e la seconda non aveva risposta da nessuna parte.*
>
> ⛔ **La condizione di fine è corretta e non basta.** §7.1 obbliga il server a rispondere a ogni
> `ADATTA_TELA` con un `TELA`, riuscito o no — ed è la ragione per cui la condizione «finché una
> `ADATTA_TELA` è senza risposta» **finisce**. ⛔ Ma un server che **non risponde** non viola una
> regola che il client possa far rispettare: fa crescere la coda del client **senza limite**, e il
> client conforme continua a trattenere finché la memoria regge. ⇒ Il difetto non è del client:
> **è una riga che manca a questo documento.**
>
> ⇒ **Le due regole:**
>
> - ⛔ il client **DEVE** avere un tetto al trattenuto, e superarlo **NON è `ERRORE_PROTOCOLLO`**:
>   il server non ha sbagliato niente in un modo che il client possa dimostrare. Si butta il più
>   vecchio, **lo si scrive nel registro**, e si tratta come un buco (§5.2). Un fermo-immagine con
>   una riga di registro è meglio di una sessione che finisce la memoria in silenzio;
> - ⛔ **e il tetto si conta in FOTOGRAMMI, non in richieste in volo.** ⚠ Il paragrafo qui sopra non
>   lo diceva, e sono due grandezze diverse: le richieste in volo dicono **se** si trattiene, i
>   fotogrammi dicono **quanto**. ⭐ E un fotogramma si conta **una volta sola anche se viene
>   rigiudicato due volte** — un trattenuto che al primo `TELA` non si risolve e resta in attesa del
>   secondo **non è due fotogrammi**. *Il prodotto lo faceva già giusto; il documento non lo diceva.*
>
> ⏳ `[?]` **Quale sia il numero non è deciso qui**: dipende dalla memoria del dispositivo e dal peso
> di una chiave (§6.2 ne ammette 16 MiB), e sceglierlo a caso rifarebbe l'errore di §1.13 —
> una grandezza sostitutiva al posto di quella vera. ⛔ Ma *«non c'è tetto»* non è una risposta, ed
> era quel che il documento diceva tacendo.

⛔ **E la regola dell'ordine si applica PRIMA di quella della misura**: un fotogramma il cui `numero`
è precedente all'ultimo già consegnato **si scarta**, e la sua misura non si guarda nemmeno.
⚠ *Senza questa precedenza le due righe di questa stessa sezione si contraddicono, e vince la più
severa su una scena in cui nessuno ha sbagliato: la chiave che chiude la tolleranza **scavalca** i
fotogrammi in volo — non per caso, ma perché quello vecchio è **il più grosso** (§5.2 vieta di
abbandonare una chiave) e quello nuovo è più piccolo. Rilievo **P14**, 12 agosto 2026, e la stessa
famiglia si era già spostata di un passo tre volte: **P8 → P11 → P13 → P14**.*

⚠ **Il cambio di tela e i fotogrammi in volo.** Dopo aver ricevuto un `TELA(ADATTATA)` (§7.1) il
client **DEVE** accettare i fotogrammi la cui misura vale **una tela che è stata in vigore da quando
la coda ha cominciato a svuotarsi**, dipingendoli riscalati alla vista e scrivendolo nel registro.
⛔ **E la tolleranza non finisce a orologio: finisce quando arriva la prima chiave alla misura
nuova**, che §5.2 gli garantisce. Da quel fotogramma in poi una misura vecchia è
`ERRORE_PROTOCOLLO`; e lo è **subito** una misura che non è mai stata in vigore in quella finestra
⛔ **e che nessuna `ADATTA_TELA` senza risposta può ancora concedere**: se una c'è, il fotogramma
**si trattiene** invece di far chiudere (il paragrafo qui sopra).

> ⚠ *Diceva «la tela **precedente**», al singolare, e ⛔ **chi trascina una finestra ne manda due**:
> 1920×1080 → `TELA(1600,900)` → `TELA(1280,720)`, e la chiave aperta prima di tutto — la più
> grossa, la più lenta, e quella che §5.2 vieta al server di abbandonare — porta 1920×1080, che non
> è né quella in vigore né la precedente. La sessione sana cadeva lo stesso, **un passo più in là**
> della scena che la cura aveva appena chiuso. Corretto il 12 agosto 2026, rilievo **P11**.*
⭐ È la **sesta** eccezione dichiarata a §3, ed è la terza scritta per il verso in cui mancava: §7.1
la dà già alle coordinate di input, per la stessa ragione — il cambio di tela è l'unico momento in
cui i due lati hanno legittimamente due verità diverse. ⛔ Senza, un client conforme **uccide una
sessione sana**: gli stream sono indipendenti, il fotogramma aperto prima che l'`ADATTA_TELA`
arrivasse al server porta legittimamente la misura di prima, e §5.2 vieta al server di abbandonare
una chiave — cioè di sgombrare il tubo proprio dei fotogrammi più grossi, che sono i più probabili
a essere in volo. ⇒ **Dal lato server non è curabile**, e per questo la riga è del client.

> ⛔⛔ *E la prima stesura di questa riga diceva «**per un secondo**», con un orologio — corretta due
> ore dopo, rilievo **P13**. La ragione è che **il secondo era la grandezza sbagliata**: quel che
> deve svuotarsi è una **coda**, e quanto ci mette un fotogramma già in volo dipende dalla **banda**,
> non dall'orologio. Una chiave 1920×1080 può pesare qualche MiB (§6.2 ne ammette 16) e su una linea
> cattiva — che è **dentro** il modello, il minimo dichiarato è 480p a 25 — arriva **dopo** il
> secondo. ⇒ Il client avrebbe chiuso un fotogramma spedito quando era legale, e che §5.2 vietava al
> server di abbandonare: non è solo una sessione sana che cade, è l'invariante **I1** — «mai a
> staccare» — rotta **perché la linea è lenta**, cioè nella condizione esatta che I1 esiste per
> proteggere. ⭐ E allungare il secondo avrebbe spostato il difetto invece di toglierlo: la
> tolleranza finisce su un **fatto osservabile sul filo** — la prima chiave alla misura nuova — che
> §5.2 garantisce esistere.*
>
> ⚠ *Aggiunta il 12 agosto 2026, difetto **D14**, e la marca non è nessuna delle due che questo
> documento usava: non è una **lettura doppia** e non è una **regola derivata** — è una
> **contraddizione interna**. Due implementazioni conformi e attente qui **non divergono**:
> producono lo stesso byte, la chiusura, ed è sbagliato. ⛔ È la specie che nessun confronto fra due
> implementazioni può trovare, ed è la stessa che la prima stesura di **P5** ha avuto per due ore
> quella mattina.*

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
| `0x000F` | `BANCO_MARCA` | → | ⭐ *nuovo, 9 ago notte*: **funzione di banco** — cambia la marca, con un ritardo noto (§7.5) |
| `0x0010` | `BANCO_ESITO` | ← | ⭐ *nuovo, 9 ago notte*: l'esito di `BANCO_MARCA` (§7.5) |

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

⛔ **La vista non ha i vincoli della tela**, e va detto perché la riga precedente diceva il
contrario: qualunque misura da **1×1 in su** è legale, dispari compresa.

> ⛔ *Corretto la sera del 9 agosto 2026, rilievo **R1.17**.* Qui c'era scritto che la vista deve
> stare fra 320×240 e 7680×4320 **con i lati pari**, cioè i limiti della tela — e i limiti della
> tela esistono per una ragione che alla vista **non si applica**: i blocchi del codificatore. In
> RCP/1 la vista **non tocca nessun codificatore** (lo dice questa stessa sezione due righe sopra).
>
> Il caso concreto: l'utente stringe la finestra del browser a 300 pixel, o apre la pagina
> affiancata sul telefono. Con la riga vecchia il client aveva tre scelte, tutte cattive — mandare
> `VISTA(300×800)` e **farsi chiudere la sessione perché ha ridimensionato una finestra**; mentire
> arrotondando a 320, che è la forma d'errore **E2**; o tacere, e lasciare che il server spenda bit
> per una vista che non esiste più. ⚠ Su un telefono con fattore di scala 2,75 nessun
> arrotondamento è innocente: 393 pixel logici valgono 1080,75 fisici.

⚠ La vista non ha nessun vincolo di proporzione con la tela: se le proporzioni non combaciano, si
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
 ├── u16 larghezza          0 con altezza 0 = cursore nascosto (§5.5)
 ├── u16 altezza
 ├── i16 attivo_x           il punto che «punta», dentro l'immagine — ⛔ 0 se nascosto (§5.5)
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
| **la rotella** | ⛔ unità da **120 per scatto**, ⚠ e i mezzi scatti esistono: `60` è mezzo scatto e **non DEVE** essere arrotondato a zero. ⭐ **Il segno è MISURATO** *(10 agosto 2026, su Mutter)*: il client manda `+120` quando l'utente gira la rotella **in su**, e ⛔ **il server DEVE invertire l'asse verticale** prima di passarlo a `libei` — vedi il riquadro |
| **il carattere** | ⛔ un **valore scalare Unicode**: da `0` a `0x10FFFF`, esclusi i surrogati `0xD800`-`0xDFFF`. Fuori intervallo è `ERRORE_PROTOCOLLO` |
| **l'identificatore** | ⛔ cresce di **almeno uno** a ogni messaggio, su tutto il canale di input — non uno per tipo. È quello che torna nel campo `input` dei fotogrammi (§6.2), e con contatori separati non tornerebbe niente |
| **l'`istante`** | ⚠ **nessuna regola di questo documento lo consuma**: il ritardo lo misura l'anello chiuso di `DECISIONI.md` §2.6, e il fotogramma porta indietro l'`id`, non l'istante. Resta perché è l'unico modo di sapere **quando l'utente ha mosso la mano** invece di quando il byte è arrivato, e serve alla diagnosi. ⛔ Il client scrive **microsecondi veri** e **NON DEVE** far credere a una precisione che non ha *(rilievo **R1.27**)*. ⚠ ⛔ **E la premessa di questa riga era FALSA — corretta il 14 agosto 2026, su misura dell'anello del modo classico della fase 4**: diceva *«l'orologio monotono è in millisecondi e la sua grana è deliberatamente ingrossata: il client scrive `millisecondi × 1000`»*. `[M]` su **Chrome 151**, pagina isolata fra origini, `performance.now()` ha grana **5 µs** — **duecento volte** più fine di quel che c'era scritto. ⇒ ⭐ **La regola sopravvive alla premessa che l'aveva prodotta** (*si scrive quel che si sa*), ⛔ ma un client che moltiplicasse i millisecondi per mille butterebbe via **199 parti su 200** di una misura che ha già in mano. ⚠ E la grana **dipende dall'isolamento fra origini**: dove non c'è, torna grossa — quindi si scrive quella che si ha e **si dichiara**, invece di fissarne una nel documento |

> ### ⭐ Il segno della rotella — rilievo **R1.26**, ed è MISURATO
>
> ⚠ *Questo riquadro finiva, fino all'11 agosto 2026, con* «**Finché non è misurata, questa riga
> resta `[?]`**» *— e la misura era stata presa la notte del 10, senza che nessuno la portasse qui
> (rilievo **R12C.7**, e la sonda lo aveva scritto di suo in* `web/rapporti/S-esiti-sonda.md` *§9,
> voce S.7). Chi avesse scritto l'iniezione dell'input alla fase 4 leggendo questa riga avrebbe
> scelto il segno a caso, e il sintomo è* «la rotella va al contrario» *— cioè la forma **E11** che
> questo riquadro esiste per evitare.*
>
> **Perché la domanda esisteva.** Questa riga diceva *«positive verso l'alto e verso sinistra. È
> l'unità di `wl_pointer.axis_value120`, quindi non si converte niente»*. ⛔ **Le due metà citano
> due convenzioni con segni opposti**: in evdev la rotella è positiva verso l'alto, in `wl_pointer`
> il valore è positivo nel verso in cui **scorre il contenuto**, cioè verso il basso. E «positive
> verso sinistra» non corrisponde a nessuna delle due. ⛔ E `libei` **non la scioglie**:
> `ei_device_scroll_discrete` documenta *«the y scroll distance in fractions or multiples of 120»* —
> **dichiara la grandezza e non il verso**. La convenzione non sta nell'API, sta nel compositore.
>
> ⭐ **LA MISURA — `[M]` 10 agosto 2026, 20:59:27→20:59:57 UTC.**
>
> | | |
> |---|---|
> | **che cosa si è visto** | `ei_device_scroll_discrete(0, **+120**)` → l'evento `wheel` della pagina porta **`deltaY = +114`** (`deltaMode = 0`, pixel) e la pagina **scende** di 114 px, cioè va **verso la fine del documento**. Con **−120**, `deltaY = −114` e la pagina **sale** |
> | **la scena, per intero** | macchina di prova **192.168.0.2**; sessione GNOME senza monitor da `banchi/00-sessione-gnome.sh` — `gnome-shell --headless --no-x11 --virtual-monitor 1920x1080`, **libmutter 48.7-0+deb13u1**, **libei 1.3.901**; la pagina in **Firefox 140.13.0esr** in `--kiosk` a schermo pieno sul monitor virtuale, `dpr` 1 |
> | **dove si ricontrolla** | `banchi/01-s7-esiti.jsonl` (due giri, `7sd0u7jv` e `oq7jqrdv`), e il rapporto `web/rapporti/S-esiti-sonda.md` §1 |
>
> ⛔ **La conseguenza, ed è del server**: `deltaY` positivo vuol dire che il contenuto va **verso la
> fine** del documento, cioè che l'utente ha girato la rotella **in giù**; questa sezione fissa
> l'altra metà — il client manda `+120` quando l'utente gira **in su**. Le due convenzioni sono
> **opposte**, quindi **il server DEVE invertire il segno dell'asse verticale** prima di passarlo a
> `ei_device_scroll_discrete`. Iniettando il valore così com'è, lo schermo remoto scorrerebbe al
> contrario per **ogni** utente.
>
> ⭐ **E il confronto è onesto perché i due lati parlano la stessa lingua**: `deltaY` è esattamente
> la grandezza che il client legge quando l'utente gira la rotella vera. Non si confrontano due
> mondi: si misura due volte lo stesso strumento.
>
> **I controlli, e quel che ciascuno vale** *(la ricontata dell'11 agosto, `S-esiti-sonda.md` §0-bis,
> ha separato quel che è nel registro da quel che stava solo a schermo — e qui si riporta la
> separazione, non solo l'esito)*:
>
> | Controllo | Esito | `[M]` o `[?]` |
> |---|---|---|
> | ⛔ **il segno opposto** — si inietta anche `−120` | ✅ `+120 → +114`, `−120 → −114`: si misura **il segno**, non «che qualcosa si muove» | `[M]`, nel registro |
> | ⛔ **i due strumenti concordano** — l'evento `wheel` e lo spostamento vero di `scrollY` | ✅ concordano su tutte le prove | `[M]`, nel registro |
> | ⛔ **`natural-scroll` nei due stati**, col dispositivo rifatto da capo | ✅ **il segno NON cambia**: `+120 → +114` in tutt'e due i giri | ⚠ **metà**: `[M]` che due giri indipendenti danno lo stesso segno; `[?]` **che fossero i due stati** — l'etichetta stava solo nell'uscita a schermo del lanciatore |
> | **il silenzio** — dieci secondi senza iniettare | ✅ nessuno scatto | ⚠ è un'**assenza** di righe: coerente coi timbri, non provata da loro |
> | *in più* — `ei_device_scroll_delta` ha lo stesso verso? | ✅ sì | ⛔ **non ritrovabile**: nessuna riga del registro lo porta. Resta cosa vista, non misura consegnata |
>
> ⚠ **Un fatto in più, per chi scriverà l'iniezione**: uno scatto (120 unità) si traduce in **114
> pixel** su Firefox+Mutter, cioè tre righe. È il fattore di conversione di quella coppia, **non una
> costante del protocollo**: non si scrive qui e non si mette in nessuna formula.
>
> ⛔ **E che cosa NON è chiuso, perché «non chiuso» e «non misurato» sono due stati diversi.** La
> misura è su **Mutter**, e questa sezione vincola **cinque** desktop. Se a normalizzare è `libei`,
> il numero vale ovunque; se normalizza il compositore, la fase 10 troverà un segno diverso su KWin.
> `[?]` **resta per gli altri quattro**, e il banco è rieseguibile su KWin senza cambiare una riga
> della pagina (`banchi/01-s7-rotella.sh` + `01-s7-pagina.html`).
>
> ⚠ *Il precedente che questa riga citava era sbagliato, ed è stato corretto la notte del 9 agosto
> 2026 (rilievo **R4.15**): diceva che «in v1 questa esatta tabella di conversione è costata il
> banco della rotella». `LEZIONI.md` §2.3 dice un'altra cosa — il banco della rotella cercava
> `asse dy=-10` mentre il registro scriveva `asse dx=0 dy=-10`: **rosso, col codice corretto**. È
> una stringa cercata male, non una conversione col segno sbagliato, e citando la lezione sbagliata
> la si perde nel punto in cui si applicherebbe.*

⛔ **Le coordinate sono sulla tela, e sono indici di pixel**: `0 ≤ x < tela_larghezza`,
`0 ≤ y < tela_altezza`. Su una tela 1920×1080 l'angolo in basso a destra è **1919, 1079**. Il client
conosce la tela (§4.5) e sa dov'è la sua vista dentro di essa: la conversione è sua, **arrotondando
per difetto**. Il server **NON DEVE** applicare nessuna trasformazione alle coordinate ricevute, e
**DEVE** rifiutare con `ERRORE_PROTOCOLLO` una coordinata fuori intervallo — salvo il secondo di
grazia di §7.1, dove satura all'ultimo pixel valido.

> ⚠ *L'intervallo mancava, e la riga diceva solo «fuori dalla tela» (rilievo **R1.16**). Una pagina
> che divide la posizione del mouse per il fattore di scala e arrotonda per eccesso produce 1920 su
> una tela di 1920: una lettura lo inietta, l'altra **chiude la sessione**. E chiudere la sessione
> per un arrotondamento è la cosa che `SPECIFICHE.md` §8.3 vieta — «mai staccare».*

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
 ├── u32 trasferimento       ⭐ l'identificatore, scelto da chi annuncia
 └── u32 lunghezza           quanti byte ha il testo disponibile

APPUNTI_CHIEDI
 └── u32 trasferimento       quello dell'annuncio a cui si risponde

APPUNTI_TESTO
 ├── u32 trasferimento       quello della richiesta che si sta servendo
 └── byte                    fino alla fine dello stream, UTF-8 valido
```

> ### ⛔ Due correzioni della sera del 9 agosto 2026 — rilievi **R1.11** e **R1.20**
>
> **L'identificatore mancava del tutto.** La regola *«ogni trasferimento va sul suo stream»* non era
> soddisfacibile: i tre messaggi viaggiano in **due versi** e gli stream sono **unidirezionali**,
> quindi un trasferimento ne occupa almeno due. E senza un campo che li leghi, con due annunci
> aperti nei due versi — *l'utente copia di qua mentre incolla di là* — le due implementazioni
> appaiano le richieste agli annunci **in ordine diverso e si scambiano i testi**.
>
> ⛔ Ciascun lato numera **i propri** trasferimenti, da 1 e crescendo. Un `APPUNTI_CHIEDI` con un
> identificatore che non corrisponde a nessun annuncio vivo è `ERRORE_PROTOCOLLO`.
>
> **E la seconda lunghezza è stata tolta.** `APPUNTI_TESTO` portava `u32 lunghezza` *dentro* un
> messaggio che ha già la sua lunghezza nell'inquadratura di §6.1: due verità sullo stesso fatto,
> cioè il difetto che §2.2 vieta con quelle parole. ⚠ Con una conseguenza sull'implementazione:
> il testo si legge **fino alla fine del messaggio**, e il tetto è quello di §5.4.

Bidirezionale. Si annuncia e si chiede, invece di spingere: chi copia un documento intero non lo
spedisce a nessuno finché qualcuno non incolla.

⛔ **Il contenuto è sempre e solo testo semplice in UTF-8**, e non c'è nessun campo che dichiari un
tipo: non esiste perché non c'è niente da scegliere. ⚠ *Questa riga diceva «un tipo diverso è
`ERRORE_PROTOCOLLO`», e nessun messaggio portava un campo di tipo — una regola che nessuna
implementazione poteva violare e nessun banco vedere fallire, e che invitava chi legge ad aggiungere
un campo inesistente (rilievo **R1.20**).*

⛔ **Ogni trasferimento ha il suo identificatore**, e i messaggi di trasferimenti diversi non si
mescolano. ⚠ Un `APPUNTI_CHIEDI` che arriva quando l'annuncio è già stato superato da uno più
recente si serve **con il testo attuale**, e il mittente lo scrive nel registro: è la corsa normale
fra due persone che copiano, non un errore. ⭐ **Ed è la quinta eccezione dichiarata a §3** — vedi
l'elenco lì.

⛔ Un `APPUNTI_TESTO` che nessuno ha chiesto è `ERRORE_PROTOCOLLO`: gli appunti si tirano, non si
spingono.

### 7.5 ⭐ La funzione di banco: la marca, e il ritardo noto

*Aggiunta la notte del 9 agosto 2026, rilievo **R3.4** della revisione del banco della fase 1, e
**prima del primo byte di codice** — §9 chiude la finestra dei tipi nuovi da lì in poi, e la clausola
che la teneva aperta era che allora non esistesse nessuna implementazione. ⛔ **Il primo byte è del
10 agosto 2026 e la finestra è chiusa** (§0-bis, §9): questi due tipi sono entrati con l'ultima
occasione, e non ce n'è una seconda. ⚠* Diceva «*la clausola che la tiene aperta è che **oggi** non
esiste nessuna implementazione*», *al presente — corretta l'11 agosto 2026, rilievo **R12C.2***.

⚠ **La sua marca resta 🔸, non ✅**, ed è registrata dove le decisioni stanno: `DECISIONI.md` §1.5
riga 26. La domanda *«era una decisione dell'utente?»* — rilievo **R11.15** — **è stata chiusa
l'11 agosto 2026**: no, non lo era, e resta togliibile senza tornare da lui.

> ### ⛔⭐ E DA OGGI NON ENTRA NEL PRODOTTO CONSEGNATO — ✅ 11 agosto 2026
>
> *`DECISIONI.md` §7.16, dall'utente: «l'utente deve vedere il desktop senza artefatti, come se
> fosse davanti al monitor del PC … si tiene quello che serve per i test, ma poi nel prodotto
> finale si fa pulizia».*
>
> ⛔ **Questa è una funzione di BANCO, e nel binario che si installa NON DEVE esserci.** Non spenta:
> **assente** — non compilata, non raggiungibile, e ⛔ **non trovabile cercandone le marche dentro il
> binario**. Sullo schermo di chi si collega non compare mai niente che non sia il suo desktop.
>
> ⚠ **«Spenta» era la forma di prima, e non basta più.** La funzione nasce spenta e
> `banchi/01-b5-violazioni.py` verifica che a funzione spenta il server rifiuti con
> `FUNZIONE_SPENTA`: quel comportamento **resta**, ed è giusto — ma vale per la **costruzione di
> prova**, che è la sola in cui questi due tipi esistano.
>
> ⛔ **E la differenza si misura, o è una buona intenzione**: *«non c'è»* e *«c'è ed è spenta»* hanno
> lo stesso aspetto da fuori. Si separano **cercando le marche dentro il binario consegnato** — la
> stessa tecnica con cui `banchi/01-p1-prodotto.sh` distingue un binario nuovo da uno vecchio. Il
> banco è della **fase 13**, dove il pacchetto nasce.
>
> ⭐ **Perché la funzione sopravvive comunque**: taratura del cronometro del ritardo alla fase 3 —
> si inietta un ritardo noto e si verifica che la mediana salga di esattamente quello. Toglierla del
> tutto avrebbe lasciato il tetto dei 50 ms **senza un modo di sapere se il numero è vero**.

> ### ⛔⛔ 13 agosto 2026 — **la funzione di banco NON dà il ritardo noto**, e non l'ha dato alla fase 3
>
> *Questo paragrafo è normativo e descrive un meccanismo che nel prodotto **non c'è**. Va scritto
> qui, o chi legge questa sezione crede di avere in mano uno strumento che non esiste.*
>
> | | stato `[R]` |
> |---|---|
> | la funzione | `BANCO_ACCESO 0` — nasce spenta, come §7.5 vuole |
> | ⛔ **il ramo `ACCETTATA`** | **è uno stub**: non dipinge, non aspetta il `ritardo_ms`, non produce l'`istante` che il messaggio promette |
>
> ⇒ ⛔ **P1, il controllo decisivo dell'anello del ritardo, alla fase 3 NON è passato di qui.**
> L'iniezione del ritardo noto è stata fatta **fuori dal prodotto**, ed è risultata `[M]` verde
> (N = 25 → **+25,08 ms**; N = 60 → **+58,58 ms**).
>
> ⭐ **E l'iniezione fuori dal prodotto non è un ripiego: è meglio.** L'ancora d'orologio del metro
> **non passa** per il percorso iniettato — se ci passasse, **P1 passerebbe anche a banco rotto**,
> perché i N millisecondi si sommerebbero identici da tutt'e due le parti. Un controllo decisivo
> che non sa più fallire ha smesso di essere un controllo (`LEZIONI.md` §1.2).
>
> ⇒ ⏳ **Che cosa resta da decidere, e non si decide qui**: se il ramo `ACCETTATA` vada completato o
> se i due messaggi vadano tolti dal protocollo, visto che la loro sola ragione dichiarata —
> «tarare il cronometro del ritardo» — è stata soddisfatta **senza di loro**. ⚠ Finché stanno
> scritti qui e non esistono nel codice, questa sezione descrive una cosa che non c'è: è la specie
> di difetto contro cui §0 esiste.

⚠ **E i due tipi hanno consumato la clausola di §9** che §12 dichiara essere stata *«l'ultima
occasione»* per aggiungere tipi di messaggio: restano nel documento, ⛔ ma d'ora in poi come
**funzione di banco dichiarata**, non come funzione del prodotto.

> ⛔ **Perché una funzione di banco sta nel protocollo e non nel codice di prova.** L'anello del
> ritardo di `DECISIONI.md` §2.6 misura **dal lato che riceve**: il client provoca un cambiamento
> visivo inequivocabile e guarda i fotogrammi che decodifica finché non lo vede. Perché quel numero
> valga, il banco deve poter **iniettare un ritardo noto** e verificare che la mediana salga di
> esattamente quello — ⛔ *«un banco che non lo fa non sa di misurare»*
> (`web/rapporti/S4-ritardo-disegno.md` §4.2, controllo P1).
>
> Quel comando **attraversa il filo**. Improvvisarlo nel codice di prova significa due
> implementazioni che se lo inventano diverso, cioè il difetto muto contro cui §0 esiste — e S4
> §5.3 lo dice con queste parole: *«va scritto in `RCP.md` come funzione di banco, non improvvisato
> nel codice di prova»*.

**I due messaggi, in byte:**

```
BANCO_MARCA                                          client → server
 ├── u32 id            ⛔ cresce di almeno uno a ogni messaggio; 0 è riservato
 ├── u32 colore        0x00RRGGBB — il colore a cui portare la marca
 └── u32 ritardo_ms    ⛔ il ritardo NOTO che il server DEVE aspettare prima di
                       dipingere. 0 = subito. È il controllo del banco

BANCO_ESITO                                          server → client
 ├── u32 id            quello di BANCO_MARCA
 ├── u8  esito         1 = ACCETTATA, 2 = RIFIUTATA
 ├── u8  motivo        0 se accettata; altrimenti:
 │                       1 = FUNZIONE_SPENTA
 │                       2 = RITARDO_FUORI_LIMITI
 └── u64 istante       microsecondi dell'orologio monotono del server, del momento
                       in cui la marca è stata dipinta. ⛔ 0 se rifiutata, ed è
                       l'unico significato di «assente» per questo campo (§6.0)
```

**Dove sta la marca, e chi la dipinge:**

| | |
|---|---|
| **la misura** | **16×16 pixel della tela**, nell'angolo in alto a sinistra: da `0,0` a `15,15` |
| ⛔ **perché 16 e non 1** | il video è codificato in **4:2:0**, quindi la crominanza è a metà risoluzione, e i codificatori lavorano a blocchi. Un quadratino piccolo o a cavallo di un bordo di blocco viene **spalmato**, e il banco leggerebbe un colore che non è stato mandato. ⚠ E chi riceve **DEVE** leggere la **mediana** dei 256 pixel, con tolleranza, non il pixel centrale |
| ⛔ **chi la dipinge** | **il server**, nel fotogramma che sta per codificare — **dopo la cattura**. ⚠ *Quindi la misura che ne esce **esclude il compositore**, e questo va dichiarato accanto a ogni numero: è il ritardo di* codifica → filo → decodifica → disegno*, non quello che l'utente sente. Il pezzo del compositore lo misura l'anello completo di `DECISIONI.md` §2.6, che passa dall'input vero* |
| ⚠ **e nella tela, non nella vista** | il client riscala: se vista e tela non coincidono, i 16×16 della tela diventano un'altra misura sul suo disegno, e **il calcolo è suo** |

**Le regole, e sono cinque:**

1. ⛔ **La funzione è SPENTA salvo che l'amministratore non l'accenda nella configurazione del
   server.** È l'invariante **I6** alla lettera — *ciò che cambia quel che si vede sta dietro un
   interruttore spento di suo* — e qui letteralmente dipinge sopra il desktop di qualcuno;
2. ⛔ **spenta, il server risponde `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)`. NON DEVE tacere e NON
   DEVE chiudere**: un silenzio lascia il banco ad aspettare per sempre, ed è lo stesso difetto che
   §7.1 vieta per `ADATTA_TELA`. Un client che chiede una funzione spenta non ha violato niente;
3. ⛔ **il server DEVE dichiararla**: la capacità `banco.marca` di §4.3. Un client che la chiede
   senza che sia stata dichiarata riceve comunque `FUNZIONE_SPENTA`, non un errore di protocollo;
4. `ritardo_ms` **DEVE** stare fra **0 e 10 000**; fuori è `BANCO_ESITO(RIFIUTATA,
   RITARDO_FUORI_LIMITI)` — ⚠ **non** `ERRORE_PROTOCOLLO`: è un parametro di banco sbagliato, e far
   cadere la sessione al banco che si sta tarando è la stessa cattiva idea di §7.1 per le misure
   fuori limite;
5. ⛔ **ogni accensione e ogni `BANCO_MARCA` servito si scrivono nel registro del server.** Una
   sessione che dipinge quadratini colorati sul desktop di una persona **deve poterlo dimostrare
   dal registro**, o il giorno in cui qualcuno se ne lamenterà non ci sarà modo di sapere se è
   stata accesa.

⚠ **E `istante` non serve a misurare il ritardo**: serve al banco per **distinguere il ritardo che
ha chiesto lui da quello che ha trovato**. Il ritardo lo misura il client, dal lato che riceve, come
dice `DECISIONI.md` §2.6 — questo campo dice soltanto quando il server ha obbedito.

---

## 8. Il congedo

### 8.1 Si dice, e si verifica dal lato che riceve

⛔ Chi chiude **DEVE** mandare `CONGEDO` con un motivo **prima** di chiudere la **sessione
WebTransport** — ⛔ **se il canale di controllo è ancora utilizzabile** (§3.1 punto 2) — e **DEVE**
ripetere il motivo nel codice d'errore applicativo della chiusura (§3.1 punto 3). ⭐ **Il punto 3
non ha condizioni e non ne ha bisogno**: viaggia nella chiusura stessa, e parte anche quando il
canale è morto.

> ⛔ *Corretto il 10 agosto 2026, rilievo **R11.8**: qui c'era «prima di chiudere la **connessione
> QUIC**», e in §4.4 «con lo stesso motivo nel **`CONNECTION_CLOSE`**». Sono i due resti che la
> correzione R1.4 di §3.1 non aveva raggiunto, e §8.1 è il paragrafo che detta l'obbligo a **chi
> chiude** — che è spesso la pagina, cioè il lato che R1.4 dichiara **incapace** di chiudere la
> connessione HTTP/3 sotto.*
>
> ⛔ **È lo stesso ingresso con due byte diversi** — un `CONNECTION_CLOSE` di trasporto contro una
> `CLOSE_WEBTRANSPORT_SESSION` — cioè la forma esatta che R1.4 dichiarava di aver chiuso: *«un
> programmatore chiudeva la sessione e dichiarava assolta la regola; l'altro cercava l'API della
> connessione, non la trovava, e lasciava il punto 3 non implementato — ed era conforme al testo
> quanto il primo»*. ⚠ E §4.4 lo imponeva proprio sul percorso `RESPINTO`, quello che B11 ha
> riaperto il 10 agosto.

⚠ **E questa riga ha un prezzo già pagato.** In v1, per **tre fasi**, il server scriveva compìto
«congedo il client» mentre il client, alla stessa ora, scriveva «errore di rete»: mancava una
seconda chiamata di libreria che nessuno sospettava (`LEZIONI.md` §1.7). Da cui l'obbligo di
collaudo: **il congedo si verifica dal lato che lo riceve**, mai dal registro di chi lo manda.

⚠ **L'unica eccezione è `RESPINTO`** (§4.4), che *è* il congedo dell'autenticazione.

> ### ⛔ E «chi chiude» non è chi ha ricevuto un `FIN` — ✅ 11 agosto 2026
>
> *L'eccezione che la decisione di `DECISIONI.md` §7.14 pretende, scritta qui perché è qui che
> l'obbligo è dettato. Senza questa frase §4.2 vieta di spedire sul canale di controllo dopo un
> `FIN` e §8.1 continua a **imporre** proprio quel byte: la decisione avrebbe spostato la
> contraddizione invece di chiuderla.*
>
> ⛔ **Chi riceve un `FIN` sul canale di controllo non è «chi chiude», e non manda nessun
> `CONGEDO`.** A chiudere è stata l'altra parte; il motivo di quella chiusura arriva da lei, e la
> sola cosa dovuta a chi riceve è **considerare la sessione finita** (§4.2).
>
> ⭐ **Restano dovuti i byte del punto 3 di §3.1** — il codice d'errore applicativo — quando è
> **questo** lato a chiudere la sessione WebTransport per primo. L'eccezione riguarda il `CONGEDO`
> sul canale, non il motivo nella chiusura.

> ### ✅ La condizione, decisa dall'utente l'11 agosto 2026 — `DECISIONI.md` §7.15
>
> *Fino a oggi questa riga non poneva condizioni, mentre §3.1 punto 2 dice «**se il canale di
> controllo è ancora utilizzabile**»: ⛔ **un'implementazione conforme a §3.1 era in violazione di
> §8.1**, e due sezioni normative dello stesso documento davano due verdetti sullo stesso ingresso
> — la violazione che arriva su uno stream unidirezionale col controllo già finito (rilievo
> **R11.23**).*
>
> ⛔ **Vince la condizione.** L'obbligo del `CONGEDO` sul canale **cade quando il canale non è
> utilizzabile**; quel che non cade mai è il motivo dentro il codice di chiusura (§3.1 punto 3).
>
> ⭐ **La ragione, con le parole dell'utente**: *«se una connessione cade nessuno può dire al server
> "chiudo perché ho finito"»*. Un `DEVE` che non si può rispettare non è una regola: è un difetto
> di questo file, e §0 dice che i difetti di questo file sono di questo file.
>
> ⚠ **E non indebolisce `DECISIONI.md` §4.1-bis**, decisa lo stesso giorno — *ogni chiusura del
> server ha un motivo che sa spiegare*: il motivo arriva comunque, per la seconda strada. ⛔ Quel
> che si perde è **solo il byte sul canale morto**, cioè un byte che non partiva.
>
> ⭐ **E chiude un rosso su codice giusto**: **B5 e B11 applicavano già il condizionale di §3.1**
> (`fasi/01-filo-nudo.md`, rilievo R3.3), e un banco scritto sulla forma assoluta **avrebbe bocciato
> un server corretto** ogni volta che la violazione arriva su uno stream unidirezionale.
>
> ⛔ **E le due decisioni dell'11 agosto non si sostituiscono.** §7.15 dice *quando* l'obbligo cade;
> §7.14 dice *chi* non è tenuto affatto. Dopo un `FIN` ricevuto il canale, nel verso di chi lo ha
> ricevuto, **è ancora utilizzabile**: senza §7.14 la condizione di §7.15 non lo salverebbe.

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
| `0x08` | `TROPPI_TENTATIVI` | ⭐ **l'indirizzo è bannato**: tre autenticazioni fallite, dodici ore (§4.4-bis). ⚠ *Diceva «limitazione della frequenza», ed era la forma precedente: dal 10 agosto 2026 non è più una frequenza, è un ban* |
| `0x09` | `NIENTE_IN_COMUNE` | nessun codec condiviso |
| `0x0A` | `VERSIONE_INCOMPATIBILE` | |
| `0x0B` | `ERRORE_PROTOCOLLO` | §3 |
| `0x0C` | `SERVER_IN_CHIUSURA` | |
| `0x0D` | `TEMPO_SCADUTO` | ⭐ *nuovo, 9 ago*: un tetto di §4.6 è scaduto |
| `0x0E` | `SESSIONE_NON_SERVIBILE` | ⭐ *nuovo, 9 ago*: l'attacco è ben formato ma non si può servire — un compositore che non parte, una disposizione che il sistema non conosce. **DEVE** portare il dettaglio nel corpo |
| `0x0F` | `GIA_ATTIVA_REMOTA` | ⭐ *nuovo, 9 ago sera*: **c'è già un client attaccato a questa sessione**, e questa connessione viene **rifiutata** |

> ### ⛔ Perché `0x0F` è stato aggiunto, e perché adesso — rilievo **R1.3**
>
> I quattordici motivi precedenti coprivano **locale contro remoto** (`SPECIFICHE.md` §5.1) e non
> **remoto contro remoto**: sei attaccato dal portatile e apri la stessa sessione dal telefono.
>
> **La scelta, dell'utente, il 9 agosto 2026**: *«se un utente ha già una sessione grafica remota
> attiva, e ne vuole attivare una seconda da un secondo device, la seconda connessione viene
> rifiutata»*. ⭐ È l'invariante **I2** applicata alla lettera — *«la seconda connessione è rifiutata
> con messaggio esplicito»* — e `0x0F` è il gemello remoto di `0x05 GIA_ATTIVA_LOCALE`.
>
> ⛔ **Chi viene rifiutato è chi arriva, non chi c'era.** Nessun client attaccato e vivo viene mai
> spodestato da un altro.
>
> ⚠ **E il confine con `DECISIONI.md` §4.4 va letto bene**, perché le due regole sembrano cozzare e
> non cozzano: *«chi tace è staccato, chi arriva entra»* parla del client **fantasma** — il telefono
> morto in galleria. Un client **silenzioso da 30 secondi** (`SPECIFICHE.md` §5.3) non è più
> attaccato, quindi non occupa niente e il nuovo entra. Un client **vivo** occupa, e il nuovo è
> rifiutato. ⛔ Il discrimine è **l'orologio del silenzio**, non l'intenzione di chi arriva.
>
> ⚠ **Il prezzo, dichiarato**: se il portatile si spegne di colpo senza congedarsi, dal telefono si
> entra **dopo trenta secondi**, non subito.
>
> ⚠ E la finestra per aggiungere un motivo si è chiusa subito dopo: §9 lo vieta dentro una versione
> maggiore, e la clausola che lo permetteva era che allora non esistesse nessuna implementazione.
> ⛔ **Dal 10 agosto 2026 esistono** (§0-bis), e questa strada non c'è più. ⚠ *Diceva «la clausola
> che lo permette è che **oggi** non esiste nessuna implementazione», al presente: corretta l'11
> agosto 2026, rilievo **R12C.2**.*

⛔ Ogni motivo **DEVE** essere mostrabile all'utente in una frase comprensibile. `BUDGET_PIENO`
non è «errore 6»: è «questa macchina non ha più capacità di codifica».

⛔ **La frase la costruisce il client**, dal codice. Il campo `dettaglio` **NON DEVE** essere
mostrato all'utente: è per il registro, e contiene quel che serve a chi diagnostica.

---

## 9. Le versioni

`CIAO` porta la versione maggiore che il client sa parlare; `ECCOMI` quella scelta dal server.
Se non c'è una versione comune, `VERSIONE_INCOMPATIBILE`.

⛔ **In concreto**: il server sceglie la versione più alta che sa parlare e che non superi quella
del `CIAO`, ⛔ **fra quelle che il percorso ammette (§2.2)**. Se non ne ha nessuna, congeda. Il
client **DEVE** verificare che la versione di `ECCOMI` sia una che sa parlare, e congedare con
`VERSIONE_INCOMPATIBILE` se non lo è — un server che risponde con una versione più alta di quella
chiesta sta sbagliando, e accettarla in silenzio è l'indulgenza che §3 vieta.

> ### ⛔⭐ Le sette parole di §2.2 sono del 10 agosto 2026, e le ha trovate **B5**
>
> ⚠ *Il numero di sezione è stato corretto lo stesso giorno, rilievo **R11.18-bis** (R11.2): queste
> tre righe mandavano a **§2.4**, che è «La porta» — 7447, TCP e UDP — e non nomina né i percorsi
> né le versioni. La regola vive in **§2.2**, righe «l'indirizzo della sessione … il numero dopo la
> barra è la versione maggiore» e «le due DEVONO coincidere», ed è lì che R1.24 l'ha scritta.*
> ⛔ **Chi leggeva §9 e andava a §2.4 come gli si diceva trovava la porta, nessun vincolo, e
> tornava a §9** — cioè ricostruiva esattamente la lettura che aveva prodotto la prima stesura di
> `banchi/rcp/rcp.c`. La cura di una contraddizione fra due sezioni mandava a una terza.
>
> Questo paragrafo diceva soltanto *«la più alta che non superi quella del `CIAO`»*. §2.2 dice che
> un `CIAO(versione=2)` su `/rcp/1` è `VERSIONE_INCOMPATIBILE`. ⛔ **Le due regole danno byte
> diversi sul filo per lo stesso ingresso** — `ECCOMI(1)` contro `CONGEDO(0x0A)` — e **nessuna
> delle due citava l'altra**.
>
> ⚠ Non è un caso di scuola: chi scrive il server legge §9, che è il paragrafo intitolato *«Le
> versioni»*, e scrive `if (versione < LA_MIA) congeda;`. È esattamente quel che è successo — la
> prima stesura di `banchi/rcp/rcp.c` **accettava un `CIAO(2)`** e rispondeva `ECCOMI(1)`, ed era
> conforme a §9 alla lettera.
>
> ⭐ **Vince §2.2**, perché è la più specifica e perché è stata scritta per risolvere proprio questo
> caso (rilievo R1.24). Questa riga adesso la nomina, così chi legge solo una delle due trova
> l'altra.
>
> ⚠ È la **seconda** contraddizione interna trovata da un banco in due giorni: la prima fu il
> trattino basso di §4.3, trovato dal validatore di B4. ⭐ Tutt'e due sono state trovate da
> programmi che leggevano **solo questo documento**, e nessuna delle due da chi lo rileggeva.

**Dentro una versione maggiore si cresce solo per capacità** (§4.3), mai aggiungendo campi a
messaggi esistenti né tipi nuovi che il vecchio dovrebbe ignorare — perché ignorare è vietato
(§3). Un tipo nuovo obbligatorio è una versione maggiore nuova.

⚠ **In pratica, finché client e server si aggiornano insieme, la versione serve a poco.** Serve il
giorno in cui un telefono resta indietro — e quel giorno o si è scritta bene, o si scopre che il
campo in più lo si era aggiunto «tanto è compatibile».

⛔ **E la finestra in cui questo documento si poteva ancora completare È CHIUSA**: il divieto qui
sopra protegge le implementazioni esistenti, e **adesso esistono** — l'elenco, contato, sta in
§0-bis. **Dal 10 agosto 2026, primo byte di codice, vale la regola senza sconti.**

⛔ **Quanto è stata usata la finestra, prima di chiudersi: QUATTRO tipi, non due.**
`RICHIEDI_CHIAVE` (`0x000D`) e `TELA` (`0x000E`) il 9 agosto; ⭐ **`BANCO_MARCA` (`0x000F`) e
`BANCO_ESITO` (`0x0010`) la notte del 9** (§7.5). Più **tre** motivi di congedo (`TEMPO_SCADUTO`,
`SESSIONE_NON_SERVIBILE`, `GIA_ATTIVA_REMOTA`). Il conto sta in `DECISIONI.md` §1.5, e §12 dichiara
che quella dei due della funzione di banco è stata *«l'ultima occasione»*.

> ⚠ *Questa riga diceva* «I **due** tipi aggiunti il 9 agosto (`0x000D`, `0x000E`) sono entrati sotto
> questa clausola», *e la finestra la dichiarava aperta. I due della funzione di banco erano stati
> aggiunti nella stessa notte e non erano mai stati portati qui: la cura del rilievo **R11.13** era
> arrivata a `DECISIONI.md` e non alla riga che tiene il conto della clausola — cioè chi verificava
> quanto era stata usata una finestra irripetibile, contando da qui, ne trovava la metà. Corretta
> l'11 agosto 2026, rilievo **R12C.3**.*

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
| **il congedo** | verificato **dal lato che riceve**, per ciascuno dei motivi **che viaggiano in un `CONGEDO`** — e per ciascuno si verifica **anche il codice nella chiusura della sessione** (§3.1). ⚠ *Diceva «per ciascuno dei quattordici»: ma `CREDENZIALI_ERRATE` e `TROPPI_TENTATIVI` viaggiano in `RESPINTO`, che §4.4 vieta di far seguire da un congedo — il banco sarebbe fallito su due motivi per costruzione, e chi lo scriveva avrebbe pensato di aver sbagliato lui (rilievo **R1.18**)* |
| ⭐ **il rilascio dei tasti al distacco** | si stacca una connessione **con un tasto premuto** e si riattacca a verificare che non sia rimasto giù (§7.3). ⛔ **È la regola con il rapporto danno/costo più alto del documento**: un Ctrl rimasto premuto rende inservibile una sessione che sopravvive al client, e nessuno collega le due cose |
| ⭐ **l'audio, ascoltato** | si apre un datagram e si guardano i byte: frequenza, canali, ordine dei byte del PCM. ⛔ Un server che spedisse 44 100 Hz, o PCM big-endian, resterebbe **verde su tutti gli altri banchi** — e il sintomo, come in v1, «sembra un difetto di rete» (`LEZIONI.md` §2.2) |
| ⭐ **gli appunti** | i tre messaggi, l'identificatore di trasferimento, e **due trasferimenti aperti insieme nei due versi**: è il caso in cui senza identificatore i testi si scambiavano |
| ⭐ **il secondo fisso** | si cronometra la risposta a `CREDENZIALI` — **anche quella riuscita** (§4.4-bis). È una proprietà di sicurezza che nessun altro banco vede, e una regressione che la togliesse non farebbe fallire niente |
| ⭐ **il ban dell'indirizzo** | tre autenticazioni fallite, e ⛔ **il quarto tentativo è rifiutato anche con la parola d'ordine GIUSTA** (§4.4-bis) — che è la prova che distingue un ban da un contatore. ⛔ E con **tre nomi utente diversi**, o non si sta provando la regola decisa ma quella vecchia. ⚠ Poi tre controlli che dicono *no*: un **altro** indirizzo entra lo stesso · un accesso **riuscito** azzera il conto (due falliti, uno riuscito, due falliti: il terzo **non** banna) · e il ban **sopravvive al riavvio** del server |
| **l'anello del ritardo** | il client manda un input che cambia colore allo schermo e guarda i fotogrammi decodificati finché non lo vede (`DECISIONI.md` §2.6) |
| ⭐ **il ritardo noto** | si chiede `BANCO_MARCA` con `ritardo_ms = N` e **la mediana DEVE salire di esattamente N** (§7.5). ⛔ *È il controllo che rende credibile ogni numero di ritardo di questo progetto: un banco che non lo fa non sa di misurare* |
| ⭐ **la funzione di banco spenta** | ⛔ con `banco.marca = no`, un `BANCO_MARCA` **DEVE** ricevere `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)` — **non un silenzio e non una chiusura**. ⚠ E si verifica **dal lato che riceve**: un server che tace lascia il banco ad aspettare per sempre, e il sintomo è «il banco si è piantato» |
| **il rigore** | si manda di proposito un tipo sconosciuto, una lunghezza sbagliata, un messaggio nello stato sbagliato: ⛔ **la connessione deve cadere ogni volta**. Un banco che non prova a violare il protocollo non prova il protocollo |
| ⭐ **il fotogramma abbandonato** | si abbandona un delta di proposito e si verifica che **arrivi una chiave** e che il client non mostri niente di rotto nel frattempo (§5.2). ⚠ Senza questo banco l'abbandono si prova solo su una rete cattiva, cioè quando non lo si sta guardando |
| ⭐ **il credito degli stream** | si tiene una sessione viva **oltre i primi 256 fotogrammi** — cioè oltre i primi quattro secondi — e si verifica che il video non si fermi (§2.3) |
| ⭐ **i tempi della stretta di mano** | si apre una connessione e si tace, per ciascuno dei tre tetti di §4.6 |

⚠ **E il controllo positivo, che qui è facile da dimenticare**: prima di concludere che il
validatore non trova errori, gli si dà una registrazione **con un errore dentro** e si verifica che
lo veda. Uno strumento che non ha mai trovato niente non è uno strumento pulito: è uno strumento
non certificato (`LEZIONI.md` §1.9).

### 11.1 ⛔ Il formato della registrazione

*Scritto il 10 agosto 2026, **prima** del registratore — rilievo R3.6. Il formato è **uno solo**:
due registratori, uno nel C e uno nella pagina, che scrivessero lo stesso fatto in due modi
sarebbero il difetto muto contro cui §0 è stato scritto.*

⛔ **Il problema che questo formato risolve.** Registrare i byte com'erano metterebbe la parola
d'ordine in chiaro in un file, che §4.4 vieta *«a nessun livello»*. Sostituirla lasciando la
`lunghezza` darebbe un corpo che non combacia più, cioè **un falso rosso perpetuo** su ogni traccia
con una stretta di mano riuscita. Sostituirla **e** riscrivere la lunghezza farebbe convalidare al
validatore un documento riscritto dal banco — e allora non è più un arbitro.

⭐ **La quarta strada**: si registra **la lunghezza vera**, si sostituiscono i soli byte segreti con
altrettanti byte di riempimento, e il formato **dichiara quali intervalli sono oscurati**, con
l'impronta di quel che c'era. La lunghezza torna, il validatore sa dove non deve guardare, la
parola non c'è.

```
intestazione (16 byte)
 ├── 8 byte   magia          "RCPREG" 0x00 0x02
 ├── u32      quanti_blocchi
 └── u32      riservato      DEVE essere 0

poi `quanti_blocchi` blocchi, ciascuno:
 ├── u8       verso          1 = client → server, 2 = server → client
 ├── u8       canale         il byte alto di `tipo` (§2.5)
 ├── u8       fine           ⛔ come si è chiuso lo stream DOPO questo blocco:
 │                             0 = continua · 1 = FIN · 2 = RESET_STREAM
 ├── u64      stream         l'identificatore dello stream QUIC
 ├── u32      lunghezza      quanti byte di carico seguono — ⛔ la lunghezza VERA
 ├── u16      quanti_oscurati
 │     per ciascuno:
 │       ├── u32   inizio        scostamento dentro il carico di questo blocco
 │       ├── u32   quanti        ⛔ la lunghezza VERA dei byte sostituiti
 │       └── 32 B  impronta      SHA-256 dei byte veri
 └── `lunghezza` byte di carico
```

> ### ⛔ Il campo `fine` non è un lusso — aggiunto il **12 agosto 2026**, proposta **P7** di F2.4
>
> *E non l'ha trovato una rilettura: l'ha trovato `banchi/02-filo-validatore.py` **provando a
> giudicare una registrazione conforme**, e non riuscendo a dire se il fotogramma fosse completo.*
>
> Senza `fine`, un fotogramma **abbandonato** (§5.1, legale — il client butta e chiede una chiave) e
> uno **troncato per errore** (§3 — la connessione cade) hanno lo **stesso aspetto** nella
> registrazione: il validatore non può applicare la riga che §6.2 ha aggiunto apposta il 9 agosto
> 2026 — *«ma solo se lo stream è finito con un FIN»*, rilievo **R1.7** — ed è la forma **E8**
> rientrata dalla finestra. `[M]` sulla registrazione di prova conforme l'arbitro dichiarava *«di 1
> su 1 NON si è potuta giudicare la completezza»*.
>
> ⚠ **La magia passa a `0x00 0x02`** perché il blocco cambia misura: un validatore vecchio deve
> **rifiutare** il formato nuovo, non leggerlo di traverso.
>
> ⭐ **E non tocca §9**: un blocco di registrazione **non è un messaggio**, e il formato porta già la
> propria versione nella magia.

⛔ **Gli intervalli oscurati contengono `0x2A` ripetuto**, non zeri: uno zero è un valore che i
campi possono avere davvero, e un intervallo di zeri che «per caso» combacia con un corpo legittimo
è un modo di non accorgersi che l'oscuramento c'è.

⛔ **Il validatore NON DEVE leggere dentro un intervallo oscurato**, e **DEVE** rifiutare una
registrazione in cui un intervallo oscurato cade fuori dal carico o si sovrappone a un altro: una
registrazione malformata e un filo non conforme sono due cose diverse, e vanno dette con due frasi
diverse.

⛔ **E il validatore riferisce lo scostamento del byte offensivo in due modi**: assoluto nel file, e
relativo al carico del blocco. Il primo serve a chi guarda il file con un editor, il secondo a chi
legge questa specifica.

---

## 12. ⏳ Quel che RCP/1 lascia aperto, dichiarato

*Non sono buchi: sono cose che non si chiudono adesso, e il motivo per cui non si chiudono.*

⛔ **E una riga di stato, perché cambia che cosa si può ancora fare qui dentro**: dal **10 agosto
2026** — primo byte di codice — la clausola di §9 è **consumata**. Quel che non è chiuso in RCP/1
resta aperto **fino a RCP/2**, o si chiude senza aggiungere tipi di messaggio (§0-bis, §9).

| | Perché non ora | Quando |
|---|---|---|
| ⭐ ~~**il tetto della sessione senza canale di controllo**~~ — ✅ **CHIUSA** | **cinque secondi**, decisi dall'utente l'**11 agosto 2026**: `DECISIONI.md` §7.17, e la riga normativa sta in **§4.6**. ⚠ *Questa casella diceva ancora* «❓ aperta … quando l'utente avrà risposto» *mentre §4.6 dello stesso file porta la riga con il ✅ e la data: **due sezioni dell'arbitro davano due stati diversi alla stessa domanda**, e chi si fosse fidato di §12 avrebbe scritto un server senza quel tetto restando convinto di essere conforme. Corretta la sera dell'11 agosto 2026, alla rilettura d'apertura* | ⛔ **resta da MISURARE**: `B6` vuole un quarto caso — apri la sessione, non aprire il canale, e verifica che a 5 s arrivi `0x0D` **nel codice di chiusura**, non sul canale. *Decisa ≠ misurata.* ⭐ Nessun tipo nuovo: `TEMPO_SCADUTO` c'era già |
| **il microfono** | il verso è previsto, il formato no. Chiuderlo adesso significherebbe scrivere una negoziazione che nessuno esercita | quando `SPECIFICHE.md` §10 smetterà di dirlo «non urgente» — e sarà una **versione maggiore nuova**, perché è un canale in più (§9) |
| **il puntatore relativo** | serve alle applicazioni remote che **catturano** il puntatore, e quel caso lo segnala il server. Non è il caso di `Pointer Capture` su Android, che è già coperto (`DECISIONI.md` §5-bis.8) | quando si presenta un'applicazione che lo chiede |
| **il tocco multi-dito** | `input.tocco` esiste e vale `no`. Un posto riservato costa niente; una definizione mai esercitata costa un vincolo | fase A4, se il tocco nativo servirà davvero |
| **il 4:4:4** | è una capacità in più (`video.sottocampionamento`), e la decisione di prodotto è `[?]` (`DECISIONI.md` §2.3) | quando l'utente avrà guardato le due immagini |
| **più schermi** | la tela è una sola. La forma del multi-monitor è «due viste sulla stessa tela», che il protocollo già regge per la tela; mancherebbe solo dire **dove** sta ciascuna vista | mai, finché resta fuori scope |
| `[?]` **la registrazione IANA della porta** | §2.4 | se e quando servirà un numero registrato |
| ~~la funzione di banco dell'anello del ritardo~~ | ⭐ **chiusa la notte del 9 agosto 2026, poche ore dopo essere stata aperta** dal rilievo **R3.4**: è **§7.5**, due tipi nuovi — `BANCO_MARCA` e `BANCO_ESITO` | ⭐ *È entrata sotto la clausola di §9 — «oggi non esiste nessuna implementazione» — e **quella era l'ultima occasione**: dal primo byte di codice in poi sarebbe stata una deroga, cioè il primo strappo fatto da noi a una regola nostra* |

⛔ **E una cosa che non è aperta e va detta perché non venga riaperta per distrazione**: il
**battito applicativo** non manca, è **vietato** (§2.2). Chi lo trova assente e pensa di aggiungerlo
sta per creare due verità sullo stesso fatto.
