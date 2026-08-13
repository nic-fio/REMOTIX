# CORSIA K — le marche che restavano, misurate

*13 agosto 2026, sera. CHUWI, porte **7625 · 7626 · 7627**, copia in `banchi/01-b12-copie/`.
Mandato: **refutare**, non verificare.*

> ## ⭐ IL CONTO, IN UNA RIGA
>
> | | |
> |---|---|
> | banchi certificati stasera | **3** — `03-deposita` · `03-scena` · `03-marca` (rigirata) |
> | marche **misurate** | **2** — e sono nel riquadro qui sotto, da copiare a catalogo |
> | cure scritte | **2** — le due righe di `03-deposita`, e il codice d'uscita di `03-b19` |
> | ⛔ resta `[?]` | **1** — la marca di `03-b19`, che è a TEMPO e vuole la finestra esclusiva |
> | ⛔ una nota di catalogo **smentita con un caso** | «la cura di `03-b19` non si può provare da qui»: si può, ed è provata |
> | porte protette | **7448 · 7501 · 7561** — contate su NIC-OS prima (1·1·1) e dopo (1·1·1). **Non toccate** |

---

## ⛔⛔ DA SCRIVERE A CATALOGO — e lo fa il coordinatore, non io

`banchi/01-b12-guasti.py` **non è nel mio perimetro**. Le due stringhe qui sotto sono **misurate**,
non dedotte dal sorgente: sono state contate nei log dei giri, e il conto è *0 nel sano, 1 nel
guasto*.

| voce | campo `marca` — la stringa **esatta** |
|---|---|
| **`03-deposita`** | `il deposito si TRONCA invece di crescere` |
| **`03-scena`** | `P7 la scena si muove — disegni consecutivi` |

⚠ Il trattino di `03-scena` è un **trattino lungo** (`—`, U+2014), non un meno: è il separatore che
`03-marca-certifica.py` usa nell'elenco dei controlli caduti, ed è quello che distingue la riga
rossa da quella verde (la verde separa con degli **spazi** di riempimento).

| stringa | sano | guasto |
|---|---|---|
| `il deposito si TRONCA invece di crescere` | **0** | **1** |
| `P7 la scena si muove — disegni consecutivi` | **0** | **1** |
| `"delta_istante_us": [0, 0]` *(la seconda candidata di `03-scena`)* | 0 | 1 |

⛔ **Perché ho scartato `"delta_istante_us": [0, 0]`**, che pure è la più bella perché mostra il
*meccanismo*: il numero di delta dipende da **quanti fotogrammi** il giro ha scaricato (tre ⇒ due
delta). Con quattro fotogrammi diventerebbe `[0, 0, 0]` e la marca morirebbe **in silenzio**. Quella
scelta non dipende dal conto. ⇒ La cito qui perché chi legge un rosso di P7 sappia dove guardare.

⚠ E la marca di `03-scena` poggia sul formato di stampa dell'elenco dei caduti: se qualcuno lo
riscrive, la marca muore — ma muore **rumorosamente**, dando 0 anche nel giro guasto, e `--giudica`
se ne accorge invece di certificare lo stesso. È la stessa riserva già scritta su `03-b15`.

---

## 🅚3 — `03-deposita`: le due righe che mancavano, e la certificazione

### Il buco, riletto e confermato

Il catalogo diceva: *«nessuno rilegge `03-scena-esiti.jsonl`»*. **È vero, e l'ho verificato
girando**: `03-scena-certifica.sh` leggeva gli esiti del **metro** in `$LAV` (che sta su tmpfs) e il
deposito lo **scriveva e basta**. Il guasto di catalogo — `open(esiti, "w")` invece di `"a"` —
lasciava il giro **tutto verde**: la riga a schermo è identica, `03-deposita.py` esce **0**, e a
sparire è la **storia**.

### La cura — `banchi/03-scena-certifica.sh`

Due controlli nuovi, **P18** e **P19**, in fondo al giro `tutto`:

