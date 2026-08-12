# F2.2 — La cattura

*Sotto-fase della fase 2 «Il primo fotogramma». Mandato: `MANDATO-12-agosto-fase2.md` §2, riga F2.2.
Porta assegnata: **7512** — e questo banco non apre nessuna porta, ma la riga resta perché un banco
che non nomina la propria porta è un banco che un giorno ne prende una d'altri.*

Aperta e lavorata il **12 agosto 2026**.

---

## Che cosa deve produrre

**Un fotogramma** preso dalla sessione GNOME del server e consegnato in memoria **con il tipo di
buffer dichiarato** — non dedotto.

**Che cosa misura il banco**: non «sono arrivati dei fotogrammi», ma ⭐ **che dentro quel fotogramma
ci sia il desktop**. Un fotogramma nero e valido è il guasto peggiore di questa sotto-fase, e ogni
altro strumento del progetto lo promuoverebbe.

---

## ⛔ Il banco — scritto prima del prodotto

Questo giro **non scrive prodotto**: `src/` non è stato toccato. Quel che segue è il banco, e la
sua certificazione.

### La scena dichiarata, e perché non è quella della fase 0

`CODER.md` §3.2: *la scena si dichiara, e si muove sempre.* La fase 0 usava `weston-simple-egl -f -o`,
che si muove benissimo — ⛔ **ma nei pixel non è riconoscibile**: un triangolo che gira non ha una
firma, e F2.6 (il confronto dei pixel) non avrebbe niente da confrontare. Un banco di F2.2 con
quella scena saprebbe dire «arrivano fotogrammi» e **non** saprebbe dire «arriva il desktop».

⭐ **Scena «bandiera»**, generata da noi e composta di tre parti, una per domanda:

| la parte | che cosa risponde | perché quella |
|---|---|---|
| **sette barre SMPTE**, ferme, a tutto schermo | *«è il desktop, o è il nulla?»* | una firma **ferma**: sta nei pixel e non nel tempo, quindi due giri diversi si confrontano — che è quel che serve a un'**immagine ferma** e a F2.6 |
| **una sfumatura da nero a bianco**, larga tutto lo schermo | *«quanti bit sono veri?»* | 1920 px per 256 livelli. ⛔ È l'unica parte dell'immagine su cui «quanti livelli distinti» sia una domanda sui **bit** e non sulla **scena** |
| **un blocco bianco che scorre**, 12 px per fotogramma | *«arriva qualcosa?»* | Mutter consegna un fotogramma **solo se qualcosa cambia** (`LEZIONI.md` §4 trappola 8). Senza, su un desktop fermo non arriverebbe nulla: uno zero legittimo, e un banco muto |

⚠ E la firma **non è un elenco di colori assoluti**, di proposito. Fra ffmpeg, mpv, il 4:2:0 e la
matrice colore i valori RGB assoluti si spostano, e un giudice che pretendesse `(191,191,0)` sarebbe
rosso su una scena perfetta. Si controllano tre proprietà **che nessuna matrice colore può
invertire**: le sette bande uniformi al loro interno (F1), la luminanza che **cala** da sinistra a
destra su tutte e sette (F2 — vale sia coi pesi 601 sia coi 709: è il disegno stesso delle barre), e
quale canale **domina** in ciascuna banda (F3).

⚠ La scena della fase 0 resta disponibile (`SCENA=tetto`) come legame col controllo positivo storico,
e su di essa il giudizio si riduce a «non è nero e non è uniforme» — e lo dice.
⛔ Con un limite dichiarato: `weston-simple-egl` **non sa scegliere l'uscita**, quindi su una sessione
con più di un monitor quella scena è inaffidabile. Non è un difetto del banco: è un limite del
client, scritto qui invece che scoperto guardando uno zero.

### Che cosa si conta

I due programmi sono **separati apposta**, e la separazione è ciò che rende il banco certificabile:
il produttore scrive un `.raw` e un manifesto, il giudice li legge. ⭐ Fra i due si può infilare un
fotogramma nero della stessa identica misura con lo stesso identico manifesto — cioè il guasto
peggiore di questa sotto-fase — **senza toccare né il produttore né il giudice, e senza
ricompilare**.

| | |
|---|---|
| `banchi/02-cattura-fotogramma.c` | prende **due** fotogrammi (vedi E9 più sotto), li scrive byte per byte, e accanto ci mette il manifesto: tipo di buffer, formato negoziato, stride, danno, sequenza, quanti sono arrivati prima e dopo la scena |
| `banchi/02-cattura-giudica.py` | ⭐ **l'unica cosa del progetto che apre il fotogramma e guarda** |
| `banchi/02-cattura-lancia.sh` | l'ordine fra monitor e scena, la sorveglianza della scena, gli esiti |
| `banchi/02-cattura-certifica.sh` | sano → quattro guasti → risanato |
| `banchi/02-cattura-esiti.jsonl` | una riga per giro, con l'ora, la scena, lo schermo per nome e lo stato della sessione |

