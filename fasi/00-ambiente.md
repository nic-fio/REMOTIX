# Fase 0 — L'ambiente e i banchi

Aperta il **9 agosto 2026** · **Chiusa il 9 agosto 2026**

> Prima fase di REMOTIX_V2, e l'unica che non produce prodotto. Il modello di questo documento sta
> in [`../PIANO.md`](../PIANO.md) §0.2; le decisioni stanno in
> [`../DECISIONI.md`](../DECISIONI.md) e qui si **rimanda**, non si copia.

---

## Che cosa deve produrre

La macchina che compila e prova, i banchi di v1 rimessi in funzione, e l'ambiente Android che la
sonda della fase 2 richiederà.

**Che cosa vede e giudica l'utente**: i numeri di v1 **riprodotti** — la cattura di Mutter che
consegna ~37 fotogrammi al secondo, quella di KWin ~60.

⭐ **Non è un risultato di prodotto: è il controllo positivo di tutto il progetto.** Se il banco non
sa riprodurre un numero che sappiamo vero, ogni misura delle tredici fasi successive è sospetta —
e non lo sarebbe *un po'*: lo sarebbe esattamente quanto lo erano le misure di ritmo delle fasi 3-9
di v1, che sono state buttate tutte (`LEZIONI.md` §1.1).

---

## Il banco

⛔ *Scritto prima di sviluppare, e revisionato per primo — `PIANO.md` §0.4, momento 1.*

### B1. Che cosa si misura, e con che scena

| | |
|---|---|
| **lo strumento** | `v1/banchi/banco-compositori/misura-cattura` — consumatore PipeWire che conta i fotogrammi e dice tipo di buffer, danno, buffer riciclati, se il disegno era finito, e la distribuzione degli intervalli. Sa montare da sé lo schermo virtuale di Mutter |
| **la scena** | ⛔ **dichiarata, e in movimento a ogni ridisegno**: a schermo intero, opaca, che ridisegna a ogni *frame callback* del compositore. Non una scena ferma, non una mossa a colpi di tastiera (`LEZIONI.md` §1.1). ⚠ *Qui era nominato `weston-simple-egl -f -o`: `[M]` **il 13 agosto 2026 non è installato**, e dalla fase 3 la scena è la nostra — `banchi/03-scena.c`, che porta una marca e **conta le proprie attese***. ⛔ **E c'è un terzo requisito, imparato in fase 3**: la scena deve stare **sul monitor che si sta catturando** |
| **il controllo che dice di chi è il tetto** | ⛔ **quanto disegna il client**, contato accanto a quanto consegna la cattura. Senza, un tetto della scena viene attribuito al compositore — e viceversa |
| **la durata** | ⚠ **almeno 300 fotogrammi, e si scartano i primi**: i primi dieci sono l'avvio, quando tutto viene ridipinto, e su di essi il rapporto si ribalta (`LEZIONI.md` §1.4) |

### B2. Come questo banco si certifica, prima di essere creduto

⛔ La domanda non è «funziona?», è **«saprebbe accorgersi che non funziona?»**. Quattro prove, e
nessuna costa più di un minuto:

| # | La prova | Che cosa dimostra |
|---|---|---|
| **C1** | si punta lo strumento su **KWin `--virtual`**, dove il numero atteso è 59-60 `[M]` 8 ago | è il controllo positivo vero e proprio: *lo strumento sa trovare qualcosa che c'è di sicuro?* (`LEZIONI.md` §1.9 regola 2) |
| **C2** | si **spegne la scena** e si rimisura | ⛔ il numero **deve crollare**. Se resta ~37 con la scena ferma, il banco non sta misurando la cattura ma qualcos'altro, e ogni fase successiva erediterebbe la bugia |
| **C3** | si punta lo strumento su un nodo **che non esiste** | ⛔ deve dire **«sono fallito»**, non «zero fotogrammi». «Vuoto» e «proibito» hanno lo stesso aspetto, ed è la lezione che è costata una riga sbagliata in un documento di riferimento (`LEZIONI.md` §1.9) |
| **C4** | si esegue il banco **due volte di fila**, senza rimettere la macchina | uno che passa solo da macchina pulita non è un banco, è una dimostrazione (`LEZIONI.md` §2.3-ter) |

### B3. ⛔ I tre difetti di banco già pagati, che qui si controllano nel codice

Sono tre righe, e in un pomeriggio dell'8 agosto hanno prodotto tre falsi rossi — **nessuno dei
tre nel prodotto** (`LEZIONI.md` §2.3-bis):

1. **`pgrep -x weston-simple-egl` non trova mai niente**: `comm` è troncato a **15 caratteri** e
   quel nome ne ha **17**. Si usa `pgrep -f`. ⚠ Il sintomo è «la scena non è partita» mentre la
   cattura consegna 58 fotogrammi al secondo;
2. **un'opzione rifiutata non è un difetto del bersaglio**: un client che stampa la pagina d'aiuto
   ed esce fa leggere al banco «zero fotogrammi» e dare la colpa al server. Le righe di comando si
   **copiano da un banco che funziona**, non si ricordano;
3. ⛔ **mai `sudo` dentro un comando di cui si redirige lo stderr**: la richiesta di password va
   sullo stderr, e il banco resta **appeso per sempre, in silenzio**. Non è «ricordarsela»:
   è non scriverla.

### B4. La certificazione dell'ambiente, che qui vale quanto quella del banco

Questa fase misura una macchina, non un prodotto — quindi l'ambiente **è** l'incognita, e va
accertato con la stessa severità:

| | Perché non si dà per scontato |
|---|---|
| ⛔ **l'utente è nei gruppi `render` e `video`** | senza, la Shell non apre `/dev/dri` e **Mutter ripiega sul rendering in software senza un errore da nessuna parte** `[M]` 6 ago. I 37 fotogrammi misurati così sarebbero un numero diverso sotto la stessa etichetta — la forma d'errore **E2** |
| ⛔ **e il gestore `systemd --user` è stato riavviato dopo** | i gruppi supplementari di un processo già vivo **non cambiano**: aggiungere l'utente al gruppo senza riavviare il gestore lascia tutto com'era, e sembra fatto |
| **su quale scheda disegna il compositore** | la macchina ha **due** GPU (Intel `0000:00:02.0`, Radeon `0000:03:00.0`), e un buffer della scheda sbagliata non è importabile: il sintomo è composizione in software **senza un errore** (`LEZIONI.md` §4 trappola 6) |
| **il rootfs vive in RAM e si azzera al riavvio** | ⚠ quindi «la macchina è a posto» è vero **per questa accensione**. Il ripristino si prova **riavviando**, non rileggendo lo script (`LEZIONI.md` §2.5-bis) |