- **P18 · il deposito CRESCE in coda.** Si contano le righe **prima** delle scritture di M6 e M8 e
  **dopo**, e si pretende `dopo == prima + <scritture chieste>`.
- **P19 · e l'ultima riga si RILEGGE.** Si riapre il deposito, si prende l'**ultima** riga e si
  pretende `marca = "M8/giro"`, `quanti_giri = 4`, catena dichiarata presente.

⭐ **E la metà che si dimentica, che è il pezzo che ho aggiunto io alla ricetta del catalogo**: con
**una sola** riga depositata, *«cresciuto di uno»* e *«troncato all'ultima»* danno **lo stesso
numero**. ⇒ Sotto le due scritture P18 dichiara **NON ESEGUITO** e conta come fallito, invece di
passare. Un controllo che non può diventare rosso non è un controllo — ed è la trappola n. 3 di
questo progetto, che stavo per rifare io.

⛔ E si contano i depositi **chiesti**, non quelli **riusciti**: se `03-deposita.py` fallisse, il
file avrebbe una riga in meno e P18 lo direbbe. Contare i riusciti avrebbe fatto sparire il guasto
**insieme alla riga**.

### I tre passi

| passo | uscita | controlli | che cosa dice P18 |
|---|---|---|---|
| **sano** | **0** | 21 su 21 | `⭐ P18 · il deposito CRESCE in coda: 1 → 3 righe (+2)` |
| **guasto** | **1** | 20 su 21, **e il caduto è P18 e solo P18** | `⛔ P18 · il deposito è passato da 1 a 1 righe, e ne erano attese 3` |
| **risanato** | **0** | 21 su 21 | come il sano |

`03-deposita.py` tornato **`414eda9d808d57bd4a8a9c89b5f00bc9a7129caec12f94a938ab93d42e24ec9e`**,
byte per byte l'originale (verificato con `--togli`, che riverifica per impronta).

⭐ **E P19 resta VERDE nel giro guasto, ed è giusto così**: l'ultima riga *è* intatta — a sparire è
tutto quel che c'era prima. Le due metà misurano due cose diverse, e il fatto che solo una cada è la
prova che non si stanno sovrapponendo.

---

## 🅚2a — `03-scena`: la marca, misurata

Il guasto congela l'istante dipinto nella marca. Il catalogo prevedeva: *«l'unico che può vederlo è
P7, che confronta gli istanti in senso STRETTO»*. ⭐ **La previsione regge, e adesso è misurata**:

| passo | uscita | controlli | P7 · `delta_istante_us` |
|---|---|---|---|
| **sano** | **0** | 21 su 21 | `[17126, 16411]` |
| **guasto** | **1** | **20 su 21, e il caduto è P7 e solo P7** | **`[0, 0]`** |
| **risanato** | **0** | 21 su 21 | `[16636, 16763]` |

`03-scena.c` tornato **`2ba6b8e73032edf03f7ac18b3ca054bc0a30d9d90b8a68ffad4f620c36ee8512`**, byte
per byte l'originale.

⭐ **E la previsione «nessun sintomo altrove» regge alla misura**: i `disegni` restano consecutivi
(`120, 121, 122`), i **pixel cambiano** (12 528 per fotogramma), il CRC è giusto, M6 e M8 restano
verdi. ⇒ Un attrezzo di scena che sbaglia **non fa arrossire niente**: avvelena e basta. È la
ragione per cui questa voce è a catalogo, ed è la ragione per cui la marca serviva.

⚠ **L'effetto collaterale dichiarato dal catalogo si è visto e non ha morso**: con l'istante
congelato `disegni_al_secondo` esce nullo nella lettura da fuori. Non ha fatto cadere nessun
controllo — P13 confronta `fidato` e `callback_in_volo_massimo`, che non passano di lì.

---

## 🅚2b — `03-b19`: la cura al codice d'uscita, **e la nota di catalogo che ho smentito**