### ⛔ Il controllo positivo — gira in coda a **ogni** esecuzione

`LEZIONI.md` §1.9, seconda regola: *«questo strumento sa trovare qualcosa che c'è di sicuro?»*. Uno
strumento che non ha mai trovato niente non è pulito: è **non certificato**.

Alla fine di ogni giro il giudice **fabbrica da sé** tre fotogrammi e si guarda addosso:

| gli si dà | deve dire | ⛔ e non deve dire |
|---|---|---|
| la bandiera sintetica | verde | nulla |
| il nero pieno | `FOTOGRAMMA NERO` | — |
| **il grigio uniforme** | `SCENA NON RICONOSCIUTA` | ⛔ **`FOTOGRAMMA NERO`** |

⭐ **La terza riga, con la sua colonna «e non deve dire», è la metà che conta.** Un giudice che
chiamasse nero un grigio sbaglierebbe la sua diagnosi peggiore **proprio nel caso in cui serve**, e
la cura verrebbe cercata dalla parte sbagliata — la stessa mezza giornata che `PIANO.md` racconta
per la sessione nera. Se anche una sola delle tre non risponde come scritto, il verdetto sul
fotogramma vero **non viene emesso**: esce 2.

E in coda allo script c'è un secondo controllo positivo: che `misura-cattura` della fase 0 sia
ancora al suo posto ed eseguibile. Se un giorno sparisse, questo banco resterebbe verde e il
progetto perderebbe il proprio controllo positivo storico senza che nessuno se ne accorgesse.

### ⛔ Il caso opposto — che aspetto avrebbe il contrario

`LEZIONI.md` §1.11: per ogni prova indiretta si scrive cosa mostrerebbe il caso opposto, o la prova
non distingue.

| il contrario | come si presenterebbe | `[M]` |
|---|---|---|
| **fotogramma nero e valido** | luminanza media ≈ 0 su 3600 punti, marca `FOTOGRAMMA NERO`. È quel che darebbe una sessione senza monitor virtuale: viva, completa e nera | ✅ innestato e visto |
| **buffer mai dipinto / grigio** | `FOTOGRAMMA UNIFORME` + `SCENA NON RICONOSCIUTA`, ⛔ **mai** `FOTOGRAMMA NERO` | ✅ innestato e visto |
| **fotogramma troncato** | `BYTE NON TORNANO`, con i byte contati contro `stride × altezza` | ✅ innestato e visto |
| **schermata vecchia rispedita** | `IL BUFFER NON È CAMBIATO` — ⛔ e questo è **verde su ogni controllo che guardi un fotogramma solo**: si vede solo confrontandone due, ed è per questo che il produttore ne prende due | ✅ innestato e visto |
| **desktop fermo** | uscita 3, zero legittimo | ⭐ ✅ **misurato dal vivo**: scena `fermo`, **1 fotogramma arrivato al montaggio e 0 dopo** |
| **buffer della scheda sbagliata** | ⛔ **questo banco NON lo vedrebbe**: sulla strada della memoria i pixel arrivano comunque | ⚠ `[?]` dichiarata, non assolta dal verde |

### ⛔ Come questo banco si certifica — sano 0 → guasto 1 → risanato 0

Gli attesi **scritti prima del giro**, nella forma di `01-b12-guasti.py`. Il guasto si innesta **nei
pixel**, sempre su una copia, con l'originale da parte e l'impronta accanto.

| # | il guasto | atteso | marca **pretesa** | marca **vietata** |
|---|---|---|---|---|
| G1 | nero pieno, stessi byte | 1 | `FOTOGRAMMA NERO` | — |
| G2 | grigio uniforme, stessi byte | 1 | `SCENA NON RICONOSCIUTA` | ⛔ `FOTOGRAMMA NERO` |
| G3 | ultimi 40 000 byte tagliati | 1 | `BYTE NON TORNANO` | — |
| G4 | il «primo» copiato sul «regime» | 1 | `IL BUFFER NON È CAMBIATO` | ⛔ `FOTOGRAMMA NERO` |

⚠ E se il giro sano non esce 0, la certificazione **si ferma**: innestare un guasto su un banco già
rosso darebbe un rosso che non dice niente.

**Esito** `[M]` **12 agosto 2026, NIC-OS, sessione GNOME headless**:
⭐ **sano 0 → quattro guasti 1 → risanato 0 dopo ognuno**, con le marche pretese presenti, quelle
vietate assenti, e l'impronta del file tornata ogni volta a
`82270430c1823ff113a3f4627fbd8b61350e9cf19d2962cda643fc1d19afad6a`.

⚠ **E non dice che il banco sia giusto**: dice che sa vedere **questi quattro** difetti.
«Non ho trovato niente» non è «è giusto» (`REVIEWER.md` §0).

---

## Le misure

