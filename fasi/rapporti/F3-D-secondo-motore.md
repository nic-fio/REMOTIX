# CORSIA D — Il secondo motore: i NUMERI

*13 agosto 2026, sera. Agente n. 4, corsia D. Mandato: **refutare**, non confermare. ⛔ Non ho
committato niente: il commit lo fa il coordinatore.*

> ## ⛔⛔⛔ TRE PREMESSE DEL MANDATO SONO CADUTE, E LA TERZA ROVESCIA UNA CONCLUSIONE DI IERI SERA
>
> | la premessa | il caso che la smentisce |
> |---|---|
> | ⛔ *«metti i profili sotto `~/.cache/`, che `/tmp` è pieno»* | **`~/.cache` è un collegamento simbolico a `/tmp`**: `ls -ld` dà `/home/nicfio/.cache -> /tmp`, e `df ~/.cache` dà la stessa tmpfs al 98 %. ⇒ Non sposta un byte. I miei profili stanno su **`/var/tmp/corsia-d`**, che `df` dà su `/dev/sda2` (178 G liberi) |
> | ⛔ *«Firefox non apre finestre su Xvfb (0 finestre in 90 s) ⇒ si usa `--headless`»* | **Firefox apre finestre su Xvfb e la pagina gira**: `xlsclients` lo vede, `xdotool` conta le finestre, e la pagina ha rimandato i suoi esiti con un POST. Il caso è in §2.2 |
> | ⛔⛔⛔ *«la GPU su Xvfb c'è: `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))`»* | **quel Chrome non era su Xvfb.** Girava con `--ozone-platform=wayland`, cioè agganciato alla **sessione Wayland vera dell'utente**, malgrado `DISPLAY` dicesse `:70`. Forzato su X11 con `--ozone-platform=x11`, lo stesso Chrome sullo stesso Xvfb dice **«niente webgl»** e HEVC **no**, 3 giri su 3. Il caso è in §2.3 |

---

## 1. Che cosa ho consegnato

| file | che cos'è |
|---|---|
| `banchi/03-ff-palco.py` | il palco comune: accende Xvfb, serve la pagina, aspetta il POST, **prova** che il browser stia sullo schermo dichiarato (`xlsclients` + `xdotool`), fotografa la macchina prima e dopo (via `03-solo.py`), conta le porte protette **su NIC-OS** |
| `banchi/03-ff-decodifica.py` | i **numeri della decodifica** su tutt'e due i motori: seriale (un pezzo alla volta, il regime del prodotto) e a raffica (la portata) |
| `banchi/03-ff-disegno.py` | i **numeri del disegno** (i due `drawImage` del prodotto) e i **quadri di `requestAnimationFrame`** |
| `banchi/03-ff-finestre.sh` | il caso che smentisce *«Firefox non apre finestre su Xvfb»*, col controllo su Chrome accanto |
| `banchi/03-ff-lancia.sh` | la campagna intera, **una configurazione alla volta** |
| `banchi/03-ff-riassunto.py` | le tabelle di questo rapporto, estratte dai verbali invece che ricopiate |

⛔ **Non ho toccato niente fuori da `banchi/03-ff-*`** e da questo rapporto. `03-palco-*`, `03-quadri.py`
e `03-solo.py` li ho **letti e ne ho copiato il codice**; `03-solo.py` lo **importo**, non lo riscrivo.

**Le porte**: 8870-8879 per i miei servitori, schermi `:70`-`:78`. ⭐ **Le protette 7448 · 7501 ·
7561 contate prima e dopo ogni banco, su NIC-OS via `ssh`: 3 prima, 3 dopo, ogni volta.**
⚠ Contarle su CHUWI avrebbe dato 0 e sarebbe stato l'errore già fatto una volta.

**Il disco**: profili e flussi su `/var/tmp/corsia-d`, **mai** su `/tmp`. Picco ~230 MB (16 MB di
flussi + un profilo alla volta), liberato a fine giro. ⭐ E i megabyte liberi sono **dentro il
messaggio d'errore** del palco, così un disco pieno non può travestirsi da guasto della pagina.

---

## 2. ⛔ IL PALCO — quattro righe rimisurate, tre cadute

### 2.1 `~/.cache` è `/tmp`