### ⛔⛔ La nota diceva che non si poteva provare da qui. Si può — ecco il caso

Il catalogo scriveva, sulla voce `03-b19`:

> *«NON È STATO CURATO, E IL MOTIVO È UNA REGOLA DI CASA: la cura sarebbe una riga, ma per provarla
> servono la macchina di prova e la scena di P1, che da CHUWI non c'è.»*

⛔ **La regola di casa è giusta; la premessa è falsa.** Il percorso `--verdetto` **non misura
niente**: rilegge un **verbale già salvato su disco**. E sul disco di CHUWI ce n'erano **quattro**,
tutti da giri veri del 13 agosto:

| verbale | i sette controlli | uscita **prima** | uscita **dopo** |
|---|---|---|---|
| `/tmp/03-b19/verbale-PRIMA.json` | P5 rosso | **0** | **1** |
| `/tmp/03-b19/verbale-DOPO.json` | P3 e P5 rossi | **0** | **1** |
| `/tmp/03-b19/verbale-PRIMA2.json` | P1 e P5 rossi | **0** | **1** |
| `/tmp/03-b17/verbale.json` | P5 rosso | **0** | **1** |

⇒ Quattro casi rossi che uscivano **verdi a macchina**, su quattro. Il difetto c'era davvero e la
cura lo chiude.

### ⭐ E il controllo negativo, che è la metà che si dimentica

Un `return 1` incondizionato avrebbe dato gli stessi quattro numeri. ⇒ Percorsa la **stessa strada**
(`--verdetto` su un verbale **vero**) col solo `giudica()` forzato a tornare tutto verde:

```
verbale VERO (P5 rosso)             → uscita 1
stessi passi, giudizio TUTTO VERDE  → uscita 0
```

⛔ **Non ho fabbricato una misura**: la misura è quella vera, e a essere forzato è il solo giudizio,
per vedere se la riga nuova **sa ancora dire 0**. Sa.

### La riga

`banchi/03-b19-ritardo-worker.py`, percorso `--verdetto`:

```python
g = stampa_verdetto(v, a)
return 0 if all(g[k].get("esito") for k in TUTTI) else 1
```

⭐ **E non è inventata**: è la **stessa identica riga** con cui `misura()` chiude la propria strada.
Le due leggono lo stesso `g` dallo stesso `giudica()` ⇒ rileggere un verbale salvato e misurarlo dal
vivo adesso danno **lo stesso codice d'uscita**, che era il punto.

⇒ **I tre `return 0` che escono sempre verdi sono adesso ZERO.**

### ⛔ E una cosa nuova, trovata cercando la marca: **l'uscita 4 ha TRE cause**

Il catalogo dà `atteso_guasto = 4` per `03-b19`. Ma nel sorgente ci sono **tre** `return 4`, e sono
tre cose diverse:

| dove | quando |
|---|---|
| la pagina non arriva a `window.REMOTIX` | il palco è rotto |
| il **prologo** del banco non è entrato | lo strumento è rotto |
| ⭐ è stato chiesto `?video=worker` e **nessun bersaglio worker si è fatto agganciare** | ← **questa è quella che il guasto produce** |

⇒ **Un `atteso_guasto = 4` senza marca non attribuisce niente**: è esattamente la forma che
`--giudica` rifiuta. La marca dovrà venire dalla **terza** riga, e ⛔ **va LETTA dal giro rosso, non
copiata dal sorgente da me adesso** — sarebbe la forma d'errore pagata su B4 e B7, e questo rapporto
esiste per non ripeterla. Ho scritto **dove guardare**, non che cosa troverà.

---

## ⏳ LA FINESTRA ESCLUSIVA — quel che CHIEDO, invece di prendermela

`03-b19` misura un **tempo** ⇒ la sua marca si prende in **finestra esclusiva**, o si misura la
contesa e la marca è finta.