---

## Che cosa è stato sviluppato

Nessun codice di prodotto: questa fase rimette in funzione quel che esiste già — più due cose
nuove, che sono banco.

| | |
|---|---|
| `v1/banco/provision-server.sh` | il ripristino della macchina, rieseguito il 9 agosto: GNOME 48.7, `vainfo`, `libei1`, e l'utente nei gruppi `render`/`video` |
| ⭐ `v1/banco/provision.sh`, passo **5-bis** | **gli utenti di prova dell'autenticazione, dichiarati l'11 agosto 2026** — vedi il riquadro qui sotto |
| `v1/banchi/banco-compositori/` | portato sul ferro in `/media/REMOTIX/tmp/`, ricompilato nel `devroot` |
| ⭐ `banchi/00-sessione-gnome.sh` | **nuovo**: avvia una sessione GNOME senza monitor con l'ambiente composto da zero, e **verifica** che sia headless invece di sperarlo (`DECISIONI.md` §4.3-bis) |
| ⭐ `banchi/00-c1-wlroots.sh` | **nuovo**: la certificazione di `misura-wlroots`, il terzo banco, su sway e labwc |
| ⭐ `banchi/00-c1-kwin.sh` | **nuovo**: la certificazione C1 — lo stesso strumento su KWin, con l'atteso di `kde.md` §5.7 stampato prima della misura |
| ⭐ `banchi/00-rimetti-macchina.sh` | **nuovo**: rimette in piedi la macchina partendo da **prima del disco**, che è il passo che nessuno script conteneva |
| ⭐ `v1/banchi/banco-compositori/misura-cattura.c` | **corretto**: ora distingue lo zero dal fallimento |
| ⭐ `v1/banchi/banco-compositori/banco.sh` | **corretto** due volte: `stdbuf -oL` sulla scena, e la verifica che la scena sia viva prima di credere al numero |
| ⭐ `v1/banchi/banco-compositori/provision-banco.sh` | **corretto**: prende le credenziali con `sudo -v -S -p`, come l'altro script di ripristino |

⚠ La sessione si avvia con `gnome-session --session=gnome` e l'ambiente di `sessione.c`; il
congedo è **`Logout(2)`**, non `systemctl --user stop`.

---

## Le misure

*(Riempito strada facendo. La scena dichiarata accanto a ogni numero.)*

### Lo stato della macchina, **prima** di toccarla

| Che cosa | Misurato | Data |
|---|---|---|
| GNOME installato sul server | ⛔ **no** (`dpkg-query` → not-installed) — conferma `gnome.md` §2 | 9 ago |
| `vainfo` installato | ⛔ **no** | 9 ago |
| `nicfio` nei gruppi `render`/`video` | ⛔ **no** (`nicfio sudo`) | 9 ago |
| `/media` montata, `/etc/fstab` | montata; ⚠ **fstab vuoto**, come `LEZIONI.md` §2.5-bis | 9 ago |
| cache apt su `/media` | ✅ 1450 `.deb`, 1,1 G — la reinstallazione non scarica quasi nulla | 9 ago |
| GPU visibili | ✅ Intel `00:02.0` → `renderD128`, Radeon `03:00.0` → `renderD129` | 9 ago |
| rootfs | ⚠ **32 G in RAM**, si azzera al riavvio | 9 ago |

### Dopo il ripristino (`provision-server.sh`, uscita 0)

| Che cosa | Atteso | Misurato | Data |
|---|---|---|---|
| Mutter / gnome-shell | 48.7 (Trixie) | ✅ **48.7**, `gnome-session` 48.0 — le versioni che `gnome.md` ha studiato | 9 ago |
| `nicfio` nei gruppi | `render`, `video` | ✅ `nicfio sudo video render` | 9 ago |
| `libei1` | presente | ✅ 1.3.901 | 9 ago |
| `weston-simple-egl` per la scena | presente | ⛔ **ASSENTE il 13 agosto 2026** — `[M]`. Era ✅ `/usr/bin/weston-simple-egl` il 9 ago, ed è sparito: **il rootfs sta in RAM** e la macchina che si rimette da sé non si rimette *completa* (`LEZIONI.md` §2.5-bis). ⇒ La scena della fase 3 è **la nostra** (`banchi/03-scena.c`), e non dipende da un pacchetto | 9 ago → **13 ago** |

### `vainfo` — la `[?]` del budget del codificatore, chiusa

⛔ *Verificato con lo stato d'uscita, non solo con l'elenco: `USCITA=0` su tutt'e due i nodi. Un
elenco vuoto e un driver che non si apre hanno lo stesso aspetto (`LEZIONI.md` §1.9).*

| | Intel UHD 730 (iHD 25.2.3) | Radeon RX 6800 (radeonsi) |
|---|---|---|
| **HEVC Main10 in codifica** | ✅ `EncSliceLP` | ✅ `EncSlice` |
| HEVC **4:4:4**, 8 e 10 bit, in codifica | ⭐ ✅ **sì** | ⛔ no |
| H.264 · VP9 · JPEG in codifica | sì | H.264 sì |
| **AV1** | ⛔ **nessun profilo, nemmeno in decodifica** | solo decodifica |

**Le tre conseguenze, tutte scritte dove vanno e non solo qui:**

1. il desiderato a 10 bit ha la sua strada in hardware su entrambe (`DECISIONI.md` §4.6);
2. ⭐ il **4:4:4** era `[?]` con accanto «Intel a volte»: sul nostro ferro è **sì**, anche a 10 bit
   — non riapre la decisione, che era stata presa per il lato Android, ma la rende misurabile
   senza comprare niente (`DECISIONI.md` §2.3);
3. ⛔ `SPECIFICHE.md` §11.4 diceva «RDNA2 e Alder Lake lo decodificano soltanto»: **falso per
   l'Intel**, che AV1 non lo tocca affatto. Corretto lo stesso giorno.

⚠ E una riga che vale per la fase 8: sull'Intel l'unico ingresso di codifica è **`EncSliceLP`**,
il percorso *low power*. Non è un ripiego — è il solo che quel chip espone — ma ha opzioni di
controllo del bitrate proprie, ed è il punto esatto in cui v1 si è fatto male due volte.

### ⭐ Il controllo positivo del progetto — riprodotto

**Scena dichiarata**: `weston-simple-egl -f -o`, schermo intero, opaco, un commit per ogni
ridisegno del compositore. Monitor virtuale 1920×1080 montato dal banco via `RecordVirtual`,
20 secondi di misura, 7 di scarto. GNOME 48.7 headless, DMA-BUF, BGRx, 60 dichiarati.

