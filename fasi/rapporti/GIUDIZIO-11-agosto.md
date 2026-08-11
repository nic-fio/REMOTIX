# Il giro dell'utente dell'11 agosto 2026 — la prova su disco

*⛔ Questo file esiste perché la misura che chiude la fase 1 è **un giudizio**, e un giudizio senza
provenienza è un ricordo. Qui c'è la scena, il registro verbatim e le impronte. La frase
dell'utente sta in [`../01-filo-nudo.md`](../01-filo-nudo.md), §«Il giudizio dell'utente».*

## La scena

| | |
|---|---|
| **chi guarda** | l'utente, dal portatile **CHUWI — 192.168.0.3** |
| **che cosa apre** | `https://192.168.0.2:7448` in **Chrome** ⚠ *(la versione esatta non è annotata — regola **B0.6** mancata: il verdetto è di un browser, e fra sei mesi «Chrome» non è un dato)* |
| **il bersaglio** | ⭐ **il PRODOTTO** — `src/`, sulla porta **7448**, non l'innesto della 7447. Processo acceso alle 08:28, binario `53c4631…` |
| **quando** | ⭐ `[M]` **2026-08-11**, `GET /` alle **12:45:44 UTC**, la stretta di mano alle **12:48:55-12:48:56 UTC** |
| **il registro** | `/srv/src/remotix-browser.log` dentro il contenitore del server (fuori: `/media/REMOTIX/devroot/srv/src/`), copiato qui sotto verbatim |
| **le due schermate** | `~/Immagini/Screenshots/Screenshot From 2026-08-11 14-45-56.png` (`b232fb5e…`) e `…14-49-03.png` (`23ad59a6…`), ora locale CEST = UTC+2. ⚠ **Stanno fuori dall'albero**: se servono domani, vanno portate dentro |

## ⭐ Che cosa chiude, e sono le due cose che il `README.md` dichiarava non misurate

| quel che il documento diceva al mattino | quel che dice questo registro |
|---|---|
| ⛔ *«`GET /` compare **ZERO** volte … la pagina non l'ha servita il prodotto»* — il **secondo mestiere** del server della fase 1, non misurato da nessuna parte | `12:45:44.420 pagina GET / da 192.168.0.3` ⇒ ⭐ **la pagina l'ha servita il prodotto**, e il modulo che l'utente ha compilato è quello |
| ⛔ *«tutte e 19 le connessioni vengono da `[192.168.0.2]`, cioè **dal server stesso**: il giro non ha attraversato la rete»* | ogni riga porta `192.168.0.3` ⇒ ⭐ **il giro ha attraversato la rete davvero** |
| ⛔ *«di **Chrome** contro questo server non c'è nessuna traccia»* | ⭐ c'è, ed è questa |

⚠ **E quel che questo giro NON è**: un banco. Non ha un atteso confrontato da una macchina (**B0.4**),
non ha un controllo che dica *no*, e non è rieseguibile senza una persona. È **I8** — il giudizio —
e vale per quello che è: la sola prova che un essere umano ha visto la cosa funzionare.

## ⛔ E ha trovato due divergenze fra i documenti e il prodotto

**1 — «desktop GNOME» non è quel che il prodotto dice, ed è il PRODOTTO ad avere ragione.**
`fasi/01-filo-nudo.md` §«Che cosa deve produrre» scrive l'atteso visibile così: *«la pagina dice
“ammesso, sessione nuova, tela 1920×1080, **desktop GNOME**”»*. La pagina ha detto **«desktop
sconosciuto»**. ⭐ Ed è onesto: `src/rcp.c` lo dichiara per iscritto — *«in fase 1 non c'è nessun
compositore (`SESSIONE` dichiara `desktop=sconosciuto`), quindi non c'è nessuno a cui chiedere»*.
La sessione grafica nasce alla **fase 2**. ⇒ ⛔ **A cambiare è la riga dell'atteso**, non il codice:
era stata scritta prima che il prodotto esistesse, e prometteva una parola che la fase 1 non può
dire senza inventarla.

**2 — il server dichiara `video.codec=hevc,av1`, il documento di fase gli fa dichiarare `hevc`.**
Il riquadro §«le capacità che il server dichiara in `ECCOMI`» elenca **`video.codec=hevc`**; il
prodotto manda `hevc,av1` (`src/rcp.c`, `#define NOSTRO_CODEC "hevc,av1"`; `src/pagina.html` idem).
⭐ `RCP.md` §4.3 ammette l'elenco (*«fra `hevc`, `av1`, in ordine di preferenza»*), quindi **non è una
violazione**. ⛔ Ma §4.3 rende le capacità **normative**, e quel riquadro dice di sé: *«è una
dichiarazione d'intenti, ed è onesta solo se qualcuno la verifica»*. ⇒ **Le promesse da verificare
alla fase 2 diventano due**, non una. Da riportare accanto alla riga, o alla fase 3 si scoprirà di
aver promesso un codificatore in più.

## ⭐ E tre cose che il registro conferma di passaggio