⭐ Ho girato l'arbitro nuovo, `banchi/03-solo.py`. In questo momento dice **`solo: true`** (carico
0,67 / 1,25 / 1,41 · nessuna porta `:76xx` altrui · nessun processo del prodotto · 1 451 MB liberi
in `/tmp`). ⛔ **Non me la prendo lo stesso**, e non per prudenza: perché la finestra non basta.

**Che cosa serve davvero, ed è più della finestra:**

| | |
|---|---|
| ⛔ il `dove` del guasto **non esiste su CHUWI** | è `banchi/03-b17-src/src/pagina.html`, la copia che `03-b17-lancia.sh porta` srotola **sul server**. Verificato: `ls` dice che non c'è |
| il prodotto sul server | costruito e acceso, con porta, ban, socket e registro propri |
| ⚠ il giro va lanciato **con `--video-worker`** | senza quell'interruttore il ramo non viene percorso e il banco resta verde — *e sembrerebbe che non veda* |
| ⚠ `atteso_sano = 1`, non 0 | perché **P5 è falso** in tutt'e tre i giri registrati, ed è una cosa **dichiarata**, non un difetto |
| ⛔ e il banco da usare è quello **CURATO di stasera** | prima della cura il `--verdetto` usciva sempre 0 |

⇒ **Chiedo al coordinatore**: la finestra esclusiva **più** la macchina di prova, per tre giri
(sano → guasto → risanato) di `03-b19` con `--video-worker`. È l'unica cosa del mio mandato che non
ho potuto chiudere.

⚠ **E la nota di metodo che il coordinatore mi ha passato vale qui più che altrove**: se il giro
*sano* parte da una macchina non libera, il verdetto giusto **non è «rosso»: è «non giudicabile»**.
Chi prenderà la finestra deve scrivere la scena di `solo.guarda()` **accanto** al numero, e
`solo.confronta(prima, dopo)` ai due estremi.

---

## 🅚 la RIGIRATA di `03-marca` — l'ho fatta scadere io, e l'ho rimessa

Il coordinatore me l'ha segnalato: `03-scena-certifica.sh` è nei **file che contano** di `03-marca`,
e appena l'ho toccato la sua certificazione ha smesso di valere. ⭐ **Rigirata**, sulla porta 7627 e
con il file nuovo dentro:

| passo | uscita | controlli |
|---|---|---|
| **sano** | **0** | 21 su 21 |
| **guasto** | **1** | 20 su 21, **e il caduto è P5**, cioè esattamente il setaccio disarmato |
| **risanato** | **0** | 21 su 21 |

Marca `{"lette_a_torto": [{"cella"` — **0 nel sano, 1 nel guasto**. `03-marca.py` tornato
`5d7fa2783c968076d76c6f84adf53799d1c489f9772b53e009a8f3b41408fce7`.

### ⭐ E il conto di che cosa **altro** ho fatto scadere: zero

| file che ho cambiato | lo contano | stato |
|---|---|---|
| `03-scena-certifica.sh` | `03-deposita` · `03-marca` · `03-scena` | ✅ **tutt'e tre certificati stasera col file nuovo** |
| `03-b19-ritardo-worker.py` | `03-b19` soltanto | ⚠ **mai certificato**: non c'è niente da far scadere |

⛔ **E `03-scena.c` NON l'ho cambiato**: il guasto è stato innestato e tolto **nella copia**, e
l'originale è tornato alla stessa impronta. ⇒ **`03-b17`, che lo conta, non scade per mano mia** —
ed era il rischio vero, perché `03-b17` è stato certificato stasera dalla corsia C.

---

## 📋 LA SCHEGGIA DI REGISTRO

`banchi/01-b12-registro-K.jsonl` — **una riga**, scritta **senza toccare `01-b12-guasti.py`**:
il catalogo è stato importato come modulo, `REGISTRO` puntato alla scheggia, e `giudica()` chiamata
com'è. Il registro comune `01-b12-registro.jsonl` **non è stato aperto in scrittura**.