> ⛔ *13 agosto 2026, e va letto prima di rifare questa misura: **la scena qui nominata non è più
> disponibile** (`weston-simple-egl` non è installato), e **il numero che questo controllo positivo
> riproduceva — i ~37 di Mutter — non si riproduce**. Non è un difetto del banco: alla cadenza che
> gli si chiedeva Mutter consegna **31,5**, e rinegoziando la sola cadenza (monitor 120, freno 90)
> ne consegna `[M]` **61,4**. ⚠ Che il 37 fosse il resto di una **divisione troncata** è la
> spiegazione più probabile, ed è `[R]` — letta nel codice di Mutter, **non misurata**
> (`gnome.md` §8.2; la «legge su 13 punti» che si leggeva qui il 13 agosto **è caduta la sera
> stessa**).*
> ⇒ **Il controllo positivo del progetto va rifatto contro le celle pulite di
> `banchi/03-b14-esiti.jsonl`, non contro il numero**, e con la scena della fase 3 — che **conta le
> proprie attese** e dichiara se ha corso a vuoto.

| Che cosa | Atteso | Misurato | Esito | Data |
|---|---|---|---|---|
| **Mutter, scena in movimento** | **~37 fps** `[M]` v1 | ⭐ **36,2 in media su sei giri** — 37,82 · 37,33 · 33,66 · 36,67 · 36,39 · 35,42 | ✅ | 9 ago |
| ⭐ **quanto disegna il CLIENT** | ≥ il consegnato | **60,0** in ogni giro ⇒ **il tetto è del compositore, non della scena** | ✅ | 9 ago |
| C2 — la stessa scena **ferma** | crolla | **0,00**, con flusso attivo e formato negoziato | ✅ | 9 ago |
| C4 — giri ripetuti senza rimettere niente | uguali | sei giri, dispersione **33,7-37,8** | ✅ | 9 ago |
| C3 — nodo inesistente | «fallito», non «zero» | ⛔ **dava 0,00 e uscita 0** → corretto, ora `GUASTO` e uscita 2 | ✅ dopo cura | 9 ago |
| **C1 — lo stesso strumento su KWin** | **59,2** `[M]` `kde.md` §5.7 | ⭐ **58,92** (1180 fotogrammi, mediana 17,0 ms) | ✅ | 9 ago |
| C1-bis — KWin **in memoria** | 43,3 `[M]` 8 ago | ⚠ **49,67** — più alto dell'atteso, vedi sotto | ⚠ | 9 ago |

⭐ **C1 è la certificazione che vale più di tutte, e non era «un altro numero»**: dice che lo
strumento sa dare un numero **diverso** quando la cosa misurata è diversa. Puntato su KWin dà
58,92 con mediana 17,0 ms; puntato su Mutter dà 36 con mediana 33,3. Se avesse risposto ~37 anche
su KWin, staremmo misurando lo strumento e non i compositori.

⚠ **La dispersione di Mutter va detta, non nascosta**: sei giri fra 33,7 e 37,8, con la **mediana
degli intervalli ferma a 33,3 ms in tutti e sei**. Il battito è stabilissimo; a muoversi è la coda
(intervalli massimi da 33,6 a 75,0 ms). Quindi «~37» di v1 è riprodotto, ma il numero onesto da
citare è **36 ± 2**, non 37,8.

⚠ **E il 49,67 in memoria non torna con il 43,3 dell'8 agosto.** Non lo spiego: lo dichiaro. Le
differenze note fra le due misure sono tre — 20 secondi per cella invece di 10, `KWIN_COMPOSE=O2`
non impostata (che `LEZIONI.md` §1.11 dà comunque per **inerte**, misurato), e la Radeon oggi
**presente ma non apribile** invece che negata. `[?]` Nessuna delle tre è stata verificata come
causa. Non tocca la certificazione, che passa sulla colonna a copia zero.

⭐ **E la distribuzione degli intervalli dice più del solo numero**: `min 16,2 · mediana 33,3 ·
p95 33,5`. I fotogrammi arrivano a **uno o due periodi di quadro**, mai a metà — cioè due orologi
a 60 che battono fra loro, che è esattamente il meccanismo che `gnome.md` §8.2 legge nel codice
(`maxFramerate` fa da freno alla cattura **e** da frequenza al monitor virtuale). ⚠ **Non è la
prova della cura**: è la prova che la spiegazione è compatibile con quel che si vede. La cura
resta l'esperimento M3 della fase 3.

⚠ **Altre due cose lette nello stesso giro**, e vanno tenute perché toccano decisioni già scritte:

| | |
|---|---|
| `disegno non finito` su **tutti** i fotogrammi contati | conferma la domanda 9: a copia zero il **100 %** arriva col disegno in corso. ⚠ *Riscritto il 9 agosto dopo la revisione: questa riga diceva «944 su 757», che è un rapporto fra due popolazioni diverse — il 944 era sugli arrivati, non sui contati. La conclusione regge (944 su 944), la frase no. Rimisurato col banco corretto: **749 su 749**, e ora le due colonne condividono il denominatore* |
| `danno: pieno 15, parziale 929` | il danno **parziale è la regola**, il pieno l'eccezione — come `LEZIONI.md` §1.4 (282 su 300) |
| `Boot VGA GPU /dev/dri/renderD128 selected as primary` | ⭐ **Mutter sceglie l'Intel da sé**, per «Boot VGA» — non come KWin, che prende la prima che riesce ad aprire. Vedi `DECISIONI.md` §4.6-ter |
| `amdgpu: amdgpu_cs_ctx_create2 failed. (-13)` | la Radeon è vista ma non usabile (permesso negato): `[?]` da capire se è la regola udev o altro. **Non ci ostacola**: il primario è quello giusto |

### ⭐ La prova che conta più di tutte: dopo un riavvio VERO

*La macchina è stata riavviata alle **10:16 del 9 agosto 2026**, su richiesta dell'utente, e
rimessa in piedi da zero. `LEZIONI.md` §2.5-bis: «un ripristino si prova riavviando, non
rileggendo lo script».*

| Che cosa | Misurato | Data |
|---|---|---|
| passi **manuali** necessari prima che il ripristino esistesse come file | ⛔ **uno**: montare `/media` | 9 ago |
| script di ripristino da eseguire | ⚠ **due**, e il primo non nomina il secondo | 9 ago |
| difetti che il riavvio ha fatto emergere | **quattro** (voci 6, 7, 8 e 9 qui sotto) | 9 ago |
| **Mutter, dopo il riavvio e il ripristino** | ⭐ **36,78 · 36,33 · 37,05** — mediana 33,3 ms, client a 60,0 | 9 ago |