```
lrwxrwxrwx 1 nicfio nicfio 4 apr  7 11:11 /home/nicfio/.cache -> /tmp
```

⇒ L'istruzione *«metti i profili sotto `~/.cache/` perché `/tmp` è pieno»* è **auto-annullante**.
⚠ E ne discende una cosa che riguarda un altro gruppo: i flussi di prova del 13 sera stanno in
`~/.cache/sonda-vp9`, cioè **sulla tmpfs** — 16 MB di quella che allora aveva 100 MB liberi.

### 2.2 ⭐ Firefox apre finestre su Xvfb, e la pagina gira

*La riga smentita sta in `F3-prossima-sessione.md:575` e :391, ed è citata come ragione per cui la
corsia D non aveva numeri: «Firefox non apre finestre su Xvfb `:81` (0 finestre in 90 s)».*

**Il caso**, `banchi/03-ff-finestre.sh`, Xvfb **`:78`** 1920×1200×24, **90 secondi**, un
`http.server` che registra le richieste, e ⭐ **il controllo su Chrome accanto**:

| comando | finestre a 10 s e a 90 s (`xwininfo`) | clienti X (`xlsclients`) | ⭐ **la pagina ha girato?** |
|---|---|---|---|
| `firefox --profile P http://…` | ⭐ **6** · **6** | ⭐ **1** | ⭐ **sì** — `GET /` 200 + `POST /vivo-…` |
| `firefox --headless --profile P …` | 0 · 0 | 0 | ⭐ **sì** |
| `google-chrome --user-data-dir=P …` *(senza `--ozone-platform`)* | ⛔ **0** · **0** | ⛔ **0** | ⭐ sì |

⇒ ⭐ **Firefox le finestre le apre**, e in **meno di 10 secondi**, non «0 in 90 s».
⇒ ⛔ **Ed è CHROME a non aprirne nessuna su Xvfb** — perché non è su Xvfb affatto (§2.3). La
stessa riga di misura che assolveva Chrome e accusava Firefox li aveva **scambiati**.

⛔ **Ma la conseguenza tratta da quella riga era sbagliata anche se la riga fosse stata vera**: in
**tutti e tre** i casi la pagina gira e rimanda i suoi esiti. La domanda giusta non era *quante
finestre si aprono*, era *se la pagina gira* — e `--headless` era la cura di un sintomo che non
bloccava niente. ⚠ *`xdotool search --onlyvisible` conta **1** anche a schermo vuoto (la finestra
radice): il conteggio onesto è quello di `xwininfo`, e per questo il banco ne usa due.*

### 2.3 ⛔⛔⛔ Chrome ignora `DISPLAY` e si aggancia alla sessione dell'utente

*È la riga più cara che ho trovato, e ne va avvisata la corsia B prima che misuri l'anello.*

Il banco lanciava Chrome con `DISPLAY=:70` e senza `WAYLAND_DISPLAY`. La riga di comando del
processo, letta con `pgrep -af`, diceva:

```
/opt/google/chrome/chrome --user-data-dir=/var/tmp/corsia-d/prof-chrome-8875
    ⛔ --ozone-platform=wayland   --render-node-override=/dev/dri/renderD128
```

⭐ **Ozone sceglie da sé guardando `XDG_SESSION_TYPE`** (qui `wayland`), e il socket lo trova in
`XDG_RUNTIME_DIR/wayland-0` anche senza `WAYLAND_DISPLAY`. ⇒ Il browser stava sul **desktop vero di
Nic**, con la GPU vera, mentre il banco scriveva «Xvfb :70» accanto al numero.

`[M]` **A/B con una sola variabile**, stesso banco, stesso flusso, stesso Xvfb, 3 giri per lato:

| Chrome 151, `DISPLAY=:70` | dove sta davvero | webgl visto dalla pagina | HEVC `isConfigSupported` |
|---|---|---|---|
| **senza** `--ozone-platform` (difetto) | ⛔ **sessione Wayland dell'utente** | `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))` | ⭐ **true**, e decodifica a **1,2-1,3 ms/fotogramma** |
| **con** `--ozone-platform=x11` | ⭐ **l'Xvfb del banco** (`xlsclients` dà `CHUWI google-chrome`, 2 finestre) | ⛔ **«niente webgl»** | ⛔ **false**, in tutt'e tre le modalità |