```
OK  03-deposita  ⭐ certificato: 0 → 1 → 0
OK  03-marca     ⭐ certificato: 0 → 1 → 0
OK  03-scena     ⭐ certificato: 0 → 1 → 0
```

⛔⛔ **E la riga porta dentro di sé la propria condizione**, scritta nel campo `scena`: le due marche
**non sono ancora a catalogo**, e per far girare `giudica()` le ho messe **in memoria**. ⇒ *Questa
riga vale quando il coordinatore avrà scritto le due stringhe nelle due voci.* Se non le scrivesse,
la riga direbbe «certificato» su un criterio che il catalogo non applica — e sarebbe la trappola
dello strumento che produce il proprio verde. **L'ho scritto dentro la riga, non solo qui.**

---

## 👁 I PUNTI CIECHI — la proposta, e comincia con quel che **NON** va legato

`--punti-ciechi` dice: **4 coperti · 2 per gemellaggio · 4 sulla carta · 22 ciechi**.

> ### ⛔⛔ LA PARTE CHE VALE DI PIÙ È LA LISTA DEI NO
>
> La tentazione è legare `rcp.h` a B3/B5/B6/B7, `trasporto.c` a B2, `comando.c` a B8. ⛔ **Sarebbe
> falso, e il registro lo dimostra riga per riga**: quei banchi sono certificati **contro
> l'INNESTO** (`bsslserver`, `b2/ngtcp2/build/examples`), **non contro il prodotto** — e **B9**
> contro i **DOCUMENTI** (`RCP.md`), senza nemmeno un server acceso.
>
> ⇒ Legare un file di `src/` a loro farebbe **due danni insieme**: farebbe scadere una
> certificazione per un file che quel giro **non ha mai guardato**, e — peggio — farebbe smettere
> `--punti-ciechi` di dire «cieco» su file che **restano ciechi**. È la riga «sulla carta»
> fabbricata apposta, dentro lo strumento che esiste per non fabbricarne.

### ⭐ I legami che PROPONGO — in ordine di quanto reggono

| # | file | a chi | la ragione, e da dove viene |
|---|---|---|---|
| **1** | `certificati.c` · `certificati.h` · `tls.c` · `tls.h` | **B13** | ⭐ **il più difendibile di tutti**. B13 è certificato **contro il prodotto** (registro: *«prodotto — remotix … NIC-OS 192.16…»*), e il suo guasto fa diventare **UNO** i due certificati. `certificati.h` dice *«I DUE CERTIFICATI, E SONO DUE»*; `tls.h` dice *«i due contesti TLS, uno per ascoltatore»*. Il guasto e i due file parlano **della stessa cosa** |
| **2** | `aiutante.c` · `aiutante.h` | **B10** | B10 è certificato contro il prodotto e rimette **la guardia pre-PAM**; `aiutante.c` è *«il processo che interroga PAM al posto del filo unico»*. È il cammino che B10 percorre |
| **3** | `pagina.h` | **P1** · **P5** | `pagina.c` è **già** contato da tutt'e due: `pagina.h` è la sua interfaccia, e non può cambiare senza che cambi quel che i due giri hanno provato. È il legame che costa meno e mente di meno |
| **4** | `registro.c` · `registro.h` · `trasporto.c` · `trasporto.h` · `comando.c` · `comando.h` · `rcp.h` · `webtransport.h` | **P1** | P1 **costruisce il prodotto dai sorgenti e lo accende**. `[M]` letto in `src/main.c`: al giro d'avvio e nel ciclo principale chiama `registro_dice`, `trasporto_leggi/scaduti/chiudi`, `pagina_muovi/chiudi`, `comando_muovi/chiudi`, `aiutante_*`, `certificati_ruota_se_serve`, `tls_contesto_quic`. ⇒ un'accensione li attraversa **tutti** |

⭐ **E di queste, tre sono già mezze misurate**: P1 pretende **tre marche** nel binario nuovo —
`NON-BANNATO`, `PING del trasporto`, `/etc/pam.d/remotix` — che vengono rispettivamente dal **ban**
(`comando`/`trasporto`), da **`trasporto.c`** e dal cammino **PAM** (`aiutante.c`). Quelle tre righe
sono le più difendibili **subito**.