⭐ **I numeri di prima del riavvio erano 33,7-37,8; quelli di dopo 36,3-37,1.** La macchina rimessa
in piedi da zero **riproduce quel che riproduceva prima** — ed è questa, non la misura di stamattina,
la frase che autorizza a credere alle misure delle tredici fasi che seguono.

### ⭐ Le tre famiglie di compositori, tutte con un numero riprodotto

*Stessa scena, stessa macchina, stesso pomeriggio — che è l'unico modo in cui tre numeri si
possono mettere accanto.*

| Compositore | Modello | Atteso | Misurato | Mediana intervalli | Client |
|---|---|---|---|---|---|
| **Mutter** (GNOME) | spinge, PipeWire | ~37 `[M]` v1 | **36,3-37,1** | 33,3 ms | 60,0 |
| **KWin** (KDE), copia zero | spinge, PipeWire | 59,2 `[M]` 8 ago | **58,92** | 17,0 ms | 60,0 |
| **sway** (wlroots), 1080p | ⭐ **fa tirare**, `wlr-screencopy` | ~61 `[M]` v1 | **61,02** | 16,4 ms | 61,2 |
| **labwc** (wlroots), 720p | fa tirare | ~61 | **61,16** | 16,4 ms | 61,2 |

⭐ **E i tre banchi sono tre programmi diversi, ora tutti certificati**: `misura-cattura` (PipeWire),
`nodo-kwin` (il protocollo di KDE, usato dentro C1) e `misura-wlroots` (`wlr-screencopy`).
Quest'ultimo era stato ricompilato **e mai puntato su niente** — cioè non certificato — fino a
questo giro.

⭐ **La riga di sway vale doppio**, perché il modello è l'opposto: Mutter e KWin **spingono** i
fotogrammi, wlroots li fa **tirare**, una richiesta per fotogramma. Che lo stesso metodo dia un
numero coerente su due modelli opposti non era scontato: è un'informazione, non una conferma.

### Quel che resta fuori da questa fase, per scelta