⇒ ⛔⛔ **La conclusione di ieri sera — *«su Xvfb la GPU c'è, era la bandiera `--disable-gpu`»* — è
vera per metà e falsa per l'altra metà**: la bandiera *accecava* davvero, ma toglierla non ha
scoperto la GPU dell'Xvfb — ha scoperto che **quel Chrome non era sull'Xvfb**.
⭐ **Quel che resta in piedi**: HEVC in hardware si dipinge davvero, e la iGPU c'è. ⛔ **Quel che
cade**: che ciò accada *su Xvfb*. Su un Xvfb vero, Chrome 151 non ha nemmeno WebGL.

> ⚠ **E c'è un secondo effetto, che ha bloccato un mio banco per 240 secondi**: una finestra sul
> desktop vero è **occlusa** dalle altre, e Chrome **strozza** le schede occluse. Il banco sembrava
> appeso «perché il motore non ce la fa». Non era il motore: era il palco sbagliato.
> ⇒ Ho aggiunto un tetto a `flush()` in tutti e due i banchi, perché *una `Promise` che non si
> risolve mai e «il motore non ce la fa» hanno lo stesso aspetto*.

⭐ **La cura, e vale per qualunque banco browser del progetto**: `--ozone-platform=x11` a Chrome,
`GDK_BACKEND=x11` e `MOZ_ENABLE_WAYLAND=0` a Firefox, e ⛔ **il banco PROVA dove sta il browser**
invece di crederlo: `xlsclients -display <schermo>` deve nominarlo.

### 2.4 ⭐ `requestAnimationFrame` gira anche su Firefox

Il coordinatore ha smentito su Chrome la riga *«su Xvfb rAF non gira mai»* (153-181 quadri in 3 s,
`banchi/03-quadri.py`). ⛔ Quella misura era di **un motore solo**. Rifatta su Firefox, con lo stesso
metodo copiato da `03-quadri.py`:

| motore · palco | quadri in 3 s | `visibilityState` |
|---|---|---|
| ⭐ **Firefox 140.13 ESR, finestra su Xvfb** | **171** | `visible` |

⇒ **Il cammino del disegno non è codice morto sul secondo motore.** I numeri del §4 sono misurabili.

---

## 3. ⭐ I NUMERI DELLA DECODIFICA — Firefox **con il gemello di Chrome accanto**

**La scena, e vale per tutta la sezione.** Flusso `testsrc2` 1920×1080, 120 fotogrammi a 60/s,
prodotto con le impostazioni del prodotto (`libsvtav1 preset 10`, `pred-struct=1`, 4:2:0) —
⚠ **scena SINTETICA, non il desktop vero**. Pezzi tagliati sugli offset di `ffprobe`, quindi **120
unità di accesso esatte in ingresso**, e i fotogrammi in uscita **contati**. Configurazione
`optimizeForLatency: true`, come il prodotto (`src/pagina.html:786`).

⛔ **Il modo che conta è il SERIALE**: si consegna un pezzo, si aspetta il suo fotogramma, poi il
prossimo — è il regime del prodotto, ed è l'analogo del **tratto 5** di `03-b17-ritardo.py`
(*«`decode()` → richiamo del decodificatore»*, **7,58 ms** su Chrome). Il modo a raffica misura la
**portata** e sovrastima quel che il prodotto vede.

### 3.1 AV1 Main 10 bit — il codec che il prodotto negozia oggi (`codec 2`)

*mediana del seriale, in ms per fotogramma, **3 giri per casella***