### ⛔ E la riserva che va scritta insieme alla proposta, o la proposta è una trappola

Il punto 4 è **letto nel sorgente**, non **misurato nel banco**. Dice che il prodotto quei file li
**usa** all'accensione; ⛔ **non** dice che P1 diventerebbe **rosso** se uno si rompesse. Sono due
cose diverse, ed è la differenza esatta fra «coperto» e «sulla carta».

⇒ **Come si chiude, e costa un giro per file**: si innesta un guasto in ciascuno e si guarda **se P1
arrossisce**. Quelli che arrossiscono si scrivono; quelli che no **restano ciechi e si dice**.
Scriverli tutti adesso perché «il prodotto ci passa» produrrebbe otto righe verdi che non hanno mai
detto di no — che sono le **quattro pretese mai innestate** del catalogo delle trappole, moltiplicate
per due.

### ⛔ Quel che resta CIECO, e la cosa onesta è **dirlo**, non legarlo

`mutter.c` · `mutter.h` · `cattura.c` · `cattura.h` · `sessione.c` · `sessione.h` · `figlio.h`

Nessun banco **certificato** li attraversa. Sono il cammino del **figlio**, che si apre solo a
**sessione aperta**, e i banchi che ci passano davvero — `03-b17` e `03-b19` — sono in mano ad altre
corsie (`03-b17` è stato certificato stasera dalla corsia C ⇒ ⭐ **`figlio.c`, `webtransport.c`,
`codificatore.c` e `codificatore.h` sono appena usciti da «sulla carta»**, e vale la pena rigirare
`--punti-ciechi` dopo l'unione dei registri: il conto che ho in mano è **di prima**).

---

## ⛔ CHE COSA NON HA FUNZIONATO

| | |
|---|---|
| ⛔⛔ **il mio primo A/B della cura di `03-b19` era VERDE PER COSTRUZIONE, e l'errore era mio** | avevo scritto `python3 …; echo "… $(basename $f) → uscita $?"`. ⛔ **La sostituzione di comando dentro l'`echo` azzera `$?`**: `basename` esce 0, e ho letto «uscita 0» **su quattro giri che uscivano 1**. Per un minuto ho creduto che la cura non mordesse. ⇒ Trovato perché ho rifatto la misura **senza** la sostituzione, non perché me ne sono accorto leggendo. ⭐ **È la trappola n. 3 fatta da me, dentro l'impalcatura che serviva a trovarla**: `$(…)` e `$?` sulla stessa riga **non si mettono** |
| ⛔ **ho lavorato su tmpfs credendo di non esserci** | avevo messo `LAV` e i log sotto `~/.cache/` come diceva il mandato. ⚠ `/home/nicfio/.cache` è un **collegamento simbolico a `/tmp`** (`df` dice `tmpfs`) ⇒ **non ho spostato un byte**. Segnalato dal coordinatore, verificato, e le prove sono state **spostate su `/dev/sda2`** (`/home/nicfio/K-corsia/`). Non ci ho sbattuto contro solo perché `/tmp` era stato liberato nel frattempo (98 % → 63 %) |
| ⛔ **ho fatto scadere `03-marca` senza accorgermene** | toccando `03-scena-certifica.sh`, che è nei suoi file che contano. Non l'ho visto io: me l'ha detto il coordinatore. ⇒ **rigirata** (sopra). ⭐ Ma la lezione è che il catalogo **l'ha detto da solo**: è esattamente il mestiere per cui esiste |
| ⚠ **le mie due modifiche risultano già committate, e non da me** | `git status` non le vedeva. Sono dentro il commit `868c265` («L'arbitro della finestra esclusiva…») del coordinatore, che le ha raccolte passando. Il contenuto è intatto e verificato; **lo dico perché non sembri che io abbia committato contro il mandato** |
| ⚠ `RUMORE=300` invece di 3000 | per accorciare i giri. **Lo stesso valore in tutt'e tre i passi di tutt'e tre le certificazioni**, quindi l'A/B regge — ma P3 della marca è stato girato su **un decimo** delle scene di rumore, e va saputo |

---

## ⛔ CHE COSA RESTA `[?]`

| | |
|---|---|
| ⛔⛔ **la marca di `03-b19`** | è a **TEMPO** e vuole **finestra esclusiva + macchina di prova**. Non me la sono presa. Vedi il riquadro sopra per che cosa serve esattamente e come si lancia |
| ⛔ **P18 è cieco sotto le due scritture** | e **lo dichiara**: sotto due depositi stampa «NON ESEGUITO» e conta come fallito. ⇒ i giri `m6` e `m8` **da soli** non certificano il deposito, solo `tutto` lo fa. Non l'ho nascosto in una nota: è nel codice |
| ⛔ **il legame dei punti ciechi al gruppo 4 è LETTO, non MISURATO** | vedi la riserva. Costa un giro per file, e finché non è fatto quelle otto righe **non vanno scritte** |
| ⚠ **la seconda strada di `03-scena` resta intatta e non toccata** | `03-scena.c` porta il **proprio** guasto dentro (`--guasto rientro`) e certifica il rilevatore della **corsa a vuoto** (P13). È complementare a questa, non sostitutiva: io ho certificato la scena come **strumento di tempo**, non il rilevatore |
| ⚠ **`--punti-ciechi` va rigirato dopo l'unione** | il conto che ho in mano (4 · 2 · 4 · 22) è **di prima** che la corsia C certificasse `03-b17`, che porta a catalogo quattro dei file «sulla carta» |
| ⚠ **la catena resta quella dichiarata** | `03-scena.c → libx265 QP 40 → ffmpeg`. **Non** è la catena del prodotto: manca la cattura PipeWire di Mutter e manca la tela del browser riletta. Quel che è certificato è che lo **strumento** sa dire di no, non che la catena vera conservi la marca |

---

## 🔒 IL PERIMETRO E LE PORTE

**File toccati** — e **solo** questi:

| file | che cosa |
|---|---|
| `banchi/03-scena-certifica.sh` | P18/P19, il contatore dei depositi, l'aggancio in `tutto` |
| `banchi/03-b19-ritardo-worker.py` | la riga del codice d'uscita di `--verdetto` |
| `banchi/01-b12-registro-K.jsonl` | la mia scheggia — **nuova** |

⛔ **NON toccati**: `banchi/01-b12-guasti.py` · `banchi/01-b12-registro.jsonl` · qualunque cosa sotto
`src/` · nessun `.md` fuori da questo. Le copie in `banchi/01-b12-copie/` sono state mosse **solo**
da `--verifica`/`--applica`/`--togli` del catalogo stesso, e ogni `--togli` ha riverificato per
impronta.

**Le porte protette, contate su NIC-OS** (⚠ è **là** che ascoltano: contarle su CHUWI darebbe zero e
farebbe concludere che sono spente):

| | 7448 | 7501 | 7561 |
|---|---|---|---|
| **prima** di tutto | 1 | 1 | 1 |
| dopo `03-deposita` | 1 | 1 | 1 |
| dopo `03-scena` | 1 | 1 | 1 |
| **dopo** tutto | 1 | 1 | 1 |

⭐ **Non le ho toccate**, e non lo credo: l'ho contato. Le mie porte 7625-7627 sono **chiuse**, i
compositori Mutter **fermati**, i blocchi `/dev/shm/remotix-scena-762*` **rimossi**, `/tmp` lasciato
al **63 %** (1,5 G liberi), più libero di come l'ho trovato.

**Non ho committato.** Le prove dei giri stanno in `/home/nicfio/K-corsia/` (su `/dev/sda2`, non su
tmpfs): nove log e i depositi dei tre giri.