*Scena dichiarata accanto a ogni numero. Tutte `[M]` del 12 agosto 2026, NIC-OS 192.168.0.2, sessione
GNOME headless (`gnome-shell --headless --no-x11`), monitor virtuale montato da noi con
`RecordVirtual`, strada **memoria**, scena «bandiera» 1920×1080@60.*

| che cosa | atteso (scritto prima) | misurato | esito |
|---|---|---|---|
| fotogrammi arrivati | > 0 | **410** (45 prima della scena, 365 dopo) | ✅ |
| **tipo di buffer dichiarato** | `[?]` mai misurato su questa strada | ⭐ **MemFd**, e lo dice PipeWire (`spa_data.type` del piano 0) | ✅ |
| misura negoziata | 1920×1080 | **1920×1080** | ✅ |
| formato negoziato | BGRx | **BGRx**, modificatore `0x0` | ✅ |
| stride | ≥ 7680, **letto** dal chunk | **7680** — cioè esattamente `larghezza × 4` | ✅ |
| byte del `.raw` | stride × 1080 | **8 294 400** | ✅ |
| buffer distinti riciclati | 4 (R29) | **4** | ✅ |
| **la scena si vede nel «regime»** | SÌ | ⭐ **SÌ**, sette bande riconosciute | ✅ |
| «primo» diverso da «regime» | SÌ | **100 % dei punti campionati** | ✅ |
| danno sul fotogramma «primo» | **pieno** | ⛔ **parziale** — vedi sotto | ⚠ |
| danno sul fotogramma «regime» | parziale | **parziale** | ✅ |

Le sette bande, misurate sul fotogramma di regime (RGB medi al cuore di ciascuna):

| banda | R | G | B | luma |
|---|---|---|---|---|
| grigio | 190,5 | 191,0 | 190,4 | 190,8 |
| giallo | 192,0 | 192,0 | 0,0 | 170,1 |
| ciano | 0,0 | 191,0 | 189,8 | 133,8 |
| verde | 0,0 | 191,0 | 0,0 | 112,1 |
| magenta | 190,2 | 0,6 | 191,2 | 79,0 |
| rosso | 190,4 | 0,0 | 0,0 | 56,9 |
| blu | 0,0 | 1,0 | 191,0 | 22,3 |

### ⭐ La domanda che due nostri documenti si contraddicevano su, chiusa con una misura

| documento | diceva |
|---|---|
| `v1/remotix-c/src/cattura.h`, in testa | *«in zero-copy Mutter ricicla i propri buffer e vi ridipinge dentro SOLO la parte cambiata; fuori da quelle regioni ci sono i pixel del fotogramma che aveva usato quel buffer prima»* |
| `gnome.md` §8.1 (Mutter riletto nel codice) | *«⛔ **falso**: blit dell'intero framebuffer, stack di clip svuotato deliberatamente»* |

⭐ **Misurato**: il fotogramma di regime porta danno **parziale** e le sette bande si vedono
**intere**, con i valori qui sopra. ⇒ **Il buffer è intero anche con danno parziale**:
`gnome.md` §8.1 ha ragione, e il commento in testa a `cattura.h` è **vecchio**.

⚠ E la posta era alta: se avesse avuto ragione `cattura.h`, la fase 2 avrebbe consegnato mezzo
desktop e metà schermata vecchia, **senza un errore da nessuna parte**.

### ⛔ Quel che si consegna a F2.3 — dichiarato, non dedotto

*Cucitura chiesta dal coordinatore per conto di F2.3. Le quattro voci sono **chieste al produttore**
(`spa_video_info_raw.color_range / .color_matrix / .transfer_function / .color_primaries`, riempite da
`spa_format_video_raw_parse`), non ricavate da noi — `CODER.md` §3.7.*

| | risposta `[M]` |
|---|---|
| **bit per canale** | **8** — dal formato negoziato (BGRx) |
| **range** | ⚠ **NON DICHIARATO dal produttore** (valore grezzo `0` = UNKNOWN) |
| **matrice** | ⚠ **NON DICHIARATA dal produttore** (`0`) |
| **trasferimento** | ⚠ **NON DICHIARATA** (`0`) |
| **primari** | ⚠ **NON DICHIARATI** (`0`) |

⛔ **E i quattro zeri sono una risposta, non un silenzio da riempire.** Mutter non dichiara nessuna
di quelle quattro cose sul flusso di cattura: chi le volesse le sta **deducendo**, ed è la forma E8.

⭐ **Il range, allora, si misura invece di assumerlo** — e il fotogramma di regime va da **0 a 255**
su tutti e tre i canali: **compatibile con il pieno**. ⚠ E la misura dipende dalla scena: è vera
perché la scena «bandiera» porta apposta il nero e il bianco pieni.

⚠ **Sulla matrice, la risposta onesta è che alla cattura non ce n'è una**: i pixel sono RGB, e
nessuna conversione 601/709 è stata applicata da noi. La matrice **la sceglie F2.3** convertendo in
YCbCr, e ⛔ **F2.6 deve confrontare con la stessa**: un confronto di pixel fatto con la matrice
sbagliata *misura la matrice*.