| `hardwareAcceleration` | **Chrome 151** Xvfb/X11 | **Chrome 151** headless | **Firefox 140 ESR** Xvfb/X11 | **Firefox 140 ESR** headless |
|---|---|---|---|---|
| `no-preference` *(quel che chiede il prodotto)* | 8,21 · 8,15 · 8,49 | 7,94 · 8,20 · 9,70 | ⚠ 11,82 · 11,50 · 11,72 | ⚠ 11,08 · 11,66 · 11,24 |
| `prefer-hardware` | ⛔ non dichiarato | ⛔ non dichiarato | 9,02 · 8,96 · 8,96 | 9,10 · 9,02 · 9,08 |
| `prefer-software` | 10,50 · 10,58 · 10,45 | 10,42 · 10,30 · 10,32 | 8,96 · 9,02 · 8,96 | 8,92 · 9,16 · 9,22 |
| ⭐ **rifatto con l'ordine dei casi ROVESCIATO** | 10,66 · 10,64 · 10,61 *(sw)* · 11,06 · 10,53 · 10,64 *(no-pref)* | — | ⭐ **9,02 · 9,02 · 8,98** *(no-pref)* · 9,02 · 8,98 · 8,96 *(hw)* · 9,02 · 9,00 · 9,04 *(sw)* | — |
| *portata a raffica (fotogrammi/s)* | 93 · 97 · 101 | 98 · 97 · 101 | 110 · 110 · 111 | 106 · 105 · 103 |
| *formato del `VideoFrame`* | `I420P10` | `I420P10` | `BGRX` | `BGRX` |
| *fotogrammi in uscita* | ⭐ 120 su 120 | ⭐ 120 su 120 | ⭐ 120 su 120 | ⭐ 120 su 120 |

> ### ⭐⭐ E i 2,7 ms di scarto di Firefox erano **la posizione, non la modalità**
>
> `no-preference` usciva sistematicamente più lento delle altre due — **6 giri su 6**, in tutt'e due
> i palchi. ⛔ Non l'ho chiamato rumore. Rovesciando l'ordine dei casi (`--rovescia`), **le tre
> modalità danno tutte 9,0 ms**, `no-preference` compreso. ⇒ **Il primo caso della lista pagava
> l'accensione del motore**, e la mediana su 119 fotogrammi non bastava a diluirlo.
> ⭐ **Il numero giusto di Firefox per AV1 10 bit è 9,0 ms**, e ⛔ **quello di 11,8 ms era un
> artefatto del mio banco** — che senza il rovesciamento sarebbe finito in questo rapporto come
> «Firefox è il 44 % più lento».

⇒ ⭐ **Il secondo motore decodifica AV1 a 10 bit più in fretta del primo, su questo palco**: nel
regime del prodotto Firefox sta a **9,0 ms** e Chrome fra **8,2 e 10,7**. **Nessuno dei due butta un
fotogramma** (120 su 120 ovunque), e tutti e due stanno **sopra i 90 fotogrammi al secondo** di
portata, cioè sopra i 60/s che il prodotto consegna.
⚠ **Nessuno di questi numeri è preso da solo sulla macchina** — vedi §6.

⚠ **E su Chrome la stessa domanda resta aperta**: rovesciando l'ordine, `no-preference` passa da
8,2 a 10,6 mentre `prefer-software` resta a 10,6 ⇒ i due giri **si contraddicono**, e non ho un
terzo dato per arbitrare. ⇒ ⏳ **Il numero di Chrome per AV1 10 bit va preso come intervallo
8,2-10,7 ms**, non come un valore.

⭐ **E il formato conferma una riga già scritta** (`DECISIONI.md` §1.13): su Firefox i 10 bit
**arrivano ma non sono osservabili** — `BGRX` per tutto, mentre Chrome dà `I420P10`. Questa è la
riprova indipendente, presa con un attrezzo diverso da quello che l'aveva scritta.

### 3.2 AV1 Main 8 bit — il controllo

| `hardwareAcceleration` | Chrome Xvfb/X11 | Chrome headless | Firefox Xvfb/X11 | Firefox headless |
|---|---|---|---|---|
| `no-preference` | 5,91 · 7,47 · 7,02 | 7,57 · 7,72 · 7,39 | 7,18 · 7,20 · 7,26 | 7,08 · 7,26 · 7,18 |
| `prefer-software` | 7,34 · 7,33 · 7,60 | 7,39 · 7,34 · 7,61 | 7,18 · 7,22 · 7,20 | 7,14 · 7,32 · 7,22 |

⇒ **A 8 bit i due motori sono indistinguibili** (~7,2 ms tutti e due). ⭐ Il divario dei 10 bit non
è «Firefox è più lento»: è **il costo dei 10 bit su Firefox**, che paga ~2 ms dove Chrome ne paga
~1.

