# La sessione del 13 agosto, sera — che cosa è successo davvero

*Cominciata da una richiesta dell'utente: **«rileggi il piano per questa nuova sessione per
controllare che non ci siano problemi»**. ⛔ Il controllo è stato fatto **misurando lo stato invece
di ricordarlo**, e da lì è uscito tutto il resto.*

---

## ⭐⭐⭐ In una riga

**La sessione non ha prodotto il numero che doveva produrre, e ha prodotto qualcosa di più raro:
ha scoperto che tre delle righe su cui stava per costruire erano false, e le ha smentite tutte e
tre con un caso.**

⇒ E la forma si è ripetuta abbastanza da poterla nominare:

> ⛔ **Ogni riga caduta stanotte diceva una cosa vera su una domanda che nessuno aveva fatto.**
> «Su Xvfb non c'è GPU» — vero, e il banco non era su Xvfb. «`isConfigSupported` dice true» — vero,
> e rispondeva alla stringa, non ai byte. «Il profilo è stato chiesto» — vero, e non era stato dato.

---

## Le tre righe cadute, in ordine di quanto sono costate

### 1. ⛔⛔⛔ Il palco — **i banchi browser misurano sul desktop dell'utente**

| chi | quando | che cosa diceva | esito |
|---|---|---|---|
| il piano | 13 notte | *«su Xvfb non c'è GPU ⇒ è un problema di PALCO, costruiscine uno»* | ⚠ premessa giusta, conseguenza sbagliata |
| il coordinatore | 20:33 | *«non era il palco: era la **bandiera** `--disable-gpu`»* | ⛔ **mezza falsa** |
| la corsia **D** | 22:00 | ⭐ *«Chrome ignora `DISPLAY` e va su Wayland da `XDG_SESSION_TYPE`»* | ⭐ **e questa regge** |

`[M]` con la controprova che **non passa dal browser** — `xlsclients`, chi è davvero attaccato allo
schermo:

| come si lancia Chrome | clienti **sull'Xvfb** | `screen` | webgl | HEVC |
|---|---|---|---|---|
| **come lo lancia il banco** | ⛔ **0** | **2560×1080** (il monitor dell'utente) | GPU Intel | true |
| `--ozone-platform=x11` | ⭐ **1** | 1280×1024 | *niente webgl* | **false** |

⇒ ⛔ **I 74,58 ms della fase 3 sono stati misurati su un browser che condivideva schermo,
compositore e GPU con il desktop su cui l'utente stava lavorando** — e nessun verbale lo diceva,
perché il banco **non scriveva quale palco fosse**. ⭐ Adesso lo scrive, e il palco entra fra i
**campi portanti** confrontati ai due estremi del giro.

⛔ **Il palco NON è stato aggiustato**, di proposito: spostarlo fra il «prima» e il «dopo»
distruggerebbe la sottrazione. **È il primo lavoro di chi riprende, prima del prossimo «prima».**

### 2. ⛔⛔ Il codec — **il prodotto ha codificato in software per giorni per una riga di un banco**

`keyint=1` faceva emettere a libx265 **`Rext`** annullando il `-profile:v main10` chiesto quattro
righe sopra. Quelle sonde finiscono in `src/pagina.html` e decidono che cosa il client dichiara:

| chi | diceva | ed era **giusto** |
|---|---|---|
| la stringa | profilo 1 / 2 | sì, per quel che dichiarava |
| i byte | `profile_idc = 4` | ⛔ e nessuno li leggeva |
| `isConfigSupported` | **true** | sì: risponde **alla stringa** |
| il decodificatore | `EncodingError` **sui byte** | sì |
| la pagina | *«HEVC non arriva al pixel»* | sì, dato quel che vedeva |
| il server | negozia **AV1** | sì: prende la prima voce del client |

⇒ **Nessuno ha sbagliato, e il risultato era sbagliato.**

⛔⛔ **E la cura è stata sbagliata a metà**, dal coordinatore: curato il generatore delle sonde di
**presenza** e non quello delle sonde di **misura** ⇒ il prodotto è finito in uno stato **peggiore
di prima** — HEVC negoziato, HEVC che non dipinge ai gradini, `misura_massima` a **320×240**, tela
concessa 320×240 contro una cattura 1920×1080, e il prodotto che (correttamente, §6.2) **non
spedisce**. **Zero fotogrammi.**
⭐ *Quando si cura un difetto nato da una riga **copiata**, si cerca la riga, non il file.*

### 3. ⛔ La codifica AV1 in hardware **non esiste** su questa macchina

`av1_vaapi` esce **218** — *«No usable encoding profile found»* — 3 giri su 3, e `vainfo` dà AV1 in
**sola decodifica**. ⚠ Il codificatore **compare** nell'elenco di `ffmpeg`: *un elenco dice che il
codice c'è, non che la macchina lo sa fare*.
⇒ ⭐ **Restare su AV1 vuol dire restare in software per sempre.** HEVC non è una preferenza: sul
lato server è **l'unica strada verso l'hardware**.

---

## I numeri prodotti

### Il codificatore, sul cammino **seriale** del prodotto (non la portata di `ffmpeg`)

| | scena **facile** | scena **dura** |
|---|---|---|
| ⭐ **hevc_vaapi** — codifica | **2,64 ms** | **3,93 ms** |
| `libx265` software — codifica | 28,03 | 225,89 |
| `libsvtav1` software — codifica | 6,17 | 113,10 |
| ⛔ **totale seriale** hw / sw | **9,73 / 9,84** | — |

⇒ ⭐ Il tratto **crolla**, e il codificatore in hardware è **quasi indifferente al contenuto**
(+49 %) dove quello software fa **×18**.
⇒ ⛔ **Ma il totale non migliora**, perché il collo di bottiglia **si è spostato**: la conversione
dei colori costa **5,65 ms — più del doppio della codifica**. La riga *«circa otto volte più
veloce»* del piano vale **per il tratto, non per l'anello**.
⇒ ⭐ **E c'è un secondo pezzo da aggredire, che non era in programma**: `swscale` BGRx→P010,
**7,1 ms su 9,7**, candidato naturale della copia zero della fase 8.

### L'anello, rimisurato con banco e pagina nuovi

| | **software + AV1** | **hardware + AV1** | Δ |
|---|---|---|---|
| totale | **72,397 ms** (n=508) | 73,677 (n=509) | +1,28 |
| Mutter · **codifica** · filo · decodifica · disegno | 16,66 · **39,82** · 0,26 · 6,32 · 9,11 | 16,65 · **40,66** · 0,26 · 6,32 · 9,16 | ≤0,05 salvo il tratto 2 |

⭐ **Il numero della fase REGGE**: la codifica vale **39,82 su 72,4 = il 55 %**, rimisurato con
strumenti diversi da quelli che l'avevano prodotto.

⭐⭐ **E il controllo che salva la fase da una conclusione falsa**: il binario hardware **non cambia
niente** — perché la sessione negozia **AV1**, e AV1 in hardware **non esiste**. ⛔ Chi avesse acceso
l'albero della corsia B così com'era (porta la **pagina vecchia**) avrebbe scritto *«l'hardware non
serve a niente»*. **Tre alberi, una variabile per volta, e le impronte lo dimostrano.**

⇒ ⛔⛔ **Il numero della fase con la codifica in hardware NON ESISTE**, e non per mancanza di tempo:
**il codificatore hardware non riceve un fotogramma** finché la pagina non offre HEVC in modo che
regga fino alla misura. *Questa è la cosa che resta da fare, ed è la prima.*

### Il client

- ⭐ **`VideoDecoder` decodifica HEVC Main10**: **120 fotogrammi su 120**, 5 giri su 5, su **due**
  strade di confezionamento (Annex-B e `hvcC`), con quattro controlli positivi che passano per la
  stessa riga di codice. Col `--disable-gpu`: **zero**, 5 su 5.
- ⭐ **Le sonde curate del prodotto**: **16 su 16** decodificano, fino a **3840×2160**, 3 giri.
- ⛔ **Su Firefox HEVC non esiste in WebCodecs**, in nessun palco ⇒ **passare a HEVC non toglie AV1:
  lo rende obbligatorio**.
- ⭐ **Firefox 9,0 ms contro 8,2-10,7 di Chrome** (AV1 10 bit, regime seriale), 120 su 120 per
  tutt'e due. ⚠ **`[?]` per contaminazione dichiarata**: nessun giro preso da solo.
- ⭐ E i **2,7 ms** che sembravano lo svantaggio di Firefox erano **la posizione nella sequenza**:
  rovesciando l'ordine spariscono. *Senza quel controllo sarebbe stato consegnato «Firefox è il
  44 % più lento».*

---

## Il catalogo

**Da 24 banchi a 25**, e da **20 certificati su 24** a quel che dice `--registro` alla chiusura.
⭐ **Nuovi certificati**: `03-scena` · `03-deposita` · `03-b17` · `03-solo`. ⭐ **Marche misurate,
non dedotte**: due, contate nei log.

⛔⛔ **E il punto cieco vero, trovato per caso e adesso contato a macchina** — `--punti-ciechi`:

```
4 coperti · 2 per gemellaggio · 4 sulla carta · 22 CIECHI
```

**Ventidue file del prodotto** — `cattura.c`, `mutter.c`, `sessione.c`, `tls.c`, `trasporto.c`,
`registro.c`, `comando.c`… — **non sono nominati da nessuna voce del catalogo**: possono cambiare
senza che nessuna certificazione scada. ⚠ *Non vuol dire che un guasto passerebbe inosservato: vuol
dire che una riga verde continuerebbe a dire «certificato» su un prodotto che nel frattempo è un
altro.*

⭐ E la proposta facile per chiuderlo **è stata rifiutata da chi doveva farla**: legare quei file ai
banchi B3-B8 sarebbe **falso**, perché il registro dice riga per riga che quei banchi si certificano
**contro l'innesto**, non contro il prodotto. *Fabbricherebbe una rete che non esiste e farebbe
smettere lo strumento di dire «cieco».*

---

## ⛔ I banchi che uscivano SEMPRE 0: erano tre, sono **cinque**

Il conto è stato corretto **due volte nella stessa sera, da due agenti diversi, e in tutt'e due i
casi il banco era di chi contava**:

| | |
|---|---|
| due curati l'11 agosto | ✅ |
| il terzo, `03-b19-ritardo-worker.py` | ✅ **curato stanotte** — e la nota che diceva «non si può provare da CHUWI» era **falsa**: `--verdetto` rilegge un **file**, e sul disco c'erano quattro verbali veri |
| il quarto, ⛔ **`03-b17-ritardo.py --verdetto`** | ⛔ **è il banco che ha prodotto il numero della fase.** Curato e misurato nei due versi |
| il quinto, ⛔ **`03-palco-dipinge.py`** | ⛔ **scritto dal coordinatore la sera stessa in cui questa trappola veniva catalogata.** Trovato da un altro agente, **fuori dal suo perimetro** |

⇒ **Non è una svista che si ripete: è una forma che il linguaggio invita.**

---

## Che cosa resta, e in che ordine

| | | perché in quest'ordine |
|---|---|---|
| **1** | ⛔⛔ **il palco dei banchi browser** — forzare `--ozone-platform` e **verificarlo dall'altro capo** | finché non è fatto, ogni numero di ritardo porta dentro la contesa col desktop dell'utente, e **il prossimo «prima» nascerebbe già sbagliato** |
| **2** | ⛔ **la pagina che offre HEVC e poi non lo dipinge nella sessione vera** | senza, **il codificatore hardware non riceve un fotogramma** e la fase non può chiudersi |
| **3** | ⚠ **`/srv/src/03-B-src/` porta la pagina vecchia** | chi accendesse quell'albero misurerebbe l'hardware **spento** |
| **4** | ⏳ **la marca di `03-b19`** | vuole finestra esclusiva **e** macchina di prova |
| **5** | ⏳ **i millisecondi della corsia D** | `[?]` per contaminazione **dichiarata**: bastano 25 minuti di macchina libera |
| **6** | ⚠ **i 22 punti ciechi** | non è lavoro di una sera, e la scorciatoia è già stata rifiutata |

⏳ **E i due punti che l'utente ha lasciato aperti di proposito restano aperti**: il debito di chiave
strozzato (si legge il registro della sessione del giudizio, **costa zero**) e *dove finisce di
contare il tetto dei 50 ms* — che **non si decide** prima di avere il numero in hardware.

---

## ⭐⭐ Il metodo, e il conto che lo dimostra

**Gli agenti sono stati mandati a REFUTARE**, e il mandato ammetteva il rifiuto. Il conto della
serata:

| | |
|---|---|
| premesse del coordinatore **smentite con un caso** | **almeno nove**, e avevano ragione tutte |
| di queste, **la riga principale della serata** | ⛔ **una**, smentita da un agente due ore dopo |
| difetti trovati **nel banco di chi li cercava** | **tre** (`03-palco-dipinge`, `03-b17 --verdetto`, l'arbitro `03-solo`) |
| agenti che hanno accusato **sé stessi** | **tre** — un A/B verde per costruzione, un confronto a due variabili, due cifre scritte prima di averle davanti |
| volte che un banco ha sbagliato **a favore** del prodotto | ⭐ **zero** |

⚠ **E una cosa prevista che NON è stata fatta**: il **refutatore della corsia B** non è stato
lanciato. La corsia B ha refutato tre premesse sue da sola, e il tempo è andato al lavoro invece che
al secondo paio d'occhi. **Si scrive, non si nasconde.**