- `il client dichiara video.misura_massima=1920x1080: è il tetto che la tela concessa DEVE rispettare (§4.5)` — la tela concessa è **capata**, come impone la correzione R4.2, e non è «quella chiesta».
- `vista=1920x927` — ⭐ una vista **dispari nell'altezza**, accettata: è il caso **R4.10** vivo, quello in cui una `valida_misura()` sola chiuderebbe la sessione perché l'utente ha stretto la finestra.
- `accesso riuscito da [192.168.0.3]: il conto dei falliti torna a zero (erano 2) — §4.4-bis` — ⭐ **l'azzeramento di B8 osservato fuori da B8**, su due fallimenti veri delle 08:35.
- `il secondo fisso è passato (1080 ms)` — §4.4-bis rispettato **anche sull'ammesso**.
- `STACCATO per silenzio: 30034 ms … (posti occupati adesso: 0)` — ⚠ a liberare il posto è stato **l'orologio**, non un congedo: la scheda è stata lasciata aperta e la pagina non si è congedata. È lo stesso `⚠` del giro del 10 agosto.

## Il registro, verbatim

⚠ *Le ultime tre righe (`12:50:21`, da `192.168.0.2`) **non sono dell'utente**: sono un controllo di
uno degli agenti al lavoro quella sera. Restano qui perché tagliarle sarebbe scegliere che cosa il
registro dice.*

```
12:45:44.420 pagina  GET / da 192.168.0.3:46602
12:45:44.867 pagina  GET /favicon.ico da 192.168.0.3:46610
12:48:55.277 pagina  GET /impronta da 192.168.0.3:51836
12:48:55.293 quic    connessione nuova da [192.168.0.3]:41793 (in tutto 1)
12:48:55.295 wt      ⭐ SETTINGS riscritto — 22 byte di nghttp3 + 14 nostri (ENABLE_WEBTRANSPORT e WT_MAX_SESSIONS)
12:48:55.302 wt      ⭐ sessione WebTransport APERTA su /rcp/1 (stream 0) — il canale di controllo va aperto entro 5000 ms (§4.6, DECISIONI.md §7.17)
12:48:55.313 rcp     canale di controllo aperto da [192.168.0.3]:41793 (indirizzo per §4.4-bis: [192.168.0.3])
12:48:55.313 rcp     canale di controllo = stream 4
12:48:55.313 wt      stream 4 e' WebTransport, sessione 0
12:48:55.316 rcp     il client dichiara video.misura_massima=1920x1080: e' il tetto che la tela concessa DEVE rispettare (§4.5)
12:48:55.316 rcp     negoziato video.codec=hevc video.profondita=8 audio.codec=opus
12:48:55.316 wt      ⭐ PING del trasporto ACCESI ogni 10 s con [192.168.0.3]:41793: §4.6 da' 60 s per digitare la parola d'ordine e l'inattivita' di QUIC ne da' 30
12:48:55.319 rcp     CREDENZIALI ricevute utente=prova (con parola)
12:48:55.369 rcp     PAM ha risposto: ammesso
12:48:55.369 rcp     accesso riuscito da [192.168.0.3]: il conto dei falliti torna a zero (erano 2) — §4.4-bis
12:48:55.369 wt      PING del trasporto spenti con [192.168.0.3]:41793: la finestra delle credenziali e' chiusa, e i 30 s di §2.2 tornano a essere l'orologio del silenzio
12:48:56.399 rcp     il secondo fisso e' passato (1080 ms)
12:48:56.399 rcp     ammesso utente=prova da=[192.168.0.3]:41793
12:48:56.403 rcp     posto PRESO da prova via [192.168.0.3]:41793 (occupati adesso: 1)
12:48:56.403 rcp     sessione aperta utente=prova via=[192.168.0.3]:41793 tela=1920x1080 vista=1920x927 disposizione=it
12:49:26.437 rcp     STACCATO per silenzio: 30034 ms senza un byte da [192.168.0.3]:41793 (posti occupati adesso: 0; stato: staccata-per-silenzio)
12:50:21.853 pagina  GET / da 192.168.0.2:58262
12:50:21.877 pagina  GET /impronta da 192.168.0.2:58272
12:50:21.893 pagina  HEAD / da 192.168.0.2:58284
```

## Quel che la pagina ha mostrato, verbatim

```
Ammesso, sessione nuova, tela 1920×1080, desktop sconosciuto

apro https://192.168.0.2:7448/rcp/1
sessione WebTransport aperta
CIAO mandato (8 capacita')
ECCOMI: versione 1 — video.codec=hevc,av1 · video.profondita=8,10 ·
audio.codec=opus,pcm · appunti.testo=si · banco.marca=no
CREDENZIALI mandate (la parola non compare in nessun registro)
AMMESSO
ATTACCA: tela 1920×1080, vista 1920×927, disposizione «it»
```

⚠ *`banco.marca=no` è la funzione di banco di `RCP.md` §7.5 a **funzione spenta**, cioè lo stato
predefinito che **B5** prova. ⭐ E la riga «la parola non compare in nessun registro» è
un'**affermazione della pagina su sé stessa**: è il soggetto di **B13**, non la sua prova.*