### 3.3 ⛔ HEVC su Firefox: un **NO**, e con il palco scritto accanto

| flusso HEVC Main10 (`hev1.2.4.L123.B0`, da `hevc_vaapi`, `-bf 0`) | esito |
|---|---|
| Firefox 140 ESR, finestra su **Xvfb** (webgl: `llvmpipe`) | ⛔ `isConfigSupported` **false** — in tutte e tre le modalità, 3 giri su 3 |
| Firefox 140 ESR, **`--headless`** (webgl: `Intel(R) HD Graphics, or similar`) | ⛔ **false** — in tutte e tre, 3 giri su 3 |
| Chrome 151, finestra su **Xvfb** (webgl: *niente*) | ⛔ **false** — in tutte e tre |
| Chrome 151, **`--headless=new`** (webgl: SwiftShader) | ⛔ **false** — in tutte e tre |
| ⭐ Chrome 151, **sessione Wayland vera** (webgl: `ANGLE (Intel, Mesa ADL-N)`) | ⭐ **true**, e decodifica **1,21-1,30 ms/fotogramma**, 120 su 120 |

⛔ **Il «no» di Firefox non è del palco**: lo dà anche nel palco in cui vede la iGPU (`--headless`,
`Intel(R) HD Graphics`), che è lo stesso hardware in cui Chrome dice **sì**.
⇒ ⭐⭐ **Conseguenza per la corsia B, e va detta prima che HEVC diventi il codec principale: su
Firefox HEVC non esiste in WebCodecs.** Il ripiego negoziato di `DECISIONI.md` §1.13 non è una
cortesia — **è l'unica cosa che fa funzionare il secondo motore**, e la scala `hevc,av1` va letta
così: *Chrome prende HEVC in hardware, Firefox prende AV1 in software*.

---

## 4. ⭐ I NUMERI DEL DISEGNO — e i due motori mentono in modi diversi

**La scena**: gli stessi due `drawImage` del prodotto — dal `VideoFrame` al deposito 1920×1080
(`src/pagina.html:1862`) e dal deposito alla tela 1280×720 (`:1445`) — con
`willReadFrequently: true` su tutt'e due i contesti, **come il prodotto** (`:1136`). 120 fotogrammi
AV1 10 bit decodificati in serie, **3 giri per casella**.