#### ⛔ F2.3-A, e l'imputato è qui

F2.3 chiama **F2.3-A** il guasto in cui *«la cattura consegna 8 bit, tutta la catena resta verde e
l'etichetta continua a dire Main10»* — e nessuno se ne accorge guardando l'immagine, perché viene
bene lo stesso.

⛔ **Su GNOME non è un rischio: è una certezza, e l'imputato è la cattura.** `gnome.md` §8.3 `[R]`,
letto riga per riga in Mutter 48.7: *«**Solo BGRx e BGRA**»* — formati a **8 bit per canale**.
⇒ **Da questa cattura non possono uscire dieci bit veri.** Un HEVC Main10 alimentato da qui porta
8 bit promossi a 10.

Il numero, misurato **già alla cattura** sulla striscia di sfumatura (righe 840-930, 8640 campioni):

| canale | livelli distinti | multipli di 4 | atteso su 8 bit veri |
|---|---|---|---|
| R | **255** / 256 | **0,259** | ~256 e ~0,250 |
| G | **256** / 256 | **0,259** | ~256 e ~0,250 |
| B | **255** / 256 | **0,249** | ~256 e ~0,250 |

⭐ **Otto bit veri, tutti e otto** — nessun percorso più povero promosso. ⚠ E il fondo scala qui è
256 e non 1024: la domanda a cui questo conto risponde non è «sono dieci bit?» (la risposta è no per
costruzione) ma **«sono almeno otto bit veri?»**. Una frazione di multipli di 4 pari a **1,000**
direbbe che la strada è passata per meno bit di quelli dichiarati.

⚠ **E il conto va fatto sulla sfumatura, non su tutto il fotogramma**: sulle sette barre piatte i
livelli distinti sono ~21-24 **per costruzione**, e lì un numero basso non dice niente sui bit. Il
banco misura e scrive entrambi, con la ragione accanto.

---

## Che cosa si riusa da v1 — **righe contate**, non ricopiate dal piano

| file | il piano dice | contato oggi (`wc -l`) | esito |
|---|---|---|---|
| `v1/remotix-c/src/cattura.c` | 1060 | **1060** | ✅ combacia |
| `v1/remotix-c/src/mutter.c` | 353 | **353** | ✅ combacia |
| `v1/remotix-c/src/superficie.c` | 675 | **675** | ✅ combacia |
| `v1/remotix-c/src/immagine.c` | 273 | **273** | ✅ combacia |
| `v1/remotix-c/src/palco.c` | *(nessuna cifra data)* | **1545** | ⚠ il piano dice solo «per la parte di montaggio» |

⭐ **Le quattro cifre del piano tornano tutte.** ⚠ `palco.c` è l'unica per cui il piano non dà un
numero, e con 1545 righe è il file più grosso dei cinque: «per la parte di montaggio» va sciolto
prima che qualcuno se lo porti dietro intero.

Che cosa vale la pena riusare, letto nei sorgenti:

| da dove | che cosa | ⚠ |
|---|---|---|
| `mutter.h` / `mutter.c` (353) | ⭐ **la sequenza D-Bus che non ammette permute**, con le due punizioni scritte accanto. È il pezzo più prezioso, e questo banco l'ha **ricopiata e provata sul ferro** | nessuna |
| `cattura.h` (l'intestazione) | il DMA-BUF **in due posti**, lo stride **letto** dal chunk, la cadenza a zero | ⛔ il paragrafo sul «diff» è **smentito dalla misura di oggi** e va corretto |
| `immagine.h`/`.c` (273) | l'allineamento R4 (larghezza a 16, altezza a 64) come **funzioni pure**, e `immagine_copia_fotogramma` che prende lo stride del produttore | ⭐ la scena sintetica di `immagine.c` è l'antenata della «bandiera», e per le stesse ragioni (geometria, scala, movimento) |
| `superficie.c` (675) | l'import sulla scheda | ⚠ serve alla fase 8, non a F2.2: qui i pixel si vogliono **leggibili** |
| `palco.c` (1545) | il montaggio | ⚠ da sciogliere |

---

## ⛔ Le trappole già pagate che mordono qui

Andate a leggere, non ricordate. Dove un paragrafo non esiste, è detto.

| # | dove | che cosa morde qui | come il banco lo para |
|---|---|---|---|
| **E1** | `REVIEWER.md` §2 · `LEZIONI.md` §1.11 | *necessario scambiato per sufficiente.* «consegna MemFd ⇒ è in software» e «ha aperto un render node ⇒ rende in GPU» | ⭐ il manifesto porta **tre campi separati**: `chiesto`, `dichiarato_dal_produttore`, `chi_lo_dice` — e una lista di **avvertenze scritte dentro il programma** (I7), che dice che il MemFd qui è la risposta a una **nostra** domanda, non una scoperta |
| **E9** | `REVIEWER.md` §2 · `CODER.md` §3.5 · `LEZIONI.md` §1.4 | *un campione dell'avvio preso per il regime* | vedi il riquadro qui sotto |
| **E2** | `REVIEWER.md` §2 | *due misure sotto la stessa etichetta* | il monitor si dichiara **per nome e per nome del prodotto**, mai per indice né per misura; `chiesto` e `negoziato` sono due campi diversi |
| **E8** | `REVIEWER.md` §2 | *il silenzio scambiato per zero* | quattro uscite distinte (0 · 1 · 2 · 3); i quattro `UNKNOWN` di SPA scritti come «non dichiarato» invece che riempiti |
| trappola 8 | `LEZIONI.md` §4 | *un fotogramma arriva solo se qualcosa cambia* | la scena ha un blocco che si muove **a ogni fotogramma**; e G4 innesta la schermata vecchia rispedita |
| trappola 6 | `LEZIONI.md` §4 | *il buffer della scheda sbagliata, senza un errore* | ⛔ **questo banco non lo vedrebbe**, ed è dichiarato — non assolto |
| trappola 1 e 2 | `LEZIONI.md` §4 | la sequenza D-Bus, e l'iscrizione **prima** di `Start` | ricopiate da `mutter.h` con la ragione accanto |
| B3 punti 1-3 | `fasi/00-ambiente.md` | i **tre difetti di banco già pagati**: `pgrep -x` su un nome di 17 caratteri, un'opzione rifiutata letta come difetto del bersaglio, ⛔ `sudo` dentro un comando di cui si redirige lo stderr | tutti e tre onorati — e vedi «Che cosa non ha funzionato», dove il terzo l'ho ripagato io |
| voce 2 | `fasi/00-ambiente.md` | *una prova che cerca una frase che, se tutto va bene, non compare mai* | ⭐ le marche del fotogramma `primo` sono **avvisi** e non rossi (lì la scena non c'è ancora), e sulla scena `fermo` l'atteso è **rovesciato** |
| voce 8 e 10 | `fasi/00-ambiente.md` | la scena morta, e `kill -0` che riesce sugli zombie | si legge lo **stato** in `ps` (`Z`), e la scena si sorveglia **per tutta** la presa |
| voce 12-bis | `fasi/00-ambiente.md` | *un'etichetta che dichiarava una misura che il compositore non aveva mai onorato* | ⚠ vedi il rilievo su `misura-cattura` più sotto |

### ⛔ E9 per un'immagine ferma: la regola non sparisce, cambia forma

*`CODER.md` §3.5: «un campione preso all'avvio non dice niente del regime».*

Per un'**immagine ferma** la domanda si rovescia: il fotogramma che la fase 2 consegna **è**, per
natura, quello dell'avvio — l'utente si collega e vede il desktop com'è in quell'istante. Quindi il
campione dell'avvio non è un difetto: è il **prodotto**.

⛔ Ma resta un modo di sbagliare, ed è questo: **misurare sul fotogramma dell'avvio e scrivere il
numero in una colonna che la fase 3 leggerà come regime.** Alla fase 0 la distribuzione del danno si
ribaltava fra i due (pieno 15 contro parziale 929).

⇒ Il banco quindi ne prende **due**, li tiene **in due file separati**, e il manifesto dice per
ciascuno quale fotogramma era fra gli arrivati e quanti erano arrivati prima e dopo la scena. La
differenza fra `arrivati_in_tutto` e `dopo_la_scena` **è** il riscaldamento, e si vede invece di
essere dedotta.

⚠ **E qui la misura ha smentito il mio atteso**, che va scritto perché è la parte utile:
avevo scritto *«danno sul fotogramma primo: pieno»*, e la macchina ha risposto ⛔ **parziale su
tutti e 410 i fotogrammi, il primo compreso**. Il ridisegno completo che mi aspettavo al montaggio
del monitor virtuale **non è marcato come tale**. `[?]` Non lo spiego: lo dichiaro. È coerente con
`gnome.md` §8.1 (il buffer è comunque intero), ed è un fatto in più per chi leggerà il danno come
segnale.

---

## ⛔ Che cosa NON ha funzionato

*Si riempie anche quando fa una brutta figura — `PIANO.md` §0.3 punto 2. Qui i quattro difetti sono
tutti **del banco**, e tre su quattro sono miei.*

### 1. ⛔⭐ Il banco è uscito VERDE mentre il difetto era vivo — al primo giro vero

Il primo giro sul ferro ha stampato **VERDETTO: VERDE**. Erano arrivati **2 fotogrammi**, tutt'e due
**prima** che la scena esistesse, e il fotogramma di regime — quello che risponde alla domanda di
F2.2 — **non c'era affatto**. Il giudice ha stampato una riga gialla («non c'è nel manifesto») e ha
concluso verde.

⛔ **È la peggiore delle prove, perché dà fiducia** (`CODER.md` §4.6, `REVIEWER.md` §1), ed è la
forma **E8**: «non c'è» letto come «va bene».

**Le due cure**, e sono due perché il difetto era in due punti:
- il **produttore** ora si ferma con uscita 2 se la scena è dichiarata viva e i fotogrammi dopo di
  lei sono meno del minimo preteso (`--minimo-dopo-scena`, 1 di suo, **0 solo se lo si dichiara**);
- il **giudice** ora conta l'assenza del `regime` come **rilievo rosso**, non come nota.

### 2. ⛔ La causa vera: la scena dipingeva su un altro schermo, e nessuno lo diceva

La sessione GNOME aveva **già** un monitor virtuale (`Meta-0`); il nostro `RecordVirtual` ne
aggiungeva un secondo (`Meta-1`); e `mpv --fs` andava a schermo intero **sul primo**. La scena era
viva — `ps` diceva `Sl`, il registro contava i secondi, i fotogrammi decodificati scorrevano — e la
nostra cattura riceveva **zero**.

⚠ **La fase 0 non l'aveva mai incontrato** perché allora la sessione non aveva nessun altro monitor:
quello montato dal banco era l'unico, e qualunque finestra a schermo intero ci finiva sopra per
forza. ⛔ Il difetto non era nel banco della fase 0: era **nell'ipotesi che quel banco poteva
permettersi e questo no**.

**La cura** è `CODER.md` §3.9 — *quando un componente può decidere da sé, digli cosa fare, e verifica
che abbia obbedito*: il banco conta i monitor **prima** di montare e **dopo**, il nuovo è il nostro,
e lo passa a mpv con `--fs-screen-name`. ⛔ E **due strade indipendenti devono concordare**: il
diff dei nomi e il **nome del prodotto** (`Virtual remote monitor` per `RecordVirtual`,
`MetaVirtualMonitor` per quello della sessione). Se non concordano, il banco si ferma invece di
scegliere il più comodo — perché sul server i due monitor sono **entrambi 1920×1080@60**, e a
distinguerli c'è solo il nome (cucitura di F2.1).

### 3. ⛔ Ho fatto io la redirezione attorno a `enter.sh`, e il comando è restato appeso

`bash …/02-cattura-lancia.sh compila 2>&1 | tail -4`: la pipe sta **attorno** al comando che dentro
chiama `enter.sh`, quindi la richiesta di parola d'ordine di `sudo` — che va sullo stderr — è finita
dentro `tail`. Il comando è restato appeso in silenzio finché non l'ho ucciso.

⚠ È `fasi/00-ambiente.md` B3.3, **pagata quattro volte** prima di me, e nominata a lettere intere nel
mandato che avevo letto un'ora prima. La forma non è «ricordarsela»: è **non scriverla**.

### 4. ⚠ Due errori di ffmpeg con la stessa faccia, e mi sono costati due giri

La scena non si generava, con `Undefined constant or missing '('`. Le cause erano **due**, e danno
lo stesso identico messaggio:
1. `mod(a,b)` — la virgola è il separatore dei filtri di ffmpeg e va protetta con una barra
   rovescia, che però attraversa `bash`, `ssh` e la shell remota e in uno dei tre si perde;
2. `drawbox` **non espone `n`** (il numero di fotogramma), solo `t`.

⭐ Curato scrivendo il modulo senza virgole (`t*V - P*floor(t*V/P)`), e il commento nel banco le
nomina **tutte e due**, perché chi vedrà quel messaggio la prossima volta non sappia solo metà della
storia.

### 5. ⚠ La scena `fermo` mi ha mostrato un giudice troppo severo

Alla prima esecuzione con la scena `fermo` — il caso opposto dichiarato — il giudice ha dato
**ROSSO** perché mancava il fotogramma di regime. ⛔ Ma su una scena che dichiara di non dipingere,
l'assenza del regime **è la risposta giusta**: è lo zero legittimo della trappola 8. Un rosso lì
sarebbe stato un rosso su un banco sano, cioè la voce 2 di `fasi/00-ambiente.md`.

⭐ Curato rovesciando l'atteso: su `fermo` il regime assente è verde, e **un regime presente è
rosso** — vorrebbe dire che sullo schermo si muove qualcosa che non abbiamo dichiarato, e ogni misura
su quello schermo misurerebbe anche quello.

---

## Un rilievo sullo strumento della fase 0, che non è mio da correggere

`REVIEWER.md` §4, marca `[R]`:

```
DOVE:             v1/banchi/banco-compositori/misura-cattura.c, la printf della RIGA
COSA CONTRADDICE: fasi/00-ambiente.md voce 12-bis — «un'etichetta che dichiarava una
                  misura che il compositore non aveva mai onorato»
COME SI DIMOSTRA: la RIGA stampa `larghezza`, `altezza` e `colore` presi da argv, cioè
                  quel che è stato CHIESTO. Il formato NEGOZIATO (`m.formato`) esiste,
                  viene letto in `su_parametri`, e finisce solo sullo stderr — mai nella
                  riga che le tabelle leggono. Se Mutter negoziasse una misura diversa da
                  quella chiesta, la RIGA direbbe quella chiesta.
MARCA:            [R]
```

⚠ La cura di 12-bis era stata scritta in `misura-wlroots` («stampa la misura vera accanto al
numero, invece di ripetere l'etichetta che gli era stata data»); in `misura-cattura` la riga
leggibile a macchina è rimasta com'era. ⛔ Non l'ho toccato: non è un mio file, ed è lo strumento
che certifica tutti gli altri. Nel mio banco `chiesto` e `negoziato` sono **due campi diversi**, e
il giudice dà `MISURA DIVERSA DA QUELLA CHIESTA` se non combaciano.

---

## Le `[?]` da misurare

| `[?]` | perché resta aperta |
|---|---|
| ⛔ **la strada DMA-BUF non è stata provata da questo banco** | il banco la supporta e la dichiarerebbe (rifiutandosi di leggere i pixel, che vivono sulla scheda), ma non è stata eseguita: F2.2 vuole i pixel **leggibili**, e la copia zero è la fase 8 |
| ⛔ **il buffer della scheda sbagliata** | due GPU (Intel `00:02.0`, Radeon `03:00.0`), e il sintomo è composizione in software **senza un errore da nessuna parte**. ⚠ Sulla strada della memoria i pixel arrivano comunque: **questo banco non lo vedrebbe**, e il suo verde non lo assolve |
| **perché il danno è `parziale` anche sul primo fotogramma** | mi aspettavo `pieno` al montaggio del monitor virtuale, e sono usciti 410 parziali su 410. Non lo spiego |
| **il 4:2:0 della scena** | la scena passa per `x264 -qp 0 -pix_fmt yuv420p`: il croma è sottocampionato, e i valori misurati sulle bande (190-192 invece di 191) lo portano dentro. ⚠ Non tocca la firma, che è scelta per sopravvivergli, ma **tocca F2.6** se qualcuno confrontasse pixel per pixel col sorgente della scena invece che col fotogramma catturato |
| **il ritmo su questa strada** | questo banco **non lo misura e non deve**: copia dentro la richiamata di tempo reale. Resta il 36 ± 2 della fase 0 sulla strada DMA-BUF, e `[?]` sulla memoria |
| **se `Meta-0` sopravviva a un riavvio** | il drop-in di F2.1 vive in `$XDG_RUNTIME_DIR`: al primo riavvio la macchina torna nera, e con lei il presupposto di ogni misura di questa sotto-fase |

---

## Le cuciture

### Che cosa **prometto** a F2.3 (la codifica)

⭐ Un fotogramma in memoria, e queste cose **dichiarate**, non dedotte — sono nel manifesto di ogni
giro e nella riga di `02-cattura-esiti.jsonl`, campo `consegna_a_F2_3`:

| | valore `[M]` |
|---|---|
| **formato di pixel** | ⭐ **BGRx, 32 bit per pixel, 8 bit per canale** — B, G, R, x nell'ordine dei byte |
| **misura** | 1920×1080, quella chiesta e onorata |
| **stride** | **7680**, e ⛔ **si legge dal manifesto, mai calcolato come `larghezza × 4`** anche se oggi coincide |
| **byte per fotogramma** | 8 294 400 = stride × altezza |
| **bit veri** | ⭐ **8, tutti e otto** — 255/256/255 livelli distinti sulla sfumatura, multipli di 4 a 0,259/0,259/0,249 |
| **range** | ⚠ Mutter **non lo dichiara** (UNKNOWN). Misurato: 0-255, compatibile con **pieno** |
| **matrice** | ⛔ **nessuna**: alla cattura i pixel sono RGB. La sceglie F2.3 |
| **trasferimento, primari** | ⚠ Mutter **non li dichiara** (UNKNOWN) |
| **integrità** | ⭐ il fotogramma è **intero** anche quando il danno è parziale |
| **la scena** | «bandiera», riproducibile con `02-cattura-lancia.sh scena`, con la sfumatura a 256 livelli per rifare **lo stesso conto sullo stesso fotogramma** |

⛔ **E la cosa che F2.3 deve sapere prima di scrivere una riga**: **F2.3-A non è un rischio, è una
certezza, e l'imputato è la cattura.** Mutter consegna solo BGRx/BGRA (`gnome.md` §8.3 `[R]`) ⇒ un
Main10 alimentato da qui porta **8 bit promossi a 10**. Il desiderato di `SPECIFICHE.md` §3.1 —
10 bit per canale — **non può essere soddisfatto da questa sorgente**, e la promozione va
**dichiarata** e non subita.

### Che cosa **chiedo** a F2.1 (la sessione)

1. ⛔ **che la sessione abbia un monitor virtuale, e che si sappia quale**: la mia cattura ne monta
   uno suo con `RecordVirtual`, ma una **scena a schermo intero va sul monitor della sessione**, non
   sul mio. È la causa del mio primo falso verde. Se F2.1 garantisce il monitor della sessione per
   nome, il mio banco può smettere di montarne uno.
   ⚠ E i due sono **entrambi 1920×1080@60**: a distinguerli c'è **solo il nome del prodotto**
   (`MetaVirtualMonitor` contro `Virtual remote monitor`).
2. `02-sessione-stato.py` **sul server**: il mio banco lo chiama prima di ogni conta e ne scrive
   l'esito nella riga. ⚠ Oggi non c'è ancora in `/media/REMOTIX/src/`, e il banco lo **dichiara**
   («non disponibile») invece di saltarlo in silenzio.
3. ⛔ **che nessuno mi spenga la sessione a metà presa**: un `Shell.Screenshot` su zero monitor
   porta via l'intera sessione. Se una mia esecuzione muore senza una ragione mia, la rifaccio
   invece di scrivere il rosso.

### Che cosa **chiedo** a F2.4 (il filo) e **prometto** a F2.5 / F2.6

| a chi | che cosa |
|---|---|
| **F2.4** | il fotogramma è **8,3 MB non compressi**: non passa sul filo così com'è, e la misura del messaggio la decide F2.3. Da me arriva un blocco continuo, righe da 7680 byte |
| **F2.5** | ⚠ `VideoDecoder` restituirà YUV: la conversione a RGB per la tela usa **una matrice**, e va **dichiarata** — o F2.6 confronterà due immagini convertite in due modi |
| **F2.6** | ⭐ **il fotogramma catturato è già su disco**, `.raw` BGRx più manifesto: il confronto si fa contro **quello**, non contro l'MP4 della scena — che è passato per 4:2:0 e non è la stessa immagine. E la firma delle sette bande (uniformità · luminanza decrescente · dominio dei canali) è **scritta e certificata**: si riusa invece di reinventarla, e sopravvive alla matrice colore |
| **F2.6** | ⛔ e la domanda che ha già un imputato: **se i pixel non tornassero, la matrice è la prima sospetta, non la cattura** — la cattura è RGB e non ne applica nessuna |

### Che cosa lascio al giro del **prodotto** (non a una sotto-fase)

- ⛔ **`cattura.h` di v1 va corretto**: il paragrafo sul «diff» dei buffer riciclati è smentito dalla
  misura di oggi, e `gnome.md` §8.1 lo aveva già smentito nel codice. Un riferimento che invecchia
  in silenzio è peggio di nessun riferimento (`CODER.md` §0).
- ⚠ **`palco.c` è 1545 righe** e il piano non gli dà una cifra: «per la parte di montaggio» va
  sciolto prima che qualcuno se lo porti dietro intero.
- ⚠ Il rilievo `[R]` su `misura-cattura.c` qui sopra: non è mio da correggere, ma è lo strumento che
  certifica tutti gli altri.

---

## La riga per il catalogo delle certificazioni

```
nome            F2.2 — la cattura (il fotogramma nero e valido)
comando         bash /media/REMOTIX/src/02-cattura-certifica.sh
atteso sano     0   VERDE: un fotogramma 1920×1080 BGRx MemFd che contiene la scena
                    dichiarata, con il regime distinto dal primo
guasti          nero · grigio · troncato · copia
                ⛔ innestati nel .raw, MAI nel codice, sempre su una copia con
                   l'originale da parte e l'impronta accanto
atteso guasto   1   ciascuno, con la marca PRETESA e la marca VIETATA:
                    nero     → FOTOGRAMMA NERO
                    grigio   → SCENA NON RICONOSCIUTA,  ⛔ vietata FOTOGRAMMA NERO
                    troncato → BYTE NON TORNANO
                    copia    → IL BUFFER NON È CAMBIATO, ⛔ vietata FOTOGRAMMA NERO
atteso risanato 0   dopo ognuno, con l'impronta tornata a
                    82270430c1823ff113a3f4627fbd8b61350e9cf19d2962cda643fc1d19afad6a
costa           copia-di-file (nessuna ricompilazione)
esito           ⭐ [M] 12 agosto 2026, NIC-OS: 0 → 1 ×4 → 0. CERTIFICATO
riferimento     fasi/rapporti/F2-2-cattura.md · gnome.md §3.1, §8.1, §8.3, §13 M9 ·
                LEZIONI.md §1.9, §1.11, §4 trappole 1, 2, 6, 8 ·
                REVIEWER.md §1 punto 4, E1, E2, E8, E9 · fasi/00-ambiente.md B3, voci 2, 8, 12-bis
```

---

## Il giudizio dell'utente

⏳ Non ancora dato. ⛔ E questa sotto-fase **non si chiude senza**: `PIANO.md` §0.3 punto 3, e
l'invariante I8 — *il metro è quel che l'utente vede, non il numero che esce dal banco*.

⚠ La cosa da mettergli davanti non è una tabella: è **il fotogramma**. Sta in
`/media/REMOTIX/tmp/02-cattura/giro-*-regime.raw`, ed è il primo pixel vero di REMOTIX_V2.
