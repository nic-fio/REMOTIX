# FASI — che cosa è stato fatto, fase per fase

*I documenti delle fasi **chiuse**, cuciti in un documento solo il **16 agosto 2026** per decisione
dell'utente. ⛔ **Non è un riassunto**: il testo è quello che era, riga per riga, con i titoli
abbassati di un livello per farli stare sotto ai capitoli. Nessuna misura, nessuna marca e nessuna
data sono state toccate.*

> ## ⛔⭐ LA REGOLA, ED È CAMBIATA IN UN PUNTO SOLO
>
> **`PIANO.md` §0.1 resta intatta**: *«il documento di fase si apre all'inizio e si riempie strada
> facendo. Non si scrive alla fine»*. Un documento scritto dopo è un **resoconto**, e in un
> resoconto le misure si *ricordano* invece di essere *registrate*.
>
> ⭐ **Quel che cambia è dove vive quel documento mentre la fase è aperta:**
>
> | | |
> |---|---|
> | **la fase in corso** | ha un file suo, `fasi/NN-nome.md`, aperto il giorno in cui si apre la fase. ⭐ Si lavora sempre su un file piccolo |
> | **la fase chiusa** | diventa un **capitolo di qui**, ripiegato dentro alla chiusura |
>
> ⇒ Il progetto tiene **dieci documenti a fase chiusa e undici mentre si lavora**, e non si edita mai
> un file da quattordicimila righe nel mezzo di una fase.
>
> ⛔ **E la regola che questo NON allenta**: il capitolo non si scrive alla chiusura. Alla chiusura
> si *sposta* un documento che esisteva già da quando la fase si è aperta. Se un capitolo compare
> qui senza essere mai esistito come file, la regola è stata violata — e si vede, perché le misure
> non avrebbero l'ora accanto.

## Come si trova una cosa qui dentro

Ogni capitolo tiene **la numerazione che aveva da file separato**, e **le chiavi dei capitoli sono i
nomi che avevano i file**: un rimando che prima diceva §01-filo-nudo §7 adesso dice
**`FASI.md` §01-filo-nudo §7**, e la sezione ha lo stesso numero di prima.

| capitolo | la fase | chiusa il | righe |
|---|---|---|---|
| [**§00-ambiente**](#00-ambiente) | L'ambiente e i banchi | | 649 |
| [**§01-filo-nudo**](#01-filo-nudo) | Il filo nudo | 11 agosto 2026 | 2 151 |
| [**§02-primo-fotogramma**](#02-primo-fotogramma) | Il primo fotogramma | 13 agosto 2026 | 594 |
| [**§03-movimento**](#03-movimento) | Il movimento | 14 agosto 2026 | 755 |
| [**§04-si-comanda**](#04-si-comanda) | Si comanda | 14 agosto 2026 | 874 |
| [**§05-la-sessione**](#05-la-sessione) | La sessione | 16 agosto 2026 | 1 470 |

⚠ **E `§00-ambiente` porta in coda un'appendice** che prima era §00-ambiente: gli
attrezzi che vivevano **solo sul server**, e i registri che sono misure.

### Le quattro regole, in breve

Il modello sta in `PIANO.md` §0.2.

1. le **decisioni** stanno in `DECISIONI.md`, una sola volta: qui si **rimanda**, non si copia;
2. **«che cosa non ha funzionato»** si riempie anche quando fa una brutta figura;
3. la fase si chiude su **una misura giudicata dall'utente**, non su un documento completo;
4. il **banco si certifica** prima di essere creduto.

---

> # ⛔⛔ I RAPPORTI DEGLI AGENTI NON SONO PIÙ SU DISCO — *16 agosto 2026*
>
> *Decisione dell'utente: «elimina i rapporti degli agenti: non dovrebbero servire più».*
>
> `fasi/rapporti/` e `web/rapporti/` — **94 file, 42 900 righe**, il 63 % di tutto quel che il
> progetto aveva scritto — sono stati tolti.
>
> ## ⭐ Ma NON sono persi, e questo è il punto: come si recupera uno
>
> Sono usciti con `git rm`, quindi la storia li ha per intero. **L'ultimo commit in cui vivono è
> `0c85e5c`**, e da lì si tira fuori qualunque rapporto senza rimetterlo su disco:
>
> ```
> git show 0c85e5c:fasi/rapporti/F3-E-anello-rimisurato.md | less     # leggerne uno
> git show 0c85e5c --stat -- fasi/rapporti | head -100                # vedere l'elenco
> git checkout 0c85e5c -- fasi/rapporti/F4-O2-anello-input.md         # riportarne uno su disco
> ```
>
> ## ⚠ E il prezzo, misurato prima di toglierli invece che scoperto dopo
>
> ⛔ **169 rimandi** dai documenti che restano puntavano dentro quei rapporti, verso **50 file
> diversi**. Quei rimandi adesso nominano un file che su disco non c'è — ⭐ **e restano risolvibili**
> con le tre righe qui sopra, perché il nome nel rimando è ancora il nome nella storia.
>
> ⚠ **I tre più citati**, perché sono quelli che qualcuno cercherà per primo:
> `web/rapporti/S-esiti-sonda.md` (18 rimandi — ⛔ e non era un rapporto, erano **gli esiti misurati
> della sonda del browser**, con la scena accanto a ogni numero), `F5-desktop-vero.md` e
> `F2-6-giudizio.md` (9 ciascuno).
>
> ⇒ ⛔ **La regola che questo tocca è `LEZIONI.md` §9.8**, *«la fonte sta accanto alla misura»*: la
> fonte **c'è ancora**, ma adesso sta in un commit invece che in un file. Chi cita un numero
> misurato da qui in avanti lo sappia — e il posto giusto per un numero che deve sopravvivere è **il
> capitolo di fase**, non il rapporto che lo ha prodotto.

---

## ✅ Lo stato: la `05` è chiusa, e la `6` non è ancora aperta — 16 agosto 2026

`§05-la-sessione` è stata aperta il 15 agosto **col suo documento e prima di una riga di codice**, e
chiusa il 16 **sul giudizio dell'utente** (§7 raccoglie le sue parole, con la data — non un verdetto
scritto da noi).

⭐ **E la prova che l'ha chiusa l'ha fatta l'utente**, con un lavoro vero dentro: un ciclo infinito
in un terminale, il browser chiuso, la finestra rimpicciolita, il rientro — e il ciclo girava
ancora. ⛔ Tutte le prove nostre avevano un desktop **vuoto**, che appena rinato è identico a com'era:
il testimone peggiore possibile per la domanda «è sopravvissuta?».

⏳ **E la fase 6 non si è aperta subito**: l'utente ha chiesto prima una revisione di `PIANO.md`,
*«che ha alcuni punti secondo me fuori sequenza»*.

> ### ✅ ⭐ La revisione è stata fatta il 16 agosto 2026, e ha cambiato due cose
>
> | | |
> |---|---|
> | ⭐ **la fase 8 non è più «l'accelerazione»: è «la copia zero»** | la codifica in hardware era già entrata nel prodotto il **13 agosto**, e i 10 bit sono un muro **a monte** (la cattura). Restava la copia zero, ed è tutta la fase |
> | ⭐⭐ **il multi-tenant passa davanti ai desktop nuovi** — *«PRIMA si chiude lo sviluppo anche con il multi-tenant, e solo dopo si pensa agli altri DE»* | **era la fase 12, è la fase 10**; KDE 10 → **11**, XFCE/LXQt 11 → **12**. La 9 e la 13 restano dove sono (`DECISIONI.md` §4.6-sexies) |
>
> ⇒ **L'ordine di adesso**: 6 · 7 · 8 la copia zero · 9 la qualità · **10 il multi-tenant** ·
> 11 KDE · 12 XFCE e LXQt · 13 il servizio.
>
> ⛔ **Trappola di lettura, e vale per chi cerca all'indietro**: `STUDI.md` §kde, `STUDI.md` §gnome,
> `STUDI.md` §xfce e `STUDI.md` §lxqt dicono in testa *«per la fase 11»*, ma quella è **la fase 11 di
> v1** — sono studi del 7-8 agosto 2026, scritti prima che questo piano esistesse. Quei numeri **non
> sono questi numeri**, e infatti non sono stati toccati.

> ### ⚠ ~~Manca il `05`~~ — com'era scritto il 15 agosto, e si conserva
>
> *15 agosto 2026.* La fase 5 non è ancora stata aperta. ⛔ E la **coda della fase 4** — la notte in
> cui la tela è diventata la finestra del browser — sta **dentro `§04-si-comanda`**, non in un
> documento suo: il numero della fase lo dà il **perché** si è fatto il lavoro, non l'elenco delle
> cose prodotte. Quel lavoro tocca contenuto della fase 6, e `PIANO.md` dice quali sue parti si
> trovano già fatte.
>
> ⚠ Quella coda porta in testa la sua riserva di forma: è stata scritta **alla chiusura**, contro la
> regola qui sopra. Le misure però non sono ricordate — vengono dai registri del server e dai giri di
> banco, con l'ora accanto. ⛔ La regola resta: **la fase 5 si apre col suo documento**.


---

<a id="00-ambiente"></a>

## Fase 0 — L'ambiente e i banchi

Aperta il **9 agosto 2026** · **Chiusa il 9 agosto 2026**

> Prima fase di REMOTIX, e l'unica che non produce prodotto. Il modello di questo documento sta
> in [`PIANO.md`](PIANO.md) §0.2; le decisioni stanno in
> [`DECISIONI.md`](DECISIONI.md) e qui si **rimanda**, non si copia.

---

### Che cosa deve produrre

La macchina che compila e prova, i banchi di v1 rimessi in funzione, e l'ambiente Android che la
sonda della fase 2 richiederà.

**Che cosa vede e giudica l'utente**: i numeri di v1 **riprodotti** — la cattura di Mutter che
consegna ~37 fotogrammi al secondo, quella di KWin ~60.

⭐ **Non è un risultato di prodotto: è il controllo positivo di tutto il progetto.** Se il banco non
sa riprodurre un numero che sappiamo vero, ogni misura delle tredici fasi successive è sospetta —
e non lo sarebbe *un po'*: lo sarebbe esattamente quanto lo erano le misure di ritmo delle fasi 3-9
di v1, che sono state buttate tutte (`LEZIONI.md` §1.1).

---

### Il banco

⛔ *Scritto prima di sviluppare, e revisionato per primo — `PIANO.md` §0.4, momento 1.*

#### B1. Che cosa si misura, e con che scena

| | |
|---|---|
| **lo strumento** | `fondamenta/banchi/banco-compositori/misura-cattura` — consumatore PipeWire che conta i fotogrammi e dice tipo di buffer, danno, buffer riciclati, se il disegno era finito, e la distribuzione degli intervalli. Sa montare da sé lo schermo virtuale di Mutter |
| **la scena** | ⛔ **dichiarata, e in movimento a ogni ridisegno**: a schermo intero, opaca, che ridisegna a ogni *frame callback* del compositore. Non una scena ferma, non una mossa a colpi di tastiera (`LEZIONI.md` §1.1). ⚠ *Qui era nominato `weston-simple-egl -f -o`: `[M]` **il 13 agosto 2026 non è installato**, e dalla fase 3 la scena è la nostra — `banchi/03-scena.c`, che porta una marca e **conta le proprie attese***. ⛔ **E c'è un terzo requisito, imparato in fase 3**: la scena deve stare **sul monitor che si sta catturando** |
| **il controllo che dice di chi è il tetto** | ⛔ **quanto disegna il client**, contato accanto a quanto consegna la cattura. Senza, un tetto della scena viene attribuito al compositore — e viceversa |
| **la durata** | ⚠ **almeno 300 fotogrammi, e si scartano i primi**: i primi dieci sono l'avvio, quando tutto viene ridipinto, e su di essi il rapporto si ribalta (`LEZIONI.md` §1.4) |

#### B2. Come questo banco si certifica, prima di essere creduto

⛔ La domanda non è «funziona?», è **«saprebbe accorgersi che non funziona?»**. Quattro prove, e
nessuna costa più di un minuto:

| # | La prova | Che cosa dimostra |
|---|---|---|
| **C1** | si punta lo strumento su **KWin `--virtual`**, dove il numero atteso è 59-60 `[M]` 8 ago | è il controllo positivo vero e proprio: *lo strumento sa trovare qualcosa che c'è di sicuro?* (`LEZIONI.md` §1.9 regola 2) |
| **C2** | si **spegne la scena** e si rimisura | ⛔ il numero **deve crollare**. Se resta ~37 con la scena ferma, il banco non sta misurando la cattura ma qualcos'altro, e ogni fase successiva erediterebbe la bugia |
| **C3** | si punta lo strumento su un nodo **che non esiste** | ⛔ deve dire **«sono fallito»**, non «zero fotogrammi». «Vuoto» e «proibito» hanno lo stesso aspetto, ed è la lezione che è costata una riga sbagliata in un documento di riferimento (`LEZIONI.md` §1.9) |
| **C4** | si esegue il banco **due volte di fila**, senza rimettere la macchina | uno che passa solo da macchina pulita non è un banco, è una dimostrazione (`LEZIONI.md` §2.3-ter) |

#### B3. ⛔ I tre difetti di banco già pagati, che qui si controllano nel codice

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

#### B4. La certificazione dell'ambiente, che qui vale quanto quella del banco

Questa fase misura una macchina, non un prodotto — quindi l'ambiente **è** l'incognita, e va
accertato con la stessa severità:

| | Perché non si dà per scontato |
|---|---|
| ⛔ **l'utente è nei gruppi `render` e `video`** | senza, la Shell non apre `/dev/dri` e **Mutter ripiega sul rendering in software senza un errore da nessuna parte** `[M]` 6 ago. I 37 fotogrammi misurati così sarebbero un numero diverso sotto la stessa etichetta — la forma d'errore **E2** |
| ⛔ **e il gestore `systemd --user` è stato riavviato dopo** | i gruppi supplementari di un processo già vivo **non cambiano**: aggiungere l'utente al gruppo senza riavviare il gestore lascia tutto com'era, e sembra fatto |
| **su quale scheda disegna il compositore** | la macchina ha **due** GPU (Intel `0000:00:02.0`, Radeon `0000:03:00.0`), e un buffer della scheda sbagliata non è importabile: il sintomo è composizione in software **senza un errore** (`LEZIONI.md` §4 trappola 6) |
| **il rootfs vive in RAM e si azzera al riavvio** | ⚠ quindi «la macchina è a posto» è vero **per questa accensione**. Il ripristino si prova **riavviando**, non rileggendo lo script (`LEZIONI.md` §2.5-bis) |

---

### Che cosa è stato sviluppato

Nessun codice di prodotto: questa fase rimette in funzione quel che esiste già — più due cose
nuove, che sono banco.

| | |
|---|---|
| `fondamenta/banco/provision-server.sh` | il ripristino della macchina, rieseguito il 9 agosto: GNOME 48.7, `vainfo`, `libei1`, e l'utente nei gruppi `render`/`video` |
| ⭐ `fondamenta/banco/provision.sh`, passo **5-bis** | **gli utenti di prova dell'autenticazione, dichiarati l'11 agosto 2026** — vedi il riquadro qui sotto |
| `fondamenta/banchi/banco-compositori/` | portato sul ferro in `/media/REMOTIX/tmp/`, ricompilato nel `devroot` |
| ⭐ `banchi/00-sessione-gnome.sh` | **nuovo**: avvia una sessione GNOME senza monitor con l'ambiente composto da zero, e **verifica** che sia headless invece di sperarlo (`DECISIONI.md` §4.3-bis) |
| ⭐ `banchi/00-c1-wlroots.sh` | **nuovo**: la certificazione di `misura-wlroots`, il terzo banco, su sway e labwc |
| ⭐ `banchi/00-c1-kwin.sh` | **nuovo**: la certificazione C1 — lo stesso strumento su KWin, con l'atteso di `STUDI.md` §kde §5.7 stampato prima della misura |
| ⭐ `banchi/00-rimetti-macchina.sh` | **nuovo**: rimette in piedi la macchina partendo da **prima del disco**, che è il passo che nessuno script conteneva |
| ⭐ `fondamenta/banchi/banco-compositori/misura-cattura.c` | **corretto**: ora distingue lo zero dal fallimento |
| ⭐ `fondamenta/banchi/banco-compositori/banco.sh` | **corretto** due volte: `stdbuf -oL` sulla scena, e la verifica che la scena sia viva prima di credere al numero |
| ⭐ `fondamenta/banchi/banco-compositori/provision-banco.sh` | **corretto**: prende le credenziali con `sudo -v -S -p`, come l'altro script di ripristino |

⚠ La sessione si avvia con `gnome-session --session=gnome` e l'ambiente di `sessione.c`; il
congedo è **`Logout(2)`**, non `systemctl --user stop`.

---

### Le misure

*(Riempito strada facendo. La scena dichiarata accanto a ogni numero.)*

#### Lo stato della macchina, **prima** di toccarla

| Che cosa | Misurato | Data |
|---|---|---|
| GNOME installato sul server | ⛔ **no** (`dpkg-query` → not-installed) — conferma `STUDI.md` §gnome §2 | 9 ago |
| `vainfo` installato | ⛔ **no** | 9 ago |
| `nicfio` nei gruppi `render`/`video` | ⛔ **no** (`nicfio sudo`) | 9 ago |
| `/media` montata, `/etc/fstab` | montata; ⚠ **fstab vuoto**, come `LEZIONI.md` §2.5-bis | 9 ago |
| cache apt su `/media` | ✅ 1450 `.deb`, 1,1 G — la reinstallazione non scarica quasi nulla | 9 ago |
| GPU visibili | ✅ Intel `00:02.0` → `renderD128`, Radeon `03:00.0` → `renderD129` | 9 ago |
| rootfs | ⚠ **32 G in RAM**, si azzera al riavvio | 9 ago |

#### Dopo il ripristino (`provision-server.sh`, uscita 0)

| Che cosa | Atteso | Misurato | Data |
|---|---|---|---|
| Mutter / gnome-shell | 48.7 (Trixie) | ✅ **48.7**, `gnome-session` 48.0 — le versioni che `STUDI.md` §gnome ha studiato | 9 ago |
| `nicfio` nei gruppi | `render`, `video` | ✅ `nicfio sudo video render` | 9 ago |
| `libei1` | presente | ✅ 1.3.901 | 9 ago |
| `weston-simple-egl` per la scena | presente | ⛔ **ASSENTE il 13 agosto 2026** — `[M]`. Era ✅ `/usr/bin/weston-simple-egl` il 9 ago, ed è sparito: **il rootfs sta in RAM** e la macchina che si rimette da sé non si rimette *completa* (`LEZIONI.md` §2.5-bis). ⇒ La scena della fase 3 è **la nostra** (`banchi/03-scena.c`), e non dipende da un pacchetto | 9 ago → **13 ago** |

#### `vainfo` — la `[?]` del budget del codificatore, chiusa

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

#### ⭐ Il controllo positivo del progetto — riprodotto

**Scena dichiarata**: `weston-simple-egl -f -o`, schermo intero, opaco, un commit per ogni
ridisegno del compositore. Monitor virtuale 1920×1080 montato dal banco via `RecordVirtual`,
20 secondi di misura, 7 di scarto. GNOME 48.7 headless, DMA-BUF, BGRx, 60 dichiarati.

> ⛔ *13 agosto 2026, e va letto prima di rifare questa misura: **la scena qui nominata non è più
> disponibile** (`weston-simple-egl` non è installato), e **il numero che questo controllo positivo
> riproduceva — i ~37 di Mutter — non si riproduce**. Non è un difetto del banco: alla cadenza che
> gli si chiedeva Mutter consegna **31,5**, e rinegoziando la sola cadenza (monitor 120, freno 90)
> ne consegna `[M]` **61,4**. ⚠ Che il 37 fosse il resto di una **divisione troncata** è la
> spiegazione più probabile, ed è `[R]` — letta nel codice di Mutter, **non misurata**
> (`STUDI.md` §gnome §8.2; la «legge su 13 punti» che si leggeva qui il 13 agosto **è caduta la sera
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
| **C1 — lo stesso strumento su KWin** | **59,2** `[M]` `STUDI.md` §kde §5.7 | ⭐ **58,92** (1180 fotogrammi, mediana 17,0 ms) | ✅ | 9 ago |
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
a 60 che battono fra loro, che è esattamente il meccanismo che `STUDI.md` §gnome §8.2 legge nel codice
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

#### ⭐ La prova che conta più di tutte: dopo un riavvio VERO

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

#### ⭐ Le tre famiglie di compositori, tutte con un numero riprodotto

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

#### Quel che resta fuori da questa fase, per scelta

| Che cosa | Perché non qui |
|---|---|
| le **tabelle per risoluzione** (720p → 4K) di Mutter e KWin | esistono già `[M]` in `STUDI.md` §kde §5.7 e in `LEZIONI.md` §3. Rifarle adesso sarebbe misurare prima di avere la domanda: servono alla fase 8 (l'accelerazione) e alla 10 (KDE) |
| le scene `video` e `carico` | idem: rispondono a domande delle fasi 3 e 9 |
| `adb`, Desktop AVD, il telefono vero | l'ambiente Android serve alla **sonda della fase 2**, e l'utente ha chiesto di lasciarlo stare per ora. ⚠ *Riletto il 9 agosto sera: `adb` e l'AVD **non servono più affatto** (non c'è più un'applicazione Android), e **il telefono vero serve alla fase 1**. Vedi la voce corretta in «Che cosa resta `[?]`»* |

---

### ⛔ Che cosa NON ha funzionato

⭐ **Cinque difetti in un pomeriggio, e nessuno era del compositore: quattro erano del banco e uno
del provisioning.** È la fase 0 che fa il suo mestiere — se questi fossero comparsi alla fase 3,
avrebbero avuto l'aspetto di difetti di Mutter.

#### 1. ⛔ Il misuratore non distingueva lo zero dal fallimento — ed era lo strumento che certifica tutti gli altri

Puntato su un nodo che non esiste, `misura-cattura` rispondeva **«fotogrammi 0 → 0,00 al secondo»
con uscita 0**: identico a una scena ferma, che è un risultato legittimo. Due cose opposte sotto
la stessa faccia (`LEZIONI.md` §1.9; è la domanda 4 di `REVIEWER.md` §1).

**La cura**: il discrimine è se il flusso sia mai diventato **attivo**. Ora stampa `GUASTO`,
non una `RIGA`, ed esce con 2. ⭐ E in dote arriva la ragione, che PipeWire dava già e che
buttavamo via: *«no target node available»*.

⚠ **Il prezzo che non abbiamo pagato**: un giro andato storto — un nodo sbagliato, un permesso
negato, il compositore non ancora in piedi — sarebbe entrato in tabella come «il compositore non
consegna niente».

#### 2. ⛔ La prova dell'headless cercava una frase che, se tutto va bene, non compare mai

La prima stesura di `00-sessione-gnome.sh` verificava l'headless cercando nel registro di Mutter
*«No seat assigned, running headlessly»*. Letto poi il codice
(`meta-backend-native.c:748-764`): quel messaggio esce **solo** nel percorso **accidentale** —
quando l'headless lo si eredita dalla mancanza di un seat. Chiedendolo con `--headless`, come
fa il nostro drop-in, Mutter esce prima e **non dice niente**.

⛔ Su una sessione perfettamente sana la prova avrebbe dato **rosso per sempre**. È `LEZIONI.md`
§1.11: per ogni prova indiretta va scritto che aspetto avrebbe il caso opposto, o la prova non
distingue. Ora il banco riconosce **tutti e due** i modi, e dice quale dei due è.

#### 3. ⛔ «Nessuna riga trovata» era una lettura negata

Il primo tentativo di leggere quel che Mutter dice usava `journalctl --user`, che ha risposto con
zero righe. Non perché Mutter tacesse: **il comando non aveva potuto aprire niente** — prima per
permessi (`insufficient permissions`), poi perché su questa macchina il journal **non esiste
affatto**, il rootfs vivendo in RAM.

⭐ La cura non chiede root: l'unità della Shell è **d'utente**, quindi un drop-in in
`~/.config/systemd/user` manda la sua uscita in un file nostro.

⚠ **E la conseguenza va oltre questa fase**: `LEZIONI.md` §1.10 dice *«accendi il registro del
componente che nega»*. Su questa macchina quel registro **non c'è di suo**, e ogni fase che vorrà
farsi dire qualcosa da un componente dovrà procurarsene il canale.

#### 4. ⛔ Riavviare la sessione: `pkill` lascia il gestore vivo, e nessuno lo dice

`pkill gnome-session` ha lasciato `gnome-session-manager@gnome.service` **attiva con il
compositore morto**: il riavvio non ha fatto niente, e il banco ha aspettato quaranta secondi
senza una riga che spiegasse perché. È `LEZIONI.md` §2.3-ter — su Plasma dava «Could not start
Plasma session», qui **non dà nessun errore**.

⛔ **E la prima cura era sbagliata a sua volta**: aspettare che `is-active` fosse *diverso da
`active`* si sblocca dopo mezzo secondo, perché passa da **`deactivating`** — cioè si riparte
dentro l'intervallo di smontaggio, che è il difetto che la guardia doveva togliere. Si aspetta
`inactive`. E il congedo giusto è **`Logout(2)`** (`STUDI.md` §gnome §3.2): `systemctl --user stop` non
ferma il gestore, e `Logout(1)` mostrerebbe un dialogo che in una sessione non presidiata non
vede nessuno.

#### 5. ⚠ Il provisioning non dichiarava una dipendenza dei banchi

Per leggere il journal servono i gruppi `adm`/`systemd-journal`, che `provision-server.sh` non
concede. È la stessa forma di `LEZIONI.md` §2.5-bis — *«i banchi dipendono da cose che il
provisioning non installa»* — e si è vista al primo riavvio vero. ⚠ Qui è finita in un vicolo
cieco (il journal non c'è comunque), ma la riga va aggiunta lo stesso: **la dipendenza esisteva e
non era dichiarata**.

#### 6. ⛔⛔ Il riavvio vero: lo script che rimette in piedi la macchina **sta sul disco che non si monta**

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

#### 7. ⛔ E i banchi dipendono da un **secondo** script, che il primo non nomina

Rimessa in piedi la macchina con `provision-server.sh` (uscita 0, oltre 500 pacchetti), la misura
ha dato **`fps=0.00` per tre giri di fila**. Con la cattura attiva quello è uno **zero legittimo**
— «il compositore non ha niente da consegnare» — ed era vero: non c'era **niente da catturare**,
perché mancava il pacchetto `weston` e `weston-simple-egl` non esisteva affatto.

⛔ `weston`, `glmark2-wayland`, `mpv` e `ffmpeg` **non sono in `provision-server.sh`**: stanno in
`provision-banco.sh`, un secondo script che il primo non chiama e non nomina. È la seconda metà
esatta di `LEZIONI.md` §2.5-bis — *«i banchi dipendono da pacchetti che il provisioning non
installa»* — riprodotta alla lettera un giorno dopo essere stata scritta.

#### 8. ⛔ Il banco stampava una misura di una scena che non era mai partita

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

#### 9. ⚠ Due script di ripristino della stessa macchina, due modi diversi di trattare `sudo`

`provision-banco.sh` si è fermato alla prima riga con *«sudo: a terminal is required»*:
`provision-server.sh` prende le credenziali con `sudo -v -S -p` dalla prima riga, questo usa
`sudo` nudo. Chi rimette in piedi la macchina da remoto — cioè sempre — trova il primo che
funziona e il secondo che no.

#### 10. ⛔ `kill 0` uccide il proprio gruppo di processi — e il banco spariva senza una riga

Nel banco di C1 la pulizia scriveva `kill ${PID_SCENA:-0}`. Quando la variabile non è ancora
definita — cioè se qualcosa fallisce **prima** di aprire la scena — diventa `kill 0`, che non
vuol dire «non uccidere niente»: vuol dire **uccidi tutto il mio gruppo di processi**, shell
remota compresa. Il banco terminava senza stampare **una sola riga**, e da fuori aveva l'aspetto
di un comando che non parte.

⚠ La forma generale è quella di §1.9 un'altra volta: il modo in cui un banco **fallisce** va
progettato quanto il modo in cui riesce.

#### 11. ⛔ Confrontato con la colonna sbagliata, il banco sembrava sbagliare di dieci fotogrammi

Il primo giro di C1 ha misurato KWin **in memoria** (49,67) e l'ha confrontato con i **59-60** di
`STUDI.md` §kde, che sono la colonna a **copia zero**. Per qualche minuto il banco è sembrato sbagliare;
stava rispondendo giusto a un'altra domanda. La tabella di `STUDI.md` §kde §5.7 ha due colonne, e a 1080p
dice 59,2 e 43,3.

⭐ **La cura è nel banco, non nella memoria di chi legge**: ora `00-c1-kwin.sh` prende la strada
come argomento e **stampa l'atteso** prima di misurare. Un banco che conosce il proprio atteso non
lascia il confronto a chi guarda.

#### 12-bis. ⛔ Un'etichetta che dichiarava una misura che il compositore non aveva mai onorato

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

#### 12. ⚠ Il controllo che dice «di chi è il tetto» era muto per un buffer

Alla cella di Mutter il registro della scena era **vuoto**, e sembrava che il client non avesse
stampato niente. Mancava `stdbuf -oL`: verso un file l'uscita è bufferizzata a blocchi, e alla
chiusura della scena i suoi fotogrammi al secondo restano nel buffer. ⭐ `banco-altri.sh` lo
`stdbuf` ce l'aveva già — la differenza fra i due file era il difetto.

**Con la cura** il controllo di `LEZIONI.md` §1.1 finalmente parla: il client disegna **60,0** in
ogni giro mentre Mutter ne consegna 36. **Il tetto è del compositore.** Senza questo numero,
quella frase sarebbe stata un'ipotesi.

#### E un difetto di misura che ho fatto io, mentre misuravo

Due volte in un'ora ho letto `$?` **dopo una pipe**, dove è lo stato dell'ultimo comando e non di
quello che interessava: una volta `COMPILAZIONE=0` mentre `gcc` non esisteva affatto. E una volta
`set -e` più `grep -c`, che esce 1 quando non trova niente, ha fermato uno script di controllo a
metà facendolo sembrare completo. Sono le stesse due forme di `LEZIONI.md` §2.3-bis, e vanno
scritte perché **non sono state pagate dal codice: sono state pagate mentre lo si certificava**.

---

### Le decisioni prodotte

| | |
|---|---|
| `DECISIONI.md` §4.6 | le capacità del codificatore Intel sono `[?]` ricavate dalla generazione del chip: **è qui che si confermano**, con `vainfo` |
| `DECISIONI.md` §4.6-ter | la GPU si sceglie con una regola udev, e negare il nodo lo nega a **tutta la sessione dell'utente** |
| `DECISIONI.md` §5-bis.0-ter | l'emulatore Android è **banco di lavoro, non strumento di misura** |
| `DECISIONI.md` §4.3-bis | essere *headless* su GNOME è un **requisito**, non una fortuna — la verifica è M2, e comincia da qui |

---

### Che cosa resta `[?]`

| | |
|---|---|
| ✅ ~~`/etc/fstab` vuoto~~ → **non è un debito: è un passo dell'utente** | *9 agosto 2026: «quando riavvio la macchina ci penso io alla cartella `/media`».* Il montaggio resta manuale per scelta, e `banchi/00-rimetti-macchina.sh` lo fa in un comando per chi non se lo ricorda. ⭐ **E il rischio vero non era dimenticare il montaggio** — quello si vede subito, perché non c'è niente — **ma misurare su una macchina rimessa a metà**: quello adesso lo prende il banco, che dice `GUASTO` invece di stampare uno zero (voci 1 e 8). La protezione sta nel programma, come vuole **I7** |
| ⚠ **i due script di ripristino** | `provision-server.sh` non chiama né nomina `provision-banco.sh`. Oggi si sa; fra un mese lo saprà solo chi c'era |
| `[?]` **il 49,67 di KWin in memoria** | contro il 43,3 dell'8 agosto. Tre differenze note, nessuna verificata come causa |
| `[?]` **la coda di Mutter** | la mediana degli intervalli è ferma a 33,3 ms su sei giri, ma il massimo va da 33,6 a 75,0. Da dove venga quella coda non è stato guardato |
| `[?]` **la Radeon negata** | `amdgpu_cs_ctx_create2 failed (-13)`: da capire se sia la regola udev di `DECISIONI.md` §4.6-ter. Non ostacola |
| ⏳ **l'ambiente Android** | SDK, `adb`, Desktop AVD e il telefono vero: non ancora toccati. ⛔ *Diceva «servono alla sonda della **fase 2**, non prima». **Corretto la notte del 9 agosto 2026**, rilievo **R3.14** della revisione del banco della fase 1: `DECISIONI.md` §1.6 ha tolto l'applicazione Android — quindi **SDK, `adb` e l'emulatore non servono più a niente** — e `PIANO.md` §1.2 ha spostato la sonda alla **fase 1**, «prima di tutto». **Il telefono vero invece serve, e serve prima**: è lo strumento di misura di S2, S3a e S5. Il censimento completo di quel che manca sta in §01-filo-nudo, «Le dipendenze»* |
| **il budget in pixel al secondo** | `vainfo` dice **quali** profili, non **quanti** pixel: il numero di sessioni è fase 10 |
| **il decodificatore HEVC dell'emulatore** | non si è riusciti a stabilire che ne esponga uno hardware — e non importa, perché nessun numero si dichiara lì |

---

### La revisione avversariale del banco

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

#### Le sette cose corrette subito, e sono quelle che fanno mentire il banco in silenzio

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

#### Un `[?]` del revisore chiuso a nostro favore

Sospettava che il **49,67** di KWin in memoria fosse una cattura a 720p etichettata 1080p —
ipotesi acuta, perché 49,6 è esattamente la cella 720p di `STUDI.md` §kde §5.7. **Smentita da un dato già
registrato**: quella corsa aveva stampato `formato negoziato: 1920x1080`. Il `[?]` sul 49,67 resta
aperto, ma con una causa candidata in meno invece che una in più.

#### Che cosa il revisore ha provato a rompere senza riuscirci

Vale quanto i rilievi, e va scritto: la guardia `t_inizio` **tiene** (nessun ingresso le fa
stampare una riga senza flusso attivo); il riconoscimento del socket nuovo di `00-c1-wlroots.sh`
non si lascia ingannare da GNOME, da KWin né da uno sway superstite; la trappola dei 15 caratteri
di `pgrep -x` non si ripaga in nessuno dei quattro file; e `sudo` con lo stderr rediretto non
compare da nessuna parte.

#### ⏳ I sedici rilievi non ancora curati, dichiarati invece che dimenticati

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

#### ⚠ E un difetto che ho fatto io mentre applicavo le cure

Ho caricato i quattro file corretti sul ferro con `... | tail -0` per non stampare il rumore di
`scp`: `tail -0` chiude la pipe subito, `scp` muore di SIGPIPE, **nessun file è partito** — e il
mio `echo "caricati"` lo ha dichiarato fatto. Il giro successivo ha misurato col binario vecchio e
i conti non tornavano. È la stessa forma delle due che avevo già scritto qui sopra — `$?` dopo una
pipe e `set -e` con `grep -c` — alla terza occorrenza in un giorno. ⛔ **La lezione non è
«ricordarsela»: è che il trasferimento va verificato dal lato che riceve** (`LEZIONI.md` §1.7),
che è esattamente quel che ho fatto subito dopo e che ha trovato il guasto in dieci secondi.

---

### Il giudizio dell'utente

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
   orologi a 60 che battono fra loro, cioè esattamente il meccanismo che `STUDI.md` §gnome §8.2 legge nel
   codice. La cura candidata (**M3**: negoziare alto e rinegoziare la sola cadenza) costa **zero
   righe di prodotto** e non è stata provata. È in `PIANO.md` fase 3.
   > ⭐ ⚠ *13 agosto 2026: **M3 è stata provata e il fatto riesce** — monitor 120, freno 90, `[M]`
   > **61,4**. ⛔ Ma il meccanismo scritto qui («due orologi che battono») **è sbagliato**, e quello
   > che lo sostituisce (una **quantizzazione** sui tick) è `[R]`, non `[M]`: la «legge verificata
   > su 13 punti» scritta il pomeriggio del 13 agosto **è caduta la sera stessa**, perché le due
   > celle della griglia portavano `scena_sul_mio_monitor: false`. ⇒ **M3 resta mezza**
   > (`STUDI.md` §gnome §13).*

⚠ La differenza fra le due frasi non è accademica: *«Mutter non va oltre 36»* chiude la questione,
*«Mutter non va oltre 36 finché nessuno separa i due orologi»* la lascia aperta a costo zero. Oggi
vale la seconda.

---

### ⛔⭐ R12-A.44 — l'utente su cui poggiava metà della fase 1 non lo creava nessuno

*11 agosto 2026. Trovato rispondendo a una domanda dell'utente — «devo creare un secondo utente
sul server?» — e la risposta interessante non era sul secondo.*

`prova` è l'utente con cui **B5, B6, B7 e B8** si autenticano, e con cui si verifica la pila PAM del
prodotto (servizio `remotix`, `SPECIFICHE.md` §4.2). ⛔ **Nessun file del deposito lo nominava.**
Era stato creato **a mano** il 10 agosto — `/home/prova` porta quella data — e viveva **dentro il
contenitore**, non sull'host: `getent passwd prova` da fuori esce 2, da dentro dà `1001`.

⇒ Rifacendo il contenitore, **quattro banchi su otto certificati** sarebbero diventati rossi per una
ragione che non è del prodotto. ⭐ È la forma più cara di falso rosso, perché manda a cercare il
difetto nel server.

#### Che cosa c'è adesso

`provision.sh` ha un passo **5-bis** che crea **tutt'e due** gli utenti dentro il contenitore, in
modo ripetibile, e che **verifica** che PAM li possa accettare — perché *«l'utente c'è»* e
*«l'utente si autentica»* sono due fatti, e il secondo è quello su cui i banchi poggiano.

| utente | uid | parola d'ordine | perché così |
|---|---|---|---|
| `prova` | 1001 | `parola-di-prova`, **fissa** | ⚠ **compromesso dichiarato**: quella stringa è il predefinito in una dozzina di banchi, e generarla oggi li romperebbe tutti in silenzio. Accettabile perché l'utente vive **dentro un contenitore** non esposto e non esiste su nessuna macchina di nessuno. ⛔ Il giorno che un utente di prova dovesse esistere su una macchina vera, va rifatto |
| `prova2` | 1002 | ⭐ **generata**, scritta in `/media/REMOTIX/credenziali-banchi` (0600) | **fuori dal deposito**, e non deve entrarci. *Deciso dall'utente l'11 agosto 2026.* Si genera **una volta** e poi si rilegge: rigenerarla a ogni giro vorrebbe dire che un banco fermato a metà non si può ripetere |

#### ⭐ E il secondo utente serve a due cose, non a una

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

#### ⚠ Quel che resta storto, e va detto

⛔ **I banchi prendono la parola d'ordine sulla riga di comando** (`--parola …`), quindi finisce in
`ps` e in ogni registro che catturi il comando. Per `parola-di-prova` è il compromesso di cui sopra;
⛔ **per la parola generata di `prova2` non lo è**, ed è la stessa forma curata oggi su `sonda/`
(R12-A.34). Chi userà `prova2` in un banco deve farle prendere un'altra strada.


> ### ⭐ Appendice — `banchi/prodotto/`, che viveva solo sul server
>
> *Era §00-ambiente, 60 righe. Entra qui il 16 agosto 2026 perché
> è materiale di banco della fase 0, e un LEGGIMI in una cartella di attrezzi è un
> documento che nessuno apre. ⛔ Testo intatto, titoli abbassati di due livelli.*

### `banchi/prodotto/` — quel che viveva **solo sul server**

*Recuperato l'11 agosto 2026, a codice fermo, prima di sincronizzare i due alberi.*

⛔ **Questi quattordici file esistevano in un posto solo**: `/media/REMOTIX/src/` sul server
192.168.0.2, che **non è un albero git** e non ha una copia da nessuna parte. Sono il lavoro della
notte del 10 agosto — la prima e unica accensione del prodotto `src/` — e nessun documento li
nomina. Un `tar` sbagliato, o una risincronizzazione con `--delete`, li avrebbe cancellati senza
che nessuno se ne accorgesse.

⚠ **Sono presi come stavano, senza toccarli.** Non sono ancora banchi: sono gli attrezzi usa-e-getta
di chi ha acceso il server quella notte, e i registri che ne sono usciti. Chi scrive il banco del
prodotto (punto 1 della sessione dell'11 agosto) li rifà nella forma che il progetto pretende —
scena dichiarata, controllo positivo, denominatore — e allora questi si buttano. **Fino a quel
momento sono l'unica prova che quel giro è avvenuto.**

---

#### ⭐ Il banco c'è, ed è `banchi/01-p1-prodotto.sh` — 11 agosto 2026, 04:55 UTC

*Aggiunto dopo il primo giro verde. ⛔ **Non si butta ancora niente**, e sotto c'è la riga che dice
esattamente quanto di questa cartella è stato sostituito e quanto no.*

| attrezzo | lo rifà `01-p1-`? | |
|---|---|---|
| `avvia-server.sh` · `spegni.sh` | ✅ **sì** | l'accensione, il pid, lo spegnimento con TERM e il controllo che TERM sia bastato stanno in `01-p1-dentro.sh`, con **la porta 7448 dichiarata** e i file in `/srv/src/tmp/p1-*` invece che sparsi in `/srv/src/` |
| `fumo.sh` | ✅ **sì, e corregge un difetto** | ⛔ `fumo.sh` ha **`PORTA=${2:-7447}`**: lanciato senza argomenti accende **il prodotto sulla porta dell'innesto**, e `bsslserver` è quello che 11 banchi su 14 si aspettano lì. `01-p1-` non prende la porta da un argomento: la 7448 è scritta dentro |
| `check-env.sh` | ✅ **sì** | quel che c'è nel contenitore lo dichiara il banco, riga per riga, invece di stamparlo e basta |
| `b11-fumo.py` | — | è di B11, non del prodotto |
| ⛔ `filo.sh` | ❌ **no** | è la **stretta di mano RCP** col cliente di prova di B3 e l'arbitro di B4. `01-p1-` si ferma prima del filo, e lo dichiara: si autenticherebbe, e tre parole d'ordine sbagliate mettono l'indirizzo fuori 12 ore (B0.3) |
| ⛔ `resto.sh` | ❌ **no** | rotazione del certificato, certificato dell'amministratore, ban + pagina + sblocco. ⚠ **E una sua gamba è già morta**: la riga 83 chiama `remotix --ban … --sblocca <ind>`, e quell'opzione **non esiste più** dal rilievo R12.1 — `[M]` l'11 agosto 2026: stampa la spiegazione ed esce **2**, e `resto.sh` non guarda lo stato d'uscita |

⛔ **Quindi questa cartella non si butta**: `filo.sh` e `resto.sh` restano l'unica traccia di come si
provano il filo e il ban contro il **prodotto**, e finché non esistono i banchi che li rifanno,
buttarli toglierebbe una descrizione senza sostituirla.

#### Gli attrezzi

| file | che cosa fa | data |
|---|---|---|
| `avvia-server.sh` | ⭐ **come il prodotto è stato acceso**: `remotix --indirizzo 0.0.0.0 --nome 192.168.0.2 --porta 7448 --certificati /srv/src/remotix-cert --pagina …/pagina.html --ban /srv/src/remotix-ban`, dentro il contenitore, con il pid su file. ⛔ **Porta 7448**, cioè non quella dell'innesto: i due server possono stare accesi insieme | 10 ago 23:05 |
| `spegni.sh` | lo spegne dal file del pid | 10 ago 23:07 |
| `filo.sh` (57 righe) | un giro di filo contro il prodotto | 10 ago 22:58 |
| `fumo.sh` (74) | la prova di fumo | 10 ago 22:52 |
| `resto.sh` (95) | il resto del giro | 10 ago 23:00 |
| `check-env.sh` (18) | che cosa c'è nel contenitore | 8 ago 22:20 |
| `b11-fumo.py` (45) | la prova di fumo di B11 | 10 ago 10:25 |

#### I registri, e sono misure

⛔ **Questi non si rifanno: sono numeri con una data.** Se una misura futura li contraddice, la
differenza si spiega — non si sovrascrive.

| file | che cosa contiene |
|---|---|
| `b8-campioni.jsonl` (15 kB) | i campioni del secondo fisso di B8 |
| `b8-fatti.jsonl` (25 kB) | i fatti del giro di B8 |
| `b12-esiti.jsonl` | gli esiti di B12 |
| `01-s1b-visite.jsonl` | le visite dell'orologio dei sette giorni di S1b (il verdetto è del 17-18 agosto) |
| `corpo.html` · `pagina-ban.html` · `pagina-dopo.html` | ⭐ **il corpo della pagina come il browser l'ha vista**, nei tre stati: normale, bannato, dopo lo sblocco. È la sola prova su disco che la pagina del ban di §4.4-bis è stata guardata da un motore vero |


---

<a id="01-filo-nudo"></a>

## Fase 1 — Il filo nudo

Aperta il **9 agosto 2026** · **Riscritta la sera del 9 agosto**, dopo due revisioni avversariali ·
⭐ **Chiusa l'11 agosto 2026**, sul giudizio dell'utente — la frase, con la scena e il registro, sta
in fondo a questo documento

> ⛔ **Questo documento si apre prima di sviluppare, e contiene i banchi** (`PIANO.md` §0.1). Le
> tabelle delle misure sono **vuote per costruzione**: si riempiono strada facendo, una riga alla
> volta, con la data e la scena. Un documento scritto dopo è un resoconto, e in un resoconto le
> misure si *ricordano* invece di essere *registrate*.

> ### ⛔ La prima stesura è stata revisionata prima di produrre un numero, e non ha retto
>
> Due revisioni avversariali con due lenti diverse — `fasi/rapporti/R3-revisione-banco-01.md` (il
> banco come strumento, **28 rilievi**) e `R4-revisione-banco-01.md` (la coerenza con quel che è
> già scritto, **16**). **44 rilievi: 38 `[R]`, 6 `[?]`, nessun `[M]`.** Nessuna delle due è verde.
>
> ⭐ **È il primo dei tre momenti di `PIANO.md` §0.4 che fa il suo mestiere**: il banco è il primo
> imputato, e questo è costato una riscrittura invece di tre fasi di misure avvelenate.
>
> **Le sei cure che hanno cambiato la forma del documento, non il dettaglio:**
>
> | | |
> |---|---|
> | **l'ordine era circolare** | tre misure della sonda pretendevano il server che il banco della libreria deve ancora scegliere. ⭐ **B2 adesso viene prima**, e la sonda si divide in *prima del filo* e *sopra il filo* — R3.4, R4.3 |
> | **cadeva sempre il controllo che dice *no*** | delle **undici** prove di controllo che i rapporti prescrivono per S1a, S2 e S4 ne erano sopravvissute **tre**, ed erano tutte del tipo che dice *sì*. Due erano già state bocciate da `R2` con l'istruzione *«curare prima di scrivere una riga di banco»* — R3.1 |
> | **il rigore puntava in un verso solo** | dodici violazioni verso il server, **nessuna verso la pagina**, mentre `RCP.md` §3 è scritta su *«un'implementazione RCP»*. ⭐ Nasce **B11** — R4.1 |
> | **i dispositivi non esistevano** | sei misure su nove pretendono ferro che nessun documento dichiara. ⭐ Nasce il capitolo delle **dipendenze**, prima dei banchi — R3.14 |
> | **la certificazione copriva 4 banchi su 12** | e i due scoperti — B3 e B7 — sono i banchi dei due difetti più cari di v1 — R3.7, R4.6 |
> | **sei cose prodotte non le guardava nessuno** | fra cui che **i due certificati siano due**, e che la parola d'ordine non finisca in un registro. ⭐ Nasce **B13** — R3.24 |
>
> ⚠ **E tre cure sono cadute fuori da questo file**, perché la stonatura era altrove: `RCP.md`
> §4.1-bis e §7.3, i controlli negativi nei banchi di `STUDI.md` §web, e la riga della fase 0 che manda la
> sonda alla fase 2. Sono elencate in fondo, sotto «Le cure fuori da questo documento».

---

### Che cosa deve produrre

La **stretta di mano di RCP su WebTransport**, dai due lati: il server in C e la pagina servita dal
server stesso. Niente video, niente audio, niente input.

**Che cosa vede l'utente, e giudica**: apre `https://192.168.0.2:7448` nel browser, digita utente e
password, e la pagina dice *«ammesso, sessione nuova, tela 1920×1080, **desktop sconosciuto**»*.
Oppure dice **perché no**, con una frase comprensibile e non un numero (`RCP.md` §8.2).

> ⚠ *Questa riga diceva* «`…:7447` … **desktop GNOME**» *— e il giro dell'utente dell'11 agosto 2026
> l'ha smentita in tutt'e due i punti, con il prodotto acceso davanti.* ⛔ **La 7447 è dell'innesto**:
> il prodotto sta sulla **7448**, e chi eseguiva questa riga alla lettera giudicava il banco invece
> del prodotto. ⛔ **E «GNOME» è una parola che la fase 1 non può dire senza inventarla**: la sessione
> grafica nasce alla fase 2, non c'è nessun compositore a cui chiedere, e `src/rcp.c` lo dichiara per
> iscritto — `SESSIONE` porta `desktop=sconosciuto`. ⇒ **A cambiare è l'atteso, non il codice**:
> era stato scritto prima che il prodotto esistesse. Prova e scena in
> `rapporti/GIUDIZIO-11-agosto.md`.

#### ⛔ Il confine della fase, e le quattro cose che produce senza sembrare

*Riscritto dopo R4.2, R4.5, R4.8 e R4.11: la prima stesura ne dichiarava una sola, e le altre tre
sarebbero nate senza banco.*

| | |
|---|---|
| **`SESSIONE`** | `stato` vale **sempre `NUOVA`**. La sessione grafica vera nasce alla fase 2, la sua vita e i tre orologi alla fase 5. ⛔ **E «sempre» si verifica** (B13): un ramo `RIPRESA` scritto per prudenza e mai provato è precisamente quel che questo riquadro esiste per impedire |
| ⛔ **la tela concessa** | **non** è «quella chiesta»: è quella chiesta **capata a `video.misura_massima`** se il client l'ha dichiarata, e comunque dentro i limiti e la parità di `RCP.md` §4.5. *Correzione R4.2: la riga precedente contraddiceva un DEVE, e il difetto sarebbe nato invisibile qui per presentarsi alla fase 2 come «il browser non apre il flusso» — cioè il sintomo di un'altra causa* |
| ⭐ **l'occupazione della sessione** | ⛔ la fase 1 produce **metà dell'invariante I2**, e va detto: per rispondere `GIA_ATTIVA_REMOTA` il server deve sapere che esiste una sessione di quell'utente con un client **vivo** attaccato. Quel che resta alla fase 5 sono **i tre orologi** (`DECISIONI.md` §4.5), non l'occupazione. *Senza questa riga B3 provava una cosa che nessuna fase dichiarava di produrre — R4.5* |
| ⭐ **le capacità che il server dichiara in `ECCOMI`** | `RCP.md` §4.3 le rende **normative**: chi non dichiara `pcm` e `8` si congeda con `NIENTE_IN_COMUNE`. Il server della fase 1 dichiara **`video.codec=hevc` · `video.profondita=8,10` · `audio.codec=pcm,opus` · `appunti.testo=si`** — cioè quel che il prodotto avrà, non quel che la fase 1 sa già fare. ⚠ **È una dichiarazione d'intenti, ed è onesta solo se qualcuno la verifica**: la fase 2 deve provare che il codec negoziato sia davvero quello prodotto, o la negoziazione mente da qui in avanti. *Senza questa riga il cliente di prova sarebbe diventato rosso applicando §4.3 alla lettera, e chi l'ha scritto avrebbe pensato di aver sbagliato lui — R4.8* |
| ⛔ **la pagina servita isolata fra origini** | `SPECIFICHE.md` §11.5: **è un vincolo di prodotto**, non una taratura del banco — cambia come il server serve **ogni** risorsa, e deciderlo dopo significa riconfezionare la pagina. La fase 1 è l'unica in cui il server acquista il mestiere di servirla. *Mancava del tutto — R4.11* |

---

## ⛔ Le dipendenze: che cosa serve, e che cosa oggi non c'è

*Capitolo nuovo, dal rilievo **R3.14**. La prima stesura scriveva nove righe di sonda dando per
esistenti dispositivi che nessun documento del progetto nomina — e §00-ambiente dichiara
quell'ambiente **non toccato**. Una dipendenza non dichiarata è una misura che non si fa, e questo
progetto l'ha già pagata due volte in un giorno (`weston` e i gruppi `adm`/`systemd-journal`).*

*Censito con l'utente la notte del 9 agosto 2026: **il telefono Android e il DeX ci sono, il mondo
Apple no**.*

| Serve a | Che cosa | C'è? |
|---|---|---|
| S2, S5, S3a | ⭐ **il telefono Android** con Chrome | ✅ **sì** — e non va configurato: si apre un indirizzo |
| S3a, S5 | ⭐ un dispositivo **DeX** (la lock esiste solo da **Android 16 QPR1**) | ✅ **sì** — ⚠ `[?]` **da verificare che sia almeno Android 16 QPR1**, o S3a misura l'assenza della lock e la scambia per una perdita di scorciatoie |
| ⛔ **S3a su Firefox** | **Firefox ≥ 151**: `requestFullscreen({keyboardLock})` è entrato nello standard l'8 maggio 2026 e Gecko l'ha spedito **nella 151** `[S]` | ⛔ **no**: il Firefox della macchina da cui si prova è la **140.0** `[M]` 9 ago. ⭐ *Trovato dalla regola B0.6 — annotare la versione esatta — al primo giro in cui è servita: `STUDI.md` §web §2 dichiara di aver letto Gecko **151-153**, e su questa macchina c'è tre versioni indietro. Chi misurasse S3a qui misurerebbe **l'assenza della lock**, e la scambierebbe per scorciatoie perdute* |
| S2 | un **PC collegato** per `chrome://inspect` — il controllo C, l'unico canale che risponde davvero | ✅ sì |
| S7 | sessione GNOME e `libei` | ✅ `banchi/00-sessione-gnome.sh`, `libei1` 1.3.901 `[M]` |
| tutti | il `devroot`, la macchina di prova, la cache dei pacchetti | ✅ fase 0 |
| B9 | `python3-aioquic` 1.2 | ⚠ `[M]` c'è, ma **che porti WebTransport lato client non è `[M]` da nessuna parte** (R3.21) |
| B10 | un **secondo utente** sul server, con parola d'ordine, che PAM sappia autenticare | ⛔ **no** — e ⛔ **va in `provision-server.sh`, non creato a mano**, o in un giorno è invisibile (`LEZIONI.md` §2.5-bis) |
| S2 | **cinque sequenze di prova** da `hevc_vaapi` (S2 §4.1), fra cui la rampa di grigio per i 10 bit | ⛔ no — dipendono dal codificatore, che è della fase 2 |
| ⛔ **S1a, B2** | un **Mac** con Safari 26.4, e un **iPhone/iPad collegato al Mac** col Web Inspector — su Safari non esiste `net-export` (S1 §4.3) | ⛔ **NO, e non si aggira** |
| ⏳ S3b | un **certificato vero con un dominio**: dietro l'eccezione il Service Worker non si installa `[R]`, quindi **la PWA non esiste** (R3.12) | ⛔ no — *rimandata* |

> ### ⭐ Safari non si misura in questa fase, ed è una decisione — non una mancanza
>
> **`DECISIONI.md` §1.8**, dall'utente il 9 agosto 2026: *Apple è un di più, non un obiettivo*.
> Non si procura un Mac, non si affittano dispositivi, non si monta un tunnel. **S1a esce dalla
> fase 1 e resta `[?]`.**
>
> ⛔ **E non è «Safari non è supportato»**: il codice è lo stesso per tutti e tre i motori, e la
> strada su Safari 26.4 è la stessa degli altri due. Non si spende per **verificarlo**.
>
> Le tre conseguenze, e nessuna si cura scrivendo codice:
>
> | | |
> |---|---|
> | **B2 perde un terzo del suo criterio** | *«tutti e tre i motori aprono la sessione»* diventa **due su tre**, e la libreria QUIC si sceglie **sapendo di Chrome e Firefox**. ⚠ Va scritto accanto alla scelta, o fra sei mesi sembrerà una scelta informata |
> | ⭐ **ma non blocca niente** | `serverCertificateHashes` è spedito in **Safari 26.4** `[R]`: iPhone e iPad hanno **la stessa strada** degli altri due. S1a decideva **una comodità** — se lì l'impronta si possa risparmiare — non se una piattaforma sia servibile (`RCP.md` §4.1-bis) |
> | ⛔ **e quel che resta scoperto va detto a chi installa** | finché nessuno prova su Safari, *«funziona su iPhone»* è **una deduzione, non una misura**. È la forma **E5**, e il posto dove non deve comparire è la documentazione del prodotto |
>
> ⚠ **Il giorno in cui un Mac ci fosse**, S1a si fa in un pomeriggio: i tre controlli sono già
> scritti qui sopra, e la pagina sonda è la stessa.

⚠ **E §00-ambiente e `PIANO.md` §1.2 non concordavano** su dove viva la sonda: la fase 0 la
mandava alla fase 2, il piano la mette *«prima di tutto»* nella fase 1. Chiarito con una nota datata
nel documento della fase 0.

---

## Il banco

⛔ **Scritto prima di sviluppare, e revisionato prima del prodotto** — `PIANO.md` §0.4.

### ⭐ L'ordine, e perché è quello

*Corretto da R3.4 e R4.3: l'ordine dichiarato era **circolare**. S1a, S6 e S4 pretendono un server
che parli WebTransport, cioè la cosa che B2 costruisce; e B2 pretende di sapere che Safari sappia
aprire la sessione, cioè la domanda di S1a. Chi eseguiva il documento nell'ordine scritto si
fermava alla prima riga della prima misura.*

| Quando | Che cosa | Perché lì |
|---|---|---|
| **1** | **le cinque misure indipendenti dal filo**: S1b · S2 · S3a · S5 · S7 | non toccano il server: si fanno subito, e S1b **va fatta per prima perché dura sette giorni** |
| **2** | ⭐ **B2 — il banco della libreria** | produce il **server minimo da cinquanta righe** su cui tutto il resto poggia, e chiude `DECISIONI.md` §6.4 |
| **3** | **le due misure che vivono sopra il server minimo**: S1a · S6 | ⚠ e se la candidata poi cambia, **si rifanno**: un controllo positivo fatto su un motore diverso da quello del prodotto è la forma **E10** |
| **4** | i banchi del filo: **B3-B13** | provano il prodotto contro `RCP.md`, mai contro sé stesso |
| ⏳ **rimandate** | **S4** → fase 3 · **S3b** → dove arriverà il suo certificato vero | S4 non è «senza prodotto»: vuole codifica, trasporto e decodifica — ⛔ **e una riga di protocollo, da decidere adesso** (vedi sotto) |

> #### ⛔ La riga di protocollo che S4 pretende, e la finestra che si chiude
>
> S4 §5.3 lo dichiara: la marca del banco — **il rettangolo 16×16 e il comando che lo cambia, con
> il ritardo `N` iniettabile del controllo decisivo** — è *«un'estensione di protocollo … va
> scritta in `RCP.md` come **funzione di banco**, non improvvisata nel codice di prova»*.
>
> ⛔ **E `RCP.md` §9 chiude la finestra dei tipi nuovi «dal primo byte scritto in poi».** Se quel
> messaggio non entra **prima** che il server esista, entrerà come deroga a una regola che protegge
> le implementazioni — cioè come il primo strappo, fatto da noi, alla regola che abbiamo scritto
> ieri. **Aperta in `RCP.md` §12, da chiudere prima del primo byte** (R3.4).

### B0 — Le regole che valgono per tutti i banchi

*Sezione nuova: cinque rilievi diversi (R3.3, R3.8, R3.16, R3.17, R3.18, R3.23) dicevano la stessa
cosa in cinque posti — che il banco non dichiara da che stato parte, e che quel che sopravvive fra
una prova e l'altra falsa la prova successiva.*

| # | La regola | Da dove viene |
|---|---|---|
| **0.1** | ⛔ **ogni banco dichiara e VERIFICA il proprio stato iniziale** prima di partire, come `00-c1-kwin.sh` verifica che il socket di KWin non ci sia più. Un banco che non sa da che stato parte **misura la storia della macchina** | R3.16 |
| **0.2** | ⛔ **e lo stato che sopravvive è più di uno**: l'eccezione concessa sul certificato della pagina *(che S1a e S1b **misurano**)*, il certificato di sessione già ruotato da B3, **la sessione creata al giro prima** *(che a meno di 30 s fa dare `GIA_ATTIVA_REMOTA` alla prima connessione del giro nuovo — rosso su codice giusto)*, il permesso `clipboard-read`, e ⛔ **il ban di §4.4-bis, che dal 10 agosto 2026 sta su file e quindi sopravvive anche al riavvio del server** — cioè lo stato che sopravvive di più fra tutti | R3.16 |
| **0.3** | ⛔ **l'isolamento fra banchi, e dal 10 agosto 2026 è il vincolo più duro del capitolo**: il conto dei tentativi è **per indirizzo**, e tutti i banchi partono dallo stesso indirizzo. B7 fallisce un tentativo, B8 ne fallisce tre, **e da lì in poi ogni banco di quella macchina è fuori per dodici ore** — compresi B10, B11 e chi sta sviluppando. ⚠ *La riga vecchia diceva «i contatori sono per nome e per indirizzo … si cura cambiando indirizzo o **dichiarando l'attesa**»: con il ban di `DECISIONI.md` §1.9 l'attesa è mezza giornata, e quella cura è morta.* ⛔ **La cura è il comando di sblocco** (§4.4-bis), chiamato fra un banco e l'altro — ⛔ **mai dentro il giro di B8**, o B8 non prova più niente. E ogni banco che lo chiama **lo dichiara**, o «il ban non è scattato» e «qualcuno l'ha tolto» hanno lo stesso aspetto. ⭐ **Lo strumento è `banchi/01-b8-sblocca.py`** — non è un pezzo di B8 — e parla un **socket Unix `0600`**: `SBLOCCA <indirizzo>` → `TOLTO` / `NON-BANNATO`, `PING` → `PONG`. ⛔ Il `PING` **è il denominatore di questa regola**: senza, «il ban non è scattato» e «lo sblocco non è mai arrivato a nessuno» hanno di nuovo lo stesso aspetto. ⚠ *Dalla notte del 10 agosto 2026 **i due server parlano lo stesso protocollo**: prima il prodotto aveva un'opzione `remotix --sblocca IND`, cioè un secondo processo che riscriveva il file mentre il ban vive nella memoria di chi serve — **usciva con 0 dicendo di aver funzionato**, e al primo ban successivo di chiunque altro il ban tolto **tornava anche su disco** (rilievo **R12.1** di `fasi/rapporti/R12-D-cuciture.md`, e l'analisi era scritta per esteso in `01-b3-rcp-innesta.py` da mesi prima che il difetto nascesse). Curato nel codice la stessa notte: `src/comando.c`.* ⛔ **E resta da fare la metà che nessuno ha fatto**: puntare `01-b8-sblocca.py` al prodotto, che oggi non è mai stato provato | R3.8 |
| **0.4** | ⛔ **l'atteso lo confronta il banco, non chi legge**: si stampa *e* si confronta, e lo stato d'uscita è quello del **confronto**. ⚠ E attenzione al punto contro la virgola: `"60"` contro `"60,0"` dà rosso su codice giusto, ed è il difetto ancora aperto di `00-c1-kwin.sh` | R3.18, R3.23 |
| **0.5** | ⛔ **dopo ogni prova che deve far cadere la connessione, il server deve essere ancora lì**: una connessione nuova che arriva fino a `SESSIONE`. «Cade sempre» è soddisfatto anche da un server **ucciso dal nucleo** | R3.3 |
| **0.6** | ⛔ **la versione esatta del browser si annota**, ogni volta. *«Un risultato senza versione, fra sei mesi, non vale niente»* (S1 §4.5) — e questo è il capitolo che invecchia in mesi | R3.16 |
| **0.7** | ⛔ **i due lati si sincronizzano con marcatori, non con `sleep`** — e il precedente in casa **non** è un esempio da copiare: `banco.sh` della fase 0 ha ancora il suo `sleep 2.5` | R3-§4.9 |

---

### Gruppo 1 — Le cinque misure indipendenti dal filo

⛔ **Tutte sul dispositivo vero, mai su un browser di comodo** (`DECISIONI.md` §5-bis.0-ter).
⭐ **E ogni riga porta il rimando puntuale al posto dove vive la procedura** — ⛔ **che per tre di
loro non è un rapporto, e va detto**: `S1a`, `S1b`, `S2`, `S3a`, `S3b` e `S4` sono nate in `STUDI.md` §web
§7 e **non compaiono in nessuno dei quattro rapporti**, dove le prove si chiamano in quattro modi
incompatibili e due rapporti usano `P1…Pn` per cose di natura opposta (R3.28). ⛔ **`S5`, `S6` e
`S7` invece non sono nate lì**: `[M]` 11 agosto 2026, `grep -cE '\bS5\b|\bS6\b|\bS7\b' web.md` →
**0**, con il controllo positivo accanto (le altre sei etichette compaiono **24** volte nello stesso
file). Sono nate **in questo documento**, dalle domande di `SPECIFICHE.md` §6.1-bis (S5),
`RCP.md` §5.3 (S6) e `RCP.md` §7.3 (S7), e rimandano **lì** perché non esiste un rapporto che le
contenga.

> ⚠ *Questa riga diceva* «le etichette `S1a…S7` **sono nate in `STUDI.md` §web §7**» *— e §7 di `STUDI.md` §web ne
> elenca **sei**, non nove. ⛔ Era la riga che **stabilisce la convenzione dei rimandi**, e le due
> righe che la seguono in questo stesso capitolo ne erano la smentita: S5 rimanda a
> `SPECIFICHE.md §6.1-bis`, S7 a `RCP.md §7.3` — cioè non a un rapporto. Corretta l'11 agosto 2026,
> rilievo **R12C.10**. ⭐ E costa poco e vale: tre misure su cinque del Gruppo 1 adesso hanno una
> provenienza, cioè chi le esegue sa da quale lettura sono nate e quale domanda chiudono.*

⛔ **E dalla notte del 10 agosto gli esiti hanno un posto solo dove vivono**:
`web/rapporti/S-esiti-sonda.md` — la scena, l'ora in UTC, i
registri, e **la ricontata dell'11 agosto che dice quali numeri hanno una provenienza su disco e
quali no**. ⚠ *Fino all'11 agosto quel rapporto non era nominato da **nessuno** dei dieci documenti
(rilievo **R12C.15**): l'unico posto in cui i numeri di quella notte vivevano non era raggiungibile
da nessuna strada di lettura, e la sola via per sapere che esisteva era aprire a caso una cartella di
rapporti.*

#### S1b — quanto dura l'eccezione su Chrome  ·  ⏳ **AVVIATA il 10 agosto 2026** · `banchi/01-s1b-eccezione.sh`

> ⚠ *Questa riga rimandava a* `S1 §4.2 P5`. ⛔ **P5 non è questa prova**: è la prova del *contesto
> sicuro* (Service Worker, keyboard lock, appunti, pointer lock, `isSecureContext`), e **in S1 non
> esiste nessuna prova di banco sulla durata** — i sette giorni sono **solo sorgente letto** (S1
> §3.1), e la sola persistenza messa a banco è quella di Safari (S1 §4.3). ⇒ *Non c'era una
> procedura da seguire: ce n'era una da scrivere.* Chi apriva S1 §4.2 P5 per eseguire S1b trovava
> cinque chiamate di API e nessuna procedura, e la spiegazione più naturale è *«ho sbagliato io a
> leggere»*. Corretto l'11 agosto 2026, rilievo **R12C.9** — ed è il terzo rimando di questa forma
> che il progetto paga (R11.2, R11.18).

| | |
|---|---|
| **si misura** | dopo quanti giorni l'avviso ricompare sulla pagina |
| **atteso** | **7 giorni** — `[S]`→`[R]` da `kCertErrorBypassExpirationInSeconds = 604800`. ⚠ **La promozione di marca è dichiarata qui**: `STUDI.md` §web §8 la teneva ancora `[?]`, e le due righe di `STUDI.md` §web si contraddicevano (R4.14) |
| ⛔ **il controllo** | **l'impronta del certificato DELLA PAGINA, letta all'inizio e alla fine, deve essere la stessa.** Senza, un certificato rigenerato da un riavvio fa scrivere «l'eccezione è durata quattro giorni» e la frase che si dirà all'utente nasce sbagliata (R3.15) |
| ⚠ **il calendario** | è l'unica misura che richiede **sette giorni di tempo reale**, e la fase non si chiude prima. Se si accelera spostando l'orologio della macchina, ⭐ il controllo diventa *«a sei giorni l'eccezione c'è ancora»* — che è un controllo vero |
| ⏳ **giorno 0 preso, l'orologio è in moto** | `[M]` **2026-08-10T21:10:01Z** — **Chrome 151.0.7922.108**, profilo persistente in `~/.remotix-s1b/profilo`, schermo finto `Xvfb :77 1280x1024x24`, sito `https://192.168.0.2:7452`, certificato **ECDSA P-256 a 3650 giorni** con SAN `IP Address:192.168.0.2` (⛔ **non** `localhost`, che in Chrome ha una corsia riservata, e ⛔ **non** in navigazione privata). Registro `banchi/01-s1b-stato.jsonl`. **Il verdetto è del 17-18 agosto 2026** |
| ⛔ **e un numero che NON regge** | Chrome si è segnato la scadenza **2026-08-17T21:09:47.889Z** (`[M]` sul valore grezzo `13431474587889370` µs dal 1601, che è su disco; la conversione è ricalcolata a mano e **dichiarata** tale). ⚠ *Il rapporto scriveva «cioè **604 800 s esatti** dalla concessione», due volte: fra i due numeri che pubblicava ci sono **604 786,889 s**. Mancavano **13,111 s**, e «esatti» era falso in tutt'e due i punti — rilievi **A26** e **R12.6**.* ⛔ **Non si arrotonda e non si rimisura** (rifare il giro «avvia» azzererebbe l'orologio dei sette giorni): che siano 604 800 s dal **clic** è tornata `[?]`, perché **l'istante del clic non l'ha registrato nessuno** |
| ⭐ **quattro controlli, e il quarto è nato dopo** | l'impronta letta **dal filo** dev'essere quella del giorno 0 · un profilo **nuovo** deve vedere l'avviso · il sito dev'essere vivo · ⭐ **il canale di lettura dev'essere certificato** (rilievo **A27**, 11 agosto): il verdetto poggiava su `ssh` + un `grep` che, se rotti, rispondevano **NO** — e il controllo che dice *no* leggeva **lo stesso canale**, quindi si dichiarava passato da sé. Il giro che ne usciva stampava *«a N giorni l'eccezione NON c'è più: è questo il numero di S1b»* — ⛔ **il numero della misura, in verde, da uno strumento muto**, e su un orologio da sette giorni se ne sarebbe accorto qualcuno **fra una settimana** |
| ⛔ **che cosa può rompere l'orologio** | rigenerare `/media/REMOTIX/s1b-certificato/s1b-pagina.pem`, cancellare `~/.remotix-s1b/`, o far cadere la data del server. I primi due li vede il controllo dell'impronta; ⚠ **il terzo no** |

#### S2 — HEVC Main10 in hardware, sul telefono vero  ·  `S2 §4.2 misure 1,2,4 · §4.4 controlli A,B,C`

| | |
|---|---|
| **si misura** | portata a saturazione (4K60 Main10), **canarina di CPU** in un worker, **decadimento su dieci minuti** |
| ⛔ **l'atteso NON è «`[S]` sì da Chrome 108»** | quel `[S]` riguarda il **supporto in WebCodecs**, non l'hardware: scriverlo come atteso di una misura di *hardware* mette **E1 nella casella dell'aspettativa**, e le prove indirette si leggono con indulgenza quando l'atteso è già scritto. **L'atteso è `[?]`** (R3.13, R4.13) |
| ⛔ **i tre controlli, non uno** | **A**: VP9 `prefer-software` **dev'essere dichiarato software** · **B**: VP9 `prefer-hardware` **dev'essere dichiarato hardware** — *era caduto, ed è quello che dice no* · **C**: ⭐ **`is_software_codec` letto via `chrome://inspect`** |
| ⭐ **e il canale diretto esiste** | su Android, `media_codec_video_decoder.cc` registra `is_software_codec` col nome che arriva da `MediaCodec.getName()`. **Il browser sa e non risponde *da JavaScript*** — ma il banco non è JavaScript: il banco è chi guarda (`LEZIONI.md` §1.11 regola 2). Rinunciarci per tre prove indirette, sull'uso primario, era una scelta non dichiarata (R3.13) |
| ⛔ **gli esiti sono tre** | ≥ 90 fps ⇒ hardware · ≤ 30 ⇒ software · **in mezzo: verdetto sospeso**. La prima stesura ne aveva due, dove il rapporto ne prevede tre |
| ⚠ | su iPhone il canale diretto non esiste, e lì le tre indirette restano l'unica strada |

#### S3a — la tastiera, nei tre stati  ·  `S3 §4.2 (quattro controlli) · §4.3 (gruppi A-E) · §4.4`

⛔ **La domanda non è «arriva?» ma «arriva *e basta*?»** — gli stati sono tre: *consegnata* ·
**consegnata *e* riservata** · *non consegnata*. Il secondo è il peggiore (`SPECIFICHE.md` §7.3-bis,
O8).

| | |
|---|---|
| ⛔ **il difetto che invertiva la misura** | `Ctrl+W` su DeX: la pagina riceve il `keydown` **e** il browser chiude la scheda. Se il registro vive nella pagina, **la chiusura porta via il registro**: il banco scrive «non consegnata», cioè **lo stato opposto** — e dichiara innocuo il caso pericoloso (R3.11) |
| ⛔ **la cura, già scritta nel rapporto** | S3 §4.3 ordina le undici combinazioni **dalla meno rischiosa alla più rischiosa, una per volta**, con `Ctrl+T`, `Ctrl+N` e `Ctrl+W` **ultime e col registro già copiato fuori dal dispositivo**. Era caduta la sola riga che rende la misura possibile |
| ⛔ **i quattro controlli, prima di ogni sessione e a ogni motore** | che una battuta **nuda** arrivi *(senza, ogni «non è arrivata» è ambiguo fra «il browser se l'è tenuta» e «il banco era sordo»)*; che arrivi una combinazione **con modificatori**; che gli **appunti in uscita** funzionino; ⛔ e che lo schermo intero **non** sia entrato con `F11` — perché con `F11` **la lock non esiste e non lo dice**, e tutte le prove che seguono non valgono niente |
| ⚠ **e «la sessione»** | alla fase 1 **non c'è canale di input**: qui il ricevente è **la pagina**. La formulazione precedente mandava chi scrive il banco a cercare qualcosa che non esiste |

#### S5 — la tela che il client dichiara  ·  `SPECIFICHE.md §6.1-bis · DECISIONI.md §5.0-quater`

| | |
|---|---|
| **si misura** | il numero che la pagina dichiarerebbe in `ATTACCA`, a zoom **100 %** e **150 %**; e che cosa risponde `screen` **su DeX** |
| ⛔ **il controllo di prima era rosso sul codice giusto** | diceva *«i due numeri devono differire»*. Ma la tela **giusta** è lo schermo in pixel fisici, e la ragione scritta qui era: *«`screen.width` cala di un terzo, `devicePixelRatio` sale di un mezzo, **il prodotto resta**»*. Una pagina scritta bene dava **1920 e 1920** ⇒ rosso, e chi lo leggeva sarebbe andato a rompere la pagina finché il numero non si muoveva — cioè a **scrivere** il difetto che `DECISIONI.md` §5.0-quater voleva evitare (R3.10) |
| ⭐ **il controllo giusto** | la tela dichiarata a 100 % e a 150 % **deve essere la stessa**, e **deve coincidere con la risoluzione fisica letta fuori dal browser**, nelle impostazioni del dispositivo. Due strumenti diversi sullo stesso fatto |
| ⛔⛔ **MISURATO, e la ragione qui sopra è FALSA su Chrome** | `[M]` **10 agosto 2026**, registro `banchi/01-s5-esiti.jsonl` (due giri identici, 23:13 e 23:14), schermo **Xvfb 1920×1080×24** con `xdpyinfo` a confermarlo da fuori. **Chrome 151.0.7922.108** a zoom 150 %: `screen` resta **1920×1080** e `dpr` sale a 1,5 ⇒ tela **2880×1620**, del **50 % più grande** di quella che esiste. **Firefox 140.13.0esr** a 150 %: `screen` cala a **1280×720** ⇒ tela **1920×1080**, invariante. ⛔ *«Il prodotto resta»* **resta su un motore su due**, e la formula di `SPECIFICHE.md` §6.1-bis non regge su Chrome. ⚠ Corretto l'11 agosto 2026, rilievo **R12C.8** — e il difetto è **di prodotto, non di banco** |
| ⭐ **ed è il controllo giusto che l'ha trovato** | il controllo vecchio (*«i due numeri devono differire»*) sarebbe stato **verde su Chrome e rosso su Firefox**: avrebbe premiato il motore rotto. È la dimostrazione, su un caso vero, che la cura di R3.10 valeva |
| ⚠ **e metà di S5 non è misurata** | il **DeX** non c'era. *«Il Chrome del portatile lo fa»* non dice niente del Chrome del telefono — forma **E10**. La pagina è la stessa (`01-s5-pagina.html`): il giorno che il DeX c'è, si apre quell'indirizzo e si legge la riga |
| ⛔ **e la terza domanda non è chiudibile con una misura** | *«l'arrotondamento può produrre un numero dispari?»* — su un dispositivo si osserva un numero; se è pari **non se ne ricava che i dispari non esistano** (`LEZIONI.md` §1.3). La protezione va **nel programma**, dove **I7** la vuole: la pagina arrotonda al pari per difetto. La misura può solo trovare un positivo |

#### S7 — da che parte gira la rotella  ·  `RCP.md §7.3`

| | |
|---|---|
| **si misura** | si inietta `+120` con `libei` in una sessione GNOME (`banchi/00-sessione-gnome.sh`) e si guarda da che parte va la pagina |
| ⭐ **il controllo** | si inietta anche **`-120`**: se la pagina va dalla stessa parte, non si sta misurando il segno. ⭐ *È il controllo meglio scritto della prima stesura, e resta* |
| ⛔ **il controllo che mancava** | si rifà **con `natural-scroll` nei due stati**: se il segno cambia, il numero che finirebbe in `RCP.md` §7.3 è **il segno di una gsetting della sessione di prova**, e il sintomo per l'utente è *«la rotella va al contrario»* su metà delle installazioni. Forma **E11** (R3.25) |
| ⭐⭐ **MISURATA — e il server deve INVERTIRE l'asse verticale** | `[M]` **10 agosto 2026, 20:59:27→20:59:57 UTC**. `ei_device_scroll_discrete(0, **+120**)` → l'evento `wheel` porta **`deltaY = +114`** e la pagina **scende**, cioè va verso la fine del documento; con **−120**, `−114` e sale. `RCP.md` §7.3 fissa l'altra metà — *il client manda `+120` perché l'utente ha girato **in su*** — quindi ⛔ **le due convenzioni sono opposte e il server inverte il segno**. Iniettando il valore com'è, lo schermo remoto scorrerebbe al contrario per **ogni** utente. ⇒ **`RCP.md` §7.3 è chiusa l'11 agosto 2026**, rilievo **R12C.7** |
| **la scena, per intero** | macchina di prova **192.168.0.2**; sessione GNOME senza monitor (`banchi/00-sessione-gnome.sh`), `gnome-shell --headless --no-x11 --virtual-monitor 1920x1080`, **libmutter 48.7-0+deb13u1**, **libei 1.3.901**; la pagina in **Firefox 140.13.0esr** in `--kiosk`, `dpr` 1, documento posizionato a 8 000 px dal bordo. Registro: `banchi/01-s7-esiti.jsonl`, due giri (`7sd0u7jv`, `oq7jqrdv`) |
| ⚠ **e i controlli non valgono tutti uguale** | `[M]` **nel registro**: il segno opposto, e i due strumenti che concordano (`deltaY` e `scrollY`). ⚠ **A metà**: `natural-scroll` nei due stati — i due giri ci sono e danno lo stesso segno, ⛔ **ma quale giro fosse quale stato non è nel registro**, l'etichetta stava solo a schermo. ⛔ **Non ritrovabile**: che `ei_device_scroll_delta` abbia lo stesso verso — visto, non consegnato |
| `[?]` **e la domanda che resta** | §7.3 vincola **cinque** desktop e la misura è su **Mutter**. Se `libei` normalizza, il numero vale ovunque; se normalizza il compositore, la fase di KDE (la 11) troverà un segno diverso su KWin e non saprà se correggere il protocollo o il server. ⛔ *«Non chiusa»* e *«non misurata»* sono due stati diversi, e questo è il primo: il banco è **rieseguibile su KWin senza cambiare una riga della pagina**. ⚠ La fase 0 ha misurato **tre** famiglie in un pomeriggio: qui la stessa domanda ha una risposta sola |
| ⚠ **e un numero che NON va nel protocollo** | uno scatto (120 unità) vale **114 pixel** su Firefox+Mutter, cioè tre righe. È il fattore di conversione di **quella coppia**, non una costante di RCP: si annota e non si mette in nessuna formula |
| ⚠ **e la lezione citata era quella sbagliata** | il banco della rotella di v1 è costato **una stringa di registro cercata male** (`LEZIONI.md` §2.3), non una tabella col segno sbagliato. Citando la lezione sbagliata **la si perde nel punto in cui si applicherebbe** (R4.15) — la frase è di `RCP.md` §7.3, ed è corretta lì |

---

### Gruppo 2 — B2, il banco della libreria: quale QUIC arriva fino a WebTransport

⛔ **Viene prima di S1a e S6, ed è la cosa che chiude `DECISIONI.md` §6.4** — con un banco davanti,
non su carta. Il criterio è cambiato il 9 agosto: non basta che la libreria parli QUIC, deve
portare **HTTP/3 e WebTransport lato server**, più un ascoltatore **TCP** per la pagina.

**La prova**: un server minimo — cinquanta righe, che si buttano — che accetta una sessione
WebTransport su `/rcp/1`, aperta da **un browser vero**, con l'impronta pubblicata nella pagina.

> #### ⭐ Il censimento del 9 agosto notte, prima di scrivere una riga
>
> *Punto 0 della ricetta, e ha cambiato la domanda.* ⛔ **Nessuna delle due candidate originali
> porta WebTransport lato server**: danno le fondamenta — extended CONNECT, datagram, capsule — e
> non lo strato di sopra. ⭐ **E sono spuntate due candidate che non erano nell'elenco**, una delle
> quali (`lsquic`, in C) **ha WebTransport server dietro un flag di compilazione**.
>
> Il censimento completo, con le marche, sta in `DECISIONI.md` §6.4 — qui non si copia.
> ⛔ **Ed è tutto `[S]` e `[R]`: letto, non misurato.** Serve solo a decidere **a chi vale la pena
> scrivere le cinquanta righe**.

| Candidata | Sul ferro | Che cosa si prova |
|---|---|---|
| ⭐ **`ngtcp2` + `nghttp3`** (MIT, C) | ✅ **costruite dai sorgenti** — `ngtcp2` 16.11.0, `nghttp3` 1.18.90, sullo stesso BoringSSL `[M]`, **e il loro `bsslserver` gira** | ⭐ **passa il criterio dell'SNI** `[M]` 10 ago. Resta da misurare quanto pesa lo strato WebTransport sopra |
| ⭐ **`quiche`** (BSD-2, API C) | ✅ **costruita**, ma alla **0.28.0**: la 0.29.3 pretende `rustc` **1.88** e Trixie ne ha **1.85** `[M]` | ⭐ **passa il criterio dell'SNI** `[M]` 10 ago. ⚠ Porta un costo di **catena di strumenti**, non di QUIC — `DECISIONI.md` §6.4 |
| ⛔ **`lsquic`** (C) | ✅ compilato, **e il collante scritto** (333 righe) `[M]` | ⛔ **ELIMINATA**: in modalità HTTP/3 pretende **SNI** per trovare il certificato, e chi si collega a un **indirizzo IP** non lo manda. È il caso primario del prodotto — `DECISIONI.md` §6.4 |
| ⚠ **`libwtf`** (C su MsQuic) | ⛔ niente | *ultima della fila*: porta dentro una seconda pila QUIC, e ha una **licenza che si contraddice** |

**L'atteso, che la prima stesura lasciava vuoto** (R3.23):

| | |
|---|---|
| **passa** | la sessione si apre su **Chrome e Firefox**, e la pagina riceve un byte dal server. ⛔ **Erano tre motori**, e Safari esce perché non c'è un Mac (vedi «Le dipendenze»): la scelta della libreria si fa **sapendo di due su tre**, e questa riga esiste perché fra sei mesi non sembri una scelta informata |
| ⛔ **e cinque proprietà si verificano qui**, perché sono della libreria e nessun altro banco le guarda | **datagram abilitati** sulla connessione HTTP/3 (§2.2) · **niente 0-RTT** (§2.3) · **migrazione non disabilitata** (§2.3) · **`max_idle_timeout` = 30 s imposto dal server** (§2.2) · **`allowPooling` a `false`** (§4.1-bis) |
| ⛔ **e una che serve a B3** | che il banco **possa cambiare `max_idle_timeout`**: senza, la riga dei 30 secondi di B3 non è distinguibile dal trasporto (R3.19). È il tipo di cosa da decidere **scegliendo la libreria**, non scrivendo B3 |
| **il criterio di scelta** | ⚠ *«il numero di righe che restano a noi»* non è un atteso: si conta il **collante misurato**, candidata per candidata, e il numero si scrive. Senza, la scelta si fa a giudizio |

⛔ **Il sintomo di 0-RTT acceso non esiste**: `CREDENZIALI` si può ripetere, e nessun banco
funzionale lo vede mai. Le librerie QUIC lo offrono **per impostazione predefinita**.

---

### Gruppo 3 — Le due misure che vivono sopra il server minimo

#### S1a — l'eccezione su Safari copre WebTransport?  ·  `S1 §4.2 P1, controlli P2-P4`

| | |
|---|---|
| **si misura** | su **Safari macOS e iOS separati**: una sessione WebTransport dietro la sola eccezione del certificato |
| ⛔ **i tre controlli, non uno** | **P2** la connessione **con l'impronta pubblicata deve riuscire** — *stesso browser, stessa pagina, stesso giro* · **P3** ⛔ **con l'impronta sbagliata di un byte deve FALLIRE** · **P4** con un certificato a **30 giorni** deve fallire **per durata** |
| ⛔ **perché P3 è quello che mancava** | senza, una pagina che guarda **la promessa sbagliata** — considera «riuscita» la costruzione dell'oggetto invece di attendere `ready` — fa riuscire **anche** la prova con l'impronta storpiata, e il banco scrive un `[M]` falso *«su Safari l'eccezione copre WebTransport»* **contro due `[R]` letti nel codice di Chromium e di Gecko** (R3.1). S1 §4.4: *«solo con P2 verde e **P3 rosso** il risultato di P1 significa qualcosa»* |
| ⚠ **che cosa decide** | **una comodità, non una piattaforma**: `serverCertificateHashes` è spedito anche in **Safari 26.4** (`STUDI.md` §web §3.1) — *la prima stesura citava `RCP.md` §4.1-bis a sostegno, e §4.1-bis diceva il contrario perché non era stata aggiornata. Curata (R4.4)* |

#### S6 — quanto porta davvero un datagram  ·  `RCP.md §5.3`

| | |
|---|---|
| ⛔ **non è una grandezza del motore** | lo decide **il cammino** — la MTU più piccola fra i due estremi meno le intestazioni — non il browser. Il motore decide solo che cosa **dichiara** l'API, che è la cosa che la riga stessa diceva di non credere: attribuirlo al motore è **E2**, due misure diverse sotto la stessa etichetta (R3.22) |
| ⛔ **quindi si dichiara il percorso accanto al numero** | come la fase 0 dichiara la scena accanto a ogni fotogramma al secondo. E si misura sul percorso **peggiore che si intende servire** — LTE, o una VPN a MTU 1400 — **non su quello comodo** |
| **il controllo** | si spedisce un datagram di quella misura esatta e **si verifica che arrivi dall'altra parte**, non che l'API lo accetti |
| ⭐ **e se il numero deve essere un tetto di protocollo, non si misura affatto** | si prende il **minimo garantito da QUIC**, che è quel che i **972 byte** del PCM già fanno. Misurare in LAN e alzare il tetto significa spedire audio che l'utente vero non riceve — ⛔ e il PCM è **il controllo positivo di Opus**: si ripiegherebbe su una strada che non esiste |

---

### I banchi del filo

#### B3 — la stretta di mano su DUE connessioni, e una terza con la chiave cambiata

⛔ In v1 un certificato condiviso uccideva il server **alla seconda** connessione, e una prova a
collegamento singolo **resta verde per sempre** (`LEZIONI.md` §2.1).

| | Atteso |
|---|---|
| **1ª connessione** | stretta di mano completa fino a `SESSIONE` |
| **2ª dopo la chiusura della prima** | ⛔ **identica alla prima.** Se il server muore, o se la seconda fallisce dove la prima è passata, il difetto è **suo** |
| **2ª mentre la prima è viva** | `CONGEDO(GIA_ATTIVA_REMOTA = 0x0F)` verso **chi arriva**, verificato **dal lato che riceve**, e ⛔ **si controlla quale delle due sopravvive** |
| **la 2ª dopo il silenzio della 1ª** | ⛔ **35 secondi con `max_idle_timeout` alzato a 120** — *non 30 secondi a timeout predefinito*: così com'era, un server **senza nessuna nozione di sessione staccata** restava verde, perché QUIC chiudeva la prima da sé e la struttura legata alla connessione si liberava. Cioè il banco benediceva **la violazione di I4** (R3.19) |
| **3ª con il certificato di sessione ruotato a mano** | la pagina **ritira l'impronta corrente dal server** e riesce (`RCP.md` §4.1-bis) |
| ⚠ **e quel che questo NON prova** | la **rotazione automatica** a quattordici giorni. Cambiare la chiave a mano prova che la pagina sa ritirare l'impronta; che il server rigeneri **prima della scadenza** resta senza banco, e il suo sintomo — *«non si collega più e non dice perché»* — arriva due settimane dopo la consegna |

#### B4 — il validatore del filo

Un **terzo programma** che legge una registrazione e dice **quale byte** non è conforme a `RCP.md`
§6. L'unico arbitro meccanico che avremo.

| | |
|---|---|
| **le sei registrazioni guaste** | lunghezza incoerente col tipo (§6.1) · UTF-8 non valido (§6.0) · nome di capacità ripetuto (§4.3) · byte alto fuori dai cinque canali (§2.5) · messaggio nello stato sbagliato — `ATTACCA` prima di `CREDENZIALI` (§1) · ⭐ **corpo giusto ma allineato**, il byte di riempimento che «fa tornare i conti» (§6.0) |
| ⛔ **la settima, che mancava: una registrazione CONFORME, che il validatore DEVE accettare** | senza, «6 su 6» è compatibile con un validatore che **boccia tutto**: basta leggere `lunghezza` come `u16` invece di `u32` — due caratteri — e da quel momento l'arbitro dichiara non conforme **ogni** traccia, con la diagnosi che punta su `RCP.md` §6.1 mentre il difetto è nello strumento (R3.5) |
| ⛔ **e si verifica QUALE byte, non solo che sia rosso** | sulla registrazione col riempimento, un validatore che non conosce §6.0 non vede il byte in più: legge di traverso il **messaggio successivo** e dichiara non conforme **quello**. Rosso giusto, byte sbagliato — e su una traccia vera manda la diagnosi a leggere il messaggio sbagliato |

> #### ⛔ Il formato della registrazione va deciso **prima** di scrivere il registratore
>
> *Rilievo R3.6, e la prima stesura vedeva il problema senza scegliere: due regole a
> contraddirsi, e nessuna che dicesse quale vince.*
>
> | Che cosa fa il registratore | Che cosa succede |
> |---|---|
> | registra i byte **come sono passati** | ⛔ la parola d'ordine in chiaro in un file, vietato da `RCP.md` §4.4 *«a nessun livello»* |
> | **sostituisce** la parola e lascia la `lunghezza` | il corpo non ha più la lunghezza dichiarata ⇒ **falso rosso perpetuo** su ogni traccia con una stretta di mano riuscita |
> | sostituisce **e riscrive la lunghezza** | la registrazione non è più i byte passati: il validatore convalida un documento che il banco ha riscritto — **non è più un arbitro** |
>
> ⭐ **La quarta strada, che si sceglie adesso**: si registra **la lunghezza vera** e **un'impronta**
> del corpo per i soli campi segreti, e il **formato della registrazione dichiara che quel corpo è
> oscurato**. La lunghezza torna, il validatore sa che non deve guardarci dentro, la parola non c'è.
>
> ⛔ **E il formato è uno solo, scritto una volta**: due registratori — uno nel C, uno nella pagina
> — che scrivono lo stesso fatto in due modi sono esattamente il difetto muto contro cui `RCP.md`
> §0 è stato scritto.

#### B5 — le prove di violazione: il rigore verso il server

⛔ La connessione **deve cadere ogni volta**, col motivo giusto, verificato dal lato che riceve —
⛔ **e il server deve essere ancora lì dopo** (B0.5).

| Che cosa si manda | Atteso |
|---|---|
| un tipo di messaggio sconosciuto | `ERRORE_PROTOCOLLO` `0x0B` |
| una lunghezza incoerente col tipo (in più e in meno) | `ERRORE_PROTOCOLLO` |
| ⛔ **una `lunghezza` annunciata di 4 GiB** | `ERRORE_PROTOCOLLO` **e il server vivo**: §6.1 vieta di allocare prima di controllare, e un server ucciso dal nucleo *«fa cadere la connessione» lo stesso* — portandosi via **tutte le sessioni degli altri utenti** (R3.3) |
| ⛔ un messaggio che **annuncia più di 1 MiB** (§6.1) | `ERRORE_PROTOCOLLO` |
| `CREDENZIALI` con utente **vuoto**, e con parola **vuota** | `ERRORE_PROTOCOLLO`, ⛔ e **nessuno dei due contatori** di §4.4-bis si muove |
| utente da 257 byte, parola da 1025 | `ERRORE_PROTOCOLLO` (§4.4) |
| `CIAO(versione = 2)` su `/rcp/1` | `VERSIONE_INCOMPATIBILE` `0x0A` |
| una sessione WebTransport su un percorso diverso | **404** |
| uno stream **bidirezionale** oltre il primo, dal client | `ERRORE_PROTOCOLLO` |
| `0x00` (controllo) su uno stream **unidirezionale**; `0x04` (audio) su uno **stream** | `ERRORE_PROTOCOLLO` (§2.5) |
| un canale nel **verso sbagliato** — `0x03` dal client | `ERRORE_PROTOCOLLO` |
| un nome di capacità con **maiuscole**, o da 65 byte; un **valore vuoto**; un valore da 257 byte | `ERRORE_PROTOCOLLO` (§4.3) |
| `video.misura_massima` dichiarata **dal server** | `ERRORE_PROTOCOLLO` |
| `video.codec = vp9` e basta | `NIENTE_IN_COMUNE` `0x09` — *non ha sbagliato a scrivere, non ha di che parlare* |
| `video.codec = hevc,vp9` | ⭐ **si legge `hevc` e si prosegue**, e lo scarto **si scrive nel registro** |
| un `CIAO` **senza `pcm`**, e uno **senza `8`** | `NIENTE_IN_COMUNE` (§4.3) |
| tela `1921×1080`, `319×240`, `7682×4320` | `ERRORE_PROTOCOLLO` (§4.5) |
| ⛔ **vista `300×801`, e vista `1×1`** | ⛔ **DEVONO PASSARE**: §7.1 dice che la vista non ha i vincoli della tela — *«qualunque misura da 1×1 in su è legale, dispari compresa»*. Chi scrive `ATTACCA` in C scrive **una** `valida_misura()` e la chiama quattro volte: è la cosa naturale da fare, e produce un server che chiude la sessione perché l'utente ha stretto la finestra. Su un telefono a fattore 2,75 la vista è **dispari quasi sempre** (R4.10) |
| `disposizione` malformata / ben formata ma sconosciuta | ⛔ **due guasti diversi**: `ERRORE_PROTOCOLLO` · `SESSIONE_NON_SERVIBILE` `0x0E` ⛔ **col dettaglio nel corpo** (§8.2) |
| ⭐ **`BANCO_MARCA` a funzione spenta** | ⛔ **`BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)` — non un silenzio, non una chiusura** (§7.5). ⚠ È lo stato **predefinito** di ogni server, quindi si prova qui anche se la marca la userà la fase 3: un silenzio lascerebbe il banco della fase 3 ad aspettare per sempre, e il sintomo sarebbe «il banco si è piantato» |
| **`BANCO_MARCA` con `ritardo_ms = 20000`** | `BANCO_ESITO(RIFIUTATA, RITARDO_FUORI_LIMITI)` — ⛔ **non** `ERRORE_PROTOCOLLO`: far cadere la sessione al banco che si sta tarando è la cattiva idea che §7.1 evita per le misure fuori limite |
| ⚠ **e la scelta del codec** | `RCP.md` §4.3 la rende **obbligatoria nel registro del server**: si verifica che ci sia |

⚠ **La chiusura si verifica nei tre punti di §3.1** — registro, `CONGEDO`, codice della sessione —
⛔ **col secondo condizionale**: §3.1 dice *«se il canale di controllo è ancora utilizzabile»*, e un
banco che pretende tutt'e tre sempre **dà rosso sul codice giusto** quando la violazione arriva su
uno stream unidirezionale (R3.3).

#### B11 — ⭐ le prove di violazione verso la PAGINA

*Banco nuovo, dal rilievo **R4.1**, ed è il buco più grande della prima stesura: dodici violazioni
verso il server e **nessuna** verso il client. `RCP.md` §3 è scritta su «un'implementazione RCP», e
§9 ha un **DEVE esplicito del client**. In un progetto che ha perso `mstsc` e scrive `RCP.md`
proprio per non fidarsi di due programmi della stessa mano, **un client mai messo alla prova è il
buco al posto dell'arbitro**.*

Un server **guasto di proposito** — poche righe, che si buttano — manda alla pagina:

| Che cosa manda il server guasto | Che cosa DEVE fare la pagina |
|---|---|
| ⛔ `ECCOMI(versione = 2)` a un `CIAO(versione = 1)` | `CONGEDO(VERSIONE_INCOMPATIBILE)` — §9 lo impone al **client** con un DEVE, e accettarla in silenzio è *«l'indulgenza che §3 vieta»* |
| un `SESSIONE` con tela **dispari**, o fuori dai limiti | rifiuta invece di adattarsi |
| un `CONGEDO` con motivo **`0x00`** | `ERRORE_PROTOCOLLO`: §3.1 vieta il codice zero |
| uno **stream bidirezionale aperto dal server** | `ERRORE_PROTOCOLLO` (§2.5) |
| un tipo di messaggio sconosciuto sul canale di controllo | `ERRORE_PROTOCOLLO` |
| una capacità **sconosciuta** in `ECCOMI` | ⛔ **si ignora e si prosegue** — è l'eccezione 1 di §3, ⛔ **e si scrive nel registro** |
| `video.misura_massima` in `ECCOMI` (lato sbagliato) | `ERRORE_PROTOCOLLO` |
| un `FIN` sul canale di controllo | ⛔ la sessione **è finita**: la pagina non spedisce più su nessun canale (§4.2) |
| `RESPINTO` **seguito da** `CONGEDO` | ⛔ il secondo è una violazione (§4.4) |
| dopo `RESPINTO`, la pagina **non deve riprovare** sulla stessa connessione | §4.4 |
| un `SESSIONE` con `desktop = kde` mentre il ferro è GNOME | ⛔ la pagina **non cambia comportamento**: §4.5 lo vieta, e il campo è per la diagnosi |
| ⚠ **e un battito applicativo** | §2.2 lo **vieta**: si verifica che la pagina non ne mandi uno, e che non ne aspetti uno |

⛔ **E la pagina, quando chiude, chiude come dice §3.1**: registro, `CONGEDO`, **e il codice
d'errore applicativo nella chiusura della sessione WebTransport** — che è il punto che
un'implementazione può lasciare indietro restando conforme alla lettera di una versione precedente
del testo.

#### B6 — i tempi della stretta di mano

Si apre una connessione e **si tace**, per ciascuno dei tre tetti di `RCP.md` §4.6.

| Da | A | Atteso |
|---|---|---|
| ⭐ **apertura del CANALE DI CONTROLLO** (non «TLS finito», e non l'apertura della sessione — vedi sotto) | `CIAO` | **5 s**, poi `TEMPO_SCADUTO` `0x0D` |
| `ECCOMI` | `CREDENZIALI` | **60 s** |
| `AMMESSO` | `ATTACCA` | **10 s** |

⛔ **Il controllo che distingue i due guasti, ed è il meglio costruito del documento**: se il server
non tiene viva la connessione coi **PING del trasporto**, al trentesimo secondo scatta il tempo di
inattività di QUIC. **Si guarda il motivo**: `TEMPO_SCADUTO` a 60 s è il server che fa il suo
mestiere; una morte a 30 s **senza motivo** è il PING che manca. *R3 ha cercato un terzo caso che
producesse una morte a 30 s con motivo e non l'ha trovato: §3.1 vieta il codice 0 e obbliga il
motivo su ogni chiusura.*

> #### ⭐ R3.27 è CHIUSA, e B6 ha dato DUE risposte — 10-11 agosto 2026
>
> ⚠ *Questo riquadro diceva* «`[?]` … *Da misurare; se confermato, `RCP.md` §4.6 cambia di una
> parola»* — *e la misura era stata presa mentre il riquadro restava `[?]`. La cella «Misurato» di
> B6 in fondo a questo documento era vuota, e i tre numeri vivevano soltanto nel `README.md`, che
> per convenzione riassume e non decide. Chiuso l'11 agosto 2026, rilievi **R12C.11** e
> **R12-A.25**.*
>
> **La domanda era**: *«stretta di mano TLS finita» non è un istante che i due lati condividono.* In
> WebTransport la connessione HTTP/3 e la **sessione** sono due cose separate, e fra i due istanti
> passa almeno un giro di rete — il browser può aver stabilito la connessione molto prima che la
> pagina chiami l'API. ⛔ E il caso peggiore: una seconda sessione su una connessione riusata
> partirebbe **col budget già consumato**.
>
> ⭐ **PRIMA RISPOSTA — il cronometro parte dall'apertura del CANALE DI CONTROLLO**, e non sono due
> parole per la stessa cosa: né la fine del TLS né l'apertura della **sessione**. È l'istante che il
> server osserva davvero, ed è quel che il codice fa (la sessione RCP nasce quando il canale si apre,
> e il tetto si conta da lì). ⇒ **`RCP.md` §4.6 riga 1 è cambiata di una parola**, l'11 agosto 2026.
> B6 lo dice con due casi costruiti apposta — `ciao-senza-controllo` e `ciao-sessione-tardiva` — e
> **non** lo consegna come un rosso del server: ha un esito suo, il **3**, che vuol dire *«il filo si
> comporta come il codice dice, e il documento dice un'altra cosa»*.
>
> ⛔ **SECONDA RISPOSTA — e curare la parola NON BASTA.** Se il cronometro parte dall'apertura del
> canale, chi apre la **sessione** WebTransport e **non apre mai il canale** non ha addosso **nessun
> tetto**: resta lì, viva e senza scadenza. È esattamente la connessione che *«tiene un posto e non
> lo dichiara a nessuno»*, cioè la prima riga di §4.6 — **sopravvissuta alla cura**. §4.6 non ha una
> riga per quello stato: la tabella comincia da *«`CIAO` ricevuto»*, e prima del `CIAO` c'è uno stato
> in cui il server non conta niente.
> ⚠ Lo copre solo il tempo di inattività di QUIC — **30 secondi di silenzio** — e chi tiene aperta la
> sessione scrivendo su un altro stream non è silenzioso, quindi non scade **mai**.
> ⛔ **Che tetto darle, e da che istante, è una domanda aperta e non una svista**: `DECISIONI.md`
> §7.17, ❓, con le due letture e il caso concreto. Un banco che avesse stampato **una riga sola**
> per le due risposte avrebbe consegnato la metà facile.
>
> ⚠ **E i tre numeri di B6 — 5,0 · 60,1 · 10,0 s — non hanno un registro.** Girano, e l'uscita è a
> schermo: non esiste nessun `.jsonl` di B6, quindi la scena di quel giro non è ricostruibile e i
> numeri non sono riverificabili. Stanno in fondo a questo documento con quel che se ne sa
> **e con quel che non se ne sa**.

#### B7 — il congedo, verificato dal lato che riceve

⛔ **Mai dal registro di chi lo manda**: in v1, per **tre fasi**, il server scriveva «congedo il
client» mentre il client scriveva «errore di rete» (`LEZIONI.md` §1.7).

⛔ **Il denominatore è quindici, e i provocabili in questa fase sono SETTE** — `CHIUSO_DALL_UTENTE`,
`VERSIONE_INCOMPATIBILE`, `NIENTE_IN_COMUNE`, `ERRORE_PROTOCOLLO`, `TEMPO_SCADUTO`,
`SESSIONE_NON_SERVIBILE`, `GIA_ATTIVA_REMOTA`. Per ciascuno si verifica il `CONGEDO` **e** il codice
nella chiusura.

> ⚠ *Questa riga diceva* «Per ciascuno degli **otto** motivi che questa fase sa produrre … `SERVER_IN_CHIUSURA`»
> *e più sotto «le **otto** frasi devono essere distinte». ⛔ Era falsa in tutt'e due i sensi, e il
> banco lo aveva **misurato e scritto** — `banchi/01-b7-congedo.py`, tabella `ESCLUSI`, voce `0x0C`:*
> «il server della fase 1 non ha un percorso di spegnimento: `RCP_SERVER_IN_CHIUSURA` è dichiarato in
> `rcp.h` e non compare in nessuna riga di `rcp.c`. ⚠ MISURATO col grep, non supposto — **e
> contraddice §01-filo-nudo B7**». *Corretta l'11 agosto 2026, rilievo **R12C.6**.*
>
> ⛔ **E il denominatore vero è QUINDICI, non otto**: §8.2 ha quindici motivi. Scrivere «8 su 8»
> scegliendo gli otto che si sanno provocare è vero **per costruzione**, ed è la forma di verde più
> vuota che ci sia. Gli **otto esclusi** stanno in `ESCLUSI` con la ragione di ciascuno, e
> `certifica_denominatore()` verifica che 7 + 8 = 15 invece di fidarsi: `0x02` e `0x03` sono orologi
> della sessione (fase 5) · `0x04` e `0x05` vogliono una sessione grafica locale (fase 2) · `0x06`
> vuole la capacità di codifica (fase 3) · `0x07` e `0x08` **non viaggiano in un `CONGEDO`** ma in
> `RESPINTO` (§4.4), e provocare `0x08` bannerebbe l'indirizzo del banco (B0.3) · `0x0C` per il
> percorso di spegnimento che manca.
>
> ⭐ **E `0x0C` è cambiato di soggetto la notte del 10 agosto, ed è il primo posto in cui i due
> server divergono in modo visibile**: **il prodotto** un percorso di spegnimento adesso ce l'ha —
> `src/main.c` congeda tutti con `SERVER_IN_CHIUSURA` prima di uscire — mentre **l'innesto**, che è
> quello che B7 accende, no (`grep`: zero occorrenze in `01-b3-rcp-innesta.py`). ⛔ Quindi i
> provocabili restano **sette contro il bersaglio che B7 misura**, e diventano **otto il giorno in
> cui B7 sarà puntato al prodotto**. Il numero da scrivere accanto a un esito è quello del bersaglio
> che si è acceso.

| | |
|---|---|
| ⛔ **«tante su tante» non basta, e la prima stesura si fermava lì** | una `switch` col ramo predefinito — `mostra("Errore " + codice)` — dà una stringa non vuota per **ogni** motivo, e quindi il conto torna sempre. L'utente legge *«Errore 14»* per `SESSIONE_NON_SERVIBILE`, che §8.2 vieta con un ⛔ e un esempio quasi identico (R3.20) |
| ⭐ **i due criteri che rendono la riga misurabile** | le frasi devono essere **distinte fra loro** — ⛔ **tutte e quindici**, non solo le sette provocabili: la frase la costruisce il client dal codice, quindi si legge senza provocare il motivo — e ⛔ **nessuna deve contenere il numero del motivo** né «errore» seguito da una cifra. Un `grep` di due righe |
| ⚠ **e «il banco guarda lo schermo» non è eseguibile** | o si legge il DOM — l'unica cosa che una prova automatica può fare — **oppure è l'utente** (I8), e allora la riga va nel **giudizio**, non in una tabella con un «tante su tante». Dichiarato, così che nessuno la legga come già coperta |
| ⚠ **i due motivi che NON viaggiano in un `CONGEDO`** | `CREDENZIALI_ERRATE` e `TROPPI_TENTATIVI` stanno in `RESPINTO` (§4.4, rilievo R1.18): un banco che li cercasse in un `CONGEDO` **fallirebbe per costruzione** |
| ⛔ **il `dettaglio` non si mostra** | è per il registro (§8.2) |

#### B8 — il secondo fisso, e il ban dell'indirizzo

> ⛔ **Riscritto il 10 agosto 2026, dopo che l'utente ha sostituito la forma della limitazione**
> (`DECISIONI.md` §1.9): tre autenticazioni fallite dallo stesso indirizzo ⛔ **dentro una finestra
> di 5 minuti**, e quell'indirizzo è fuori per **12 ore**. Cadono con la regola vecchia il raddoppio della finestra, la
> scadenza a 30 minuti di quiete e **il contatore per nome utente**; ⭐ **e cade il controllo che
> teneva fermo questo banco** — *«quattro falliti · uno riuscito · altri quattro»* non è più
> eseguibile, perché dopo il terzo fallito non esiste nessun quinto tentativo.
>
> ⚠ *E il rosso del 10 agosto va riletto con la regola nuova prima di indagarlo: il quinto tentativo
> — quello con le credenziali buone — aveva ricevuto `CREDENZIALI_ERRATE` `0x07` e **non**
> `TROPPI_TENTATIVI` `0x08`. §4.4-bis rifiuta **senza interrogare PAM**, quindi non ha modo di dire
> «errate»: il motivo sul filo accusa **la gamba del banco**, non il limitatore. Il controllo si
> riscrive comunque da capo, e la mezz'ora si spende su quello nuovo.*

⭐ **È un banco che vede due proprietà che nessun altro vede**, e una regressione che le togliesse non
farebbe fallire niente.

**Il secondo fisso** — invariato, la regola non l'ha toccato:

| | |
|---|---|
| ⛔ **il criterio NON è «≥ 1 s», ed è la cura più importante di questo banco** | `pam_authenticate(); sleep(1); rispondi();` dà **1,001 · 1,050 · 1,300 s** nei tre casi: **tre righe verdi**, e la distinzione che §4.4 vieta di scrivere nel motivo si legge col cronometro **esattamente come prima**. Il banco che si dichiara *«l'unico che vede questa proprietà»* non la vedeva (R3.2) |
| ⭐ **il criterio giusto è di forma diversa, non di soglia diversa** | ⛔ **le mediane dei tre casi differiscono meno del rumore della misura** — molti campioni per caso, non uno. Con un campione i cinquanta millisecondi che separano «utente inesistente» da «password sbagliata» non sono nemmeno visibili. **Atteso: ≥ 1 s in ogni campione, e le tre mediane indistinguibili** |
| ⛔ **e i campioni adesso costano** | tre per indirizzo, poi il ban. Le mediane vogliono **molti** campioni per caso, quindi il banco deve **variare l'indirizzo di provenienza** o sbloccare fra un blocco e l'altro — ⛔ **e dichiarare quale delle due fa**, perché cambiano quel che la misura sta misurando |
| ⚠ **e il `[?]` che questo banco ha già trovato** | `[M]` 10 agosto: mediana **2636 ms** sui respinti, dove §4.4-bis vuole ~1000. ⛔ **A governare i tempi è PAM, non noi**, e finché quel ritardo non è costante il secondo fisso non nasconde quel che dichiara di nascondere. Il ban **non** chiude questa `[?]` |

**Il ban** — nuovo, e sostituisce tutte le righe del limitatore:

> ⛔ **LA FINESTRA DI CINQUE MINUTI, che questa sezione non nominava.**
>
> ⚠ *Il riquadro qui sopra e la tabella che segue dicevano* «tre autenticazioni fallite
> **consecutive** dallo stesso indirizzo», *senza finestra — e «consecutive» era la **prima**
> formulazione dell'utente, stretta lo stesso giorno da una **terza** frase:* «i 3 tentativi falliti
> devono avvenire **entro i 5 minuti** per far scattare il ban» *(`DECISIONI.md` §1.9). La finestra
> era in `DECISIONI.md`, in `RCP.md` §4.4-bis, in `SPECIFICHE.md` §4.2 e nel codice
> (`#define FINESTRA 300000u`) — e mancava nei **due** documenti da cui si scrive il banco.
> Corretto l'11 agosto 2026, rilievo **R12C.5**.*
>
> ⛔ **Perché morde sul banco e non sulla carta**: le due regole danno **esiti opposti sullo stesso
> ingresso**. Tre fallimenti alle 0:00, 4:00 e 8:00 sono *consecutivi* ⇒ bannati secondo la riga
> vecchia, e **fuori finestra** ⇒ non bannati secondo il codice. Un banco scritto da qui che spaziasse
> i tre tentativi darebbe **rosso sul codice giusto**, che è la forma di `LEZIONI.md` §2.3.
> ⚠ E la ragione per cui è successo è quella che il `README.md` vieta: la decisione era **copiata** in
> quattro documenti invece che rimandata, e le quattro copie non erano uguali.
>
> ⚠ **La finestra è scorrevole**: si guarda l'ora degli **ultimi tre** fallimenti, non si riparte dal
> primo. Ancorandola al primo, tre fallimenti a 0:00 · 4:59 · 5:01 farebbero ripartire il conto da
> uno, e chi prova a un ritmo appena più lento della finestra non verrebbe **mai** fermato.
> ⇒ **La decisione sta in `DECISIONI.md` §1.9 e qui non si copia**: questa è la sua conseguenza sul
> banco.

| | Atteso |
|---|---|
| ⛔ tre autenticazioni fallite dallo stesso indirizzo, **dentro 5 minuti** | le prime tre rispondono `RESPINTO(CREDENZIALI_ERRATE)`, ciascuna **non prima di un secondo** |
| ⭐ **il quarto controllo che dice *no*, ed è nuovo: FUORI dalla finestra il ban NON scatta** | tre fallimenti spaziati di più di 5 minuti ⇒ **nessun ban**, e il quarto tentativo con la parola giusta **entra**. ⛔ Senza, «il ban scatta al quarto» è compatibile con un server che non guarda l'orologio, e la riga di `DECISIONI.md` §1.9 che protegge *«chi sbaglia a digitare ogni tanto»* non è provata da nessuno |
| ⛔ **il quarto tentativo, con la parola d'ordine GIUSTA** | ⛔ **rifiutato lo stesso**, e la pagina lo **dice**: `TROPPI_TENTATIVI`. ⭐ *È la riga che distingue un ban da un contatore, ed è anche il sintomo che l'utente vedrà — «l'ho scritta giusta e non mi fa entrare» — quindi è voluto e va provato, non evitato* |
| ⛔ **e i tre nomi utente DEVONO essere diversi** | ⚠ Con lo stesso nome tre volte, un server che avesse ancora il contatore **per nome** della forma vecchia darebbe verde: il banco proverebbe la regola sbagliata. È la stessa forma con cui **B5** ha trovato il contatore chiavato sulla porta |
| ⭐ **il controllo che dice *no*, primo**: un **altro** indirizzo | entra **subito**, con le credenziali buone. Senza, «il quarto è rifiutato» è compatibile con un server che ha smesso di funzionare |
| ⭐ **il controllo che dice *no*, secondo**: l'azzeramento | **due** falliti · **uno riuscito** · **due** falliti ⇒ il terzo fallito **non** banna. Se il successo non azzerasse, il secondo blocco sarebbe già scattato. ⚠ *È il controllo di R3.9 nella forma che la regola nuova rende eseguibile: prima serviva un quinto tentativo che non esiste più* |
| ⭐ **il controllo che dice *no*, terzo**: la persistenza | si banna, **si riavvia il server**, e l'indirizzo **è ancora bannato**. ⛔ Senza, il ban vive in memoria e un aggiornamento del pacchetto regala tre tentativi a chiunque — è l'invariante **I7** |
| **quel che l'utente vede** | ⛔ la **pagina si carica** e dice che i tentativi sono esauriti (§4.4-bis). Si legge il DOM, come per le otto frasi di B7: un banco non guarda uno schermo |
| **e la scheda già aperta** | la sessione WebTransport si rifiuta con `TROPPI_TENTATIVI` nel codice della chiusura, verificato **dal lato che riceve** |
| **lo sblocco** | il comando toglie il ban, **lo scrive nel registro**, e l'indirizzo rientra. ⛔ **Questa riga si prova in fondo**, non all'inizio: uno sblocco chiamato dentro il giro fa passare tutto il resto per costruzione (B0.3) |

⛔ **E `TROPPI_TENTATIVI` non viaggia in un `CONGEDO`, viaggia in `RESPINTO`** (§4.4, rilievo R1.18):
un banco che lo cercasse in un congedo fallirebbe per costruzione, e chi lo scrive penserebbe di
aver sbagliato lui.

#### B9 — il cliente di prova: il secondo lettore

⭐ Poche centinaia di righe, **in un linguaggio diverso dal server e dalla pagina**, scritte
leggendo `RCP.md`.

| | |
|---|---|
| ⛔ **la separazione dev'essere un MECCANISMO, non una regola** | la prima stesura scriveva *«chi lo scrive non guarda il C né la pagina»*, cioè affidava **l'unico arbitro esterno rimasto** a una memoria. È **I7 al contrario**, ed è la forma che questo progetto ha pagato tre giorni fa: *«la lezione era già scritta, la cura è rimasta una nota in un documento»* (R3.21) |
| ⭐ **il meccanismo, e costa poco** | chi scrive il cliente di prova **riceve `RCP.md` e i suoi riferimenti, e non l'albero del server e della pagina**. E la cosa si **dichiara qui**, così che il giorno in cui il cliente di prova concorderà col server si sappia se quella concordanza vale qualcosa |
| ⛔ **una dipendenza da verificare prima**, ed è il criterio di B2 non riapplicato | che **`python3-aioquic` 1.2 porti WebTransport lato client non è `[M]` da nessuna parte**. Se non lo porta, il cliente di prova non esiste — cioè cade l'arbitro — e ce ne accorgeremmo dopo aver scritto il server |
| ⚠ **l'esito più prezioso non è «passa»** | è **ogni punto in cui chi lo scrive ha dovuto scegliere** perché `RCP.md` ammetteva due letture. Quei punti vanno in «che cosa NON ha funzionato», e sono difetti **del documento** |

#### B10 — il secondo utente: il difetto ereditato da `autenticazione.c`

⛔ Il banco autentica un utente **diverso** da quello che possiede il processo del server.
`autenticazione_utente_atteso()` rifiuta chiunque non sia il proprietario del processo: era giusto
in v1, **contraddice il multi-tenant** di `SPECIFICHE.md` §5.5.

| | |
|---|---|
| ⛔ **«non entra» ha quattro cause, e il banco ne nominava una** | *(1)* la guardia è ancora lì — **il difetto**; *(2)* il contatore per indirizzo è nella sua finestra (B0.3); *(3)* la pila PAM non consente al processo di verificare la parola di **un altro** utente; *(4)* il secondo utente non esiste o non ha parola d'ordine. Chi legge quel rosso credendo alla riga vecchia va a cercare nel posto sbagliato — `LEZIONI.md` §1.6 (R3.26) |
| ⛔ **chi possiede il processo va dichiarato** | il banco si definiva *«un utente diverso da quello che possiede il processo»* **senza dire chi sia**, mentre `SPECIFICHE.md` §5.5 lo vuole **di sistema** |
| ⭐ **il controllo che costa dieci secondi** | prima di credere al rosso, si verifica che la stessa parola **funzioni fuori dal server**: `pamtester` sullo stesso servizio PAM. Se fallisce anche lì, **non si sta misurando il server** |
| **atteso** | l'utente `prova` — creato dal provisioning, non a mano — completa la stretta di mano fino a `SESSIONE` |

> #### ⭐⭐ IL BANCO ESISTE DALL'11 AGOSTO 2026, SERA — e si è certificato nello stesso giro
>
> *Era l'unico dei dodici **mai provato**, e il motivo era che non c'era: `banchi/01-b10-secondo-utente.py`
> e `banchi/01-b10-lancia.sh`. ⭐ Il banco **importa** `01-b3-cliente.py` come modulo invece di
> copiarlo: misura RCP col secondo lettore, e la parola non passa da nessun `argv`.*
>
> | | |
> |---|---|
> | ⭐ **l'atteso è misurato** | **`prova2`** — dal provisioning, non a mano — arriva a `SESSIONE` sul **PRODOTTO**: `AMMESSO` a **1001-1059 ms** (il secondo fisso di §4.4-bis), stretta intera **1213-1261 ms**. `[M]` **11 agosto 2026, 13:08 UTC**, NIC-OS, porta **7491**, binario md5 `9dcb9657…`. Registro `banchi/b10-esiti-prodotto.jsonl` |
> | ⛔ **chi possiede il processo è DICHIARATO** | **`root`, uid effettivo 0** — letto da `/proc/<pid>/status`, non supposto — cioè **di sistema**, come §5.5 vuole. ⭐ E il banco verifica di **non essere vacuo**: se il server girasse come l'utente della prova esce **2**, *«non ho potuto misurare»*, invece di stampare un verde che non significa niente |
> | ⛔ **le quattro cause si distinguono, e con tre osservazioni** | *(1)* **la guardia** — il server rifiuta **e nel suo registro non c'è nessuna riga di `autenticazione.c`**: PAM non è stata nemmeno interrogata; *(2)* **il contatore per indirizzo** — il motivo sul filo è `TROPPI_TENTATIVI` `0x08`, e allora il banco **sblocca dichiarandolo e riprova**, o (2) coprirebbe (1); *(3)* **la pila PAM** — `pamtester` fallisce con la stessa parola; *(4)* **l'utente** — `getent passwd` e `getent shadow` |
> | ⭐ **il controllo che costa dieci secondi, e il suo negativo** | `pamtester remotix prova2 authenticate` **riesce** — ⛔ sul servizio **`remotix`**, non `login` — e con la parola sbagliata **fallisce**: senza il secondo, il primo non varrebbe niente |
> | ⭐⭐ **e la `[?]` R3.26 è MISURATA** | da un utente **non privilegiato** la verifica della parola di **un altro** utente **fallisce**; da **root riesce**. ⇒ **la pila PAM giudica un altro utente solo se il processo è privilegiato**. Il server oggi è di root e ci riesce; ⛔ un servizio di sistema che **lasciasse i privilegi** vedrebbe la causa (3), e il sintomo sarebbe di nuovo *«credenziali errate»* — è la domanda che la fase 2 si porta dietro |
> | ⭐ **due utenti, non uno** | dopo il respinto, **`prova`** arriva a `SESSIONE`: è insieme **B0.5** (il server è ancora lì) e §5.5 (due utenti diversi, **nessuno dei due** proprietario del processo) |
> | ⛔ **la parola generata non passa da nessuna riga di comando** | il compromesso che il `README.md` dichiarava **non accettato** è chiuso: la parola si legge da `credenziali-banchi`, si scrive con un **builtin** in un file `0600`, arriva come `--parola-file`, e una `trap` la cancella. ⚠ Resta una copia su disco per la durata del giro, ed è dichiarata |
>
> ⭐ **CERTIFICATO — `0 → 1 → 0`** `[M]` 11 agosto, **15:09 UTC**. Il guasto **rimette la guardia di
> v1** — `getpwuid(geteuid())` e il confronto col nome, **prima** di `pam_start` — su una **copia
> intera** dell'albero del prodotto, ⛔ **mai su `src/remotix`**: gli altri banchi lo stavano
> misurando in quegli stessi minuti, e per un quarto d'ora avrebbero avuto sotto i piedi un server
> bugiardo. Marca **`CAUSA-1-GUARDIA-PRE-PAM`: 2 nel giro guasto, 0 nei due giri sani**.
>
> ⛔ **E il guasto in catalogo non guastava niente.** L'appiglio `autenticazione_utente_atteso` era
> puntato su un file dove compare **solo dentro un commento**: il sostituto ci appiccicava accanto la
> marca e il codice compilato restava **identico byte per byte**. ⚠ **È la terza volta in un giorno**
> che un appiglio di commento fa credere di aver guastato qualcosa — dopo B5 e B3 — ed è la forma che
> costa di più, perché il giro *sembra* una certificazione riuscita.
>
> ⚠ **B10 non passa da `01-b12-lancia.sh`**: il suo guasto si ricostruisce con
> `GEMELLO=nessuno <copia>/costruisci.sh`, mentre `attrezzi-misura-marca.sh` sa fare solo
> `ninja … bsslserver`, cioè **l'innesto**. Finché `gira()` non impara a costruire il **prodotto**,
> la certificazione si fa dal lanciatore del banco — ed è la stessa lacuna del punto 4 dell'elenco.
>
> ⛔ **E quel che B10 NON prova**: il caso dell'utente **proprietario** del processo. `root` non ha
> una parola d'ordine nota nel contenitore, quindi *«con la guardia rimessa entra solo root»* è
> **dedotto, non misurato**. ⚠ E B10 è provato solo contro il **prodotto**, mai contro l'innesto.

#### B12 — la certificazione: come questi banchi si fanno credere

⛔ `PIANO.md` §0.3 regola 4. *La prima stesura costruiva **quattro** guasti per **dodici** banchi, e
i due scoperti erano i banchi dei due difetti più cari di v1 (R3.7, R4.6).*

| # | La prova | Che cosa dimostra |
|---|---|---|
| **C1** | ⛔ **un guasto costruito a mano PER OGNI BANCO**, e sono dodici | il banco **deve diventare rosso**. Fra i nuovi: **B3** — non si libera la struttura per connessione (il difetto di v1); **B7** — ⛔ **si toglie la spedizione del `CONGEDO` e si lascia il codice nella chiusura**: se B7 resta verde sta facendo una `\|\|` dove serve una `&&`, e **il banco è nato per non accorgersene**; **B4** — il validatore che legge `lunghezza` come `u16`; **B9** — il cliente di prova che ha letto il C |
| **C2** | ⛔ **si guasta il collegamento in TRE modi e si pretendono TRE diagnosi diverse**: nessuno in ascolto · **UDP 7447 filtrato col TCP che risponde** · impronta non corrente. *La prima stesura provava solo il primo — e il secondo è il caso concreto con cui `R2` ha dimostrato che il primo controllo positivo del progetto era cieco* (R3.17) | un banco che le confonde dirà «il server non risponde» il giorno in cui il certificato è scaduto |
| **C3** | si esegue tutto **due volte di fila**, senza rimettere niente | ⚠ e quel che sopravvive è **cinque cose, non una**: vedi B0.2 |
| **C4** | i due lati si sincronizzano con **marcatori** | `LEZIONI.md` §2.3-quinquies |
| **C5** | ⛔ **ogni banco confronta il proprio atteso**, e lo stato d'uscita è quello del confronto | ⚠ *La prima stesura citava `00-c1-kwin.sh` come modello: quel file **stampa e non confronta**, ed è un difetto dichiarato aperto nella fase 0. Citato adesso come **il difetto da non ripetere*** (R3.18) |

> #### ⭐ IL GIRO DELL'11 AGOSTO, POMERIGGIO — e la prima cosa da dire è che il conto di stamattina era già scaduto
>
> ⛔ **Nessuno dei tre certificati valeva più.** Il registro porta, accanto a ogni certificazione,
> l'impronta di `rcp.c` con cui è stata fatta: **`d839839f…`**. Oggi `rcp.c` è **`cb7af778…`** —
> l'hanno cambiato le cure del 10-11 agosto. ⇒ *«3 su 12»* era **3 su 12 su un codice che non esiste
> più**, ed è esattamente ciò che il registro dice quando lo si legge invece di leggerne il totale.
>
> ⚠ ⛔ **E la prova qui sopra è scritta in due alfabeti, cioè non si rifà** — trovato la sera dell'11
> agosto. `d839839f…` è un **sha256 troncato** (il registro lo scrive per esteso); `cb7af778…` è un
> **md5**. Il `sha256` di `rcp.c` oggi è **`84411b9c…`**. ⇒ La **conclusione regge** — il codice è
> cambiato davvero, `d839839f…` → `84411b9c…` — ma **il confronto stampato mette a paragone due
> funzioni diverse**, e chi lo rifacesse domani troverebbe due numeri che non c'entrano niente e non
> saprebbe se ha sbagliato lui. ⭐ *Un'impronta senza il nome della funzione è la stessa cosa di un
> numero senza unità di misura.*
>
> | Banco | Oggi | Come |
> |---|---|---|
> | **B4** | ⭐ **certificato** | `0 → 1 → 0`, marca «⛔ atteso il byte» |
> | **C2** | ⭐ **certificato** | `0 → 1 → 0`, marca «IRRAGGIUNGIBILE» |
> | **B9** | ⭐ **certificato** | `0 → 3 → 0`, marca «il testo è cambiato sotto il banco». ⭐ **Ma prima ha trovato un difetto vero, e nostro**: il giro sano usciva **3**, perché la voce **L6** citava la vecchia riga 1 di `RCP.md` §4.6 — quella che partiva dalla fine del TLS — e **l'abbiamo corretta noi** l'11 agosto sulla misura di B6. ⛔ Nessun altro banco se ne sarebbe accorto: gli altri sarebbero diventati **più verdi**, non meno. La `[?]` R3.27 è ora registrata come **DECISA**, che non è «sparita» |
> | **B7** | ⭐ **certificato** | `0 → 1 → 0`, marca «il motivo nel `CONGEDO` sul canale: assente» — ⛔ e la riserva del 10 agosto (*«marca non discriminante, 37 occorrenze»*) **è chiusa**: la marca di oggi nel giro sano non compare |
> | **B6** | ⭐ **certificato — e non era mai stato provato** | `0 → 1 → 0`, marca «⭐ nessuna caduta», cioè la riga che solo un caso `-presto` **caduto** può produrre. Il guasto porta `TETTO_CIAO` da 5000 a 500 ms: ⭐ *la metà del requisito che nessuno scrive è «non prima»* |
> | ⭐ **B5** | ⭐ **certificato — e non era mai stato provato** | `0 → 1 → 0`, marca «§3.1 punto 3 su «capacita-ripetuta»». ⛔ Il guasto in catalogo **non rompeva niente**: l'appiglio era una stringa di *commento* e il sostituto ci appiccicava accanto la marca — il codice compilato restava identico byte per byte. Rifatto sul **ramo**: `if (ripetuto)` spento, `congeda()` mai chiamato |
> | ⛔ **B8** | ⛔ **provato e NON certificato**, e il motivo è cambiato — *poi **certificato la sera dello stesso giorno**, vedi in fondo alla sezione* | vedi il riquadro qui sotto |
> | ⭐ **B3** | ⭐ **certificato — e non era mai stato provato** | `0 → 2 → 0`, marca «`CONGEDO invece di SESSIONE: motivo 0x0f = GIA_ATTIVA_REMOTA`». ⛔ L'appiglio in catalogo aveva **due** spazi di rientro dove il file ne ha **quattro**: compariva **zero** volte, e il guasto non si sarebbe innestato. ⭐ Il sintomo col guasto è quello di v1 alla lettera: la prima connessione passa, la seconda si vede rifiutare perché il posto della prima non si è liberato |
> | ⭐ **B2** | ⭐ **certificato — e ha trovato un difetto vero prima di lasciarsi certificare** | `0 → 1 → 0`, marca «`- credito uni DISPONIBILE a RCP all'apertura`». Vedi il riquadro |
> | ⭐ **B11** | ⭐ **certificato dal PROPRIO giro** | **CONFORME, 0 punti** contro il server guasto; **NON-CONFORME, 9 punti** contro quello sano — il controllo che dice *no*. ⚠ Riserva scritta: **un motore solo**. Vedi il riquadro |
> | **B13** | ⛔ **non certificabile, e il motivo ha un nome** | vedi il riquadro qui sotto |
>
> ⇒ ⭐ **9 certificati su 12 sul codice di oggi**, contro **3 su 12 su un codice che non c'è più**.
> ⚠ Restano **due provati e non certificati** — **B8** e **B13**, tutt'e due su lacune con un nome,
> non su capricci dello strumento — e **uno mai provato**, **B10**. ⛔ Nessuno dei tre è «pulito».
>
> ⛔ **E questa riga ha portato «5» per mezza giornata mentre il registro diceva 8** — R12-A.49.
> Due aggiornamenti di questo file erano andati a vuoto **in silenzio**, perché una sostituzione di
> testo non protesta quando non trova, e lo script diceva «fatto» lo stesso. ⭐ È la forma «il
> denominatore non lo guarda nessuno», applicata a un documento invece che a un banco: adesso ogni
> sostituzione si verifica, e chi non trova l'ancora **si ferma**.
>
> ⚠ **E il numero dipende da dove lo si chiede — R12-A.36.** Il registro viveva in **due copie**,
> una per macchina, e nessuna delle due sapeva dell'altra: il server dava «B9 NON certificato»
> mentre sul portatile B9 era certificato da un'ora. ⭐ Unite (il file è quello versionato,
> `banchi/01-b12-registro.jsonl`, e la copia del server ne è ora un riflesso). ⛔ Ma anche unite, il
> server dice **4 su 12** e il portatile **5 su 12**, e ⭐ **hanno ragione tutt'e due**: sul server
> `RCP.md` non c'è, quindi la certificazione di B9 non si può *riverificare* lì — e lo strumento
> scrive *«non si può dire se valga oggi»* invece di arrotondarlo a «certificato». ⇒ Il numero è
> **5**, e va detto **dove** si legge.
> ⚠ E i due che restano provabili subito sono **B5** e **B8**, tutt'e due fermi sulla **marca
> mancante**; **B2** costa una ricostruzione intera; **B3** e **B11** la marca non ce l'hanno;
> **B10** non ha nemmeno il banco.
>
> ##### ⭐⭐ `01-b0-terreno.sh` — il controllo che guarda SOTTO i banchi
>
> *Nato l'11 agosto 2026, rilievo **R12-A.46**. Non muove il conto di un punto, e protegge tutti.*
>
> ⛔ **Due volte nello stesso giorno un banco è stato verde su un terreno che non era quello che
> credevamo**, e in tutt'e due i casi il banco non aveva nessun motivo di accorgersene: l'innesto
> RCP sparito da `examples/` (**R12-A.45**) e l'utente `prova` che non lo creava nessuno
> (**R12-A.44**). ⚠ Nel primo caso **la certificazione di B2 è passata lo stesso** — la sua sonda
> legge i parametri QUIC e di RCP non sa niente. ⭐ **L'ho preso per caso**, mentre provavo un'altra
> cosa: senza quella coincidenza starebbe nel registro, datato, e sbagliato in un modo che nessuno
> ritrova.
>
> ⇒ Gira **prima** di ogni giro di certificazione e guarda **14 cose**: i due innesti al loro posto
> in tutt'e due i file che se li contendono · i tre file che B3 copia dentro `examples/` · che
> `examples/rcp.c` sia **identico** a `rcp/rcp.c` · che nessun guasto di B12 o di B11 sia rimasto
> addosso · ⭐ e che **il binario sia più nuovo di tutti i sorgenti che dichiara**. Se non regge, B12
> **non certifica e non scrive nel registro**.
>
> ⭐ **E si è fatto dire di no tre volte prima di essere creduto**: con un guasto di B12 lasciato
> addosso → rosso; con un pezzo dell'innesto tolto → rosso; e ⭐ **la terza non l'avevo preparata** —
> il mio stesso giro di prova aveva lasciato `rcp.c` più nuovo del binario, cioè *sorgente sano e
> binario vecchio*, la trappola **R12-A.6** in persona. Il controllo l'ha trovata da solo.
>
> ⚠ **Che cosa non dimostra**: che il server sia *corretto*. Dimostra che è **quello dichiarato** —
> cioè che i banchi cerchino nel posto giusto. Un server può passare tutti e 14 ed essere pieno di
> difetti: quelli sono il mestiere dei banchi.
>
> ⛔ E la prima stesura sbagliava **nella stessa forma curata quella mattina su S1b** (A31): `grep
> -c` esce **1** quando non trova niente — che è la risposta «zero», non un errore — e il `|| printf
> '?'` ci appiccicava un `?` dopo lo zero già stampato. **Cinque falsi rossi in un colpo, dentro il
> file che esiste per impedirli.**

> ##### ⛔⭐ Tre falsi rossi, tutti prodotti da B12 stesso — e sono la parte che vale
>
> **R12-A.31 — B12 certificava dove non poteva.** Il lanciatore avvertiva *«B9 e B4 si certificano
> dove stanno i loro file»* e poi li lanciava lo stesso. `[M]`: sul server **`RCP.md` non esiste** —
> lì arrivano i banchi, non i documenti — B9 è uscito **4** e il registro ha scritto **«B9 NON
> certificato»**. ⛔ È **la forma opposta del falso verde**, e costa uguale: un banco sano marchiato
> rosso manda a cercare un difetto che non c'è, e il registro se lo porta dietro con una data.
> ⭐ Cura: `--provabile` guarda se i file su cui la certificazione poggia ci sono, e il lanciatore si
> **rifiuta** invece di misurare. *«Non posso provarlo qui»* e *«l'ho provato e non passa»* sono due
> fatti.
>
> **R12-A.32 — B6 era certificabile, e l'obiezione in catalogo non reggeva.** Diceva che il guasto
> non si può innestare perché *«`01-b6-lancia.sh` ricopia il sorgente a ogni giro»*. ⭐ Tutt'e due le
> metà dell'obiezione parlano del **lanciatore**, e **B12 non lo usa**: chiama il programma del
> banco. Aggiunta la riga di comando, coi tetti **letti** dal sorgente compilato invece che scritti a
> mano. ⚠ E va detto che cosa questa certificazione **non** copre: certifica `01-b6-tetti.py`, non il
> confronto sorgente/binario che sta nel lanciatore.
>
> **R12-A.33 — `--bersaglio` è diventato obbligatorio e i chiamanti sono rimasti indietro. Tre volte
> in due giorni.** Il 10 agosto su `01-b6-lancia.sh` e `01-b3-quarto-giro.sh`; oggi su
> `01-b12-lancia.sh`, che chiamava B7 **senza `--bersaglio`** e con un `--sorgente` che non esiste
> più: il giro ha scritto **«B7 NON certificato»** su un banco sano.
>
> ⭐ **Da cui un banco nuovo: `banchi/01-b0-chiamate.py`** — *chi chiama un banco gli passa quel che
> il banco pretende?* Legge gli `add_argument` con l'AST, scioglie le variabili di shell definite nel
> file, e distingue **tre** esiti: approvata · rotta · **IGNOTA** (una variabile che potrebbe
> nascondere il nome di un'opzione). Ha subito trovato **R12-A.33-bis**: `01-b8-lancia.sh` chiamava
> il cronometro senza `--bersaglio` né `--porta`, quindi il passo *«che cosa mi aspetto, prima di
> misurare»* stampava da giorni **un messaggio d'uso di argparse** — e non faceva fallire niente.
>
> ⛔ **E scriverlo ha insegnato quattro cose, tutte misurate, tutte sullo stesso tema:**
> · accusava **21** righe di *esempio* dentro le spiegazioni. ⭐ Un controllo che grida sul falso non
>   viene ignorato meno di uno che tace: viene ignorato **insieme ai suoi veri**;
> · un filtro troppo stretto ha fatto sparire le chiamate `python3 -u` **in silenzio** — le viste
>   sono passate da **83 a 22** e il conto sembrava soltanto più pulito. ⛔ Una copertura che cala
>   senza dirlo è un banco che smette di guardare, e si vede **solo dal denominatore**;
> · *«c'è un `$` ⇒ ignota»* rendeva ignote **26 righe su 34**, ⛔ compresa quella che aveva appena
>   rotto B7. La domanda giusta non è «c'è una variabile», è **«quella variabile può nascondere il
>   nome di un'opzione?»**;
> · ⭐⭐ e il più istruttivo: unendo le opzioni del modulo condiviso avevo preso quelle **ammesse** e
>   non quelle **pretese**. Risultato: la riga per B6 che avevo appena scritto — **senza
>   `--bersaglio`** — il controllo l'ha dichiarata **approvata**, e il giro di certificazione ha
>   scritto «B6 NON certificato» su un errore mio che lo strumento nato per trovarlo aveva guardato e
>   promosso. ⛔ **Allargare le maglie per far tacere i falsi si porta via i veri nella stessa
>   mossa**, e non si vede, perché il conto dei rossi scende — che è precisamente l'aspetto di un
>   progresso.
>
> ⚠ E le tre accuse superstiti **le ho lanciate davvero** invece di dedurle: due erano false (B7 ha
> una scorciatoia `--elenco` prima di `parse_args`) e una vera. Curarle tutt'e tre avrebbe rotto due
> chiamate funzionanti per far tacere il mio stesso strumento.
>
> ##### ⭐⭐ B11: certificato — e il difetto era una CORSA, non una divergenza
>
> ⚠ Non era «mai provato»: era **mai lanciato**. E va lanciato **dalla macchina di chi guarda**, non
> dal server — `01-b11-lancia.sh` cerca `fondamenta/strumenti/sshpw.py`, che sul server non c'è. Lanciato di
> là muore prima di applicare qualsiasi guasto (verificato: zero marche nei sorgenti e nel binario,
> porta 7447 libera).
>
> ⛔ **Al primo giro un punto solo non passava**: contro il server guasto, `respinto-non-riprovare`
> restituiva **`canale-rotto`** dove l'atteso dice **`muta`**. ⭐ **E la pagina aveva ragione**:
> distinguere un `FIN` da un `RESET_STREAM` è la cura del rilievo R6.12, e il server in quel caso
> **non manda nessun `FIN`** — chiude la *sessione* con `CLOSE_WEBTRANSPORT_SESSION`.
>
> ⭐⭐ **Ma la causa vera era un'altra, e allargando l'atteso non l'avrei mai trovata.** La pagina
> non arrivava nemmeno al ramo del `RESPINTO`: il server manda `RESPINTO` e **chiude subito
> dietro**, e la chiusura **corre** contro il lettore della pagina. ⇒ Il verdetto dipendeva da chi
> vinceva la corsa.
>
> ⛔ **E la cura era già scritta nel file, per il caso gemello.** `respinto-poi-congedo` porta
> questo commento: *«La chiusura di §3.1 partirebbe subito dietro al messaggio, e correrebbe contro
> la risposta della pagina… un banco che cambia verdetto fra due giri identici non misura la pagina:
> misura il carico della macchina»*. ⇒ Stessa cura, stesso posto: dopo `RESPINTO` il server guasto
> **tace**, e chi chiude sarà la pagina.
>
> ⚠ **E non è allargare l'atteso**: l'atteso resta `muta`, e il caso può ancora dire di no — se la
> pagina riprovasse, i byte in più li vedrebbe il **registro del server**, che è il testimone che
> quel caso dichiara da sempre (§8.1).
>
> ⭐ **Esito**: **CONFORME, 0 punti** contro il server guasto; **NON-CONFORME, 9 punti** contro
> quello sano, in 35 secondi. ⚠ Riserva scritta nel registro: **un motore solo** — Chrome non l'ha
> guardato, e con un motore solo la seconda strada di §3.1 non si vede.
>
> ⭐ **E B12 ha imparato a giudicarlo — R12-A.48.** Il modello sano/guasto/risano non gli si
> applica: il suo giro «sano» **dev'essere rosso**, perché è il controllo che dice *no*. `giudica()`
> ha ora un passo **`proprio-giro`** che pretende **tutt'e due le metà, esplicite** — ⛔ un giro che
> portasse solo *«il guasto è verde»* non certifica niente, perché sarebbe compatibile con una
> pagina che dichiara conforme qualunque cosa.

> ##### ⛔⭐ B13: la parola d'ordine in un indirizzo — e il banco aveva ragione da ieri
>
> B13 non si certifica perché **il suo soggetto è davvero rotto**, ed è la regola giusta: si lascia
> NON CERTIFICATO invece di allargare l'atteso finché torna. Oggi il difetto ha un nome — **rilievo
> R12-A.34**.
>
> `B13.2` — *«la parola d'ordine compare in 1 registri su 1288»* — indicava
> `sonda/racc.log`. ⛔ Non era un registro stantio da cancellare: **`sonda/lancia.sh` passava le
> credenziali nella query dell'indirizzo** (`&utente=prova&parola=…`), e la query fa parte della
> **riga di richiesta HTTP**, che ogni server registra per mestiere.
>
> ⚠ E la stessa pagina, venti righe più sotto, stampava *«CREDENZIALI mandate (la parola non compare
> in nessun registro)»*: una frase che si smentiva da sola nel file accanto.
>
> ⛔ **E il difetto era più largo del registro**: la parola stava anche nella sessione salvata di
> **due profili Firefox** (`prof-ammesso`, `prof-respinto`), perché l'indirizzo è passato dalla
> cronologia.
>
> ⭐ **Cura**: le credenziali passano nel **frammento** (`#`), che il browser **non manda al
> server** — quindi non entra in nessun registro HTTP, né nostro né di un proxy in mezzo. ⛔ E la
> seconda metà, che da sola avrebbe reso la cura una finzione: `lancia.sh` **stampava l'indirizzo**
> sul terminale, e il terminale di un giro finisce in un file come tutto il resto — adesso lo stampa
> mascherato.
>
> ⚠ **Che cosa la cura non chiude, detto qui e non altrove**: il frammento resta nella **cronologia**
> del browser. Per un banco con una parola di prova va bene; ⛔ **una pagina di prodotto non deve
> prendere la parola d'ordine da nessun pezzo dell'indirizzo**.
>
> ⛔ **E i registri sporchi NON sono stati cancellati**: farlo prima di aver verificato la cura
> sarebbe rendere B13 verde **buttando la prova**. Si buttano il giorno in cui un giro nuovo della
> sonda ne produce di puliti. ⚠ Resta inoltre aperta `B13.4` (*«qualcuno ascolta in TCP ma la pagina
> non si carica»*): B13 non si certifica finché non passano tutt'e due.
>
> ##### ⭐⭐ LA SERA DELL'11 AGOSTO: la cura regge, i registri sono buttati, e **B13 è certificato**
>
> ⭐ **Il giro nuovo della sonda l'ha verificata** `[M]` **11 agosto 2026, 12:54:33Z-12:54:53Z**, su
> **NIC-OS**, contro il **PRODOTTO** su `192.168.0.2:7481` (raccoglitore su `127.0.0.1:7482`,
> **Firefox 140.13.0esr**): `AMMESSO` e `RIFIUTATO`, **8 file prodotti**, ⛔ **zero registri con la
> parola dentro**. A contenerla restano i soli due **sorgenti** — ed è quel che `B13.2` dichiara di
> non chiamare rosso.
>
> ⛔ **E il giro nuovo ha trovato che la cura era scritta e non fatta.** `sonda-rcp.html` prometteva
> *«il profilo lo si butta a fine giro (`lancia.sh`)»*, e `lancia.sh` lo buttava all'**inizio**:
> quello dell'ultimo giro restava sul disco. ⚠ **E le prime due cure non hanno tenuto, ed è
> misurato**: profilo cancellato alle **12:49:54**, `recovery.jsonlz4` ricomparso alle **12:50:10**
> (2223 byte, la parola dentro) — Firefox era ancora vivo; poi, con `setsid` + `kill -- -$p`,
> ricomparso alle **12:51:31**, perché *«il gruppo è morto»* rispondeva **subito**: ⛔ **il controllo
> era muto, e un controllo muto ha la stessa faccia di un controllo che passa**. ⭐ Adesso si guarda
> in `/proc` **chi ha ancora quel profilo fra i propri argomenti** — mai `pkill -f` — e la
> cancellazione **si riverifica cinque secondi dopo**.
>
> ⭐ **Poi i registri sporchi sono stati buttati, e non prima**: `sonda/racc.log` e i **due profili
> Firefox interi**, **33 file**, di cui **5** contenevano la parola. ⛔ La traccia — nome, byte,
> `sha256`, data, e **se** la contenevano ma non **quale** — sta in `banchi/01-b13-buttati.jsonl`:
> buttare una prova senza lasciarne il conto è la seconda metà dello stesso difetto.
> ⇒ ⭐ **`B13.2` è verde**: *«la parola non compare in nessuno dei **1368** registri»*, denominatore
> **22 461 file**, **zero illeggibili**, col controllo positivo accanto.
>
> ⭐⭐ **`B13.4` si chiude, perché contro il prodotto ha finalmente un imputato**: la pagina si carica
> (**200, 31 083 byte**), porta l'**impronta corrente**, e **`/impronta` risponde**. **4 su 4**.
> ⚠ Contro l'**innesto** resterà `[?]` per sempre: lì nessuno ascolta in TCP.
>
> ⭐⭐ **E B13 è certificato** `[M]` **11 agosto 2026, 15:19**, NIC-OS: **sano 3 → guasto 1 → risanato
> 3**, col guasto di B12 (`pagina.pem` sostituito da `sessione.pem`) e la marca *«LE IMPRONTE
> COMBACIANO»* **nel suo punto** — più i **14 guasti costruiti a mano** di `--certifica`: **14 su
> 14** ⚠ **da utente normale**, e **13 su 14 da root**, perché i permessi `0000` non fermano root e
> ⛔ **un guasto saltato non è un guasto passato**. ⚠ **Tre deviazioni da B12, scritte dentro la riga
> di registro**: porta **7481** invece della 7447 · bersaglio il **prodotto** e non l'innesto · il
> ciclo condotto da uno script suo, perché `01-b12-lancia.sh` **scrive `PORTA=7447` in chiaro** e non
> si può puntare altrove.
>
> ⛔ **Che cosa resta aperto, e sono due**: **`B13.3`** — c'è un imputato (`src/certificati.c`, **45
> righe**) e questo banco **non lo interroga**: serve un banco che *installi* un certificato
> d'autorità e guardi che cosa il server presenta sul filo dopo · **`B13.5`** — **non misurata**: il
> credito letto dal pari è **19** (§2.3 ne vuole almeno 16), ma `aioquic` concede **tutti** i 23
> stream chiesti, quindi lo strumento non sa dire *no* e il suo *sì* non vale. ⚠ È un difetto del
> **banco**, non del server.
>
> ⛔⭐ **E la prima riga di registro di B13 non contava, e ci sono volute due letture per accorgersene.**
> Il banco era certificato e il rapporto lo diceva; ⚠ ma `01-b12-guasti.py --registro` classificava
> B13 fra le certificazioni **NON RIVERIFICABILI**, cioè **non lo contava**. ⛔ E il motivo non era
> *«mancano le impronte»*: le impronte c'erano, **sotto nomi che il catalogo non conosce**
> (`01-b13-sera-certifica.sh`, `src/rcp.c`, `src/pagina.c`). `FILE_CHE_CONTANO["B13"]` ne nomina
> **due** — `01-b13-proprieta.py` e `rcp/rcp.c` — e `confronta_impronte()` scorre le chiavi vecchie
> con un `get`: ⛔ **una sola chiave fuori catalogo manda l'intera riga in *«non si sa»***.
> ⭐ **Lo strumento aveva ragione, e per la ragione giusta**: *«non so se valga oggi»* non si
> arrotonda a *«certificato»* (`LEZIONI.md` §1.9).
> ⭐ **E la correzione è una riga NUOVA, non una riga riscritta**: quella delle 15:07 resta dov'è, e
> quella delle 15:19 dice perché esiste. ⚠ *E si è visto perché serviva anche l'altra metà della
> cura: fra un `--put` dell'intero registro e il successivo, il server aveva guadagnato **una riga
> di un altro agente** — che un `--put` avrebbe cancellato in silenzio.*
>
> ⚠ **E la riga porta scritta dentro una riserva che altrimenti non si vedrebbe**:
> `FILE_CHE_CONTANO["B13"]` nomina `rcp/rcp.c`, la copia dei **banchi**, mentre il ciclo ha misurato
> il **prodotto**. Oggi le due copie sono identiche byte per byte (`84411b9c…`) — ⛔ **per
> combinazione, non per costruzione**: il giorno in cui divergono, quella riga riverificherà il file
> sbagliato e continuerà a dire di sì.
>
> ⭐ **E la cartella `sonda/` non era nel deposito**: come i quattordici file del 10 agosto, viveva
> solo sul server. Adesso sta in `banchi/sonda/`.
>
> ---
>
> #### ⛔ Che cosa B12 ha certificato DAVVERO: **3 su 12** — all'11 agosto 2026, *mattina*
>
> ⚠ *Il riquadro qui sotto è lo stato di stamattina, ed è tenuto perché spiega da dove si partiva.
> Il conto di oggi sta nel riquadro qui sopra.*
>
> *Scritto qui perché è la domanda che vale doppio, e la risposta non stava in nessun documento: il
> `README.md` diceva «sei verdi» nello stesso momento in cui il registro di B12 ne certificava due.
> ⛔ **«Verde» e «certificato» sono due cose diverse** — verde vuol dire che il banco ha girato e non
> ha trovato niente; certificato vuol dire che qualcuno **gli ha rotto sotto il codice** e il banco è
> diventato rosso, e sulla marca giusta. È la seconda che dice se la prima valga qualcosa. Rilievo
> **R12C.16**, e il conto viene da `banchi/01-b12-registro.jsonl` letto riga per riga l'11 agosto.*
>
> ⛔ **E le parole sono quattro, non due**, perché quattro sono gli stati:
>
> | Banco | Stato | Quando, e su che cosa |
> |---|---|---|
> | **B4** | ⭐ **certificato** | 11 ago 00:27, macchina `CHUWI`, con le impronte dei **tre file che partecipano** (`01-b4-lancia.py`, `01-b4-validatore.py`, `01-b4-registrazioni.py`) |
> | **B9** | ⭐ **certificato**, ⚠ **con una riserva scritta** | 11 ago 00:27, `CHUWI`, impronte di `01-b9-letture.py`, `01-b3-cliente.py` e di `RCP.md`. ⚠ Il guasto costruito per lui **cancella una citazione** del documento: quel che dimostra è che B9 sa vedere **un testo cambiato**, che è la cosa che B9 dichiara apertamente di saper fare — **non** che sappia vedere il secondo lettore allinearsi al primo (rilievo **A8**) |
> | **C2** | ⭐ **certificato** | 10 ago 22:32, macchina `NIC-OS`, con una marca **discriminante** — cioè che nel giro sano **non compare** |
> | **B13** | ⛔ **provato e NON certificato** | 10 ago 22:24 e 22:25, due volte. ⛔ E il motivo è del **guasto, non del banco**: è di tipo «riga di comando» e l'orchestratore non lo sa innestare; e anche innestandolo a mano costruirebbe un difetto che **B13.1 non guarda** (rilievi **A1**, **A2**) |
> | **B7** | ⚠ **certificato e NON riverificabile** | 10 ago 21:19. ⛔ La marca pretesa era la parola `CONGEDO`, che `01-b7-congedo.py` stampa **37 volte** e anche nel giro **sano**: *«una marca che compare in tutt'e due i giri non è una marca, è un modo di certificare senza guardare»* (rilievo **A3**). E quel giro non ha lasciato le impronte per banco |
> | **B2 · B3 · B5 · B6 · B8 · B10 · B11** | ⛔ **mai provati** — sette | nessun giro di B12 li ha toccati |
>
> ⛔ **Il conto onesto: 3 certificati su 12**, uno provato e non riuscito, uno non riverificabile,
> sette mai provati. ⚠ **Non si arrotonda a «quattro»** (il numero che il registro ha dichiarato alle
> 21:19) **né a «sei»** (i verdi del README): *«provato e non riuscito»* e *«mai provato»* hanno due
> cure diverse, e un registro che le fonde le fonde sempre **nella più innocente**.
>
> ⚠ **E il denominatore va dichiarato, o è un conteggio senza denominatore**: i dodici di questa
> tabella sono **il catalogo di B12**, che comprende **B10** — il quale non ha uno script suo — ed
> esclude **B12**, che non certifica sé stesso. ⛔ **Non sono gli stessi dodici** dei banchi scritti
> (i prefissi in `banchi/`, che comprendono B12 e non B10): due insiemi di dodici che si somigliano
> e non coincidono, ed è precisamente il modo in cui un conteggio smette di essere una misura.
>
> ⭐ **E due difetti del registro stesso sono stati curati la notte del 10, e vanno detti perché
> spiegano perché il conto di ieri non tornava**:
> · il campo si chiamava **`mai_provati`** ed era *«mai provati **in questo giro**»*: B7 e C2,
>   certificati alle 21:19, alle 23:01 comparivano come **mai provati**, e B13 passava da *«provato e
>   non riuscito»* a *«mai provato»* — con la **stessa** impronta del codice (rilievo **A4**). Adesso
>   il campo si chiama `non_provati_in_questo_giro`;
> · l'impronta annotata era quella di `banchi/rcp/rcp.c` **anche per i banchi in cui `rcp.c` non
>   entra affatto** (B4, B9, C2): un denominatore che promette una cosa e ne misura un'altra, cioè
>   **peggio di nessuna impronta**, perché dà alla riga l'aria di essere già stata controllata
>   (rilievo **A5**). Adesso ogni riga porta le impronte **dei file che partecipano davvero**.

> #### ⭐ P1 e P5 entrano nel catalogo, e il denominatore cambia — la sera dell'11 agosto 2026
>
> Il `README.md` lo diceva con un numero: *«P1 e P5 non sono nel catalogo di B12: i banchi sono 14,
> le voci 12»*. ⛔ E quei due non erano «puliti»: erano **due banchi mai diventati rossi**, cioè la
> definizione di NON CERTIFICATO — ⛔ **e sono i due che guardano il PRODOTTO**, l'unica cosa di
> questa fase che un utente vedrebbe.
>
> ⛔ **Il denominatore vero, contato e non ricordato** (`ls banchi/`): **22** prefissi `01-`, che non
> sono 22 banchi — **14 banchi** (B2 B3 B4 B5 B6 B7 B8 B9 B11 **B12** B13 C2 **P1 P5**), **1
> attrezzeria** (`01-b0-*`) e **7 sonde del Gruppo 1** (S1b S2 S3a S5 S6 S7 S-telefono), che sono
> misure e non banchi che si certificano. Le voci del catalogo passano da **12 a 14**.
> ⚠ ⭐ **E non sono gli stessi quattordici**: il catalogo comprende **B10** ed esclude **B12**, che
> non certifica sé stesso. ⇒ I banchi che il catalogo può certificare sono **13**, e le voci che
> hanno un banco dietro sono **13**: due insiemi che adesso **coincidono**, mentre prima di stasera
> erano dodici e dodici **diversi** — cioè il conto tornava e contava cose che non erano le stesse.
>
> | | |
> |---|---|
> | ⭐⭐ **P1 è CERTIFICATO** | `[M]` NIC-OS, porta **7501**, tre giri alle **12:56:20 · 12:56:56 · 12:57:24 UTC**: **0 → 1 → 0**, VERDE 34/34 → ROSSO 33/34 → VERDE 34/34. Guasto: `Cross-Origin-Opener-Policy` da `same-origin` a **`unsafe-none`**. Marca `MANCA: Cross-Origin-Opener-Policy: same-origin`, misurata **0 · 2 · 0** |
> | ⭐ **e il rosso è di UN controllo solo** | `costruzione.esito` resta **0** e `binario.marche` resta **8/8**: il guasto **non** è passato per una compilazione fallita, che renderebbe rosso qualunque banco e certificherebbe **zero** |
> | ⛔ **e la prima stesura del guasto sarebbe stata proprio quella** | toglieva **l'intestazione**. ⚠ Ma `src/costruisci.sh` **cerca `Cross-Origin-Opener-Policy` dentro il binario e si ferma se non la trova**, e la cerca anche P1 fra le sue otto marche. ⭐ Preso **leggendo `costruisci.sh` prima di innestare**, e la cura è nella forma del guasto: **si cambia il valore, si lascia il nome** |
> | ⛔ **P5 è PROVATO e NON CERTIFICATO** | e non *«non provabile»*, che è l'altra cosa. ⭐ Ma il suo conto è cambiato due volte in un'ora, e la seconda in meglio |
> | ⛔⛔ **ATTENZIONE: le due righe qui sotto sono state SMENTITE la sera stessa** | ⭐ Il banco aveva davvero un difetto — `ctrl+w` sul display sbagliato, ed è vero — ⛔ **ma l'assoluzione che ne è seguita era falsa**: l'arbitrato contava una chiusura **senza guardarne il motivo**. Il difetto del prodotto **c'è, su tutt'e due i motori**. Si leggano queste righe **fino in fondo al riquadro**, dove la misura le corregge |
> | ⭐⭐ **e l'accusa al PRODOTTO era del BANCO** *(riga smentita — vedi sotto)* | ⛔ P5 scriveva *«nessun congedo, per nessuna delle due strade di §3.1»* — cioè accusava la pagina di violare §8.1 **per un gesto mai fatto**: `01-p5-lancia.sh` batteva `xdotool key ctrl+w` **senza la funzione `X`**, su un `DISPLAY` che non è lo schermo finto. Il tasto non arrivava, `pagehide` non scattava. ⭐ **L'arbitrato è `banchi/01-p5-congedo.sh`** `[M]` **13:26 UTC**: si va via in **due modi** — navigando via, dove `pagehide` scatta di sicuro, e con `ctrl+w`, dove scatta solo se il tasto arriva — e ⭐ **da tutt'e due il congedo ESCE** (strada 2 di §3.1, posto `LASCIATO`, **zero** `STACCATO per silenzio`, e il gesto verificato dalle finestre **1 → 0**). ⇒ **La pagina fa quel che §8.1 le impone.** ⚠ È `LEZIONI.md` §1.9 di nuovo, e **la seconda volta in questa fase dopo B3**: il rosso puntato sull'imputato sbagliato |
> | ⭐ **e il testimone è stato scelto bene** | il registro **del server**, letto a **+8 s** — prima che il tetto dei 30 secondi possa liberare il posto: senza quella finestra, *«si è congedato»* e *«staccato per silenzio»* arrivano con la stessa faccia. ⚠ *E il primo giro dell'arbitrato ha sbagliato lui: il segmento si chiudeva sul marcatore di fine, mentre `pagehide` scatta **mentre quella richiesta è in volo**, e la riga del congedo cadeva fuori. Uno zero da segmento sbagliato ha la stessa faccia di uno zero vero — vale il **secondo** giro* |
> | ⭐ **curato il pilota, i numeri si muovono** | `X` davanti al `ctrl+w`, e `fuoco` portato **fuori dal ramo di N2** — con lo sblocco che non risponde quel ramo si saltava, e si arrivava alla gamba `P` **senza aver mai dato il fuoco a nessuna finestra**. `[M]` giro sano **13:29:41 UTC**: ⭐ **Chrome passa a CONFORME**, e ⭐ **Firefox adesso MISURA** — arriva a `SESSIONE`, **14 su 15**, secondo fisso **1069 ms** — dove prima non aveva denominatore |
> | ⛔ **e resta UN punto, che questa volta NON è del banco** | su **Firefox** il congedo non esce lo stesso: dal registro del server il client chiude con un **`FIN` nudo sul canale di controllo**, il posto è `LASCIATO` **in modo ordinato** e `STACCATO per silenzio` vale **0**. ⇒ **Il gesto è arrivato, la sessione si è chiusa bene, e il client non ha detto perché** — dove §8.1 lo impone senza condizioni. ⚠ **I due imputati residui non si distinguono da questa parte**: *«la pagina non spedisce»* e *«Firefox butta via quel che la pagina spedisce dentro `pagehide`»* arrivano identici al server, e a separarli serve il registro **del browser**. ⭐ E si noti che la pagina prevede il caso **opposto** — *«Chrome butta un messaggio spedito subito prima di chiudere, quindi la strada che regge è il codice di chiusura»* — mentre su Firefox non regge **nessuna** delle due: è la differenza fra motori per cui P5 esiste, ⛔ **e è comparsa solo DOPO aver curato il pilota**, che è la prova che le due colonne servono |
> | ⭐ **e il guasto di P5 è misurato lo stesso** | la marca `sono due impronte diverse per lo stesso certificato di sessione` compare **1** volta nel giro rosso e **0** nel sano: il banco **vede** il proprio guasto. ⇒ P5 non si certifica perché **il suo giro sano non è verde** — la stessa forma di B8 — **non** perché sia cieco |
>
> ##### ⛔⛔ E POI LA MISURA HA SMENTITO L'ASSOLUZIONE: **il congedo non esce, ed è della PAGINA**
>
> *`[M]` 11 agosto 2026, sera, `banchi/01-p5-ff-*`. ⛔ Due giri identici per motore, su una **copia
> strumentata** di `src/pagina.html` servita da un server a parte — il prodotto non è stato toccato.
> Il tracciatore è `navigator.sendBeacon`, cioè **un portatore che non passa da WebTransport**: se
> passasse di lì condividerebbe il destino della cosa che si misura.*
>
> ⛔ **L'imputato è la pagina, e Gecko è scagionato per misura.** Chiudendo la scheda con `ctrl+w`
> **a browser vivo**, su Firefox 140.13.0esr `pagehide` **scatta** — e la traccia della pagina dice
> `congeda_corrente NULLA`. ⇒ Il gestore di `src/pagina.html:331` è **codice morto**: il `finally`
> del gestore di `submit` (riga **620**) azzera `congeda_corrente` **un millisecondo dopo
> `SESSIONE`**, perché `collega()` ritorna lì. Il posto se ne va dopo `STACCATO per silenzio:
> 30060 ms`.
>
> | variante, stesso motore e stessa scena | `pagehide` | `congeda()` chiamata | che cosa arriva al SERVER |
> |---|---|---|---|
> | **fedele** — il prodotto com'è | ⭐ **1** | **0** | ⛔ **niente** |
> | **tenace** — la *stessa* `congeda()`, riferimento non azzerato | 1 | 1 | ⭐ **`CONGEDO` sul canale + codice `0x01`** |
> | **codice** — solo `wt.close(0x01)` | 1 | — | ⭐ codice `0x01` |
> | **vivo** — la stessa `congeda()`, scheda **viva** | — | 1 | ⭐ `CONGEDO` + codice `0x01` |
>
> ⇒ ⭐ **Firefox non butta via niente**: dentro `pagehide` funzionano **tutt'e due** le strade di
> §3.1. **Manca solo chi le imbocchi.**
>
> ⛔⛔ **E il ⭐ di Chrome era un FALSO VERDE — è il rilievo che vale di più.** Nella stessa scena,
> su Chrome, la pagina non spedisce niente e al server arriva **lo smontaggio di Chrome**:
>
> ```
> ⛔ VIOLAZIONE §3.1 — la pagina ha chiuso la sessione col codice 0x0 … A verbale va ERRORE_PROTOCOLLO
> la pagina ha chiuso la sessione, motivo 0x0b
> ```
>
> ⛔ `01-p5-congedo.sh:318` conta la riga *«la pagina ha chiuso la sessione, motivo»* **senza
> guardare il motivo**: ha contato **una violazione di §3.1 come un congedo**, e ha stampato
> *«⭐⭐ LA PAGINA FA QUEL CHE §8.1 LE IMPONE»*. ⇒ ⭐⭐ **I due motori non erano opposti: mostravano
> lo STESSO difetto della pagina attraverso due smontaggi diversi**, e su uno dei due il banco è
> inciampato nel proprio contatore. ⚠ *E il server lo diceva*: la riga di violazione la scrive lui,
> ed era nel registro.
>
> ⭐ **La cura è di tre righe, ed è DESCRITTA E NON APPLICATA** — la fase era chiusa da un'ora, e una
> cura di prodotto infilata dopo la chiusura non è una cura, è un cambiamento non dichiarato.
> L'ancora di `congeda_corrente` è sbagliata: non è *«il tentativo è finito»*, è ⭐ ***«la sessione è
> finita»***. ⇒ togliere l'azzeramento dal `finally` (riga 620) · azzerarlo dentro
> `wt.closed.then(…)` di `collega()`, l'unico punto che sa quando la sessione non c'è più · lasciare
> quello a inizio gestore (riga 606), perché un tentativo nuovo deve buttare il riferimento vecchio.
>
> ##### ⭐⭐ E POI LA CURA È STATA APPLICATA E RIMISURATA — **due giri per motore, e il difetto non c'è più**
>
> *`[M]` 11 agosto 2026, tarda serata, `banchi/01-p5-ff-*` sulla **7511**, registro in
> `banchi/01-p5-ff-registro-cura.log`. ⛔ **L'atteso è scritto in
> `banchi/01-p5-ff-strumenta.py` PRIMA di misurare**, ed è quello il documento che dà il verdetto:
> «`fedele` deve comportarsi come `tenace`; `eco` deve dire `congeda_corrente PRESENTE`; gli altri
> tre invariati».*
>
> | la stessa scena, `ctrl+w` su due schede | PRIMA della cura | DOPO, due giri per motore |
> |---|---|---|
> | **Firefox** — `pagehide` | scatta, guardia **NULLA** | scatta, guardia ⭐ **PRESENTE** |
> | **Firefox** — `congeda()` | **0** | ⭐ **1** |
> | **Firefox** — al server | ⛔ **niente**, `FIN` nudo e `STACCATO per silenzio` | ⭐ `CONGEDO` sul canale **+** codice **`0x01`** |
> | **Chrome** — al server | ⛔ chiusura col codice **`0x0`**, che §3.1 **vieta** e che il server mette a verbale | ⭐ `CONGEDO` sul canale **+** codice **`0x01`**, e **zero** violazioni |
> | **`fedele` contro `tenace`** | due colonne diverse: era **lì** il difetto | ⭐ **non si distinguono più** — ed è la definizione della cura, visto che `tenace` era la variante che la scavalcava |
>
> ⭐ **E la traccia più bassa dice la stessa cosa da sotto**: `finally-congeda_corrente-PRESENTE-cura-in-vigore`
> è arrivata in **10 varianti su 10** (cinque per motore), e `fine-sessione-lascio-il-mio-riferimento`
> dove la sessione si chiude davvero ⇒ il riferimento si lascia andare **una volta sola, alla fine
> della sessione**, che è esattamente l'ancora nuova. Su Firefox anche per via **sincrona**
> (`eco-congeda_corrente`: **NULLA → PRESENTE**, in tutt'e due i giri).
>
> ⛔ **Tre cose che la misura ha aggiunto e che nell'atteso non c'erano**, e si scrivono:
>
> | | |
> |---|---|
> | ⛔ **il tracciatore del banco è CIECO su Chrome dentro `pagehide`** | non esce **né** `sendBeacon` **né la XHR sincrona** di `eco`: sei giri, zero tracce. ⇒ Su Chrome l'attribuzione poggia **solo** sul registro del server — che però è netto, perché fra prima e dopo cambia **la riga della violazione**. ⚠ E spiega a posteriori tutte le colonne a zero dei giri di Chrome: non erano un silenzio del prodotto, erano un silenzio del **portatore** |
> | ⚠ **una corsa vista una volta sola su sei giri** | nel `vivo` delle 18:54 su Firefox il `CONGEDO` **sul canale** non è arrivato, benché la pagina avesse visto *«la write si è risolta»* e *«il FIN del canale è passato»*. È la stessa corsa che **B11 ha misurato su Chrome** (difetto 2). ⛔ **Non tocca §8.1**: il motivo `0x01` è arrivato lo stesso, per il **codice di chiusura** — cioè per la strada che `DECISIONI.md` §7.14 ha scelto **proprio per questo**. ⚠ Una osservazione non è una misura: si scrive e non si conclude |
> | ⭐ **e `eco` su Chrome è il controllo negativo che nessuno aveva chiesto** | lì la chiusura col codice **`0x0`** c'è **ancora**, con la violazione a verbale — ed è giusto: `eco` esce da `pagehide` **senza spedire niente**, cioè è il prodotto **di prima**. ⇒ Il `0x0` non è sparito dal motore: sparisce **quando qualcuno congeda** |
>
> ⛔ **E che cosa questa misura NON dice.** Gira su una **copia strumentata** di `src/pagina.html`
> servita da un server a parte: il prodotto di casa non è stato acceso, e vale la riga di sempre —
> *«nessun banco ha mai acceso `src/`»*.
>
> ##### ⛔⭐ E LA CURA NE HA SCOPERTA UN'ALTRA SOTTO: **il posto che si libera in silenzio**
>
> *Trovata curando la scena di P5, `[M]` la tarda serata dell'11 agosto 2026 — e non cercandola.*
>
> ⛔ **Il difetto.** `src/rcp.c` libera il posto in **quattro** punti, e **tre** lo scrivono nel
> registro. Il quarto — `CONGEDO` ricevuto dal client — no. ⇒ Sulla strada che **§8.1 impone**, cioè
> quella che il prodotto sano percorre sempre, il registro **non porta nessun** `posto LASCIATO`.
>
> ⚠ **E il posto si liberava davvero**: `[M]` dodici sessioni di fila nei registri della sera, e
> **ogni** `posto PRESO` successivo dice `occupati adesso: 1`. Non era una perdita — era che
> **l'invariante §8.2 `0x0F` non si poteva più osservare**. ⛔ E la conseguenza è concreta: P5
> **giudica il numero finale** di `occupati adesso`, non lo trovava, e avrebbe scritto *«IL POSTO NON
> SI È LIBERATO»* su un server che aveva fatto il suo mestiere — un rosso all'imputato sbagliato, la
> settima veste di `LEZIONI.md` §1.9 per la **terza** volta in questa fase.
>
> ⭐ **Ed era invisibile fino a stanotte**: prima della cura del congedo il client non si congedava
> **mai**, quindi quel ramo non veniva percorso e il posto se ne andava sempre per il tetto
> d'inattività — che la sua riga la scrive. ⇒ **La cura ha scoperto il difetto che la cura stessa
> rendeva raggiungibile.**
>
> | il giudice di P5 sullo stesso genere di segmento | guasti |
> |---|---|
> | prima della cura del congedo (Chrome) | ⛔ **2** — *«nessun congedo per nessuna delle due strade»* **+** *«violazione-31 trovate=1 atteso=0»* |
> | curato il congedo, non ancora il posto | ⛔ **1** — *«IL POSTO NON SI È LIBERATO»*, **e era falso** |
> | curato anche il posto | ⭐ **0**, strada *«congedo del client (posto LASCIATO)»* — `[M]` **due giri per motore**, quattro su quattro |
>
> ⛔ **E «zero guasti» non vuol dire «P5 è certificato».** Quel che è verde è **il giudice di P5 su
> un segmento vero** prodotto dal prodotto curato; il **giro di P5** — col suo guasto innestato, le
> due colonne e tutta l'impalcatura — **non è stato fatto**. Sono due parole diverse, e questa fase
> le ha già confuse una volta.
>
> ##### ⭐⭐ E ALLORA P5 È STATO RILANCIATO — la gamba che contava è **VERDE su tutt'e due i motori**
>
> *`[M]` la notte fra l'11 e il 12 agosto 2026, contro una **copia del prodotto curato** sulla
> **7501** (`banchi/01-p5-accendi.sh`, scritto stanotte: la ricetta stava in prosa dentro il
> catalogo dei guasti, e una ricetta in prosa la ricopia a mano chi la usa).*
>
> | | |
> |---|---|
> | ⭐⭐ **`p-sessione`: CONFORME, Chrome E Firefox** | 15 controlli, **0 guasti**: congedo per **tutt'e due** le strade col motivo `0x01`, `violazione-31` a **zero**, posto **preso e lasciato**. ⇒ Il punto che teneva P5 fuori dal verde **non c'è più** |
> | ⭐ **e la gamba N2 gira, per la prima volta da quando esiste** | bastava poter passare da `sudo`: `SSH_ROOT` sceglie il portatore dei comandi privilegiati (`fondamenta/strumenti/sshpw.py` digita la password su un pty), e lo sblocco di §4.4-bis risponde `PONG`. ⛔ E i due portatori restano **due**: `sshpw.py` lascia due righe di preambolo nel proprio stdout, e usarlo anche per **scaricare** il registro sporcherebbe la prova con lo strumento che la raccoglie |
>
> ⛔ **E due difetti del PILOTA sono venuti fuori uno dopo l'altro, tutti e due trovati da una
> FOTOGRAFIA** — cioè dalla cosa che questo banco scatta dicendo *«materiale per chi legge, NON un
> verdetto»*:
>
> | | trovato da | e la cura |
> |---|---|---|
> | ⛔ **il browser di N1 sopravvive, e la gamba dopo ci si attacca** | `firefox-n2-parola-sbagliata-1-pagina.png`: Firefox con **tre schede** — due della sonda di N1 — ferma sul marcatore d'avvio, dopo due `ctrl+l`+indirizzo+`Invio` andati nel vuoto | `kill` ammazza il processo ma **la finestra resta**, e la gamba dopo riusa **lo stesso profilo**: il browser nuovo non nasce, si attacca al vecchio come scheda in più. ⭐ Cura **già in casa**: è quella che `01-p5-ff-lancia.sh` aveva misurato lo stesso giorno |
> | ⛔ **la striscia dei dati sposta la pagina di ~23 px** | `firefox-0-avviso-non-superato.png`: l'avviso del certificato **non superato**, con la barra *«Firefox automatically sends some data…»* in cima | i due clic di `supera_avviso` stanno a coordinate **misurate**, e con la barra cadono **sopra** i bottoni. ⭐ La cura non è spostare le coordinate — è **togliere la barra**, così la misura da cui quei numeri vengono torna a valere |
>
> ⛔⭐ **E il secondo lo nascondeva il primo**: finché la gamba del prodotto riusava il browser di N1,
> la striscia se l'era già mangiata la sessione precedente. ⇒ *Curato un difetto, il secondo è
> comparso* — ed è la stessa forma del `posto` muto qui sopra, due volte nella stessa notte.
>
> ⚠ **E il banco ha fatto la cosa giusta la prima volta che è successo**: la gamba N2 su Firefox non
> ha dato un rosso, ha detto **SENZA-DENOMINATORE**. È il controllo aggiunto curando la scena, e ha
> funzionato al primo caso vero.
>
> ⭐⭐⭐ **E LA CERTIFICAZIONE È FATTA: `0 → 1 → 0`** — `[M]` la notte fra l'11 e il 12 agosto 2026,
> i tre giri `sano → guasto → sano` per intero contro la copia sulla **7501**, con i browser su
> CHUWI e il prodotto su NIC-OS. `01-b12-registro.jsonl`, riga delle 21:02 su CHUWI, con l'impronta
> dei tre file su cui poggia.
>
> | | |
> |---|---|
> | ⭐ **sano: VERDE su due motori** | n1 giusta/storpiata `ok`, N2 **11 controlli 0 guasti**, `p-sessione` **15 controlli 0 guasti**, Chrome **e** Firefox |
> | ⭐ **guasto: ROSSO, e nomina la cosa giusta** | *«la pagina pubblica «AAAA…=» e l'endpoint dice «PJ03…=»: sono due impronte diverse per lo stesso certificato di sessione»* — il difetto **R1.14** |
> | ⭐ **e la marca è una marca** | `[M]` **0** volte nel sano, **1** nel guasto, **0** nel risanato — contate sui tre giri di quella notte, non su una misura di ieri |
> | ⭐ **risanato: VERDE, e il binario torna identico** | `d69df441…` → `117911ca…` → `d69df441…`: che il guasto sia entrato e poi uscito lo dice **l'impronta del binario**, non il colore del verdetto |
>
> ⛔ **E il guasto dimostra MENO di quel che il suo titolo dice.** Con l'impronta falsa nella pagina
> le gambe `p-sessione` restano **CONFORMI**: la sessione **si apre lo stesso**. ⭐ La ragione è del
> prodotto ed è §4.1-bis applicato — `pagina.html` **ritira `/impronta` prima di ogni tentativo** e
> usa quella, tenendo l'impronta servita solo come ripiego, e **dice** quando le due divergono.
> ⇒ Il guasto prova che **P5 vede la divergenza**, che è ciò per cui P5 esiste; **non** prova che la
> divergenza uccida la sessione, perché su questo prodotto non la uccide. ⚠ Il sintomo descritto in
> R1.14 resta quello di un prodotto che l'impronta **non** la ritira.
>
> ⛔⭐ **E il primo tentativo di giro sano è uscito ROSSO con tutt'e quattro le gambe CONFORMI** — la
> contraddizione fra la tabella e la riga finale era il sintomo. L'imputato l'ha nominato una riga
> che `grep` stampa da sé: `binary file matches`. Il registro del server aveva un **buco di 37.120
> byte NUL** (`svuota-registro` chiamato a server vivo), `grep` diventava cieco **con stato d'uscita
> 0**, e il banco mandava lo sblocco di §4.4-bis **sul server invece che su di noi**. Tre cure,
> tutte rimisurate; la lezione è `LEZIONI.md` §1.9 punto 9.
>
> ✅ **E la cura è un cambiamento di prodotto dopo la chiusura della fase, quindi è stata
> DICHIARATA**: `DECISIONI.md` §1.12, dall'utente la stessa notte. ⛔ **La fase 1 non si riapre** e
> la certificazione resta **12 su 14** com'è stata consegnata — questa sezione è un'**appendice
> datata**, e non cambia un numero del documento. ⭐ **E la cura non si arretra**, perché è misurata
> con lo stesso rigore della fase. ⇒ Alla fase 2 passa la **ricertificazione di P5**, che non passava
> proprio per questo difetto — ⚠ e vuole prima la cura della sua scena, che chiude ancora `ctrl+w`
> sull'**unica** scheda.
> ⭐ *Aggiornamento della stessa notte: la scena è curata, e **la ricertificazione di P5 non passa
> più alla fase 2 — è fatta**, qui sopra. ⛔ Quel che passa alla fase 2 è invece la **riesecuzione di
> sette certificazioni scadute**: la cura di §1.12 ha toccato `rcp.c` e `RCP.md`, e `--registro` le
> conta come non certificate — B3, B5, B6, B7, B8, B13 e B9. Il conto sta in `README.md`.*
>
> ⚠ *Un giro è stato **annullato**, e sta scritto in `01-p5-ff-esiti.jsonl`: il **PC dei browser si è
> resettato a giro aperto** alle 18:40. L'ultima traccia al server è `ffm-183953-29125-fedele-avvio`,
> nessun esito è stato scritto e lo sblocco «dopo» non è mai partito. ⛔ Non conta né a favore né
> contro, e la coppia di giri concordi è stata rifatta da capo.*
>
> ⚠ **E due rilievi per i banchi, che valgono oltre questo caso**: *(a)* si conta **`motivo 0x01`**,
> non *«una chiusura qualunque»* — un contatore che non legge il motivo trasforma una violazione in
> un verde; *(b)* ⛔ **`ctrl+w` sull'unica scheda fa USCIRE Firefox**, e in quella scena non esce
> niente per **nessuna** via, nemmeno per le varianti che scavalcano il difetto: **la scena va fatta
> con due schede**, o si misura l'uscita del programma invece della chiusura di una scheda. *Era la
> scena di P5.*
>
> ⛔ **E tutt'e due i guasti si innestano su una COPIA INTERA del prodotto**, mai su
> `/media/REMOTIX/src/remotix/`. ⚠ La ragione **non** è quella dei guasti in Python degli altri
> banchi: è che **P1 ricostruisce il binario come primo passo del proprio giro**, e guastare il
> prodotto di casa lascerebbe, per i minuti del passo di mezzo, **un binario bugiardo sotto i piedi
> di chiunque altro lo riaccendesse**. *La sera dell'11 agosto sulla macchina di prova c'era un
> `remotix` vivo sulla 7448 e cinque agenti al lavoro insieme.*
>
> ⭐ **E `01-p1-prodotto.sh` e `01-p1-dentro.sh` accettano da stasera `PORTA`, `PORTA_MORTA`, `SORG`
> e `PREFISSO_TMP`**, coi predefiniti di prima: chi lancia a mano misura quel che misurava.
>
> #### ⭐⭐ B8 CERTIFICATO — e la cura non è stata completare la copia, è stata TOGLIERE la copia
>
> | | |
> |---|---|
> | ⭐ **B8** | **certificato, e non lo era mai stato**: `[M]` 11 agosto 2026, **13:46 UTC**, NIC-OS, innesto, porta **7471** — **`5 → 1 → 5`**, marca *«N risposte sotto il secondo»*, vista **solo** nel rosso |
> | ⛔ **e l'atteso sano è 5, non 0** | ⭐ **scritto nel catalogo prima del giro, non allargato dopo**: è il quinto esito di B8 — *«il ban passa per intero, ma le mediane si separano»* — e si concede **solo** perché l'imputato è **misurato** ed è **PAM**. ⭐ Il giorno in cui quel `[?]` si chiudesse, il sano diventerà **0** e **quella riga del catalogo diventerà rossa da sé**: è il modo giusto di accorgersene |
> | ⭐ **il guasto dà un rosso pieno** | `RITARDO_FISSO` da 1000 a **0**: `[M]` **17 risposte sotto il secondo**, la più veloce **49,7 ms**, e la mediana del caso «parola giusta» da **1085,9** a **56,3 ms** |
> | ⭐ **e il giro copre finalmente la sequenza intera** | **due vite del server** — la seconda accensione dichiara *«ban caricati: 1»*, cioè il ban torna **dal disco** e non dalla memoria (**I7**) · **la pagina** (HTTP **200**, `bannato=True`, *«tentativi esauriti»*, **12h 0m**, col controllo che dice no a 594 byte) · **lo sblocco su un ban vero** (`TOLTO` → poi `NON-BANNATO` → e l'indirizzo **rientra**) |
> | ⭐ **il segreto NON trapela** | mediane `[M]`: **inesistente 2123,2 · sbagliata 2198,1 · giusta 1085,9 ms**; la coppia che §4.4 protegge — *«inesistente − sbagliata»* — vale **−74,8 ms**, intervallo **[−509,3; +255,7]** ⇒ ⛔ **non si separa**. E l'imputato del resto è misurato: il server ha atteso **+1034 ms** oltre il secondo fisso sui respinti e **+84 ms** sugli ammessi — la firma di `pam_faildelay` |
> | ⚠ **e i due denominatori accanto** | la certificazione **fuori dal filo** 33 su 33, e il **giudice** di B8 15 su 15 guasti a mano, in tutt'e tre i passi |
>
> ⭐⭐ **E la cura strutturale è il punto 4 dell'elenco, fatto dove mordeva.** `01-b12-lancia.sh`
> **riscriveva a mano** la sequenza di B8, e la copia era incompleta in tre punti: il giro sano
> usciva rosso su **otto** punti che parlavano **dell'orchestratore, non del banco**. ⇒ Adesso
> `gira()` **chiama `01-b8-lancia.sh`** — come faceva da sempre con C2, quindi è un precedente in
> casa e non una deroga inventata — e la marca la legge dal file che il verdetto di B8 scrive da sé.
> ⚠ **E si è fermato lì apposta**: estendere la cosa agli altri banchi stasera avrebbe cambiato il
> modo di lanciare banchi **certificati oggi**, cioè invalidato nove certificazioni per rifarle in un
> tempo che non c'era.
>
> ⛔ **Che cosa questa certificazione NON copre**, e va detto: B8 è certificato **contro l'innesto**.
> Sul **prodotto** i tre appigli della pagina del ban esistono, ⚠ ma il giro non è stato fatto lì; e
> **la pagina la legge un socket, non un browser**, mentre questa sezione ne chiede il DOM *«come per
> le otto frasi di B7»*.
>
> ⚠ **E la certificazione di P1 non si riverifica da CHUWI**: la sua riga elenca `remotix/pagina.c`,
> che da `banchi/` esiste **solo sul server** — qui il prodotto sta in `../src/`. ⛔ Quindi
> `--registro` la classifica *«non si può dire se valga oggi»*, ed è **la scena di B9 al contrario**
> (là mancava `RCP.md` sul server). ⭐ *«Non riverificabile da questa macchina»* non è
> *«non certificato»*, e lo strumento fa bene a non fonderli — ma il conto **dipende ancora da dove
> lo si chiede**, ed è la stessa `[?]` del pomeriggio, non curata.

#### B13 — ⭐ Sei cose che la fase produce e che nessun banco guardava

*Rilievo **R3.24**. Tre hanno un ⛔ scritto in `RCP.md`.*

| # | Che cosa si verifica | Quando morderebbe |
|---|---|---|
| **1** | ⛔ **che i due certificati siano DUE** (§4.1-bis): impronte diverse, scadenze diverse | un server che ne genera uno solo a scadenza breve **passa tutti i banchi** — e l'avviso ricompare **quattordici giorni dopo**, quando *«nessuno collegherebbe le due cose»* |
| **2** | ⛔ **che la parola d'ordine non sia in nessun registro**: un `grep` della parola di prova su **tutti** i file prodotti dal giro — registro del server, registro della pagina, registrazione del validatore | la fase riusa `registro.c`, che in v1 è *«un registratore di battitura»*, e aggiunge un registratore di byte decifrati |
| **3** | **la chiave privata a `0600`**, il `subjectAltName` che combacia, e ⛔ **che un certificato d'autorità installato venga usato senza rigenerare il proprio** (§4.1) | nessuna fase lo dichiarava |
| **4** | **la pagina servita in TCP**: che si carichi, che pubblichi l'impronta **corrente**, e che **l'endpoint da cui si ritira l'impronta aggiornata esista** (§4.1-bis) | è il secondo mestiere che il server acquista qui, e B3 lo presupponeva in una riga |
| **5** | **il credito di almeno 16 stream unidirezionali** concessi al client (§2.3) | se finisse, *«l'input non partirebbe affatto»* e il sintomo sarebbe «il desktop non risponde» — alla fase 4, lontano da qui |
| **6** | ⛔ **che `stato` valga SEMPRE `NUOVA`**, cioè che nessuno abbia scritto per prudenza un ramo `RIPRESA` che nessuno proverà fino alla fase 5 | un `[?]` implementato a metà e non provato è quel che il confine dichiara di voler evitare |

#### B14 — che cosa di `RCP.md` §11 questa fase NON prende, e dove va

| Banco di §11 | Dove |
|---|---|
| ⛔ **il rilascio dei tasti al distacco** | **fase 5**, non fase 4 — *corretto da R4.7*: §11 ne scrive la procedura come *«si stacca una connessione con un tasto premuto **e si riattacca**»*, e alla fase 4 non esiste una sessione a cui riattaccarsi. Alla fase 4 la sessione **muore con la connessione**, quindi il banco o non si scrive o **si scrive verde per costruzione** |
| l'audio ascoltato, il formato del PCM | **fase 7** — ⚠ ma **S6** è qui, perché decide i 5 ms |
| gli appunti, i tre messaggi, i due trasferimenti insieme | **fase 7** |
| l'anello del ritardo | **fase 3**, ⛔ **e S4 con lui** (vedi «L'ordine») |
| il fotogramma abbandonato e la chiave che segue | **fase 3** |
| il credito degli stream oltre i 256 fotogrammi | **fase 3** — ⚠ il **credito concesso al client** invece è qui (B13.5): sono due versi diversi dello stesso obbligo |
| ⏳ **`GIA_ATTIVA_LOCALE` `0x05`** | ⛔ **non era di nessuna fase** *(R4.16)*: nasce all'attacco, cioè nel messaggio che questa fase scrive, e la riga di `SPECIFICHE.md` §5.1 che lo impone è la stessa che genera `GIA_ATTIVA_REMOTA`. ⚠ **Va alla fase 5**, con i tre orologi e la sessione locale — ma **dichiarato qui**, o cadeva fra le fasi |

---

## Che cosa è stato sviluppato

> ⚠ **Questo capitolo si apriva con** *«Nessuna riga di **prodotto** scritta. Quel che c'è è
> banco.»* — ⛔ **ed era falso dalla notte del 10 agosto 2026**, quando `src/` è nato: venti file,
> poi ventidue. Nessuno dei dieci documenti del progetto nominava quella cartella, e `PIANO.md` §0.2
> assegna proprio a questo capitolo il compito di dire che cosa la fase ha prodotto. ⛔ **Il costo
> era concreto**: chi riprendeva la fase leggeva *«nessuna riga di prodotto»* e **riscriveva da zero
> un server che esiste** — oppure lo trovava per caso con un `ls` e non sapeva se fosse prodotto,
> scarto o l'esperimento di qualcuno. Riscritto l'11 agosto 2026, rilievo **R12C.1**.
>
> ⛔ **E c'è una seconda cosa che quella riga faceva, meno visibile**: da quando `src/` esiste, ogni
> frase che dice *«il server»* ha **due soggetti** — il prodotto e l'innesto di
> `banchi/01-b3-rcp-innesta.py` dentro `bsslserver`. In questo documento, da qui in poi, *«il
> prodotto»* è `src/` e *«l'innesto»* è l'altro, **e i banchi misurano l'innesto**.

### ⭐⭐ Il prodotto — `src/`, il server della fase 1 in C

`[M]` **11 agosto 2026** (`wc -l` e `grep -cvE` su questo albero, codice fermo alle 00:36):
**22 file**, **9.647 righe**, di cui **5.248 di codice** nei `.c`/`.h`.

⭐ **Che cosa fa, in una riga**: un browser vero apre `https://192.168.0.2:7447`, l'utente digita
nome e parola d'ordine, e **la stretta di mano di RCP/1 arriva fino a `SESSIONE`** — con i due
certificati, la pagina servita dal server stesso, e il ban di `RCP.md` §4.4-bis. ⛔ **Niente video,
niente audio, niente input**: quelle sono le fasi da 2 in poi.

| | |
|---|---|
| `src/main.c` | ⛔ **i due ascoltatori sulla stessa porta 7447** (`RCP.md` §2.4): UDP per HTTP/3 e WebTransport, TCP per il primo caricamento della pagina — e sono **indipendenti**, WebTransport non passa da `Alt-Svc`. Un ciclo `poll` solo. ⭐ All'avvio **guarda che `/etc/pam.d/remotix` ci sia** e lo scrive: senza, Linux-PAM ripiega su `other` (che su Debian è `pam_deny`) e **ogni parola giusta viene rifiutata**, con una diagnosi che punta sulla parola d'ordine mentre il difetto è un file mancante. ⭐ E alla chiusura **congeda tutti** con `SERVER_IN_CHIUSURA` (§8.2 `0x0C`) invece di sparire |
| `src/trasporto.c` | QUIC su **ngtcp2**: `max_idle_timeout` 30 s imposto dal server, datagram annunciati, **19** stream unidirezionali concessi (§2.3 ne vuole 16 *disponibili* e HTTP/3 se ne prende 3 — il numero si dichiara invece di essere sottratto in silenzio), migrazione non disabilitata. ⭐ I datagram che arrivano si **contano e si scartano scrivendolo nel registro** (§6.3), invece di sparire in un callback che non c'è |
| `src/webtransport.c` | HTTP/3 e WebTransport: la `CONNECT` estesa **solo** su `/rcp/1` (404 altrove, §2.2), le capsule, la chiusura col codice del motivo. ⭐ E i **PING del trasporto** mentre il server aspetta le credenziali — senza, al trentesimo secondo la connessione muore in silenzio e i 60 s di §4.6 non scadono mai (§4.6, rilievo R1.8) |
| ⭐⭐ `src/rcp.c` + `rcp.h` | **RCP/1**, la stretta di mano e il ban. ⛔ **Identici byte per byte a `banchi/rcp/`** — `[M]` 11 agosto 2026, `md5sum`: `cb7af778…` (`rcp.c`), `0458f154…` (`rcp.h`). ⚠ **Identici per fortuna, non per costruzione**: nessuno script confronta le due copie a ogni giro, e da stanotte hanno **due storie diverse** (una in git, una no). `src/costruisci.sh` accetta `GEMELLO=` per dichiarare il confronto |
| `src/autenticazione.c` + `remotix.pam` | PAM, ⭐ **servizio `remotix`** come vuole `SPECIFICHE.md` §4.2 — con il file del servizio nella cartella, non in una nota d'installazione. ⚠ *Il 10 agosto notte diceva `pam_start("login")`, cioè la pila della **console locale** con `pam_securetty`, `pam_lastlog`, `pam_limits`: rilievo **B-11** di `fasi/rapporti/R12-B-prodotto.md`, curato nel codice la stessa notte* |
| `src/certificati.c` | i **due** certificati di §4.1-bis, con il rifiuto di partire se le due impronte coincidono, il breve a 13 giorni che ruota quando ne restano due, e `/impronta` servito con `no-store` |
| `src/tls.c` | TLS per l'ascoltatore TCP. ⭐ **0-RTT spento a livello di contesto**, dove nessuna sessione lo può riaccendere (§2.3) |
| `src/pagina.c` + `pagina.html` | la pagina servita dal server: l'impronta corrente, la stretta di mano dal lato del browser, e l'avviso di chi è bannato con **le ore che mancano** (§4.4-bis). ⭐ Il server **si rifiuta di partire** se la pagina non contiene i segni da sostituire, o se ne contiene due — una sostituzione che «riesce senza fare niente» servirebbe per sempre una pagina senza impronta |
| ⭐ `src/comando.c` + `comando.h` | **il comando di sblocco di §4.4-bis**, su un **socket Unix `0600`**: `SBLOCCA <indirizzo>` → `TOLTO` / `NON-BANNATO`, `PING` → `PONG`. ⛔ È lo stesso protocollo, byte per byte, che parla `banchi/01-b8-sblocca.py`, cioè lo strumento della regola **B0.3** |
| `src/registro.c` | riusato da v1, con l'obbligo di **B13.2**: la parola d'ordine non compare in nessun registro |
| `src/Makefile` + `costruisci.sh` | ⭐ **butta il binario prima di ricostruire** (così *«c'è»* vuol dire *«è di adesso»*) e **controlla cinque marche dentro il binario prodotto**, con il controllo positivo dello strumento. È la ottava veste di `LEZIONI.md` §1.9 curata prima di pagarla |

#### ⛔ Che cosa di `src/` NON è provato

*Elencato riga per riga, perché è la metà che non si vede. Le prime due voci vengono da
`fasi/rapporti/R12-B-prodotto.md` §0; le altre le ho misurate io l'11 agosto 2026, e dove ho
misurato lo dico.*

| | |
|---|---|
| ⛔ **il server intero non è mai stato eseguito da un revisore** | sulla macchina del revisore mancano `ngtcp2`, `nghttp3`, `libssl-dev` e `libpam0g-dev` (`make dipendenze` dà **cinque NO**). ⇒ tutto quel che riguarda `trasporto.c`, `webtransport.c`, `pagina.c`, `certificati.c` è **letto, non misurato**. ⭐ L'unica esecuzione è `src/rcp.c` **compilato isolato** con `-Wall -Wextra` — **zero avvisi** — contro un driver del revisore, sei ingressi byte per byte |
| ⛔ **UN SOLO MOTORE** | l'unica traccia di un giro con un **browser vero** contro questo server è un commento dentro `src/pagina.html`: `[M]` 10 agosto notte, **Firefox** — e quel giro ha trovato un difetto vero (la pagina mandava `disposizione = en`, che **non è** un nome XKB, e il server congedava con `SESSIONE_NON_SERVIBILE` facendo esattamente il suo mestiere). ⛔ **Di Chrome contro questo server non c'è nessuna traccia**, e il criterio di B2 vuole **due motori su due** |
| ⛔ **e quel giro non è riverificabile da questa parte** | `[M]` 11 agosto 2026, **mattina**: in `src/` non c'è né il binario `remotix` né un `.o`; nessun `.jsonl`; `git status` dà `src/` **untracked**, mai committata. E **nessuno dei 14 script `01-*-lancia.sh` accende il prodotto**: `bsslserver` compare in **11** di loro, il binario `remotix` in **zero** (l'unica occorrenza della parola è `remotix.prova`, un nome SNI in `01-b2-lancia-sni.sh`). ⚠ ⛔ **E questa riga è SCADUTA la sera dello stesso giorno, e va letta con la data addosso**: `[M]` 11 agosto **sera** — `git ls-files src/` dà **22 file** (commit `ffeb341`), gli script di lancio sono **16** e **11 di loro sanno puntare al `BERSAGLIO=prodotto`**, tre accendono il binario per nome. ⭐ *Una riga che dichiara un'assenza invecchia nel verso peggiore: resta vera nell'aspetto e falsa nei fatti, e chi la legge non ha nessun motivo di sospettarla* |
| ⛔ **le proprietà di trasporto non sono state rimisurate contro questo server** | le sei di B2 — tetto 30 s · datagram · credito uni · migrazione · niente 0-RTT · `allowPooling` — sono `[M]` **sull'innesto**, letto dal pari. `src/trasporto.c` oggi dichiara **19** stream uni dove la misura di B2 ne leggeva 16: è un numero diverso, ed è **la sonda `01-b2-sonda-trasporto.py` puntata al prodotto** che lo direbbe |
| `[?]` **il rinnovo del credito degli stream** | il prodotto lo dichiara **di suo** (`src/trasporto.c`): ngtcp2 non alza il tetto da sé *«tranne quando uno stream si chiude senza che `stream_open` sia stato chiamato»*, e questo codice cade **probabilmente** in quell'eccezione. Nessuno l'ha misurato. ⛔ Si misura alla **fase 4**, quando gli appunti apriranno uno stream per trasferimento: prima di allora nessun client ne apre più di quattro, e una misura senza il carico che la provoca non è una misura |
| ⚠ **la pagina del prodotto e quella dell'innesto sono due documenti diversi** | e **B8 misura i marcatori che solo l'innesto produceva**. Curato nel prodotto la notte del 10 (`data-bannato` e `data-restano-ms` ci sono, in una sola occorrenza ciascuno, e il server rifiuta di partire se ce ne fossero due) — ⛔ **ma nessuno ha puntato B8 al prodotto per verificarlo**: finché non lo si fa, «curato» è letto e non misurato |

#### ⛔ I ripieghi di fase — due che pesano e uno minore, dichiarati qui e non solo in un commento

> ### ⭐ E i due che pesano hanno una SCADENZA, decisa dall'utente alla chiusura della fase
>
> *11 agosto 2026, sera. ⛔ Le decisioni stanno in `DECISIONI.md` e qui si rimanda: sotto c'è la
> conseguenza sulla fase, non la decisione.*
>
> | | |
> |---|---|
> | **il filo** | **`DECISIONI.md` §1.10** — ⛔ **si cura PRIMA della fase 2**, e con un **processo aiutante** (PAM non è affidabilmente rientrante). ⭐ A spostare la scadenza dalla fase 5 alla 2 è stato **un numero di B8**: il blocco è di **1,0-2,2 s** a tentativo, ⛔ **e a metterlo è PAM**. Fino alla fase 1 il sintomo è *«l'ultimo dei dieci aspetta»*; **dalla fase 2 in poi è lo schermo di chi sta già lavorando che si pianta quando entra qualcun altro**, e chi lo vede lo attribuisce al video. ⛔ **E la proprietà da provare non è «PAM funziona ancora»**: è *«mentre uno si autentica, gli altri non se ne accorgono»* — e **quel banco oggi non esiste** |
> | **il tetto** | **`DECISIONI.md` §1.11** — ⛔ **resta 16 fisso fino alla fase 3**, di proposito: `SPECIFICHE.md` §5.5 dice di sé che *«il limite vero non è un conteggio, è un budget di pixel al secondo»*, quindi qualunque numero di oggi è un segnaposto. ⚠ **Il prezzo dichiarato**: per due fasi il codice dice **16** e la specifica dice **dieci**. ⛔ E vale per qualunque numero: **nessun banco ha mai visto quel tetto mordere** — riempirlo vuole dieci utenti **diversi** (I2), e il motivo del rifiuto è di fase 3 |

*Rilievo **R12C.17**: stavano scritti in `src/main.c` e `src/rcp.c`, cioè dove non li legge nessuno
che non stia leggendo quel file — mentre `SPECIFICHE.md` §5.5 e `DECISIONI.md` §4.6 promettono dieci
sessioni insieme senza una riga che dica il contrario. ⚠ Un ripiego di fase dichiarato nel codice non
è una promessa rotta: è una promessa **non ancora dovuta**. Ma il posto in cui si scrive è dove la
fase dichiara i propri confini.*

| | |
|---|---|
| ⛔ **un solo filo, e la verifica PAM lo BLOCCA** | tutto gira in un ciclo `poll` solo, e `pam_authenticate` è sincrona: la stretta di mano di un utente **ritarda i pacchetti di chiunque altro**. ⛔ E il secondo fisso di §4.4-bis lo rende misurabile: con dieci utenti che entrano insieme, l'ultimo aspetta **dieci secondi** — e il sintomo, *«il server è lento quando c'è gente»*, non nomina né PAM né il filo. **Prima della fase 5 la verifica va su un filo a parte** |
| ⚠ **sedici sessioni attaccate, in compilazione** | `src/rcp.c`: `#define MAX_ATTACCATE 16`, col commento *«un server vero lo sostituirà con la sua tabella delle sessioni»*. `SPECIFICHE.md` §5.5 dice **dieci, configurabile**: qui è sedici e fisso |
| ⚠ **e un terzo, minore, che vale la pena di nominare adesso** | l'interruttore della funzione di banco di `RCP.md` §7.5 è `#define BANCO_ACCESO 0`. L'invariante **I6** è rispettata — è spenta di suo — ⛔ ma §7.5 la vuole accendibile **nella configurazione del server**, e oggi accenderla richiede di **ricompilare**. Il giorno in cui la configurazione ci sarà, questa è la riga da cambiare |

### I banchi

| | |
|---|---|
| ⭐ `banchi/01-b2-costruisci.sh` | **nuovo**: costruisce BoringSSL e `lsquic` con `-DLSQUIC_WEBTRANSPORT=ON`, e ⛔ **verifica che il flag abbia prodotto i simboli** — non che compili |
| ⭐ `banchi/01-b2-certificati.sh` | **nuovo**: i **due** certificati di `RCP.md` §4.1-bis con quattro controlli — curva, `subjectAltName`, durata sotto i 14 giorni, e ⛔ **che i due siano davvero due** (il difetto di B13.1, colto alla nascita invece che due settimane dopo) |
| ⭐ `banchi/01-b2-controllo-aioquic.py` | **nuovo**: ⛔ **il controllo positivo di B2** — una sessione WebTransport che *deve* riuscire. Senza, «la candidata non apre la sessione» e «il banco non sa aprirne nessuna» hanno lo stesso aspetto (R3.17) |
| ⭐ `banchi/01-b2-cliente-aioquic.py` | **nuovo**: il germe del **cliente di prova** (B9), e il controllo d'ambiente che separa «il server non regge» da «il browser non accetta» |
| ⭐ `banchi/01-b2-sonda.html` | **nuovo**: la pagina, ⛔ **servita da `localhost`** — contesto sicuro senza avvisi, così quel che si misura è **la sessione** e non il clic dell'utente |
| ⭐ `banchi/01-b2-sni-ngtcp2.sh` | **nuovo, 10 agosto**: costruisce `bsslserver`, il server d'esempio di `ngtcp2`, che è il bersaglio della prova SNI. ⛔ **Non guarda l'uscita di `ninja`: guarda se il binario c'è** — `examples/CMakeLists.txt` costruisce quel blocco solo `if(LIBEV_FOUND AND HAVE_BORINGSSL AND LIBNGHTTP3_FOUND)`, e se una manca cmake **salta in silenzio** |
| ⭐ `banchi/01-b2-sonda-sni.py` | **nuovo, 10 agosto**: la sonda del criterio nuovo di `DECISIONI.md` §6.4. Due gambe (senza SNI · con SNI), e ⛔ **due gradini per gamba**: la stretta di mano riesce **e** l'impronta del certificato ricevuto combacia con quella del file |
| ⭐ `banchi/01-b2-sni-quiche.sh` | **nuovo, 10 agosto**: la terza candidata. ⛔ **Due azioni separate — `leggi` e `costruisci`** — perché se leggere e misurare stanno nello stesso comando la previsione la si scrive **dopo** aver visto il risultato, cioè non la si scrive. ⭐ E **sceglie la versione**: confronta il `rust-version` di ogni etichetta col compilatore presente, e dice quale e perché |
| ⭐⭐ `banchi/rcp/rcp.c` + `rcp.h` | **nuovo, 10 agosto**: ⭐ **la stretta di mano di RCP/1 E IL BAN DELL'INDIRIZZO, in C** — `[M]` **11 agosto 2026** (`wc -l` su questo albero, codice fermo alle 00:36): `rcp.c` **2.566 righe / 1.418 di codice**, `rcp.h` **197 / 54**. ⚠ *Diceva «**1292 righe / 875 di codice**, `rcp.h` **131 / 49**», `[M]` delle **ore 16:30 del 10 agosto**, e alle 23:48 il file ne misurava già 2.339: lo scarto era dell'**81 %** — rilievo **R12C.12**. E prima ancora diceva «807 righe, 662 di codice», il conto della mattina. ⛔ **La cura era già in questa tabella, tre righe più giù**, applicata a un numero della stessa natura (la riga del collante di B2, che porta «alle 08:00 la stessa misura dava 456/329»): una cura applicata in un posto solo, dentro la stessa tabella.* ⛔ **E la riga non nominava il ban**, che è il lavoro della notte del 10 — `FINESTRA` di 5 minuti, `BAN_DURATA` di 12 ore, `salva_ban`, `rcp_ban_carica`, `rcp_sblocca`, `rcp_bannato`, la tabella da 256 posti con lo sfratto che non butta mai una voce bannata — cioè la decisione dell'utente del giorno (`DECISIONI.md` §1.9). ⛔ **E questo numero non c'entra con quello dello strato WebTransport**: il protocollo **non dipende da ngtcp2** — riceve byte, restituisce byte, e non entra in nessuna delle misure di collante di B2. ⛔ **Non sa che sotto c'è QUIC**: riceve byte, restituisce byte, e il tempo glielo passa chi lo ospita. È la ragione per cui potrà passare al server vero senza riscritture, e per cui §6.4 — se si riaprisse — non porterebbe via il protocollo |
| ⭐ `banchi/rcp/autenticazione.c` | **nuovo, 10 agosto**: `[M]` **99 righe / 52 di codice** (ore 16:30) — PAM, derivato da `fondamenta/remotix-c/src/autenticazione.c` con ⛔ **la cura di B10** — è caduto il confronto con l'utente del processo, che contraddiceva il multi-tenant di `SPECIFICHE.md` §5.5 |
| ⭐ `banchi/01-b3-rcp-innesta.py` | **nuovo, 10 agosto**: ⛔ **un innesto SEPARATO da quello di B2**, perché quel numero misura WebTransport e farlo crescere con RCP dentro renderebbe due misure diverse sotto la stessa etichetta (E2) |
| ⭐ `banchi/01-b3-cliente.py` | **nuovo, 10 agosto**: **il cliente di prova** — la stretta di mano scritta una seconda volta, in un linguaggio diverso, e **registra** nel formato di §11.1 con la parola d'ordine oscurata |
| ⭐ `banchi/01-b3-lancia.sh` + `01-b3-terzo-giro.sh` | **nuovi, 10 agosto**: le tre connessioni di B3, e ⛔ **ogni traccia passa dal validatore di B4** — non si collauda il server contro il client |
| ⭐⭐ `banchi/01-b3-quarto-giro.sh` | **nuovo, 10 agosto**: l'**orologio del silenzio** — 35 s a `max_idle_timeout` 120, con il controllo a +6 s che dice **no**. ⛔ Senza quel primo tempo, «dopo 35 s la seconda entra» è compatibile con «la seconda entra sempre» |
| ⭐⭐ `banchi/01-b3-quinto-giro.sh` | **nuovo, 10 agosto**: ⚠ **gira da questa parte del filo** — ruota il certificato, riavvia, e prova che la pagina ritira l'**impronta corrente**. ⛔ E che con la **vecchia** non si apre: senza quel controllo, «funziona con la nuova» è compatibile con un browser che l'impronta non la guarda |
| ⭐⭐ `banchi/01-b4-validatore.py` | **nuovo, 10 agosto**: ⭐ **il validatore del filo** — un terzo programma che legge una registrazione e dice **quale byte** non è conforme a `RCP.md`. ⛔ Scritto leggendo **solo la specifica**, prima che esistesse un byte di server. Ha **tre** esiti, non due: conforme · non conforme · ⚠ *registrazione malformata*, perché «il file è rotto» e «il filo non era conforme» sono due fatti con due cure |
| ⭐ `banchi/01-b4-registrazioni.py` + `01-b4-lancia.py` | **nuovi, 10 agosto**: le **sette** registrazioni, ciascuna col **byte offensivo dichiarato in anticipo** in un manifesto — e il confronto lo fa il banco, non chi guarda |
| ⭐ `banchi/01-b2-sonda-trasporto.py` + `01-b2-lancia-trasporto.sh` | **nuovi, 10 agosto**: le sei proprietà, lette **dal pari** con una spia dichiarata su `pull_quic_transport_parameters` di `aioquic`. ⛔ Hanno trovato due difetti che nessun banco funzionale vedeva, e il secondo giro (`--timeout=10s`) misura la proprietà che serve a **B3** |
| ⭐ `banchi/01-b2-sonda-impostazioni.py` | **nuovo, 10 agosto**: legge **sul filo** quali impostazioni un server HTTP/3 dichiara (`received_settings` di `aioquic`), e dice se c'è WebTransport. ⛔ È la prova che ha chiuso §6.4, e stampa **tutte** le impostazioni: un elenco vuoto e uno senza le due che interessano sono due fatti diversi |
| `banchi/01-b2-quiche-wt-innesta.py` + `01-b2-lancia-impostazioni.sh` | **nuovi, 10 agosto**: accendono su `quiche` tutto quel che la sua API C permette (3 righe di codice), e conducono il confronto con `ngtcp2` come **controllo positivo** |
| ⭐⭐ `banchi/01-b2-ngtcp2-wt-innesta.py` | **nuovo, 10 agosto**: ⭐ **il server minimo** — innesta lo strato WebTransport nel server d'esempio di `ngtcp2`. ⛔ Ogni innesto ha un **appiglio che deve comparire una volta sola**: zero o due, e lo script si ferma dicendo quante ne ha trovate. E **conta le righe nostre** da `git diff`, che è il dato di §6.4 |
| ⭐ `banchi/01-b2-lancia-wt.sh` | **nuovo, 10 agosto**: misura il server minimo col cliente di prova, ⛔ **e col controllo che dice no** — `/rcp/9` deve essere rifiutato (`RCP.md` §2.2). `accendi`/`spegni` servono alla misura col browser |
| ⭐ `banchi/01-b2-lancia-sonda.sh` | **nuovo, 10 agosto**: ⚠ **gira sulla macchina di chi guarda, non sul server** — i browser stanno lì. Accende il server dall'altra parte, serve la pagina da `127.0.0.1`, lancia i due motori sotto `xvfb` e aspetta che il **registro cresca**, non un tempo fisso |
| `banchi/01-b2-sonda.html` | **corretto**: `?avvia=1` fa partire la prova da sé. ⛔ Un banco che ha bisogno di una mano **non si può rifare uguale**, e rifarlo uguale è l'unico modo di sapere se una misura è cambiata perché è cambiato il server |
| `banchi/01-b2-raccogli.py` | **corretto**: registra **ogni richiesta**. Prima taceva, «il rumore non serve» — ed è quel silenzio che ha reso indistinguibili «il browser non ha caricato la pagina» e «l'ha caricata e la prova è fallita» |
| ⭐ `banchi/01-b2-lancia-sni.sh` | **nuovo, 10 agosto**: conduce la prova sui **tre** bersagli — `ngtcp2`, `quiche`, e `lsquic` come **controllo negativo** in coda, che a ogni esecuzione ridimostra che la sonda sa vedere un rifiuto. ⛔ Verifica che le porte siano libere **prima**, che i server ascoltino davvero (`ss`, non solo «il processo è vivo»), e li ferma **per PID** |
| `fondamenta/banco/provision.sh` | **corretto**: `libev-dev` fra i pacchetti — è quel che serve agli esempi di `ngtcp2`, ed è **un'altra libreria** da `libevent-dev` che c'era già. ⚠ Senza, cmake mette `LIBEV_LIBRARY-NOTFOUND` e **salta gli esempi senza dire niente** |
| `fondamenta/banco/provision.sh` | **corretto**: `golang-go` fra i pacchetti del contenitore. Serve a compilare BoringSSL, che è la sola pila TLS con cui `lsquic` e `quiche` parlano QUIC. ⛔ Nel provisioning, non a mano (`LEZIONI.md` §2.5-bis) |

> #### ⛔ E i banchi che questa tabella non nominava — undici, contati
>
> *Rilievo **R12C.13**. Questa tabella si fermava a B5 e agli innesti di B2, mentre il README
> dichiarava chiusi B6, B7, B8 e B11 e la notte del 10 ne ha fatti nascere altri quattro. ⛔ La
> regola con cui **R11.21** era stato chiuso sta nel `README.md` e vale identica qui: «un banco che
> non è nominato dove si dice come rimettere in piedi i banchi **non si può rifare uguale**», e
> rifarlo uguale è l'unico modo di sapere se una misura è cambiata perché è cambiato il server.
> Aggiunti l'11 agosto 2026.*
>
> | | |
> |---|---|
> | `banchi/01-b6-lancia.sh` + `01-b6-tetti.py` | **B6**, i tre tetti di §4.6. ⭐ Legge i `#define TETTO_*` **da tutt'e due** le copie del sorgente — quella dei banchi e quella compilata — e pretende che combacino, «perché una copia stantia darebbe un numero che nel binario non c'è». ⭐ E ha **tre esiti separati**: il server sbaglia · il **documento** sbaglia · non ho saputo classificare |
> | `banchi/01-b7-lancia.sh` + `01-b7-congedo.py` | **B7**, il congedo dal lato che riceve. ⛔ Dichiara il **denominatore vero**: §8.2 ha **quindici** motivi, i provocabili in questa fase sono **sette**, e gli altri otto stanno in una tabella `ESCLUSI` con la ragione di ciascuno |
> | `banchi/01-b8-lancia.sh` + `01-b8-cronometro.py` + `01-b8-prova-ban.c` + ⭐ `01-b8-sblocca.py` | **B8**, il secondo fisso e il ban. ⭐ `01-b8-sblocca.py` **non è un pezzo di B8**: è lo strumento della regola **B0.3**, e parla il socket di comando di §4.4-bis con tre esiti distinti (`TOLTO` · `NON-BANNATO` · «non ho parlato con nessuno», che esce **3**) |
> | ⭐ `banchi/01-b9-letture.py` | **B9**, il secondo lettore messo a confronto con l'arbitro: **dodici** punti in cui `RCP.md` ammette due letture, ciascuno con **i byte che cambiano sul filo**. L'elenco sta in «Che cosa NON ha funzionato» |
> | `banchi/01-b11-lancia.sh` + `01-b11-pagina.html` + `01-b11-guasto.sh` + `01-b11-guasto-innesta.py` | **B11**, le violazioni verso la **pagina**, col server guasto di proposito e `ricostruisci()` che rimette quello sano nei due `--togli` nell'ordine |
> | `banchi/01-b12-guasti.py` + `01-b12-lancia.sh` + `01-b12-copie/` + `01-b12-registro.jsonl` | **B12**, il banco che certifica gli altri: un guasto costruito a mano per ogni banco, e il registro delle certificazioni con la data e le impronte. ⛔ Quel che ha certificato davvero sta più sotto, ed è **3 su 12** |
> | `banchi/01-b13-lancia.sh` + `01-b13-proprieta.py` | **B13**, le sei cose che nessun altro banco guardava |
> | `banchi/01-c2-lancia.sh` + `01-c2-diagnosi.py` | **C2**, le tre diagnosi del collegamento guasto — nessuno in ascolto · UDP filtrato col TCP che risponde · impronta non corrente |
> | ⭐ **le sette pagine della sonda** | `01-s1b-eccezione.sh` + `01-s1b-pagina.html` + `01-s1b-sito.sh` + `01-s1b-servi.py` (**S1b**, l'orologio dei sette giorni) · `01-s2-pagina.html` (**S2**) · `01-s3a-pagina.html` (**S3a**) · `01-s5-tela.sh` + `01-s5-pagina.html` + `01-s5-raccogli.py` (**S5**) · `01-s6-pagina.html` (**S6**) · `01-s7-rotella.sh` + `01-s7-rotella.c` + `01-s7-pagina.html` + `01-s7-raccogli.py` (**S7**) · `01-s-telefono.sh` (le procedure che aspettano un dispositivo) |
>
> ⚠ **E i registri che quei banchi lasciano**, perché un banco senza il suo registro non è
> riverificabile: `banchi/01-s7-esiti.jsonl` · `01-s5-esiti.jsonl` · `01-s1b-stato.jsonl` ·
> `01-b12-registro.jsonl` · `b2-esiti.jsonl`. ⛔ **B6, B7, B8, B11, B13 e C2 non ne hanno nessuno**:
> i loro numeri vivono nell'uscita a schermo del giro, e quando la scena è smontata non ci si torna.

**Si riusa** (`PIANO.md` fase 1): `autenticazione.c` di v1 (144 righe) — ⛔ **con la cura di B10**,
e quel che ne è uscito misura **99 righe / 52 di codice** `[M]` — e `registro.c` (140) — ⚠ **con
l'obbligo di B13.2**.

---

## Le misure

*⛔ Con la scena, il dispositivo e la **versione** dichiarati accanto a ogni numero (B0.6).*

#### La sonda

⛔ **Gli esiti per esteso, con i registri e la ricontata dei numeri, stanno in
`web/rapporti/S-esiti-sonda.md`** — qui c'è il numero con la
data, come vuole B0.6. ⚠ *Fino all'11 agosto 2026 queste sei celle erano **vuote** mentre tre delle
misure erano state prese la notte del 10: chi leggeva questo documento credeva che la misura non ci
fosse (rilievi **R12.7** e **R12C.7**, e la sonda lo aveva scritto di suo — voce S.6 del suo §9).*

| # | Che cosa | Dispositivo · versione | Atteso | Misurato | Data |
|---|---|---|---|---|---|
| S1b | durata dell'eccezione su Chrome | **Chrome 151.0.7922.108**, profilo persistente, `Xvfb :77 1280x1024x24` | **7 giorni** `[R]` | ⏳ **AVVIATA — giorno 0 preso.** Chrome si è segnato la scadenza **2026-08-17T21:09:47.889Z** `[M]` (grezzo su disco, conversione dichiarata). ⚠ `[?]` **che siano 604 800 s esatti dal clic**: l'istante del clic non l'ha registrato nessuno. Il numero sul campo si legge **il 17-18 agosto** | **10 ago**, 21:10:01Z |
| S2 | HEVC Main10 **in hardware** | ✅ telefono + PC per `chrome://inspect` | `[?]` — ⛔ *non «sì da Chrome 108»* | ⛔ **non eseguita**: manca il telefono, manca il PC per il controllo C, e le cinque sequenze dipendono dal codificatore della **fase 2**. ⭐ Banco pronto: `01-s2-pagina.html`, e finché A e B non passano **non pubblica verdetti** | |
| S3a | tastiera, nei tre stati di O8 | ✅ DeX — ⚠ `[?]` **verificare che sia ≥ Android 16 QPR1** | `[?]` | ⛔ **non eseguita**: manca il DeX. ⚠ E una riga di S3 §4.4 non è eseguibile **nemmeno col DeX**: `requestFullscreen({keyboardLock})` vuole **Firefox ≥ 151** e questa macchina ha la **140.13.0esr** — chi provasse qui misurerebbe l'assenza della lock e la scambierebbe per scorciatoie perdute | |
| S5 | tela dichiarata, zoom 100 %/150 % | **Chrome 151.0.7922.108** e **Firefox 140.13.0esr** su `Xvfb 1920×1080×24` (⛔ il **DeX** manca) | **uguale nei due**, e = risoluzione fisica | ⛔ **I DUE MOTORI NON CONCORDANO.** Firefox: `screen` 1280×720 a 150 % ⇒ tela **1920×1080**, invariante ✅. Chrome: `screen` resta 1920×1080 ⇒ tela **2880×1620**, del **50 % più grande** ⛔. `[M]`, due giri identici, `01-s5-esiti.jsonl`. ⇒ la formula di `SPECIFICHE.md` §6.1-bis **non regge su Chrome** | **10 ago**, 23:13-23:14 |
| S7 | segno della rotella, `natural-scroll` nei due stati | **server 192.168.0.2**, GNOME headless, **libmutter 48.7-0+deb13u1**, **libei 1.3.901**, **Firefox 140.13.0esr** in `--kiosk` | `[?]`, e **non deve cambiare** con la gsetting | ⭐ **`+120` → `deltaY +114`, la pagina SCENDE** ⇒ ⛔ **il server inverte l'asse verticale**. `[M]`, due giri, `01-s7-esiti.jsonl`. Il segno **non cambia** fra i due giri ⚠ (`[?]` che fossero i due stati di `natural-scroll`: l'etichetta non è nel registro). ⛔ Misurata **su Mutter**: per gli altri quattro desktop resta `[?]` | **10 ago**, 20:59 UTC |
| S6 | carico utile di un datagram, **sul percorso peggiore** | ✅ telefono su LTE | ≥ **972 byte** | ⛔ **non eseguita**: manca una LTE vera e manca la metà di server che faccia l'**eco** dei datagram. ⭐ Banco pronto: `01-s6-pagina.html`, che **si rifiuta di misurare senza `?percorso=`** | |
| ⛔ S1a | eccezione ⇒ WebTransport su Safari | ⛔ **niente Mac** | *fuori dalla fase, resta `[?]`* | | |
| ⏳ S3b | PWA su Chrome per Android | ⛔ + certificato vero | *rimandata* | | |
| ⏳ S4 | anello del ritardo del disegno | | *→ fase 3* | | |

#### Il filo

⚠ *Tre `[M]` di **B3** — la 2ª mentre la 1ª è viva, l'orologio del silenzio, la 3ª col certificato
ruotato — stavano in questa tabella **senza la cella della data**, in un capitolo che apre
imponendola: rilievo **R11.17**. La data c'è dal 10 agosto 2026, e la cella mancante non era
formalismo — `[M]` è definito come «misurato da noi, sul ferro, **con la data**» (`README.md`), e
la riga della 3ª è quella che dichiara un esito su **due browser**, cioè quella che B0.6 nomina per
prima.*
⚠ *E la stessa cura è dovuta tornare l'11 agosto 2026, tre righe sotto quel riquadro: la riga di
**B8** portava il suo `[M]` nella colonna dell'**atteso**, con «Misurato» e «Data» vuote e il «10
ago» dentro il testo invece che nella cella — rilievo **R12C.14**. ⛔ Il controllo meccanico che
aveva trovato R11.17 (contare le `|`) qui **non vede niente**: le celle sono cinque su tutte le
righe, e il difetto è nel loro **ordine**. Cioè la cura era stata applicata alla forma che il rilievo
descriveva e non alla proprietà che il rilievo proteggeva — che è, di nuovo, «una cura applicata in
un posto solo».*

⛔ **E la scena, che B0.6 pretende accanto a ogni numero**: i giri **1-4** di B3 li fa il cliente
`banchi/01-b3-cliente.py` contro il server minimo su `ngtcp2`, sulla macchina di prova — **nessun
browser**, quindi nessuna versione di browser da annotare; il **quinto** (certificato ruotato) è
l'unico coi browser veri, e le loro versioni sono dentro la riga.

| Che cosa | Atteso | Misurato | Data |
|---|---|---|---|
| **B2** — BoringSSL compila nel `devroot` | sì | ✅ **sì** — ramo predefinito, `libssl.a` e `libcrypto.a` | 9 ago |
| **B2** — `lsquic` compila con `-DLSQUIC_WEBTRANSPORT=ON` | sì | ✅ **sì**, v4.9.3, e la define è nei `FLAGS` di `build.ninja` | 9 ago |
| ⛔ **B2** — **il flag ha prodotto i simboli?** | **4 su 4** | ⭐ **4 su 4** `[M]` — dopo aver curato il banco, vedi sotto | 9 ago |
| **B9** — `aioquic` porta WebTransport? | `[?]` | ⭐ **sì** `[M]` 1.2.0: 29 occorrenze nel modulo h3, l'evento e `create_webtransport_stream`. *Era la `[?]` di R3.21: se fosse stata «no», cadeva l'arbitro* | 9 ago |
| **B2** — i due certificati, quattro controlli | 4 su 4 | ✅ **4 su 4** — e i due sono davvero due | 9 ago |
| ⭐ **B2** — **il controllo positivo d'ambiente** (senza browser) | sessione accettata **e** byte che tornano | ⭐ **`:status = 200`, `b'ciao'` torna identico** `[M]` | 9 ago |
| ⭐ **B2** — **la sessione si apre da un BROWSER VERO** | si apre, e i byte tornano | ⭐ **APERTA in 30,2 ms** su **Chrome 151.0.0.0** (X11, Linux), `"ciao"` torna identico `[M]` | 9 ago |
| ⭐ **B2** — lo stesso su **Firefox** | si apre | ⭐ **APERTA in 52,0 ms** su **Firefox 140.0**, `"ciao"` torna identico `[M]` | 9 ago |
| ⭐ **B2** — ⛔ **`ngtcp2` serve il certificato SENZA SNI?** | **sì** (previsione scritta prima: zero ricerche per nome in 109+18 file) | ⭐ **sì** `[M]` — sessione stabilita, e **l'impronta del certificato ricevuto combacia** con quella del file | 10 ago |
| **B2** — lo stesso con SNI, il controllo | sì | ✅ **sì** — `remotix.prova` | 10 ago |
| ⭐ **B2** — ⛔ **`quiche` serve il certificato SENZA SNI?** | **sì** (previsione scritta prima: l'unico punto che nomina l'SNI è un **lettore**, `tls/mod.rs:510`) | ⭐ **sì** `[M]` su **`quiche` 0.28.0** — sessione stabilita, **impronta combaciante** | 10 ago |
| **B2** — lo stesso con SNI, il controllo | sì | ✅ **sì** | 10 ago |
| ⛔ **B2** — quale `quiche` si costruisce con `rustc` di Trixie? | *non era una domanda* | ⛔ **la 0.28.0**: la **0.29.3 pretende rustc 1.88**, Trixie ha **1.85** `[M]` | 10 ago |
| ⭐ **B2** — il **controllo negativo**: `lsquic` senza SNI | **fallisce** | ⭐ **fallisce** `[M]`, e il suo registro dice **perché**: `SNI is not set … fail certificate lookup` | 10 ago |
| ⭐ **B2** — `lsquic` **con** SNI: trova il certificato? | sì — *la metà che mancava alla diagnosi del 9* | ⭐ **sì** `[M]`: `looked up cert for remotix.prova`. ⚠ poi cade su ALPN (avviso 120), **causa non indagata** | 10 ago |
| ⭐⭐ **B2** — **la sessione si apre da un BROWSER VERO, su `ngtcp2`** | 2 motori su 2 | ⭐ **2 su 2** `[M]`: **Chrome 151.0.0.0** (118,6 ms) e **Firefox 140.0** (140,0 ms), impronta pubblicata, nessun avviso, `"ciao"` torna identico | 10 ago |
| ⛔ **B2** — e il percorso **sbagliato** si rifiuta? | non 200 | ⭐ **404** su `/rcp/9` `[M]`, come impone §2.2 (R1.24) | 10 ago |
| ⭐ **B2** — le sei proprietà della libreria | 6 su 6 | ⭐ **6 su 6** `[M]`, e **lette dal pari, non dal registro del server**: `max_idle_timeout` 30 000 ms · datagram 65 536 · credito uni **16** · migrazione **non** disabilitata · **niente 0-RTT** · `allowPooling: false` | 10 ago |
| ⛔ **B2** — e il tetto d'inattività si può **cambiare**? (serve a B3) | il pari vede il valore nuovo | ⭐ **sì** `[M]`: con `--timeout=10s` il pari legge **10 000 ms**. B3 potrà distinguere il tetto del protocollo da quello del trasporto | 10 ago |
| ⛔ **B2** — ⭐ **due difetti trovati proprio da queste misure** | *nessuno era atteso* | ⛔ il server offriva **0-RTT** (2 biglietti, `max_early_data_size` 0xffffffff) e concedeva **3** stream unidirezionali invece di 16. **Nessuno dei due ha un sintomo funzionale**: la sessione si apriva uguale | 10 ago |
| ⛔⭐ **B2** — **`quiche` riesce a dichiarare WebTransport dal C?** | **no** (previsione scritta prima: `set_additional_settings` esiste in Rust, **non nell'FFI**) | ⛔ **no** `[M]`: 4 impostazioni sul filo, **nessuna** delle due di WebTransport. Il controllo positivo (`ngtcp2`) ne dichiara 7 | 10 ago |
| **B2** — la sessione si apre, **per candidata** | 2 motori su 2, **e le sei proprietà** | ⭐ **fatto su `ngtcp2`**; su `quiche` **non si arriva a provarlo**: cade al cancello prima | 10 ago |
| ⭐ **B2** — righe di collante **per lo strato WebTransport** | *si conta, non si stima* | ⭐ **`ngtcp2`, lo strato di B2 da solo: 553 righe aggiunte — 373 di CODICE, 134 di commento, 46 vuote** `[M]` **ore 16:30**, su albero pulito dopo i due `--togli` e riapplicando il solo innesto di B2. ⚠ *Alle 08:00 la stessa misura dava **456 / 329**: la lettura della capsula di chiusura è cresciuta lì dentro. La successione sta in `DECISIONI.md` §6.4, non qui.* ⛔ **I 972 / 618 dei due innesti insieme non vanno in questa riga.** ⚠ Su `quiche` il numero **non esiste e non esisterà**: la candidata cade prima, ed è il lavoro che non abbiamo speso | 10 ago |
| **B2** — quanto pesa il loro esempio (il punto di partenza) | *si conta* | `ngtcp2` **7.041 righe** (HTTP/3 completo, C++, 13 file) · `quiche` **614** (esempio minimo, C, 1 file) `[M]`. ⛔ Due etichette diverse: non si sottraggono | 10 ago |
| ⭐ **B3** — la **1ª** connessione, fino a `SESSIONE` | passa | ⭐ **passa** `[M]` 10 ago: `CIAO`→`ECCOMI`→`CREDENZIALI`(PAM)→`AMMESSO`→`ATTACCA`→`SESSIONE`, e ⛔ **la traccia è dichiarata CONFORME dal validatore di B4** | 10 ago |
| ⭐ **B3** — la **2ª dopo la chiusura della 1ª** | **identica alla prima** | ⭐ **passa** `[M]`, e anche la sua traccia è conforme. ⛔ **Non lo era al primo giro**: vedi il difetto qui sotto | 10 ago |
| ⭐ **B3** — la **2ª mentre la 1ª è viva** | `CONGEDO(0x0F)` a chi arriva, e la 1ª sopravvive | ⭐ **passa** `[M]`: la seconda riceve `GIA_ATTIVA_REMOTA` **per tutt'e due le strade di §3.1** — `CONGEDO` sul controllo *e* codice `0x0f` nella chiusura della sessione — e la prima sopravvive. ⚠ *Era rossa al primo giro, e il difetto era del banco* | 10 ago |
| ⭐⭐ **B3** — la 2ª **dopo il silenzio** della 1ª, 35 s a `max_idle_timeout` **120** | **entra** | ⭐ **entra** `[M]`, e ⛔ **con il controllo che dice no**: a **+6 s** la seconda è **rifiutata** con `0x0F`, a **+35 s** la terza **entra**. Il registro: `STACCATO per silenzio: 30072 ms`. ⭐ E la connessione della prima è **ancora viva**: a liberare il posto è stato **il server**, non QUIC | 10 ago |
| ⭐ **B3** — la 3ª con il certificato **ruotato a mano** | passa | ⭐ **PASSA, pieno** `[M]` **2026-08-10 sera**: rotazione (impronta nuova ≠ vecchia, quattro controlli sui certificati su quattro), la pagina ritira la nuova e apre su Chrome 151 e Firefox 140, **e il server risponde `ECCOMI` al `CIAO` della sonda** — la seconda metà del criterio di B2 è soddisfatta —, e con la vecchia **tutt'e due rifiutano**. ⛔ Il rosso del mattino era della SONDA, non del certificato: mandava `ciao` e aspettava l'eco di B2, che con RCP innestato non esiste più. ⚠ Resta `[?]` che a rifiutare sia il confronto dell'impronta e non una delle altre due cause con lo stesso aspetto.<br><br>*Quel che diceva prima* `[M]` **2026-08-10 09:36**, Chrome **151.0.0.0** e Firefox **140.0**: con l'impronta corrente (`5o99/7rSTJER…`) la **sessione si apre** su tutt'e due — 149,0 ms Firefox, 180,0 ms Chrome — ⛔ **ma lo stream non ha funzionato in nessuno dei due** (`remote WebTransport close` · `The session is closed.`), e il criterio di B2 vuole *«la sessione si apre su Chrome e Firefox, **e la pagina riceve un byte dal server**»*. ⚠ Con l'impronta vecchia (`35wqjGTOmKSj…`) **tutt'e due rifiutano** — Firefox `WebTransport connection rejected`, ⚠ Chrome `Opening handshake failed.`, *due frasi diverse* — ma `[?]` **che a rifiutare sia il confronto dell'impronta non è dimostrato**: l'esito registrato dichiara di suo **tre cause con lo stesso aspetto** (UDP filtrato · impronta non del certificato servito · certificato oltre i 14 giorni), e nessuno le ha distinte. È la forma **E1**, e il banco l'aveva già dichiarata | 10 ago |
| ⭐ **B3** — il **secondo fisso** di §4.4-bis, cronometrato | ≥ 1000 ms **anche su `AMMESSO`** | ⭐ **1074–1085 ms** `[M]` su tre connessioni. È una proprietà che nessun altro banco vede | 10 ago |
| ⭐ **B10** — PAM, con `pamtester` come controllo | entra | ⭐ **entra** `[M]`: `pamtester login prova authenticate` riesce, e il server ammette lo stesso utente | 10 ago |
| ⭐ **B4** — sette guaste, quattro rotte, una conforme, una senza niente da giudicare | i **quattro esiti** coperti, byte esatto | ⭐ **13 su 13** `[M]` 10 ago sera: ciascuna guasta accusata sul **byte dichiarato in anticipo**, e i quattro codici d'uscita del validatore tutti esercitati (0 conforme · 1 non conforme · 2 registrazione rotta · 3 niente da giudicare). Il validatore è **certificato** | 10 ago |
| ⭐⭐ **B4** — e ha trovato una contraddizione in `RCP.md` | *non era un atteso* | ⛔ §4.3 vietava il trattino basso nei nomi di capacità **e ne definisce uno che ce l'ha** (`video.misura_massima`). Curato in `RCP.md` §4.3 | 10 ago |
| ⭐⭐ **B5** — le violazioni, e il server vivo dopo ciascuna | motivo giusto sempre, **server vivo sempre** | ⭐ **36 violazioni su 36 + 8 verdi attesi su 8** `[M]` 10 ago sera, e per **tutt'e due le strade di §3.1** ogni volta — ⛔ **36 su 36 anche sul punto 3**, che nessuno aveva mai contato: `CONGEDO` sul controllo *e* il codice del motivo nella chiusura della sessione. ⛔ E dopo **ciascuna** una connessione nuova arriva a `ECCOMI`: il server è sempre lì | 10 ago |
| ⭐ **B5** — i cinque casi che **devono passare** | *nessuna caduta* | ⭐ **5 su 5** `[M]`: `hevc,vp9` sceglie `hevc` e scrive lo scarto · **vista 300×801** e **1×1** passano (§7.1, R4.10) · `BANCO_MARCA` a funzione spenta risponde `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)` e **la sessione regge** · `ritardo_ms = 20000` → `RITARDO_FUORI_LIMITI`, **non** `ERRORE_PROTOCOLLO`. ⛔ Senza di loro «il server chiude su tutto» darebbe 44 verdi su 44 | 10 ago |
| ⭐⭐ **B5** — e ha trovato **un difetto che nessun altro banco vedeva** | *non era un atteso* | ⛔ il contatore **per indirizzo** di §4.4-bis era chiavato sulla `provenienza`, che contiene **la porta**: con un solo tentativo per connessione (§4.4) la porta cambia ogni volta, e quel contatore **valeva sempre 1**. Codice presente, che sembrava giusto, e che non faceva niente. Curato, e ora al **sesto** tentativo scatta `TROPPI_TENTATIVI` — anche per la parola d'ordine **giusta**. ⚠ *Il **sesto** è della regola di quel giorno; dal 10 agosto sera la regola è il **ban al quarto** (`DECISIONI.md` §1.9), e questa riga resta com'è perché una misura porta la data della regola che misurava* | 10 ago |
| ⭐ **B5** — e una **seconda contraddizione in `RCP.md`** | *non era un atteso* | ⛔ §2.2 dice che un `CIAO(2)` su `/rcp/1` è `VERSIONE_INCOMPATIBILE`; §9 dice che il server sceglie *«la più alta che non superi quella del `CIAO`»*, cioè `ECCOMI(1)`. **Byte diversi sul filo per lo stesso ingresso**, e nessuna delle due cita l'altra. Vince §2.2 (la più specifica); `RCP.md` §9 curata. ⚠ *La cura citava **§2.4**, che è «La porta»: numero corretto lo stesso giorno, rilievo **R11.2*** | 10 ago |
| ⭐⭐ **B11** — le violazioni verso la pagina | 13 su 13 | ⭐ **13 su 13 su TUTT'E DUE i motori** `[M]` 10 ago sera — Firefox **140.0** e Chrome **151.0.0.0**, `CONFORME` con **0 guasti** — **più le due proprietà negative** (`desktop` non cambia i byte usciti · nessun battito applicativo). ⭐ **E ripetuto**: due giri completi conformi, `15:51:54`+`15:52:28` e `15:54:51`+`15:55:24`. ⚠ *Alle 11 questa riga diceva «12 su 12 su Firefox, 9 su 12 su Chrome»: i tre rossi di Chrome sono stati chiusi la sera stessa, e questo documento era rimasto indietro fino al rilievo **R11.4** del 10 agosto* | 10 ago |
| ⛔ **B11** — e il controllo che dice **no** | la pagina contro un server **SANO** deve dire NON-CONFORME | ⭐ **NON-CONFORME** `[M]`, **9 casi su 13** falliti. Senza, «tredici verdi» sarebbe compatibile con una pagina che approva qualunque cosa. ⚠ `[?]` **gira su un motore solo** (Firefox), e il banco lo dichiara di suo — **rilievo R11.24**. ⭐ *Dalla notte del 10 agosto 2026 lo dichiara anche il `README.md`, che prima lo elencava dentro «su tutt'e due i motori»: resta da **eseguirlo anche su Chrome**, e la differenza morde proprio qui, perché i tre casi rossi di stasera vivevano **nella differenza fra i due motori*** | 10 ago |
| **B6** — i tre tetti | 5 s · 60 s · 10 s, **col motivo giusto** | ⚠ **5,0 · 60,1 · 10,0 s**, e ⭐ **il cronometro parte dall'apertura del CANALE DI CONTROLLO** — R3.27 chiusa, `RCP.md` §4.6 riga 1 cambiata di una parola. ⛔ **E una seconda risposta**: la sessione che il canale non lo apre mai **non ha addosso nessun tetto** (`DECISIONI.md` §7.17). ⛔ **Questi tre numeri non hanno un registro**: non esiste nessun `.jsonl` di B6, la scena di quel giro non è dichiarata da nessuna parte e **non sono riverificabili** — si rifanno col registro, o restano tre numeri di cui si sa solo l'ordine di grandezza | **10 ago**, ora non registrata |
| **B7** — i motivi dal lato che riceve, frasi distinte, nessun numero | ⛔ **7 provocabili su 15 dichiarati** + **15 frasi distinte** | ⭐ **7 su 7 + 15 su 15**, con gli **otto esclusi** e la ragione di ciascuno. ⚠ *L'atteso di questa riga diceva «**8 su 8** + 8 frasi distinte», e l'ottavo — `SERVER_IN_CHIUSURA` — è quello che il banco **misura** di non poter produrre sull'innesto* | **10 ago** |
| **B8** — ≥ 1 s per campione, **e le tre mediane indistinguibili** | ≥ 1 s in **ogni** campione, e le tre mediane **indistinguibili** fra loro | ⚠ **parziale**: **2636 ms** di mediana sui **42** tentativi respinti, dove §4.4-bis vuole ~1000 ⇒ ⛔ **a governare i tempi è PAM, non il nostro ritardo fisso**. Le tre mediane **restano da confrontare**. ⚠ E il numero è la mediana **del servizio `login`**: il prodotto usa `remotix`, quindi con lui **la misura va rifatta** | **10 ago** |
| ⛔ **B8** — il ban: tre falliti con **tre nomi diversi**, poi il quarto con la parola **giusta** | il quarto **rifiutato** con `TROPPI_TENTATIVI`, e la pagina lo dice | | |
| ⭐ **B8** — i tre controlli che dicono *no* | un **altro** indirizzo entra · **2 falliti · 1 riuscito · 2 falliti** non banna · il ban **sopravvive al riavvio** | | |
| **B8** — lo sblocco, in fondo al giro | l'indirizzo rientra, e lo sblocco è **nel registro** | | |
| **B9** — `aioquic` porta WebTransport; la stretta di mano completa | sì; e **l'elenco delle ambiguità trovate** | ⭐ **12 punti su 12**, ciascuno con le due letture, la lettura che il secondo lettore ha scelto, **i byte che cambiano sul filo** e il caso concreto in cui la differenza morde. L'elenco sta in «Che cosa NON ha funzionato» — ⛔ **sono difetti del documento, non del banco** | **10 ago** |
| **B10** — l'utente `prova` entra, con `pamtester` come controllo | entra | ⭐ **entra** — vedi la riga di B10 qui sopra | **10 ago** |
| **B13** — le sei cose | 6 su 6 | ⛔ **non certificato**: il guasto costruito per lui **non è quello giusto** (accende il server con l'altro certificato, che B13.1 non guarda perché legge le impronte dei **file su disco**), e l'orchestratore non lo sa nemmeno innestare. `[M]` B12, 10 ago 22:24 e 22:25 | **10 ago** |
| **C1** — dodici guasti costruiti a mano | **12 rossi su 12** | ⛔ **3 su 12**, e le parole giuste per gli altri: vedi il riquadro «Che cosa B12 ha certificato davvero» | **10-11 ago** |
| **C2** — tre modi di fallire | **tre diagnosi diverse** | ⭐ **certificato** `[M]` 10 ago 22:32 (macchina `NIC-OS`), con una marca **discriminante**. ⚠ Un giro precedente (22:28) lo dava **non certificato**: fra i due è cambiato il file, non il verdetto — l'impronta di `01-c2-diagnosi.py` è diversa nelle due righe | **10 ago** |

---

## ⛔ Che cosa NON ha funzionato

*Si riempie anche quando fa una brutta figura* (`PIANO.md` §0.3 regola 2). ⭐ **E qui va ogni punto
in cui `RCP.md` ha ammesso due letture**: sono difetti del documento, e questa è la fase in cui
costano meno.

### ⭐⭐ I dodici punti in cui `RCP.md` ammette due letture — B9, 10 agosto 2026

*È **l'esito più prezioso di B9**, e questa sezione lo dichiarava in anticipo: «l'esito più prezioso
non è "passa": è ogni punto in cui chi lo scrive ha dovuto scegliere perché `RCP.md` ammetteva due
letture». `banchi/01-b9-letture.py` li ha trovati e li tiene con **gli appigli citati alla lettera**
— una citazione che non si trova più è una voce che parla di un altro documento — e con **i byte che
cambiano sul filo** fra l'una e l'altra. ⛔ Portati qui l'11 agosto 2026: finché stavano solo nel
banco, erano dodici difetti del documento che il documento non sapeva di avere.*

⛔ **Perché la colonna dei byte è quella che conta**: due letture che producono gli stessi byte sono
una questione di gusto. Queste **producono byte diversi per lo stesso ingresso**, cioè due
implementazioni conformi a `RCP.md` divergono senza che nessuna delle due abbia torto — che è
esattamente ciò che §0 esiste per impedire.

| # | Dove | La domanda | Che cosa ha scelto il secondo lettore | ⛔ Il byte che cambia |
|---|---|---|---|---|
| **L1** | §4.3 | `ECCOMI` porta **l'elenco** dei codec del server o **la scelta**? | ⚠ nessuna delle due: legge i due byte della versione e **butta il resto** — la lettura A **per omissione**, cioè la scelta fatta senza accorgersi di sceglierla | il valore di `video.codec`: `0008 «hevc,av1»` contro `0004 «hevc»`, e con lui la `lunghezza` u32 |
| **L2** | §3.1 punto 3 | il codice d'errore della chiusura: il motivo **nudo** nei 32 bit, o **mappato** come vuole HTTP/3? | A — e ⛔ **in più tronca**: legge l'**ultimo dei quattro byte**, quindi un codice sopra 255 gli arriverebbe come **un altro motivo**, senza una riga che lo dica | `00 00 00 0D` contro otto byte di un valore mappato — e la capsula cambia lunghezza. ⚠ `RCP.md` **non dichiara la larghezza del campo in nessun punto** |
| **L3** | §3.1 p. 2 contro §4.2 | dopo il `CONGEDO`, il canale si chiude **con un FIN** o si chiude solo la sessione? | B — non manda mai il FIN; e dal lato che riceve chiama il FIN *«il canale si è chiuso»*, che è un esito **diverso** da «sessione chiusa dal server» | il **bit FIN** del frame STREAM che porta il `CONGEDO`: gli stessi byte di carico, un bit di trasporto in più |
| **L4** | §6.1 | byte in più in coda al corpo, con la `lunghezza` che li conta: **violazione** o **riserva** per il futuro? | ⛔ **i nostri due lettori hanno scelto DIVERSAMENTE**: il cliente di prova legge `lunghezza` byte e passa il corpo così com'è (B, tollerante); il **validatore di B4** ha una registrazione apposta per bocciarlo (A) | quattro byte in coda e la `lunghezza`: `0000002A` contro `0000002E`. ⛔ È il difetto che B9 esiste per trovare: **l'arbitro e il secondo lettore non leggono la stessa specifica** |
| **L5** | §4.3 | una capacità **assente** è un elenco **vuoto** (⇒ `NIENTE_IN_COMUNE`) o una cosa **non negoziata**? | ⚠ **la domanda l'ha evitata**: dichiara sempre tutte e otto le capacità, quindi nessuna sua esecuzione la farà mai emergere | il campo `quante`: `0003` contro `0002`, e ventidue byte in meno |
| **L6** | §4.6 riga 1 | da quale istante parte il primo tetto? | ⛔ **ha scelto B6**, che lo fa partire dall'apertura del canale — ed è una scelta **del banco**, non del documento | ⛔ **nessuno, e va detto invece di inventarne uno**: le due letture mandano lo stesso `CIAO`. Cambia **quando** arriva il `CONGEDO(TEMPO_SCADUTO)` — e nel caso della sessione senza canale, **se** arriva. ⇒ `DECISIONI.md` §7.17 |
| **L7** | §2.2 | la `CONNECT` estesa deve portare un `origin`? | A — **lo manda**, copiando il browser. ⚠ È prudente e ha un prezzo: mandandolo, **non può più scoprire** se il server lo pretenda — l'arbitro si è adattato all'imputato | il campo `origin` nell'intestazione della `CONNECT`: una riga in più, compressa da QPACK |
| **L8** | §4.5 | un `desktop` fuori dai sei nomi: **campo fuori intervallo** (§3) o **stringa di diagnosi** da non guardare? | B — lo stampa e non lo controlla | la stringa in fondo a `SESSIONE`: `0005 «gnome»` contro `0007 «plasma6»` — e la connessione che sopravvive o cade. ⚠ **Le due letture stanno in sei righe, una sotto l'altra, e sono opposte** |
| **L9** | §11.1 contro §6.0 | nella registrazione, che cosa si scrive in `stream` quando l'identificatore non si conosce? | ⛔ **sempre zero** — ma §6.0 vieta i valori sentinella impliciti, e **zero è un identificatore di stream legale** (è quello della `CONNECT`) | gli otto byte di `stream`: `…04` contro `…00`. ⚠ E il validatore **non se ne può accorgere**: un campo sempre zero e un campo assente hanno lo stesso aspetto — forma **E8** |
| **L10** | §8.1 contro §4.4 | il client, dopo un `RESPINTO`, deve mandare `CONGEDO`? | ⚠ **una terza cosa**: non manda mai un `CONGEDO`, in nessun caso — cioè **non esercita mai** l'obbligo che §8.1 mette su chi chiude | un'inquadratura di **undici byte** contro **il silenzio**. ⛔ Il caso è già costato un rosso: il server contava come «byte dopo la fine» anche il congedo **conforme** della pagina |
| **L11** | §9 contro §2.2 | che versione mette nel `CIAO` un client che ne sa parlare **due**, su `/rcp/1`? | ⚠ scrive `1` a mano perché ne sa parlare una sola: **la domanda non gli si è posta**, e non se la porrà finché RCP/2 non esisterà | i due byte di `versione`: `0002` contro `0001` — e una connessione che vive o muore |
| **L12** | §4.5 contro §7.1 | i limiti 320×240-7680×4320 e la parità valgono anche per `vista_*` dentro `ATTACCA`? | ⚠ manda **vista = tela**: ancora una volta la domanda evitata, non risposta | `vista_larghezza`/`vista_altezza`: `00000780 00000438` contro `0000012C 00000321` (sotto il minimo e dispari). ⭐ **La risposta esiste ed è B**, ma sta in **§7.1** — chi implementa `ATTACCA` leggendo §4.5 non ha nessun motivo di andarci |

⛔ **Che cosa se ne fa**, e non è «si sistemano tutte adesso»: **tre** di queste dodici sono già
domande aperte dove le decisioni stanno — L3 in `DECISIONI.md` §7.14, L10 in §7.15, L6 in §7.17. Le
altre nove sono **difetti di scrittura di `RCP.md`**, e il posto in cui si curano è `RCP.md`, una
riga per volta, ⛔ **senza aggiungere tipi di messaggio**: la clausola di §9 è consumata dal 10
agosto.

⚠ **E una cosa che B9 dice di sé, e va letta**: `01-b9-letture.py` verifica che le due letture di
ogni voce producano **byte diversi**, e una voce «UGUALI» è **un rosso di B9**. Cioè l'elenco non
può crescere di voci inventate per far tornare la colonna — e L6, che byte non ne cambia, lo
**dichiara** invece di fabbricarne uno.

### ⛔ Tre trappole in un giro solo, e la terza non era nei banchi — 11 agosto 2026, sera

*Dal giro che ha certificato **B8**. ⭐ Le prime due sono difetti che il progetto aveva già scritto,
e la terza spiega perché le prime due erano rimaste invisibili.*

- ⛔ **La pagina del ban era illeggibile sull'innesto, e nessuno lo sapeva.** `leggi_pagina()`
  incartava **sempre** in TLS — `[M]` `SSLError: WRONG_VERSION_NUMBER` da tutt'e due gli indirizzi —
  perché l'innesto la serve **in chiaro**. ⇒ Il banco scriveva *«la pagina non si è caricata»*, cioè
  **il silenzio che §4.4-bis vieta al ban**, su un server che la pagina la serve. ⚠ **Ed era la cura
  del giorno prima ad averlo spostato**: era stata scritta per il **prodotto**, che vuole HTTPS. Due
  rossi opposti a un giorno di distanza, e in tutt'e due i casi **il server faceva la cosa giusta**.
  ⭐ Ora il dialetto lo **dichiara il bersaglio**, e se quello dichiarato tace si prova l'altro:
  *«il dialetto è l'altro»* è un fatto, *«non ho parlato con nessuno»* è un altro fatto.
- ⛔ **Due redirezioni ATTORNO a `enter.sh` — dentro i due file che quella trappola la descrivono in
  testa.** La richiesta di `sudo` esce su **stderr**: buttandola via, **nessuno può rispondere**.
  `[M]` `ps` sul server: `sudo -v -S -p Password` fermo, ⛔ **col guasto ancora addosso al codice**,
  che è il peggior punto in cui fermarsi. ⚠ Da un terminale interattivo è **invisibile** finché il
  credito di `sudo` regge: morde solo sui giri lunghi, cioè quelli che costano di più da rifare.
  ⇒ È la **quinta veste** della regola pagata il 10 agosto, e stavolta dentro i suoi stessi guardiani.
- ⛔⭐ **E la causa vera stava nello strumento, non nei banchi**: `fondamenta/strumenti/sshpw.py` rispondeva
  ad al massimo **64** richieste di parola d'ordine, e un giro di certificazione di B8 — **tre**
  esecuzioni del banco, una sessantina di ingressi nel contenitore ciascuna — ne chiede **oltre
  200**. Il giro si fermava a metà del passo «guasto», ⚠ **e il sintomo era di nuovo quello che
  inganna: non un errore, una prova «lenta»**. Chi guardava il registro vedeva l'ultimo blocco
  stampato e credeva che stesse ancora misurando. ⚠ Il tetto era **già stato alzato una volta**, da 8
  a 64, per la stessa ragione: **è la terza**. ⭐ Il numero giusto non è *«quante ne servono oggi»*:
  a proteggere non è il tetto, è **l'ancora** che spedisce la parola d'ordine solo a chi la sta
  chiedendo **in quell'istante**.

### I difetti pagati, uno per uno

| | |
|---|---|
| ⛔ **la prima stesura del banco, 9 agosto** | 44 rilievi su due revisioni. La forma che si ripete: **cadeva sempre il controllo che dice *no***, e in tre casi era già stato scritto da chi ci era passato prima. ⚠ *Due delle tre amputazioni erano state bocciate da `R2` poche ore prima, con l'istruzione «curare prima di scrivere una riga di banco»: il documento che le doveva ereditare curate le ha ereditate intatte* |

#### ⛔ Tre difetti di banco pagati in un'ora, sul primo banco eseguito — 9 agosto 2026

*E il terzo è il più istruttivo del progetto finora, perché **stava per cancellare la candidata
migliore** con un `[M]` falso contro un `[R]`.*

| # | Che cosa è successo | Che cosa insegna |
|---|---|---|
| **1** | `git clone -b master` di BoringSSL: *«Remote branch master not found»*. Google l'ha rinominato | ⚠ **un ramo scritto a mano è una dipendenza dal nome di qualcun altro**. Tolto: si prende il predefinito |
| **2** | ⛔ il fallimento è arrivato **con «uscita 0»** a chi guardava, perché avevo messo `\| tail` in coda al comando remoto: lo stato d'uscita era quello di `tail` | `LEZIONI.md` §1.9 — *zero e fallimento con la stessa faccia* — **presa nell'invocazione invece che nello script**. Il banco era innocente; chi lo lanciava no |
| **3** | ⛔⭐ il banco ha dichiarato **«0 simboli su 4»** stampando **i quattro simboli tre righe sopra** | vedi il riquadro |

> ##### ⛔ Il terzo: `set -o pipefail` più `grep -q`, cioè un falso rosso garantito
>
> Il controllo era `nm -g --defined-only "$LIB" \| grep -q " $s$"`. **`grep -q` esce al primo
> riscontro** e chiude il tubo; `nm` sta ancora scrivendo, prende `SIGPIPE`, muore con **141**; e
> `set -o pipefail`, in cima allo script, fa valere **quel 141** come esito della pipeline.
>
> ⛔ **Il riscontro riuscito veniva letto come fallimento** — e la perversione è che *più il simbolo
> era facile da trovare, prima `grep` usciva, più sicuro era il falso rosso.*
>
> ⚠ **Che cosa avrebbe prodotto se nessuno avesse guardato**: la riga *«il flag di `lsquic` non
> produce niente»* in `DECISIONI.md` §6.4 — cioè **la candidata con più WebTransport dentro,
> cancellata da un difetto del banco**, con un `[M]` falso che avrebbe battuto un `[R]` letto nel
> codice. È `LEZIONI.md` §2.3 (*una prova che boccia il codice giusto costa quanto una che promuove
> quello sbagliato*) e `CODER.md` §3.11 (*quando codice letto e misura si contraddicono, il sospetto
> va prima sulla misura*) nello stesso difetto.
>
> ⭐ **Che cosa l'ha fatto emergere**: non l'intuito — **tre righe di strumentazione nel banco**, che
> dichiarano su quale archivio si sta guardando e quanti simboli si vedono *prima* di dire quali
> mancano. Ora sono permanenti: erano la differenza fra «chi dei due mente» e mezza giornata di
> supposizioni.
>
> ⚠ **E una quarta, che non è un difetto ma un'abitudine da prendere**: la diagnosi a mano era
> passata attraverso **tre shell annidate** (locale → ssh → `enter.sh` → chroot) e si è rotta sulle
> virgolette, restituendo `grep: ...: No such file or directory`. La regola della fase 0 vale qui:
> **le righe di comando si mettono in un file, non si ricordano**.

#### ⛔ E il terzo difetto della stessa famiglia, che ha stampato un VERDE

*9 agosto, banco di `ngtcp2`.* Il controllo diceva **«nessuna traccia di `SETTINGS_WT_MAX_SESSIONS`:
la previsione regge»** — ⛔ **da una ricerca mai eseguita**. I due alberi erano passati a `grep` come
**una stringa sola**, quindi cercava in un percorso con uno spazio dentro che non esiste; e
`2>/dev/null` nascondeva il «No such file or directory» che l'avrebbe detto subito.

⛔ **È il peggiore dei tre, perché gli altri due davano rosso e questo ha dato verde** — e un verde
non lo si va a verificare. A insospettirmi non è stato il banco: è stato **un numero impossibile**
nella riga accanto — «extended CONNECT in 0 file» su una libreria che implementa RFC 9220.

⭐ **La cura è diventata una regola generale**, ed è entrata in `LEZIONI.md` §1.9 come **quarta
regola**: *una misura deve dichiarare su che cosa ha guardato — il denominatore, non solo il
risultato*. Adesso il banco stampa «dentro 447 file di 2 alberi» e **cerca una cosa che deve
esserci** (`nghttp3`, trovata in 110 file) prima di credere a uno zero.

#### ⚠ `aioquic` sa creare uno stream WebTransport e non sa riconoscerlo quando risponde

*Trovato costruendo il controllo positivo, 9 agosto 2026, ed è del **cliente di prova** — quindi
tornerà a mordere a ogni fase in cui quello cresce.*

Il primo giro andava in **timeout aspettando il ritorno**, mentre il server dichiarava di averlo
spedito. `[R]` `H3Connection.create_webtransport_stream` di aioquic 1.2 scrive l'intestazione dello
stream e **non registra lo stream in ricezione**: i byte tornano — si vedono a livello QUIC — e il
livello H3 non emette nessun `WebTransportStreamDataReceived`.

⛔ **Che cosa l'ha distinto**: due righe che stampano gli eventi **a tutt'e due i livelli**. Senza,
*«i byte non arrivano»* e *«i byte arrivano e nessuno li riconosce»* sono lo stesso rosso — e sono
due difetti in due posti diversi. È la seconda volta in un'ora che la strumentazione batte
l'intuito.

⚠ **La cura è dichiarata, non nascosta**: il ritorno si legge a livello QUIC, **scrivendo perché**.
Fingere che l'abbia riconosciuto il livello H3 sarebbe stato comodo e falso.

#### ⛔ Sei difetti di banco per una prova che dura due secondi — 10 agosto 2026

*La prova SNI di B2 è **una connessione**. Ci sono volute **sei esecuzioni** per arrivarci, e
nessuno dei sei difetti era della libreria che si stava misurando.*

| # | Che cosa è successo | Che cosa insegna |
|---|---|---|
| **1** | ⛔ **Due server della sessione del 9 agosto erano ancora vivi**, otto ore dopo, e tenevano le porte 7447 e 7448. `bsslserver` ha scritto *«Could not bind»* ed è morto | ⚠ Il rootfs del server è in RAM e **non si riavvia mai**: *«l'avevo fermato»* non è un'informazione. ⛔ E il rosso non sarebbe stato «il banco non parte», sarebbe stato **«`ngtcp2` rifiuta»** — un rosso attribuito alla libreria. Ora la porta si controlla **prima** |
| **2** | La sessione remota è rimasta **appesa senza stampare nulla** | `>/dev/null 2>&1` su una chiamata a `enter.sh`: era la prima della sessione, `sudo` chiedeva la parola d'ordine, e **la domanda finiva nel nulla**. ⛔ È il `2>/dev/null` del 9 agosto in una veste peggiore: un errore nascosto fa sbagliare diagnosi, **una domanda nascosta ferma la macchina** |
| **3** | ⛔ E non si vedeva **dove** si fermasse, perché avevo messo `\| tail` in coda al comando remoto | ⚠ **Identico al difetto n. 2 del 9 agosto**, commesso di nuovo dalla stessa mano il giorno dopo: `tail` non stampa niente finché il flusso non finisce. La cura non è ricordarsene — è **scrivere su un file e leggerlo** |
| **4** | Il banco ha dichiarato **MORTI due server che stavano ascoltando** | `setsid` **forca**: `$!` era il PID di `setsid`, che esce subito, non quello del server. ⭐ E `lsquic` lo smentiva **tre righe sotto**, con un *«in ascolto»* stampato nel suo stesso registro |
| **5** | E l'ha rifatto dopo la cura | `kill -0` da utente normale su un processo di **root** risponde *«operazione non permessa»* — cioè **un errore**, non *«non esiste»*. ⛔ **Vuoto e proibito con la stessa faccia**, `LEZIONI.md` §1.9 regola 1, su un controllo di sanità. Cura: `[ -d /proc/<pid> ]` |
| **6** | Il collegamento è caduto su `cannot find -lngtcp2`, e ⛔ **il banco ha dato la diagnosi opposta** — *«cmake ha saltato gli esempi in silenzio»* | Cmake li aveva configurati benissimo: mancava la libreria **condivisa** (`ENABLE_SHARED_LIB=OFF`), che è il bersaglio che gli esempi chiedono. ⚠ Un messaggio d'errore che indovina la causa **manda a cercare nel posto sbagliato**: ora il banco distingue «ninja è fallito» da «ninja è riuscito e il file non c'è» |

> ##### ⛔⭐ E il settimo, che è il più grave del progetto finora: **la sonda dichiarava un denominatore falso**
>
> La quarta regola di `LEZIONI.md` §1.9 era **applicata**: la sonda stampava, a ogni gamba, che cosa
> avesse messo nel campo `server_name`. Diceva `'192.168.0.2'` — **e sul filo non andava niente.**
>
> Due righe di `aioquic`, in due file diversi: `asyncio/client.py:66` riempie il campo con l'ospite
> **anche se è un indirizzo IP**; `tls.py:1551` poi, scrivendo il ClientHello, **butta gli indirizzi
> IP**. La sonda leggeva la prima e credeva di descrivere la seconda.
>
> ⛔ **Conseguenza: la gamba «con SNI» mandava esattamente quel che mandava la gamba «senza SNI».**
> Le due gambe misuravano **la stessa cosa** mentre la sonda dichiarava che erano opposte — cioè il
> controllo che doveva distinguere «la libreria pretende l'SNI» da «il banco è rotto» **non
> distingueva niente**.
>
> ⚠ **E il verde di `ngtcp2` era già stampato quando me ne sono accorto.** Era vero — la misura
> rifatta lo conferma — ma era vero **per caso**: nessuna delle due gambe stava provando quel che
> diceva di provare.
>
> ⭐ **Che cosa l'ha fatto emergere**: non un sospetto, la riga stessa. `server_name spedito:
> '192.168.0.2'` in **tutt'e due** le gambe è un'impossibilità visibile — e l'ha resa visibile
> proprio la regola che stava sbagliando. Un denominatore falso si scopre solo se lo si stampa.
>
> ⛔ **La cura, in tre pezzi**: la sonda stampa il valore configurato **e** quel che finisce sul
> filo, con la riga di codice che li separa; la gamba di controllo usa un **nome** (`remotix.prova`)
> invece dell'indirizzo, perché è l'unico modo di far comparire l'estensione davvero; e ⭐ **il
> testimone finale non è nostro** — il registro di `lsquic`, che scrive *«SNI is not set»* guardando
> lo stesso filo dall'altro capo. È entrata in `LEZIONI.md` §1.9 come **corollario della quarta
> regola**: *un denominatore si legge dove la cosa succede*.

#### ⚠ E su `quiche`, quattro intoppi e **una trappola vera** — 10 agosto 2026

*I primi tre sono cronaca di costruzione, e stanno qui perché costano tempo a chi li rifà. Il
quarto è un fatto per `DECISIONI.md` §6.4. **La trappola è il quinto**, e sarebbe stata il terzo
falso rosso attribuito a una libreria in due giorni.*

| | Che cosa è successo | |
|---|---|---|
| **1** | `cargo`/`rustc` **non erano nel contenitore** | ⚠ Il `[M]` del 9 agosto diceva che *Trixie li offre* (1.85.0) — ed era vero. **«Disponibile come pacchetto» e «installato» sono due cose diverse**, e la seconda ora sta in `provision.sh` |
| **2** | Gli esempi in C stanno in `quiche/examples`, non in `examples` | Il deposito ha una cassetta per ogni pezzo e una si chiama come il deposito. ⭐ **Il banco l'ha detto** invece di contare zero: era la quarta regola che funzionava |
| **3** | Il loro esempio non compilava: manca `uthash.h` | Nel `provision.sh`, come le altre. È una dipendenza del **banco** di `quiche`, non del prodotto |
| **4** | ⛔ `cargo` si è fermato: **`quiche` 0.29.3 pretende `rustc` 1.88**, Trixie ne ha **1.85** | ⭐ **Non è un intoppo, è un dato della decisione.** Il banco adesso sceglie da sé la versione più recente che il compilatore presente sa costruire — la **0.28.0** — e stampa quale e perché. ⚠ E nemmeno quella basta da sola: il loro `workspace` tira dentro `tonic`, `icu`, `image`; si costruisce `-p quiche`, il solo pacchetto che useremmo |

> ##### ⛔ La trappola: il loro esempio **non controlla** di aver caricato il certificato
>
> `[R]` `quiche/examples/http3-server.c:564-565`: legge `./cert.crt` e `./cert.key` **dalla
> cartella corrente**, e ⛔ **ignora l'esito** di `quiche_config_load_cert_chain_from_pem_file`.
>
> ⚠ Con i due file assenti **il server parte lo stesso**, ascolta, e ogni stretta di mano
> fallisce — che alla sonda ha esattamente l'aspetto di *«`quiche` pretende l'SNI»*. Sarebbe stato
> il **terzo falso rosso attribuito a una libreria in due giorni**, dopo il `0 su 4` di `lsquic` e i
> due server dichiarati morti.
>
> ⭐ **La cura sta nel conduttore, non nella speranza**: mette i due file con i nomi che l'esempio
> pretende e **controlla che ci siano** prima di avviare. ⚠ E il controllo usa `case`, non
> `grep -q` in un tubo: con `pipefail`, `grep -q` esce al primo riscontro e il **riscontro riuscito**
> diventa un errore — il difetto del 9 agosto, che qui non si è ripetuto perché era scritto.

#### ⛔ E la misura col browser: **quattro silenzi**, e un verde su zero misure

*Il server minimo ha funzionato al primo colpo col cliente di prova. La misura col **browser** — che
è il criterio vero di B2 — ha richiesto cinque giri, e nessuno dei difetti era del server.*

| | Che cosa è successo | Che cosa insegna |
|---|---|---|
| **1** | ⛔ **L'impronta del certificato arrivava tagliata della prima cifra** | Il banco la estraeva con `[A-Za-z0-9+/]{42}=`, e un SHA-256 in base64 è **43** cifre più il riempimento. ⚠ Il sintomo sarebbe stato *«i browser non aprono la sessione con `ngtcp2`»* — cioè **una candidata bocciata per una lettera**. Ora il banco **conta i caratteri** invece di fidarsi dell'espressione |
| **2** | Firefox non chiedeva nemmeno la pagina, e **non lo diceva** | La cartella del profilo non esisteva: con `--profile` su una cartella assente, Firefox si ferma sul suo gestore dei profili. ⛔ **Silenzio su tutt'e due i lati** — zero richieste al raccoglitore, registro del browser vuoto — per una cartella mancante |
| **3** | ⛔ E non c'era modo di saperlo, perché il raccoglitore **taceva le richieste** | `log_message` era `pass`, con scritto accanto *«il rumore delle richieste non serve: serve l'esito»*. È falso: la richiesta **è il denominatore dell'esito**. Senza, *«il browser non è partito»* e *«è partito e la prova è fallita»* sono lo stesso silenzio |
| **4** | E il primo tentativo di denominatore **contava sé stesso** | Cercavo `01-b2-sonda.html` nel registro del raccoglitore, e quel nome compare anche nel suo **banner d'avvio**: ha stampato *«richieste: 1»* quando erano **zero**. ⚠ Terzo falso denominatore in due giorni, e stavolta l'ho scritto io mentre curavo il secondo |

> ##### ⛔ E il peggiore, che non è un difetto di diagnosi ma di giudizio: **OK su zero motori**
>
> Un giro ha stampato `OK — i motori provati hanno registrato il loro esito`, e i motori provati
> erano **zero**: il controllo di presenza guardava `xvfb-run -a`, cioè verificava che esistesse un
> programma chiamato `-a`, e saltava tutt'e due i browser dicendolo in una riga di avviso che
> l'esito finale contraddiceva.
>
> ⛔ *«Tutti quelli provati sono andati bene»* **è vero anche quando i provati sono zero**, ed è la
> forma di verde più vuota che ci sia — perché non ha nemmeno bisogno che qualcosa vada storto.
> ⭐ Ora il banco conta i motori provati, li stampa, e **si rifiuta di dare un esito se sono zero**.
>
> ⚠ *E vale la pena dire come si è visto: non da un sospetto, ma perché il numero dei motori è stato
> messo accanto al verdetto. È la quarta regola di `LEZIONI.md` §1.9 applicata al **verdetto**
> invece che alla misura — il denominatore di un'approvazione è quante cose ha approvato.*

#### ⭐⛔ Le sei proprietà: due difetti veri, e nessuno dei due aveva un sintomo

*E il difetto peggiore era in una misura **nostra**, dichiarata verde poche ore prima.*

> ##### ⛔ La misura che non misurava: il server che si dà ragione da solo
>
> Il 10 agosto il server minimo stampava all'avvio
> `REMOTIX B2: max_idle_timeout=30000ms max_datagram_frame_size=65536`, e quella riga è finita nei
> documenti come una misura di `RCP.md` §2.2. ⛔ **Ma è la sua configurazione, non il filo**: dice
> che cosa il server ha *chiesto* a ngtcp2, non che cosa è *arrivato* al pari.
>
> ⚠ È **esattamente** il corollario di `LEZIONI.md` §1.9 nato quella stessa mattina — *un
> denominatore si legge dove la cosa succede* — e l'ho violato io, quel pomeriggio, su una misura
> mia. La regola scritta contro `aioquic` non mi ha protetto dal commetterla contro me stesso.
>
> ⭐ La cura è `01-b2-sonda-trasporto.py`, che legge i parametri **dal pari**. E leggendoli da lì ha
> trovato subito due cose che nessuno aveva chiesto:

| | Che cosa si è visto | Perché nessun banco lo vedeva |
|---|---|---|
| ⛔ **il server offriva 0-RTT** | due biglietti di sessione con `max_early_data_size` = `0xffffffff`. `RCP.md` §2.3 lo **vieta**: i dati 0-RTT si possono ripetere, e il secondo messaggio di RCP è `CREDENZIALI` | ⭐ **Il documento l'aveva previsto**: *«il sintomo di 0-RTT acceso non esiste… le librerie QUIC lo offrono per impostazione predefinita»*. La sessione si apre uguale, i byte tornano uguali |
| ⛔ **concedeva 3 stream unidirezionali su 16** | `initial_max_streams_uni = 3` — quanti ne vuole HTTP/3 per il controllo e QPACK. §2.3 ne impone **almeno 16** «in ogni momento» | Il client di prova non ne apre nessuno. Il sintomo sarebbe comparso **nella fase 3**, come *«il desktop non risponde»* — e nessuno l'avrebbe collegato al credito |
| ⚠ **e la pagina non passava `allowPooling: false`** | §4.1-bis lo mette fra i vincoli, accanto al certificato di 14 giorni e alla chiave P-256 | Mettendolo a `true` la sessione si aprirebbe **uguale**: è un vincolo senza sintomo, e i due browser avevano già dato verde senza di lui |

⭐ **E il 0-RTT ha avuto il suo controllo positivo per caso, dal bersaglio stesso**: la sonda ha
*visto* un 0-RTT acceso prima di vederne uno spento. Il verde che è seguito è un verde dopo una
cura, non un verde da uno strumento cieco — che è la differenza fra i due che conta.

⚠ **E un colpo a vuoto, mio, che vale come regola**: curando la pagina ho sostituito una riga con
`str.replace` in Python su un appiglio con l'indentazione sbagliata. ⛔ **Python non protesta**:
restituisce la stringa intatta. La proprietà era nel codice ma non nell'esito registrato — cioè
affermata dal sorgente e non vista da nessuno. `01-b2-ngtcp2-wt-innesta.py` questo controllo ce
l'ha (l'appiglio dev'essere **uno**); le modifiche fatte a mano no, finché non l'ho aggiunto.

#### ⭐⛔ B3: due difetti veri, e il primo è **esattamente** quello che B3 esiste per trovare

> ##### ⛔ La stretta di mano funzionava **una volta sola**
>
> Al primo giro di B3 la **prima** connessione veniva rifiutata con
> `GIA_ATTIVA_REMOTA` — cioè il server diceva *«c'è già qualcuno»* a un client che era solo.
>
> La causa: `rcp_libera()`, che libera il posto nel registro delle sessioni, **non la chiamava
> nessuno**. Ogni connessione occupava un posto per sempre; dopo la prima riuscita, il server
> rispondeva `0x0F` a chiunque, per sempre.
>
> ⭐ **È la forma di `LEZIONI.md` §2.1 alla lettera**: *in v1 un certificato condiviso uccideva il
> server alla seconda connessione, e una prova a collegamento singolo resta verde per sempre*. Il
> banco che B3 impone — **due, mai una** — l'ha preso al primo giro. Una prova a connessione
> singola sarebbe stata verde e sarebbe rimasta verde fino alla fase 5.
>
> ⚠ E si noti dove **non** si sarebbe visto: la traccia della prima connessione è *conforme* a
> `RCP.md`. Il validatore non poteva dire niente — il difetto non è nei byte, è nello stato del
> server fra una connessione e l'altra.

> ##### ⭐⛔ Il secondo: il banco accusava il server, e il colpevole era il buffer di Python
>
> Il terzo giro dava **rosso sul server**: la seconda connessione, che arriva mentre la prima è
> attaccata, veniva **accettata** invece che rifiutata con `0x0F`. Sembrava una violazione
> dell'invariante **I2** — *«la seconda connessione è rifiutata con messaggio esplicito»*.
>
> ⛔ **Non lo era. Il server aveva ragione dal primo istante.**
>
> La diagnosi, e sono state due righe di strumentazione — *chi prende il posto, chi lo lascia, e
> quanti ne restano occupati*:
>
> ```
> posto PRESO da prova via [..]:39390 (occupati adesso: 1)
> sessione aperta utente=prova via=[..]:39390
> posto LASCIATO da prova via [..]:39390 (occupati adesso: 0)   ← prima che la 2ª arrivi
> ```
>
> E i **timestamp** di ngtcp2 hanno chiuso il caso: la prima connessione si chiude a **t≈13,1 s**
> con `CONNECTION_CLOSE 0x0` — cioè ha retto i suoi dodici secondi — e la seconda arriva **dopo**.
> Le due non erano mai state contemporanee.
>
> ⭐ **La causa**: il banco aspettava la parola `SESSIONE` nel registro della prima connessione, e
> **Python bufferizza lo stdout quando è rediretto su un file**. Quella riga compariva solo
> all'uscita del processo — cioè **nell'istante esatto in cui il client si staccava**. Il controllo
> stampava `OK la prima è attaccata` leggendo una verità appena scaduta, e la seconda trovava
> sempre il posto libero.
>
> ⛔ **È la forma peggiore di difetto di banco**: non un rosso su un verde, ma **un rosso puntato
> sull'imputato sbagliato**. Il server rispettava §3.1 alla lettera — manda `CONGEDO(0x0F)` sul
> canale di controllo *e* chiude la sessione col codice `0x0f` — e il banco lo dichiarava in
> violazione di un'invariante.
>
> ⭐ **La cura, e la regola che ne esce**: il client scrive un **file** quando la sessione è aperta,
> e il banco aspetta quel file. *Un file scritto e chiuso è un fatto; una riga stampata è una
> speranza sul momento in cui qualcuno la vedrà.* (E `python3 -u`, che toglie l'altra metà della
> causa.)
>
> ⚠ E vale la pena dire **come non si è visto prima**: il controllo «la prima è attaccata» c'era, ed
> era proprio quello che doveva impedire questo errore. Era scritto giusto e misurava l'istante
> sbagliato.

#### ⛔ E due difetti di banco degli ultimi due giri, uno dei quali ha dato un VERDE

| | Che cosa è successo | |
|---|---|---|
| **1** | ⛔ Il validatore ha dichiarato **«conforme»** una registrazione mentre il cliente di *quel* giro non si era nemmeno collegato | Stava giudicando il **file rimasto dal giro precedente**. ⚠ Un verde da un file stantio: la registrazione ora si **butta prima**, e se manca il banco dice *«non ho niente da giudicare»* — che non è «conforme» |
| **2** | Il cliente «non si collegava», e il colpevole ero io | `shift 3` con **meno di tre argomenti non sposta niente e non fallisce**: `$*` restava `accendi`, il server riceveva il nome dell'azione come opzione e moriva con *«port: invalid port number»*. ⛔ **Di nuovo il rosso sull'imputato sbagliato**, e stavolta a una manciata d'ore dalla lezione che l'aveva appena nominato |

> ⚠ **E una scelta di documento, dichiarata invece che nascosta**: `SPECIFICHE.md` §5.3 dice che un
> client silenzioso da trenta secondi «si considera staccato», e **non dice che cosa succede alla
> sua connessione**. Qui si è scelto di **lasciarla aperta** e liberare solo il posto: chiuderla
> sarebbe un congedo, e §8.2 non ha un motivo che voglia dire *«taci da un po'»*. È uno dei punti
> in cui `RCP.md` ammette due letture, ed è quel che questa sezione esiste per raccogliere.
>
> ⚠ **E un filo dell'ospite, non del protocollo**: per valutare l'orologio mentre il client tace, il
> server accende il **keep-alive di QUIC a 5 s** — è un battito del *trasporto*, che §2.2 non
> vieta, ma un server vero armerà un proprio timer e non metterà niente sul filo.

#### ⛔ E tre trappole di shell in una sera, tutte la stessa

Il terzo giro di B3 si è impiccato **tre volte**, e ogni volta per lo stesso motivo in una veste
diversa: una **sottoshell in secondo piano**, una **sostituzione di comando**, e un
**`nohup ... &` con le virgolette annidate** — tutt'e tre attorno a `enter.sh`, e tutt'e tre si
portano via la richiesta di password di `sudo`. Lo script resta ad aspettare una domanda che
nessuno vede.

⭐ **La cura è la regola che il progetto aveva già**: le righe di comando si mettono in un file. Il
terzo giro adesso è `01-b3-terzo-giro.sh`, e gira **dentro** il contenitore, dove non c'è nessun
`sudo` e nessuna shell annidata.

⚠ **E un'ultima, a mio carico**: fermando i banchi ho scritto `pkill -f "01-b2-raccogli.py"`, e il
comando **ha ucciso la shell che lo eseguiva** — il modello compariva nella sua stessa riga di
comando. È la trappola del 9 agosto, scritta nel README di questo progetto, ripetuta il giorno dopo
da chi l'aveva appena documentata. Si ferma **per PID**.

⛔ **E la quarta veste, la sera dopo, su `01-b5-lancia.sh`**: `bash enter.sh --root "ninja …" > log
2>&1`. Nessuna sottoshell, nessun `&`, nessuna virgoletta annidata — **solo una redirezione**, e
`sudo` si è fermato lo stesso. Sei minuti a guardare un processo senza figli e un registro vuoto.
⭐ **La regola è più larga di come era stata scritta**: *non è `>/dev/null`, è **qualunque
redirezione attorno a `enter.sh`***. Dentro le virgolette invece è del comando remoto, e la
richiesta resta sul filo dove qualcuno la vede.

#### ⭐⛔ B5: quarantaquattro violazioni, e **un difetto che nessun altro banco poteva vedere**

*Il banco è passato al primo giro su tutte le violazioni. Il rosso è arrivato da un **controllo**,
ed era stato **previsto per iscritto dentro il banco prima di misurare**.*

⛔ **Il contatore per indirizzo di §4.4-bis non ha mai bloccato nessuno.** La chiave era
`s->provenienza`, cioè `192.168.0.2:44661` — **con la porta**. E §4.4 ammette **un solo tentativo
per connessione**: la porta cambia ogni volta, quindi quel contatore valeva **sempre 1**.

⚠ **È la forma peggiore**: il codice c'era, si leggeva bene, sembrava giusto, e **non faceva
niente**. Nessun registro lo nominava; il sintomo — *«si può provare una parola d'ordine
all'infinito»* — non arriva mai da solo.

⭐ **E il controllo che l'ha trovato è preciso**: sette tentativi falliti con **sette nomi diversi**
dallo stesso indirizzo. Con lo stesso nome, il contatore **per nome** copriva il buco e il banco
sarebbe stato verde. Curato; ora al **sesto** tentativo scatta `TROPPI_TENTATIVI` — ⛔ **anche per
la parola d'ordine giusta**, che è il secondo controllo, quello che distingue un contatore da un
blocco.

⚠ **E un ordine che è una misura**: il giro completo buono si esegue **prima** del limitatore. Dopo,
l'indirizzo è bloccato per trenta secondi, e un banco che mettesse la stretta di mano in coda
leggerebbe quel rifiuto come *«il server è rotto»* — cioè darebbe rosso **proprio quando la regola
funziona**.

#### ⭐⛔ B11: il difetto che serviva **un browser vero** per esistere

*E che B3 non poteva vedere, per cinque giri, con nessun cliente di prova.*

⛔ **Il posto nel registro delle sessioni si liberava solo alla morte della CONNESSIONE.**
`rcp_libera()` stava in `~ProtoCodec`. Con `aioquic` i due istanti coincidono — il cliente di prova
chiude tutto — e B3 è rimasto verde. ⭐ **Un browser no**: chiude la *sessione* e **tiene viva la
connessione**, e da quel momento il posto resta occupato da una sessione che non esiste più.
Con Chrome: **sette `posto NEGATO` su nove tentativi**, e alla pagina arrivava solo silenzio.

⚠ È **la stessa forma** del difetto che B3 aveva trovato il giorno prima — il posto che non si
libera — in un altro punto. ⛔ *Il difetto viveva nella differenza fra i due client, quindi nessuna
prova con un client solo poteva trovarlo.* È `LEZIONI.md` §2.1, la regola dei tre client, applicata
a una cosa che sembrava già provata.

⛔ **E il secondo, che riguarda §3.1 alla lettera.** `respingi()` manda `RESPINTO` sul canale di
controllo e chiude la sessione **nella riga dopo**: i due finivano nello stesso volo di pacchetti, e
il browser processa la capsula `CLOSE_WEBTRANSPORT_SESSION` **prima** dei byte dello stream, che a
quel punto butta. ⛔ **La pagina non ha mai visto `RESPINTO`: ha visto silenzio.**

⭐ **Ed è la dimostrazione che il punto 3 di §3.1 non è ridondanza**: il motivo è arrivato comunque,
dentro il codice d'errore della chiusura. *«Se il congedo non arriva — perché lo stream era rotto,
perché il messaggio era illeggibile — il motivo viaggia comunque»* è vero alla lettera, e questo è
il caso che lo prova. ⚠ Curato lo stesso da tutt'e due i lati: il server **rimanda** la capsula
finché la coda d'uscita non è vuota, e la pagina **legge `wt.closed`**.

⛔ **E il terzo, che è della PAGINA e lo ha reso visibile la differenza fra due motori.** La pagina
**chiudeva senza congedarsi**: chiamava `close()` e basta. Ma §8.1 dice che chi chiude *DEVE*
mandare `CONGEDO` con un motivo **prima** di chiudere — e vale anche per una chiusura volontaria
(`CHIUSO_DALL_UTENTE`). ⚠ Con Firefox non si vedeva: il trasporto chiudeva gli stream in tempo e il
posto si liberava lo stesso. ⛔ Con **Chrome** no, e otto casi su dodici ricevevano
`GIA_ATTIVA_REMOTA`. ⭐ *Non è una cura per Chrome: è §8.1 applicata, e la pagina non se ne era
accorta perché nessuno gliel'aveva chiesto.* Aggiunta: i falliti su Chrome sono passati **da 8 a 4**.

⛔ **E il quarto, che è stato l'ultimo a cadere.** Su Chrome, dopo il caso in cui è il **server** a
chiudere il canale di controllo con un `FIN`, il posto restava occupato: da lì in poi non arrivava
più un byte che potesse liberarlo, e la pagina non poteva rimediare. ⭐ **Il difetto viveva nella
differenza fra i due motori** — su Firefox il trasporto chiudeva lo stream in tempo e il posto se ne
andava lo stesso, quindi con un motore solo non esisteva. ⭐ **Curato la sera del 10 agosto: il
server libera il posto anche quando a chiudere è lui**, ed è quello che ha chiuso i tre casi rossi
di Chrome. Da lì Firefox 140 e Chrome 151 fanno **13 su 13** tutt'e due, `CONFORME` con zero
guasti, e il giro è stato **ripetuto**.

⚠ *Fino al rilievo **R11.4** del 10 agosto questo paragrafo diceva «quella riga non c'è ancora», e
la tabella delle misure «12 su 12 su Firefox, 9 su 12 su Chrome»: il commit che ha chiuso B11 ha
toccato `README.md`, `RCP.md`, cinque file di banco e `b2-esiti.jsonl`, e **non questo documento** —
che è quello che `PIANO.md` §0.1 fa leggere per primo alla ripresa. Chi riprendeva domani
riscopriva come aperto un difetto curato, e cercava una riga che c'è.*

⚠ **E la giustificazione che si dava a quel rosso è a sua volta `[?]`**: si diceva che la pagina non
poteva mandare il congedo perché *«§4.2 le vieta di spedire ancora»*. §4.2 vieta di continuare a
spedire **sugli altri canali**, e su uno stream bidirezionale il `FIN` del server non chiude il
verso della pagina — che quindi **potrebbe** mandare il `CONGEDO` che §8.1 le impone. Le due letture
danno byte diversi, il banco ha scelto il silenzio, e `RCP.md` **non dice quale sia giusta**:
rilievo aperto **R11.22**. ⛔ **La domanda sta in `DECISIONI.md` §7.14** — le due letture, i nove
byte di `CONGEDO` contro il silenzio, e il prezzo di ciascuna — e ci è arrivata la notte del 10
agosto 2026: era nominata qui, nel `README.md` e nel rapporto, e **in nessun posto dove si
decide**. ⚠ *E `RCP.md` §4.2 adesso lo dice di suo, invece di lasciar credere a chi implementa che
stia obbedendo mentre sta scegliendo.*

⛔ **E un difetto di banco che avrebbe accusato la pagina**: il confronto *«`desktop` non cambia
niente»* metteva a paragone **tutti** i byte usciti nei due giri — compreso il `CIAO`, che porta
`banco.guasto=…kde` contro `…gnome`, due stringhe di lunghezza diversa. Il denominatore conteneva
**il byte che il banco stesso aveva cambiato**, e avrebbe detto «DIVERSI» anche su una pagina
perfetta.

---

## Le decisioni prodotte

*Rimandi, non copie (`PIANO.md` §0.3 regola 1). ⚠ La prima stesura copiava tre passaggi da `RCP.md`
§4.1-bis e da `PIANO.md`, e uno aveva perso il rimando dell'originale (R4.12).*

| | |
|---|---|
| ⭐ `DECISIONI.md` §6.4 | 🔸 **CHIUSA il 10 agosto 2026, con un banco**: **`ngtcp2`+`nghttp3`**. `lsquic` fuori sull'SNI, `quiche` fuori perché **dal C non riesce a dichiarare WebTransport**, `ngtcp2` dentro perché **due browser veri aprono la sessione**. ⚠ Il prezzo — **373 righe di codice** `[M]` ore 16:30, di cui la riscrittura del SETTINGS di nghttp3 — è scritto accanto alla scelta |
| ✅ `DECISIONI.md` §1.8 | ⭐ **Apple è un di più, non un obiettivo** — 9 agosto 2026, dall'utente: S1a esce dalla fase, e la libreria si sceglie su due motori su tre |
| ⭐ ✅ `DECISIONI.md` §1.9 | **Il ban dell'indirizzo** — 10 agosto 2026, dall'utente: **tre autenticazioni fallite, dodici ore**, con un contatore solo e senza quello per nome utente. Riscrive `RCP.md` §4.4-bis — che da 🔸 diventa ✅ — `SPECIFICHE.md` §4.2, la regola **B0.3** e il banco **B8** per intero. ⛔ Nessun tipo nuovo sul filo: `TROPPI_TENTATIVI` c'era già |
| ⏳ `DECISIONI.md` §1.7 | resta aperta solo la comodità su Safari, e nessuno la misurerà per ora |
| ✅ `DECISIONI.md` §7.14 | ⭐ **CHIUSA dall'utente l'11 agosto 2026**: dopo un `FIN` sul canale di controllo **chi lo riceve tace** — cioè la lettura che **B11** aveva scelto da sé. ⚠ *Questa riga l'ha data **aperta** per mezza giornata dopo che era stata decisa (commit `ea35b5a`), e il documento di chiusura della fase **sottostimava quel che la fase aveva prodotto**: quattro decisioni contate come domande* |
| ✅ `DECISIONI.md` §7.15 | ⭐ **CHIUSA dall'utente l'11 agosto 2026**: il congedo di §8.1 vale **se il canale è ancora utilizzabile** — vince la condizione di §3.1 punto 2, e **B5 e B11 applicavano già quella** |
| ✅ `DECISIONI.md` §7.16 | ⭐ **CHIUSA dall'utente l'11 agosto 2026**: la funzione di banco resta 🔸 — ⭐ **e fuori dal prodotto consegnato** |
| ⛔ `DECISIONI.md` §5.0-quater | **S5 ha risposto, e la risposta smentisce la ragione scritta accanto alla decisione**: la tela resta lo schermo in pixel fisici, ⛔ **ma la formula con cui il client lo legge non regge su Chrome** — `screen.width × devicePixelRatio` dà `risoluzione × zoom`. `[M]` 10 agosto 2026. ⚠ La decisione **resta 🔸** e non è ripensata: cade la formula, non l'oggetto. La cura è di `SPECIFICHE.md` §6.1-bis e **non c'è ancora** |
| ⭐ `RCP.md` §7.3 | ⭐ **CHIUSA su Mutter l'11 agosto 2026**: S7 ha misurato il segno, e il server **inverte l'asse verticale**. ⛔ Resta `[?]` per gli altri quattro desktop, e *«non chiusa»* e *«non misurata»* sono due stati diversi |
| ✅ `DECISIONI.md` §7.17 | ⭐ **CHIUSA dall'utente l'11 agosto 2026: cinque secondi.** L'ha **prodotta una misura** — B6, chiudendo R3.27, ha trovato che una sessione che **non apre mai il canale di controllo** non aveva addosso nessun tetto — e l'ha chiusa l'utente dandogliene uno. ⭐ È il giro intero: una misura apre una domanda, la domanda va dove si decide, e la decisione torna nel protocollo |
| ⏳ `RCP.md` §5.3 | S6 dice se i 5 ms del PCM reggono |
| 🔸 `RCP.md` §7.5 | ⭐ **chiusa la notte del 9 agosto**: la funzione di banco — `BANCO_MARCA` e `BANCO_ESITO` — è entrata **prima del primo byte**, sotto la clausola di §9. ⚠ La usa la fase 3; qui se ne prova solo il **rifiuto a funzione spenta** (B5). ⚠ *Era marcata ✅, cioè «deciso dall'utente» (`README.md`), e non risulta presa dall'utente: §7.5 dichiara di venire dal **rilievo R3.4** e la motivazione da `web/rapporti/S4-ritardo-disegno.md` §5.3 — non c'è né frase né voce, come invece l'hanno §1.6 e §1.8. Corretta il 10 agosto 2026, rilievo **R11.15**, e **registrata dove le decisioni stanno**: `DECISIONI.md` §1.5 riga 26.* ⛔ **E la domanda «era sua?» è aperta, e sta in `DECISIONI.md` §7.16**: si chiude con una parola, e conta perché quei due tipi hanno consumato la clausola di §9 che `RCP.md` §12 dichiara essere stata *«l'ultima occasione»* |
| ⭐ `RCP.md` §4.6 | ⭐ **CHIUSA l'11 agosto 2026**: il cronometro parte dall'**apertura del canale di controllo**, e la riga 1 è cambiata di una parola (B6, R3.27). ⛔ Con la seconda risposta che apre `DECISIONI.md` §7.17 |
| ⭐ `SPECIFICHE.md` §11.5 | ⭐ **MISURATA l'11 agosto 2026, sera**, e da fuori: `curl -skI https://192.168.0.2:7448/` sul **prodotto** risponde **200, 31 840 byte**, con `Cross-Origin-Opener-Policy: same-origin` · `Cross-Origin-Embedder-Policy: require-corp` · `Cross-Origin-Resource-Policy: same-origin` · `Cache-Control: no-store`. ⇒ l'isolamento fra origini **c'è sulla pagina che il prodotto serve**, e non è più *«un vincolo da rispettare»* letto in un documento. ⚠ È `[M]` sulle **intestazioni**, non sul comportamento del browser sotto attacco |

---

## Che cosa resta `[?]`

| | |
|---|---|
| quanti **stream al secondo** regga ciascun browser | `RCP.md` §2.3 — banco della **fase 3** |
| **Safari su HTTP/2 e TCP** | l'unico motore che ci ripiega, e il nostro server non lo parla: ⏳ **va deciso** se implementarlo o dichiarare Safari fuori dal ripiego (`STUDI.md` §web §3.2, O5) |
| ⭐ **S1a — l'eccezione su Safari e su iOS** | ✅ **resta `[?]` per decisione**, non per dimenticanza (`DECISIONI.md` §1.8). ⛔ E finché è `[?]`, *«funziona su iPhone»* **non si scrive nella documentazione del prodotto** |
| i **10 bit** fino allo schermo | tre indizi contrari, nessuno è una misura (`STUDI.md` §web §1.2 A). Verifica alla **fase 2**, e la prova finale è **guardare una sfumatura** |
| il **pezzo cieco** di S4 | 16-40 ms fra il disegno e il pixel acceso, e nessuna API JavaScript lo vede: la stima **si dichiara accanto a ogni numero** |
| ⚠ **che a rifiutare l'impronta vecchia sia il CONFRONTO dell'impronta** | il terzo giro di B3 lo dava per dimostrato, e non lo è: l'esito registrato dichiara **tre cause con lo stesso aspetto** — UDP filtrato, impronta non del certificato servito, certificato oltre i 14 giorni — e nessuno le ha distinte. ⛔ Si chiude con un controllo che le separi, non con la frase *«il browser confronta davvero»* (R11.3) |
| ⭐ **~~e la seconda metà del criterio di B2 sul terzo giro~~ — CHIUSA** | il giro è stato **rifatto la sera del 10 agosto**, su decisione dell'utente, e adesso passa pieno: la sonda manda un `CIAO` conforme e accetta `ECCOMI`, invece dell'eco di B2 che il server non fa più. ⭐ E registra **sempre** un esito, anche quando il server tace: prima restava appesa, e «il browser non è partito», «la sessione non si è aperta» e «il server non ha risposto» avevano lo stesso aspetto (R11.3) |
| ⚠ **il segno della rotella su più di un compositore** | R3.25 — ⭐ **misurato su Mutter** il 10 agosto 2026 (`+120` ⇒ il server inverte), ⛔ **e §7.3 vincola cinque desktop**: se a normalizzare è `libei` il numero vale ovunque, se normalizza il compositore KWin darà un segno diverso. Il banco è rieseguibile su KWin senza cambiare una riga |
| ~~**l'istante da cui parte il primo tetto**~~ — **CHIUSA** | R3.27, chiusa da **B6** l'11 agosto 2026: si parte dall'apertura del **canale di controllo**. ⛔ E la seconda risposta di B6 ha aperto `DECISIONI.md` §7.17 — **la sessione senza canale non ha nessun tetto** |
| ⭐ ~~**la pila PAM per un utente diverso dal proprietario del processo**~~ — **CHIUSA** | R3.26, chiusa da **B10** l'11 agosto 2026 **con una misura**, sul servizio **`remotix`**: la pila PAM verifica la parola di un utente **diverso dal proprietario del processo** ⛔ **solo se il processo è privilegiato** — da `root` riesce, da un utente normale no. Il server oggi è di root. ⚠ **Resta la domanda della fase 2**: un servizio di sistema che **lascia i privilegi** vedrebbe quella causa, e il sintomo sarebbe *«credenziali errate»* |
| ⛔ **il secondo fisso di §4.4-bis, e l'imputato adesso ha un nome** | ⭐ **Rimisurato la sera dell'11 agosto 2026** dal giro di certificazione di B8: mediane **2123,2 · 2198,1 · 1085,9 ms** — ⛔ *e quindi i «1984 ms» del `README` e i «2636 ms» qui sotto sono **due fotografie di giri diversi**, non un numero corretto due volte*. ⭐ **Quel che è cambiato non è il numero, è che l'imputato è misurato**: il server attende **+1034 ms** oltre il secondo fisso sui respinti e **+84 ms** sugli ammessi — la firma di `pam_faildelay`, cioè **PAM e non il nostro codice**. ⚠ E la `[?]` resta aperta lo stesso, perché finché quel ritardo non è costante il secondo fisso **non nasconde quel che dichiara di nascondere** |
| ⛔ **il secondo fisso di §4.4-bis contro il servizio `remotix`** | i **2636 ms** di B8 sono la mediana **di `login`**. Il prodotto ha il suo servizio PAM, quindi *«a governare i tempi è PAM»* va rimisurato prima di credergli, e il `[?]` sul secondo fisso **non lo chiude quella misura** |
| ⛔ **la formula della tela, dopo S5** | `screen.width × devicePixelRatio` non è invariante allo zoom su Chrome 151, e lo zoom di pagina **non è leggibile da JavaScript in modo portabile**. Non è una `[?]` da misurare: è una **cura da trovare**, in `SPECIFICHE.md` §6.1-bis |
| ⛔ **S5 su DeX, e S2, S3a, S6** | quattro misure che aspettano un **dispositivo**, non un'idea: il telefono Android, il DeX, una rete LTE vera. ⭐ I banchi sono pronti e girano il giorno che il ferro c'è (`web/rapporti/S-esiti-sonda.md` §4-§6) |
| ⏳ **il numero di S1b** | l'orologio è in moto dal 10 agosto 21:10 UTC: il verdetto è il **17-18 agosto 2026**. Fino ad allora S1b dice *«a N giorni l'eccezione c'è ancora»*, e il `[R]` dei sette giorni **non è confermato dal comportamento** — solo dalla contabilità di Chrome |
| ⛔⛔ ~~**il congedo di §8.1 su FIREFOX**~~ — **NON È PIÙ UNA `[?]`: È UN DIFETTO DI PRODOTTO, CON UN NOME** | ⭐ **Attribuito la sera stessa** (`banchi/01-p5-ff-*`, due giri per motore): **è della PAGINA**, e su **tutt'e due i motori**. `src/pagina.html:620` azzera `congeda_corrente` un millisecondo dopo `SESSIONE`, e il gestore di `pagehide` (riga 331) è **codice morto**. ⇒ Chiudendo la scheda, il client **non manda nessun congedo** dove §8.1 lo impone senza condizioni, e il posto se ne va per il tetto dei 30 s. ⛔ **Gecko è scagionato per misura**: la stessa `congeda()` chiamata da dentro `pagehide` consegna **tutt'e due** le strade di §3.1. ⛔ E su Chrome quel che sembrava un congedo era **lo smontaggio col codice `0x0`, che §3.1 vieta** — il banco lo contava senza leggere il motivo. ⭐⭐ **E la cura è APPLICATA E RIMISURATA la tarda serata dell'11**, `[M]` **due giri per motore**: `pagehide` scatta con la guardia **PRESENTE**, `congeda()` viene chiamata, e al server arrivano **tutt'e due** le strade di §3.1 col motivo `0x01` — su Firefox **e** su Chrome, dove la chiusura col codice `0x0` **non compare più**. Il riquadro di P5 porta i numeri. ✅ **E la dichiarazione c'è**: `DECISIONI.md` §1.12 — la cura è **fuori fase**, la fase 1 **non si riapre** e resta a **12 su 14**; alla fase 2 passa la ricertificazione di P5 |
| ⛔ **il prodotto contro i banchi** | nessun banco ha mai acceso `src/`. Finché non lo fa, *«il server fa X»* è vero **dell'innesto**, e di `src/` è **letto** |
| `[?]` **il rinnovo del credito degli stream unidirezionali** | dichiarato dal prodotto stesso; si misura alla **fase 4**, col carico che lo provoca |
| ⚠ **perché `lsquic` con l'SNI cada su ALPN** | `[M]` 10 agosto: avviso TLS **120**, `no suitable application protocol`, **dopo** che il certificato è stato trovato. ⛔ **Non indagato di proposito**: `lsquic` è fuori per un motivo che non dipende da questo, e la riga esiste perché nessuno lo riscopra credendolo nuovo |
| ⚠ **la previsione sulla bozza 02 di `lsquic`** | ⛔ **ancora aperta dopo due misure**: nemmeno con l'SNI si arriva alle impostazioni HTTP/3. Non è stata né confermata né smentita |

---

## Le cure fuori da questo documento

*Tre stonature che le revisioni hanno trovato guardando questo banco, e che stavano altrove. ⛔
Curate lo stesso giorno, o sarebbero rimaste note in un documento.*

| | |
|---|---|
| `RCP.md` §4.1-bis | diceva ancora *«`[S]` WebKit non lo implementa»*, mentre `STUDI.md` §web §3.1 e `DECISIONI.md` §1.7 erano stati corretti il 9 agosto. ⛔ **È l'arbitro**: chi lo leggeva alla lettera scriveva il ramo sbagliato **restando conforme** (R4.4) |
| `RCP.md` §7.3 | attribuiva al banco della rotella di v1 una tabella di conversione: `LEZIONI.md` §2.3 dice che è costato **una stringa di registro cercata male** (R4.15) |
| `STUDI.md` §web §3.3, §4.3, §6.3 | i **controlli negativi** che i rapporti prescrivono e che la sintesi aveva perso — è la cura che `R2` aveva ordinato *«prima di scrivere una riga di banco»* (R3.1) |
| `STUDI.md` §web §8 | la durata dell'eccezione su Chrome era `[?]` in §8 e `[R]` in §3.2, **nello stesso documento** (R4.14) |
| §00-ambiente | dichiara che l'ambiente della sonda serve *«alla fase 2, non prima»*, mentre `PIANO.md` §1.2 la mette prima di tutto nella fase 1 (R3.14) |
| `PIANO.md` §1.2 | la sonda era di quattro misure e **S4 non è eseguibile in questa fase** |

**E quelle dell'11 agosto 2026**, uscite dalla revisione avversariale della notte
(`fasi/rapporti/R12-A/B/C/D`) e dalle misure della sonda. ⛔ *Ogni riga dice **dove** la cura è
andata: quando si cura una riga si cercano tutti gli altri posti che dicevano la stessa cosa, ed è
la forma di difetto che questo progetto paga più spesso.*

| | |
|---|---|
| `RCP.md` §0-bis · §9 · §7.5 · §8.2 · `DECISIONI.md` §1.5 | ⛔ **cinque punti dicevano «oggi non esiste nessuna implementazione»**, al presente, mentre ne esistono tre: la finestra di §9 era dichiarata **aperta** dall'arbitro. Chiusa in tutti e cinque, con la data del primo byte (R12C.2) — ⭐ **e §9 adesso conta QUATTRO tipi entrati sotto la clausola, non due** (R12C.3) |
| `RCP.md` §7.3 | il segno della rotella: da `[?]` a **misurato**, con la scena, la data, i quattro controlli e quel che di ciascuno è nel registro (R12C.7) |
| `RCP.md` §4.6 | la riga 1 cambia di una parola, ⛔ **e la tabella guadagna la riga dello stato che non aveva** (R12C.11) |
| `RCP.md` §4.4-bis | il comando di sblocco **non è di RCP e non sta sul filo**: dichiarato, con la forma che non funziona e perché (R12C.4, R12.1) |
| `SPECIFICHE.md` §6.1-bis | *«va misurato quanto e su quali motori»* → **è misurato**, e la formula non regge su Chrome (R12C.8) |
| `SPECIFICHE.md` §5.5 | ⛔ prometteva dieci sessioni insieme mentre la fase 1 gira su **un filo solo con PAM sincrona**: il ripiego era dichiarato **solo in un commento di `src/main.c`** (R12C.17) |
| `DECISIONI.md` §5.0-quater | la `[?]` su cui poggiava è misurata, e va **nell'altro verso** — `LEZIONI.md` §2.3-quater preso in flagrante (R12C.8) |
| `DECISIONI.md` §7.17 | ❓ **nuova**, aperta da una misura di B6 e non da una lettura |
| `STUDI.md` §web §7 · §8 | le etichette della sonda, e S1b che non è più *«da avviare»* |

---

## ⛔ Un verdetto che la regola dell'utente ha cambiato: **R9.10**

*Scritto qui la notte del 10 agosto 2026, e non nel rapporto: ⛔ **`fasi/rapporti/R9-prodotto-rcp.md`
porta la sua data e non si riscrive**. Chi lo legge domani deve poter sapere, da qualche parte, che
una sua metà è decaduta e l'altra è peggiorata — e da quando.*

Il rilievo diceva due cose sul limitatore di `banchi/rcp/rcp.c` (*«il blocco per indirizzo non
scade mai, e raddoppia fra prove separate da settimane»*).

| | |
|---|---|
| ⭐ **la prima metà è DECADUTA** | il blocco che raddoppiava — 30 s, poi 60, poi 120, fino a 15 minuti, e `blocco_corrente` che nessuna strada riportava a zero — **descriveva la forma 🔸 che non esiste più**. `DECISIONI.md` §1.9, la sera dello stesso giorno, l'ha sostituita per intero: niente finestra che raddoppia, niente contatore per nome utente, **un ban di dodici ore con una scadenza scritta su file**. ⛔ La cura non è più *«far scadere il contatore»*, è che il ban abbia **una scadenza e un comando di sblocco** (`RCP.md` §4.4-bis) |
| ⛔ **la seconda metà è PEGGIORATA** | *«due giri identici, due verdetti diversi, e la causa non è nel banco»*: l'indirizzo del banco resta bloccato dal giro prima, e nel secondo ogni caso che passa da `fino_ad_ammesso()` riceve `TROPPI_TENTATIVI` invece di `AMMESSO`. ⛔ **Adesso quel blocco dura 12 ore invece di 15 minuti, e sta su file**: sopravvive anche al riavvio del server, quindi «si aspetta» e «si riavvia» non sono più cure. E non tocca solo B5: **B7 fallisce un tentativo, B8 ne fallisce tre**, e da lì in poi B10, B11 e chi sta sviluppando sono fuori da quella macchina per mezza giornata |

⛔ **La cura è la regola B0.3 di questo documento**, e va letta prima di lanciare qualunque banco: il
**comando di sblocco** fra un banco e l'altro — ⛔ **mai dentro il giro di B8**, o B8 non prova più
niente — e **ogni banco che lo chiama lo dichiara**, o *«il ban non è scattato»* e *«qualcuno l'ha
tolto»* hanno lo stesso aspetto.

⚠ E la parte del rilievo che **non** cambia: era, ed è, il **difetto noto n. 6** del mandato del 10
agosto — *«B11 ha dato verdetti diversi fra giri identici»* — con l'imputato fuori dal banco.

---

## Il giudizio dell'utente

*La frase vera, con la data. La fase si chiude qui, non quando questo documento è pieno.*

> ### ✅ **«Va bene, la stretta di mano funziona: fase 1 approvata.»**
>
> — l'utente, **11 agosto 2026**, dopo aver aperto `https://192.168.0.2:7448` **dal portatile**, in
> **Chrome**, digitato `prova` e la parola d'ordine, e aver letto sulla pagina *«Ammesso, sessione
> nuova, tela 1920×1080, desktop sconosciuto»*.

⭐ **La misura che chiude la fase ha una provenienza su disco**, e non è un ricordo:
`rapporti/GIUDIZIO-11-agosto.md` — la scena, le impronte, il
registro del server verbatim (`GET /` alle **12:45:44 UTC**, la stretta di mano alle
**12:48:55-12:48:56 UTC**) e quel che la pagina ha mostrato.

⛔ **E quel giro ha chiuso da solo le due cose che il `README.md` di quella mattina dichiarava non
misurate**: che **la pagina l'abbia servita il prodotto** (`GET /` era a **zero**) e che un giro
**abbia attraversato la rete** (le 19 connessioni del 10 agosto venivano **dal server stesso**). Su
**Chrome**, di cui contro questo server non c'era nessuna traccia.

⚠ **Che cosa il giudizio NON è**: un banco. Non ha un atteso confrontato da una macchina (**B0.4**),
non ha un controllo che dica *no*, non è rieseguibile senza una persona, e ⛔ **la versione esatta di
Chrome non è annotata** (regola **B0.6** mancata). È **I8**, e vale per quello che è — che è
esattamente ciò che `PIANO.md` §0.2 regola 3 chiede per chiudere una fase: *una misura giudicata
dall'utente, non un documento completo*.

⛔ **E la fase si chiude con del lavoro dichiarato aperto**, che è la forma onesta: le certificazioni
mancanti e i `[?]` qui sopra non si cancellano perché il giudizio è arrivato — si portano in fase 2
scritti, o la prossima fase comincia credendo a misure che nessuno ha fatto certificare.


---

<a id="02-primo-fotogramma"></a>

## Fase 2 — Il primo fotogramma

Aperta il **12 agosto 2026** · ⭐⭐⭐ **CHIUSA il 13 agosto 2026, sul giudizio dell'utente** — la
catena consegna, e l'utente ha guardato il proprio desktop dentro una scheda del browser.
⭐ La provenienza sta in `rapporti/GIUDIZIO-13-agosto.md`: la scena,
il registro del server verbatim, le impronte, e ⭐ **la misura fatta sui pixel dello scatto**.

> ⚠ *Questa riga diceva «il banco esiste, il prodotto no», e con lei altri tre punti del documento
> (§«Come è stata divisa», §«Che cosa è stato sviluppato», §«Il giudizio dell'utente»). Erano vere
> del **giro del 12 agosto mattina** e sono rimaste addosso al documento mentre il prodotto nasceva
> la sera stessa. ⛔ **È la causa di processo di R12-C alla terza occorrenza**: il documento è stato
> chiuso alle **08:36** del 13 agosto e il codice è arrivato fino alle **09:55** — quattro commit
> più tardi. Corretto il 13 agosto 2026 a codice fermo, revisione **R13**, rilievi 1 e 2.*

> Il modello di questo documento sta in [`PIANO.md`](PIANO.md) §0.2; le decisioni stanno in
> [`DECISIONI.md`](DECISIONI.md) e qui si **rimanda**, non si copia. ⛔ E si rimanda anche ai
> **sei rapporti di sotto-fase e ai sette del prodotto**: quel che sta lì non si ricopia qui, o le
> due copie divergono — è la lezione del 10 agosto, quando i `.md` erano stati chiusi due ore prima
> del codice.

---

### Che cosa deve produrre

Cattura da una sessione GNOME vera → codifica → filo → `VideoDecoder` → tela della pagina.
**Un'immagine ferma.**

**Che cosa vede e giudica l'utente**: il proprio desktop, dentro una scheda del browser. Fermo, ma
suo — e da qualunque dispositivo.

**Il banco**: il fotogramma decodificato confrontato con quello catturato. Non «il programma non è
crollato»: **i pixel**.

---

### Come è stata divisa, e perché

⭐ **Su richiesta dell'utente, il 12 agosto 2026**: la fase è stata tagliata in **sei sotto-fasi** e
ciascuna affidata a un agente, che ha lavorato in parallelo agli altri. Il taglio segue **gli anelli
della catena**, non delle fette arbitrarie: ogni sotto-fase possiede file suoi, una porta sua, e
consegna alle altre attraverso una sezione dichiarata — **le cuciture**.

Il mandato comune sta in `rapporti/MANDATO-12-agosto-fase2.md`.

| # | Sotto-fase | Rapporto | Banco | Porta |
|---|---|---|---|---|
| **F2.1** | La sessione GNOME headless | `rapporti/F2-1-sessione.md` | `banchi/02-sessione-*` | 7511 |
| **F2.2** | La cattura | `rapporti/F2-2-cattura.md` | `banchi/02-cattura-*` | 7512 |
| **F2.3** | La codifica HEVC in software | `rapporti/F2-3-codifica.md` | `banchi/02-codifica-*` | 7513 |
| **F2.4** | Il filo | `rapporti/F2-4-filo.md` | `banchi/02-filo-*` | 7514 |
| **F2.5** | La pagina | `rapporti/F2-5-pagina.md` | `banchi/02-pagina-*` | 7515 |
| **F2.6** | Il giudizio | `rapporti/F2-6-giudizio.md` | `banchi/02-giudizio-*` | 7516 |

⛔ **E il giro del 12 agosto MATTINA non ha scritto una riga di prodotto**, per la regola di
`PIANO.md` §0.4: il revisore interviene **appena il banco esiste**, prima che il prodotto esista,
perché *«un difetto nel prodotto lo trova un banco buono; un difetto nel banco non lo trova niente,
e avvelena ogni misura successiva perché dà fiducia»*. In quel momento `src/` era **intatto**.

⭐ **Il prodotto è arrivato la sera dello stesso giorno**, con lo stesso taglio ad anelli e un
rapporto per ciascuno — ⛔ e questa tavola non li nominava, così che chi riprendeva leggendo questo
documento **non sapeva che esistessero** (revisione **R13**, rilievo 1; è il danno di R12C.1, dove
*«chi riprendeva il lavoro leggeva quella riga e riscriveva da zero un server che esiste»*):

| # | Il prodotto dell'anello | Rapporto |
|---|---|---|
| **P2.1** | la sessione GNOME | `rapporti/P2-1-sessione.md` |
| **P2.2** | la cattura | `rapporti/P2-2-cattura.md` |
| **P2.3** | la codifica, HEVC **e** AV1 in software | `rapporti/P2-3-codifica.md` |
| **P2.4** | il canale video, dentro `rcp.c` | `rapporti/P2-4-filo.md` |
| **P2.5** | la pagina che dipinge il fotogramma | `rapporti/P2-5-pagina.md` |
| **P2.6** | il montaggio: i cinque anelli messi insieme | `rapporti/P2-6-montaggio.md` |
| **P2.7** | il figlio per utente (`DECISIONI.md` §1.10-bis) | `rapporti/P2-7-figlio.md` |

---

### Il banco

⭐ **Sei banchi, e tutti e sei certificati nello stesso giro in cui sono nati** — la regola scritta
l'11 agosto 2026 (*chi scrive un banco lo certifica nello stesso giro, o il conto non cala mai*)
è stata rispettata sei volte su sei.

| | La certificazione, `[M]` 12 agosto 2026 |
|---|---|
| **F2.1** | sul ferro `sano 0 → guasto 1 (zero monitor) → risanato 0`, girato **due volte**, sessione fermata e riavviata sei volte · sulle scene registrate **9 su 9**, otto guasti ciascuno nel suo punto |
| **F2.2** | `sano 0 → quattro guasti 1 → risanato 0`, con la marca **pretesa** *e* quella **vietata**: il grigio deve dare *«scena non riconosciuta»* e ⛔ **mai** *«fotogramma nero»*, o il giudice sbaglia la diagnosi peggiore proprio dove serve |
| **F2.3** | **30 su 30** verde su CHUWI **e** dentro il contenitore di NIC-OS · sano → guasto → risanato su **due** organi, cinque esecuzioni, marca verificata **assente** nel giro sano |
| **F2.4** | **6 pezzi su 6** · il giudice **27 su 27** come previsto · `sano 0 → guasto 4/1/2/3 → risanato 0`, marca vista nel guasto e mai nel sano |
| **F2.5** | sano → **cinque** guasti → risanato, uscita 0. ⚠ Due dei cinque sono **nati certificando**: erano stati innestati e non facevano virare niente |
| **F2.6** | `sano 0 → dodici guasti su dodici con la marca giusta → risanato 0` |

#### ⭐⭐ E la cosa che dice se il giro è valso la pena: **nove difetti trovati dentro i banchi, prima che il prodotto esista**

⛔ Non nel prodotto — **nei banchi appena scritti**, e tutti trovati *girando*, non rileggendo:

- **F2.2** — ⛔ **il suo banco è uscito VERDE col difetto vivo**, al primo giro: zero fotogrammi di
  regime, riga gialla, verdetto verde. La forma **E8**. Causa: la sessione aveva già `Meta-0`, il
  banco montava `Meta-1`, e la scena finiva sul primo. ⭐ Curato in tre punti, e **le due righe
  sbagliate restano nel registro** con accanto la nota che dice perché non valgono.
- **F2.6** — quattro: un controllo che correlava i canali su tutta l'immagine (R, G, B sono correlati
  a 0,978 ⇒ **rosso su catena sana**); uno che sottraeva 8 bit da 16 (−3,18 dB su catena perfetta);
  uno che innestava il guasto sull'imputato e **ri-scambiando i piani li rimetteva a posto**; e uno
  che aggregava `None` con `is not False` e **promuoveva** un giro senza riferimento.
- **F2.4** — due: il confronto della regola citata dava **rosso su quattro giudizi esatti**, e le
  marche di due guasti erano nomi che compaiono **anche nel giro sano**.
- **F2.5** — due, quelli «nati certificando».

⇒ Ciascuno di questi, se il prodotto fosse stato scritto prima, sarebbe diventato **un'accusa al
prodotto**. La fase 1 ne ha pagati tre di quel tipo.

---

### Che cosa è stato sviluppato

**Il 12 agosto mattina, niente prodotto** — e non era un ritardo, era l'ordine (`PIANO.md` §0.4).
Quel che esisteva era il banco, e con esso la **forma** che il prodotto avrebbe dovuto avere: le
decisioni qui sotto erano vincoli per chi avrebbe scritto il codice.

⭐ **Il prodotto è stato scritto la sera del 12 e la mattina del 13**, e sta in `src/` — la sessione,
la cattura, le due codifiche, il canale video dentro `rcp.c`, la pagina che dipinge, il montaggio e
il figlio per utente. I sette rapporti sono nella tavola `P2.1` … `P2.7` qui sopra, e **quel che sta
lì non si ricopia qui**.

---

### Le misure

#### ⛔ 1. Il terreno era rotto da due giorni, e nessuno lo sapeva

`[M]` 12 agosto: la sessione GNOME viva su NIC-OS **dal 10 agosto** girava `--headless --no-x11`
**senza** `--virtual-monitor`. `GetCurrentState` → **zero monitor**, con `IsSessionRunning` true,
cinquanta nomi sul bus, Nautilus e Terminale accesi.

⇒ **Il guasto M9 di `STUDI.md` §gnome §13 non è stato innestato: era già addosso alla macchina.** Una
cattura puntata lì avrebbe misurato **zero fotogrammi** cercandoli dentro PipeWire, e l'imputato
sarebbe stata la cattura.

- ⚠ **La sessione nera non è solo nera: è fragile.** `Shell.Screenshot` su zero monitor fa tentare a
  Mutter una texture 0×0; con `OnFailure=gnome-session-shutdown.target` **cade tutta la sessione**.
  `[M]`, provato involontariamente e dichiarato.
- ⛔ **La cura di oggi non sopravvive a un riavvio**: il drop-in vive in `$XDG_RUNTIME_DIR`. Si
  rimette con `bash banchi/02-sessione-lancia.sh sano`.
- ⛔ **E la cura vera è di prodotto**: `fondamenta/remotix-c/src/sessione.c:671` è
  `if (tipo == COMPOSITORE_KWIN && …)` — sul ramo GNOME `larghezza` e `altezza` **entrano nella
  funzione e si perdono**. Che il monitor virtuale stia in `provision-server.sh` invece che nel
  programma è l'invariante **I7** violato.

#### ⛔ 2. La sorgente dà OTTO bit — il desiderato dei 10 bit non passa di qui

`[M]` 12 agosto: **Mutter consegna solo BGRx/BGRA**, cioè 8 bit per canale. 1920×1080, stride 7680
**letto dal manifesto** e non calcolato, 8 294 400 byte, range non dichiarato da Mutter ma **misurato
0-255**, e **nessuna matrice** — i pixel sono RGB.

Il conto che lo dimostra, fatto **sulla sfumatura** della scena (⚠ sulle barre piatte i livelli sono
una ventina per costruzione, e direbbe «8 bit» su qualunque cosa): **255/256/255 livelli distinti,
multipli di 4 a 0,259/0,259/0,249**.

⇒ ⛔ **Main10 da questa strada significa otto bit promossi a dieci**, e l'etichetta continuerebbe a
dire *«10 bit»* per tutta la catena. Il desiderato di `SPECIFICHE.md` §3.1 **non è raggiungibile in
fase 2 per via MemFd**, e la `[?]` viva si sposta su **DMA-BUF**, che F2.2 dichiara **non provata**.

⭐ E la previsione era stata scritta prima: F2.3 aveva messo a verbale *«se la cattura dà 8 bit, tutta
la catena resta verde e l'etichetta dice Main10 lo stesso»* come rischio da misurare. F2.2 ha
risposto: **è una certezza, e l'imputato sono io.**

#### ⛔⛔ 3. HEVC non arriva al pixel su Firefox, e su Chrome esiste solo con la GPU

`[M]` 12 agosto, F2.5 — **e la scena decide una delle due risposte**:

| | schermo vero `:10` (GPU) | Xvfb (senza GPU) |
|---|---|---|
| **Chrome 151** | ⭐ **HEVC arriva al pixel**, 8 celle su 8, Main **e** Main10, Annex-B **e** hvcC | ⛔ **zero**: ogni stringa HEVC rifiutata |
| **Firefox 140 ESR** | ⛔ **zero**, `NotSupportedError` | ⛔ **zero**, identico |

⭐ **VP9 dipinge 8 su 8 in tutti e quattro i casi**: il «no» è **di HEVC**, non del banco — il
controllo positivo c'era.

**La causa è misurata, non dedotta**: con `prefer-software` Chrome dice `Unsupported`, con
`prefer-hardware` dipinge ⇒ `[M]` **Chrome su Linux non ha un decodificatore HEVC software**. HEVC
esiste **solo via VA-API**, e senza GPU sparisce.

> ⭐ **Verificato una seconda volta, su un secondo strumento e sul browser vero dell'utente** — `[M]`
> 12 agosto, ricognizione fatta guidando il Chrome di CHUWI da fuori, con i due controlli:
>
> ```
> hev1.1.6.L93.B0 (Main)     no-preference SI · prefer-hardware SI · prefer-software  no
> hvc1.1.6.L93.B0 (Main)     no-preference SI · prefer-hardware SI · prefer-software  no
> hev1.2.4.L93.B0 (Main10)   no-preference SI · prefer-hardware SI · prefer-software  no
> vp09.00.10.08  (positivo)  SI · SI · SI
> avc1.42E01E    (positivo)  SI · SI · SI
> pippo.00.00    (negativo)  no · no · no
> ```
>
> ⇒ La firma è **esattamente** quella descritta da F2.5: HEVC cade **solo** su `prefer-software`,
> mentre VP9 e H.264 reggono tutte e tre le strade e il codec inventato è rifiutato da tutte e tre.
> ⚠ **E questa non è un banco**: è una ricognizione a mano, non lascia traccia su disco e non si
> rifà domani. Vale come **secondo testimone** della causa, non come misura della fase — e
> `isConfigSupported` resta la forma **E1** (*necessario scambiato per sufficiente*): dice che la
> configurazione è accettata, **non** che il pixel arriva. Quello lo dice il banco di F2.5.

#### ⭐⭐ 4. E su Firefox tre testimoni concordi dicono il falso

`[M]`: `mediaCapabilities` risponde `supported / smooth / powerEfficient: true` e `canPlayType`
risponde *«probably»* per **tutte e sette** le stringhe HEVC — mentre `isConfigSupported` dice
**false** e il pixel **non arriva**.

⇒ ⛔ **Una pagina che scegliesse il codec da lì non dipingerebbe niente**, e nessuno dei tre testimoni
l'avrebbe avvertita. È una trappola di prodotto, non di banco.

#### 5. Le altre misure, in breve

| | |
|---|---|
| ⭐ **il prefisso non conta** | `hev1.` **e** `hvc1.` vanno tutti e due in Annex-B puro `[M]`: Chromium decide dalla presenza della `description`, non dal prefisso. ⇒ la `[?]` che F2.3 aveva lasciato aperta **è chiusa** |
| ⛔ **il livello non lo controlla il browser** | Chrome accetta `L30` su un flusso di livello 3.0 e **dipinge 8 su 8** `[M]`. L'atteso del banco è stato **smentito**, col guasto verificato in vigore ⇒ **il controllo del livello deve stare dal lato server** |
| ⛔ **`ffmpeg` non rifiuta un flusso corrotto: lo conceala** | due storpiature su tre escono con stato **0** `[M]` ⇒ un giudizio sulla decodifica **non si prende mai dallo stato d'uscita**: si prende sui pixel |
| ⛔ **il codec non è un rivelatore di corruzione** | un byte girato nell'intestazione di uno slice ha lasciato il fotogramma **identico bit per bit** `[M]` — numero da avere in mano se qualcuno propone scorciatoie attorno alle garanzie di QUIC |
| ⚠ **x265 sceglie da sé** | `bframes=4` e `open-gop` di default, che nessuno ha chiesto: costano **un fotogramma di ritardo** contro un tetto di 50 ms. v1 li vietava a mano ⇒ si decide, non si eredita |
| ⭐ **`cattura.h` e `STUDI.md` §gnome §8.1 si contraddicevano** | sul buffer riciclato. Misurato: danno **parziale** e le sette bande **intere** ⇒ ha ragione `STUDI.md` §gnome, il commento nel codice è vecchio. ⛔ Se avesse avuto ragione `cattura.h`, la fase 2 avrebbe consegnato **mezzo desktop senza un errore** |
| ⛔ **la `[?]` del piano sull'ordine di `libei` è contraddetta** | `[M]`, riprodotta due volte: un client Wayland tenuto vivo *attraverso* la nascita del puntatore **riceve** `capabilities(0)` → `capabilities(1)`. La spiegazione *«non si iscrive mai»* **non regge**, e la caccia si sposta dal compositore al client. ⭐ E la regola vera è più stretta del piano: `ensure_virtual_device()` sta nei gestori di `NotifyPointerMotion*`, **non** in `Start()` — il puntatore nasce al **primo movimento iniettato**, la tastiera al **primo tasto** `[R]` |
| ⛔ **E2 preso sul campo** | sul server ci sono **due** monitor virtuali, `Meta-0`/`MetaVirtualMonitor` e `Meta-1`/`Virtual remote monitor`, **entrambi 1920×1080@60**: li distingue **il nome del prodotto**, non la misura. Sceglierne uno «per misura» o «per indice» è la forma E2 |

---

### Le decisioni prodotte

| | La decisione | Perché |
|---|---|---|
| ⭐ **D1 — Annex-B puro, e NESSUNA `description`** | il flusso sul filo è `[00 00 00 01] VPS · SPS · PPS · SEI · IDR` | quattro ragioni **lette**: è quel che `libavcodec` già produce (l'hvcC lo fa il muxer MP4, e sarebbe codice nostro da mantenere — `CODER.md` §4.1); in Chromium l'hvcC costa **un'allocazione e una copia per fotogramma** perché converte comunque ad Annex-B `[R]`; l'hvcC ha una trappola documentata sul profile-tier-level che fa **rifiutare** `isConfigSupported()`; tre progetti su tre fanno così. ⚠ **Il prezzo dichiarato**: WebKit fa la conversione inversa ⇒ si paga su Safari |
| ⭐ **D2 — il primo fotogramma è sempre chiave, coi parameter set dentro** | e ogni chiave si decodifica da sola | oggi `RCP.md` lascia **conforme** un delta in apertura, e il client **non ha modo di accorgersene**: nessun buco, nessun errore dal decodificatore ⇒ la fase 2 mostrerebbe spazzatura **senza che nessuno abbia torto** |
| ⭐ **D3 — il metro della fase è a due piani** | *piano 1*: `pagina ⟷ riferimento ffmpeg`, perdita ammessa **zero**, soglia **PSNR-Y ≥ 45 dB** — perché la decodifica HEVC è **normativa** · *piano 2*: `Δ = PSNR(pagina, cattura) − PSNR(riferimento, cattura) ≥ −0,5 dB` | il piano 2 è una **differenza**: il QP scelto da F2.3 si cancella, e **la soglia non invecchia** quando la codifica cambia. ⭐ E il riferimento `ffmpeg` è **il secondo lettore** che `PIANO.md` §0.4 dichiara mancante |
| ⛔ **D4 — il controllo del livello sta dal lato server** | non dal lato pagina | misurato: Chrome accetta un livello sbagliato e dipinge lo stesso |
| ⛔ **D5 — `codificatore.c` si riscrive, non si «riporta»** | ne sopravvive **la forma**, non le righe | 889 righe (la cifra del piano è giusta), ma **77 nominano H.264/AVC**, **47 nominano RDP/FreeRDP**, e *HEVC*, *265*, *10 bit* compaiono **zero volte**: è un codificatore H.264 AVC420 per RDP, quattro candidati tutti `h264_*`, tutti **NV12 a 8 bit**. Sopravvivono il giro dei tentativi, il divieto di ripiego silenzioso, il conto dei tempi, il divieto di `GLOBAL_HEADER` |

#### ⚠ E una correzione a una misura della fase 1

⛔ **La prova dei 10 bit «contando le bande»** — sonda **S2**, `web/` §3.7 punto 2 — **non
sopravvive alla codifica con perdita**: `[M]` rapporto **4,13** prima, **1,31** dopo QP 20.
⭐ Sostituita dai **due bit bassi del piano Y sulle zone sfumate**, che convergono con la misura
indipendente di F2.3 (**0,25** su catena sana contro **1,000** su un flusso troncato a 8 bit).
⚠ E la firma dei «multipli di 4» **non sopravvive alla conversione RGB→YUV**: i bit veri si misurano
**alla sorgente**, o non si misurano.

---

### ⛔ Che cosa NON ha funzionato

- ⛔ **La sessione del server è caduta**, chiamando `Shell.Screenshot` su zero monitor. Rimessa in
  due minuti; **7448 e 7501 verificate intatte** prima e dopo (girano nel contenitore). ⭐ Da lì è
  uscita la scoperta che la sessione nera è **fragile**, che vale più del disturbo.
- ⛔ **Un banco verde col difetto vivo** (F2.2, sopra). La forma E8, dentro un banco appena scritto.
- ⛔ **Nove difetti di banco** trovati girando (elenco sopra).
- ⚠ **In Chrome headless `VideoEncoder.flush()` non ritorna.** Aggirato con una finestra vera,
  ⛔ **non capito**: resta `[?]`, e chi lo riusa altrove deve saperlo.
- ⛔⛔ **E un difetto del COORDINAMENTO, che è mio.** La regola *«ogni agente possiede file suoi, e
  non tocca quelli degli altri»* — scritta per impedire che sei agenti si sovrascrivessero — ha
  prodotto questo: l'agente degli arbitri ha **fatto e riferito cinque ricertificazioni**, e
  **nessuna ha scritto una riga nel registro**, perché il registro apparteneva a un altro agente.
  ⇒ Per ore il conto ha detto *«B9 scaduta»* mentre B9 era stato rigirato **quattro volte**.
  ⚠ È la stessa forma che questa giornata ha inseguito tutto il tempo — ***«fatto» e «scritto dove
  qualcuno lo legge» sono due cose diverse*** — applicata al registro invece che al filo.
  ⭐ **La regola che ne esce**: *chi è autorizzato a certificare deve essere autorizzato a scrivere
  la riga della certificazione*. Un permesso a metà produce lavoro che non esiste per nessuno.
- ⚠ **`misura-cattura.c` stampa nella riga di esito la misura CHIESTA, non quella negoziata** — la
  voce 12-bis fu curata in `misura-wlroots` e **non lì**. Rilievo `[R]` **lasciato aperto e non
  toccato**: non è di questa fase, ed è lo strumento che certifica gli altri banchi.

---

### Che cosa resta `[?]`

| | |
|---|---|
| ⛔ **i 10 bit veri** | ⇒ **`DECISIONI.md` §2.3-ter, e non è più una `[?]`**: non escono da Mutter per **nessuna** strada — né MemFd né DMA-BUF, e i formati a 10 bit chiesti **per nome** danno `no more input formats` su tutt'e due, col controllo positivo accanto. ⚠ *Questa riga diceva «restano possibili solo per via DMA-BUF, non provata»: era una **copia invecchiata di una decisione**, cioè proprio quel che il riquadro in testa promette di non fare, e teneva aperta una speranza che una misura aveva chiuso (R13.5b)* |
| ⚠ **il telefono, e la `[?]` adesso è più stretta** | `[M]` **13 agosto 2026**, telefono vero — **SM-S916B**, Chrome 151.0.7922.108, Adreno 740: **4 sequenze su 4 dipinte**, HEVC Main10 **e** AV1 10 bit. ⛔ **Ma `copyTo` dà `format` `RGBA` e 4 byte per pixel**: al capo del dispositivo i dieci bit sono **otto promossi**, come alla sorgente. ⛔ **E resta aperto l'hardware**: senza cavo dati non si legge `Created MediaCodec <nome>`, quindi *«lo decodifica il silicio o la CPU?»* non ha risposta — e il criterio A/B esce `valido: false`, perché misura **spesa fissa**. ⚠ *Questa riga diceva «nessun numero prodotto, e nessuno dedotto», e i numeri stanno in `banchi/02-giudizio-sonda.jsonl` dalle 07:53 del 13 (R13.5a)* |
| ⛔ **il buffer della scheda sbagliata** | il banco della cattura **non lo vedrebbe**, e il suo verde **non lo assolve**. La macchina ha due GPU |
| ✅ **che un fotogramma arrivi davvero sul filo** | ⭐ **chiusa il 13 agosto**: l'utente l'ha guardato, e il registro del server lo scrive — `fotogramma 1 SPEDITO: CHIAVE 0x0301, codec 2, 1920x1080, 9746 byte, FIN` |
| ⛔ **M5 — lo scarto di crominanza fra due decodificatori** | 0,9791 contro un limite di 0,98: è **l'unico rosso rimasto su catena sana** — M0 e M1 erano rossi ai giri delle 09:19-09:20, prima della cura del riscalamento. ⛔ **Non si riproduce sulla mira**, e **la soglia non è stata allargata**: il rosso non è stato curato, **è sparito quando è cambiata la scena** |
| ⛔ **P15** | `RCP.md` §7.1, il secondo di grazia sulle coordinate: **l'ultimo posto della fase dove un orologio decide**. Sta per esteso in `rapporti/F2-4-filo.md` |
| ⛔⛔ **«due utenti con due sessioni vere, ciascuno vede LA PROPRIA»** | ⛔ **non lo copre nessun banco**, ed è il buco più grande della fase. `[M]` 13 agosto: il caso `senza-palco` di `02-figlio-prova.py` prova **la metà negativa** — `prova` (uid 1001, tutti e quattro i campi chiesti al nucleo) **non** vede il desktop di `nicfio`, e il cliente RCP indipendente conta **zero** fotogrammi dove il 12 agosto ne contava uno conforme. ⛔ **Ma la metà positiva no**: su quella macchina `prova` non ha mai fatto login — niente `/run/user/1001`, niente bus, niente palco — quindi **un prodotto che non consegnasse niente a nessuno passerebbe allo stesso modo**. La metà positiva regge oggi **solo per uid 1000**. ⚠ Guardati e scartati: `01-b10-secondo-utente.py`, `attrezzi-prova2.sh`, `02-pam-i3.py --caso secondo` si fermano tutti **all'autenticazione**, non al vedere |
| ⚠ **`02-figlio-accendi.sh:165` conta i figli di tutti** | `pgrep -f -- "--figlio-interno" \| wc -l` non guarda **di chi** sono: allo spegnimento ha accusato due orfani che erano figli vivi di padri vivi (la 7693 di un altro banco e ⛔ **la 7561 dell'utente**). È la stessa forma che il file **vieta trenta righe più su** per l'azione `stato`. ⚠ Non cura, non ferma nessuno (`spegni` esce 0 lo stesso) — si accende solo quando due banchi girano in parallelo, e il 12 agosto infatti taceva. ⇒ ✅ **Curato in fase 3** (13 agosto 2026) — ⛔ **`[R]`, non eseguito**: la cura è letta nel codice e **non è stata girata**, quindi non porta la marca `[M]` |
| ⛔ **la risoluzione del desktop, `1920×1080`** | ⛔ **ereditata dalla scena di un banco, senza decisione né misura** — `grep 1920 DECISIONI.md` non trova nessuna decisione che la fissi, e in v1 era **2560×1080**. ⚠ È la tela che l'utente vedrà: `LEZIONI.md` §2.3-quater la vuole scritta come **provvisoria**, ed è quel che questa riga fa. ⇒ ✅ **CHIUSA il 13 agosto 2026, e decisa dall'utente**: **1920×1080 resta**, con il prezzo misurato accanto (tela dipinta all'**86 %**, **912 px di nero**) e la ragione di metodo scritta — `DECISIONI.md` §5.0-quinquies. ⛔ E le bande nere **non sono la risoluzione**: sono la forma della finestra |
| ⚠ **`VideoEncoder.flush()` in headless** | aggirato, non capito |
| ⚠ **le soglie M1b e M3 del metro** | **calcolate**, non tarate sul campo |
| ⚠ **Safari, e Chrome per Android/DeX** | manca il dispositivo |
| ⚠ **Firefox con `media.hevc.enabled`** | **non provato di proposito**: si misura il browser che l'utente ha, non quello che potrebbe configurare |

---

### Che cosa aspetta l'utente

#### ✅ 1. ~~Una decisione: HEVC esclude Firefox~~ — **decisa e chiusa il 12 agosto**

Il progetto promette *«nessun client da installare — basta un browser moderno»*, e con HEVC quella
frase valeva per **Chrome con una GPU che porta VA-API**: Firefox non dipinge, e Chrome senza GPU
nemmeno. ⛔ La difesa dei tre motori indipendenti — quella che `DECISIONI.md` §1.6 comprava al posto
dell'arbitro perduto — **su HEVC non c'era**.

✅ **L'utente ha deciso: `DECISIONI.md` §1.13** — HEVC **con un ripiego negoziato**, non un requisito
dichiarato, perché `CODER.md` §4.2 impone che ogni dipendenza mancante abbia un ripiego e che il
ripiego **si dichiari**.

🔸 **E il secondo codec è AV1**, chiuso lo stesso giorno **su una misura** e non su una preferenza:
`[M]` **quattro caselle su quattro** — i due motori, con GPU e senza — a **8 e a 10 bit**, e ⛔ **con
`prefer-software`**, cioè senza dipendere dalla GPU. ⭐ AV1 riempie **esattamente** le tre caselle che
HEVC lascia vuote, e ⭐⭐ i 10 bit su Chrome diventano per la prima volta **osservabili**
(`VideoFrame.format` = `I420P10`, massimo del luma **870** — impossibile a 8 bit).

⭐ **E non costa una riga di protocollo**: `av1` era già fra i valori ammessi di `RCP.md` §4.3 e aveva
già `codec = 2` in §6.2 ⇒ **§9 non viene sfiorata**. ⛔ *VP9, che pure era misurato funzionare,
sarebbe costato **RCP/2**: in §4.3 compare come l'esempio di valore che RCP/1 deve **ignorare**.*

⛔ **L'ordine di preferenza non si rovescia**: resta `hevc,av1`. HEVC è ancora il primo, perché è
quello che il telefono decodifica in hardware — ed è la domanda **S2**, ancora aperta.

#### ⚖️ 2. La sonda del telefono, che non si fa da soli

*Un telefono **Android** con **Chrome ≥ 108** — non il portatile — sulla stessa WiFi, con un cavo
USB e il debug acceso per `chrome://inspect`. Si apre l'indirizzo stampato da
`bash banchi/02-giudizio-telefono.sh serve`, si accetta l'avviso del certificato **una volta**, si
premono i bottoni 1 e 2 tenendo schermo acceso e scheda in primo piano: **~10 minuti**, più 10 di
fila per il decadimento quando le sequenze di F2.3 ci sono.*

⛔ **Non gli si chiede se «si vede bene»: la sonda produce numeri.**

#### ⛔ 3. E un debito della fase 1 che questa fase NON può scavalcare

⚠ *Il `README.md` elenca fra «quel che aspetta l'utente» i due ripieghi — il filo unico e il tetto
delle sessioni. **Quella riga è scaduta**: tutt'e due sono state decise dall'utente la sera dell'11
agosto, e stanno in `DECISIONI.md` §1.10 e §1.11. Corretto il 12 agosto 2026.*

⛔ **E `DECISIONI.md` §1.10 impone una cosa a questa fase**: la verifica PAM esce dal filo unico
**prima che la fase 2 si apra**, con un **processo aiutante** e non con un filo — perché PAM non è
affidabilmente rientrante.

La ragione è scritta lì, ed è del video: *«finché non c'è video il sintomo è «l'ultimo dei dieci
aspetta dieci secondi», sgradevole e circoscritto; dalla fase 2 in poi lo schermo di **tutti** quelli
collegati si pianta per uno o due secondi ogni volta che **qualcun altro** entra — e chi lo vedrà lo
attribuirà al **video**»*. `[M]` da B8: **da 1,0 a 2,2 secondi** per tentativo, e il ritardo lo mette
`pam_faildelay`, non il nostro codice.

⇒ ⭐ **Il banco di questa fase poteva nascere prima della cura — il prodotto no.** Questo giro ha
scritto solo banchi, quindi il debito non è stato violato; ⛔ **ma la prima riga di prodotto della
fase 2 viene dopo quella cura**, o si misura il video con dentro un difetto che si attribuirà al
video.

#### ⏳ 4. Il tetto delle sessioni resta 16, e il prezzo è dichiarato

`DECISIONI.md` §1.11: non si cambia fino alla fase 3, perché *«il limite vero non è un conteggio: è
un budget di pixel al secondo, e lo pone il codificatore»*. ⚠ Per due fasi **il codice dice 16 e la
specifica dice 10**.

---

---

### ⭐ LA SERA DEL 12 AGOSTO — il cancello si apre, e l'arbitro si corregge sei volte

*Su richiesta dell'utente — «fai una lista dei bug, assegna un agente a ciascuno, e arriva al
completamento della fase 2» — sono stati aperti **dodici difetti** (`rapporti/DIFETTI-12-agosto.md`)
e affidati a un agente ciascuno, in ondate che non si pestassero i piedi.*

#### ⭐⭐ Il cancello della fase 2 è aperto: `DECISIONI.md` §1.10 è applicata e misurata

La verifica PAM esce dal filo unico, **con un processo aiutante** — tre piani: il server scrive su un
`socketpair` SEQPACKET e torna al `poll`; uno **smistatore** che non chiama mai PAM legge e forca; un
**nipote** fa **una sola** transazione PAM e muore. ⇒ La rientranza di PAM non è *«gestita»*: **non è
in gioco**.

| | `[M]` 12 agosto 2026, cinque giri per lato |
|---|---|
| ⭐⭐ **chi NON si autentica** | picco **2259 → 3 ms** |
| ⭐ **la stretta di mano di chi arriva in quel momento** | **2262 → 10 ms** |
| ⚠ **chi si autentica** | 2260 → 1844 ms, cioè **invariato** — e deve restarlo: quel tempo lo mette PAM |

⛔ **E il fallimento è un no, non un forse** (I3): il `true` nasce in **un punto solo del programma**,
e sette strade portano a un no. Provato ammazzando l'aiutante con `SIGKILL` e presentando la parola
**giusta** → `RESPINTO` in 1001 ms, col controllo positivo accanto.

⭐ **E il filo NON è cambiato**: B3 `0→2→0` e B5 `0→1→0` danno gli **stessi identici numeri** di
prima della cura. L'ipotesi di chi l'ha scritta è diventata una misura.

#### ⛔ Il prodotto sul server non era il prodotto che avevamo scritto

`[M]`: **10 file su 24 diversi**, e i due che mancavano **del tutto** erano i due nuovi
(`aiutante.c`, `aiutante.h`); il binario girava dall'11 agosto con `exe` marcato `(deleted)`.

⭐ **E la cura non è la copia: è l'attrezzo che mancava** — `banchi/attrezzi-allinea-prodotto.sh`,
che **enumera l'albero intero** invece di un elenco scritto a mano. È esattamente la lezione del
difetto: *i due file che mancavano sono quelli che un elenco a mano non avrebbe mai avuto*. E non si
ferma ai sorgenti: ⛔ **sorgenti allineati e binario nuovo non bastano finché il processo vivo è
l'altro**.

#### ⛔⛔ E l'arbitro si è corretto sei volte in una sera

Le sette righe di F2.4 sono entrate in `RCP.md`; ⛔ **due erano sbagliate**, e le due cure che le
sistemavano ne hanno generate altre quattro. La successione **P8 → P11 → P13 → P14** e la lezione che
ne esce stanno in **`LEZIONI.md` §1.13**, ed è la cosa più riusabile prodotta oggi:

> ⭐ *Una tolleranza si scrive sulla **grandezza vera del fenomeno**, o si sposta di un passo a ogni
> rilettura.* La risposta esatta stava dentro i 28 byte dell'intestazione da tre giorni — il campo
> `numero` — e le prime tre stesure hanno usato una **grandezza sostitutiva**: una misura, un tempo,
> un evento.

⚠ **E chi le ha trovate, tutte e quattro: non chi rileggeva il documento, ma chi doveva far
rispettare la regola** scrivendo l'arbitro che la giudica.

#### Il conto dei banchi, la sera del 12 agosto

```
banchi nel catalogo: 15   (P5R e' entrato: il guasto che toglie il RITIRO, non il valore)
13  certificati e valgono oggi
 0  non riverificabili        ⭐ la riga di P5R adesso porta le impronte
```

⚠ **E il numero è sceso e risalito sei volte in una sera**, sempre per la stessa ragione dichiarata:
curare il prodotto o l'arbitro **fa scadere le certificazioni che li guardavano**. ⛔ *«Scaduta» non
è «fallita»*, e non è nemmeno «pulita».

#### ⭐ Gli attrezzi nuovi, e servono al prossimo giro

- **`attrezzi-allinea-prodotto.sh`** — quel che il `README` dichiarava mancante da ieri.
- **`02-sessione-guardia.sh`** — si mette **davanti** a una misura e fa le **due domande separate**:
  *«è viva?»* e *«ha un monitor?»*. Con tre bande d'uscita, così un **rifiuto** non si confonde con
  un fallimento del comando.
- ⭐⭐ **il controllo positivo dell'àncora** (in `01-b8-cronometro.py`, riusato in
  `01-b10-secondo-utente.py`) — allunga la riga di registro nei modi già successi e pretende che
  l'esito **non cambi**. ⛔ Nato perché **un'àncora fragile passa tutti i guasti**: rompersi *fa*
  diventare rossi, quindi nessuno dei quindici guasti la smascherava.
- **`01-b12-lancia.sh`** prende `B12_BERSAGLIO=innesto|prodotto`, e ⛔ **la scena finisce in ogni
  riga del registro**: chi non la dichiara ottiene *«non dichiarata»*, mai «innesto».

---

### ⭐⭐⭐ L'UTENTE HA VISTO IL PROPRIO DESKTOP — 13 agosto 2026, mattina

*Non è il giudizio di fase: è il fatto che la catena consegna. Si scrive qui perché è la prima volta
che un essere umano guarda l'uscita di questo prodotto, e perché fin qui tutto quel che ne sapevamo
erano decibel.*

> **«È lo sfondo GNOME, è OK.»** — l'utente, davanti a `https://192.168.0.2:7561/`, entrato come sé
> stesso.

⭐ Cattura → codifica → filo → `VideoDecoder` → pixel sullo schermo di una persona, con in mezzo un
protocollo scritto da zero. Il registro del server, dalla stessa sessione:

```
il client dichiara video.misura_massima=3840x2160   ← MISURATA decodificando, non dedotta dallo schermo
sessione aperta utente=nicfio  tela=1920x1080  vista=2559x922
fotogramma 1 SPEDITO: CHIAVE 0x0301, codec 2, 1920x1080, 9746 byte, FIN — spediti 1, abbandonati 0
```

⚠ **E si scrive che cosa questo NON è**: non è il giudizio della fase, e la fase resta aperta.

⚠ *Questo riquadro, chiuso alle **08:36**, proseguiva così: «L'immagine è **piccola** — la pagina non
riscala alla vista, che §6.1 le impone — e il metro a pixel sulla catena vera non è stato girato».
⛔ **Tutt'e due le metà sono morte nell'ora e venti che è seguita**, e il documento è rimasto indietro
di quattro commit (R13.2):*

- ⭐ *il riscalamento è **in servizio** dalle **08:56** (`dc2f6a9`): due grandezze si chiamavano
  tutt'e due «larghezza della tela». E il rimando era **rotto** — `RCP.md` §6.1 è «Sui canali
  affidabili» e non nomina né vista né riscalamento; la sezione giusta è **`SPECIFICHE.md` §6.1**,
  ed è la terza volta in due fasi che un `§x.y` manda altrove (R13.8);*
- ⭐ *il metro a pixel **ha girato sulla catena vera** alle **09:50** — e quel che dice, per intero e
  senza arrotondarlo, sta nella sezione qui sotto.*

#### ⛔ E i tre difetti che l'utente ha trovato in una mattina, che 518 file di banco non avevano preso

| | Che cosa ha visto | Perché il banco non lo vedeva |
|---|---|---|
| **1** | ⛔ entrando come `prova` vedeva il desktop di **`nicfio`** | il deposito dei fotogrammi era **di processo**, non di sessione — e nessun banco entrava con **due** utenti diversi sullo stesso server |
| **2** | ⛔ **pagina vuota**, nessuna spiegazione | la pagina dichiarava `video.misura_massima` dalla **misura dello schermo** invece che da quel che sa decodificare ⇒ tela concessa più piccola della cattura, e il prodotto **si rifiutava di spedire**. ⚠ Le pagine di prova dichiaravano un tetto comodo: **solo la pagina del prodotto, su uno schermo vero, sbagliava** |
| **3** | ⚠ l'immagine è **piccola** | i banchi guardano **se** i pixel arrivano, non **quanto grandi** sono dipinti |

⇒ ⭐ **È l'invariante I8 in azione** — *il metro è quel che l'utente vede, non il numero che esce dal
banco*. Quella notte i banchi dicevano **48,27 dB**; l'utente ha detto *«non vedo nessun desktop»*, e
aveva ragione lui.

---

---

### ⭐ Il metro ha girato sulla catena vera — e che cosa dice, per intero

`[M]` **13 agosto 2026**. I quattro ingressi messi insieme per la prima volta: la **cattura** (il
buffer BGRx che il prodotto ha scritto con `--rilievo`), il **flusso** che il prodotto ha spedito, il
**riferimento** (lo stesso flusso decodificato da `ffmpeg` — ⭐ il *secondo lettore* che `PIANO.md`
§0.4 dichiarava mancante) e la **pagina** (`getImageData` dalla tela, in un browser vero collegato al
server vero).

| la scena | l'esito | PSNR-Y | strumenti vivi |
|---|---|---|---|
| ⭐ **la mira di F2.6 a sfondo del desktop** | **PROMOSSO** | **62,09 dB** (soglia 45) | **12 su 12**, zero ciechi |
| ⛔ **il desktop naturale dell'utente** | **BOCCIATO su M5** | 58,62 dB | 8 su 12 — ciechi *precedente · otto-bit · piani · ribaltato* |

⛔ **E le due righe non si scelgono: si leggono insieme.** Il verde è del metro **con la mira**; sul
desktop nudo il metro vede meno — senza i marcatori, M4, M7 e M-V si spengono per costruzione — e
trova un rosso. ⚠ Il rosso di M5 **non è stato curato: è sparito quando è cambiata la scena**, e
resta `[?]`.

#### ⛔ E uno dei dodici era verde per costruzione

Trovato da una **revisione avversariale** il 13 agosto, mandata a *refutare* la frase invece che a
confermarla. M8 leggeva un contatore `reset` che la pagina del prodotto chiama **`azzerati`**: valeva
sempre zero, e con lui due costanti scritte a mano. ⇒ **erano 11 vivi più un verde vuoto.**

⭐ Curato, **e la cura di una parola era sbagliata**: `azzerati > 0` è *il prodotto che si comporta
bene*, quindi leggerlo lì avrebbe prodotto un **falso rosso**. La grandezza vera è l'invariante
**`consegnati > completi`**. La storia intera, col controllo del falso rosso e con quel che la
certificazione **non** dice, sta in `rapporti/F2-6-giudizio.md` — qui non
si ricopia.

#### ⛔ Il punto cieco che non è del metro: **a monte della cattura**

Il fondo di verità del metro è **il buffer che il prodotto stesso ha catturato**. ⇒ Quale monitor,
quale sessione, **quale utente** sono fuori dalla sua portata: se il prodotto catturasse il desktop
di un altro utente, cattura, flusso, riferimento e pagina sarebbero **tutti d'accordo**, e il metro
direbbe **62 dB e promosso**.

⛔ **Ed è il difetto numero 1 che l'utente ha trovato in una mattina.** Lo copre un altro banco,
`02-figlio-prova.py` — rigirato il 13 agosto sul prodotto di oggi, **9 misure, 9 uscite 0, nessuna
uscita 2** — ⛔ ma solo per **metà**: vedi la tavola «Che cosa resta `[?]`».

---

### ⛔ Che cosa va detto insieme al verde, o il giudizio è preso su metà quadro

*Scritta il 13 agosto 2026, revisione **R13** rilievo 9. ⛔ Queste tre cose vivevano solo in un
riquadro del `README`, e chi leggeva **questo** documento — che il `README` gli dice di leggere per
primo — ne trovava una e mezza, e sbagliata.*

#### 1. Il **piano 2** del metro non è applicabile: la catena intera non è stata giudicata

Il metro ha due piani (`banchi/02-giudizio-metro.py:46,56`): **piano 1** confronta *pagina ⟷
riferimento* — il browser contro `ffmpeg` **sullo stesso flusso**, cioè due decodificatori
indipendenti; **piano 2** confronta *pagina ⟷ cattura*, che è la catena intera.

⛔ **Il numero che il verde porta è del piano 1.** Il piano 2 il metro lo dichiara **non
applicabile**, e la ragione è aritmetica: perché la sottrazione misuri il client e non la tela, la
perdita del codificatore deve stare **10 dB sotto** il rumore della tela a 8 bit, e qui ne sta
**7,01** (55,08 contro 62,09). Il numero grezzo esiste — **54,11 dB** — ma non è un giudizio.

> ⚠ **E si dichiara un difetto dello strumento**: il messaggio che finisce nel file di esiti dice
> *«non è almeno **6 dB** sotto la prima»* mentre il codice usa **10** (`02-giudizio-metro.py:610`).
> La soglia vera è quella del codice; il messaggio è rimasto alla prima stesura.

#### 2. I dieci bit sono **otto promossi**, e lo sono **a tutt'e due i capi**

- **alla sorgente**: ⇒ `DECISIONI.md` §2.3-ter — non escono da Mutter per **nessuna** strada, né
  MemFd né DMA-BUF, e i formati a 10 bit chiesti per nome danno `no more input formats`;
- **al dispositivo**: `[M]` 13 agosto sul telefono vero — `VideoFrame.format` è **`RGBA`** e `copyTo`
  dà **4 byte per pixel**, su una sequenza dichiarata `hev1.2.4.L90.90`, profondità 10.

⇒ ⛔ **L'etichetta `Main10` continuerebbe a dirlo per tutta la catena senza che nessuno se ne
accorga**: l'immagine viene bene lo stesso. Non è un ripiego nostro, ed è per questo che si scrive.

#### 3. Il telefono **è stato misurato**, ma non sull'hardware

`[M]` 13 agosto, **SM-S916B**, Chrome 151.0.7922.108, Adreno 740: **4 sequenze su 4 dipinte** — HEVC
Main10 **e** AV1 10 bit, `tela_rileggibile: true`.

⛔ **Quel che non ha risposta è «lo decodifica il silicio o la CPU?»**: nel browser il nome del
decodificatore non c'è, senza cavo dati non si legge `Created MediaCodec <nome>` da
`chrome://media-internals`, e il criterio A/B esce **`valido: false`** perché misura *spesa fissa*.
⇒ `[?]` dichiarata — ed è la misura **S2** che `PIANO.md` §1.2 mette in questa fase.

---

### ⭐⭐⭐ Il giudizio dell'utente — **dato il 13 agosto 2026, e la fase è chiusa**

L'utente ha riaperto `https://192.168.0.2:7561/` **come sé stesso** dopo la cura del riscalamento, ha
consegnato lo scatto come risultato, e — messe davanti le **sette cose dichiarate aperte** — ha deciso
di **chiudere la fase adesso**, con quelle scritte come aperte.

⭐ **E questa volta il giudizio non è solo una frase**: lo scatto è stato letto **pixel per pixel**, e
il numero si confronta con quel che il server dichiara.

| dal registro del server, `08:45:44 UTC` | dai pixel dello scatto, otto secondi dopo |
|---|---|
| `vista=2545x927` | la zona dipinta è alta **927 px** ⭐ **identico** |
| `tela=1920x1080` | larga **1648 px**, rapporto **1,7778** contro un 16:9 di **1,7778** |

⇒ ⭐⭐ **La pagina riscala alla vista rispettando la proporzione, e non di un pixel storta** — è
`SPECIFICHE.md` §6.1 misurata **sul vetro**, non dichiarata. Le bande nere (448 a sinistra, 464 a
destra) sono la conseguenza aritmetica di una finestra 2,74 che ospita una tela 16:9: l'alternativa
sarebbe **stirare**, che §6.1 vieta.

⛔ **E lo scatto ha sollevato una cosa che nessun banco aveva visto**: la tela viene dipinta all'**86%**
su un monitor largo **2560**. Non è un difetto del riscalamento — è la `[?]` sulla risoluzione, e
**912 px di nero** sono il suo prezzo, misurato.

⚠ *Si scrive quel che è successo e non una frase che non è stata detta: il verdetto dell'11 agosto
era una **citazione**, questo è una **decisione presa davanti a un elenco**. Le due cose hanno lo
stesso valore e non la stessa forma.* ⇒
`rapporti/GIUDIZIO-13-agosto.md`.


---

<a id="03-movimento"></a>

## Fase 3 — Il movimento

Aperta il **13 agosto 2026**, subito dopo la chiusura della fase 2.
⏳ **In corso.** Questo documento è aperto **all'apertura della fase**, non alla chiusura: è la
regola di [`README.md`](README.md) di questa cartella, e la ragione è che in un documento scritto
dopo le misure si *ricordano* invece di essere *registrate*.

> ⛔ **Stato al 13 agosto 2026, sera**: le **misure sono finite**, i **documenti sono allineati**,
> e restano due cose prima del giudizio — **rigirare le certificazioni** (curare il prodotto le ha
> fatte scadere, ed era previsto) e **il giudizio dell'utente**. ⚠ La fase **non si chiude su un
> documento completo**: si chiude su una misura che l'utente guarda.

> Il modello sta in [`PIANO.md`](PIANO.md) §0.2; le decisioni stanno in
> [`DECISIONI.md`](DECISIONI.md) e qui si **rimanda**, non si copia.

---

### Che cosa deve produrre

Uno **stream per fotogramma**, l'abbandono con `RESET_STREAM`, la **cadenza**.

**Che cosa vede e giudica l'utente**: il desktop **che si muove**, e dice se è fluido.

**I numeri da raggiungere**: ritardo **≤ 50 ms**, traguardo **40** (`SPECIFICHE.md` §3.2).

---

### ⛔ Le tre cose decise PRIMA di scrivere, e da chi

*Il punto di ripresa del 13 agosto ne elencava tre, e imponeva di scioglierle prima di qualunque
riga. Sciolte tutte e tre la mattina del 13 agosto, a codice ancora fermo.*

| # | La cosa | Decisa da | Che cosa è stato deciso |
|---|---|---|---|
| **1** | ⛔⛔ **la risoluzione della tela** | ⭐ **l'utente**, 13 agosto 2026 | **1920×1080 resta**. Era ereditata dalla scena di un banco e mai decisa; adesso è **decisa** |
| **2** | ⛔ **la scena** | il progetto, su `LEZIONI.md` §1.1 | un client **a schermo intero, opaco, che ridisegna a ogni *frame callback*** del compositore, che **conta da sé quanto disegna**, e che porta una **marca leggibile a macchina** |
| **3** | ⚠ **l'attesa dichiarata in anticipo** | il progetto, su `SPECIFICHE.md` §3.2 | il numero da battere è **≤ 50 ms**; il traguardo dei **40** è dichiarato **a rischio** sul muro dei 37 fotogrammi di Mutter — ⛔ **e l'attesa è stata sbagliata due volte**, vedi §3 |

#### 1. ⭐ La tela: **1920×1080**, e adesso è una decisione

La domanda era posta con il suo prezzo misurato accanto: sullo schermo dell'utente la tela viene
dipinta all'**86 %**, cioè **912 px di nero**. Le alternative messe davanti erano tre — tenerla,
portarla a 2560×1440 (lo schermo dell'utente), o accendere subito `SPECIFICHE.md` §6.1 (*la tela
nasce dallo schermo del client*, che il prodotto oggi **non** fa: `src/main.c` · `TELA_L` ha `TELA_L 1920`
scritto a mano).

⭐ **Scelta la prima**, e la ragione è di metodo: la fase 3 misura il **tempo**, non la geometria.
Con la tela ferma, un ritardo che sfora i 50 ms accusa l'architettura; con la tela cambiata sotto,
non si saprebbe se accusa l'architettura o il conto dei pixel.

⛔ **E le bande nere non sono la risoluzione**: 2545×927 di finestra fanno un rapporto **2,74**
contro un 16:9 di **1,7778**. Quelle bande sono la **forma della finestra**, e sparirebbero solo a
schermo pieno — cambiare la tela non le tocca. Va detto perché la `[?]` non venga riaperta
credendo di curarle.

⏳ **Resta aperta** — e va nominata alla fase in cui si accende — l'attuazione di `SPECIFICHE.md`
§6.1: *la tela nasce dallo schermo del client*. Oggi è una specifica scritta e non attuata.

#### 2. ⛔ La scena, e perché non è negoziabile

`LEZIONI.md` §1.1 la prescrive, e il prezzo di averla sbagliata è già stato pagato: **tutte le
misure di ritmo delle fasi 3-9 di v1 sono state buttate**. Un compositore Wayland consegna un
fotogramma **solo quando qualcosa cambia** ⇒ una misura di fotogrammi senza la scena dichiarata
**non è una misura**.

Le due parti, e la seconda è quella che si dimentica:

1. la scena **si muove a ogni ridisegno** — non a raffiche, come farebbe una scena mossa battendo
   tasti;
2. ⛔ **si conta quanto disegna il client**, che è il controllo che dice se il tetto è **del
   compositore** o **della scena**. Senza, il 7 agosto si sarebbe attribuito a Mutter un tetto che
   era della scena — e viceversa.

⭐ **E la fase 3 ne chiede una terza, che §1.1 non chiede**: la scena porta una **marca** — un
contatore che cresce a ogni disegno, e l'istante — rileggibile **dai pixel del fotogramma
decodificato**, e ⛔ **rileggibile dopo la codifica con perdita**, il che va **provato** e non
supposto. Serve a chiudere **M6** e a riaprire il `giro` di **M8** (qui sotto).

#### 3. ⚠ L'attesa, dichiarata prima della misura

Su GNOME il traguardo dei **40 ms** probabilmente **non si raggiunge**, per il muro dei 37
fotogrammi di Mutter. ⛔ Se la misura lo confermasse **non è un difetto nostro** — ed è una ragione
in più per la fase di KDE. Il numero da battere resta **≤ 50 ms**.

⭐ **Ma prima di dichiararlo si prova la cadenza disaccoppiata**, ed è lo **step 1** proprio perché
costa **tre celle e zero righe di prodotto**.

> #### ⛔⛔ L'attesa era sbagliata, e **la parte che ha sbagliato è quella che dava la colpa a un altro**
>
> *Scritto alla chiusura, e questa è la ragione per cui l'attesa si dichiara **prima**: perché poi
> si possa scrivere di quanto si era sbagliato, e in che direzione.*
>
> | quel che l'attesa diceva | quel che la misura dice |
> |---|---|
> | il traguardo dei **40** è a rischio | ⛔ **peggio**: si sfora anche il **tetto dei 50**. `[M]` mediana **74,58 ms**, e con il pezzo cieco **90-115 ms** sullo schermo dell'utente |
> | ⛔ per il **muro dei 37 fotogrammi di Mutter** | ⛔⛔ **falso in tutt'e due i pezzi**: il 37 **non si riproduce**, e Mutter pesa il **22 %** del ritardo. Il **78 % è nostro**, quasi tutto nel codificatore in software |
> | ⛔ *«non è un difetto nostro»* | ⛔ **è un difetto nostro.** Ed è la riga che questa fase ha smentito nel modo più utile |
>
> ⚠ **E la cura dello step 1 riesce, ma non salva il numero**: monitor 120 + freno 90 danno `[M]`
> **61,4** fotogrammi al secondo — e il ritardo **non si muove**, perché il collo è altrove. La
> cadenza non è il ritardo (`LEZIONI.md` §6.2).
>
> ⭐ **Che cosa ha funzionato del metodo**: dichiarare l'attesa prima ha reso **visibile** lo
> scarto. Un'attesa non scritta si sarebbe riadattata al risultato, e nessuno avrebbe notato che la
> fase è entrata credendo di misurare la colpa di Mutter ed è uscita con la propria.

---

### Come è divisa: cinque step

⭐ **Su richiesta dell'utente, il 13 agosto 2026**: la fase è tagliata in **cinque step**, e a
ciascuno sono assegnati **uno o due agenti**, che si occupano di **sviluppo, prova e correzione**.
Il taglio segue le dipendenze, non delle fette arbitrarie.

| # | Step | Che cosa produce | Dipende da | Porta |
|---|---|---|---|---|
| **1** | ⭐ **La cadenza disaccoppiata** | la misura **M3** di `STUDI.md` §gnome §13: `maxFramerate` rinegoziato **da solo**, a monitor fermo | — | 7601 |
| **2** | ⛔ **La scena che si dichiara** | la scena, il conto dei suoi disegni, la marca e il suo lettore | — | 7602 |
| **3** | **Il prodotto: uno stream per fotogramma** | cattura continua · chiave/delta · l'intestazione da 28 byte · `RESET_STREAM` · il credito di stream | 1, 2 | 7603 |
| **4** | **La pagina: i fotogrammi consegnati** | molti stream in parallelo · FIN contro RESET · l'ordine · il buco → `RICHIEDI_CHIAVE` · ⭐ **il conto dei fotogrammi DIPINTI** | 3 | 7604 |
| **5** | ⭐ **L'anello del ritardo (S4)** | il numero, i sette controlli di `STUDI.md` §web §6.3, e il pezzo cieco dichiarato | 4 | 7605 |

⛔ **Ogni step ha porta, file di ban e socket propri**: in fase 3 i banchi girano in parallelo per
davvero, e due banchi che condividono un ban-file si fermano a vicenda.
⚠ **Le tre porte che non si toccano**: **7448** (prodotto di casa), **7501** (bersaglio di P5) e
soprattutto **7561**, che è **quella che l'utente apre** ed è anche il bersaglio del metro — si
legge, non si tocca.

⭐⭐ **E il mandato degli agenti è di REFUTARE, non di verificare.** È la lezione che il 13 agosto
ha prodotto il risultato migliore della giornata: la riga su cui si stava per chiedere il giudizio
è stata smentita da chi era mandato a smentirla, e uno mandato a *verificare* l'avrebbe confermata.
⭐ **E il mandato ammette il rifiuto**: una cura passata dall'alto può essere sbagliata, e chi cura
deve poterla rifiutare con un caso.

---

### ⭐ Che cosa la fase 3 eredita, con due occasioni dentro

| | |
|---|---|
| ⭐ **M6 si può chiudere** | «il fotogramma è del giro prima» è l'unico controllo che vede quel guasto, e **non è mai stato misurato sulla catena vera** perché mancava la cattura del giro precedente. In fase 3 i giri precedenti **ci sono** |
| ⭐ **il `giro` di M8 si può riaprire** | oggi è dichiarato **NON APPLICABILE** perché il prodotto non conosce il nome del giro del banco. Con un `numero` che cresce a ogni fotogramma la domanda torna ponibile ⇒ `rapporti/F2-6-giudizio.md` |
| ⛔ **P15** | `RCP.md` §7.1, il secondo di grazia sulle coordinate: **l'ultimo posto dove un orologio decide**. La fase 3 è tutta tempo — è qui che si scopre se regge |
| ⛔ **il punto cieco a monte della cattura** | il metro non guarda prima della cattura, e con molti fotogrammi il punto cieco **si allarga** |
| ⛔ **«due utenti, ciascuno vede la propria sessione»** | non lo copre nessun banco (metà positiva scoperta). Col movimento diventa **più caro** sbagliarlo, non meno |
| ⚠ **`02-figlio-accendi.sh:165`** | conta i figli **di tutti** invece dei propri: si accende solo quando due banchi girano in parallelo, **e in fase 3 girano** |

#### Gli esiti delle sei eredità, alla chiusura

| | esito |
|---|---|
| ⭐ **M6** | ✅ **chiusa**: da `[?]` a `[M]`, ⛔ **col limite della catena scritto accanto** — mancano la cattura PipeWire e la tela del browser riletta, quindi non è la catena intera |
| ⭐ **il `giro` di M8** | ✅ **riaperto**: la dichiarazione *«NON APPLICABILE per costruzione»* **cade**, con il `numero` che cresce a ogni fotogramma il controllo è **eseguibile** |
| ⛔ **P15**, il secondo di grazia | ⏳ non è quel che ha morso. L'orologio che ha fatto danni in questa fase è stato un altro: quello **del banco**, non del protocollo (§P1 a blocchi, `LEZIONI.md` §1.13) |
| ⛔ **il punto cieco a monte della cattura** | ⛔ **si è allargato come previsto, e adesso ha un numero**: 16-40 ms non compresi nel 74,58. ⚠ E **su Xvfb non esiste**: la stima vale per l'utente, non per il banco |
| ⛔ **«due utenti, ciascuno vede la propria sessione»** | ⭐ **il prezzo è stato pagato, non rinviato**: il deposito del video è sparito **del tutto** — non «uno per sessione», **nessuno**. ⏳ Il banco che copre la metà positiva **resta da scrivere** |
| ⚠ **`02-figlio-accendi.sh:165`** | ✅ **curato** `[R]` — ⛔ **e non eseguito**: la cura è letta nel codice, non girata. Non porta la marca `[M]` |

---

### Lo stato della macchina all'apertura

⛔ *Verificato il 13 agosto 2026, non ricordato.*

| | |
|---|---|
| **albero** | pulito, `f2f21c2` |
| ⭐ **il catalogo dei banchi** | **15 su 15 certificati oggi**, zero scadute, zero non riverificabili — `python3 banchi/01-b12-guasti.py --registro`, rieseguito **all'apertura della fase 3** |
| ⏳ **la scadenza del giorno** | `01-s1b-eccezione.sh oggi` — **4 controlli su 4**, a **2,50 giorni su 7**; la scadenza che Chrome si è segnato è il **2026-08-17T21:09:47Z** |
| ⚠ **le porte in ascolto** | 7448, 7501, 7561 — le sole `:7xxx` |

⛔ **E va detto in anticipo**: la fase 3 tocca `rcp.c` e la pagina, e **curare il prodotto fa
scadere le certificazioni che lo guardavano**. Il catalogo va ricontato alla chiusura, non
all'apertura soltanto.

> ⭐ **È successo esattamente così, ed era previsto dal documento** — quindi non è una riga da
> correggere, è **la riga da rieseguire**. Alla sera del 13 agosto il catalogo dava **5 su 15**, con
> **10 scadute**, e ⛔ **nove banchi nuovi non erano ancora a catalogo** con le loro impronte:
> **sei numerati** — `03-b14` · `03-b15` · `03-b16` · `03-b17` · `03-b18` · `03-b19` — **più tre
> senza numero**: `03-scena`, `03-marca`, `03-deposita`.
> ⚠ **I tre senza numero sono quelli che si dimenticano**, ed è la ragione per cui il conto si fa
> con `ls banchi/03-*` e non a memoria: un catalogo contato sui nomi che uno ricorda è un catalogo
> che dichiara un denominatore falso (`LEZIONI.md` §1.9, regola 5).
> ⚠ **La ricontata si fa a codice fermo e a documenti scritti**, non prima: è la stessa ragione per
> cui questo documento si aggiorna tutto insieme alla chiusura.

---

### Che cosa è stato sviluppato

⛔ *Scritto alla chiusura, **a codice fermo**, dai numeri dei sei gruppi di lavoro — non a memoria.*

#### ⭐ Il numero della fase, che è quel che la fase esisteva per produrre

`[M]` **ritardo cattura → vetro: mediana 74,58 ms** — min 50,4 · p05 58,1 · p95 101,2 · p99 138,1,
**6 giri** da ~800 campioni ciascuno, errore d'orologio **±0,63 ms**.
⛔ **Pezzo cieco 16-40 ms NON compreso** ⇒ sullo schermo dell'utente **90-115 ms**, contro un tetto
di **50**. ⇒ ⛔⛔ **SFORA il tetto e il traguardo.**
⚠ **Non è input → vetro**: il canale di input nasce alla fase 4 (`input` = 0 in **953 su 953**), e
al suo posto sta il controllo **P1**.

| dove se ne va | mediana | di chi è |
|---|---|---|
| disegno → cattura (il `pts` di Mutter) | 16,66 ms | Mutter — **22 %** |
| ⛔ **cattura → primo byte in pagina** | **39,17 ms** | ⛔ **nostro** — codificatore in software |
| il filo | 0,32 ms | — |
| stream completo → `decode()` | 0,08 ms | nostro |
| decodifica | 7,58 ms | nostro |
| richiamo → disegno finito (due `drawImage`) | 10,51 ms | nostro |

⛔⛔ **Il muro non è di Mutter, e le tre prove sono queste**: la scena disegna **59,98/s con 0
attese**; il figlio del prodotto consegna **23,93/s con ZERO attese a vuoto** — *non aspetta mai
Mutter*; il codificatore è **in software** e lo dichiara il prodotto stesso (libsvtav1 / libx265).
⇒ **58 ms su 74,6 sono nostri**, ~39 nel solo tratto cattura→filo. **La cura è la fase 8.**

#### La tavola dei cinque step, con gli esiti

| # | Step | Che cosa ha prodotto | Esito |
|---|---|---|---|
| **1** | ⭐ **La cadenza disaccoppiata** (M3) | `[M]` monitor **120** + freno **90** ⇒ **61,4** consegnati (60,04), mediana **16,66 ms** — cella **D**, pulita. ⚠ E la spiegazione, che è `[R]`: `min_interval_us = 10⁶/maxFramerate` **troncato a intero** contro un tick da 16666,67 µs — una **quantizzazione**, non un battimento, **letta nel codice di Mutter** | ⭐ **il fatto riesce** — ⛔ **ma M3 è MEZZA, non chiusa**: la causa non è misurata, il prodotto non sa chiedere quella cadenza, e la causa scritta in tre documenti era sbagliata |
| **2** | ⛔ **La scena che si dichiara** | `banchi/03-scena.c` — `wl_shm` + `xdg-shell`, marca a **144 bit**, quattro conti fra cui le **attese**, verifica `wl_surface.enter` — e il suo lettore | ✅ **34 verdi / 0 rossi**. M6 chiusa `[M]`, il `giro` di M8 riaperto |
| **3** | **Il prodotto: uno stream per fotogramma** | **135 fotogrammi**, `numero` 1→135 · **132 delta e 3 chiavi** · il primo dopo `SESSIONE` è una **chiave con FIN** · `RICHIEDI_CHIAVE` → chiave in **≤ 200 ms** · **10 stream azzerati contro 18 con FIN**, nessuna chiave abbandonata, **E8 provata sul filo** · ⭐ nei 28 byte il **`pts` di Mutter** (scarto dal nostro `CLOCK_MONOTONIC`: **11 347 µs**) · ⭐ **il deposito del video sparito del tutto** | ✅ **6 punti su 7 chiusi** · 13 controlli di certificazione, **13 verdi** · giro dal vivo **8 verdi, 1 rosso** |
| **4** | **La pagina: i fotogrammi consegnati** | **60,0 fotogrammi dipinti al secondo** offrendone 60; tetto a saturazione **127,6/s** a 1080p | ✅ **19 casi verdi**, **8 guasti innestati su 8 accusati** |
| **5** | ⭐ **L'anello del ritardo (S4)** | il numero qui sopra. **P1** verde (N=25 → **+25,08**; N=60 → **+58,58**), con l'iniezione **fuori dal prodotto** e l'ancora d'orologio che **non ci passa**. **P3** verde **sui pixel veri**: 234 fotogrammi in movimento, **0 falsi positivi** | ✅ **banco 31 su 31, ponte 11 su 11** — ⛔ **ma P5 NON ESEGUITO, e adesso lo dice** |

> ⛔⛔ ⚠ **La riga dello step 1 diceva un'altra cosa, e va detto che cosa diceva.** *Fino alla sera
> del 13 agosto 2026 portava: «13 punti, 8 confermano, 0 smentiscono» e l'esito «⭐ **M3 chiusa, e
> riesce**». ⛔ **Falso tutt'e due.** Il file degli esiti della griglia,
> `banchi/03-b14-esiti-griglia.jsonl`, porta **tre righe**: il terreno e **due celle**
> (`griglia-apertura-120` e `griglia-freno-90`), e **tutt'e due portano `scena_sul_mio_monitor:
> false`** ⇒ sono rifiutate dal banco stesso, che sul verdetto stampa «⛔ la legge NON regge su **0
> punti su 0**». **Corretta il 13 agosto 2026**, rilievo del coordinatore della fase 3, verificato
> sui due file di esiti.*
>
> | | |
> |---|---|
> | ✅ **che cosa sopravvive** | tutto quel che sta in `banchi/03-b14-esiti.jsonl`: sette celle, **tutte** con `scena_sul_mio_monitor: true` — A (60/60 → 31,5), B (120/120 → 82,9), C (120/60 → 46,13), ⭐ **D (120/90 → 61,4, mediana 16,66, p99 20,43)** e i tre controlli. E con loro il **«sei decimi non si riproducono»** (la A dà 0,50 pulito) e il **«37 non si riproduce»** |
> | ⛔ **che cosa cade** | la **legge della griglia verificata**. La quantizzazione torna `[R]`: resta la spiegazione migliore che abbiamo, coerente con la cella D, **ma è letta nel codice di Mutter, non misurata** |
> | ⛔ **e cade anche** | il **riscontro incrociato**: in `banchi/03-b14-esiti-scena2.jsonl` la cella D porta `scena_sul_mio_monitor: false` e **1 fotogramma in 25 s**, e il controllo di ritorno di quella scena non torna. ⇒ **il 61,4 ha una scena sola** |
> | ⚠ **e M3** | **non è chiusa: è mezza** — il fatto è `[M]`, la causa `[R]`, il riscontro non c'è (`STUDI.md` §gnome §13) |
>
> ⭐⭐ **E la cosa che vale più della correzione**: la ragione del rifiuto è **la trappola numero uno
> della giornata** — *la scena deve stare sul monitor che si sta catturando* — che stamattina era
> già costata **quattro giri** ad altri due gruppi ed era già stata scritta in `LEZIONI.md` §1.1.
> ⛔ Il banco **lo aveva scritto nel proprio file**, campo `scena_sul_mio_monitor: false`, e nessuno
> l'ha guardato: si è letto il numero e non la riga accanto. ⇒ *Un banco che dichiara la propria
> invalidità non serve a niente se chi legge guarda solo il risultato* — `LEZIONI.md` §1.1-bis.

#### ⭐ E tre cose che il prodotto sa fare adesso e non sapeva stamattina

1. ⭐ **il deposito del video non esiste più.** Il prezzo dichiarato il 12 agosto — *«due utenti
   insieme non possono vedere tutt'e due il proprio»* — **è pagato**, e la cura non è «un deposito
   per sessione»: è **nessun deposito**. `wt_video_deposita` non esiste;
2. ⛔ **la cura B-18**, che è la più cara di tutte a non averla: uno dei tre percorsi di abbandono di
   un delta **non accendeva** la richiesta di chiave ⇒ **un solo delta saltato per mancanza di posto
   sfasciava l'immagine per sempre e in silenzio** — il `numero` non veniva consumato, quindi nessun
   buco, quindi il client non poteva chiedere la chiave, e con un GOP infinito non ne arrivava più
   una da sola;
3. ⛔ **la pagina nel worker**, scritta per intero, **misurata e tenuta spenta** — vedi qui sotto.
   ⭐ È uno sviluppo finito nella colonna delle cose che non hanno funzionato, **e ha prodotto lo
   stesso una riga utilizzabile**: `[M]` la **decodifica** fuori dal thread principale vale
   **−3,44 ms**; è la **tela** che affonda il conto (+17,6).

---

### ⛔ Che cosa non ha funzionato

⭐ *Si riempie anche quando fa una brutta figura — è la regola 2 del modello. E questa fase ne ha
prodotta abbastanza da riempirla: ci vanno i **giri buttati**, le **cure rifiutate**, e i **banchi
che hanno accusato il prodotto a torto**.*

#### ⛔⛔⛔ 0. LA PEGGIORE, e non è stata trovata da un banco: è stata trovata **rileggendo un piano**

*13 agosto 2026, sera, a codice fermo, sulla richiesta dell'utente di **controllare che il piano
della sessione nuova non avesse problemi**.*

Il piano della sessione seguente si apriva con una corsia dichiarata *«quella da cui comincia la
sessione»*: **dare al banco un palco con una GPU vera**. Nasceva da una conclusione scritta la notte
prima, e scritta con la fermezza di una misura ripetuta — *«`[M]` 5 giri validi su 5:
`isConfigSupported` è `false` per tutte le stringhe HEVC. E la causa vera: su **Xvfb non c'è GPU
affatto** ⇒ non è un problema di codec, è un problema di PALCO»*.

⛔⛔ **Era la bandiera `--disable-gpu` del banco stesso** (`03-b17-ritardo.py:626`). La sonda
chiedeva a un browser **accecato da lei** se vedesse.

| Chrome, stesso Xvfb, stesso script, **una sola variabile** | webgl | HEVC |
|---|---|---|
| **senza** `--disable-gpu` | `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))` | ⭐ **true** |
| **con** `--disable-gpu` | `niente webgl` | no |

⭐⭐ **E non è rimasta una dichiarazione**: il flusso uscito da `hevc_vaapi` è stato fatto
**dipingere** allo stesso Chrome — `[M]` **5 giri su 5**, 1920×1080, **119 fotogrammi su 120**,
`powerEfficient: true`.

⚠ **Il segnale c'era, ed era stato archiviato**: il piano stesso annotava *«un giro della sonda ha
detto HEVC = true con GPU, e non si è più riprodotto (0 su 5 successivi)»*, catalogandolo come
**anomalia da inseguire**. ⇒ Era **l'unico giro giusto**. *Un esito che non si riproduce una volta
su sei non è rumore: è una **variabile non dichiarata**.*

⭐ **Quel che NON è successo, e va detto perché era il rischio grosso**: `03-b17-ritardo.py:582` ha
**`gpu=True` di default** — `--senza-gpu` è opt-in ⇒ ⛔ **il numero della fase, i 74,58 ms, NON era
misurato al buio.** Era **la sonda dei codec** a esserlo, non la misura.

⇒ **Costo**: una corsia intera di un piano, e la sessione seguente sarebbe cominciata da lì.
⇒ **Riga nuova per `LEZIONI.md`, ed è la §2.0**: *un banco che risponde «no» deve scrivere **con che
palco** ha risposto* — «non c'è» e «non ho potuto guardare» hanno lo stesso aspetto, e il secondo è
più frequente del primo.

#### ⛔ 1. I giri buttati, e sono tutti dello stesso errore

⛔ **La scena stava sul monitor sbagliato**, e i monitor virtuali erano **quattro**. Una scena
aperta su quello che non si stava catturando produce un banco che **gira, non fallisce, e misura il
palco di qualcun altro**. *Costo: **quattro giri** — due allo step 3 e due allo step 1.*
⚠ E la stessa forma è arrivata come **cura passata dall'alto**: *«accendi su `Meta-3`»* — il monitor
giusto era `Meta-2`, e seguirla avrebbe fatto misurare il palco di un altro gruppo.
⇒ **Riga nuova per `LEZIONI.md` §1.1**: *la scena deve stare sul monitor che si sta catturando*, che
su un palco con monitor virtuali **non è quello dell'utente**.

#### ⛔⛔ 2. Le cure passate dal coordinatore e RIFIUTATE — cinque, e avevano ragione tutte e cinque

*È il risultato di metodo della giornata, e va scritto qui perché l'imputato è chi coordinava.*

| la cura passata | perché è stata rifiutata |
|---|---|
| la `ResizeObserver` | ⛔ **la premessa era falsa** |
| la seconda cura della vista | ⛔ **caduta alla misura**: `overflow-y: scroll` tiene `clientWidth` **fermo** |
| il **seqlock in contesa** | ⛔ **200 letture su 200 riuscite** con la scena a 1034 disegni/s. La causa era un **relitto a `seq` dispari**, non la contesa |
| *«quel che manca ai 60 è di Mutter»* | ⛔ **zero attese a vuoto** |
| *«accendi su `Meta-3`»* | ⛔ i monitor sono **quattro**, il suo era `Meta-2` |

⭐ **E il mandato ammetteva il rifiuto**, che è la ragione per cui i cinque si sono visti. Una cura
passata dall'alto può essere sbagliata, e chi cura deve poterla rifiutare **con un caso**.

#### ⛔⛔ 3. I banchi che hanno accusato il prodotto a torto

1. ⛔⛔ **lo `STREAM_LIMIT_ERROR`, ed è la specie peggiore: il banco aveva creato lui la condizione,
   e illegalmente.** Doveva provare che il prodotto regge un credito basso, e annunciava
   `initial_max_streams_uni = 6` **dopo** la stretta di mano — cosa che **RFC 9000 §4.6 vieta** ⇒
   ⛔ **il `6` non è mai passato sul filo.** `[M]` il server aveva **128 posti concessi** e ne ha
   aperti **14**. ⇒ **`ngtcp2` non ha violato niente, e lì il prodotto non ha un difetto.** ⚠ Il
   prodotto reagiva **correttamente** a una condizione impossibile, e la reazione corretta è stata
   letta come il guasto. ⭐ Ma cercandolo è uscito **B-18**, che era vero e peggiore;
2. ⛔ **«nessuna delle tre porte protette è in ascolto»**: misura presa dalla **macchina sbagliata**
   — il controllo girava su CHUWI, e 7448/7501/7561 ascoltano su **NIC-OS**. Verificato: `ss -ltn`
   su `192.168.0.2` le dà tutt'e tre vive, più la **7603** dello step 3;
3. ⛔ **la mia diagnosi del seqlock in contesa era sbagliata**, ed è la stessa specie: accusava il
   lettore mentre il difetto stava nella scena.

#### ⛔⛔ 4. Un verde in catalogo lo produceva lo STRUMENTO — ed era peggio di un falso verde

**Non era falso nel merito: non era mai stato provato capace di arrossire.** Su Xvfb i quadri non
girano, e in Blink l'evento `resize` si consegna **dentro** il giro di rendering ⇒ senza quadri non
arriva mai. A svegliare la conduttura era `Page.captureScreenshot`, chiamata solo `if args.copia`:
⛔ **un'opzione di comodo di stampa**, con un effetto collaterale non dichiarato.

| il banco ORIGINALE, sul prodotto SANO | esito |
|---|---|
| **senza** `--copia` | ⛔ **ROSSO, 5 pretese cadute** — fra cui «la tela è stata RICOMPOSTA (1 → 1)» |
| con `--copia` | verde (1 → 3) |

⛔ **E il buco strutturale**: le **quattro** pretese di quel blocco **non erano mai state innestate
con nessun guasto**. Verdi da sempre, senza che nessuno sapesse se sapessero fare altro.
⭐ **Curato**: il quadro si batte apposta (5 battiti fissi, non «finché diventa verde»); una spia del
palco conta quadri ed eventi; ⭐ **si giudica prima il palco** — se il `resize` non è arrivato il
banco dice *«IL PALCO, NON IL PRODOTTO»* e si ferma; due guasti nuovi accusano 5 e 4 pretese.
Tre giri: **9 giri, 5 scene sane verdi, 4 pagine guaste rosse**.
⚠ **Stessa trappola armata altrove e oggi non vulnerabile**: un secondo banco regge solo perché
nessuna sua pretesa passa da un quadro. Chi ve ne aggiunga una ci cade, **in verde**.

#### ⛔⛔ 5. La scena che correva a vuoto, e i suoi due sintomi erano lo stesso difetto

**Causa unica**: `buffer_libero()` chiamava `wl_display_dispatch()` **da dentro un gestore di
eventi** ⇒ `disegna()` annidata ⇒ da un `wl_surface.frame` in volo se ne fanno due, e si moltiplica.
⚠ Si accende **solo fuori da casa sua**: serve che i tre buffer siano occupati insieme, cioè un
compositore più carico — **quel che succede quando accanto gira una cattura**.

| | sano | guasto innestato | risanato |
|---|---|---|---|
| `fidato` | true | **false** | true |
| `frame` in volo, max | **1** | **18** (fino a 26) | 1 |
| disegni/s a 60 Hz | 60 | **461,7** (fino a 1034) | 60 |

⭐ **E i due sintomi erano lo stesso difetto**: una scena in corsa a vuoto non torna al ciclo
principale ⇒ ignora `--secondi` (**6 chiesti, 146 vissuti**) ⇒ il banco la **uccide** ⇒ la morte cade
a metà scrittura ⇒ `seq` del seqlock resta **dispari per sempre**. Il lettore vecchio falliva **3 su
3**, non «ogni tanto».
⭐ **Il rilevatore misura la CAUSA, non il ritmo**: *«i `wl_surface.frame` in volo non possono mai
essere più di 1»* — un invariante di protocollo, che non ha bisogno di sapere a che frequenza va il
monitor. E lo **stato d'uscita porta il verdetto** (2 = letto ma NON fidato), così `set -e` ferma chi
legge i disegni senza guardare `fidato`. **Chiusa: 43 righe verdi, 0 rosse.**

⛔⛔ **RIGA CHE VALE PER TUTTO IL PROGETTO**: *ogni cella di ritmo misurata con `03-scena` **prima**
del 13 agosto va rifatta o marcata `[?]`* — la scena poteva correre a vuoto senza dirlo.
⭐ **Le celle che contano dello step 1 reggono**: `banchi/03-b14-esiti.jsonl` usa `03-b14-scena`
(EGL, sua), e la matrice dei tetti rifatta con la cura è **invariata** (60,0-60,2 disegni/s,
0 attese).

> ⛔ ⚠ *Questa riga diceva: «**Il riscontro incrociato dello step 1 regge** […] ⇒ l'accordo **entro
> il 4 %** fra due scene indipendenti tiene». **Non regge.** La seconda scena del riscontro è
> proprio `03-scena`, cioè quella che questa stessa riga dichiara da rifare — e in
> `banchi/03-b14-esiti-scena2.jsonl` la sua **cella D** porta `scena_sul_mio_monitor: false`,
> `palco_stabile: false` e **1 fotogramma in 25 s**, mentre il suo controllo di **ritorno** dà 52,84
> contro gli 80,28 della sua cella B: **non torna**. Il 4 % vale su A (0,7 %), B (3,2 %) e il
> controllo positivo; C sta al **5,4 %** e il negativo al **7 %**. ⇒ ⛔ **La cella D — il 61,4 — ha
> UNA scena sola.** Corretta il 13 agosto 2026, rilievo del coordinatore della fase 3.*

#### ⛔ 6. Il metro si stava regalando 11 ms, e P5 si dichiarava verde senza esserlo

1. ⛔ **la prima stesura del metro chiudeva al richiamo del decodificatore**, regalandosi **~11 ms**
   nostri e misurabili su un tetto di 50. ⭐ **Il confine è stato spostato nella direzione scomoda**:
   il numero è salito da **63,8 a 74,6** e lo si è lasciato salire;
2. ⛔ **P5 si dichiarava verde**, e dopo tre iniettori `scavalcati = 0` non è *«l'anello regge»*: è
   *«il fenomeno non si è presentato»*. Adesso è dichiarato **NON ESEGUITO**. ⚠ E la causa vera del
   fuori ordine è la **dimensione** del fotogramma, non la rete: l'evento scatta al completamento
   dello stream, quindi l'ordine d'arrivo è quello delle dimensioni — e **una chiave grossa viene
   scavalcata dai delta**.

#### ⛔ 7. La pagina nel worker: scritta, misurata, e **sbagliata a metà**

`STUDI.md` §web §6.1 la prescriveva. Attuata, ha dato `[M]` **+27,6 / +33,5 ms** di mediana (73,66 / 67,79
→ **101,30**) e **tetto −73,4 %** a 1080p (127,6 → **33,9** dipinti/s). ⛔ **Ma il totale nasconde
la cosa che serve**, e la scomposizione la mostra:

| tratto (mediana, ms) | prima | dopo | Δ |
|---|---|---|---|
| stream completo → `decode()` | 0,07 / 0,06 | **10,23** | ⛔ **+10,2** |
| ⭐ **la decodifica** | **7,17** / 6,13 | ⭐ **3,73** | ⭐ **−3,44 / −2,40** |
| richiamo → disegno finito | 9,63 / 9,11 | **27,19** | ⛔ **+17,6** |

⭐⭐ **⇒ §6.1 non è sbagliata per intero: vale la DECODIFICA, non la TELA.** Il decodificatore
consegna prima quando non contende; è la tela che affonda il conto. ⇒ La riga utilizzabile non è
*«il worker è sbagliato»* — quella sarebbe solo una porta chiusa — ma *«la decodifica sì, la tela
no»*, che dice dove mettere il confine.

⭐ **E il meccanismo è la scoperta che cambia una regola**: `transferControlToOffscreen` **impegna la
tela al ritmo del quadro** — un `requestAnimationFrame` implicito che nessuno ha scritto. ⛔⛔ **La
prescrizione conteneva la propria smentita**: §6.1 prescriveva il worker e vietava il salto di
quadro, che il worker reintroduce in silenzio. Nessuna rilettura del documento poteva accorgersene
senza misurarla.

⚠ **E le due grandezze dicono cose opposte**: sulla catena vera il worker dipinge **di più**
(26,3/s contro 22,8-24,2), a saturazione crolla di tre quarti (`LEZIONI.md` §6.2).

⏳ ⛔ **`[?]` E questo va letto accanto ai numeri, non in fondo**: tutto è su **Xvfb, in software,
senza GPU**, e la penale è in gran parte sincronizzazione al quadro. ⇒ **Su hardware vero il conto
va rifatto prima di seppellire §6.1.** Il codice resta dietro `#video=worker`, **spento**, proprio
perché quel giorno il numero si rifà senza riscrivere niente (`DECISIONI.md` §2.8).

#### ⚠ 8. E le cose che non hanno funzionato senza essere colpa di nessuno

- ⛔ **`src/pagina.c` · `servi()`**: `strcmp(percorso, "/")` ⇒ `/?qualunque-cosa` prende **404** (`[M]`: `/`
  → 200 / 166107 byte, `/?video=worker` → 404 / 9). ⇒ **`?tela=desincronizzata` non è MAI stato
  raggiungibile**, e il commento della pagina indica da sempre una strada che non esiste. Non visto
  da nessuno perché i banchi servono la pagina da un `http.server` di Python, che il `?` lo ignora;
- ⛔ **i due gemelli `rcp.c` divergevano**, e **il prodotto non compilava per nessuno**. Riallineati
  la sera del 13;
- ⚠ **`weston-simple-egl` non è installato** sulla macchina di prova (rootfs in RAM), mentre due
  documenti lo davano presente e uno lo prescriveva come scena. Ha smesso di essere un riferimento:
  la scena della fase 3 è la nostra;
- ⚠⚠ **`/tmp` è una tmpfs da 3,8 G al 94 %**, 246 M liberi: ha già fatto fallire un giro di
  `03-b16` (Chrome non parte). ⛔ **Non è stata svuotata di proposito** — dentro ci sono le prove
  dei giri di oggi, e buttarle toglierebbe la **provenienza** dei numeri di questa fase.

---

### Il giudizio dell'utente — ⭐ DATO il 14 agosto 2026, mattina

> #### ⭐ **«Mi sembra abbastanza fluido, non il massimo ma pur sempre fluido.»**
> — l'utente, davanti a `https://192.168.0.2:7571/`, entrato come sé stesso

⇒ ⭐ **La fase 3 si chiude qui**, ed è la regola: *una fase si chiude su una misura giudicata
dall'utente, non su un documento completo* (`PIANO.md` §0.3).

#### ⭐⭐ E il giudizio è stato MISURATO — dalla registrazione fatta dall'utente

*L'utente ha registrato il proprio schermo mentre guardava (`Screencast From 2026-08-14 07-47-30.webm`,
10,5 s, 2560×1080, VP8 a 30,3/s). ⇒ **La sua impressione si può contare invece di crederla**: si
segue il baricentro della barra bianca fotogramma per fotogramma.*

| | |
|---|---|
| fotogrammi della registrazione | **318**, la barra visibile in **tutti** |
| ⛔ **fotogrammi in cui il contenuto NON è cambiato** | **97 su 312 = 31,1 %** |
| ⇒ ⭐ **ritmo del contenuto** | **20,9 fotogrammi/s** |
| le pause | **83 volte 33 ms · 7 volte 66 ms** — ⭐ **mai più lunghe** |

⭐⭐ **E tre misure indipendenti danno lo stesso numero**: il banco dell'anello **21,98/s**, il
registro del prodotto **~21/s**, e ora **l'occhio dell'utente, da fuori, 20,9/s**. *Nessuna delle tre
sa delle altre.*

⛔ **E la causa del «non il massimo» è stata cercata, non supposta.** L'ipotesi naturale era
*l'irregolarità* — che la barra avanzasse a scatti. **Falsa**: la distribuzione dei passi è
**bimodale sui due valori attesi** (~7-8 colonne = un fotogramma di attesa, ~14-15 = due), e **solo
il 7 % dei passi** sta fuori da quei due gruppi, con **due soli** valori anomali su 215.

> ⇒ ⭐ **Il «non il massimo» non è instabilità: è il RITMO.** A 21 fotogrammi al secondo su uno
> schermo che ne mostra 30, **una volta su tre l'occhio vede lo stesso fotogramma due volte** — e
> quello si sente, anche quando non c'è nessuno scatto.
> ⛔ **Quindi la strada per «il massimo» non è togliere jitter: è alzare il ritmo** — e il ritmo lo
> tiene giù un tratto da **28,0 ms su 78,1** che allora chiamavamo «il disegno».
> ⚠ ⛔ **E quel nome era falso, corretto il 14 agosto 2026** (deciso dall'utente): il disegno costa
> **2,25 ms** `[M]`, e i 28,0 erano **l'attesa del fotogramma dalla GPU** più il disegno. Il totale
> resta vero. `fasi/rapporti/F4-A2-pagina-dipinge.md` e `F4-A10-anello-input.md`.

⚠ **I limiti di questa misura, dichiarati**: la registrazione stessa gira a 30,3/s, quindi **non può
vedere niente di più veloce**; e un fotogramma perso dal registratore si conterebbe come una pausa
del prodotto. ⇒ I 20,9/s sono un **limite inferiore**, e concordano con gli altri due numeri.

#### ⛔ E i tre limiti del giudizio, scritti PRIMA che lo desse e non dopo

| | |
|---|---|
| **1** | vale per la catena con **AV1 in software** — ⭐ ed è **esattamente** la configurazione su cui è stato misurato il numero (71,86 ms, ~22 fotogrammi/s) |
| **2** | ⛔ **non** vale per la codifica in hardware: **il browser dell'utente non dipinge HEVC** (§0-ter) |
| **3** | ⛔ **non ha visto un desktop**: ha visto **un monitor aggiunto** con dentro la scena dei banchi (§0-quater) |

#### ⭐⭐ E il giudizio ha prodotto DUE difetti che nessun banco aveva trovato

*È il valore che il piano attribuiva al giudizio — «l'utente guarda **il suo** desktop, un'altra
scena da quella misurata» — e si è realizzato in trenta secondi, due volte.*

> #### ⛔⛔ §0-ter — Il browser dell'utente NON dipinge HEVC, e chiede chiavi a vuoto
>
> `[M]` dal registro del prodotto, sessione vera del 14 agosto:
> ```
> 1748 fotogrammi consegnati (118 chiavi) … 0 guasti — codec 1
> [192.168.0.3]: §5.2 vuole una CHIAVE — richiesta girata al palco   ← 1 659 volte
> ```
> **Il server manda, il client rifiuta e richiede una chiave, per sempre.** Schermo nero.
> ⛔ **E i banchi dicevano il contrario** — 1 047 fotogrammi dipinti, 30 fps esatti, `consegnati ==
> dipinti`. La differenza: quel giro aveva **una scena sintetica e un Chrome lanciato dal banco**;
> questo ha **il browser dell'utente e il suo desktop**.
> ⇒ ⭐ *Un banco che dice sì e un utente che vede nero: il banco stava misurando un'altra cosa.*

> #### ⛔⛔ §0-quater — Il prodotto non mostra il desktop: ne AGGIUNGE uno vuoto
>
> `[M]` dal registro: `il nostro monitor e' **Meta-2**, **2 prima e 3 dopo**` — il prodotto trova la
> sessione grafica dell'utente e **le attacca un monitor nuovo**, poi registra quello. GNOME ci
> disegna **lo sfondo** (va su tutti i monitor) ma **barra, dock e finestre restano sul primario**,
> che nessuno guarda.
> ⇒ ⛔ **L'utente non vede il suo desktop: vede un secondo schermo vuoto.** E senza input (fase 4)
> lì non ci finirà mai niente da solo — quindi *«l'utente vede il desktop che si muove»* **non era
> realizzabile per costruzione**.
> ⛔⛔ **E la riga che ha nascosto tutto questo per due fasi** è il giudizio della fase 2 —
> *«è lo sfondo GNOME, è OK»*: **uno sfondo vuoto preso per un successo**. ⇒ `SPECIFICHE.md` §5.1
> vuole che la sessione remota **sia** la sessione grafica dell'utente. Non lo è ancora, ed è
> **lavoro della fase 5**.

---

### ⏳ Il punto lasciato APERTO dall'utente — il debito di chiave strozzato

*Deciso dall'utente la sera del 13 agosto 2026: ⭐ «**a freddo non si può prendere una decisione:
l'esperienza potrebbe essere migliore di quello che si teme. Lasciamo il punto aperto**».*

⛔ **E la decisione è metodologicamente giusta, non una rinuncia**: è `LEZIONI.md` §2.6 — *l'utente
non è il banco*. Curare sulla base di un sintomo **temuto** invece che **osservato** è scrivere una
tolleranza su una grandezza che nessuno ha misurato (`LEZIONI.md` §1.13).

#### Che cos'è

`rcp_video_serve_chiave()` **non ha nessun chiamante in `src/`**: il debito di chiave arriva al
codificatore solo per una strada laterale (`webtransport.c:1352`), **strozzata a una richiesta al
secondo**. Il prodotto è **conforme** a `RCP.md` §5.2 — la chiave arriva — ma paga il ritardo.

⛔ **E il numero non è quel che sembra: `[M]` 343 delta buttati in un giro solo NON sono 343
intoppi. Sono UNO, moltiplicato.** La catena:

1. si butta **un** fotogramma (legittimo, §5.1 — «si butta il passato quando è passato»);
2. scatta il debito di chiave (§5.2);
3. il server **rifiuta tutti i delta** finché la chiave non è pronta;
4. ⛔ ma la richiesta passa da una strada che ne lascia passare **una al secondo**;
5. ⇒ per quel secondo, **tutto quel che il prodotto produce viene buttato**.

⇒ A 60 fotogrammi al secondo, **un abbandono legittimo ne genera fino a sessanta illegittimi**, e
il sintomo — l'immagine che resta rotta **per un secondo intero** dopo un singolo intoppo — è
precisamente quel che un utente chiama *«va a scatti»* senza saper dire perché.

#### ⭐⭐⭐ CHIUSO IL 14 AGOSTO 2026 — e la risposta è **peggiore della domanda**

*Letto dal registro della sessione in cui l'utente ha dato il giudizio, come previsto: **costo
zero**, nessun banco nuovo.*

⛔ **La strozzatura a «una richiesta al secondo» NON tiene** — e non tiene **esattamente nel caso
per cui esiste**. `[M]`, due sessioni vere dello stesso prodotto, stesso giorno:

| sessione | intervalli fra due richieste di chiave | ritmo |
|---|---|---|
| **AV1** — il client dipinge | `33.558 · 34.585 · 35.586 · 36.586` | ⭐ **1 al secondo**: la strozzatura tiene |
| ⛔ **HEVC** — il client NON dipinge | `40.160 · 40.360 · 40.560 · 40.760` | ⛔ **5 al secondo**, esatte |

⇒ ⛔⛔ **Quando il client decodifica, la strozzatura funziona; quando NON decodifica — cioè quando
ogni chiave è sprecata — si apre a cinque volte tanto.** `[M]` **1 659 richieste** in una sessione,
ciascuna girata al palco, e **la chiave è il fotogramma più caro che esista**.

⭐ **E i tre numeri che il punto aperto chiedeva, con la risposta accanto:**

| | domanda | risposta misurata |
|---|---|---|
| **1** | quante volte scatta | **1 659** nella sessione del giudizio |
| **2** | quanti delta per volta | ⚠ **nessuno**: `abbandonati 0` in tutta la sessione AV1 ⇒ **lo scenario temuto — «un abbandono legittimo ne genera fino a sessanta illegittimi» — NON si è presentato** |
| **3** | quanto passa fino alla chiave | **200 ms** nel caso rotto, **1 000 ms** in quello sano |

⇒ ⭐ **Il timore era mal posto e il difetto è un altro**: non è l'abbandono a generare richieste, è
**il client che non decodifica**. E il freno che doveva contenerlo **si stacca proprio lì**.
⚠ *Il punto era stato lasciato aperto per non decidere su un sintomo temuto invece che osservato
(`LEZIONI.md` §2.6). Osservato, il sintomo era un altro.* ⛔ **Non si cura qui**: si cura dove nasce,
cioè in fase 5 insieme al difetto di HEVC.

#### ⭐ Come si chiudeva, e costava ZERO lavoro in più

Il prodotto **scrive già ogni abbandono nel registro**: `RCP.md` §5.1 lo impone — *«un fotogramma
perso in silenzio e uno abbandonato di proposito hanno lo stesso aspetto dal lato che riceve»*.

⇒ ⭐ **Basta leggere il registro DOPO la sessione in cui l'utente dà il giudizio.** Tre numeri, e
decidono da soli:

| che cosa si legge | che cosa dice |
|---|---|
| quante volte il debito di chiave è scattato | se sulla rete vera l'evento **capita** o no |
| quanti delta sono stati buttati per ciascuno | se il moltiplicatore è **60** o **2** |
| quanto è passato fra l'abbandono e la chiave | se il secondo di strozzatura si paga davvero |

⛔ **Se il debito non scatta mai sulla LAN dell'utente, il punto si chiude come `[?]` che non morde
qui** — e va nominato alla fase in cui la rete è cattiva per davvero. **Se scatta, il numero dice di
quanto**, e la cura si giustifica su un fatto invece che su un timore.

⚠ **Quel che NON va fatto**: chiudere questo punto perché il desktop *sembrava* fluido. La sessione
del giudizio si guarda **e si legge**, ed è la stessa disciplina con cui la fase 2 è stata chiusa —
davanti a un elenco, non a un'impressione.

---

### ⏳ Il secondo punto lasciato APERTO dall'utente — dove finisce di contare il tetto

*Deciso dall'utente la sera del 13 agosto 2026: ⭐ «**alla tua domanda si può rispondere solo dopo
aver misurato i risultati con l'accelerazione HW**».*

#### La domanda che oggi nessun documento risponde

`SPECIFICHE.md` §3.2 chiede **≤ 50 ms**. ⛔ **Ma non dice fino a dove si conta**, e la fase 3 ha
scoperto che la differenza non è accademica:

| dove si smette di contare | con la codifica di **oggi** (software) | con un codificatore **gratis** `[R]` |
|---|---|---|
| al **disegno finito** | **74,58 ms** ⇒ fuori | **~35,4 ms** ⇒ ⭐ **dentro il tetto, vicino al traguardo** |
| al **pixel acceso** (col pezzo cieco) | 90-115 ms ⇒ fuori | **51-75 ms** ⇒ ⛔ **fuori anche a fase 8 fatta** |

⇒ **La stessa architettura è promossa o bocciata a seconda di dove si mette il traguardo.**

⚠ *E il confine della **misura** è stato spostato oggi, nella direzione scomoda: la prima stesura
dell'anello chiudeva al richiamo del decodificatore, regalandosi ~11 ms nostri e misurabili. Il
numero è salito da 63,8 a 74,58 ed è stato lasciato salire. `CODER.md` §1-bis dichiara adesso dove
finisce la **misura** — non fino a dove vale il **tetto**, che è questa domanda.*

#### ⛔ Perché NON si decide adesso, e sono due ragioni indipendenti

1. **il pavimento con l'accelerazione vera non è misurato**, e non lo sarà finché la fase 8 non
   esiste;
2. ⛔ **il pezzo cieco è a sua volta una `[?]`**: **16-40 ms** è una forbice larga **due volte e
   mezzo**, e nessuna API JavaScript la espone (`STUDI.md` §web §6.2). Decidere dove finisce di contare un
   tetto di **50** appoggiandosi a un numero che oscilla di **24** è decidere su niente — ed è la
   grandezza sostitutiva che `LEZIONI.md` §1.13 vieta.

⇒ È la stessa disciplina del primo punto aperto: **non si cura, e non si decide, su un sintomo
temuto invece che osservato** (`LEZIONI.md` §2.6).

#### ⛔ E una cosa che va detta perché non venga letta male

**Il «codificatore finto» misurato in fase 3 NON è un codificatore hardware.** Risponde a
*«la catena regge quando la codifica costa poco?»*, che è una domanda utile e **diversa**. Un
codificatore vero in hardware ha un profilo di ritardo suo — la consegna alla GPU, l'attesa della
fine, il ritorno dei byte — che un finto **non modella affatto**.
⇒ ⛔ **Quel numero dice se l'architettura ha margine, NON quanto varrà la fase 8.** Le due cose non
si sommano, e chi le sommasse otterrebbe una previsione che nessuno ha misurato.

#### ⭐ Come si chiude

Alla **fase 8**, e nell'ordine:

1. si misura l'anello **con la codifica in hardware**, con lo stesso banco (`03-b17-ritardo.py`) e
   la stessa scena, così i due numeri si sottraggono davvero;
2. si guarda **dove cade il totale al disegno finito**, e **quanto vale davvero** il tratto della
   codifica quando è la GPU a farla;
3. ⛔ **solo allora** la domanda «fino al disegno o fino al vetro» ha davanti due numeri veri invece
   di una forbice, e l'utente decide **sapendo che cosa costa ciascuna delle due letture**.

⚠ **Quel che NON va fatto**: scrivere in `SPECIFICHE.md` una risposta oggi. Una soglia decisa per
prudenza, e poi trovata comoda, è una soglia che si sposta di un passo a ogni rilettura — è la
famiglia **P8 → P11 → P13 → P14**, che questo progetto ha già percorso quattro volte.

---

### ⭐⭐⭐ LA FASE NON SI CHIUDE QUI — la codifica in hardware è anticipata dentro la fase 3

*Deciso dall'utente la sera del 13 agosto 2026: ⭐ «**si anticipa la codifica HW alla fase 3. Per
questo però dopo servirà una nuova sessione**».*

⛔ **Quindi tutto quel che sta scritto sopra è vero e NON è finale.** Il documento resta com'è —
non si riscrive una misura perché è arrivata una decisione — e questa sezione dice **che cosa manca
ancora prima del giudizio**.

#### Perché, in un numero

Il ritardo misurato è **74,58 ms**, e ⛔ **39,17 di quelli — il 53 % — sono la codifica in
software**. Gli altri quattro tratti sommano **~35,4 ms**, che sarebbe il **pavimento della catena a
codificatore gratis**: `[R]` **dentro il tetto dei 50, e vicino al traguardo dei 40**.

⇒ L'obiezione dell'utente, che è quella giusta: *«senza accelerazione hw stiamo ragionando e
sviluppando su numeri non molto affidabili»*. Un totale dominato da un pezzo che sta per essere
sostituito **non è un numero su cui prendere decisioni** — e le fasi 4-7 ne produrrebbero altri
uguali, da rifare dopo.

⚠ **Ma il danno era stretto, e va detto perché non si legga la giornata come persa**: dei risultati
della fase 3, **solo il verdetto sul ritardo** dipendeva dal codificatore. La cella **D** (61,4 a
monitor 120 e freno 90), il verde prodotto dallo strumento, **B-18**, **B-20**, il worker respinto,
la scena che correva a vuoto e i tre falsi rossi **non ci si appoggiano affatto**.

> ⛔ ⚠ *Questa riga cominciava l'elenco con «**La legge della griglia**». **Va tolta di lì**: la
> legge della griglia non è mai stata misurata — le due celle della griglia sono rifiutate dal banco
> stesso (riquadro nella tavola dei cinque step). Al suo posto sta la **cella D**, che è pulita e
> regge. **Corretta il 13 agosto 2026**, rilievo del coordinatore della fase 3.*

#### ⭐⭐ E si può fare — `[M]` verificato il 13 agosto sul server

```
Intel iHD driver 25.2.3   ·   /dev/dri/renderD128 e renderD129
VAProfileHEVCMain10     : VAEntrypointEncSliceLP    ← 10 bit, IN HARDWARE
VAProfileHEVCMain444_10 : VAEntrypointEncSliceLP    ← e perfino 4:4:4 a 10 bit
```

⛔ **E questa riga corregge un errore di oggi**: un agente aveva riferito *«su questo server non c'è
un codificatore hardware per nessuno dei due codec»*, e **nessuno l'aveva verificata**. È vera per
**AV1** — e stava già nei documenti — ed è **falsa per HEVC**. ⚠ È la stessa forma dei «37
fotogrammi di Mutter»: una riga **ripetuta** invece che **misurata**, che poi decide un piano.

#### Che cosa manca, e in che ordine

| | |
|---|---|
| 1 | ⛔ **il primo scoglio, e va affrontato per primo**: il codec negoziato nelle misure di oggi è **AV1**, perché la sonda HEVC di Chrome **fallisce su Xvfb** (`EncodingError`). Senza un client che accetti HEVC, l'anello intero non si misura — al massimo si misura il lato server, e sarebbe **mezzo anello** |
| 2 | la codifica HEVC in hardware nel prodotto, **su una copia** finché non è misurata |
| 3 | ⭐ **l'anello rimisurato con lo STESSO banco e la STESSA scena** — o i due numeri non si sottraggono |
| 4 | ⛔ **i CINQUE tratti affiancati**, non il totale: *tolta la codifica in software, gli altri quattro restano dove sono?* Se restano, l'architettura è **assolta**; se si muovono, c'è una contesa che nessuno ha visto |
| 5 | ⚠ **i fotogrammi consegnati accanto ai millisecondi** (`LEZIONI.md` §6.2): in v1 il costo per fotogramma scese da 41 a 6 **mentre i consegnati calavano da 29 a 22,7** |
| 6 | e **solo allora** il giudizio dell'utente, su un numero che non ha il freno a mano tirato |

⚠ **`EncSliceLP` è la codifica «a bassa potenza»**: veloce, ma con limiti suoi di qualità e di
funzioni. **Non è equivalente** alla codifica piena, e va dichiarato accanto al numero.
⭐ **E porta un'occasione**: `EncSliceLP` è l'entrypoint che `STUDI.md` §web nomina come *«da verificare»*
per i **sotto-livelli temporali** — cioè la strada per abbandonare un fotogramma **senza rompere
quelli dopo**, che oggi costa una chiave ogni volta.

⛔ **Che cosa NON si anticipa**: la **copia zero** resta alla fase 8. È lavoro suo, e non tocca
questo numero.


---

<a id="04-si-comanda"></a>

## Fase 4 — Si comanda

*Aperta il 14 agosto 2026, mattina. ⛔ Questo documento è aperto **all'apertura della fase**, non
alla chiusura: le misure qui si **registrano** strada facendo, non si ricordano dopo
(questo documento).*

---

### Che cosa deve produrre

`PIANO.md` §«Fase 4 — Si comanda», e in testa la priorità decisa dall'utente:

| | | |
|---|---|---|
| ⭐ **1** | **IL DESKTOP VERO** — deciso dall'utente il 14 agosto 2026, ed è **dentro la fase, in testa** | finché il desktop non si vede, **non c'è niente da comandare** |
| **2** | il **canale di input**: puntatore assoluto, pulsanti, rotella, lettere, posizioni | `RCP.md` §7.3 |
| **3** | il **puntatore disegnato dalla pagina**, e il cursore che non entra mai nell'immagine | `SPECIFICHE.md` §7.1 |
| **4** | le **due disposizioni della pagina** — classica con `Pointer Lock`, tocco coi sette gesti, **passaggio automatico sul contesto** | `DECISIONI.md` §5-bis.0-bis |
| **5** | le **scorciatoie che il browser si tiene**, **dichiarate** e non falsificate | `SPECIFICHE.md` §7.3-bis |

**E i due lavori ereditati dalla fase 3**, che senza di loro l'utente non ha niente da giudicare:

| | | dove |
|---|---|---|
| ⛔ | **HEVC non dipinge nel browser dell'utente** — 1 748 consegnati, **0 dipinti** | §03-movimento §0-ter |
| ⛔ | **il disegno: 28,0 ms su 78,1 — il 36 %**, il collo di bottiglia nuovo | `fasi/rapporti/F3-E-anello-rimisurato.md` |

**L'utente vede**: ⭐ **usa il desktop**. È il momento in cui REMOTIX smette di essere una
dimostrazione.

---

### Il banco *(scritto PRIMA di sviluppare)*

⛔ **Ogni sottofase scrive il proprio banco prima del proprio codice, e lo certifica prima di
crederlo** (`CODER.md` §3.3). L'elenco vive qui e si riempie strada facendo.

**Le dieci sottofasi, un agente ciascuna** *(lanciate il 14 agosto 2026, in parallelo)*:

| | sottofase | il banco | che cosa accusa | porte | esito |
|---|---|---|---|---|---|
| **A1** | ⭐ il desktop vero | `04-b20-desktop-vero` | la shell è **sul monitor che si cattura** — non uno schermo in più, vuoto | 7601-05 | ✅ **205 contro 0** |
| **A2** | la pagina che dipinge | `04-b21-dipinge` · `04-b22-disegno` | fotogrammi **dipinti**, non «consegnati» · il tratto del disegno scomposto | 7611-15 | ⭐ **le due accuse CADONO** |
| **A3** | il filo dell'input | `04-b23-filo-input` | le violazioni di `RCP.md` §7.3, ciascuna col motivo giusto | 7621-25 | ✅ **64 su 64** |
| **A4** | l'iniezione (libei/EIS) | `04-b24-iniezione` | l'input arriva **al desktop**, e il segno della rotella è quello giusto | 7631-35 | ✅ **27 OK, 0 NO** |
| **A5** | la tastiera | `04-b25-tastiera` | la lettera accentata con la disposizione giusta **e** con quella sbagliata | 7641-45 | ✅ **26 su 26** |
| **A6** | il cursore | `04-b26-cursore` | il cursore **non** è nell'immagine, e la forma arriva in banda laterale | 7651-55 | ✅ **0 contro 762** |
| **A7** | la pagina, modo classico | `04-b27-classico` | `Pointer Lock`, il puntatore disegnato, il rilascio alla perdita del fuoco | 7661-65 | ✅ **19 su 19**, due giri |
| **A8** | la pagina, modo tocco | `04-b28-gesti` | i sette gesti, e il passaggio automatico sul contesto | 7671-75 | ⭐ **24 su 25**, tre giri |
| **A9** | le scorciatoie (sonda S3) | `04-b29-scorciatoie` | «arriva **e basta**?» — i tre stati, su due motori | 7681-85 | ⭐ **594 misure**, 74 buttate |
| **A10** | i banchi di fase | `04-b30-anello-input` | ⭐ l'anello **input → vetro**, che alla fase 3 non era misurabile | 7691-95 | ⭐ **16 su 16**, e ⏳ `n=0` |
| ⭐ **O2** | **il numero dell'anello** | `04-b30-*` (esteso) · `04-b32-terreno` · `04-b32-coda` · `04-b32-ritmo` | ⭐ **il ritardo input → vetro, con `n` e la scomposizione**, e la coda che cresce | **7721-25** | ⭐⭐ **~140 ms, n = 326 e 322**, 10 controlli su 11 |

⭐ **E le cuciture le tiene il coordinatore, non gli anelli** — `src/input.h`, `src/tastiera.h`,
`src/cursore.h`, più `figlio.c`, `main.c` e il `Makefile`. ⛔ È la lezione di
`fasi/rapporti/F5-desktop-vero.md`: *il difetto della fase 3 non era **dentro** un pezzo, era **fra**
due pezzi ciascuno corretto per conto suo — e le cuciture, non avendo un proprietario, non le
guardava nessun banco.* Qui il proprietario ce l'hanno.

---

### Che cosa è stato sviluppato

#### ⭐ A5 — la tastiera *(chiusa il 14 agosto 2026)*

`src/tastiera.c` su `xkbcommon` 1.7.0: dato un carattere Unicode e la disposizione, quali codici
**evdev** premere e in che ordine. Rapporto in
`rapporti/F4-A5-tastiera.md`.

---

### Le misure *(si riempie strada facendo)*

#### ⭐ Il costruttore, prima di ogni misura — `[M]` 14 agosto 2026

L'albero della fase 4 **costruisce**: `make` esce 0 nel contenitore della macchina di prova, con
`-lei -lxkbcommon` collegate davvero e `input.o · tastiera.o · cursore.o` dentro il binario.
⛔ È il controllo che vale **prima** di tutti gli altri: dieci anelli interrotti a metà da un guasto
del server potevano lasciare l'albero rotto, e non l'hanno fatto. ⭐ E i **gemelli sono pari**
(`src/rcp.c` ≡ `banchi/rcp/rcp.c`).

#### ⭐⭐ LA CATENA DELL'INPUT È CUCITA DA UN CAPO ALL'ALTRO — `[M]` 14 agosto 2026

*E la cucitura è del coordinatore, per la ragione scritta in testa a questo documento.*

⛔ **Il fatto che nessun anello aveva in mano, e che cambia la forma del lavoro: il palco vive in un
ALTRO PROCESSO.** `libei` parla con la sessione grafica dell'utente, e quella ce l'ha il **figlio**;
QUIC, RCP e i byte del client stanno nel **padre**. ⇒ Fra il tasto premuto nel browser e il tasto
premuto sul desktop c'è **un confine di processo**, e nessuno dei due lati poteva attraversarlo da
solo.

| il tubo | il verso | dove |
|---|---|---|
| ⭐ **l'input** | padre → figlio | `MSG_INPUT` + `figli_input()` · i **sei ganci** in `rcp_avvia()` · il ponte `input_al_figlio()` in `main.c` |
| ⭐ **la forma del cursore** | figlio → padre | `MSG_CURSORE` a pezzi (un 256×256 in BGRA fa 262 144 byte, otto volte `PEZZO_MAX`) · `wt_cursore_diffondi()` · `rcp_cursore_forma()` |
| ⭐ **il campo `input` dei fotogrammi** | figlio → padre, **dentro il fotogramma** | ⛔ e questa è la scelta che lo rende **vero** invece di plausibile |

> ##### ⛔⭐ Perché il campo `input` lo timbra il FIGLIO e non il padre
>
> §6.2 promette che «l'effetto di quell'input è già nella scena». Il padre sa che cosa ha
> **mandato** al palco; solo il figlio sa che cosa il compositore ha **preso**, e in che istante ha
> catturato. ⇒ Riempirlo nel padre direbbe *«l'ultimo input spedito prima della spedizione»*: un
> numero più alto, e l'anello del ritardo misurerebbe un ritardo **più corto del vero — in nostro
> favore**, che è la direzione in cui nessuno sbaglia per caso.
> ⭐ Da cui due conseguenze scritte nel codice: il contatore avanza **solo se l'iniezione è
> riuscita**, e il fotogramma *tenuto* porta il **suo** `input`, non quello di adesso.
> `CODER.md` §1-bis: *il confine si sposta nella direzione scomoda*.

⭐ **E l'albero costruisce con tutti e tre i tubi collegati**: `make` esce 0, `-lei -lxkbcommon`
dentro, gemelli pari, e la marca nel binario verificata.

---

#### ⭐⭐ A1 — il desktop vero, e **la persistenza** `[M]` 14 agosto 2026

**L'A/B, stessa scena in movimento, stesso quarto d'ora:**

| | monitor | fotogrammi al client in 40 s | verdetto sui pixel |
|---|---|---|---|
| **con** `--virtual-monitor` | 1 → 2 | ⛔ **0** (`0 guasti`: uno zero vero) | ⛔ **VUOTO** |
| **senza** (curato) | 0 → 1 | ⭐ **205 conformi** | ⭐ **SHELL** (salto di luminanza 51,3 · fronti del testo 548) |

⭐ **E il banco non si fida di «c'è lo sfondo»** — è l'errore che ha nascosto il difetto per due fasi.
Distingue con **due indicatori di natura diversa**, calibrati su immagini vere *prima* di fissare le
soglie: il **salto di luminanza** al bordo basso della barra (11,8 shell / 0,07 sfondo) e i **fronti**
del testo dell'orologio (565 / 0). ⛔ Il terzo indicatore (la dock) **non distingueva, e sta scritto
che è stato scartato**.

##### ⛔ Tre cose che hanno smentito il mandato che avevo scritto

| | |
|---|---|
| ⛔ **`sessione.c:650` non lo esegue nessuno** | `sessione_assicura()` **non è chiamata dal prodotto**. Su questa macchina `--virtual-monitor` lo impone un drop-in scritto a mano ⇒ **I7 violato**, e il desktop di `prova` si vedeva grazie a un file di configurazione, non al prodotto |
| ⛔ **la cura è in QUATTRO posti, non due** | coi due soli, `sessione_assicura()` avrebbe **ucciso la sessione giusta a ogni chiamata** (0 monitor = `SESSIONE_NERA` = «fai rinascere»). La macchina a stati è stata rovesciata, e dichiarato |
| ⛔ **la tela concessa è una promessa che nessuno mantiene** | client a 1280×720: il server la concede, il palco cattura a 1920×1080 (costante di compilazione), `rcp` rifiuta ogni fotogramma — `[M]` **145 prodotti, 0 spediti, client nero senza errori**. ⚠ E la misura la decide il **nostro** formato PipeWire `[R]`, non `RecordVirtual`: la `[?]` n. 1 di questo documento è **risolta, e la risposta era un'altra** |

##### ⭐⭐ E la persistenza REGGE — la tesi del difetto è **falsa**

*Nata da un'obiezione dell'utente, il 14 agosto: «deve lavorare anche quando nessuno guarda lo
schermo — altrimenti che senso ha la persistenza della sessione?».*

⛔ **La tesi da refutare era**: *«un client che si stacca porta via l'unico monitor: la sessione resta
senza dove disegnare, e le applicazioni se ne accorgono»* — cioè il difetto che in v1 mandava
`libmutter` in asserzione fallita. `[M]` otto letture in 11 minuti, sessione fatta nascere dal
prodotto curato, scena dichiarata (una finestra che scrive l'ora 5 volte al secondo, **sullo schermo
e su un file**):

| | |
|---|---|
| ⭐ il monitor | **mai sparito**: sempre **1**, `Virtual remote monitor`, anche nei quattro minuti senza nessuno. Mai `0` |
| ⭐ l'applicazione | **1 160 righe fra 07:37:36 e 07:41:36** — i 240 s a 4,8/s **senza un buco**, mentre non guardava nessuno |
| ⭐ `libmutter` | **nessuna asserzione nuova**: le 2 asserzioni e 7 critiche sono **costanti** dalla prima all'ultima lettura, e portano il pid di un `gnome-shell` che il prodotto stava **congedando** |
| ⭐ al riattacco | `riattacco-1` **120 fotogrammi conformi → SHELL**; `riattacco-2` → **SHELL**. ⭐ Ed è **la stessa finestra**: **pid invariato** (465823 all'inizio e alla fine, da 154 a 3 497 righe) — una finestra nuova avrebbe un pid nuovo |

⇒ ⭐ **L'esito è «il monitor c'è e nessuno lo cattura», che non è un difetto: è l'invariante I4
mantenuta.** E il merito è del **figlio**, che sopravvive al distacco per costruzione.
⚠ **Ma resta una cosa per la fase 5, e non era attesa**: **il palco muore col FIGLIO, non con la
sessione** ⇒ chi congederà un figlio che gira a vuoto **toglierebbe il monitor a una sessione viva**
— il difetto di v1 preso dall'altro capo.

⛔ **E tre numeri del banco mentivano**, trovati da chi li aveva scritti: il conteggio dei monitor era
**il doppio** (`GetCurrentState` elenca ogni schermo due volte) e sbagliava **nella direzione che
rassicura**; il contatore dei client **non esisteva** (QUIC vive su un solo socket non connesso, e
dava zero in tutt'e due i modi di guardare); e il file di esiti non era JSON valido. ⭐ **Nessuno dei
tre entrava nel verdetto — e proprio per questo nessuno li avrebbe controllati.**

---

#### ⭐⭐ A2 — le due accuse ereditate dalla fase 3 sono CADUTE

| | |
|---|---|
| ⛔ «HEVC non dipinge» | **falso**: `[M]` **8 caselle su 8** dipingono (profilo della stringa × profondità del flusso, HEVC e AV1, 64×48 **e** 1920×1080), compresa la combinazione esatta del prodotto — flusso Main10 letto con la stringa Main8. Palco = il **desktop vero**, GPU vera, dichiarato e verificato dall'altro capo. E in continuo: **60 su 60**, sei giri |
| ⛔ i «1 748 consegnati, 0 dipinti» | ⛔ **il conto era letto male**: nella finestra della sessione nera il contatore **entra a 1748 ed esce a 1748** per 2 min 38 s — il 1748 è **il residuo della sera prima** (`ciclo_fotogrammi` è statico di file). E il «1 659» era un `grep -c` su tutto il file da 6,7 MB: nella finestra vera sono **653** |
| ⇒ la causa vera | **il monitor aggiunto e vuoto**: nulla si muove, Mutter non consegna. **Lavoro di A1, non del codec** |
| ⛔ «il disegno costa 28,0 ms» | **falso**: `[M]` **2,25 ms** (5 giri, dispersione 0,30), stesso confine della fase 3. E il controllo positivo su AV1 dà **6,25-8,45** contro i **9,07** della fase 3 ⇒ **il cronometro era tarato** |

⭐ **E la prima ipotesi dell'anello — profondità 8 negoziata contro flusso a 10 — è stata scritta
prima di misurare e smentita alla prima casella.** *Scritta prima, quindi smentibile: è il verso
giusto.*

---

#### ⭐⭐ A3 — il filo dell'input: **64 casi su 64**, e **16 guasti** certificati

29 violazioni + 25 verdi attesi + **10 su §7.2** (il cursore). 64/64 con una connessione nuova che
arriva a `ECCOMI` dopo ciascuna, e gli stessi numeri su due macchine.

⭐ **E la certificazione ha trovato DUE difetti del prodotto che nessun giro verde avrebbe visto:**

| | |
|---|---|
| ⛔ `6u + lung` a 32 bit | con `lung = 0xFFFFFFFF` vale **5**: un annuncio da 4 GiB passava il controllo di lunghezza |
| ⛔⭐ il `CURSORE_FORMA` da otto byte | spediva `w.len` invece di `n` ⇒ dichiarava `16×16` con **otto byte di corpo**, e **la pagina avrebbe chiuso a ogni cambio di forma**. ⭐ E la riga più preziosa: **il registro del server scriveva il vero e il filo un'altra cosa** — un banco che avesse guardato il valore di ritorno sarebbe stato **verde** |

⭐ **E la coppia dei limiti è provata nei DUE versi**, che è la cosa che un caso solo non dimostra:
`0×5` e `5×0` devono essere **rifiutati** *e* `0×0` (il nascosto) deve **passare**. Due guasti
opposti: togliendo il controllo parte il messaggio vietato; rendendolo troppo severo **sparisce per
sempre il cursore nascosto**. ⛔ Nessuno dei tre casi, da solo, distingue le due implementazioni.

⚠ **E la divisione dei compiti che ne è uscita**, che vale oltre il cursore: `cursore.c` decide **che
cos'è** quel cursore; `rcp.c` non deve **emettere** ciò che la specifica vieta. *Sono due obblighi a
due strati, e confonderli fa perdere quello che protegge l'utente.*

---

#### ⭐⭐ A4 — l'iniezione: l'input arriva DAVVERO al desktop `[M]` 14 agosto 2026

*Macchina di prova, utente `prova`, `libmutter` 48.7 · `libei` 1.3.901 · `wl_seat` v8.*

⛔ **Come si è misurato, ed è la metà che conta**: il testimone è **una finestra Wayland vera**
(`banchi/04-b24-testimone.c`) a schermo intero **sul monitor che abbiamo montato noi**, che stampa
una riga per ogni evento che il **compositore le consegna**. ⚠ Il registro dell'iniettore *non è* la
misura: dice che abbiamo chiamato una funzione.
⭐ **E il monitor non si spera, si sceglie per misura**: la sessione aveva già un `Meta-0` di un
altro client; il nostro `RecordVirtual` monta `Meta-1`, e il testimone si mette **su quello**. Senza,
ogni iniezione sarebbe finita sullo schermo sbagliato — la stessa forma d'errore che alla fase 2
teneva verde un banco mentre la cattura riceveva zero fotogrammi.

**Il giro sano: 27 righe `OK`, 0 `NO`, 0 `??`.** E il banco è **certificato con due guasti innestati
su una COPIA di `input.c`** — ⛔ e se la copia risulta identica all'originale **il banco si rifiuta di
girare**, perché un guasto che non cambia niente certifica il nulla:

| guasto | il banco ha detto |
|---|---|
| **`segno`** — si toglie l'inversione | ⛔ **ROSSO**: *«lo schermo remoto scorre AL CONTRARIO»* — ⭐ e la riga del mezzo scatto è rimasta **verde**: ha accusato **il segno**, non «qualcosa» |
| **`conto`** — il rilascio non rilascia | ⛔ **ROSSO** su tre righe, e una è **dal lato che riceve**: *«la finestra NON ha visto il rilascio del tasto»* |

##### ⭐ I quattro `[R]` portati a `[M]`

| | |
|---|---|
| ⭐⭐ **il `mapping-id` era INVERTITO in v1** | quello che dichiariamo (`277896a5…`) **non è** quello che la regione porta (`d72788c1…`): lo genera **Mutter** e ce lo pubblica, e `handle_record_virtual` **ignora in silenzio** la nostra proprietà. ⇒ Riusare v1 alla lettera dava **un puntatore che finiva sull'altro monitor** |
| **il segno della rotella, nei DUE versi** | `+120` (utente in su) → `axis_value120 = −120`; `−120` → `+120`. ⭐ Segni **opposti**: si misura il segno, non «che qualcosa si muove». E l'orizzontale passa com'è, misurato anche lui nei due versi |
| **i mezzi scatti** | `60` → `−60`. ⛔ Con `scroll_discrete` sarebbe stato `60/120 = 0`: la strada è `scroll_delta` |
| ⭐⭐ **i due ricambi silenziosi, riprodotti a dispositivo IN USO** | keymap `us`→`de` (68 402 → 70 138 byte, `ricambi_tastiera 0→1`) e geometria 1600×900 → 1280×720 (`ricambi_puntatore 0→2`). ⭐ **E il codice li regge**: rilegge keymap e regioni a ogni `DEVICE_ADDED` |

⭐ **E due fatti che nessun documento portava**: **la regione non è all'origine** (`1920,0`) — senza
sommarla il puntatore va sull'altro schermo **senza errore** — e **senza un consumatore PipeWire il
dispositivo assoluto non nasce affatto**.

⭐ **Il rilascio al distacco** (`RCP.md` §11): conto tenuto, `input_rilascia_tutto()` ritorna **2**, e
⭐ **la finestra vede i due rilasci**. ⏳ La metà «e si riattacca a verificare» è della fase 5, ed è
dichiarata.

⛔ **Che cosa NON ha funzionato**: **Firefox non chiede mai la pagina** in questa sessione (5 giri,
149 s, **zero richieste HTTP**, causa non trovata) ⇒ lo strumento è stato sostituito con il testimone
Wayland nativo — ⭐ più vicino alla verità, ⛔ **ma il ponte con `deltaY` scende da `[M]` a `[S]`**.
E **tre difetti erano del banco**: il contatore dei ricambi cieco (accusava «non riprodotto» su un
difetto avvenuto), la prova del rilascio che girava dopo i ricambi e **accusava la cosa sbagliata**,
e — dopo la cura — il banco che **leggeva il `PRONTA` di ieri** e stampava un `NO` falso contro il
prodotto.

---

#### ⭐⭐ A7 — la pagina, modo classico: **19 casi su 19**, due giri di fila

`[M]` 14 agosto 2026, Chrome 151, GNOME Wayland, pagina **isolata fra origini**. ⭐ **Il verdetto si
costruisce sui BYTE**, decodificati fuori dal browser da un lettore scritto leggendo `RCP.md` §7.3 —
**mai dal registro della pagina**. E il giudice è **certificato prima di ogni misura** (sano → otto
guasti → risanato).

| | |
|---|---|
| ⭐ **il caso del bordo** | spinto oltre con `Pointer Lock` esce **1919, 1079 e mai 1920**. ⚠ E l'attesa è **ricalcolata in Python** a cinque fattori di scala: a `1279×719` il valore vero è **1918,5**, dove `round`/`ceil` direbbero 1919 — cioè il banco sa distinguere l'arrotondamento giusto da quello che chiude la sessione |
| ⭐ **`Ctrl+C` copia** | `29↓ 46↓ 46↑ 29↑`, **zero `LETTERA`**; e `Maiusc+a` → **una** `LETTERA` U+0041 e **zero** posizioni |
| ⭐ **il rilascio alla perdita del fuoco** | fuoco tolto con una **scheda vera**: i due rilasci escono. A fuoco tenuto: **nessuno** |
| **la rotella** | +120 su, −120 giù, **+60 mezzo scatto**, e il segno invertito **una volta sola** (dal server) |

⛔⭐ **E la tesi 5 è metà refutata, con una misura**: l'`id` è confermato, ⛔ ma **la premessa
dell'`istante` in `RCP.md` §7.3 era FALSA** — `performance.now()` ha grana **5 µs**, non 1 ms:
**duecento volte** più fine. ⇒ La riga è stata corretta in `RCP.md` il 14 agosto: la regola
sopravvive alla premessa, ma un client che moltiplicasse i millisecondi per mille butterebbe via
**199 parti su 200** di una misura che ha già.

⛔ **Che cosa NON ha funzionato**: `unadjustedMovement` **rifiutato** da Chrome su Wayland (ripiego
dichiarato) · la lock è **negata senza fuoco** · ⚠ **tre rossi su tre erano del BANCO**, non del
prodotto (l'attesa sul bordo, `wheelDelta` che gonfia il mezzo scatto a uno intero `[M]`, e le fasi
marcate a tempo invece che a quiete) · **«e poi che cosa fa il desktop» non è misurato** · e **solo
Chrome**.

---

#### ⭐⭐ A6 — il cursore: il canale aveva un capo e nessuna sorgente

| | |
|---|---|
| ⛔ **il `[R]` portato a `[M]`** | con la negoziazione di ieri: **62 buffer, 0 `SPA_META_Cursor`, 0 `CURSORE_FORMA`**. Lo stesso strumento con una riga in più: ⭐ **49 su 49**. ⇒ *Lo zero era uno zero, non una cecità* |
| ⭐ **il cursore NON è nell'immagine** | riquadro 96×96 sul puntatore fermo su tinta nota: **0 pixel** fuori tinta con `cursor-mode=2`, ⛔ **762** con `cursor-mode=1` — il controllo positivo sui pixel veri |
| ⭐ **la forma arriva, riletta dai byte** | 48×48 (attivo 6,2) · `0×0` nascosto · 48×48 al ritorno · 32×32 (3,1). **Zero violazioni** di §7.2/§5.5 |
| ⭐ **e non si rimanda mille volte** | 52 metadati ⇒ **4** forme (7,7 %); **40 movimenti ⇒ 0 forme nuove** |

⛔ **E una cosa che va dichiarata invece di inventata**: su un flusso appena aperto la forma **può non
arrivare mai** — `cursor_bitmap_invalid` nasce falso e si accende **solo** su `cursor-changed`
(43 metadati su 43 con la sola posizione). `cursore.c` lo **dichiara**, e non inventa una freccia.

---

#### ⭐⭐ A8 — la pagina, modo tocco: **24 verdi su 25**, tre giri

`[M]` 14 agosto 2026, Chrome 151. Giudice certificato **verde → rosso → verde su 5 guasti**, uno per
**famiglia di confusione**; 78 messaggi §7.3 con `id` 1→78 crescenti.

⛔⭐ **E le tre confusioni che ha trovato, `DECISIONI.md` §5-bis.3 non ne nomina NESSUNA** — cioè la
tabella dei sette gesti descrive che cosa fare, non che cosa *si confonde con che cosa*:

| | |
|---|---|
| ⛔ **tap-e-mezzo e doppio clic sono lo stesso gesto** | ⭐ e la cura **non è una soglia**: *si preme al contatto e si rilascia al distacco*, e le due strade divergono da sole **senza ritardo**. ⚠ La stesura «prudente» — aspettare per decidere — **rompe il doppio clic**. Provato coi casi gemelli |
| ⛔ **«2 dita tap» contro «1 dito tap ripetuto»** | un **clic destro che esce come doppio clic sinistro**. ⛔ Nessuna soglia in ms li separa, e separarli costerebbe **300 ms su ogni clic** — vietati da `CODER.md` §1-bis. ⇒ La soglia è **una sovrapposizione: ≥ 1 campione**, e sotto quella il difetto è **DICHIARATO**, non nascosto |
| ⛔ **rotella contro pizzico** | che la tabella non nomina affatto: si confronta Δdistanza contro Δcentro, e si decide **una volta sola** |

**Le soglie, in ms e px CSS**: `T_TAP` **180 ms per CONTATTO** · `D_TAP` 9 px · `T_SEQUENZA` 300 ms ·
⭐ `D_STESSO_DITO` **40 px ≈ 10 mm** — e viene da `SPECIFICHE.md` §7.1: **lo stesso millimetraggio che
motiva il puntatore disegnato** separa il tap-e-mezzo dal tap a due dita · `D_PIZZICO` 24 px `[?]` ·
`PX_PER_SCATTO` 40 px `[?]`.

⭐ **Due difetti trovati dal banco e non dalla lettura**: la durata va misurata **per contatto** (o il
tap a tre dita **non esce mai**), e **un dito che si stacca sposta il centro di 40 px senza che
nessuno si muova** — veniva letto come rotella.

---

#### ⭐⭐ A9 — le scorciatoie: **594 misure, 520 credibili, 74 buttate e CONTATE**

`[M]` 14 agosto 2026, Chrome 151 e Firefox 140 ESR.

> ##### ⛔⛔ Lo stato di mezzo esiste, è misurato, **ed è LARGO**
> `[M]` **18 combinazioni su 42** su Chrome in finestra arrivano alla sessione remota **e** fanno
> agire anche il browser. ⇒ ⭐ *Una prova che avesse guardato solo il lato della sessione le avrebbe
> dichiarate **tutte verdi**.* È la ragione per cui §7.3-bis dice che la misura non è «arriva?» ma
> «arriva **e basta**?», e adesso quella riga ha un numero sotto.

**La ricetta, ogni gradino col suo numero:**

| gradino | Chrome 151 | Firefox 140 ESR |
|---|---|---|
| `preventDefault()` nella pagina | caso peggiore **18 → 0** | **15 → 0** |
| schermo intero **+ Keyboard Lock** | riservate dal browser **8 → 0** | ⛔ **impossibile**: non ha nessuna delle due forme, e a schermo intero **PEGGIORA** (5 → 7) |
| i bottoni a schermo | restano **5** | idem |

⛔ **E quel che resta perso non è del browser**: `Super`, `Super+D`, `Alt+Tab`, `Alt+F2`, `Alt+F4`,
`Ctrl+Alt+Canc` — sono del **compositore del client**, e **nessuna API le riprenderà mai**.

⭐⭐ **E il giro salvato dalla regola di credibilità vale quanto la misura**: un giro di Firefox usciva
*«Firefox si tiene tutto, `Ctrl+C` compreso»* — **verosimile e interamente falso**, perché
`document.hasFocus()` ⛔ **mente su Firefox/Wayland**. ⇒ Da lì il cancello vero: **non si chiede alla
pagina se CREDE di avere il fuoco — le si chiede di DIMOSTRARE che riceve i tasti.** 74 righe su 594
buttate da quella regola, e **contate**.

⛔ **Non provati, e non dedotti** (ciascuno col suo strumento scritto nel rapporto): Safari/WebKit,
iPhone, **DeX**, **PWA su Chrome per Android**, Firefox ≥ 151, Edge. ⭐ La PWA è `[M]` **solo sul
desktop** (`--app`: **0 riservate già in finestra**); la metà Android resta `[?]`.

---

#### ⛔⭐ E la quinta cucitura rotta della fase, trovata dall'anello che la subiva

`REMOTIX_PUNTATORE.muovi()` non accendeva `cl_noto` ⇒ su una pagina che nasce in **disposizione a
tocco** e non entra mai nel modo classico, il dito muoveva **un puntatore che non compariva mai** —
⛔ e senza nessun errore, da nessuna parte. Cura di **una riga**, chiusa dal coordinatore.
⭐ **E l'anello del tocco nel frattempo aveva fatto la cosa giusta**: ha verificato la cucitura, ha
**dichiarato il ripiego nel registro** e ha disegnato un puntatore suo — invece di tacere o di
rompersi. Il ripiego sparisce da sé adesso che la riga c'è.

⚠ ⭐ **Cinque cuciture rotte su cinque erano FRA due pezzi, e nessuna dentro uno.** È la lezione di
`fasi/rapporti/F5-desktop-vero.md` verificata cinque volte in una fase sola.

---

#### ⭐⭐ A10 — il metro dell'anello **input → vetro**

| | |
|---|---|
| ⭐ **la certificazione** | **16 guasti innestati accusati su 16** · **53 controlli su 53** (uscita 0) · di cui il ponte **19 su 19** |
| ⭐ **tre guasti NUOVI**, che alla fase 3 non erano nemmeno esprimibili | e il più importante è *«la mediana sale di N ma **nel tratto sbagliato**»*: ⛔ **un metro così non diventa mai rosso — dice bugie sulla diagnosi**, che è esattamente quel che è successo all'etichetta del disegno |
| ⭐ **la catena in UNDICI tratti** (quattro nuovi) | provata sul finto che li somma al totale con scarto **0,00 ms** |
| ⛔ **e il numero NON c'è: `n = 0`, uscita 3** | *«non ho niente da giudicare»* — ⭐ **e dirlo è la cosa giusta**: il client non manda ancora §7.3. È il difetto che il validatore della fase 1 aveva (conforme e «niente da giudicare» con lo stesso codice d'uscita), qui evitato per costruzione |
| ⭐ **i pezzi ciechi sono DUE, non uno** | quello in uscita (16-40 ms, noto) e ⭐ **quello in INGRESSO** — `[?]` **4-12 ms** fra la mano e `event.timeStamp` — **che nessuno aveva mai nominato** |

⛔ **E il suo controllo di precondizione ha dato un FALSO VERDE**: cercava `0x0101` in `pagina.html`,
ne trovava cinque, ed erano **tutti commenti**. ⚠ *Pagata dentro il banco che esiste per non pagarla.*

---

#### ⭐⭐⭐ O2 — IL NUMERO C'È: **~140 ms fra la mano e il pixel**, e sono **due giri che concordano**

*14 agosto 2026, pomeriggio. Rapporto in `rapporti/F4-O2-anello-input.md`.*

`[M]` **139,40 ms** (n = **326 su 326**) e **141,60 ms** (n = **322 su 322**), due giri indipendenti
che concordano entro **2,2 ms** · p95 **190-195** · p99 **200-232**. ⛔ **Il tetto è 50 ms: si sfora
di quasi tre volte.** Coi due pezzi ciechi dichiarati: **160-193 ms sullo schermo di un utente, più
la rete.** ⚠ E sul prodotto di un'ora prima — senza la cura di O1 in `src/figlio.c` — erano
**151,17 ms** (n = 573).

⭐ **E la scomposizione dice che NESSUN TRATTO DOMINA** — la tesi 1 del mandato è **refutata**:

| tratto | ms | | tratto | ms |
|---|---|---|---|---|
| **5** cattura → primo byte *(codifica compresa)* | **30,4** | | **4** la scena disegna → cattura | **16,2** |
| **3** la scena riceve → disegna | **26,6** | | **1a** evento → il prodotto lo vede | **13,1** |
| **2** byte usciti → la scena riceve | **26,0** | | **8** la decodifica **vera** | **0,75** |
| **9** richiamo → 1° `drawImage` *(l'ATTESA)* | **25,6** | | **10** 1° → 2° `drawImage` *(il disegno VERO)* | **0,08** |

⇒ I **sei** tratti maggiori valgono fra **13,1 e 30,4 ms** e fanno il **99 %**: curarne uno solo
toglie al massimo il **22 %** del ritardo, e il tetto resterebbe sforato di due volte e mezzo.
⚠ La codifica sta **dentro** il tratto 5 e vale **5,3 su 30,4**; la **decodifica** vale **0,75 ms**:
«il collo di bottiglia è la codifica» resta falsa, e adesso con un numero sotto.
⭐ **E la scomposizione è ripetibile quanto il totale**: nessun tratto si sposta di più di **1,6 ms**
fra i due giri.

⭐⭐ **E i tratti che il metro della fase 3 NON attraversava** (1a + 1b + 2 + 3) valgono **65,8 ms**,
cioè **il 47 %**: ⛔ *il numero della fase 3 non vedeva quasi metà del ritardo che l'utente sente.*

> ##### ⛔⛔ E IL DIFETTO PIÙ GRAVE NON È UN TRATTO: È UNA CODA CHE CRESCE
> `[M]` il server consegna **39,6** fotogrammi/s, la pagina ne dipinge **34,7**, e ⛔ **nessuno
> butta l'avanzo** (`scartati_ordine` 0 · `trattenuti` 0 · `corti` 0). ⇒ Il ritardo cresce di
> **+108 ms al secondo**: 31,6 ms dopo 1 s → **4 650 ms dopo 43 s**. **Dopo un minuto l'utente
> comanda un desktop che ha visto sei secondi fa, e tutti i contatori sono verdi.**
> ⭐ **Curato** in `src/pagina.html` (ancora `F4-CODA-DEL-DECODIFICATORE`): si salta **il disegno**,
> non la decodifica — nessun buco, nessuna chiave. `[M]` dopo: pendenza **−2 ms/s**, ritardo **1,3
> ms** dopo 41 s.

> ##### ⛔ E LA TESI 2 — *«il ritmo è quanto ci consegna Mutter»* — **REFUTATA in questo regime**
> `[M]` quattro conti nella stessa finestra di 30 s: la scena disegna **59,99/s**, Mutter ce ne
> consegna **30,84** (il 51 %), il server ne spedisce **30,54**, la pagina ne dipinge **30,6** —
> ⭐ e le **attese a vuoto sono 0,00/s**: ogni volta che abbiamo chiesto un fotogramma ce n'era già
> uno pronto. ⇒ **Non stiamo aspettando Mutter: il limite è nel nostro ciclo.**
> ⚠ `[?]` I 10,8/s che l'utente ha misurato dal suo video sono su un desktop **vero**, cioè in
> regime di scarsità: le due misure rispondono a due domande diverse.

> ##### ⛔⛔ E LA TESI 3 (tastiera contro mouse) NON È CHIUSA — ⭐ e a dirlo è **la scomposizione**
> `[M]` ultimo giro: **35 sonde chiuse su 296**, mediana **151,7 ms** contro i **141,6** del mouse
> nello stesso giro. ⚠ Verosimile: *«la tastiera è 10 ms più lenta»*. ⛔ **È falso**, e la prova è
> che la sua scomposizione **non è fisica**: `2 byte usciti → la scena riceve` = **−562,8 ms**,
> negativo. ⇒ L'accoppiamento prende il fotogramma sbagliato, e **il totale da solo non lo direbbe
> mai**: è il **guasto n. 12 della certificazione di A10** visto dal vivo.
> ⇒ ⛔ **Il numero non è stato pubblicato.** Serve un eco della tastiera che non si sovrascriva
> (lavoro mio su `04-b30-scena.c`).

⭐ **Quel che invece è `[M]` e regge: il cammino della tastiera arriva al compositore** — `Escape`
mandato dal canale del prodotto **chiude la Panoramica di GNOME**, quattro volte su quattro,
verificato nei pixel; e la scena riceve **744** eventi di tastiera in un giro.

⭐⭐ **E Q6 — il controllo del ramo d'ANDATA, che alla fase 3 non poteva esistere — PASSA sul ferro**:
iniettando 30 ms il totale sale di **30,84** e il surplus compare **tutto nel tratto 2** (+33,49) e
**in nessun altro**. ⇒ Metà dell'anello che non aveva nessuna taratura adesso ce l'ha.
⛔ Q5 (ramo di ritorno) resta rosso **per 0,2 ms**: il surplus sta nel tratto giusto (+24,70 contro
N = 25) ma il totale sale di 20,78. ⚠ **La tolleranza non è stata allargata.**

**⛔ E i tre difetti che tenevano `n = 0` erano tutti del banco o del contorno, nessuno del canale:**

| | |
|---|---|
| ⛔⛔ **la Panoramica di GNOME** | una sessione headless appena nata si apre in Panoramica: la scena «a schermo intero» era **una miniatura a 0,79** e la Panoramica teneva il fuoco. ⇒ `eventi_puntatore = 0` (diagnosi suggerita: «`libei` non consegna») **e** 0 marche lette su 966 (diagnosi suggerita: «l'eco non si legge»). ⭐ **A trovarlo è stato guardare l'immagine**, non leggere un numero |
| ⛔ **`04-b30-scena.c`: `oy` sommato due volte** | le celle della **seconda** marca finivano fuori dalla loro zona di quiete, sullo sfondo del desktop. Sulla marca 1 (`oy = 0`) non si vedeva. ⭐ E la certificazione era verde 53 su 53: **i sedici guasti si innestano nel verbale, e nessuno dipinge un pixel** |
| ⛔ **il controllo di precondizione di A10, falso ROSSO** | cercava i ganci in `figlio.c`; stanno in `webtransport.c` (il canale è del **padre**). ⚠ Stamattina lo stesso controllo aveva dato un falso **verde**: adesso guarda tutt'e due i lati del confine |

---

#### ⭐ A5 — la tastiera: **26 prove, 0 rosse** `[M]` 14 agosto 2026

Identiche in locale e nel contenitore (`xkbcommon` 1.7.0 su tutt'e due). Si ricontrolla con
`bash banchi/04-b25-lancia.sh` — ⭐ **senza sessione, senza `libei` e senza nessuna porta**.

| | |
|---|---|
| ⭐ **il metro è la lettera che ESCE** | non il codice che parte: il banco simula il compositore su una `xkb_state` costruita da sé e **legge il carattere** |
| ⭐ **e ha un controllo negativo** | tasto 26 **senza** Maiusc ⇒ `è`, non `é`. Senza di lui, un simulatore compiacente avrebbe dato verde anche a chi dimentica i modificatori |
| **le tre prove che `PIANO.md` nomina** | `é` su `it` ⇒ `42+26`, esce `é` · `é` su `us` ⇒ ⛔ **niente**, e la riga nel registro · `@` per due strade: `100(AltGr)+16` su `it`, `42(Maiusc)+3` su `us` · emoji e `中` non producibili ovunque |
| ⭐ **il banco è CERTIFICATO** | tre implementazioni sbagliate apposta, e il lanciatore pretende **ROSSO sulla prova giusta**: quella che manda `e` al posto di `é` è rossa |
| **il ripiego non è silenzioso** | `[M]` `xkbcommon` 1.7.0 **non ripiega da sé** (ritorna NULL), e `tastiera_disposizione()` dice `it [Italian]` ⇒ un ripiego entrato da altrove si leggerebbe nel registro come `it [English (US)]` |

⛔ **E tre misure hanno cambiato il codice** — cioè il banco ha lavorato:

| | |
|---|---|
| ⛔ **evdev 84 non esiste** | la prima stesura sceglieva per l'AltGr italiano un codice che **non è in `linux/input-event-codes.h`** (c'è un buco fra 83 e 85). ⚠ **Il banco era VERDE**: dal lato che riceve quel codice funziona. Trovato **guardando il numero**, non dal banco. Ora esce `100` |
| **`de(neo)`** | `√` vuole `100+43+17`, e il terzo livello lì è il tasto **43**, non il `100` che v1 aveva scritto a mano. ⭐ E la stessa misura risponde alla domanda implicita del contratto: **quattro posizioni bastano**, il caso peggiore ne usa tre |
| il Maiusc | usciva **destro**; ora sinistro |

#### ⛔⛔ E il contratto della tastiera era SBAGLIATO — il rifiuto è stato accolto

*`src/tastiera.h` diceva: «la disposizione è la stringa negoziata all'attacco». L'anello l'ha
attuata, ha visto che funzionava, **e l'ha rifiutata lo stesso** — con la ragione giusta.*

⛔ **Non scegliamo noi la disposizione della sessione: la sceglie GNOME, e `libei` ce la CONSEGNA**
col dispositivo tastiera. Il danno, in concreto — sessione `it`, client che ha negoziato `us`,
l'utente scrive `[`:

| | |
|---|---|
| su `us` | `[` sta sul tasto **26**, da solo |
| su `it` | sul tasto **26** c'è la **`è`**, e `[` vuole l'AltGr |

⇒ Mandiamo `26` e sullo schermo compare **`è`**: ⛔ non un carattere *mancante* — **un carattere
DIVERSO**, che `RCP.md` §7.3 vieta. E nessuno collegherebbe il sintomo alla disposizione.
⚠ **E rende falsa una riga che credevamo vera**: `DECISIONI.md` §5-bis.7 dice che la degradazione è
morbida — *«mai caratteri sbagliati, al massimo un paio di accenti irraggiungibili»*. È vero **solo**
usando la keymap della sessione.
⭐ **E v1 lo faceva già così** (`fondamenta/remotix-c/src/tastiera.c:69`): è l'unico pezzo di v1 che il primo
contratto di V2 non aveva ripreso.

⇒ ✅ **Accolto il 14 agosto 2026**: `tastiera_apri_da_keymap()` è in `src/tastiera.h`, e
`input_apri()` **non** prende la disposizione — la keymap arriva da `libei` dentro `input.c`, a ogni
`DEVICE_ADDED`.

---

### ⛔ Che cosa NON ha funzionato

⏳ *si riempie anche quando fa una brutta figura.*

---

### Le decisioni prodotte

⏳ *le decisioni stanno in `DECISIONI.md` una sola volta: qui si **rimanda**.*

---

### Che cosa resta [?]

Aperte all'apertura della fase, e vanno **misurate prima di essere credute**:

1. ~~chi decide la misura del monitor ora che non la dà più la sessione~~ ⇒ ✅ **CHIUSA il
   14 agosto 2026, e la risposta era un'altra da quella che la domanda supponeva**: ⛔ **non la
   decide `RecordVirtual` — la decide il NOSTRO formato PipeWire** `[R]`. E la promessa della tela
   concessa **oggi nessuno la mantiene**: `[M]` client a 1280×720 ⇒ il server la concede, il palco
   cattura a 1920×1080 (costante di compilazione), `rcp` rifiuta ogni fotogramma — **145 prodotti,
   0 spediti, client nero senza errori**. ⏳ La cura è lavoro della fase 6 (`RCP.md` §4.5);
2. ⚠ `PIANO.md` **399, 402-404, 591-593** e `STUDI.md` §gnome **108-109, 111-112, 551** dicono che
   `--virtual-monitor` **non è opzionale**: ⛔ sono vere solo per una sessione che deve vivere
   **senza nessuno che la catturi**, e vanno riscritte. *(Righe individuate da A1, non toccate da
   lui: si riscrivono a codice fermo.)*
3. `[?]` la Keyboard Lock su **DeX**, e la PWA su **Chrome per Android** (`SPECIFICHE.md` §7.3-bis);
4. `[?]` il segno della rotella sugli **altri quattro** compositori (`RCP.md` §7.3);
5. ⭐ **CHIUSA il 14 agosto 2026 — la persistenza al distacco REGGE**, e la tesi del difetto è
   **falsa**: il monitor non sparisce (sempre 1, anche senza nessuno), l'applicazione lavora
   (1 160 righe in 240 s senza un buco), `libmutter` non scrive asserzioni nuove, e al riattacco
   si ritrova **la stessa finestra** (pid invariato), due volte di fila. ⚠ **Ma il palco muore col
   FIGLIO, non con la sessione**: chi congederà un figlio che gira a vuoto toglierebbe il monitor a
   una sessione viva — ⏳ **fase 5**;
6. ⛔ **aperta il 14 agosto, e nessuno l'aveva posta**: se la sessione ha `us` e il client ha
   negoziato `it`, **chi cambia la disposizione della sessione?** `DECISIONI.md` §5-bis.7 dice che
   si rinegozia all'attacco — ⚠ ma un client `libei` **non può imporre una keymap all'EIS: la
   riceve**. ⇒ O la si cambia dalla sessione (`org.gnome.desktop.input-sources`, prima di
   attaccare), oppure §5-bis.7 va riscritta come *«il client **dichiara**, il server **si adegua a
   quel che trova**, e lo dice»*. `[?]` — nessuno l'ha misurato.

---

### Il giudizio dell'utente — ⭐ DATO il 14 agosto 2026

> ### *«Mi sembra ok.»*
> — l'utente, 14 agosto 2026, dopo aver usato il desktop di `prova` dentro una scheda di Chrome
>
> e, poco prima, sulle due cose che aveva chiesto di ottimizzare:
> > *«La situazione mi sembra migliorata. La comparsa del desktop è più immediata.»*

⭐⭐ **E la fase si chiude qui**, come `PIANO.md` §0.2 impone: *«su una misura giudicata dall'utente,
non su un documento completo»*.

#### ⭐ Che cosa il giudizio ha confermato, e con quale numero accanto

| la sua frase | il numero che le corrisponde |
|---|---|
| *«la comparsa del desktop è più immediata»* | `[M]` **5,11 s → 1,04-1,13 s** (7 giri) — e di quel secondo, **1,00 s è il secondo fisso di §4.4-bis**: ⭐ quel che è nostro sono **34-124 ms** |
| *«mi sembra ok»* (dopo qualche minuto d'uso) | `[M]` il ritardo **non cresce più**: pendenza da **+108 ms/s a −2 ms/s**, e **1,3 ms** dopo 41 s |

#### ⛔ E i limiti del giudizio, scritti PRIMA che lo desse e non dopo

*Gli sono stati messi davanti in tavola prima della prova — «un giudizio dato senza sapere che cosa
manca è un'approvazione al buio», la stessa regola con cui ha chiuso la fase 2.*

| | |
|---|---|
| ⛔ **il ritardo SFORA** | `[M]` **139,40 ms** (n=326) contro un tetto di **50**. ⚠ Ha giudicato **con gli occhi**, non su quel numero — e i due non si sostituiscono |
| ⛔ **nessun tratto domina** | sei tratti da ~25 ms: **nessuna cura singola** porta 140 a 50. È lavoro della **fase 8**, e va detto perché il giudizio non venga letto come «il ritardo è a posto» |
| ⛔ **la tela non è la sua** | il suo schermo è **21:9**, il desktop remoto **16:9** ⇒ `[M]` dal suo video, **il 36 % dei pixel è banda nera**. Ha giudicato una finestra, non uno schermo pieno |
| ⚠ **un browser solo** | **Chrome 151**. Safari, iPhone e DeX restano `[?]` **dichiarate, non dedotte** |
| ⚠ **qualche minuto, non qualche ora** | i tre orologi della sessione sono della **fase 5**: l'abbandono lungo non è stato giudicato |

#### ⭐⭐ E il giudizio dell'utente ha trovato SETTE difetti che nessuno dei dieci banchi vedeva

*Non è un aneddoto: è il conto della giornata, ed è la ragione per cui il piano fa chiudere le fasi
così.*

| che cosa ha detto | che cosa c'era sotto |
|---|---|
| *«se il server non mostra il desktop, a che serve REMOTIX?»* | il monitor aggiunto e vuoto — **due fasi** l'avevano preso per uno sfondo |
| *«non si vede nessun desktop»* | **due server nostri** che montavano un monitor a testa sulla stessa sessione |
| *«lo schermo appare strano»* | la dichiarazione delle scorciatoie che copriva il **38 %** della finestra |
| *«non vedo il drawer di gnome»* | la barra piazzata **esattamente dove GNOME tiene il dock** |
| *«il puntatore sembra catturato… studia XPRA»* | ⭐ `SPECIFICHE.md` §7.1 che contraddiceva §7.5: la cattura **non comprava niente** |
| *«niente desktop»*, due volte | il figlio che tiene per sempre **un palco fallito** |
| *«il tempo fra login e desktop è troppo lungo»* | ⛔ **una riga del coordinatore**: `poll()` su due descrittori e `pf.revents` mai guardato |

⛔ **Sette su sette stavano FRA i pezzi, nessuno dentro uno** — ed è la lezione di
`fasi/rapporti/F5-desktop-vero.md` verificata sette volte in una giornata sola.

---

### ⭐⭐ Il numero della fase — `[M]` 14 agosto 2026

*L'anello **input → vetro**, che alla fase 3 non era misurabile: il campo `input` valeva 0 in 953
fotogrammi su 953, perché il canale non esisteva.*

| | |
|---|---|
| ⭐ **il numero** | **139,40 ms** (n = 326 su 326) e **141,60 ms** (n = 322 su 322), ⭐ **due giri indipendenti che concordano entro 2,2 ms** |
| ⚠ **coi pezzi ciechi** | **160-193 ms** sullo schermo dell'utente, **più la rete** |
| ⛔ **contro il tetto** | **50 ms**. Si sfora di quasi **tre volte**, e si scrive com'è |

#### ⭐ La scomposizione, e la risposta a «che cosa ottimizzo?»

| tratto | mediana |
|---|---|
| cattura → primo byte | **30,4 ms** |
| la scena riceve → disegna *(è il desktop remoto, non noi)* | 26,6 |
| byte → scena | 26,0 |
| richiamo → primo `drawImage` | 25,6 |
| disegno → cattura | 16,2 |
| decodifica | 0,75 |
| ⭐ **il `drawImage` vero** | **0,08** |

⇒ ⛔ **Nessun tratto domina**: sono sei tratti da ~25 ms. **Nessuna cura singola porta 140 a 50.**
⭐ La somma dei tratti fa **139,08** contro un totale di **139,40** — scarto **0,32 ms**: la
scomposizione è completa, non ha buchi.
⭐⭐ **E i tratti che il metro della fase 3 NON attraversava valgono 65,8 ms, il 47 %**: metà del
ritardo vero stava fuori dal vecchio metro.

> #### ⭐⭐ E la prova sul ferro che l'etichetta corretta stamattina era giusta
> Il **primo** `drawImage` costa **25,6-27,1 ms**, il **secondo 0,080** ⇒ **320-339 volte**.
> ⛔ *Il disegno non è mai stato caro: era l'attesa del fotogramma dalla GPU.*

---

### ⭐⭐ Le due ottimizzazioni chieste dall'utente — e tutt'e due erano NOSTRE

#### 1. Il login → desktop: **5,11 s → 1,04-1,13 s**

⛔⛔ **E la causa era una riga del coordinatore, scritta la mattina stessa.** Per far arrivare
l'input più in fretta era stato messo il descrittore di `libei` nello stesso `poll()` del figlio —
⛔ ma il codice dopo **non guardava `pf.revents`**: svegliandosi per `libei`, il figlio andava lo
stesso a leggere il socket del padre, **bloccante**.
⇒ *Una modifica fatta per risparmiare millisecondi sull'input costava **quattro secondi** al login.*
⭐ **La cura è una riga**: `if (!pf.revents) break;`

⚠ **E il registro lo diceva già**: *«0 fotogrammi consegnati, **0 attese a vuoto**»* — zero attese a
vuoto vuol dire che il ciclo **non aveva nemmeno provato** a catturare. ⛔ Era scritto, ed è stato
letto due volte come «la scena è ferma». *Il difetto ha resistito a due sonde leggere che davano
risposte opposte: l'ha chiuso solo un debugger attaccato al processo.*

#### 2. ⭐⭐ E il ritardo CRESCEVA senza limite, con tutti i contatori verdi

`[M]` il server consegnava **39,6 fotogrammi/s**, la pagina ne dipingeva **34,7**, e **nessuno
buttava l'avanzo**: `scartati_ordine 0 · trattenuti 0 · corti 0`.

| | |
|---|---|
| la crescita | ⛔ **+108 ms al secondo** |
| dopo 43 s | ⛔ **4 650 ms** — si comandava un desktop visto **sei secondi prima** |
| ⭐ curato | pendenza **−2 ms/s**, ritardo **1,3 ms** dopo 41 s |

⇒ ⛔ **È il difetto che l'utente sentiva e che nessun contatore contava**: tutti verdi, e la coda del
decodificatore che si allungava e basta.

#### ⭐ E i due difetti che potevano rovinare una macchina vera

| | prima | dopo |
|---|---|---|
| il registro a raffica | **151,9 MB/s** (⛔ `[M]` **30,8 GB** scritti in una mattina) | **284 B/s** |
| un nucleo bruciato a vuoto | **1,00** | **0,00** |
| il desktop dopo che la sessione grafica torna | ⛔ **non tornava mai** | ⭐ **1,11 s, stesso figlio** |

⚠ ⭐ **E il ciclo a vuoto ha DUE facce, e una è MUTA**: per questo il banco misura il registro **e**
la CPU. E con un client muto **un difetto ne nasconde un altro** — serve un client che *chieda le
chiavi*, come fa un client vero che non vede niente.


---
---

## ⭐⭐ LA CODA DELLA FASE 4 — 15 agosto 2026, la notte in cui la tela è diventata la finestra

*Questa fase è stata giudicata «mi sembra ok» il 14 agosto sera, ⛔ ma il suo mandato
(`fasi/rapporti/F4-IN-12-mandato-prossima-sessione.md`) diceva **«a lavoro riuscito ma non
finito»**: mancava un pezzo solo, `figli_ritela()` → `cattura_ridimensiona()`, e da lì dipendevano
quattro sintomi che l'utente vedeva sull'input e sul video.*

⛔ **E questa coda NON è la fase 6**, anche se ne tocca il contenuto: il numero della fase lo dà il
**perché si è fatto il lavoro**, non l'elenco delle cose prodotte. Qui si è fatto per **curare il
mouse e il ritardo dei clic**, cioè per finire la fase 4 — e infatti tutti i rapporti della notte si
chiamano `F4-IN-*`. ⚠ La fase 6 resta **aperta**: `PIANO.md` dice quali sue parti si trovano già
fatte e quali no.

⚠ **E vale la riserva di forma di questo documento**: queste righe sono scritte **alla chiusura**.
⭐ Le misure però non sono ricordate: ognuna viene da un registro del server o da un giro di banco,
con l'ora accanto.

### Che cosa doveva produrre questa coda

Il mandato di `F4-IN-12` §1, in una riga: **scrivere la catena `figli_ritela()` →
`cattura_ridimensiona()`**, quella che porta la misura chiesta dal client dal filo fino al
compositore.

⭐ **E vale più di quanto sembri perché chiude QUATTRO sintomi, non uno** — tutti e quattro nascono
dalla stessa cosa, *la misura della tela non la chiede nessuno*:

| sintomo | perché sparisce |
|---|---|
| le bande nere laterali | le due tele combaciano ⇒ niente da impaginare |
| il testo interpolato | scala **1** ⇒ nessuno ricampiona l'immagine |
| il ri-attacco a misura diversa | la tela si cambia a caldo |
| ⭐⭐ i 4 secondi fra login e desktop | riavviare il flusso **consegna un buffer** |

**Che cosa l'utente vede e giudica**: il desktop remoto riempie la finestra del browser, **senza
bande nere e senza testo sfocato**, ritrova la sua misura quando si riattacca, e **risponde al
clic** invece di farsi aspettare.

---

### Il banco

⛔ **Scritto DOPO la prima stesura del codice, non prima** — e va detto: la regola di §0.2 vuole il
banco per primo. Quel che ha retto al posto suo è stato il mandato **avversariale** a quattro agenti
(§«che cosa non ha funzionato»), che ha trovato dieci difetti prima che il banco esistesse.

| | |
|---|---|
| `banchi/04-b31-tela.c` | monta `rcp.c` **nudo**, con un palco finto che si può far rispondere in ritardo, concedere un'altra misura, o non rispondere affatto. **19 casi**, ciascuno con l'atteso dichiarato prima (⭐ il 19° aggiunto il 16 agosto 2026, vedi §05-la-sessione §6-ter) |
| `banchi/04-b31-certifica.sh` | ⭐ **il controllo positivo**: innesta **12 guasti** in una copia di `rcp.c` e pretende che diventino rossi **i casi attesi** — non «che diventi rosso qualcosa» |

⛔ **E il banco è stato corretto due volte dalla misura, non il contrario**: l'atteso di G1 diceva
dieci casi e ne ha accesi sei; G9 restava verde perché un **secondo** controllo mascherava il guasto
innestato nel primo. Tutt'e due scritti accanto al guasto, con la ragione.

⚠ **Quel che questo banco NON prova, dichiarato**: non prova che il compositore ridimensioni
(quello è `[M]` di `banchi/04-in8-misura.c`), non prova che i pixel siano giusti (qui non c'è un
pixel), non prova la pagina. Prova la sola cosa che sta in mezzo, e che nessun banco guardava: **che
a ogni `ADATTA_TELA` risponda esattamente un `TELA`, e che la tela in vigore non prenda mai un
valore che nessuno ha concesso.**

---

### Che cosa è stato sviluppato

| file | che cosa |
|---|---|
| `src/cattura.c` · `.h` | `cattura_ridimensiona()` (l'esito è la RICHIESTA, non il cambio), `cattura_risveglia()`, `cattura_misura_negoziata()`, i quattro parametri di consumo in un posto solo, la guardia sulla geometria incoerente |
| `src/figlio.c` · `.h` | `figli_ritela()`, il ramo `RITELA`, **la riconciliazione sul fotogramma** (codificatore riaperto, puntatore rimappato, chiavi tenute buttate), `MSG_TELA` — la risposta al padre —, la tela *voluta* per il rimontaggio, l'attesa che cresce sul codificatore |
| `src/rcp.c` · `.h` | i ganci `ritela` e `tela_del_palco`, `rcp_tela_dal_palco()` (tre casi), `tela_richiama_il_palco()`, il fondo di §7.1, i limiti di §4.5 per lato, il tetto `video.misura_massima` anche su `ADATTA_TELA` |
| `src/webtransport.c` · `.h` | il ponte dei due ganci, la tabella delle tele dei palchi per utente |
| `src/main.c` | le due cuciture, e `wt_palco_dimentica()` alla morte del figlio |
| `src/mutter.c` · `.h` | `mutter_scala_nostra()` — la scala del **nostro** monitor logico |
| `src/pagina.html` | `chiedi_tela()`, `tela_da_chiedere()`, l'interruttore `?adatta=`, il bersaglio, i limiti per lato, e tre correzioni al lettore dei fotogrammi |
| ⭐ `src/Contenitore` · `src/costruisci-in-contenitore.sh` | **come si costruisce**, che era il blocco dichiarato di `F4-IN-12` §3 |

---

### Le misure

Tutte sulla macchina di prova (`192.168.0.2`, NIC-OS, GNOME headless), utente `prova`, client
Chrome. ⚠ L'orologio di quella macchina è **indietro di due ore** rispetto a quello del portatile:
le ore qui sono le sue.

| che cosa | scena | atteso | misurato | data |
|---|---|---|---|---|
| tela concordata all'attacco | finestra 1265×800 | la misura della finestra | **1264×800** (pari, troncata in giù) | 15 ago |
| ⭐ dal canale video al primo fotogramma | login, desktop fermo | «meno dei 4,4 s del 14 ago» | **311 ms** | 15 ago |
| scala di disegno del client | idem | 1,000 | **1,000**, `imageRendering: pixelated` | 15 ago |
| ridimensionamento a caldo | 1264×800 → 1000×640 | ~41 ms (`[M]` F4-IN-8) | **6 ms** dalla risposta del palco alla chiave spedita | 15 ago |
| ri-attacco a misura diversa | palco a 1264×800, pagina che chiede 1920×1080 | i pixel arrivano subito | `SESSIONE` concede **1264×800** (§4.5), **0 fotogrammi scartati** | 15 ago |
| fotogrammi scartati per misura · trattenuti · errori | sessione intera | 0 · 0 · 0 | **0 · 0 · 0** | 15 ago |
| guardia 2 (la scala del monitor) | montaggio del palco | 1,000 | **1,000** su «Meta-0», e la riga si scrive **anche quando è buona** | 15 ago |
| ⭐⭐ clic → primo fotogramma spedito | 25 clic veri dell'utente, desktop fermo | ≤ 50 ms (`CODER.md` §1-bis) | ⛔ **136 ms** (peggiore 502) → dopo la cura **41 ms** (peggiore 47) | 15 ago |
| il giro completo, misurato dalla pagina (`GIRO`) | 10 clic, portatile su rete locale | — | **55 ms**, peggiore 71 (era 135 dal DeX il 14 ago) | 15 ago |
| il banco | `04-b31` | 18 verdi | **18 verdi**, e **11 guasti su 11** visti | 15 ago |
| ⛔ **e il 16 agosto era 11/18** | `04-b31` | — | l'atteso di sette casi non contava la richiesta della nascita di `477d708`. ✅ **19/19 e 12 guasti su 12**, col caso 19 a guardia della cura | 16 ago |

⭐ **E la misura che non viene da noi**: GNOME *Impostazioni → Displays*, **dentro** la sessione
remota, dichiara **«Resolution 1264 × 800 (3:2)»** e **«Scale 100%»**. È il compositore che dice la
misura che gli abbiamo chiesto.

---

### ⛔ Che cosa NON ha funzionato

#### I dieci difetti trovati refutando la cura appena scritta

Quattro agenti, mandato **avversariale** («parti dall'ipotesi che sia falsa»). ⭐ Tre affermazioni su
quattro sono state smentite, e **otto dei dieci difetti erano nati quella notte insieme alla cura**.
L'elenco per intero è in `fasi/rapporti/F4-IN-13-la-tela-che-cambia.md` §3. I quattro che avrebbero
fatto danno:

1. una **lettura oltre la memoria copiata** quando la tela si allarga (la guardia copriva un verso
   solo dei due);
2. il **`TELA` non richiesto**, che per §6.2 fa **chiudere una sessione sana**;
3. **due `ADATTA_TELA` incatenate**: il fotogramma della prima preso per la risposta della seconda,
   e il desktop assestato sulla misura sbagliata **con i conti dei messaggi in ordine**;
4. il ritorno a una misura **già stata in vigore**, che chiudeva la sessione di chi trascina un
   bordo e lo rimette dov'era.

#### ⛔⛔ E il difetto che ha trovato l'UTENTE, non il banco

*15 agosto, mattina, con queste parole: «su Android il mouse dà problemi: non prende più i click».*

Erano **due sue sessioni che si contendevano il palco**: il portatile staccato per silenzio aveva
perso il posto **ma continuava a pretendere la sua misura**, il telefono pretendeva la propria, e il
palco rimbalzava fra 2544×926 e 2560×926 **diciassette volte al secondo**. Ogni giro riavviava il
flusso, e Mutter ricreava i dispositivi di `libei`: `[M]` **640 «ricambi»** del puntatore, e la
regione dell'input mai d'accordo con la tela. ⇒ I clic partivano, arrivavano, venivano iniettati — e
finivano altrove.

⭐ La cura è l'invariante che c'era già: **I2 — chi non ha il posto guarda, non comanda**. Una riga.
⛔ E la mia difesa dell'attesa che cresce **non bastava**, per una ragione che vale più della cura:
si azzerava ogni volta che il palco arrivava dove *quella* sessione lo voleva, cioè a ogni giro del
ping-pong. **Un fondo temporale cura un padrone insistente, non due padroni.**

#### ⛔ Il quarto di secondo su ogni clic, e il numero che stava nel registro da un giorno

Il ciclo del figlio aspettava un fotogramma fino a **250 ms**, e in quell'attesa non leggeva il
socket del padre. `[M]` 136 ms di mediana sui clic veri. ⭐ E la causa era stampata **una volta al
secondo** in una riga scritta per un'altra domanda: *«3 attese a vuoto»* = quattro giri al secondo =
250 ms per giro. È la seconda volta in due giorni che il registro aveva già il fatto
(`LEZIONI.md` §6.2-ter).

#### Le tre cose che ho sbagliato di metodo, e che il banco ha corretto

- l'**atteso di G1** dichiarava dieci casi rossi e ne ha accesi sei;
- **G9 restava verde** perché un secondo controllo mascherava il guasto innestato nel primo;
- il **caso 18** non riproduceva la scena vera finché non ha avuto **due** sessioni: con una sola, il
  posto se lo riprendeva da sé e il difetto non compariva.

---

### Le decisioni prodotte

- `DECISIONI.md` **§5.0-sexies** — attuata per intero, con le misure della notte, le tre guardie
  chiuse e i quattro tempi (`RCP_TELA_ATTESA_MS`, `RCP_TELA_RICHIAMO_MS`, `TELA_FONDO_MS`,
  `RISVEGLIO_MS`);
- `DECISIONI.md` **§5.1** — vale **durante** la sessione, non all'attacco: l'inseguimento della
  finestra sta dietro `?adatta=segui`, spento di suo (I6). ⛔ **E il 17 agosto 2026 è uscito del
  tutto** — `DECISIONI.md` **§5.1-bis**, decisione dell'utente: *«non voglio mettere delle
  eccezioni nel progetto»*. Durante la sessione la tela non si tocca, e non c'è più interruttore;
- `SPECIFICHE.md` **§6.4** e `RCP.md` **§7.1** — corrette: *«mai come automatismo»* non è più vero
  all'attacco, e il perché è scritto con la data;
- `LEZIONI.md` **§7.5** (una deduzione al posto di un messaggio), **§6.2-bis** (un'attesa che
  protegge un anello è un ritardo per gli altri), **§6.2-ter** (il numero è già nel registro).

---

### Che cosa resta `[?]`

| | |
|---|---|
| ⏳ **la riga che manca a `RCP.md` §7.1** | che cosa fa il server quando il palco cambia misura **da sé**. Oggi lo richiama e non manda nessun `TELA` — funziona, ma è una regola del prodotto che l'arbitro non nomina |
| ⛔ **il banco del riattacco che BATTE UN TASTO dopo** | `PIANO.md` lo chiede per questa fase. `[M]` si è visto nel registro che `libei` ricrea i dispositivi al cambio di geometria e che `input.c` li riaggancia, ⛔ **e l'utente ha scritto in un terminale dopo un riattacco** — ma un banco che lo provi non c'è |
| ⛔ **il ripiego su KWin dichiarato nel registro** | `PIANO.md` lo chiede per questa fase e **non è verificabile**: KDE è la fase 11, e su questa macchina non c'è. Il percorso di codice esiste (`COMPOSITORE_INCAPACE`) ed è provato dal caso 11 del banco, **su un ospite finto** |
| `[?]` **il mezzo pixel del `margin: 0 auto`** | quando `clientWidth × devicePixelRatio` è dispari. ⭐ Giudizio dell'utente sul DeX: *«tutto perfetto»* ⇒ **non si presenta**, ma nessuno l'ha misurato |
| ⚠ **i 4 ms di ritardo medio aggiunto** | l'attesa di 8 ms è un **ripiego dichiarato**: la cura vera è un descrittore che la cattura scrive quando il fotogramma è pronto, nello stesso `poll()` del padre e di `libei` |
| ⚠ **il multi-monitor** | `SPECIFICHE.md` §6.5, fuori scopo come funzione |
| ⚠ **i banchi RCP/1 non esercitano la strada nuova** | `01-b3-cliente.py` e `01-b4-validatore.py` restano verdi perché il filo non è cambiato, ⛔ ma nessuno dei due manda un `ADATTA_TELA` |

---

### Il giudizio dell'utente

> **«Funziona. Niente barre nere, il desktop riempie perfettamente la finestra del browser e mouse e
> tastiera funzionano.»** — 15 agosto 2026, dal portatile Linux
>
> **«Sia su Linux sia su Android (DeX) è tutto perfetto. Ci sono i presupposti per chiudere la
> fase.»** — 15 agosto 2026, dopo la cura del ritardo

⭐ E prima, con l'immagine del desktop remoto a schermo intero: **«Questo è linux!»**


---

<a id="05-la-sessione"></a>

## Fase 5 — La sessione

⭐ **Aperta il 15 agosto 2026**, col suo documento e prima di una riga di codice (questo documento).
Il mandato di partenza è `rapporti/F5-IN-0-mandato.md`; il piano è
`PIANO.md` §«Fase 5 — La sessione».

> **La scena che l'utente giudicherà**: *«chiude il client, va a pranzo, riapre — e ritrova tutto
> com'era»*.

⛔ **E il 15 agosto l'utente ha aggiunto quattro punti** che il piano non conteneva, o conteneva
sparsi. Sono il §1 di questo documento, prima del resto, perché due di essi **cambiano l'ordine del
lavoro**: il primo tocca la configurazione del desktop, il secondo apre una decisione di protocollo.

---

### 1 · ⭐ I QUATTRO PUNTI AGGIUNTI DALL'UTENTE

#### 1.1 ⛔ Togliere «Spegni, Riavvia, Sospendi, Iberna» dal menu di sistema del desktop

*Motivo dichiarato dall'utente: un utente collegato da remoto non deve poter «sfilare da sotto il
naso» la macchina agli altri, in remoto o in locale.*

`SPECIFICHE.md` §11.3 lo prometteva già in una riga — *«spegnimento, riavvio, sospensione: **tolti**
alla sessione remota»* — e **nessuna riga di codice la mantiene**.

⭐ **La leva ovvia è quella sbagliata, ed è misurabile nelle fonti che abbiamo in casa:**

| strada | che cosa fa davvero |
|---|---|
| ❌ `org.gnome.desktop.lockdown disable-log-out` | fa sparire Spegni **e** Riavvia — ⛔ **ma fa sparire anche «Esci…»**, e fa rifiutare `org.gnome.SessionManager.Logout` con `GSM_MANAGER_ERROR_LOCKED_DOWN`. Cioè ci porta via **il punto 1.2 dell'utente** *e* il congedo che `sessione.c:789` usa oggi per fermare la sessione |
| ✅ **regola polkit `no`** su `org.freedesktop.login1.power-off`, `reboot`, `suspend`, `hibernate` (e le varianti `*-multiple-sessions`, `*-ignore-inhibit`) | `[R]` `gsm-manager.c`: `CanShutdown = !lockdown && (can_stop ‖ can_restart ‖ can_suspend ‖ can_hibernate)`, e ciascuno dei quattro è vero solo se logind risponde `yes` o `challenge` (`gsm-systemd.c:698-803`). Con tutt'e quattro a `no` ⇒ `CanShutdown` falso ⇒ gnome-shell nasconde **Spegni** e **Riavvia** (`systemActions.js:340-359`), e **Sospendi** cade per conto suo (`loginManager` `CanSuspend`). ⭐ **«Esci…» resta**, perché dipende solo da `disable-log-out` |

⛔ **`no`, mai `auth_admin`**: `"challenge"` **mostra** la voce — vale su GNOME e su KDE
(`STUDI.md` §gnome §5.1, `STUDI.md` §kde §1579). ⚠ E la voce **sparisce**, non si ingrigisce: `system.js:218-226`
lega `can-*` a `visible`.

> #### ✅ E LA PORTATA È DECISA — dall'utente, il 15 agosto 2026
>
> > *«No, nessuno può spegnere, riavviare, mettere in standby o sospensione il server, altrimenti si
> > rischia di "buttare fuori" anche altri eventuali utenti collegati alla macchina.»*
> > *«L'utente collegato a REMOTIX può solo fare espressamente il logout o, ovviamente, operare sul
> > PC che sta utilizzando.»*
>
> ⇒ `DECISIONI.md` §4.7, e `SPECIFICHE.md` §11.3 è stata allargata: **non «alla sessione remota»,
> a tutti**. ⛔ La regola polkit si scrive **piatta**, senza `subject.local`: la discriminante che
> avevo proposto non serve più, e con lei sparisce la misura che sarebbe costata.
>
> ⭐ **Il metro del banco, ed è più forte di «le voci sono sparite»:** *nel menu di sistema del
> desktop remoto resta «Esci…» **e nient'altro** di quella famiglia.*

**Il lavoro, allora — tre cinture, perché le strade sono tre** (`DECISIONI.md` §4.7):

1. **la regola polkit**, piatta, sulle quattro azioni e le loro varianti `*-multiple-sessions` /
   `*-ignore-inhibit`. ⭐ Copre **due strade con una riga sola**, perché guarda l'azione e non
   l'interfaccia: il menu **e** `systemctl poweroff` da un terminale dentro la sessione;
2. **`logind.conf`**: `HandlePowerKey`, `HandleSuspendKey`, `HandleHibernateKey`, `HandleLidSwitch`
   = `ignore` — ⛔ il tasto fisico **non passa da polkit**, e la prima cintura non lo vede;
3. **la sospensione automatica**, che è §2.2 di questo documento: l'`Inhibit` **e**
   `sleep-inactive-ac-type=nothing`. ⚠ Due cinture per **due sintomi**: polkit impedisce il fatto,
   dconf toglie dallo schermo la notifica *«Automatic Suspend»* che l'utente vedrebbe lo stesso.

**E quel che resta da fare bene:**

- ⚠ **sono tutte righe di configurazione, cioè quel che I7 vieta**: vanno **installate da noi** e
  **verificate dopo l'avvio**, come l'headless di `DECISIONI.md` §4.3-bis. ⭐ Qui la verifica non ha
  incognite: si chiede a logind `CanPowerOff` / `CanReboot` / `CanSuspend` / `CanHibernate`
  **dalla sessione dell'utente** e si pretende **`no`**; se risponde `yes` o `challenge`, si dichiara
  il fallimento;
- ⚠ **root resta, e deve restare**: `systemctl --force poweroff` parla con PID 1 e salta logind.
  ⭐ È la strada dell'amministratore, e i client attaccati lo vengono a sapere con
  `SERVER_IN_CHIUSURA 0x0C` — ⭐ già emesso da `main.c:850`, cura del rilievo B-7. ⇒ **questo
  percorso va provato in questa fase**: adesso è l'unico spegnimento legittimo che esista;
- gli altri desktop arrivano con le loro fasi (KDE è la 10): la regola polkit è **la stessa per
  tutti e quattro** — `STUDI.md` §xfce §618 dice che su XFCE non esiste nessuna chiave e restano solo
  polkit e logind — ⛔ ma **si verifica desktop per desktop**, quando la fase arriva.

#### 1.2 ⛔⛔ Chiusura della scheda **contro** «Esci» dal menu: due esiti, e oggi uno solo esiste

> ### ⭐⭐ LA DISTINZIONE, DETTATA DALL'UTENTE IL 15 AGOSTO 2026
>
> > *«Distinguiamo il comportamento del PC usato dall'utente rispetto a quello che fa REMOTIX. Se
> > l'utente chiude, spegne o riavvia il **proprio** PC, questo lo trattiamo come browser chiuso /
> > connessione caduta. Se invece sceglie la voce «Esci/logout», allora significa che l'utente vuole
> > **terminare la sessione**, il che comporta la chiusura di tutti i programmi che aveva in
> > esecuzione.»*
>
> ⭐ **Il PC dell'utente non è mai un caso speciale**, e questo toglie lavoro invece di aggiungerne:
> scheda chiusa, browser chiuso, PC spento, PC riavviato, campo perso in galleria — **un caso solo**,
> quello già misurato. Non c'è niente da rilevare dal lato client e niente da distinguere sul filo.
>
> ⭐ **«Esci/logout» è l'unico gesto che significa «ho finito»**, e la sua conseguenza è dichiarata:
> **i programmi dell'utente si chiudono**. Non è un distacco più forte: è l'altro verso.
>
> ⛔ **E tre cose smettono di essere domande:**
>
> 1. ⛔ **`disable-log-out` è VIETATA.** Toglieva la voce «Esci…» e faceva rifiutare
>    `SessionManager.Logout`: adesso che il logout è una funzione **promessa**, quella chiave
>    toglierebbe la funzione. ⇒ per §1.1 resta **solo** la regola polkit — la strada si è chiusa da
>    sé, senza doverla scegliere. *(Era la domanda 2 di §4, e decade.)*
> 2. **`org.gnome.shell always-show-log-out` va acceso.** `[R]` Senza, su una macchina con un utente
>    e una sessione sola gnome-shell **non mostra** la voce. ⚠ E rovescia
>    `reference-gnome/rapporti/02-shell-blocco-voci.md:214` — *«va lasciata `false`»* — che era
>    scritto quando l'obiettivo era togliere voci, non darne una. *(Era la domanda 3 di §4, e
>    decade.)*
> 3. **Fra il clic e la fine non tocchiamo niente**: se un programma ha lavoro non salvato, GNOME
>    mostra il **suo** dialogo dentro il desktop remoto, come se l'utente fosse al monitor. È I8, e
>    vale anche qui.

| caso | oggi | che cosa manca |
|---|---|---|
| **1 · il filo cade** — scheda chiusa, browser chiuso, ⭐ **il PC dell'utente spento o riavviato** | ⭐ **vivo e misurato**: `pagina.html:2504` aggancia `pagehide` (⛔ non `beforeunload`) e spedisce `CONGEDO 0x01` prima di morire — `[M]` il server l'ha visto arrivare. Il posto si libera, **la sessione sopravvive** (I4, `SPECIFICHE.md` §5.2). ⚠ E quando il PC muore di colpo il `CONGEDO` non parte affatto: allora è l'orologio del **silenzio** a liberare il posto, 30 s (§5.3) — ⭐ **stesso esito, altra strada** | il **banco** che lo provi, e lo provi **due volte di fila** (`LEZIONI.md` §2.3-ter) |
| **2 · l'utente sceglie «Esci…» nel menu del desktop** | ⛔ **non è definito da nessuna parte e non è gestito**: `gnome-session` esce, Mutter muore, il palco cade — e sul filo **non parte nessun motivo**. Il client vede una connessione che si spegne, cioè esattamente la forma di guasto del rilievo **B-7** | tutto quel che segue |

**Quel che il caso 2 richiede, in ordine:**

- **chi se ne accorge**: il figlio sorveglia già l'unità `gnome-session-manager@gnome.service`
  (`sessione.c`, `unita_inattiva()`); qui serve accorgersene **mentre accade**, non chiederlo;
- ⛔ **il motivo deve partire PRIMA che il filo muoia**, ed è la parte che oggi non esiste: quando
  Mutter cade, il palco cade con lui e il canale non serve più a niente. ⚠ È l'ordine, non il
  contenuto, a essere il difetto — la stessa forma del rilievo **B-7**;
- ✅ **il motivo sul filo è `0x10 SESSIONE_TERMINATA`**, aggiunto a `RCP.md` §8.2 il 15 agosto: non
  il riuso di `0x01`, che porta la promessa opposta *«riattacca e ritrovi tutto»*. ⇒ da definire in
  `rcp.h`, da **emettere** in `rcp.c`, e da leggere in `pagina.html` — ⛔ e i tre pezzi vanno insieme,
  o è il rilievo B-7 daccapo;
- ✅ **che cosa legge l'utente**: *«la sessione è terminata»* sopra il **modulo di accesso**
  (deciso dall'utente il 15 agosto, `DECISIONI.md` §4.1-quater). ⛔ Non una schermata di chiusura;
- **la pulizia**: posto liberato, palco smontato, e il prossimo attacco è una **sessione nuova** —
  non un riattacco a un palco morto;
- ⭐ **la seconda strada per lo stesso logout** (`DECISIONI.md` §4.1-quinquies, 15 agosto): la
  scorciatoia **`Ctrl+Alt+Fine`** gestita **dalla pagina** — con `preventDefault()`, la conferma
  *«terminare la sessione?»*, e ⛔ da **aggiungere alla sonda S3** (`banchi/04-b29-scorciatoie.py`,
  42 combinazioni: questa non c'è) e misurare su due motori prima di prometterla. ⛔ **Nessun
  bottone a schermo**: la voce del menu si raggiunge col dito e basta a sé stessa. ⚠ E le due strade
  finiscono **nella stessa** `sessione_termina()`: un solo percorso di uscita, o due che divergono;
- ⚠ **e la nostra `sessione_termina()` resta valida**: chiude con `SessionManager.Logout`, che
  `disable-log-out` avrebbe ucciso (`STUDI.md` §gnome §5.1). ⭐ Vietando quella chiave, il congedo del
  server e il logout dell'utente **passano dalla stessa porta**, e la porta resta aperta.

#### 1.3 Il riattacco da uno schermo di misura diversa — e i compositori

⭐ **Tre quarti sono già fatti e misurati**, ma nella **coda della fase 4** (§04-si-comanda,
`rapporti/F4-IN-13-la-tela-che-cambia.md`): la tela è la finestra, `SESSIONE` concede la tela che il
palco ha già con **zero fotogrammi scartati** `[M]`, e il ridimensionamento a caldo costa **6 ms**.

> #### ✅ ⭐⭐ E IL RIATTACCO A MISURA DIVERSA È STATO MISURATO — 16 agosto 2026, **e l'ha fatto l'utente**
>
> *`banchi/05-b4` dichiara per iscritto di non poterlo provare: «`01-b3-cliente.py` non conosce
> `ADATTA_TELA` (zero occorrenze; la pagina ne ha 45) ⇒ si misura col browser».*
>
> `[M]` Sessione aperta col browser **massimizzato** (`2544x926`), scheda chiusa, riattacco con la
> finestra **ridotta**. La catena intera in **61 millisecondi**:
>
> ```
> 17:11:00.875  ⚠ RIPIEGO DICHIARATO (§4.5): chiesta 1240x622, il palco ha 2544x926
>                 → CONCESSA quella del palco, così i fotogrammi arrivano da subito
> 17:11:00.887  ⭐ ADATTA_TELA 1240x622 GIRATA al palco            (+12 ms)
> 17:11:00.935  ⭐ tela IN VIGORE cambiata da 2544x926 a 1240x622  (+60 ms)
> ```
>
> | | |
> |---|---|
> | fotogrammi dopo il cambio | **62**, tutti a `1240x622` — **zero** alla misura vecchia |
> | CHIAVE alla misura nuova (§5.2) | ✅ `fotogramma 2` |
> | `NON lo spedisco` (il congelamento) · «il palco non è alla tela» (il *ballo*) | **0** e **0** |
> | ⭐ **e quel che ha visto l'utente** | *«il desktop copre per intero lo schermo (che adesso è di dimensioni ridotte)»* · *«funziona»* |
>
> ⚠ **E una trappola del registro, pagata sul posto**: il primo conteggio diceva «1 fotogramma alla
> misura vecchia dopo il cambio». ⛔ Era falso: una riga del registro aveva **perso il timestamp** —
> due processi che scrivono sullo stesso file si erano accavallati — e senza data `$1 >= "17:11:00.935"`
> la prendeva per buona, perché una parola ordina dopo una cifra. ⇒ *Un confronto su un campo che può
> mancare non è un filtro, è una scommessa.*

**Quel che resta a questa fase:**

- ✅ **il tasto e il puntatore DOPO il riattacco a misura diversa** — ⭐ **chiuso il 16 agosto 2026, e
  l'ha chiuso l'utente senza saperlo.** Il timore era misurato: al cambio di geometria **`libei`
  distrugge e ricrea i dispositivi assoluti** (`[M]` 15 ago, *«il puntatore è stato TOLTO dal
  compositore, ricambio n. 640»*), e il puntatore al dispositivo vecchio smette di funzionare **senza
  errore** (`STUDI.md` §gnome §9) ⇒ la prova sarebbe stata **verde per costruzione**.

  `[M]` **E il ricambio è avvenuto davvero**, al ridimensionamento verso `1240x622`:

  ```
  17:11:00.918  il puntatore e' stato TOLTO dal compositore (ricambio n. 1)
  17:11:00.918  il puntatore e' stato TOLTO dal compositore (ricambio n. 2)
  ```

  ⭐ **Un minuto dopo, alla misura nuova, l'utente ha aperto il menu di sistema col mouse e premuto
  «Log Out»** (`17:12:05.742 §7.6: prova ha chiesto di USCIRE`, e la sua schermata mostra il menu
  aperto): un bersaglio piccolo, nell'angolo. ⇒ **I clic finiscono dove punta, dopo il ricambio dei
  dispositivi.** E lo stesso nell'altro verso, verso `2544x926`: `[M]` alle `17:13:09` trenta
  `PUNTATORE` con coordinate fino a `2509`, coerenti con la tela nuova.

  ⚠ **Quel che questa prova NON è**: un banco. È una misura su gesti veri, e vale per Mutter su
  questa macchina. ⇒ Il banco resta desiderabile, ma non è più l'unica cosa che sta fra noi e il
  sapere;
- ✅ **che fine fanno le finestre aperte** quando la tela rimpicciolisce — ⭐ **chiuso dall'utente il
  16 agosto 2026**, e con l'argomento giusto: *«il punto 1 si è chiuso nel momento in cui ho
  riattaccato la sessione con il browser a finestra: se fosse accaduto qualcosa il terminale lasciato
  aperto si sarebbe chiuso»*.

  ⇒ `[M]` La tela è passata da `2544x926` a `1240x622` con un terminale aperto e un `cat /dev/urandom`
  dentro: **la finestra è sopravvissuta, il processo pure** (PID 523560, 2 min 31 s), e il desktop è
  rimasto usabile alla misura nuova — l'utente ci ha aperto il menu di sistema col mouse.

  ⚠ **Quel che resta NON osservato**, e si scrive per non spacciarlo per provato: se una finestra
  **più grande dello schermo nuovo** venga riportata dentro da Mutter o resti tagliata. ⛔ Il
  terminale della prova era piccolo, quindi il caso non si è presentato. È cosmetica, è di GNOME, e
  non blocca niente;
- **la tabella dei compositori**, che è la parte «studia bene i compositori» del punto:

| | ridimensiona a caldo? |
|---|---|
| **Mutter** (GNOME) | ✅ `[M]` — è la strada su cui la coda della fase 4 è stata misurata |
| ⛔ **KWin** | **no fino a `v6.7.4` compreso** — `[R]` verificato su invent.kde.org il 14 ago: il ridimensionamento c'è **solo su `master`**, `Plasma/6.8` **non esiste** e non ha data. Riavviare KWin ucciderebbe la sessione, cioè proprio il distacco che il modello offre ⇒ **ripiego dichiarato** (`DECISIONI.md` §5.0-bis): si tiene la tela vecchia e riscala il client. ⛔ La riga nel registro (`COMPOSITORE_INCAPACE`) esiste nel codice ed è provata **su un ospite finto** — verificabile davvero solo alla **fase 11** (KDE) |
| **labwc** (XFCE, LXQt) | ⚠ e il rischio non è la misura: su **XFCE** `xfsettingsd` è il primo client della sessione e **spegne ogni output nuovo** (`enabled = FALSE`); su **LXQt** non c'è niente di simile (`SPECIFICHE.md` §11.2) |
| **muffin** (Cinnamon) | la riga peggiore, e prima del ridimensionamento mancano `RecordVirtual`, libei e gli appunti |

⭐ **La memoria dell'utente era giusta**: KWin è il caso problematico, e la sua degradazione è
**l'unico punto del modello che non può essere servito**.

#### 1.4 L'utente che ha **già** una sessione grafica attiva

`SPECIFICHE.md` §5.1 li elenca tutti e quattro. Lo stato, oggi:

| situazione | motivo | stato |
|---|---|---|
| remota viva + un **secondo dispositivo** | `0x0F GIA_ATTIVA_REMOTA` | ⭐ **vivo e provato** `[M]`: il registro dei posti in `rcp.c`, e il caso 18 del banco `04-b31` |
| remota **muta da 30 s** + un altro dispositivo | *(entra)* | vivo: `torna_a_parlare()` |
| ⛔ **locale già attiva**, arriva la remota | `0x05 GIA_ATTIVA_LOCALE` | **definito in `rcp.h:45` e MAI EMESSO da nessun `.c`** |
| ⛔ remota viva, **si apre la locale** | `0x04 SESSIONE_LOCALE_PREVALSA` | **definito in `rcp.h:44` e MAI EMESSO** |

⛔ È la stessa forma di guasto di `RCP_SERVER_IN_CHIUSURA` (rilievo **B-7**): un motivo che esiste
nell'intestazione e che nessuno spedisce. ⭐ E la pagina **è già pronta a leggerli**
(`pagina.html:440-441`): manca solo chi li manda.

**Quel che serve:**

- **chi guarda le sessioni locali — logind.** Oggi l'unico file che lo nomina è `sessione.c`, di
  sfuggita. Il pezzo da riportare è `fondamenta/remotix-c/src/sentinella.c` (307 righe): `ListSessions` +
  i segnali `SessionNew` / `SessionRemoved`, e le proprietà `Type`, `Remote`, `Active`;
- ⛔⛔ **la definizione di «sessione grafica locale», scritta prima del codice — e la prima stesura
  ovvia è SBAGLIATA.** Il criterio che viene in mente è `Type ∈ {wayland, x11}` **e**
  `Remote = false`; ⛔ ma `[R]` **noi non chiamiamo `pam_set_item(PAM_RHOST, …)` da nessuna parte**
  — `autenticazione.c:176` fa `pam_start` e basta — quindi `pam_systemd` crea le **nostre** sessioni
  senza host remoto e logind le segna con ogni probabilità `Remote=no`. ⇒ ⭐ **con quel criterio la
  nostra sessione remota conterebbe come locale, e ci rifiuteremmo da soli con `0x05`.**

  **Due cure, e conviene farle tutt'e due:**
  1. **il discrimine è il SEAT, non `Remote`**: locale = **ha un seat** (`seat0`); la nostra
     headless non ne ha (è la stessa proprietà su cui Mutter decide `is_headless()`, §2.3);
  2. ⭐ **e `PAM_RHOST` va impostato lo stesso**, con l'indirizzo del client: costa una riga e
     ripaga due volte — logind segna la sessione `Remote=yes`, **e** l'accesso finisce nei registri
     di sistema (`last`, audit) con la provenienza, che oggi non c'è.

  ⏳ `[?]` **Da misurare sulla macchina**, e non è dedotto: `loginctl show-session` sulla sessione
  di `prova` e su quella locale di `nicfio`, guardando `Type`, `Class`, `Remote`, `Seat`, `Active`.
  ⚠ Tentato il 15 agosto sera: la macchina non rispondeva a ssh;
- le sessioni **testuali** (ssh, tty) devono continuare a convivere: sono innumerevoli, §5.1;
- ⚠ il caso `0x04` è l'unico in cui **il server butta fuori un client sano**: `DECISIONI.md` §4.1-bis
  lo ammette solo con un motivo dicibile, ed è per questo che il motivo esiste. Il banco lo verifica
  **dal lato che lo riceve**.

#### 1.5 ⭐ Il multi-tenant: la domanda dell'utente, e la riga dove passa il confine

*Chiesto dall'utente il 15 agosto: «poiché qui trattiamo le sessioni, mi chiedo se il multi-tenant
non ricada in questa fase».*

✅ **Deciso dall'utente lo stesso giorno: «potremmo anche lasciare in questa fase 1 solo utente, e
nella fase 12 il multi-tenant».** ⇒ `DECISIONI.md` §4.6-quater, dove il confine vive per intero.
⚠ La domanda era buona perché i documenti dicevano cose diverse: `SPECIFICHE.md` §5.5 dice *«il
multi-tenant è delle fasi da 5 in poi»*, `PIANO.md` intitolava la fase 12 «Multi-tenant e il budget».

> ⚠ **E quella fase adesso è la 10, non la 12** — spostata dall'utente il **16 agosto 2026**
> (`DECISIONI.md` §4.6-sexies): *«PRIMA si chiude lo sviluppo anche con il multi-tenant, e solo
> dopo si pensa agli altri DE»*. ⭐ **Il confine deciso qui non è cambiato**, è cambiato il posto in
> fila. ⛔ E la frase virgolettata qui sopra **resta com'era detta**: era il numero di quel giorno.

| | dove | in breve |
|---|---|---|
| **un utente remoto per volta** | ⭐ **questa fase** | nessuna prova di due sessioni remote insieme, nessun budget, nessun conteggio |
| **più sessioni insieme, il budget, `BUDGET_PIENO`, `MAX_ATTACCATE` configurabile** | **fase 10** | hanno bisogno di un numero vero, e lo dà il codificatore hardware della **fase 8** |
| ⛔ **il codice chiavato sull'utente**, e il guardiano di logind che **discrimina per utente** | ⭐ **questa fase, e non è rinviabile** | ⛔ non perché sia importante: perché **non si può scrivere «per un utente solo»** |

⛔ **E la ragione per cui l'ultima riga non si rinvia è che la macchina la smaschera da sola.** Il
guardiano di §1.4 risponde a una domanda che suona in due modi diversissimi — *«c'è una sessione
grafica locale?»* contro *«c'è una sessione grafica locale **di questo utente**?»* — che sono una
riga di differenza e due prodotti diversi. ⭐ E la macchina di prova è **già** nella configurazione
che smaschera l'errore: `nicfio` ha la sua sessione grafica **locale**, `prova` si collega da
**remoto**. Scritto male, `prova` viene rifiutato con `0x05` **il primo giorno**.

⇒ ⭐ **Il banco di `0x04`/`0x05` si scrive su quella coppia** — locale `nicfio` e remota `prova`, che
**devono convivere senza toccarsi** — e costa quanto costerebbe comunque.

⚠ **E il ripiego resta dichiarato**: `MAX_ATTACCATE` è un `#define` a **16** (`rcp.c:568`) dove
§5.5 promette **dieci configurabile**. Oggi non morde, e la sua scadenza è la fase 10.

---

### 2 · Quel che il piano chiedeva già, e resta

*Dal mandato §3 e §4 — nessuno di questi ha un banco, ed è esattamente il lavoro della fase.*

1. ✅ **Il rilascio dei tasti al distacco, CON UN TASTO PREMUTO DAVVERO** — `[M]` **16 agosto,
   provato col browser su due delle quattro strade, e il testimone è il desktop vero.**
   `RCP.md` §11 la chiama *«la regola col rapporto danno/costo più alto del documento»*.
   ⇒ **Regge**, e i tempi sono quelli di §6-bis qui sotto. ⛔ Ma la prova ha trovato **due difetti**,
   uno chiuso e uno aperto: la riga che diceva sempre `0` (chiusa) e **l'orologio del silenzio**
   (punto 4, e adesso ha una misura).
2. ✅ **L'inibizione della sospensione** — `[M]` 16 agosto, **20 giri su 20**: *«sospensione e
   inattività INIBITE al gestore di sessione (flag 12 = SUSPEND\|IDLE — mai LOGOUT)»*. ~~Quel che
   segue resta come cronaca di com'era:~~ `[M]` 15 agosto: la notifica **«Automatic Suspend —
   Suspending soon because of inactivity»** compare in due schermate del desktop remoto.
   `sleep-inactive-ac-type` vale `suspend` a **900 s**. La cura è una chiamata:
   `SessionManager.Inhibit(…, 12)` = `SUSPEND|IDLE` **insieme**, ⛔ **mai** il bit `LOGOUT`.
   ⚠ `energia.c` **non esiste in `src/`**: va portato da `fondamenta/remotix-c/src/energia.c`.
   ⚠ E senza questa, il banco delle **sei ore** non misura niente.
3. ✅ **L'headless si dichiara e si verifica dopo l'avvio** — `[M]` 16 agosto, **20 giri su 20**: il
   figlio scrive *«VERIFICATO: la mia sessione non ha seat ⇒ Mutter è headless»*. ⛔ Non è più «per
   accidente»: è un fatto letto dal nucleo a ogni sessione.
4. **I tre orologi**: ✅ **30 s di silenzio** — era **rotto**, trovato il 16 agosto col browser
   mentre si provava il punto 1 (contava i secondi in cui *l'utente non tocca niente* invece di
   quelli in cui *il client tace*: un secondo dispositivo entrava e si prendeva il desktop di chi
   stava guardando). **Riparato e provato in tre punti**, §6-bis. ✅ **30 min di inattività**: fatto il 16 agosto,
   motivo `0x02` di §8.2 che era dichiarato e mai spedito — §6-quinquies. ✅ **il terzo**: niente 6 ore — **60 minuti
   senza input e la sessione si chiude** (`DECISIONI.md` §4.8), provato a 20 s in §6-septies.
5. ✅ **Distacco e riaggancio due volte di fila** — *«un banco che passa solo da macchina pulita non è
   un banco, è una dimostrazione»*. ⇒ `[M]` 16 agosto: **cinque giri**, tre col distacco pulito e
   **due col filo tagliato**. Indistinguibili fra loro, e ⭐ **niente si accumula** — §6-sexies.
6. ✅ **La sessione senza nessuno che guarda** — `[M]` 16 agosto, col browser. In v1 il monitor
   virtuale spariva al distacco e `libmutter` andava in asserzione fallita: ⭐ **qui non succede**, e
   il costo di un desktop che nessuno guarda è **praticamente zero**. Misure in §6-quater.
7. ✅ **PAM per intero**: asincrono (`aiutante.c`) **e** la sessione PAM aperta dal figlio (passo
   2-bis). `[M]` provato venti volte col browser: *«PAM ha risposto: ammesso — e il filo non si è mai
   fermato»*.

⇒ ⭐ **I sette punti di §2 sono chiusi.**

---

### 3 · Quel che la coda della fase 4 lascia aperto e che passa di qui

| | |
|---|---|
| ⏳ la riga che manca a `RCP.md` §7.1 | che cosa fa il server quando il palco cambia misura **da sé** |
| ⚠ i 4 ms di ritardo medio aggiunto | `MOVIMENTO_ATTESA_S` a 8 ms è un ripiego dichiarato |
| ⚠ i banchi RCP/1 non esercitano `ADATTA_TELA` | `01-b3` e `01-b4` restano verdi perché il filo non è cambiato |

---

### 4 · ⛔ LE DECISIONI CHE ASPETTANO L'UTENTE

*⭐ Le domande si affrontano **una alla volta**, per volontà dell'utente.*

**Chiuse:**

| | |
|---|---|
| ✅ **le due uscite** — il filo che cade contro il logout | `DECISIONI.md` §4.1-ter, 15 agosto |
| ✅ **dopo il logout la pagina torna al modulo di accesso**, e il motivo è `0x10` | `DECISIONI.md` §4.1-quater, `RCP.md` §8.2, 15 agosto |
| ✅ ~~`disable-log-out`?~~ **vietata** · ✅ ~~`always-show-log-out`?~~ **acceso** | cadute per conseguenza, non per scelta |
| ✅ **nessuno spegne il server**, chi è davanti alla macchina compreso — e l'utente remoto ha **il solo logout** | `DECISIONI.md` §4.7, `SPECIFICHE.md` §11.3, 15 agosto |
| ✅ **il logout si raggiunge in due modi**: la voce del menu e `Ctrl+Alt+Fine` — ❌ `Ctrl+Alt+F12` e ❌ `Win+F12` scartate **con una misura ciascuna**, ❌ **nessun bottone a schermo** | `DECISIONI.md` §4.1-quinquies, `SPECIFICHE.md` §5.2-bis, 15 agosto |
| ✅ **il multi-tenant è della fase 10** — qui **un utente remoto per volta**, ⛔ ma il guardiano di logind discrimina **per utente** | `DECISIONI.md` §4.6-quater, 15 agosto |

| ✅ **due secondi all'accesso vanno bene; diciotto no** — 16 agosto. ⇒ Il guadagno da 2,1 s a ~1,2 s (dichiarare la misura della finestra nel saluto invece che dopo l'ammissione) **non si fa adesso**: costa mezza giornata **nella stretta di mano**, che è l'unico pezzo dove uno sbaglio è un buco e non un difetto estetico. ⭐ Si riprende quando il protocollo si aprirà comunque — la fase 12 tocca quella zona | qui sotto, e la misura è già fatta |

**Aperte:** ⭐ nessuna. ⚠ Il 16 agosto ne è passata una che **non era una decisione**: l'orologio del
silenzio contava i secondi sbagliati (§6-bis). `SPECIFICHE.md` §5.3 e `RCP.md` §8.2 avevano già
deciso, e il prodotto non li rispettava — ⇒ **riparato senza chiedere**, perché non c'era niente da
scegliere.

#### ⏳ Il secondo che si potrebbe recuperare, con la misura già fatta

`[M]` L'accesso costa **2087 ms** di mediana, e **968** sono il figlio che aspetta: il browser
dichiara la misura della sua finestra **solo dopo essere stato ammesso**, e prima di allora la
sessione non può nascere perché non si sa a che misura.

⇒ Se la misura arrivasse **col saluto** — come già fa il tetto del decodificatore — la sessione
nascerebbe **durante** il secondo fisso invece che dopo: accesso a **~1,2 s**. ⛔ E il secondo fisso
resterebbe intatto: cambia *quando si dichiara la misura*, non *quando si risponde*, quindi il
canale del cronometro resta chiuso.

⚠ **Il costo**: `RCP.md`, `pagina.html`, `rcp.c` **e il suo gemello identico byte per byte** in
`banchi/rcp/`, `figlio.c`, il client di banco, più una prova per il caso «client vecchio che non lo
manda». **Mezza giornata**, e nel pezzo più delicato del programma.

---

### 5 · Che cosa non ha funzionato

#### 15 agosto 2026, sera — quattro cose, e tre le ha trovate il banco

1. ⛔⛔ **La pila PAM del prodotto non chiamava `pam_systemd`.** `src/remotix.pam` chiudeva con
   `common-session-noninteractive`, che su Debian **non** contiene `pam_systemd` — quindi nessuna
   sessione logind, quindi niente `is_headless()` e niente soggetto per §5.1. ⭐ **E funzionava
   lo stesso, per un accidente rovesciato**: il file non era installato, PAM ripiegava su `other`,
   e `other` include `common-session`, che `pam_systemd` ce l'ha. ⇒ Installare il nostro file
   «come si deve» avrebbe **rotto** quel che l'assenza del file faceva funzionare.
   *(`DECISIONI.md` §1.10-ter.)*
2. ⛔ **La regola polkit di v1 copriva 3 azioni su 12**, e la mancante era
   `power-off-multiple-sessions` — cioè **il caso multi-utente**, l'unico per cui la regola era
   stata scritta. Con un utente solo funzionava.
3. ⛔ **Il mio ragionamento su root era sbagliato**, e me l'ha detto la misura: avevo scritto in
   `DECISIONI.md` che serviva un'eccezione per root, altrimenti `sudo systemctl poweroff` sarebbe
   fallito. `[M]` Non serve: logind guarda `CAP_SYS_BOOT` **prima** di polkit. ⇒ La voce è stata
   corretta, e con lei la conseguenza vera — **la verifica non si può fare dal server, che è root**.
4. ⛔⛔ **Il banco è stato verde due volte per il motivo sbagliato**, ed è la forma che questo
   progetto paga più spesso:
   - la prima perché **gli utenti di prova non esistevano** (il rootfs vive in RAM e il riavvio li
     aveva cancellati come la chiave ssh): PAM apriva sessioni per un conto inesistente, e i casi
     «falso» erano falsi perché **non c'era niente**;
   - la seconda perché **logind rifiutava in silenzio** la seconda sessione sulla stessa console
     virtuale: `pam_systemd` è `optional`, PAM tornava `SUCCESS`, e il caso 6 era verde **perché
     vuoto**.
   ⇒ In tutt'e due i casi a smascherarlo è stato **il dump di `loginctl` dentro il banco**: un banco
   che dice solo il colore fa ricominciare la caccia da capo.

#### 15 agosto 2026, 19:02 UTC — lo schermo nero, e la domanda dell'utente

**Il sintomo**: l'utente si collega, entra, e **non vede il desktop**. La domanda che ha fatto —
*«sicuri che non hai introdotto regressioni?»* — era quella giusta da fare.

**Non era una regressione**, e il registro lo diceva per intero: l'attacco è passato (nessun `0x05`,
nessun rifiuto), e il figlio ha scritto tre volte

> ⛔ *runtime «/run/user/1001» NON c'è, socket del bus non c'è — senza bus non c'è niente da catturare*

⇒ Il riavvio aveva cancellato l'utente `prova` insieme alla chiave ssh (rootfs in RAM); ricreandolo
**non avevo acceso il linger**, e `/run/user/<uid>` lo crea quello. Curato con
`loginctl enable-linger prova prova2`, e scritto come **requisito** in `DECISIONI.md` §1.10-ter.

> #### ⭐⭐ E l'utente ha visto sotto il sintomo un tema — 15 agosto 2026
>
> > *«Bisogna fare attenzione al corretto setting delle variabili d'ambiente (XDG…). Dovrebbe essere
> > compito del session manager, ma per qualche motivo in REMOTIX sembra che non vengano
> > impostate.»*
>
> ⭐ **Ha ragione, e la ragione è strutturale**: quelle variabili le imposta `pam_systemd` al login,
> e ⛔ **noi il login non lo facciamo** — `figlio.c:2428` dichiara fuori mandato far nascere la
> sessione. ⇒ Nessuno le imposta, e noi le **componiamo a mano**.
>
> **Quel che c'è oggi**, letto nel codice:
>
> | dove | che cosa compone |
> |---|---|
> | `figlio.c:723-737` | `HOME`, `USER`, `LOGNAME`, `PATH`, `SHELL=` (vuota), `XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS` — **sette, e nient'altro esiste dall'altra parte** (`execve`) |
> | `sessione.c:492-511` | le due di sopra più `XDG_CURRENT_DESKTOP`, `XDG_SESSION_DESKTOP`, `XDG_SESSION_TYPE`, `LANG` |
>
> ⛔ **E `XDG_RUNTIME_DIR` è ASSERITA, non ottenuta**: si scrive `/run/user/<uid>` per convenzione.
> La convenzione è giusta su systemd — ⚠ ma è esattamente la forma del guasto di stasera: un valore
> **dichiarato** al posto di un valore **avuto**.
>
> ⚠ **Quel che nessuno imposta, e che ricade sui predefiniti in silenzio**: `XDG_DATA_DIRS`,
> `XDG_CONFIG_DIRS`, `XDG_DATA_HOME`, `XDG_CONFIG_HOME`, `XDG_STATE_HOME`, `XDG_CACHE_HOME`,
> `XDG_SESSION_CLASS`. ⛔ E `XDG_SESSION_ID` **di proposito** (`sessione.c:523`).
>
> ⇒ **Il lavoro che ne nasce, per questa fase:**
> 1. un posto solo che compone l'ambiente **e lo verifica**, scrivendo per ogni variabile **da dove
>    viene** — asserita, ereditata, dedotta. Oggi `sessione.c` già lo fa per il bus (*«assente: uso
>    …»*), ed è la forma da estendere;
> 2. ⛔ `XDG_RUNTIME_DIR` si **verifica prima di `execve`**: esiste, ed è di quell'uid. Se non c'è, il
>    messaggio deve **nominare la causa probabile** — *«quell'utente ha il linger acceso?»* — invece
>    del solo sintomo, che stasera è costato un giro;
> 3. decidere se le sei `XDG_*_DIRS`/`_HOME` vadano dichiarate invece di lasciate al predefinito.

#### 15 agosto 2026, 20:00 UTC — ⛔⛔ il lag, e il prezzo nascosto dell'headless

**Il sintomo**, riferito dall'utente: *«qualche piccolo lag in generale»*, e poi il numero che conta —
*«impartisco un comando nel terminale e risponde con 1-2 secondi di ritardo»*.

**Le due cose escluse per prime, con una misura ciascuna** — ⛔ e la prima è quella che avevo
aggiunto io, quindi andava esclusa per prima:

| sospetto | misura |
|---|---|
| il **ripasso di logind** ogni 2 s, sincrono nel ciclo dei fotogrammi | ⭐ `[M]` 200 chiamate: **mediana 0,125 ms**, p95 0,226, **max 0,351 ms**. ⇒ Non è quello, e il ripiego «sincrono» di `sentinella.c` regge |
| il **danno degenerato** — `libmutter-WARNING: Not enough buffers (4) to accommodate damaged regions (6)` | `[M]` 18 avvisi in tutto, non continui. ⚠ E la lettura del sorgente di Mutter (`meta-screen-cast-stream-src.c:891`) dice che **non** sono i buffer PipeWire: sono i **posti-regione** nel metadato `VideoDamage`, che chiediamo `×4` con tetto `×16` (`cattura.c:419`). Quando le regioni sono di più, Mutter dichiara **tutto il fotogramma danneggiato**. ⏳ Difetto vero, piccolo, da curare — ma non è questo il lag |

⛔ **La causa era il compositore che disegnava IN SOFTWARE**, e l'ho introdotta io: `[M]`
`gnome-shell` non aveva **nessun** nodo `/dev/dri/*` aperto. Ricreando l'utente `prova` dopo il
riavvio l'ho fatto con `useradd` nudo — `groups=prova` e basta — mentre `nicfio` è in **`video`
(44)** e **`render` (991)**, e i nodi sono `root:render` in modo `0660`. Senza accesso alla GPU,
Mesa ripiega su llvmpipe e il compositore compone **a mano** un desktop di 2544×926.

**La cura, in due passi e il secondo non è ovvio**: `usermod -aG video,render prova` — ⛔ **e far
rinascere `user@1001.service`**, perché il compositore lo avvia il **gestore d'utente**, che le
credenziali le fissa alla propria partenza: `[M]` dopo il solo `usermod` il processo aveva ancora
`Groups: 1001`. Dopo il riavvio del gestore: `Groups: 44 991 1001` e **10 descrittori** su
`/dev/dri/renderD129`.

> #### ⭐⭐ E LA DOMANDA DELL'UTENTE HA SCOPERTO UN PREZZO CHE NON ERA SCRITTO DA NESSUNA PARTE
>
> > *«Nei DE normali l'utente NON appartiene ai gruppi `video` e `render`, eppure usano
> > l'accelerazione hardware. Come mai?»*
>
> ⭐ **Perché su un desktop normale non servono i gruppi: serve il SEAT.** `[M]` verificato sulla
> macchina: `/dev/dri/renderD129` porta i tag udev **`uaccess`** e **`seat`**, e logind concede
> l'accesso con un'**ACL per utente** — è il `+` nei permessi — all'utente della sessione **attiva
> su quel seat**. Nessun gruppo, nessuna configurazione: la dà il fatto di essere seduti lì.
>
> ⛔ **E noi quel seat non ce l'abbiamo, di proposito**: è la condizione di `is_headless()`
> (`DECISIONI.md` §4.3-bis), cioè quel che ci salva dalla revoca del blocca-schermo di GNOME.
> `[M]` `getfacl` sul nodo, adesso: **nessuna voce per utente** — perché nessuna sessione sta su un
> seat.
>
> ⇒ ⛔⛔ **Il prezzo dell'headless è la perdita delle ACL di `uaccess`**, e nessun documento lo
> diceva. Per una sessione REMOTIX i gruppi `video` e `render` **non sono una comodità
> dell'ambiente di prova: sono un requisito del prodotto**, esattamente come il linger — e come
> quello vanno dichiarati e verificati, o si ripaga una serata.
>
> ⚠ **E c'è una coda da non perdere**: senza la regola udev di `DECISIONI.md` §4.6-ter — `[M]` non
> installata: `/etc/udev/rules.d` è vuota — i gruppi danno accesso a **tutt'e due** le schede, e
> `[M]` il compositore ha scelto **`renderD129`, l'AMD**. Che sia quella giusta è una decisione
> della fase 8, non un caso da lasciare all'ordine di enumerazione.

#### 15 agosto 2026, 22:09 — ⭐⭐ la controprova, e la porta l'utente

*Registrazione dello schermo del client, 17,3 s a 2560×1080, consegnata dall'utente.*

**La scena**: il banco WebGL **«Aquarium»** di `webglsamples.org` — 100 pesci, tela 1024×1024 —
girato **dentro** il desktop remoto in Firefox, e guardato attraverso REMOTIX.

| che cosa | misura |
|---|---|
| il contatore dell'Aquarium, **letto a piena risoluzione su 16 secondi consecutivi** | ⭐ **58 · 59 · 60 · 61** — inchiodato a sessanta, mai un tuffo |
| fotogrammi **distinti** arrivati sullo schermo del client (`mpdecimate`) | ⭐ **453 su 17,26 s = 26,2 al secondo** ⚠ e il tetto è del registratore, che campiona a 30: non si distingue «26 consegnati» da «più di 26, campionati 30» |

⭐ **È la controprova della cura di §5 di stanotte**: llvmpipe non fa 60 fps su un WebGL con 100
pesci, neanche per sbaglio. ⇒ La GPU c'è, e il difetto dei gruppi mancanti era davvero tutto il lag.

⚠ **E quel che questa misura NON dice, dichiarato**: non è una misura di **latenza** — dice che il
flusso è fluido, non quanto tempo passa fra il tasto e il pixel. Quella resta `[M]` 41 ms della coda
della fase 4, e va rifatta su questa configurazione.

> #### ⛔⛔ E QUESTA MISURA È STATA FATTA SULLA SCHEDA SBAGLIATA — vincolo posto dall'utente, 15 agosto
>
> > *«I test vanno fatti sulla GPU integrata, altrimenti "trucchiamo" il gioco. La solidità del
> > sistema la si vede su GPU poco potenti, non mostri come la RX 6800.»*
>
> `[M]` I 60 fps dell'Aquarium sono stati presi sulla **Radeon RX 6800**, perché senza la regola
> udev di `DECISIONI.md` §4.6-ter — non installata — la scheda **la sceglieva il compositore**, e
> aveva preso la discreta. ⇒ ⛔ **Il numero non vale come misura del prodotto**: dice quanto è veloce
> quel ferro.
>
> ⭐ **Curato la sera stessa** (`DECISIONI.md` §4.6-quinquies): `gpu-udev.sh 0000:03:00.0` esclude la
> Radeon, e `[M]` dopo il riavvio del gestore e della sessione `gnome-shell` apre **6 descrittori su
> `renderD128`** — la **Intel UHD 730**, e solo quella.
>
> ⇒ **La misura dell'Aquarium va rifatta sull'integrata**, ed è quella che conta.
>
> #### ⭐⭐⭐ E RIFATTA SULL'INTEGRATA REGGE — riferita dall'utente, 15 agosto 2026, 20:15
>
> > *«Su Android ho 60 fps fissi con il test Aquarium.»*
>
> `[M]` **Verificato che la scena fosse quella giusta prima di crederci**: `gnome-shell` pid 22462 —
> quello nato **dopo** la regola udev — ha 6 descrittori su **`renderD128`**, la Intel UHD 730; e il
> registro dice che alle `20:15:12` si è collegato **`192.168.0.24`**, un dispositivo diverso dal
> portatile (`.3`), con tela 2544×926 e vista 2560×926: il **DeX**.
>
> ⇒ ⭐ **WebGL Aquarium, 100 pesci, 60 fps fissi — sulla GPU integrata, guardato da Android.** ⚠ E
> vale doppio perché DeX è l'uso **primario** (`DECISIONI.md` §5-bis.0), cioè il caso in cui il filo
> è più lungo e il dispositivo più debole. ⛔ Resta quel che questa misura non è: **non è latenza**.

#### 15 agosto 2026, 20:27 UTC — ⭐⭐⭐ IL PRODOTTO FA NASCERE LA SESSIONE, e la catena si chiude

*Ordine dei lavori **cambiato su indicazione dell'utente**: «il discorso `Ctrl+Alt+Fine` introduce
poi anche il discorso della persistenza della sessione, del detach e re-attach». ⛔ Aveva ragione, e
la conseguenza era più stretta di così: **implementare il logout prima che il prodotto possieda la
nascita della sessione sarebbe stato dannoso** — `Ctrl+Alt+Fine` avrebbe chiuso la sessione e
nessuno ne avrebbe fatta un'altra. Una funzione che porta l'utente allo schermo nero.*

**Che cosa è stato scritto:**

| | |
|---|---|
| `figlio.c`, `diventa_ed_esegui()` **passo 2-bis** | apre la **sessione PAM** dopo la chiusura dei descrittori e prima di scendere all'uid: `XDG_SESSION_TYPE=wayland`, `XDG_SESSION_CLASS=user`, `PAM_RHOST`, ⛔ **nessun `XDG_SEAT`** — headless per costruzione. `pam_end` **senza** `pam_close_session`: la sessione è del processo guida, ed è I4 vista dal sistema |
| `figlio.c`, `prendi_il_palco()` | la riga *«guardo e non tocco»* è diventata **«LA FACCIO NASCERE io»**, con la briglia di un minuto |
| `sessione.c/h`, `sessione_fai_nascere()` | fa nascere **senza aspettare**: `sessione_assicura()` attende fino a 40 s, e chi chiama è l'unico processo che in quei 40 s deve rispondere al padre (`LEZIONI.md` §6.2-bis). ⭐ L'attesa esiste già ed è il ciclo di ri-tentativi |
| `/media/REMOTIX/tmp/riavvia-7700-unita.sh` | ⛔ **il server fuori da ogni sessione utente** — vedi sotto |

⛔⛔ **E il vincolo di dispiegamento che ne nasce, misurato**: `pam_systemd`, quando chi chiama sta
già in una sessione, **non ne crea una seconda e non lo dice**. `[M]` Col vecchio
`riavvia-7700.sh` — che usa `setsid`, il quale stacca il terminale ma **non cambia il cgroup** — il
server stava in `session-127.scope` (la ssh di `nicfio`), e i figli restavano senza sessione: **lo
stesso schermo nero, per una causa nuova**. Con `systemd-run` sta in `system.slice`.

**La prova, da piazza pulita** — nessuna sessione di `prova`, nessun `/run/user/1001`, ⛔ **linger
spento**, nessuna impalcatura:

| ora | il registro |
|---|---|
| 20:27:15 | `⭐ IL BUS DI SESSIONE È MIO: collegato come uid 1001` |
| 20:27:15 | `⭐ nessuna sessione grafica per «prova»: LA FACCIO NASCERE io (tela 1920x1080) e torno subito` |
| 20:27:15 | `sessione avvio la sessione grafica: exec gnome-session --session=gnome` |
| 20:27:47 | `cattura il nostro monitor è Meta-0 («Virtual remote monitor»), 0 prima e 1 dopo` |
| 20:27:47 | ⭐ `fotogramma catturato COME «prova»: 1920x1080 … BGRx a 8 bit, **non nero**` |

`[M]` **E la sessione nata dal prodotto è quella giusta**: `loginctl` la dà `c52`, **`Class=user`**,
`RemoteHost=remotix`, **`Seat=` vuoto**; e il compositore apre **`renderD128`**, l'integrata — la
regola udev regge anche su una sessione che nasce da sola.

⚠ **Il prezzo, dichiarato**: dal primo attacco al primo fotogramma passano **~32 secondi**, ed è
l'avvio a freddo di `gnome-session`. Succede una volta per sessione, ⛔ ma in quei 32 s il client è
attaccato e non vede niente — e oggi non gli diciamo perché.

> ⭐ **E questo numero è VECCHIO: il 16 agosto l'avvio a freddo misura `[M]` 2353 ms**, non 32 s (vedi
> §«venti giri dal browser»). ⇒ Il difetto di fondo resta — *mentre aspetti non ti diciamo perché* —
> ma l'attesa è passata da mezzo minuto a due secondi e mezzo, e con essa l'urgenza. ⏳ Da coprire,
> non da correre.

#### 15 agosto 2026, 20:50 UTC — ⛔⛔ «il terminale è congelato finché non muovo il mouse»

**Il sintomo, e l'ha isolato l'utente** dopo che io avevo inseguito la banda per mezz'ora:

> *«Dal terminale do il comando `exit` e il terminale sembra come congelato: non appena muovo il
> mouse allora si chiude correttamente.»*

⭐ **Quella frase è la diagnosi**: se lo schermo si allinea appena arriva *un fotogramma qualunque*,
allora il fotogramma giusto **era stato prodotto e non è stato consegnato**.

**Quel che avevo escluso prima, con le misure** — e servono, perché dicono dove NON è:

| | |
|---|---|
| dal palco al filo | `[M]` **0 ms** di mediana e p95, **1 ms** il massimo su 200 fotogrammi |
| il codificatore | `hevc_vaapi` **in hardware** su `renderD128`, chiave in **8,8 ms** |
| il ripasso di logind | `[M]` 0,125 ms di mediana |
| la banda | ⚠ c'erano abbandoni a 45 Mbit/s **con l'Aquarium in moto** — ⛔ ma l'utente ha detto *«niente Aquarium»*, e la pista è caduta |

⛔⛔ **LA CAUSA, e stava scritta in un commento del nostro codice**: `cattura.c` consegnava il
fotogramma **solo se qualcuno lo stava aspettando in quell'istante** —
`if (qualcuno_aspetta && !posto_pieno)` — con questa giustificazione: *«copiare 8 MB per nessuno
sarebbe lavoro dentro la richiamata di tempo reale, fatto per niente»*.

⭐ **Il ragionamento è giusto per il caso a regime e sbaglia il caso che l'utente vede.** La finestra
che si chiude produce una **raffica**: prendiamo il primo fotogramma e passiamo ~20 ms a convertirlo
e comprimerlo; ⛔ tutti quelli che arrivano in quei 20 ms trovano `qualcuno_aspetta == FALSE` e
**vengono buttati — compreso l'ultimo**, quello con la finestra già sparita. Poi la scena è ferma e
Mutter non manda più niente (cadenza `0/1`: *«un fotogramma quando cambia qualcosa»*). ⇒ L'utente
resta a guardare il **primo** fotogramma della raffica, finché un movimento non ne produce un altro.

⛔ **E la seconda metà dello stesso difetto era dal lato di chi consuma**: `cattura_prendi()`
all'ingresso faceva `posto_pieno = FALSE`, cioè **buttava via il fotogramma che trovava già pronto**
e si metteva ad aspettarne uno nuovo che, a scena ferma, non sarebbe mai arrivato.

**La cura**: si tiene **sempre l'ultimo** — un posto solo, vince il più recente, che è anche la
politica giusta per un desktop remoto (di un fotogramma vecchio non se ne fa niente nessuno). ⭐ E il
costo che il vecchio commento temeva **si paga meno di prima**: il buffer si **riusa**
(`posto_capienza`), quindi la richiamata di tempo reale fa una `memcpy` e non più una
`g_free`+`g_malloc` da 8 MB.

⚠ **Con un contatore nuovo nella riga di riassunto** — *«sostituiti nel posto N (prima del 15 ago
erano PERSI)»* — perché il numero che conta non è che la cura c'è: è **quante volte serve**.

> #### ⭐⭐⭐ CONFERMATO DALL'UTENTE — 15 agosto 2026, e il giudizio va oltre il difetto
>
> > *«Ora il terminale si chiude subito, problema risolto **sia su Linux sia su Android**. Inoltre
> > adesso il sistema mi sembra **tremendamente responsivo**, i tempi di risposta sono istantanei
> > anche su Android, e considerando che sia su una Intel integrata direi risultato eccellente.»*
>
> ⭐ **E il guadagno è più grande della cura, per una ragione che vale la pena capire**: non si
> perdeva solo l'ultimo fotogramma — si perdevano **tutti quelli di ogni raffica**, cioè quelli che
> arrivavano mentre comprimevamo il precedente. ⇒ Ogni finestra che si apre, ogni scorrimento, ogni
> riga di terminale era più a scatti del necessario, **e nessuno l'aveva mai notato** perché il
> difetto si vedeva solo nella coda.
>
> ⇒ ⚠ *Un difetto che si manifesta in un caso limite può costare in tutti gli altri, in silenzio.*
> La lezione per intero è in `LEZIONI.md` §6.5.
>
> ⏳ **E ora la misura di latenza va rifatta**: i `[M]` 41 ms della coda della fase 4 sono di prima
> di questa cura, e su una configurazione diversa. Il numero vero non lo sappiamo ancora.

*⚠ L'orologio della macchina di prova è **UTC**, cioè due ore indietro rispetto al nostro: le ore
qui sotto sono le sue.*

#### 15 agosto 2026, 18:20-18:35 UTC — la macchina, dopo il riavvio

*La macchina si era inchiodata; l'utente l'ha riavviata, e il rootfs vive in RAM ⇒ chiave ssh
reinstallata e `provision-server.sh` rieseguito.*

| | esito |
|---|---|
| **`provision-server.sh`** | passato, ⛔ **tranne la §4** (*«daemon-reload d'utente fallito»*, il bus d'utente non c'era). ⭐ **E non è un problema**: quella sezione scrive `--virtual-monitor` in `/etc/systemd/user/`, cioè proprio quel che v2 **non vuole più** dal 14 agosto — `sessione.c` scrive il suo drop-in `zz-` apposta per vincere su quello. ⇒ **provisioning di v1 rimasto indietro**, da rifare per v2 |
| ⭐ **`loginctl` — il discrimine** | `[M]` la sessione **ssh** risulta `Remote=yes`, `RemoteHost=192.168.0.3`, `Type=tty`, **`Seat=` vuoto**. Il seat esiste (`seat0`) ma ⛔ **nessuna sessione grafica locale è viva**: per provare `0x05` servirà un accesso vero alla consolle |
| ⛔⛔ **la regola polkit di v1 copriva 3 azioni su 12** | `[M]` `org.freedesktop.login1.policy` ha anche `*-multiple-sessions` e `*-ignore-inhibit`. ⇒ Con **più utenti** logind chiede `power-off-multiple-sessions`, che v1 non nominava: **falliva esattamente nel caso per cui era scritta**. ⚠ E `…login1.halt` **non esiste**: riga morta |
| ⭐ **root non ha bisogno di eccezioni** | `[M]` con la regola in vigore: da `nicfio` `CanPowerOff="no"`, **da root `"yes"`** — logind guarda `CAP_SYS_BOOT` **prima** di polkit. ⇒ ⛔ **la verifica va fatta dal FIGLIO, non dal server**, che è root e si sentirebbe dire sempre di sì |
| ⭐ **il tasto fisico era vivo** | `[M]` tutte le righe `Handle*` di `logind.conf` erano **commentate** ⇒ `HandlePowerKey=poweroff`. Il pulsante spegneva il server con chiunque collegato sopra |
| ✅ **le due cinture installate e rilette** | `[M]` da `nicfio`: `CanPowerOff` `CanReboot` `CanSuspend` `CanHibernate` = **tutte `"no"`**; `systemd-analyze cat-config` dice `HandlePowerKey=ignore`, `HandleSuspendKey=ignore`, `HandleLidSwitch=ignore`. ⇒ `src/remotix-niente-spegnimento.rules` e `src/remotix-tasti.conf`, **nel repository** (I7) |
| ⭐ **la sospensione ha una cintura più forte** | `[M]` `sleep.conf.d AllowSuspend=no` fa dire `CanSuspend="no"` **anche a root**: è systemd a rifiutare, non polkit |

#### 15 agosto 2026, 18:31-18:45 UTC — il guardiano di logind, costruito e certificato

| | |
|---|---|
| **il codice** | `src/sentinella.c` + `.h` (nuovi), il gancio `sessione_locale` in `rcp.h`/`rcp.c`, `wt_locale_gancio` e `wt_sorveglia_locali()` in `webtransport.c`, la cucitura in `main.c` con ripasso ogni **2 s** |
| ⭐ **è vivo sul server** | `[M]` nel registro: *«guardiano delle sessioni locali pronto (bus di sistema); il discrimine è il SEAT, non «Remote»»* |
| ⭐⭐ **la misura che giustifica il discrimine** | `[M]` una sessione fatta **come la nostra** — `pam_open_session` senza `XDG_SEAT` — risulta a logind: `Seat=` **vuoto**, `Remote=no`, `Type=wayland`. ⛔ Cioè **indistinguibile da una locale** se il criterio fosse `Remote`: il primo utente collegato sarebbe stato respinto con `0x05` dalla sua stessa sessione |
| ✅ **il banco** | `banchi/05-b1-sentinella.c`, **6 casi, 0 rossi**: nessuna sessione · una come la nostra · una locale (`seat0`, wayland) · chiusa la locale · la locale è **di un altro utente** · l'utente è alla consolle **in una sessione di testo** |
| ⭐⭐ **certificato** | `banchi/05-b1-certifica.sh`, **3 guasti innestati, tutti e tre cadono dove devono**: tolto il seat → rossi 2 4 5 6; tolto l'utente → 5 6; tolto il tipo grafico → 6 |
| ⛔ **e la certificazione ha scritto il banco, non solo controllato** | il guasto «il tipo grafico non si guarda più» non faceva cadere **niente** ⇒ nessun caso esercitava quel controllo. ⭐ Da lì è nato il **caso 6** — l'utente alla consolle in una sessione di testo, che `SPECIFICHE.md` §5.1 ammette esplicitamente («testuali e grafiche convivono») e che nessuno aveva provato |
| ⏳ **quel che il banco NON prova**, dichiarato | non prova il filo (`0x05` non è mai uscito su una connessione vera), non prova `0x04` end-to-end, e ⛔ **non prova la scena con una sessione locale VERA**: sulla macchina non c'è nessuno alla consolle, e le sessioni del banco le crea PAM |

### 6 · ⭐⭐ 16 AGOSTO 2026 — IL RILASCIO AL DISTACCO, PROVATO COL DESKTOP VERO

*«Da adesso i test si fanno sul browser e non più su banchi ipotetici. Così misuriamo quello che
succede davvero, non quello che simuliamo»* — l'utente, 16 agosto.

#### 6.1 Il testimone: un file che cresce di trenta righe al secondo

⛔ Il problema di questa prova non era premere il tasto: era **vedere il danno**. «Un Ctrl rimasto
giù» non si legge in una schermata.

⭐ **La cura**: dentro la sessione grafica di `prova` gira un terminale con

```sh
while IFS= read -r _; do date +%s%N >> /tmp/testimone.txt; done
```

⇒ Ogni battuta di `Invio` che arriva al desktop scrive **una riga con l'istante in nanosecondi**.
Un tasto rimasto giù si ripete da solo — è il desktop remoto a farlo, non la pagina (`pagina.html`
lo dice: *«la ripetizione automatica la fa il DESKTOP remoto, che il tasto ce l'ha giù»*) — e il
file cresce. Un tasto rilasciato ferma il file **all'istante**.

| | |
|---|---|
| `[M]` **la ripetizione esiste, e si misura** | 1016 righe in ~30 s ⇒ **~33 battute al secondo** sul desktop vero |
| `[M]` **il rilascio la ferma di netto** | fra l'ultima battuta e la riga del registro che dichiara il rilascio: **1 ms · 15 ms · 28 ms** nelle tre prove |

⚠ **Che cosa è finto in questa prova, dichiarato**: il *keydown* nasce da `dispatchEvent` dentro la
pagina, perché il pilota del browser non sa **tenere premuto** un tasto (manda sempre giù-e-su
insieme). ⭐ Tutto il resto è vero: stesso gestore della pagina, stesso messaggio sul filo, stesso
server, stesso `libei`, stesso desktop. E per la **chiusura della scheda** si è tolta alla pagina la
sua rete di sicurezza (`cl_rilascia_tutto` su `blur`/`pagehide`), che è l'equivalente di un browser
che muore: senza toglierla, **è la pagina a rilasciare e il server non ha mai niente da fare** — ed è
questa la ragione per cui i venti giri del mattino leggevano sempre zero.

#### 6.2 Le due strade provate, e tutt'e due reggono

| strada | come si è provocata | `[M]` esito |
|---|---|---|
| ⭐ **il silenzio di §5.3** — «il telefono morto in galleria» | `Invio` tenuto giù, poi il filo tagliato con `nft` sulla porta 7700 in tutt'e due i versi | `13:33:07.251 STACCATO per silenzio: 30949 ms` → `13:33:07.257 rilascio al distacco: **1**`. Ultima battuta del testimone: `13:33:07.229` — **28 ms prima** |
| ⭐ **il congedo del client** — la scheda che si chiude | `Invio` **e** pulsante sinistro tenuti giù, rete della pagina tolta, scheda chiusa | `13:42:55.042 congedo del client` → `13:42:55.052 rilascio al distacco: **2**`. Ultima battuta: `13:42:55.037` — **15 ms prima** |

⏳ **Le altre due strade di §7.3 non sono state provate** e lo si dichiara invece di lasciarlo
credere: l'**errore di protocollo** (`viola_input()`) e la **liberazione della sessione**
(`rcp_libera()`). ⚠ La seconda è la rete di sicurezza di tutte le altre, e passa dallo stesso
`rilascia_al_distacco()` con la stessa guardia `inp_rilasciato`.

#### 6.3 ⛔⛔ E LA RIGA IN VETRINA DICEVA SEMPRE ZERO

`[M]` In tutti e quattro i distacchi, a un millisecondo di distanza, il registro diceva **due cose
diverse sullo stesso fatto**:

```
13:42:55.042 rcp     ⭐ §7.3 — RILASCIO AL DISTACCO (congedo del client): 0 fra tasti e pulsanti
                        erano premuti e sono stati rilasciati
13:42:55.052 input   rilascio al distacco: 2 fra tasti e pulsanti (restano segnati 0 e 0)
```

⛔ **Lo zero era strutturale, non un caso.** Chi tiene la mappa dei tasti premuti è il **figlio**, un
altro processo; `webtransport.c` mandava la richiesta e rispondeva `0` intendendo *«è partita»*, e
`rcp.c` lo scriveva come *«zero erano premuti»*. Il commento nel codice lo diceva pure — a due
funzioni di distanza da quella che stampava.

> ⚠ **È `LEZIONI.md` §1.9 nel posto peggiore che avesse.** La regola col rapporto danno/costo più
> alto del documento aveva un unico testimone, e quel testimone diceva **sempre** «non c'era niente
> giù» — cioè **la faccia del verde su un rilascio mai avvenuto**. Un difetto vero in
> `input_rilascia_tutto()` sarebbe stato invisibile a chiunque leggesse quella riga.

✅ **Chiuso**: il gancio ha tre risposte invece di un numero — il conto vero, `SENZA_CONTO`
(«chiesto, e il numero lo sa il figlio: cercalo lì»), `IMPOSSIBILE` («⛔ non si è potuto chiedere: se
qualcosa era premuto, resta premuto»). `[M]` Rimisurato dopo la cura:

```
13:54:24.166 rcp     ⭐ §7.3 — RILASCIO AL DISTACCO (congedo del client): richiesta MANDATA al
                        palco.  ⚠ Questa riga NON porta il numero, perche' chi lo sa e' il figlio…
13:54:24.172 input   rilascio al distacco: 2 fra tasti e pulsanti
```

### 6-bis · ⛔⛔⛔ L'OROLOGIO DEL SILENZIO CONTA LA COSA SBAGLIATA

*Trovato per caso il 16 agosto, mentre si provava il §7.3: **due volte di fila il tasto si è
rilasciato da solo prima che io tagliassi il filo**, e la ragione non era il §7.3.*

`SPECIFICHE.md` §5.3 tiene **tre orologi separati, ciascuno col suo significato**:

| orologio | quanto | che cosa misura |
|---|---|---|
| **silenzio del client** | 30 s | *«un client che tace è un client che si è staccato»* — ⭐ e il paragrafo dice **perché**: *«i 30 secondi coprono solo le interruzioni vere»* |
| **inattività dell'utente** | 30 **minuti** senza input | *«chi resta mezz'ora a guardare un video senza toccare nulla viene staccato»* |

⛔ **Oggi il prodotto li ha confusi**: `rcp.c` misura `ultimo_byte`, cioè l'ultimo byte **di RCP**
arrivato dal client — e un client che guarda e non tocca **non manda niente**. ⇒ Trenta secondi
senza toccare la tastiera valgono come «il client è sparito».

`[M]` **La misura, col browser, e l'atteso dichiarato prima:**

| | |
|---|---|
| `13:46:27.968` | `sessione aperta utente=prova via=[192.168.0.3]:53805` |
| ⛔ `13:46:57.980` | `STACCATO per silenzio: 30013 ms senza un byte` — **posti occupati adesso: 0** |
| ⭐ **e la connessione era viva** | per **111 secondi** QUIC non ha detto niente: nessun `trenta secondi di silenzio (§2.2)`, nessuna chiusura |
| ⭐ `13:48:19.750` | un solo tasto: `posto RIPRESO … dopo il silenzio`, **stessa connessione `:53805`**, nessuna `sessione aperta` nuova |

⇒ ⭐⭐ **I due orologi hanno misurato la stessa cosa e hanno dato risposte opposte.** Nel taglio vero
del filo, QUIC ha dichiarato il silenzio a `13:33:43` — **esattamente 30 s dopo il taglio delle
`13:33:13`**, cioè giusto. RCP l'aveva dichiarato a `13:33:07`, **36 secondi prima e senza motivo**.

#### ⛔ E il prezzo si paga, misurato

`[M]` Prima scheda entrata e ferma (nessun input); dopo 30 s il posto risulta libero. **Seconda
scheda, stesso utente:**

```
13:49:57.274 rcp  posto PRESO da prova via [192.168.0.3]:54839 (occupati adesso: 1)
13:49:57.332 rcp  ⛔ [192.168.0.3]:53805: tela in vigore 2544x926 ma il fotogramma catturato e'
                     1552x568 — NON lo spedisco (§6.2)
```

⇒ **Il secondo dispositivo è entrato e ha preso il desktop del primo, che era vivo e collegato.**
E la prima scheda si è **congelata**, perché il nuovo arrivato ha ridimensionato il palco.

⛔ È l'invariante **I2** rotta **nel caso che `RCP.md` §8.2 nomina per iscritto**:

> *«Chi viene rifiutato è chi arriva, non chi c'era. Nessun client attaccato e vivo viene mai
> spodestato da un altro.»* · *«Un client silenzioso da 30 secondi non è più attaccato, quindi non
> occupa niente e il nuovo entra. Un client **vivo** occupa, e il nuovo è rifiutato. ⛔ Il discrimine
> è l'orologio del silenzio»*

⚠ Il discrimine c'è, ed è quello giusto. ⛔ **È l'orologio che è tarato sulla cosa sbagliata.**

#### ⭐ La cura, e non tocca il protocollo

Il segno di vita giusto **esiste già e funziona**: è il pacchetto QUIC. `trasporto.c` ha il proprio
orologio (`NGTCP2_ERR_IDLE_CLOSE`, i 30 s di §2.2) e nella prova del taglio ha risposto **al
secondo**. ⇒ Basta che §5.3 guardi **l'ultimo pacchetto arrivato da quel peer** invece dell'ultimo
byte di RCP.

| | |
|---|---|
| **che cosa si tocca** | `s->ultima_vita` in `rcp.c` accanto a `ultimo_byte` (**due campi, due orologi**) · `rcp_segno_di_vita()` · il ponte `wt_segno_di_vita()` · la chiamata in `trasporto.c` dopo `ngtcp2_conn_read_pkt()` |
| ⭐ **che cosa NON si tocca** | **il protocollo**: nessun messaggio nuovo, nessun battito da aggiungere alla pagina, `RCP.md` invariato. ⚠ E `rcp.c` ha il gemello identico byte per byte in `banchi/rcp/` |
| ⛔ **e SOLO se `rv == 0`** | il pacchetto dev'essere **decifrato e autenticato**: un datagram UDP qualunque non basta, o chiunque potrebbe tenere occupato il posto di un altro spedendo pacchetti col suo indirizzo |
| ⚠ **il caso da non rompere** | la scheda **congelata** dal browser dopo ~5 minuti in secondo piano (§5.3 la nomina): una scheda congelata smette anche di rispondere a QUIC ⇒ i due orologi restano d'accordo, il posto si libera lo stesso |

#### ✅ FATTA, e la controprova è di tre punti — 16 agosto 2026

⛔ **Due su tre non bastavano**: se avessi provato solo che il posto non si perde, avrei potuto aver
**spento** l'orologio invece di ripararlo. Il terzo punto è il controllo positivo.

| | l'atteso, dichiarato prima | `[M]` |
|---|---|---|
| 1 | entro e **non tocco niente per 90 s** ⇒ nessuno stacco | ✅ `occupati: 1` a +15/30/45/60/75/90 s, zero stacchi (prima si staccava a 30 s) |
| 2 | **seconda scheda** mentre la prima è viva e ferma ⇒ **respinta** | ✅ `posto NEGATO a prova … lo occupa un altro client di questo stesso utente` · `congedo motivo=0x0f` |
| 3 | ⛔ **taglio il filo** ⇒ il posto si libera **davvero**, e a 30 s netti | ✅ `STACCATO per silenzio: 30015 ms senza un PACCHETTO … e l'ultimo byte di RCP è di 66695 ms fa` |

⭐ **La riga nuova porta tutt'e due i numeri**, ed è la differenza in una riga sola: 30 s senza
pacchetti *contro* 66 s senza che l'utente toccasse niente. Prima sarebbe stato il secondo numero a
buttare fuori l'utente.

#### ⚠ E su che cosa poggia la cura, scritto invece che sperato

⛔ **La riparazione ha un'assunzione**: che fra un pacchetto e l'altro passi meno di 30 s. Nessuno la
garantisce — i PING del trasporto sono accesi **solo** nella finestra delle credenziali, e per una
ragione scritta (`webtransport.c`, `regola_tienila_viva()`: tenerli sempre accesi cambierebbe il
significato dei 30 s di §2.2). Durante la sessione i pacchetti arrivano perché **qualcosa si muove**
— fotogrammi, cursore, riscontri — e su una scena ferma non è detto che si muova abbastanza spesso.

⇒ ⭐ **Quindi l'assunzione si sorveglia da sola**: `rcp_segno_di_vita()` scrive nel registro quando
il buco fra due pacchetti supera **metà** del tetto.

> ⛔ **Ed è la lezione della mattina applicata alla sua stessa cura**: una protezione che poggia su
> qualcosa che nessuno può guardare è la protezione che si scopre rotta da un utente buttato fuori
> mentre leggeva.

#### ⛔⭐ E LA SORVEGLIANZA HA PARLATO ALLA PRIMA CORSA

`[M]` Sessione ferma **260 secondi**, nessuno che tocca niente. ✅ Il posto ha tenuto per tutti e
260. ⛔ **Ma la riga del margine è comparsa 8 volte**, e il numero è impressionante per quanto è
regolare:

```
15:31:00.007  ⚠ §5.3: fra due pacchetti sono passati 15004 ms, e il tetto è 30000
15:31:30.016  ⚠ §5.3: fra due pacchetti sono passati 15005 ms, e il tetto è 30000
15:32:00.019  ⚠ §5.3: fra due pacchetti sono passati 15002 ms, e il tetto è 30000
```

⇒ **Quindici secondi esatti.** Un numero così preciso non è traffico: è **un keep-alive**, e ⛔ **non
è il nostro** — i nostri PING in quella finestra sono spenti. È il browser.

⚠ **Quindi il margine è 2×, e dipende dalla cortesia di Chrome.** Un browser diverso, o Chrome che
cambia quel numero, e i posti ricominciano a cadere sotto il naso di chi sta leggendo.

> #### ⛔ LA DECISIONE CHE NE ESCE, e non la prendo da solo
>
> **La cura vera**: accendere i PING del trasporto **anche a sessione attiva**, così il segno di
> vita lo produce il server su un orologio suo invece di sperare in quello del browser. ⭐ Costa una
> riga in `regola_tienila_viva()`.
>
> ⚠ **Ma la ragione per cui oggi sono spenti è scritta**, e va guardata bene:
>
> | l'obiezione scritta in `webtransport.c` | tiene? |
> |---|---|
> | *«Tenere viva la connessione SEMPRE cambierebbe il significato dei 30 secondi di §2.2»* | ⭐ **No, per il client MORTO**: RFC 9000 §10.1 rimette in moto il cronometro quando si **riceve**, non quando si manda. Un client morto non risponde ai nostri PING e muore lo stesso — e lo dice il commento stesso, due righe più sotto |
> | ⛔ **ma tiene per la scheda CONGELATA** | `SPECIFICHE.md` §5.3 promette che una scheda messa in secondo piano e congelata dal browser dopo ~5 minuti **tace, quindi si stacca**. Se il servizio di rete del browser continua a rispondere ai nostri PING mentre la pagina è congelata, quella promessa cade: il posto resterebbe occupato da uno zombie |
>
> ⇒ ⏳ **E la domanda si può misurare invece che discutere**: *una scheda in secondo piano, congelata,
> risponde ancora a QUIC?* Sei minuti di prova col browser. ⛔ Se risponde, allora la promessa di
> §5.3 sulla scheda congelata **è già falsa oggi** — perché quei 15 secondi arrivano lo stesso — e la
> decisione cambia forma.

#### ⛔ La misura è stata fatta, e la risposta è «NON LO SO» — e lo dice il contatore

`[M]` 16 agosto, scheda in secondo piano per **8 minuti e 30 secondi**, senza toccarla mai.

| | |
|---|---|
| ✅ stacchi per silenzio | **zero**, il posto tenuto per tutti e 8 i minuti |
| ✅ i pacchetti | puntuali: `15003 · 15018 · 15006 · 15001 · 15002 ms` fino all'ultimo |
| ⛔ **la scheda era congelata?** | **NO** |

⭐ **E la risposta a quest'ultima riga vale più delle prime due**, perché senza sarei uscito con una
conclusione falsa. Nella pagina era armato un contatore che batte una volta al secondo:

```
battiti: 542   ·   attesi se MAI congelata: 544   ·   JS fermo da: 0 s
```

⇒ ⛔ **542 su 544**: il JavaScript della scheda ha girato a pieno regime tutto il tempo — **non era
congelata, e non era nemmeno rallentata** (una scheda in secondo piano normale prende i timer
strozzati a uno al minuto: sarebbero stati ~9, non 542).

⚠ **Il motivo è lo strumento**: Chrome **non congela una scheda sotto automazione** — il debugger si
attacca e stacca a ogni comando, e questo la esenta. ⇒ La prova ha misurato *una scheda nascosta*,
non *una scheda congelata*, e **sono due cose diverse**.

> ⭐ **È `LEZIONI.md` §1.9 regola 2 che paga il biglietto**: il controllo positivo — *«questo
> strumento sa distinguere il caso che mi interessa?»* — è costato tre righe di JavaScript e ha
> impedito di scrivere «la scheda congelata risponde a QUIC» da una prova in cui **nessuna scheda si
> è mai congelata**.

⏳ **Quindi la domanda resta aperta, e non la può chiudere l'automazione**: serve un essere umano che
apra la pagina in un browser normale, passi a un'altra scheda e la lasci lì **dieci minuti**. Il
registro del server dice tutto il resto da sé — se compare `STACCATO per silenzio`, la promessa di
§5.3 regge e i PING sempre accesi la romperebbero; se non compare, la promessa **è già falsa oggi**.

#### ✅ L'HA CHIUSA L'UTENTE, e la promessa di §5.3 non si avvera

`[M]` 16 agosto 2026, browser dell'utente, **senza automazione attaccata** — cioè nella condizione in
cui Chrome congela davvero. Scheda in secondo piano per **undici minuti**:

```
15:54:38  posto PRESO da prova
   …      nessuno stacco, nessun congedo, nessun silenzio di QUIC
16:04:30  ⚠ fra due pacchetti sono passati 15002 ms
16:05:30  ⚠ … 15002 ms
16:06:00  ⚠ … 15002 ms
16:07:25  posto LASCIATO   (l'utente chiude la scheda: congedo pulito)
16:07:55  quic: trenta secondi di silenzio, staccato (§2.2)
```

⇒ ⛔ **La scheda in secondo piano non smette di rispondere**, e i 15 secondi arrivano puntuali ben
oltre i cinque minuti del congelamento. La riga di `SPECIFICHE.md` §5.3 — *«una scheda congelata
tace, quindi si stacca»* — è `[S]`, una **previsione** sul comportamento dei browser, e la misura la
smentisce.

⚠ **Quel che questa misura NON prova**, dichiarato: non prova che la scheda *fosse* congelata — dentro
il browser dell'utente non si può guardare. ⭐ Ma per la decisione non cambia niente: **congelata o
no, risponde**.

#### ✅ FATTO: i PING restano accesi per tutta la sessione

`regola_tienila_viva()` accendeva i PING solo nella finestra delle credenziali. Adesso li tiene
accesi finché la sessione non è `finita`.

| l'obiezione che li teneva spenti | perché è caduta |
|---|---|
| *«cambierebbe il significato dei 30 secondi di §2.2»* | ⛔ **era già cambiato, e non da questi PING**: da §6-bis l'orologio conta i **pacchetti**. «Il client c'è» vuol dire già «risponde sul filo» — i PING non aggiungono quella semantica, la rendono **affidabile** |
| *«la scheda congelata deve staccarsi»* | ⛔ misurato: **non si stacca**, undici minuti |
| ⚠ **il prezzo, dichiarato** | un client con la **pagina** morta e la **rete** viva tiene il posto. ⭐ Ma lo teneva già, e chi torna su quella scheda ritrova la sua sessione (I4). Resta scoperto solo il client che smette di rispondere **anche sul filo** — e quello si stacca ai trenta secondi come sempre |

⭐ **E il metro dell'accettazione è la riga del margine**: con i PING a 10 s il buco fra due pacchetti
non può superare i 15, quindi *«il margine si sta assottigliando»* **non deve comparire mai**.

`[M]` **Misurato, e il controllo positivo è la seconda riga:**

| | atteso | visto |
|---|---|---|
| tre minuti fermo | zero righe-margine, posto tenuto | ✅ **0 righe-margine** (prima: una ogni 30 s), zero stacchi |
| ⛔ **filo tagliato** | il posto si libera lo stesso: i PING non tengono in vita un morto | ✅ tagliato `16:13:26`, staccato `16:13:50` |

⭐ **E la riga dello stacco porta la riparazione intera in una frase:**

```
16:13:50  STACCATO per silenzio: 30701 ms senza un PACCHETTO — e l'ultimo byte
          di RCP e' di 238832 ms fa
```

⇒ **Trenta secondi** senza pacchetti contro **quattro minuti** senza che l'utente toccasse niente.
Stamattina sarebbe stato il secondo numero a buttarlo fuori.

⭐⭐ E i due orologi adesso **vanno d'accordo**: `rcp` alle `16:13:50`, `quic` alle `16:14:00` — dieci
secondi di scarto. ⛔ Stamattina divergevano di **36 secondi, e nel verso sbagliato**.

### 6-ter · ⛔⛔ E IL BANCO DELLA TELA È ROSSO DA IERI, e nessuno se n'era accorto

*Trovato il 16 agosto controllando che la riparazione dell'orologio non avesse rotto i banchi in
processo. ⭐ Non l'aveva rotto niente — era già rotto.*

`banchi/04-b31-tela.c` monta `rcp.c` **nudo** con un palco finto: **18 casi, ciascuno con l'atteso
dichiarato prima**. §04-si-comanda lo chiama il banco della tela, e
`fasi/rapporti/F5-IN-0-mandato.md` lo cita fra quelli da tenere verdi.

`[M]` Ricostruito a mano su sette versioni di `rcp.c`, una per commit:

| commit | esito | |
|---|---|---|
| `c7c57e5` | 17 / 0 | *«La tela del server prende la misura del client»* |
| `2e061f6` · `a4c26fa` · `bbc93a2` | ⭐ **18 / 0** | |
| ⛔ `477d708` | **11 / 7** | *«La tela era sbagliata dal primo istante»* — **la cura della coda dei tempi, ieri** |
| `26d463c` · `d32cda6` | 11 / 7 | oggi, identico ⇒ **non è di oggi** |

⇒ ⛔ **Sette casi su diciotto sono rossi da ieri**, e il banco non è stato rilanciato dopo la cura.
⚠ I casi caduti sono 6, 9, 10, 17 e altri tre: tutti attorno alla **misura concessa** — che è
esattamente quel che `477d708` ha cambiato, introducendo il ripiego dichiarato di §4.5 *«concessa la
tela del palco»*.

#### ⭐ La diagnosi, fatta: **una causa sola**, e il prodotto ha ragione

`[M]` Tutti e sette i rossi hanno **lo stesso identico scarto**: `richieste al palco` è **esattamente
una in più** dell'atteso.

| caso | atteso | visto |
|---|---|---|
| 1 · 6 · 9 · 10 | richieste al palco **1** | **2** |
| 2 · 5 · 17 | richieste al palco **0** | **1** |

⇒ ⭐ **È la richiesta della NASCITA**, quella che `477d708` ha aggiunto apposta e che il registro
dichiara a ogni sessione: *«§4.5: dico al palco che la tela di questa sessione è NxM — così nasce
già così invece di nascere a una misura sua e doverla cambiare (e il cambio è una gara)»*.

⚠ E il «TELA usciti 0» dei casi 1, 6, 9, 10 **non è un secondo difetto**: quei casi sono scritti
`bene = …; if (bene) { palco_consegna(…); … }`, quindi caduta la prima condizione la seconda metà
**non viene mai eseguita**. Un solo difetto, sette facce.

⇒ ⛔ **L'atteso è vecchio, il prodotto è giusto** — la **quinta** volta in due giorni che un banco
misura se stesso.

#### ✅ Riparato — e **non** sommando uno

⛔ Sommare uno sarebbe stato il gesto sbagliato: il banco sarebbe tornato verde e **cieco proprio
sulla cosa che l'aveva reso rosso**. Il giorno in cui la richiesta della nascita sparisse — cioè
tornassero i diciassette secondi di coda — i conti tornerebbero lo stesso. ⇒ Due gesti invece di uno:

1. i sette casi contano **da dopo la nascita** (`dopo_la_nascita()`), che dice a chi legge che la
   nascita esiste ed è un'altra cosa. E la riga di esito la nomina: *«richieste al palco 2 (di cui 1
   alla nascita, §4.5)»*;
2. ⭐ **il caso 19 prova la nascita per conto suo**: *«UNA richiesta al palco già con l'`ATTACCA`, a
   1600x900»*.

⭐ **E il banco riparato è stato certificato prima di fidarsene** (`CODER.md` §3.3). `[M]` Innestato
il guasto — la richiesta della nascita tolta dal prodotto:

| | |
|---|---|
| i **18 casi vecchi** | ⛔ **tutti e diciotto VERDI** — la cecità era reale, non ipotetica |
| il **caso 19** | ✅ **rosso, e solo lui** |

⇒ ✅ **19 su 19**, e il guasto è entrato in `04-b31-certifica.sh` come **G12**, che pretende rosso
esattamente il caso 19.

⭐ **E la lezione di processo è indipendente dall'esito**: il banco più forte che abbiamo su `rcp.c`
è rimasto rosso un giorno intero perché **nessuno lo lancia**. Costa due secondi:

```sh
gcc -O1 -std=gnu11 -w -D_GNU_SOURCE -o /tmp/b31 banchi/04-b31-tela.c src/rcp.c && /tmp/b31
```

### 6-quater · ✅ LA SESSIONE SENZA NESSUNO CHE GUARDA — 16 agosto 2026

*In v1 era il caso che rompeva: il monitor virtuale spariva al distacco e `libmutter` andava in
asserzione fallita. È il punto 6 di §2.*

**L'atteso, dichiarato prima**: (1) la sessione grafica resta viva e col suo PID; (2) ⛔ zero
asserzioni in `mutter.log`; (3) con nessuno che guarda, zero fotogrammi e CPU vicina a zero — ⚠ *se
il figlio continuasse a catturare a vuoto sarebbe uno spreco che non vedrebbe nessuno*; (4) al
riattacco si ritrova tutto.

#### `[M]` Due minuti con nessuno attaccato

| | |
|---|---|
| **figlio** | **2 tick in 120 s** ⇒ ~0,017 % di un nucleo |
| **gnome-shell** | 33 tick ⇒ 0,27 % |
| **fotogrammi spediti** | **0** |
| **righe nuove in `mutter.log`** | **0** — ⭐ il difetto di v1 non c'è |
| figlio · gnome-shell · terminale | tutti e tre **vivi** |

⭐ **Il confronto che dà il senso al numero**: con un client attaccato e la scena ferma il figlio
consuma **0,63 tick al secondo**; senza nessuno, **0,017**. ⇒ **37 volte meno**: il ciclo di cattura
si ferma davvero quando non guarda nessuno, non gira a vuoto.

⭐ E il figlio non tace: ogni 60 secondi scrive *«"prova" ricontrollato: uid 1001, pid 476758, padre
476313, 40 descrittori — il legame regge»*. Una sessione che nessuno guarda **dice di essere viva**.

#### `[M]` Il riattacco

| | |
|---|---|
| `gnome-shell` | **390241** — lo stesso attraverso un riavvio del server, uno stacco per filo tagliato, i due minuti di nessuno e **tre** riattacchi |
| avvii di sessione grafica | **0** ⇒ è un riattacco, non un accesso nuovo: l'utente non ha perso niente |
| primo fotogramma | **CHIAVE `0x0301`**, come §5.2 pretende |
| la tela, guardata nei pixel | **1113 colori diversi**, luminosità media 102 ⇒ non nera, non piatta |
| l'input | ✅ un `Invio` tenuto 200 ms ⇒ **18 battute** arrivate al terminale, e `cl_tasti_premuti` vuoto dopo |

⏳ **Quel che questa prova NON copre, dichiarato**: la finestra è di **due minuti**, non di ore.
⇒ L'orologio delle **6 ore di abbandono** resta da provare, ed è l'ultimo dei tre di §5.3.

⚠ E `mutter.log` contiene **7 righe `CRITICAL`** che non sono nostre: sono tutte alle 13:18 e 13:19, di
due `gnome-shell` **che si stavano chiudendo** (*«has been already disposed»*), cioè rumore di
smontaggio di GNOME al logout. Nessuna dalla sessione viva.

### 6-quinquies · ✅ L'INATTIVITÀ DEI 30 MINUTI — e come si prova un tetto lungo senza aspettarlo

> *«30 minuti di inattività va bene testare, ma le 6 ore proprio no, significa tenere il PC occupato
> 6 ore»* — l'utente, 16 agosto 2026.

⭐ **E il vincolo ha migliorato il lavoro**, perché la risposta era già scritta in `SPECIFICHE.md`
§5.3: *«il secondo e il terzo sono **configurabili**, con quei valori come predefiniti»*. ⇒ Due
verifiche invece di una, e nessuna tiene occupata una macchina:

| che cosa | come si prova |
|---|---|
| **il meccanismo** | a valori corti: `riavvia-7700.sh --inattivita-s 10` |
| **il numero in vigore** | ⭐ si **legge**, perché il server lo scrive all'avvio |

```
⭐ §5.3, i tre orologi in vigore: silenzio del client 30 s (fisso) ·
   inattivita' dell'utente 1800 s · abbandono della sessione:
   ⛔ NON ANCORA IN VIGORE, nessun codice lo conta
```

⛔ **Senza quella riga il valore predefinito non lo verificherebbe mai nessuno**, ed è la forma E1
(«scritto non è in vigore») — la stessa che stamattina è costata cara due volte.

#### ⛔ E `RCP_INATTIVITA = 0x02` era proprio quello: dichiarato e mai usato

`rcp.h` aveva il motivo di §8.2, `RCP.md` §8.2 lo documentava — e **non c'era una riga di codice che
lo spedisse**. Un motivo di congedo che un'altra implementazione avrebbe dovuto gestire per niente.

#### `[M]` Le due prove, con l'atteso dichiarato prima

| | atteso | visto |
|---|---|---|
| entro e **non tocco niente** | congedo `0x02` a ~10 s, e la pagina torna al modulo | ✅ `16:31:13 INATTIVITA': 10048 ms (tetto 10000)` · `congedo motivo=0x02` · la pagina è tornata al modulo d'accesso |
| ⛔ **controllo positivo**: un tasto ogni 4 s per 32 s | **zero** scatti finché si lavora | ✅ input alle `16:34:23 · 27 · 31 · 36`, zero scatti; poi `16:34:46.979`, **10051 ms dopo l'ultimo** |
| la sessione grafica | resta (I4) | ✅ `gnome-shell` 390241, terminale aperto, **0** avvii |

⚠ **E la prima stesura del controllo positivo misurava sé stessa** — la sesta volta in due giorni.
Lo stimolo era un `mousemove` sintetico, e al server **non è arrivato niente**: la sessione è caduta
per inattività e sembrava un difetto del prodotto. ⭐ Il registro l'ha smentito prima che scrivessi
la conclusione: `input id=` **zero**. ⇒ Rifatto con un tasto — uno stimolo già provato end-to-end
oggi — è passato.

#### ⛔ La pagina diceva la cosa sbagliata per `0x02`

Il testo era *«silenzio troppo lungo: la sessione è scaduta»*, cioè **l'altro orologio**: il silenzio
dura trenta *secondi* e non manda nessun congedo. ✅ Adesso dice *«sei stato mezz'ora senza toccare
niente: per rientrare servi tu, con la tua parola d'ordine — i programmi sono rimasti aperti»*, e
⭐ **torna al modulo d'accesso** come §5.3 pretende (*«per rientrare servono utente e password»*):
prima solo `0x10` lo faceva, e l'utente inattivo restava davanti a un desktop congelato.

#### ⏳ Il terzo orologio, e perché la corsa da 30 minuti non si fa

⛔ **L'abbandono a 6 ore non esiste ancora**, e il server lo **dichiara** invece di tacerlo.
⚠ Quando si farà, allo scadere **chiude la sessione**: i programmi aperti se ne vanno. Lo dice §5.3,
ma è la conseguenza da tenere davanti agli occhi.

⭐ **E nemmeno la corsa vera da 30 minuti si fa**, con la ragione scritta: il meccanismo è provato, e
l'unica cosa che una corsa da mezz'ora aggiungerebbe è che `1800000 ms` sono trenta minuti — che è
aritmetica, non una misura. ⇒ *Un tetto si prova sul meccanismo e si legge sul numero.*

### 6-sexies · ✅ DISTACCO E RIAGGANCIO DUE VOLTE DI FILA — 16 agosto 2026

> *«Un banco che passa solo da macchina pulita non è un banco, è una dimostrazione»* — il mandato,
> punto 5 di §2.

⇒ Quindi **cinque giri, di due specie**: tre col distacco **pulito** (la scheda si chiude, congedo
`0x10`) e due col distacco **sporco** (il filo tagliato, stacco per silenzio di §5.3).

**L'atteso, dichiarato prima**: i giri devono essere **indistinguibili fra loro**, e ⛔ *niente deve
accumularsi* — è quello il modo in cui questa roba si rompe alla seconda volta.

#### `[M]` I tre giri puliti

| | giro 1 | giro 2 | giro 3 |
|---|---|---|---|
| ms fino al desktop | 1430 | 1318 | **1164** |
| primo fotogramma | CHIAVE | CHIAVE | CHIAVE |
| **descrittori del figlio** | **41** | **41** | **41** |
| `gnome-shell` | 390241 | 390241 | 390241 |
| battute arrivate al testimone | +18 | +18 | +18 |
| tasti rimasti giù | 0 | 0 | 0 |

⭐ E i tempi **calano** invece di crescere: 1430 → 1318 → 1164 ms.

#### `[M]` I due giri sporchi — il filo tagliato

| | taglio A | taglio B |
|---|---|---|
| stacco | `30492 ms senza un PACCHETTO` | `30939 ms` |
| descrittori, prima e dopo | 41 → 41 | 41 → 41 |
| riaggancio successivo | ✅ 1245 ms, 894 colori | ✅ 2007 ms, 894 colori |

#### ⭐ Il bilancio, su tutti e sei gli attacchi

| | |
|---|---|
| primi fotogrammi, e quanti erano **CHIAVE** (§5.2) | **6 su 6** |
| avvii di sessione grafica | **0** — nessun giro è un accesso nuovo |
| smontaggi del palco | **0** — il palco sopravvive a tutti i distacchi |
| descrittori del figlio | **41**, sempre |
| `gnome-shell` | **390241**, sempre |

#### ⛔ E il difetto che è saltato fuori era il MIO, la settima volta in due giorni

Il taglio B, la prima volta, **non ha staccato**: il posto restava occupato e sembrava un difetto
grosso — *«il server non fa scattare i suoi orologi quando l'uscita è bloccata»*.

⭐ **L'ha smentito l'aritmetica, prima che scrivessi la conclusione.** Attorno al taglio A avevo messo
un guardiano di sicurezza, `(sleep 100; nft delete table) &`. Taglio A alle `16:42:53`; +100 s =
**`16:44:33`** — l'istante esatto in cui nel registro si fermano le righe `NON spedito`. ⇒ Il
guardiano del taglio A ha **rimesso il filo nove secondi dentro il taglio B**: B è durato 9 secondi,
non 40, cioè sotto il tetto.

⚠ **E la seconda stesura si è ammazzata da sola**: `pkill -f "sleep 100"` ha ucciso lo script che lo
conteneva, perché quel testo stava nella sua stessa riga di comando. ⇒ Niente guardiani in
background: **`trap ... EXIT INT TERM`**, che toglie il taglio comunque vada.

> ⭐ Rifatto pulito, il taglio B ha staccato a `30939 ms`. **Nessun difetto del prodotto** — e la
> regola resta quella di `SPECIFICHE.md` §5.9: *quando un banco è rosso, la prima cosa da sospettare è
> l'atteso* (o lo strumento).

### 6-septies · ✅ IL TERZO OROLOGIO — 60 minuti senza input, provato a 20 secondi

*Deciso dall'utente il 16 agosto 2026 (`DECISIONI.md` §4.8), e provato subito: «procedi con il tetto
dei 20 secondi».* ⭐ È esattamente il modo di provare un tetto lungo senza tenere occupata una
macchina — il meccanismo a valori corti, il numero letto nella riga d'avvio.

```
17:22:53.004  ⭐ §5.3 — ABBANDONO: «prova» non tocca niente da 20065 ms (tetto 20000)
17:22:53.004  congedo motivo=0x03
17:22:53.011  rilascio al distacco: 0 fra tasti e pulsanti
17:22:53.011  ⭐ §5.3: la sessione e' ABBANDONATA — chiudo la sessione grafica
```

| | |
|---|---|
| lo scatto | **20065 ms** su un tetto di 20000 |
| `gnome-shell` | **spenta** |
| la pagina | tornata al modulo d'accesso con *«la sessione è stata abbandonata»* |
| ⭐ il congedo `0x03` | spedito **prima** di chiudere, come l'ordine normativo di §7.6 impone |

#### ⛔ E al primo giro il registro ha detto DUE bugie — la stessa malattia di tutta la giornata

| la riga | perché era falsa |
|---|---|
| *«guardavano senza toccare niente **da un'ora**»* | il tetto è **configurabile**, e in quel giro valeva **20 secondi**. «Un'ora» è vero solo col predefinito ⇒ una riga che afferma un numero che non conosce |
| *«⭐ §7.6: **l'utente ha chiesto** di USCIRE»* | ⛔ **nessuno aveva chiesto niente**: a chiudere era un orologio. Il figlio scriveva quella frase per *ogni* chiusura, perché fino a stamattina l'unico a chiedergliela era §7.6 |

⭐ **Curate tutt'e due**, e la seconda senza aggiungere un messaggio al protocollo interno: il campo
`a` della busta era libero, e adesso porta il **perché** (`FIGLI_USCITA_UTENTE` /
`FIGLI_USCITA_ABBANDONO`). Rimisurato, le righe dicono `20065 ms (tetto 20000)` e *«⚠ Non l'ha
chiesto nessuno: è scaduto il tetto»*.

> ⚠ **È la terza volta in un giorno** che una riga di registro afferma una causa o un numero che non
> possiede — dopo `RILASCIO AL DISTACCO: 0` e il testo `0x02` della pagina. ⇒ Non è sfortuna: è che
> **una riga scritta quando esisteva un solo chiamante diventa falsa al secondo**, e nessun
> compilatore lo dice.

### 6-octies · ⭐⭐ LA PROVA CHE CONTA, E L'HA FATTA L'UTENTE — con un lavoro vero dentro

*Tutte le prove di questa giornata avevano un desktop **vuoto**. ⛔ E un desktop vuoto è il testimone
peggiore possibile per la domanda «la sessione è sopravvissuta?»: appena rinato è identico a com'era.*

L'utente, il 16 agosto 2026, con parole sue:

> *«Mi sono loggato con la finestra del browser massimizzata e ho lanciato un task nel terminale (un
> ciclo infinito), poi ho chiuso il browser. Ho ridimensionato a finestra il browser, mi sono
> ricollegato e il task nel terminale era ancora in esecuzione.»*

`[M]` Il registro, riga per riga:

```
17:30:13.541  posto LASCIATO da prova            ← chiude il browser: e' un DISTACCO
                                                   ⛔ nessun «USCIRE», nessun «avvio la sessione»
17:30:36.535  posto PRESO da prova
17:30:36.535  ⚠ RIPIEGO §4.5: chiesta 1240x622, il palco ha 2544x926 — e SOPRAVVIVE al client (I4)
17:30:36.635  ⭐ tela IN VIGORE cambiata a 1240x622        (+100 ms)
```

`[M]` E il testimone vero, che nessuna prova mia aveva:

```
PID 523560   ELAPSED 02:31   %CPU 20.8   cat /dev/urandom
```

⇒ **Il lavoro dell'utente girava da due minuti e mezzo, attraverso un distacco di ventitré secondi e
un cambio di misura.** Se la sessione fosse morta, sarebbe morto con lei.

⭐ **In una prova sola ne chiude tre**: l'invariante **I4**, il **riattacco a misura diversa**, e — la
sola che conta davvero — **la scena su cui questa fase si giudica**: *«chiude il client, va a pranzo,
riapre, e ritrova tutto com'era»*.

#### ⚠ E la distinzione che aveva insospettito l'utente, perché ingannerà anche il prossimo

L'utente aveva scritto: *«guarda che la sessione non è stata distrutta»*. ⭐ **Aveva visto una cosa
vera** — ma sono **due** cose diverse che si chiamano tutt'e due «sessione»:

| | che cos'è | destino |
|---|---|---|
| **il gestore d'utente** — `user@1001.service`, logind `8799`, `Class=manager` | il *linger*: il bus, `/run/user/1001`, i servizi d'utente | ⭐ **non muore mai**. `[M]` attivo dalle 13:13, ore prima. **È deliberato**: è la cura che ha portato il bus di sessione da **2,6 s a 18 ms** |
| **la sessione grafica** — `gnome-session`, `gnome-shell`, logind `Class=user` `remotix` | il desktop, e i programmi dentro | ⛔ **questa** muore: al logout, e allo scadere dell'abbandono |

⇒ Chi guarda `loginctl` o `/run/user/1001` dopo una chiusura **vede qualcosa di vivo e conclude che
non è successo niente**. ⛔ Il solo testimone che non inganna è il **numero di processo** di
`gnome-shell`, o un programma dell'utente che c'era prima.

### 6-novies · ✅⭐ IL SECONDO DISPOSITIVO È RESPINTO — provato da Android, 16 agosto 2026

*§05-la-sessione §1.4 dichiarava che questa strada era provata **solo su un ospite finto**:
«non prova il filo». ⇒ Provata dall'utente con un **telefono vero**, altra rete, altro motore.*

`[M]` Sessione attiva sul PC (`192.168.0.3`), tentativo da Android (`192.168.0.24`):

```
17:50:00.664  ammesso utente=prova da=[192.168.0.24]      ← la parola d'ordine era GIUSTA
17:50:00.742  posto NEGATO a prova: lo occupa un altro client di questo stesso utente
17:50:00.742  congedo motivo=0x0f — «c'e' gia' un client attaccato», stato=attesa-attacca
```

| l'atteso di `RCP.md` §8.2 | `[M]` |
|---|---|
| **prima ammesso, poi negato** — o il telefono si sentirebbe dire una bugia sulla parola | ✅ `ammesso` e poi `posto NEGATO` |
| motivo **`0x0F`**, non un errore generico | ✅ e `stato=attesa-attacca`: fermato **prima** di toccare il desktop |
| *«chi viene rifiutato è chi arriva, non chi c'era»* | ✅ i fotogrammi del PC continuavano a partire (`1571`, `1572`…) durante il rifiuto; `occupati adesso: 1`, nessun `posto LASCIATO` |
| ⭐ **`0x0F` non conta come tentativo fallito** (§4.4-bis: *«chi prova a riattaccarsi tre volte dal telefono si bannerebbe da sé»*) | ✅ **zero** tentativi contati, nessun ban |
| e la frase che legge l'utente | ✅ *«quell'utente e' gia' collegato da un altro dispositivo»*, sul modulo pulito |

⭐ **E la pagina torna al modulo**: è la correzione fatta dieci minuti prima (§6-decies). Senza,
`0x0f` avrebbe prodotto la schermata rotta — cioè un difetto al posto di un rifiuto corretto.

### 6-decies · ⛔⛔ IL MODULO D'ACCESSO SOTTO IL DESKTOP — tre segnalazioni per una causa

*L'utente, tre volte, sempre più seccato: «ho notato solo una sezione della finestra» · «devi
togliermi quella barra perché mi blocca tutto» · «ancora quella cazzo di barra del login? LEVALA!»*

⛔ **E le prime due volte ho tolto la cosa sbagliata**, guardando la schermata invece del foglio di
stile: prima la barra delle scorciatoie `⌨`, poi la striscia di diagnostica. ⚠ Andavano tolte
entrambe — il bottoncino `⌨` sta a 4 px dall'angolo in basso a sinistra, cioè dove si va a cercare le
cose del **desktop**, e si preme mirando altro — **ma non erano la causa**.

#### La causa

Il «vestito da desktop» (`body[data-schermo="acceso"]`) faceva **quattro** cose: via il margine, la
tela per prima (`order: -1`), sfondo nero, colonna flessibile. ⛔ **E non nascondeva niente.**

⇒ Titolo, avviso, **modulo d'accesso**, esito e dichiarazioni restavano nella colonna **sotto la
tela**. Le bande bianche e nere della schermata dell'utente **erano i campi del modulo** su fondo
nero, col bottone «Collegati» sotto. La pagina diventava più alta della finestra: barra di
scorrimento, mezzo desktop fuori, e i clic della fascia bassa mangiati.

⭐ **La regola era già scritta**, nel commento di `torna_al_modulo()`: *«chi accende uno stato è lo
stesso che deve saperlo spegnere; un ritorno che ripristina metà delle cose è peggio di un ritorno
che non c'è, perché sembra riuscito»*. ⛔ Nessuno l'aveva letta **al verso opposto**: *chi accende il
vestito da desktop deve nascondere quel che il desktop sostituisce.*

#### E un secondo difetto trovato per strada, dallo stesso sintomo

```js
if (mot === 0x10 || mot === 0x02) torna_al_modulo();
```

⛔ Si tornava al modulo per **due motivi su quindici**. Per `0x0c` (il server si spegne), `0x03`
(abbandonata), **`0x0f` (già collegato altrove)**, `0x07`, e gli errori di rete, la pagina restava
vestita da desktop col modulo sotto. ⇒ Adesso **ogni** `CONGEDO` torna al modulo: il discrimine non è
il motivo, è il fatto — *una sessione finita si rientra dal modulo*.

> ⚠ **E il costo del mio metodo, dichiarato**: ho riavviato il server **due volte mentre l'utente
> stava provando**, buttandolo fuori a metà (`congedo motivo=0x0c`), dopo aver detto che avrei
> chiesto. ⛔ Una correzione consegnata addosso a chi sta misurando non è una consegna: è un'altra
> variabile nella sua misura.

### 6-undecies · ⭐ LE MISURE CHE STAVANO IN `SESSIONE.md`

> ⚠ *`SESSIONE.md` è stato sciolto il 16 agosto 2026: la scaletta è andata in `SPECIFICHE.md`
> §5.9, e **undici** delle sue quattordici sezioni di misura erano già qui, voce per voce
> (§6…§6-decies) — 237 righe, buttate perché doppie. ⛔ **Queste tre no**: portano numeri che
> non si ritrovavano da nessun'altra parte, e l'ho verificato numero per numero invece che a
> occhio sui titoli. Entrano qui perché sono misure della fase 5.*

### ⏱ I tempi, misurati (16 agosto 2026, 20 giri, GPU integrata)

| fase | mediana | p90 | max |
|---|---|---|---|
| login → richiesta della sessione | 244 ms | 300 ms | 301 ms |
| ⛔ richiesta → palco montato | **2907 ms** | 16969 ms | 17885 ms |
| palco → primo fotogramma | 84 ms | 89 ms | 91 ms |
| ⭐ **TOTALE login → desktop** | **3211 ms** | 17255 ms | 18158 ms |

⭐ **Il giro tipico è 3,2 s**, e di questi ~2,9 sono `gnome-session` che si alza: quel che facciamo noi
sta in ~330 ms. ⛔ **La coda no**: circa un giro su sette costa 13-18 secondi, e sotto c'è il
**punto aperto** qui sotto.

### ⭐⭐⭐ VENTI GIRI DAL BROWSER VERO — la misura che l'utente aveva chiesto

*«Fai il login/logout almeno venti volte e misura esattamente i tempi» · «per i test usa il browser,
non il banco: è l'unico modo di misurare effettivamente quello che accade».*

`[M]` 16 agosto 2026, Chrome su questo portatile → il server, venti cicli **accesso → desktop →
`Ctrl+Alt+Fine` → conferma → modulo di accesso**, senza mai toccare il banco.

| fase | mediana |
|---|---|
| nascita del figlio → tela dichiarata dal browser | 968 ms |
| tela → avvio di `gnome-session` | 214 ms |
| avvio → palco montato | 850 ms |
| palco → **primo fotogramma spedito** | 45 ms |
| ⭐ **TOTALE, «Collegati» → desktop** | **2087 ms** |

⭐ **p90 2142 ms · minimo 1968 · massimo 2155.** ⇒ **187 ms di dispersione su venti giri**: nessuna
punta, nessun giro lento.

⭐ E le tre cose che facevano paura sono a zero:

| che cosa | quante volte |
|---|---|
| fotogrammi a una misura diversa da quella chiesta | **0** (tutti e 263 a `1552x532`) |
| «il palco non è alla tela in vigore» (il *ballo*) | **0** |
| figlio fermo ad aspettare senza provare | **0** |
| congedi `0x10` puliti | **21 su 21** |

⚠ E il **secondo fisso** dell'ammissione è quasi metà del totale (968 ms su 2087): è la difesa dalla
forza bruta — senza, si leggerebbe **col cronometro** la differenza fra «l'utente non esiste» e «la
parola è sbagliata», che §4.4 vieta di dire a parole.

#### ⭐ E il caso peggiore: il primo accesso della giornata

`[M]` Stessa prova col browser, ma con **la sessione grafica mai avviata** — nessun desktop in
memoria, tutto da freddo:

| | |
|---|---|
| nascita del figlio → tela dal browser | 1074 ms |
| tela → avvio di `gnome-session` | 229 ms |
| avvio → palco | 952 ms |
| palco → primo fotogramma | 98 ms |
| ⭐ **TOTALE a freddo** | **2353 ms** |

⇒ ⭐ **Il caso peggiore riproducibile è 2,4 secondi**, non diciotto. ⚠ E il criterio è dell'utente:
*«se il tempo medio fra la parola d'ordine e la comparsa del desktop è circa 2 secondi va bene. Ma
non va bene se i secondi diventano 18»*.

### ⚠ Quel che ancora NON è a posto, dichiarato

- ✅ ~~La voce «Power Off» resta nel menu~~ — **chiuso dall'utente il 16 agosto 2026**: *«il menù di
  sistema è corretto. L'utente non può spegnere, riavviare o mandare in standby la macchina»*.
  ⭐ **Tre voci su quattro sono sparite** (Riavvia, Sospendi, Iberna) `[M]`, e le quattro azioni sono
  negate a chi conta — chiesto **dal figlio, che è l'utente vero**: `CanPowerOff = CanReboot =
  CanSuspend = CanHibernate = no`. ⇒ §4.7 chiedeva che **nessuno possa spegnere**, e nessuno può.
  ⚠ Resta la voce a schermo, e chi la preme si vede rifiutare da logind.
  ⛔ **E la causa che questo documento le attribuiva è SMENTITA da una misura**: diceva «una cache di
  gnome-shell letta all'avvio». `[M]` La sessione delle 17:13:07 del 16 agosto è nata **molto dopo**
  che le regole polkit erano in vigore, e la voce c'è lo stesso. ⇒ La causa vera **non è accertata**,
  e non si insegue: il difetto è cosmetico e l'utente l'ha giudicato accettabile.
> ### ⭐⭐⭐ LA CODA: TROVATA, ed è il ridimensionamento contro una scena ferma
>
> `[M]` 16 agosto 2026, registro pulito e figlio finalmente **parlante** (vedi sotto). In un giro
> lento:
>
> - fotogrammi spediti: **uno solo, e a `1920x1080`** — cioè alla tela di **riserva**, non a quella
>   chiesta dal cliente (`2544x926`);
> - righe «TELA NUOVA DAL PALCO»: **zero** — il ridimensionamento **non è mai avvenuto**;
> - e il ciclo lo diceva: *«1 fotogrammi consegnati, **3538 attese a vuoto** (scena ferma: Mutter
>   consegna solo quando qualcosa cambia)»*.
>
> ⇒ ⛔ **Il palco nasce alla tela sbagliata.** Il figlio viene generato con `1920x1080` (il valore
> della tabella dei figli) **prima** che il cliente dichiari la sua finestra, monta il palco a quella
> misura, e spedisce una chiave sbagliata. Poi arriva `2544x926` e serve un ridimensionamento —
> ⛔ **ma su Wayland il ridimensionamento si compie solo quando il compositore consegna un
> fotogramma nuovo, e su un desktop appena nato non cambia niente.** ⇒ Si aspetta che qualcosa si
> muova da sé.
>
> ⭐ **E questa è la causa comune di tutti i sintomi che l'utente ha elencato il 16 agosto**: bande
> nere (fotogramma alla misura sbagliata), «desktop rotto», «nessun input» (la regione del puntatore
> segue la tela), «ci mette molti secondi». ⚠ B5 e B6 di questa tabella lo dicevano già a parole; la
> cura scritta (`rcp.c` §4.5, dire al palco la tela) **arriva troppo tardi**, perché il figlio ha
> già montato.
>
> ⇒ ⭐ **La cura**: il figlio non fa nascere la sessione né monta il palco **finché non sa la tela del
> cliente**. ⚠ Con un tetto (`TELA_ATTESA_MS`), perché I1 vieta di stare fermi per prudenza: se il
> cliente non la dichiara, si parte col ripiego e lo si **dichiara**.
>
> ### ⭐⭐⭐ E la misura, 20 giri, prima e dopo
>
> | fase | ⛔ prima | ⭐ dopo |
> |---|---|---|
> | login → richiesta | 244 ms | 1192 ms |
> | **richiesta → palco** | 2907 ms · p90 **16969** | **900 ms** · p90 950 |
> | palco → 1° fotogramma | 84 ms | 85 ms |
> | ⭐ **TOTALE al desktop** | 3211 ms · p90 **17255** · max **18158** | **2164 ms** · p90 **2242** · max **2294** |
> | fotogrammi alla misura sbagliata | 1 su 1 a `1920x1080` | ⭐ **nessuno**: tutti a `2544x926` |
>
> ⇒ ⭐ **Mediana −33%, p90 −87%, massimo −87%.** E i venti giri stanno fra **2067 e 2294 ms**: la
> dispersione totale è **227 ms**, cioè il tempo del desktop adesso è un *numero*, non un intervallo.
>
> ⚠ `login → richiesta` cresce da 244 ms a 1192 perché adesso il **secondo fisso** dell'ammissione
> sta sul percorso critico: la sessione non può nascere prima che il cliente sia ammesso e abbia
> dichiarato la finestra. ⭐ Ed è pagato con gli interessi dal pezzo dopo.

- ⛔⛔ **LA CODA: un giro su sette costa 13-18 secondi** — ⭐ **causa trovata**, vedi il riquadro qui
  sopra. Qui resta il diario di come ci si è arrivati, che vale più della causa. `[M]`
  Quel che si è ESCLUSO con la misura, e ognuno era una diagnosi che sembrava giusta:

  | ipotesi | come è stata esclusa |
  |---|---|
  | l'attesa che raddoppia (1→2→4→…→30 s) | ⭐ era **vera** e curata (vedi sotto), ma la coda resta |
  | il gestore d'utente che rinasce | curato col **linger**: bus 2,6 s → **18 ms** `[M]`, coda invariata |
  | il sondaggio a Mutter da 5 s | tetto sceso a 400 ms, coda invariata; e `[M]` quel tetto non scatta mai |
  | un passo lento dentro `prendi_il_palco` | ⏱ i tre cronometri **tacciono**: nessun passo sopra 250 ms |
  | il figlio che aspetta invece di provare | ⏳ **nessuna riga**: non sta aspettando |

  ⇒ ⚠ Nei 17 secondi il figlio **non scrive niente, non aspetta e non ha passi lenti**: le tre cose
  insieme non tornano, quindi manca ancora un pezzo di strumentazione. ⭐ **Il sospettato che
  resta**, ed è l'unica regione non ancora cronometrata: il **montaggio della cattura dopo
  `mutter_apri`** — `ATTESA_AVVIO_S 10` in `cattura.c` e `ATTESA_NODO_MS 10000` in `mutter.c`.
  Dieci secondi più l'avvio del compositore fanno proprio i diciassette.

  ⛔⛔ **E LA RAGIONE PER CUI CI SONO VOLUTE SEI DIAGNOSI È UNA SOLA, ed è la peggiore possibile:
  il figlio non aveva la parlantina.**

  `[M]` Il figlio **non è un `fork`**: è un `execve` di `remotix-figlio`. ⇒ Non ereditava il
  flag `--parlantina`, e **ogni `registro_dettaglio()` di `figlio.c` finiva nel nulla, in silenzio,
  senza un errore.** ⚠ Metà della strumentazione di quel file non è mai arrivata al registro.

  ⭐ E ha mentito nella direzione peggiore: cercando la coda, ho concluso per ore che certi rami
  «non scattavano mai» *perché la loro riga non compariva* — mentre scattavano eccome. ⇒ È la forma
  **E8** (`LEZIONI.md` §1.9) dentro lo strumento che serve a smascherarla: «non l'ha fatto» e «non
  me l'ha detto» con la stessa faccia.

  ⇒ *Una diagnostica che tace non è neutra: **mente**.* E la prima cosa da verificare su uno
  strumento non è che dica il vero, è che **dica**.

- ⭐ **Curato**: l'attesa fra un tentativo e l'altro raddoppiava fino a 30 s **anche mentre un
  cliente stava a guardare uno schermo fermo**. `[M]` Il registro: *«attesa in corso 30000 ms,
  nascita chiesta 0 ms fa»* — e i due numeri insieme dicono tutto: raddoppiava, e la guardia non
  poteva scattare perché si arma solo quando la sessione risulta **morta**, mentre i giri lenti sono
  proprio quelli in cui la precedente **sta ancora chiudendo** (`State=closing`). ⇒ Adesso: se
  qualcuno guarda, si riprova ogni **200 ms**. p90 da 21,2 s a 17,3 s, e le punte a 30 s sparite.

### 7 · Il giudizio dell'utente

*(la fase si chiude qui, non su un documento completo)*

### ✅ CHIUSA IL 16 AGOSTO 2026 — autorizzata dall'utente

⛔ **Non si scrive un verdetto che l'utente non ha dato.** Qui sotto ci sono le sue parole, con la
data, e niente altro.

| quando | che cosa ha detto | su che cosa |
|---|---|---|
| 16 ago | *«Se il tempo medio tra l'inserimento della password e la comparsa del desktop è circa 2 secondi va bene. Ma non va bene se i secondi diventano 18»* | il criterio dei tempi — `[M]` mediana **2087 ms**, peggiore caso a freddo **2353 ms** |
| 16 ago | *«Mi ritengo più che soddisfatto così»* | i tempi, dopo la misura |
| 16 ago | *«Il menù di sistema è corretto. L'utente non può spegnere, riavviare o mandare in standby la macchina»* | §1.1 e `DECISIONI.md` §4.7 |
| 16 ago | *«Niente timeout delle 6 ore: se dopo 60 minuti non c'è traccia di input la sessione viene killata»* | il terzo orologio — `DECISIONI.md` §4.8 |
| 16 ago | *«Funziona»* · *«Il desktop copre per intero lo schermo»* | il riattacco a misura diversa (§1.3) |
| 16 ago | *«Il task nel terminale era ancora in esecuzione»* | ⭐ la scena su cui la fase si giudica (§6-octies) |
| 16 ago | *«Possiamo considerare chiusa la fase 5?»* → **«procedi»** | la chiusura |

#### ⏳ Quel che resta — ripulito col criterio dell'utente

> ⛔ *«Se i punti non toccano il prodotto è solo rumore burocratico»* — l'utente, 16 agosto 2026.

⭐ **E ha ragione**, e questo elenco è stato **tagliato** invece che difeso. Quel che era scritto qui
e non cambiava niente è stato tolto, non spostato:

| tolto | perché non era un debito |
|---|---|
| ~~«due strade di §7.3 su quattro»~~ | passano tutte dallo **stesso imbuto** (`rilascia_al_distacco` + `inp_rilasciato`), e l'imbuto è esercitato due volte. Coperte per **costruzione**, non da provare |
| ~~le tre code della fase 4~~ | le stavamo **traslocando da due fasi**. Se nessuno le fa non sono un elenco: sono un modo di non decidere. ⇒ Restano dove sono nate, in §04-si-comanda |
| ~~«la latenza va rimisurata»~~ | non è un punto aperto: è **un numero che non abbiamo**. Si prende quando serve un numero |

**Resta questo, e sono due cose sole:**

1. ⭐ **`0x05` — l'utente ha già una sessione grafica LOCALE.** È l'unico pezzo di prodotto della fase
   mai uscito su una scena vera: il banco lo prova con sessioni finte create da PAM, perché alla
   consolle di quella macchina non si è mai seduto nessuno. ⇒ Si chiude come si è chiuso `0x0F`:
   **con una persona**, che entra sul desktop locale e poi tenta da remoto;
2. ⏳ **Un banco per il puntatore dopo il ricambio dei dispositivi.** ⚠ Non è carta: al cambio di
   geometria `libei` distrugge e ricrea i dispositivi assoluti e **il puntatore vecchio smette di
   funzionare senza errore** (`STUDI.md` §gnome §9). Oggi è stato provato con le mani dell'utente e passa.

#### ⭐ E la cura al «banco che nessuno lancia», che è la stessa obiezione

`[M]` `04-b31-tela.c` — 19 casi sul modulo più delicato — è rimasto **rosso per un giorno intero**
perché nessuno lo lanciava. ⛔ Un banco che nessuno lancia **è** rumore burocratico.

⚠ E la cura **non è un lanciatore**: di banchi che si giudicano da soli e girano senza macchina ce
n'è **uno**, e uno script per lanciarne uno è la stessa burocrazia con un altro nome.

⇒ **Gira da sé, dove si passa comunque**: `src/costruisci-in-contenitore.sh` lo compila e lo esegue a
ogni costruzione, in due secondi.

```
⭐ costruito: …/src/remotix
⭐ 04-b31 (la tela,  passati 19, falliti 0):
```

⛔ E **non ferma la costruzione**: il binario c'è e può servire. Ma il rosso si vede — ed era l'unica
cosa che serviva.

#### ⭐ La lezione della giornata, in una riga

> **Una riga di registro scritta quando esisteva un solo chiamante diventa falsa al secondo, e nessun
> compilatore lo dice.**

`[M]` Tre volte in un giorno, sulle protezioni più importanti che abbiamo: `RILASCIO AL DISTACCO: 0`
che non poteva dire altro; il testo `0x02` della pagina che nominava l'orologio sbagliato;
*«l'utente ha chiesto di USCIRE»* detto da un orologio. ⇒ Ed è la stessa forma di `LEZIONI.md` §1.9,
che adesso ha la sua **quinta regola**.

⚠ **E il corollario, pagato sette volte oggi**: quando una prova è rossa, la prima cosa da sospettare
è **lo strumento** — l'atteso vecchio del banco della tela, il guardiano `sleep 100` che rimetteva il
filo dentro il taglio successivo, il `mousemove` sintetico che non arrivava, il filtro sul timestamp
di una riga che il timestamp non ce l'aveva, il contatore che ha svelato che Chrome non congela una
scheda sotto automazione.