⛔ **E il controllo che impedisce il verde facile**: a fine giro la tela si rilegge e si pretende
che i pixel **non siano tutti uguali** (`0-255` in tutti i giri: la tela ha davvero ricevuto
l'immagine). Un `drawImage` che non disegna niente è velocissimo.

| mediana per fotogramma, ms | Chrome Xvfb/X11 | Chrome headless | **Firefox** Xvfb/X11 | **Firefox** headless |
|---|---|---|---|---|
| **il disegno come lo fa il prodotto** | 5,58 · 5,67 · 5,55 | 5,61 · 5,69 · 5,62 | **11,46 · 10,94 · 11,58** | 11,68 · 11,16 · 11,90 |
| ⛔ **lo stesso, più la rilettura di UN pixel** | **9,25 · 9,50 · 9,41** | 9,11 · 8,80 · 9,17 | 11,86 · 11,12 · 11,06 | 11,06 · 11,28 · 11,56 |
| ⇒ **quanto lavoro era rimandato** | ⛔ **+3,7 ms (+66 %)** | ⛔ +3,4 ms | ⭐ **+0,0 ms (niente)** | ⭐ −0,3 ms (niente) |
| *quadri di `requestAnimationFrame` in 3 s* | ⭐ 181 · 181 · 182 | 181 · 182 · 182 | ⭐ **178 · 178 · 178** | 181 · 181 · 182 |
| *pixel letti dalla tela* | 0-255 | 0-255 | 0-255 | 0-255 |

> ### ⛔⛔ **`drawImage` su Chrome RIMANDA il lavoro; su Firefox no**
>
> È un A/B a **una sola variabile** — la rilettura di un pixel, che obbliga il motore a finire — e
> i due motori rispondono in modo **qualitativamente diverso**, 3 giri su 3 ciascuno.
>
> ⇒ ⚠ **Il tratto 6 di `03-b17-ritardo.py`** (*«richiamo → disegno finito (`drawImage` ×2)»*,
> **10,51 ms** nel numero della fase 3) è misurato **su Chrome e nella forma «come il prodotto»**:
> su questo palco quella forma **sottostima di circa due terzi** il lavoro che il disegno comporta.
> ⛔ Non dico che i 10,51 siano sbagliati — dico che **misurano il costo di METTERE IN CODA**, non
> quello di dipingere, e che la differenza **non è la stessa sui due motori**.
> ⚠ E il +3,7 ms è un **limite superiore**: dentro c'è anche il costo della rilettura stessa.
>
> ⭐ **Questo è esattamente l'arbitro esterno che `SPECIFICHE.md` §11.5 si aspetta dal secondo
> motore**: due squadre che non ci conoscono, e quando non sono d'accordo il difetto della misura
> si dichiara da sé.

⇒ ⭐ **Nel confronto onesto (tutt'e due i motori obbligati a finire) il disegno costa 9,4 ms su
Chrome e 11,4 ms su Firefox**: il secondo motore è più lento del **21 %**, non di un fattore.
⚠ Su Firefox il disegno gira su `llvmpipe` (nessuna accelerazione), quindi quel numero è **il caso
peggiore**, non il caso tipico.

### 4.1 ⭐ `requestAnimationFrame` gira anche sul secondo motore

**178 quadri in 3 secondi** con la finestra su Xvfb, **181** in `--headless`, `visibilityState`
sempre `visible`, 3 giri per configurazione. ⇒ **Il cammino del disegno non è codice morto su
Firefox**, e i numeri qui sopra sono misurabili davvero.

---

## 5. ⭐⭐ Una `[?]` di `DECISIONI.md` §1.13 si CHIUDE: Firefox **ripiega in silenzio** (forma E2)

*La domanda aperta era: «perché Firefox accetti `prefer-hardware` e dipinga AV1 dove `vainfo` non
elenca nessun entrypoint di decodifica AV1 — o ha una strada che VA-API non dichiara, o ripiega in
silenzio. Non è misurato quale».*

**È misurato adesso, e con due prove indipendenti.**

**1. Gliel'ho chiesto** (`LEZIONI.md` §1.6, *non si deduce: si chiede*). Firefox lanciato con
`MOZ_LOG=PlatformDecoderModule:5`, e il motore **nomina da sé** il decodificatore che ha creato,
in **tutte** le istanze del giro, `prefer-hardware` compresa:

```
RemoteDecoderChild has been initialized -
   description: ffvpx video decoder (RDD remote), process: rdd, codec: av1
```

⛔ **`ffvpx` è il decodificatore SOFTWARE incorporato in Firefox** (dav1d per AV1), e gira nel
processo RDD. **Nessuna istanza VA-API è mai stata creata**, in nessun caso del giro.

**2. I numeri lo confermano**: `prefer-hardware` e `prefer-software` danno **lo stesso numero fino
alla terza cifra** — 9,02 · 8,98 · 8,96 contro 9,02 · 9,00 · 9,04 — su **9 giri**.

**3. E l'hardware non ce l'ha**: `vainfo` su CHUWI **non elenca AV1 affatto**, né in decodifica né
in codifica (c'è un solo nodo, `renderD128`; il `renderD129` di NIC-OS qui non esiste).

⇒ ⭐ **La risposta è la seconda: forma d'errore E2, ripiego silenzioso.** `prefer-hardware` su
Firefox **non è una promessa**, è un desiderio che il motore esaudisce col software senza dirlo.
⛔ **Un prodotto che si fidasse di `prefer-hardware` per decidere qualcosa deciderebbe al buio.**
⚠ Chrome invece **è sincero**: su AV1 risponde `supported: false` a `prefer-hardware`, che è la
verità di questa macchina.

---

## 6. ⛔ «ERO SOLO?» — no, e lo dico accanto ai numeri

**Nessuno dei giri di questa corsia è stato preso su una macchina esclusiva**, e l'arbitro
(`banchi/03-solo.py`) lo ha detto **in ogni verbale**. Le ragioni registrate, giro per giro:

| | |
|---|---|
| carico a 1 minuto | fra **0,52 e 4,84** (la soglia dell'arbitro è 1,0) |
| browser altrui vivi | fino a **10 processi** — ⛔ **il Chrome vero dell'utente** |
| altre corsie | tre, che lanciavano browser e `ffmpeg` |
| ⭐ ma il disco no | `/var/tmp` sempre sopra i 180 G liberi, `/tmp` mai sotto 1,3 G |

⇒ ⛔ **Tutti i millisecondi di questo rapporto sono `[?]` per contaminazione dichiarata, non `[M]`.**
⭐ **Quel che invece regge senza finestra esclusiva** — ed è la parte che decide la `[?]` di
`SPECIFICHE.md` §11.5 — è tutto ciò che è **correttezza e conteggio**: i sì/no di
`isConfigSupported`, i **120 fotogrammi su 120**, i formati `I420P10` contro `BGRX`, i quadri di
rAF, la confessione del decodificatore, il conteggio delle finestre e delle porte.

⇒ ⭐ **Chiedo al coordinatore una finestra esclusiva su CHUWI** (≈ 25 minuti) per rigirare
`bash banchi/03-ff-lancia.sh`: i banchi già rifiutano di misurare con `--esigi-solitudine`, e in
quella finestra i quattro numeri diventerebbero `[M]`.

---

## 7. ⛔ CHE COSA NON HA FUNZIONATO

*Compreso quel che ho sbagliato io: sono quattro, e tre sono voci del catalogo delle trappole già
pagate, cadute di nuovo addosso a chi lo aveva appena letto.*

| | |
|---|---|
| ⛔⛔ **il banco misurava sul desktop di Nic credendo di essere su Xvfb** | e non se n'è accorto per tre campagne. A dirlo non è stato un controllo: è stato un `pgrep -af` fatto per un'altra ragione. ⇒ Ho aggiunto `clienti_x()`, che **prova** dove sta il browser. **Costo: una campagna intera da rifare** |
| ⛔ **un banco appeso 240 s che sembrava «il motore non ce la fa»** | la finestra era sul desktop vero, **occlusa**, e Chrome strozza le schede occluse. In più `flush()` non aveva un tetto. ⇒ Tetto a 15 s, e la causa vera curata col palco |
| ⛔⛔ **il mio confronto del disegno non era un confronto** | la prima stesura metteva `willReadFrequently` **solo** nel passaggio «forzato» ⇒ i due numeri differivano per **due** variabili. È la stessa forma del confronto fra codificatori a bitrate libero, riletta un'ora prima. ⇒ Rifatti tutti i 12 giri del disegno |
| ⛔ **due verbali sovrascritti**, la famiglia del `w` invece del `>>` | il giro di verifica e quello della confessione hanno riscritto i file di due campagne, perché il nome non portava dentro il **palco**. I dati sopravvivono nei registri; i file sono stati **rietichettati** (`…-PROVA-30pezzi-…`, `…-CONFESSIONE-…`) invece di essere lasciati con un nome che mentiva |
| ⛔ **il mio `03-ff-finestre.sh` è morto a metà e ha lasciato acceso il servitore** | il giro dopo non ha potuto legare la porta e **avrebbe consegnato «0 POST» come se fosse un esito del browser**. ⇒ `trap … EXIT` e un **controllo che il servitore sia vivo prima di misurare** |
| ⛔ **e in questo rapporto avevo scritto due numeri che non avevo davanti** | i valori del **terzo giro** del disegno su Firefox `--headless` (11,42 e 11,34): li avevo scritti mentre il giro era ancora in corso. I veri sono **11,90** e **11,56**. ⇒ Trovati rileggendo il verbale contro la tabella, che è la ragione per cui `03-ff-riassunto.py` esiste. ⚠ **Nessuna conclusione cambia**, ma due cifre erano inventate |
| ⚠ **il flusso HEVC di prova aveva fotogrammi B** | il modo seriale consegnava **1 fotogramma su 30** e quello a raffica **30 su 30**: non era il decodificatore, era il riordino. ⇒ `-bf 0`, che è anche l'assetto giusto (il prodotto lavora a bassa latenza) |
| ⚠ **`set -u` mi ha salvato una volta** | tre `local` in una riga sola: la terza variabile non vedeva la prima. Il banco è morto invece di misurare a vuoto |

---

## 8. ⏳ CHE COSA RESTA `[?]`

| | |
|---|---|
| ⏳ **i millisecondi sono `[?]` per contaminazione** | vedi §6: servono 25 minuti di finestra esclusiva. I conteggi e i sì/no invece reggono |
| ⏳ **il numero di Chrome per AV1 10 bit è un intervallo, non un valore** | 8,2-10,7 ms: i due ordini si contraddicono e non ho un terzo dato per arbitrare (§3.1) |
| ⏳⏳ **perché Firefox rifiuti HEVC in WebCodecs mentre un suo modulo dice di conoscerlo** | nel registro convivono `FFmpeg decoder supports requested type 'video/hevc'` e `rejects`, e `isConfigSupported` dice **false** ⇒ il no sembra posto **sopra** il decodificatore, non dalla sua mancanza. ⚠ **Non ho provato la strada `<video>`**: potrebbe suonare HEVC dove WebCodecs lo rifiuta, e sarebbe una differenza che il prodotto vede |
| ⏳ **la scena è SINTETICA** | `testsrc2`, non il desktop vero. I codificatori software sono sensibili al contenuto ⇒ questi numeri **non si sottraggono** dai 74,58 ms della fase 3; si confrontano solo fra motori |
| ⏳ **su Firefox i 10 bit non sono osservabili** | `BGRX` per tutto, contro `I420P10` di Chrome ⇒ **non posso dire se Firefox conservi davvero i 10 bit**, solo che li accetta. Conferma indipendente di `DECISIONI.md` §1.13 |
| ⏳ **il palco non è una GPU vera** | su Xvfb Chrome non ha WebGL e Firefox ha `llvmpipe`; solo Firefox `--headless` vede la iGPU. ⇒ **il disegno di Firefox è misurato nel caso peggiore**, e su hardware vero cambierebbe |
| ⏳ **il terzo motore non esiste ancora** | `SPECIFICHE.md` §11.5 nomina anche WebKit/Safari: manca il dispositivo, forma **E10** |

---

## 9. ⇒ CHE COSA CAMBIA PER LE ALTRE CORSIE

| a chi | che cosa |
|---|---|
| ⛔⛔ **corsia B e corsia E** | **il palco dei banchi browser va rifatto o ridichiarato**: `--ozone-platform=x11` a Chrome, o il banco misura sul desktop dell'utente. ⚠ E se i numeri della fase 3 (74,58 ms e i cinque tratti) sono stati presi con Chrome su Wayland, **il «prima» e il «dopo» di E devono stare sullo stesso palco**, e oggi non si sa quale fosse (`03-b17-ritardo.py` non lo scrive) |
| ⛔ **corsia B** | **su Firefox HEVC non esiste in WebCodecs**, in nessuna modalità e in nessuno dei due palchi. Portare il prodotto su HEVC **non toglie AV1**: lo rende obbligatorio per il secondo motore |
| ⚠ **corsia E** | il tratto 6 (`drawImage` ×2) **sottostima di ~3,7 ms su Chrome** e non sottostima su Firefox (§4) |
| ⭐ **il coordinatore** | `DECISIONI.md` §1.13 ha una `[?]` in meno (§5); `LEZIONI.md` §1.15 è già stata smentita da lui su Chrome e **lo è anche su Firefox** (§4.1); la riga «Firefox non apre finestre» va corretta in `F3-prossima-sessione.md:575` e `:391` |

---

## 10. Come si rifà tutto

```bash
bash banchi/03-ff-lancia.sh                 # le quattro configurazioni, in serie
python3 banchi/03-ff-riassunto.py           # le tabelle di questo rapporto
bash banchi/03-ff-finestre.sh 90            # il caso delle finestre
python3 banchi/03-ff-decodifica.py firefox 3 --con-finestra --rovescia      # l'ordine
python3 banchi/03-ff-decodifica.py firefox 1 --con-finestra --confessione   # il decodificatore
```

⭐ **Porte protette: 3 prima, 3 dopo, in ogni banco.** Macchina lasciata pulita: nessun mio
processo, nessuna mia porta, `/var/tmp/corsia-d` a 14 MB. ⚠ L'`Xvfb :81` che resta **non è mio**:
c'era prima che cominciassi.