| Che cosa | Perché non qui |
|---|---|
| le **tabelle per risoluzione** (720p → 4K) di Mutter e KWin | esistono già `[M]` in `kde.md` §5.7 e in `LEZIONI.md` §3. Rifarle adesso sarebbe misurare prima di avere la domanda: servono alla fase 8 (l'accelerazione) e alla 10 (KDE) |
| le scene `video` e `carico` | idem: rispondono a domande delle fasi 3 e 9 |
| `adb`, Desktop AVD, il telefono vero | l'ambiente Android serve alla **sonda della fase 2**, e l'utente ha chiesto di lasciarlo stare per ora. ⚠ *Riletto il 9 agosto sera: `adb` e l'AVD **non servono più affatto** (non c'è più un'applicazione Android), e **il telefono vero serve alla fase 1**. Vedi la voce corretta in «Che cosa resta `[?]`»* |

---

## ⛔ Che cosa NON ha funzionato

⭐ **Cinque difetti in un pomeriggio, e nessuno era del compositore: quattro erano del banco e uno
del provisioning.** È la fase 0 che fa il suo mestiere — se questi fossero comparsi alla fase 3,
avrebbero avuto l'aspetto di difetti di Mutter.

### 1. ⛔ Il misuratore non distingueva lo zero dal fallimento — ed era lo strumento che certifica tutti gli altri

Puntato su un nodo che non esiste, `misura-cattura` rispondeva **«fotogrammi 0 → 0,00 al secondo»
con uscita 0**: identico a una scena ferma, che è un risultato legittimo. Due cose opposte sotto
la stessa faccia (`LEZIONI.md` §1.9; è la domanda 4 di `REVIEWER.md` §1).

**La cura**: il discrimine è se il flusso sia mai diventato **attivo**. Ora stampa `GUASTO`,
non una `RIGA`, ed esce con 2. ⭐ E in dote arriva la ragione, che PipeWire dava già e che
buttavamo via: *«no target node available»*.

⚠ **Il prezzo che non abbiamo pagato**: un giro andato storto — un nodo sbagliato, un permesso
negato, il compositore non ancora in piedi — sarebbe entrato in tabella come «il compositore non
consegna niente».

### 2. ⛔ La prova dell'headless cercava una frase che, se tutto va bene, non compare mai

La prima stesura di `00-sessione-gnome.sh` verificava l'headless cercando nel registro di Mutter
*«No seat assigned, running headlessly»*. Letto poi il codice
(`meta-backend-native.c:748-764`): quel messaggio esce **solo** nel percorso **accidentale** —
quando l'headless lo si eredita dalla mancanza di un seat. Chiedendolo con `--headless`, come
fa il nostro drop-in, Mutter esce prima e **non dice niente**.

⛔ Su una sessione perfettamente sana la prova avrebbe dato **rosso per sempre**. È `LEZIONI.md`
§1.11: per ogni prova indiretta va scritto che aspetto avrebbe il caso opposto, o la prova non
distingue. Ora il banco riconosce **tutti e due** i modi, e dice quale dei due è.

### 3. ⛔ «Nessuna riga trovata» era una lettura negata

Il primo tentativo di leggere quel che Mutter dice usava `journalctl --user`, che ha risposto con
zero righe. Non perché Mutter tacesse: **il comando non aveva potuto aprire niente** — prima per
permessi (`insufficient permissions`), poi perché su questa macchina il journal **non esiste
affatto**, il rootfs vivendo in RAM.

⭐ La cura non chiede root: l'unità della Shell è **d'utente**, quindi un drop-in in
`~/.config/systemd/user` manda la sua uscita in un file nostro.

⚠ **E la conseguenza va oltre questa fase**: `LEZIONI.md` §1.10 dice *«accendi il registro del
componente che nega»*. Su questa macchina quel registro **non c'è di suo**, e ogni fase che vorrà
farsi dire qualcosa da un componente dovrà procurarsene il canale.

### 4. ⛔ Riavviare la sessione: `pkill` lascia il gestore vivo, e nessuno lo dice

`pkill gnome-session` ha lasciato `gnome-session-manager@gnome.service` **attiva con il
compositore morto**: il riavvio non ha fatto niente, e il banco ha aspettato quaranta secondi
senza una riga che spiegasse perché. È `LEZIONI.md` §2.3-ter — su Plasma dava «Could not start
Plasma session», qui **non dà nessun errore**.

⛔ **E la prima cura era sbagliata a sua volta**: aspettare che `is-active` fosse *diverso da
`active`* si sblocca dopo mezzo secondo, perché passa da **`deactivating`** — cioè si riparte
dentro l'intervallo di smontaggio, che è il difetto che la guardia doveva togliere. Si aspetta
`inactive`. E il congedo giusto è **`Logout(2)`** (`gnome.md` §3.2): `systemctl --user stop` non
ferma il gestore, e `Logout(1)` mostrerebbe un dialogo che in una sessione non presidiata non
vede nessuno.

### 5. ⚠ Il provisioning non dichiarava una dipendenza dei banchi

Per leggere il journal servono i gruppi `adm`/`systemd-journal`, che `provision-server.sh` non
concede. È la stessa forma di `LEZIONI.md` §2.5-bis — *«i banchi dipendono da cose che il
provisioning non installa»* — e si è vista al primo riavvio vero. ⚠ Qui è finita in un vicolo
cieco (il journal non c'è comunque), ma la riga va aggiunta lo stesso: **la dipendenza esisteva e
non era dichiarata**.

### 6. ⛔⛔ Il riavvio vero: lo script che rimette in piedi la macchina **sta sul disco che non si monta**

*Provato il 9 agosto 2026 alle 10:16, riavviando davvero il server invece di rileggere lo script —
che è precisamente quel che `LEZIONI.md` §2.5-bis prescrive. L'utente ha chiesto di farlo.*

Trovato subito dopo l'avvio, **senza toccare niente**:

```
/media is not a mountpoint
/etc/fstab: 1 riga, vuota
ls: cannot access '/media/REMOTIX/provision-server.sh': No such file or directory
gnome-shell: unknown ok not-installed
id -nG nicfio: nicfio sudo          ← niente render, niente video
```

⛔ **Il ripristino non era eseguibile.** Non «era incompleto»: **non esisteva come file**, perché
vive su `/media` e `/media` non si monta da sola. Il primo comando dopo ogni riavvio è un
montaggio che nessuno script contiene.

⚠ **E la parte che pesa più del difetto: la lezione era già scritta.** `LEZIONI.md` §2.5-bis lo
dice dal 7 agosto, con queste parole — *«il disco non si monta da solo — `/media` vuota,
`/etc/fstab` senza righe, e i sorgenti stanno lì. Senza quel passo il primo dei tre comandi non
esiste nemmeno come file»*. **La cura non è mai stata applicata**: è rimasta una nota in un
documento. È l'invariante **I7** al contrario — la protezione di un difetto noto non stava in una
riga di configurazione che si può perdere, stava in una **memoria**, che è peggio.

⭐ **La cura, scritta oggi**: `banchi/00-rimetti-macchina.sh`, che parte da **prima** del disco —
monta `/media` per **UUID** (non per nome di nodo, per la stessa ragione per cui la GPU si sceglie
per id PCI) e poi chiama il ripristino dichiarato. Ha anche un verbo `controlla`, che dice che cosa
manca senza toccare niente.

⚠ **E non risolve la radice, e va detto**: anche questo file vive su `/media`. La radice è una riga
in `/etc/fstab`, che il rootfs in RAM riazzera a ogni avvio — quindi va messa da chi costruisce
l'immagine del rootfs, non da noi. `[?]` **Resta aperta**, ed è la vera questione che il riavvio ha
scoperchiato.

### 7. ⛔ E i banchi dipendono da un **secondo** script, che il primo non nomina

Rimessa in piedi la macchina con `provision-server.sh` (uscita 0, oltre 500 pacchetti), la misura
ha dato **`fps=0.00` per tre giri di fila**. Con la cattura attiva quello è uno **zero legittimo**
— «il compositore non ha niente da consegnare» — ed era vero: non c'era **niente da catturare**,
perché mancava il pacchetto `weston` e `weston-simple-egl` non esisteva affatto.

⛔ `weston`, `glmark2-wayland`, `mpv` e `ffmpeg` **non sono in `provision-server.sh`**: stanno in
`provision-banco.sh`, un secondo script che il primo non chiama e non nomina. È la seconda metà
esatta di `LEZIONI.md` §2.5-bis — *«i banchi dipendono da pacchetti che il provisioning non
installa»* — riprodotta alla lettera un giorno dopo essere stata scritta.

### 8. ⛔ Il banco stampava una misura di una scena che non era mai partita

È la terza faccia dello stesso difetto, e la più insidiosa perché le prime due erano già curate:
`misura-cattura` ora distingue «flusso mai attivo» da «zero», ma **«flusso attivo e scena morta»**
produceva ancora una `RIGA` con `0.00`, che in una tabella avrebbe l'aspetto di un compositore
muto. Il registro della scena diceva *«failed to run command 'weston-simple-egl'»*, e nessuno lo
guardava.

**La cura**: `cella` verifica che la scena sia viva prima di credere al numero, e altrimenti
stampa `GUASTO` con dentro il registro della scena.

⛔ **E la prima cura era sbagliata**: `kill -0 $pid` **riesce su uno zombie** — un figlio morto
subito resta nella tabella dei processi finché nessuno lo raccoglie, quindi «il pid esiste» non è
«il processo è vivo». La guardia non scattava. Si legge lo **stato** in `ps`, che dice `Z`.

### 9. ⚠ Due script di ripristino della stessa macchina, due modi diversi di trattare `sudo`

`provision-banco.sh` si è fermato alla prima riga con *«sudo: a terminal is required»*:
`provision-server.sh` prende le credenziali con `sudo -v -S -p` dalla prima riga, questo usa
`sudo` nudo. Chi rimette in piedi la macchina da remoto — cioè sempre — trova il primo che
funziona e il secondo che no.

### 10. ⛔ `kill 0` uccide il proprio gruppo di processi — e il banco spariva senza una riga

Nel banco di C1 la pulizia scriveva `kill ${PID_SCENA:-0}`. Quando la variabile non è ancora
definita — cioè se qualcosa fallisce **prima** di aprire la scena — diventa `kill 0`, che non
vuol dire «non uccidere niente»: vuol dire **uccidi tutto il mio gruppo di processi**, shell
remota compresa. Il banco terminava senza stampare **una sola riga**, e da fuori aveva l'aspetto
di un comando che non parte.

⚠ La forma generale è quella di §1.9 un'altra volta: il modo in cui un banco **fallisce** va
progettato quanto il modo in cui riesce.

### 11. ⛔ Confrontato con la colonna sbagliata, il banco sembrava sbagliare di dieci fotogrammi

Il primo giro di C1 ha misurato KWin **in memoria** (49,67) e l'ha confrontato con i **59-60** di
`kde.md`, che sono la colonna a **copia zero**. Per qualche minuto il banco è sembrato sbagliare;
stava rispondendo giusto a un'altra domanda. La tabella di `kde.md` §5.7 ha due colonne, e a 1080p
dice 59,2 e 43,3.

⭐ **La cura è nel banco, non nella memoria di chi legge**: ora `00-c1-kwin.sh` prende la strada
come argomento e **stampa l'atteso** prima di misurare. Un banco che conosce il proprio atteso non
lascia il confronto a chi guarda.

### 12-bis. ⛔ Un'etichetta che dichiarava una misura che il compositore non aveva mai onorato

Il primo giro su **labwc** ha stampato «1920×1080» su una cattura fatta a **1280×720**: `labwc`
non prende larghezza e altezza sulla riga di comando — il backend headless di wlroots nasce a
720p e lì resta — mentre il banco passava la misura solo come *etichetta*.

⚠ **E il numero era giusto**: 61,16, che a 720p è esattamente l'atteso. Niente sarebbe sembrato
storto. A smascherarlo è stato il fatto che `misura-wlroots` **stampa la misura vera accanto al
numero**, invece di ripetere l'etichetta che gli era stata data — cioè uno strumento che non si
fida di chi lo chiama.

È la forma **E2** applicata al banco: due misure diverse sotto la stessa etichetta. Ora con
`labwc` l'etichetta non dichiara una misura che non abbiamo chiesto, e chi vuole 1080p su wlroots
usa `sway` — dove la misura sta nella configurazione ed è stata onorata (**61,02 a 1920×1080**,
confermato dallo strumento).

### 12. ⚠ Il controllo che dice «di chi è il tetto» era muto per un buffer

Alla cella di Mutter il registro della scena era **vuoto**, e sembrava che il client non avesse
stampato niente. Mancava `stdbuf -oL`: verso un file l'uscita è bufferizzata a blocchi, e alla
chiusura della scena i suoi fotogrammi al secondo restano nel buffer. ⭐ `banco-altri.sh` lo
`stdbuf` ce l'aveva già — la differenza fra i due file era il difetto.

**Con la cura** il controllo di `LEZIONI.md` §1.1 finalmente parla: il client disegna **60,0** in
ogni giro mentre Mutter ne consegna 36. **Il tetto è del compositore.** Senza questo numero,
quella frase sarebbe stata un'ipotesi.

### E un difetto di misura che ho fatto io, mentre misuravo

Due volte in un'ora ho letto `$?` **dopo una pipe**, dove è lo stato dell'ultimo comando e non di
quello che interessava: una volta `COMPILAZIONE=0` mentre `gcc` non esisteva affatto. E una volta
`set -e` più `grep -c`, che esce 1 quando non trova niente, ha fermato uno script di controllo a
metà facendolo sembrare completo. Sono le stesse due forme di `LEZIONI.md` §2.3-bis, e vanno
scritte perché **non sono state pagate dal codice: sono state pagate mentre lo si certificava**.

---

## Le decisioni prodotte

| | |
|---|---|
| `DECISIONI.md` §4.6 | le capacità del codificatore Intel sono `[?]` ricavate dalla generazione del chip: **è qui che si confermano**, con `vainfo` |
| `DECISIONI.md` §4.6-ter | la GPU si sceglie con una regola udev, e negare il nodo lo nega a **tutta la sessione dell'utente** |
| `DECISIONI.md` §5-bis.0-ter | l'emulatore Android è **banco di lavoro, non strumento di misura** |
| `DECISIONI.md` §4.3-bis | essere *headless* su GNOME è un **requisito**, non una fortuna — la verifica è M2, e comincia da qui |

---

## Che cosa resta `[?]`

| | |
|---|---|
| ✅ ~~`/etc/fstab` vuoto~~ → **non è un debito: è un passo dell'utente** | *9 agosto 2026: «quando riavvio la macchina ci penso io alla cartella `/media`».* Il montaggio resta manuale per scelta, e `banchi/00-rimetti-macchina.sh` lo fa in un comando per chi non se lo ricorda. ⭐ **E il rischio vero non era dimenticare il montaggio** — quello si vede subito, perché non c'è niente — **ma misurare su una macchina rimessa a metà**: quello adesso lo prende il banco, che dice `GUASTO` invece di stampare uno zero (voci 1 e 8). La protezione sta nel programma, come vuole **I7** |
| ⚠ **i due script di ripristino** | `provision-server.sh` non chiama né nomina `provision-banco.sh`. Oggi si sa; fra un mese lo saprà solo chi c'era |
| `[?]` **il 49,67 di KWin in memoria** | contro il 43,3 dell'8 agosto. Tre differenze note, nessuna verificata come causa |
| `[?]` **la coda di Mutter** | la mediana degli intervalli è ferma a 33,3 ms su sei giri, ma il massimo va da 33,6 a 75,0. Da dove venga quella coda non è stato guardato |
| `[?]` **la Radeon negata** | `amdgpu_cs_ctx_create2 failed (-13)`: da capire se sia la regola udev di `DECISIONI.md` §4.6-ter. Non ostacola |
| ⏳ **l'ambiente Android** | SDK, `adb`, Desktop AVD e il telefono vero: non ancora toccati. ⛔ *Diceva «servono alla sonda della **fase 2**, non prima». **Corretto la notte del 9 agosto 2026**, rilievo **R3.14** della revisione del banco della fase 1: `DECISIONI.md` §1.6 ha tolto l'applicazione Android — quindi **SDK, `adb` e l'emulatore non servono più a niente** — e `PIANO.md` §1.2 ha spostato la sonda alla **fase 1**, «prima di tutto». **Il telefono vero invece serve, e serve prima**: è lo strumento di misura di S2, S3a e S5. Il censimento completo di quel che manca sta in `fasi/01-filo-nudo.md`, «Le dipendenze»* |
| **il budget in pixel al secondo** | `vainfo` dice **quali** profili, non **quanti** pixel: il numero di sessioni è fase 12 |
| **il decodificatore HEVC dell'emulatore** | non si è riusciti a stabilire che ne esponga uno hardware — e non importa, perché nessun numero si dichiara lì |

---

## La revisione avversariale del banco

*Chiesta dall'utente il 9 agosto 2026, **dopo** la chiusura della fase, e con un mandato stretto:
non la fase — che è chiusa e le cui misure verranno rifatte cento volte — ma i **quattro file del
banco**, che sono l'unica cosa di questa fase che sopravvive alla fase.*

> «La fase 0 è stata una fase in cui si sono misurate le performance. Non sono sicuro che sia
> necessaria una review avversariale.»

⭐ **L'obiezione era per metà giusta, e va scritta.** La revisione avversariale nasce come
sostituto dell'arbitro perduto (`PIANO.md` §0.4): serve ad accorgersi che client e server
condividono lo stesso fraintendimento. Qui non c'è protocollo, non ci sono due implementazioni,
non c'è prodotto — quell'argomento **non vale**. Vale l'altro, che sta in `REVIEWER.md` §1: *il
banco è il primo imputato*, perché un difetto nel banco non lo trova niente **e dà fiducia**.

⛔ **Il conto: 22 rilievi `[R]`, 5 `[?]`, su un banco che era stato appena certificato con quattro
controlli.** E il revisore non ha ricevuto il ragionamento di chi l'aveva scritto — solo il codice
e le regole (`PIANO.md` §0.4, pratica 1).

### Le sette cose corrette subito, e sono quelle che fanno mentire il banco in silenzio

| # | Il difetto | La cura |
|---|---|---|
| 1 | ⛔ **la riga metteva insieme due popolazioni**: danno, fence, salti e buffer contavano dal primo istante, fotogrammi e ritmo dopo lo scarto — e `arrivati` non era stampato, quindi non si poteva vedere | i contatori si aggiornano **dentro** il campione, e `arrivati` è una colonna: la differenza **è** il riscaldamento |
| 2 | ⛔ **morte a metà misura**: il flusso *era stato* attivo, quindi la guardia non scattava. Uccidendo il compositore al dodicesimo secondo uscivano ~59 fps su 5 secondi sotto l'etichetta di una cella da 20 | si guarda lo stato del flusso **alla fine**, non solo all'inizio |
| 3 | ⛔ **`--dmabuf` poteva consegnare memoria**: la maschera dei tipi conteneva sempre anche MemFd, e la colonna diceva la strada **chiesta**. A 1080p sono 59,2 contro 43,3 | si confronta chiesto e ottenuto, e si fallisce dichiarandolo (`LEZIONI.md` §1.8, corollario) |
| 4 | ⛔ **una scena dal nome sbagliato** (`tetti` invece di `tetto`) lasciava `pid_scena` vuoto — la stessa sentinella che la scena `fermo` usa di proposito — e la guardia si disattivava da sé | un ramo di difetto che dice `GUASTO` |
| 5 | ⛔ **la scena era controllata una volta sola**, un secondo dopo l'avvio | si sorveglia per tutta la misura |
| 6 | ⛔ **`00-c1-kwin.sh` non la controllava affatto**, e `misura-wlroots` **ritorna 0 in ogni percorso**: le due certificazioni potevano uscire verdi su un compositore morto | la scena sorvegliata anche lì; e per wlroots il verdetto lo costruisce lo script, ⚠ **dichiarando che è un ripiego** e non una cura nel sorgente |
| 7 | ⛔ **il binario versionato era dell'8 agosto**, senza le cure del 9: chi clonasse il progetto riprenderebbe difetti che questo documento dichiara chiusi | `banco.sh` **si rifiuta di misurare** se il sorgente è più recente del binario — I7: la protezione sta nel programma |

⭐ **E la settima si è dimostrata da sé**: appena scritta, la guardia ha bloccato la prima
esecuzione con *«misura-cattura è più vecchio del suo sorgente»* — cioè ha intercettato in tre
secondi il difetto che al revisore era costato una lettura di `strings`.

### Un `[?]` del revisore chiuso a nostro favore

Sospettava che il **49,67** di KWin in memoria fosse una cattura a 720p etichettata 1080p —
ipotesi acuta, perché 49,6 è esattamente la cella 720p di `kde.md` §5.7. **Smentita da un dato già
registrato**: quella corsa aveva stampato `formato negoziato: 1920x1080`. Il `[?]` sul 49,67 resta
aperto, ma con una causa candidata in meno invece che una in più.

### Che cosa il revisore ha provato a rompere senza riuscirci

Vale quanto i rilievi, e va scritto: la guardia `t_inizio` **tiene** (nessun ingresso le fa
stampare una riga senza flusso attivo); il riconoscimento del socket nuovo di `00-c1-wlroots.sh`
non si lascia ingannare da GNOME, da KWin né da uno sway superstite; la trappola dei 15 caratteri
di `pgrep -x` non si ripaga in nessuno dei quattro file; e `sudo` con lo stderr rediretto non
compare da nessuna parte.

### ⏳ I sedici rilievi non ancora curati, dichiarati invece che dimenticati

Nessuno di questi produce un numero sbagliato in silenzio — sono falsi rossi, etichette imprecise
o rumore — e si prendono quando la fase che li usa li tocca:

| | |
|---|---|
| `fence_non_pronta = 0` non distingue «tutte pronte» da «non l'ho mai chiesto» — sul percorso `memoria` è **sempre** 0 | fase 8 |
| la riga porta la misura **chiesta**, non quella negoziata (che pure è nota) | fase 8 |
| `00-c1-wlroots.sh` uccide un processo prima di validare il nome dell'argomento, e i due banchi C1 prendono gli argomenti in **ordine diverso** | prossimo giro |
| i socket residui su disco fanno bocciare un compositore vivo (falso rosso) | prossimo giro |
| `banco.sh` sincronizza i due lati con `sleep 2.5` invece che con un marcatore (`LEZIONI.md` §2.3-quinquies) | fase 3 |
| il riscaldamento parte da `PAUSED`, non da quando il flusso è attivo | fase 3 |
| una cella fallita sparisce dalla tabella senza lasciare traccia sullo stdout | fase 3 |
| l'atteso di `00-c1-kwin.sh` è **stampato e non confrontato**, ed è scritto con la virgola mentre il misuratore stampa il punto | prossimo giro |
| `prepara` salta ogni file non vuoto: una scena troncata non viene mai rifatta | fase 3 |
| fra una cella e l'altra si uccide e si riparte dopo 1,5 s fissi, e non c'è `trap` | fase 3 |
| `banco.sh` scrive `scena.log` e **non lo legge**: nella tabella di venti celle il controllo di §1.1 non compare, e il file è sovrascritto a ogni cella | fase 3 |
| più cinque rilievi minori e i `[?]` su `quanti_fd`, sul tipo dell'ultimo fotogramma e sul `pkill -x` di una sessione reale | — |

### ⚠ E un difetto che ho fatto io mentre applicavo le cure

Ho caricato i quattro file corretti sul ferro con `... | tail -0` per non stampare il rumore di
`scp`: `tail -0` chiude la pipe subito, `scp` muore di SIGPIPE, **nessun file è partito** — e il
mio `echo "caricati"` lo ha dichiarato fatto. Il giro successivo ha misurato col binario vecchio e
i conti non tornavano. È la stessa forma delle due che avevo già scritto qui sopra — `$?` dopo una
pipe e `set -e` con `grep -c` — alla terza occorrenza in un giorno. ⛔ **La lezione non è
«ricordarsela»: è che il trasferimento va verificato dal lato che riceve** (`LEZIONI.md` §1.7),
che è esattamente quel che ho fatto subito dopo e che ha trovato il guasto in dieci secondi.

---

## Il giudizio dell'utente

**9 agosto 2026**, sui numeri di questa fase:

> *«Non ci sono sorprese: sappiamo che tra tutti i compositor dei 4 DE Mutter è quello che performa
> peggio non riuscendo a produrre oltre i 35 fps, il che significa che GNOME non è in grado di
> garantire 4K/60 fps, ma va bene. Non sarà adatto per il gaming ma consente comunque una
> soddisfacente esperienza desktop e multimedia.»*

⭐ **Che cosa questo giudizio decide, e va scritto perché non venga riaperto per distrazione**: il
tetto di Mutter è **accettato**, e il desiderato di `SPECIFICHE.md` §3.1 — 4K a 60 — resta un
traguardo che **su GNOME non si promette**. Il minimo garantito (`DECISIONI.md` §2.1) è lontanissimo
e non è mai stato in discussione.

⚠ **Due precisazioni tecniche che il giudizio non cambia, ma che chi legge fra sei mesi deve avere
accanto**, o attribuirebbe il tetto alla cosa sbagliata:

1. ⛔ **Il 4K non c'entra.** Il tetto di Mutter è lo stesso a ogni risoluzione — `LEZIONI.md` §3
   domanda 10, *«niente fino a 4K»*. I 36 fotogrammi misurati oggi sono a **1080p**: non si perde
   passando a 4K, si perde e basta. La frase giusta è «GNOME consegna ~36 fotogrammi, a qualunque
   misura», non «GNOME non regge il 4K».
2. ⏳ **E il tetto non è ancora `[M]` come limite: è `[M]` come stato attuale.** Gli intervalli
   misurati oggi — mediana **33,3 ms**, minimo **16,2**, mai valori intermedi — sono la firma di due
   orologi a 60 che battono fra loro, cioè esattamente il meccanismo che `gnome.md` §8.2 legge nel
   codice. La cura candidata (**M3**: negoziare alto e rinegoziare la sola cadenza) costa **zero
   righe di prodotto** e non è stata provata. È in `PIANO.md` fase 3.
   > ⭐ ⚠ *13 agosto 2026: **M3 è stata provata e il fatto riesce** — monitor 120, freno 90, `[M]`
   > **61,4**. ⛔ Ma il meccanismo scritto qui («due orologi che battono») **è sbagliato**, e quello
   > che lo sostituisce (una **quantizzazione** sui tick) è `[R]`, non `[M]`: la «legge verificata
   > su 13 punti» scritta il pomeriggio del 13 agosto **è caduta la sera stessa**, perché le due
   > celle della griglia portavano `scena_sul_mio_monitor: false`. ⇒ **M3 resta mezza**
   > (`gnome.md` §13).*

⚠ La differenza fra le due frasi non è accademica: *«Mutter non va oltre 36»* chiude la questione,
*«Mutter non va oltre 36 finché nessuno separa i due orologi»* la lascia aperta a costo zero. Oggi
vale la seconda.

---

## ⛔⭐ R12-A.44 — l'utente su cui poggiava metà della fase 1 non lo creava nessuno

*11 agosto 2026. Trovato rispondendo a una domanda dell'utente — «devo creare un secondo utente
sul server?» — e la risposta interessante non era sul secondo.*

`prova` è l'utente con cui **B5, B6, B7 e B8** si autenticano, e con cui si verifica la pila PAM del
prodotto (servizio `remotix`, `SPECIFICHE.md` §4.2). ⛔ **Nessun file del deposito lo nominava.**
Era stato creato **a mano** il 10 agosto — `/home/prova` porta quella data — e viveva **dentro il
contenitore**, non sull'host: `getent passwd prova` da fuori esce 2, da dentro dà `1001`.

⇒ Rifacendo il contenitore, **quattro banchi su otto certificati** sarebbero diventati rossi per una
ragione che non è del prodotto. ⭐ È la forma più cara di falso rosso, perché manda a cercare il
difetto nel server.

### Che cosa c'è adesso

`provision.sh` ha un passo **5-bis** che crea **tutt'e due** gli utenti dentro il contenitore, in
modo ripetibile, e che **verifica** che PAM li possa accettare — perché *«l'utente c'è»* e
*«l'utente si autentica»* sono due fatti, e il secondo è quello su cui i banchi poggiano.

| utente | uid | parola d'ordine | perché così |
|---|---|---|---|
| `prova` | 1001 | `parola-di-prova`, **fissa** | ⚠ **compromesso dichiarato**: quella stringa è il predefinito in una dozzina di banchi, e generarla oggi li romperebbe tutti in silenzio. Accettabile perché l'utente vive **dentro un contenitore** non esposto e non esiste su nessuna macchina di nessuno. ⛔ Il giorno che un utente di prova dovesse esistere su una macchina vera, va rifatto |
| `prova2` | 1002 | ⭐ **generata**, scritta in `/media/REMOTIX/credenziali-banchi` (0600) | **fuori dal deposito**, e non deve entrarci. *Deciso dall'utente l'11 agosto 2026.* Si genera **una volta** e poi si rilegge: rigenerarla a ogni giro vorrebbe dire che un banco fermato a metà non si può ripetere |

### ⭐ E il secondo utente serve a due cose, non a una

- **B10** — `SPECIFICHE.md` §5.5: il server serve più utenti, e uno non può prendersi la sessione
  dell'altro. Con un utente solo quella proprietà non si può nemmeno provare.
- **R3.26** — la pila PAM per un utente che **non è il proprietario del processo**. ⚠ Conta più di
  quanto sembri: l'11 agosto B8 ha misurato che le mediane dei tempi si separano per colpa di PAM,
  e **tutte** quelle misure sono con l'utente proprietario.

⭐ **Primo dato, misurato subito**: `prova2` con la parola generata arriva ad **AMMESSO** e poi a
**SESSIONE**, *«dopo 1080 ms — il secondo fisso c'è»*; con la parola sbagliata si vede rispondere
**`RESPINTO: 0x07 = CREDENZIALI_ERRATE`**. ⇒ Il secondo utente si autentica, e il controllo che dice
*no* funziona. ⚠ Il numero dei tempi per un non-proprietario resta da misurare per bene: questo è un
campione solo.

### ⚠ Quel che resta storto, e va detto

⛔ **I banchi prendono la parola d'ordine sulla riga di comando** (`--parola …`), quindi finisce in
`ps` e in ogni registro che catturi il comando. Per `parola-di-prova` è il compromesso di cui sopra;
⛔ **per la parola generata di `prova2` non lo è**, ed è la stessa forma curata oggi su `sonda/`
(R12-A.34). Chi userà `prova2` in un banco deve farle prendere un'altra strada.
