# Le righe da riscrivere a fine fase 3 — registro corrente

⛔ Si aggiornano **tutte insieme, a codice fermo**, alla chiusura. Aggiornarle mano a mano
farebbe scadere le certificazioni sotto ai gruppi ancora al lavoro.

## Dallo step 2 — la scena (rientrato, 34 verdi / 0 rossi)

| Dove | Che cosa non regge più | Stato |
|---|---|---|
| `LEZIONI.md:87` | «`weston-simple-egl -f -o` fa esattamente questo» — `[M]` **non è installato** su CHUWI, e comunque **non porta la marca**. Va nominata la forma di riposo della fase 3 | da fare |
| `fasi/00-ambiente.md:126` | «`weston-simple-egl` \| presente \| ✅ `/usr/bin/weston-simple-egl` \| 9 ago» — `[M]` **assente** il 13 agosto (rootfs in RAM, §2.5-bis) | da fare |
| `fasi/00-ambiente.md:35`, `:155` | «Scena dichiarata: `weston-simple-egl -f -o`» | da fare |
| `fasi/rapporti/F2-6-giudizio.md:503` | `giro` «⛔ NON APPLICABILE… per costruzione» — **cade**, adesso è eseguibile | da fare |
| `fasi/rapporti/F2-6-giudizio.md:447` | «e un limite dichiarato» — la metà sul `giro` cade, quella su `dipinto_dopo_reset` **resta** | da fare |
| `fasi/rapporti/F2-6-giudizio.md:63`, `:78`, `:184` | M6: da `[?]` a `[M]`, ⛔ **col limite della catena scritto accanto** (manca la cattura PipeWire e la tela del browser riletta) | da fare |
| `README.md:393-397` | le due righe su M8/`giro` e su `02-figlio-accendi.sh:165` | da fare |
| `fasi/02-primo-fotogramma.md:280` | il difetto del figlio: curato `[R]`, **non eseguito** | da fare |
| `fasi/03-movimento.md` | step 2 consegnato · difetto del figlio curato · il catalogo va **ricontato** | da fare |

### ⚠ Due rilievi dello step 2 da NON riportare come sono

1. **«nessuna delle tre porte protette è in ascolto»** — ⛔ **falso**, ed è una misura presa dalla
   macchina sbagliata: il controllo girava su CHUWI, ma 7448/7501/7561 ascoltano su **NIC-OS**.
   Verificato dal coordinatore il 13 agosto: `ss -ltn` su `192.168.0.2` dà **7448, 7501, 7561**
   vive, più la **7603** dello step 3. ⇒ La riga di `fasi/03-movimento.md` **regge**.
2. **«il catalogo è 5 su 15, 10 scadute»** — vero, e ⭐ **previsto dal documento stesso**: la fase 3
   tocca `src/` e curare il prodotto fa scadere le certificazioni che lo guardavano. Non è una
   riga da correggere: è la riga da **rieseguire alla chiusura**.

## Dallo step 4 — la pagina (rientrato, 19 casi verdi, 8 guasti innestati su 8 accusati)

| Dove | Che cosa va scritto | Stato |
|---|---|---|
| `RCP.md` §6.2 | ⛔ il trattenimento **non ha tetto in byte**: §7.1 obbliga il server a rispondere, ma un server che non risponde fa crescere la coda del client **senza limite**. La riga manca | da fare |
| `RCP.md` §6.2 | il paragrafo del trattenuto non dice se il contatore vada su «richieste in volo» o su «fotogrammi». Risolto nel codice (fotogrammi contati una volta sola anche se rigiudicati due volte), **non nel documento** | da fare |
| `web.md` §6.3, riquadro **P5** | la causa misurata: il fuori ordine nasce dalla **dimensione** del fotogramma, non solo dalla rete — `stream_video` scatta al completamento dello stream ⇒ l'ordine d'arrivo è quello delle dimensioni, e una chiave grossa viene scavalcata dai delta. E **costa una chiave** | da fare |
| ~~`LEZIONI.md` (§1.x nuova)~~ | ⛔⛔⛔ **NON SI SCRIVE: È SMENTITA.** Diceva *«su Xvfb `requestAnimationFrame` non gira mai — 0 quadri in 3 s, **con e senza GPU**, `visibilityState` visible ⇒ ogni cammino di prodotto che ci passa dietro è codice morto sul banco, e vale per TUTTI i banchi browser del progetto»*. `[M]` **13 agosto sera, `banchi/03-quadri.py`, 3 giri per configurazione su Chrome 151, Xvfb**: **con la GPU 153-167 quadri** in 3 s · **con `--disable-gpu` 164-173** · **con `--headless=new` 180-181**. ⇒ **rAF gira, in tutt'e tre.** ⚠ Se il giro originale aveva un palco diverso (un worker — dove `requestAnimationFrame` non esiste per costruzione — o una finestra non mappata), **va dichiarato QUALE**: com'era scritta, la riga condannava a «codice morto» il cammino del disegno di ogni banco del progetto | ⛔ **CADUTA — 13 ago sera** |
| `LEZIONI.md` §1.11 | il caso: `Emulation.setDeviceMetricsOverride` cambia `clientWidth` **senza** emettere `resize`; un banco che ci si appoggia misura l'emulazione, non il browser | da fare |
| `fasi/03-movimento.md` | «Che cosa è stato sviluppato» e «Che cosa non ha funzionato» | da fare |

### ⛔ Un sospetto di FALSO VERDE in un banco già certificato
`banchi/02-pagina-vista-prova.py` pretende `ricomposizioni > prima` dopo `Emulation`, e su Xvfb
quella pretesa **dovrebbe essere impossibile** — eppure il registro la dà verde. O la sua scena è
diversa, o quel verde va riesaminato. ⇒ **Da chiudere prima della fine della fase**: un falso verde
in catalogo avvelena ogni misura che gli viene dopo, perché dà fiducia.

## ⭐⭐ Dallo step 1 — la cadenza. È il risultato più grosso della giornata

**La causa scritta in tre documenti è SBAGLIATA, e la cura esiste.** ⭐ **Il fatto, `[M]`**: monitor
**120** + freno **90** ⇒ **61,4** consegnati. ⚠ **La causa nuova, `[R]`**: letta nel codice di
Mutter, `maxFramerate` non è un tetto continuo ma una **griglia** —
`min_interval_us = 10⁶/maxFramerate` **troncato a intero** (16666 per 60) contro un tick da
16666,67 µs ⇒ chi cade sotto perderebbe un tick intero. Non un **battimento** fra due orologi: una
**quantizzazione**.

> ⛔⛔ ⚠ *Questo capoverso diceva: «Legge verificata su **13 punti**, 8 confermano, 0 smentiscono», e
> il capoverso sotto la tabella diceva: «Riscontro incrociato con la scena dello step 2: concordano
> **entro il 4 %**, attese **0** ovunque». ⛔ **Falsi tutt'e due**, e questo rapporto è il posto da
> cui la riga si è propagata negli altri otto documenti.*
>
> | file di prova | che cosa contiene davvero |
> |---|---|
> | `banchi/03-b14-esiti-griglia.jsonl` | **tre righe**: il terreno e **due celle** (`griglia-apertura-120`, `griglia-freno-90`), **tutt'e due con `scena_sul_mio_monitor: false`** ⇒ rifiutate dal banco, che stampa «⛔ la legge NON regge su **0 punti su 0**». ⇒ **i 13 punti non esistono** |
> | `banchi/03-b14-esiti-scena2.jsonl` | la **cella D** — proprio quella da confermare — porta `scena_sul_mio_monitor: false`, `palco_stabile: false`, **1 fotogramma in 25 s**; e il controllo di **ritorno** dà 52,84 contro gli 80,28 della sua cella B, cioè **non torna**. Entro il 4 % concordano A (0,7 %), B (3,2 %) e il controllo positivo; C sta al **5,4 %**, il negativo al **7 %** ⇒ **il 61,4 ha una scena sola** |
> | `banchi/03-b14-esiti.jsonl` | ⭐ **pulito**: sette celle, **tutte** `scena_sul_mio_monitor: true`, coi tre controlli che chiudono. **È da qui che viene la tabella qui sotto**, ed è tutto quel che sopravvive |
>
> **Corretto il 13 agosto 2026**, rilievo del coordinatore della fase 3, verificato riga per riga
> sui file di esiti. ⇒ La quantizzazione torna `[R]`, e **M3 non è chiusa: è mezza**.

| monitor | freno | consegnati | mediana | p99 | cella |
|---|---|---|---|---|---|
| 60 | 60 | 31,5 | 33,31 ms | 35,53 | **A** |
| 120 | 120 | 82,9 | 12,12 ms | 18,53 | **B** |
| 120 | 60 | 46,13 | 24,12 ms | 29,23 | **C** |
| ⭐⭐ **120** | ⭐⭐ **90** | ⭐⭐ **61,4** (60,04) | ⭐ **16,66 ms** | 20,43 | ⭐ **D** |

⛔ **E NON si riproducono**: né i «sei decimi» (la cella A dà **0,50** pulito), né il **37** che tre
documenti citano come fatto. ⭐ **Queste due righe reggono**, perché vengono da celle pulite.

| Dove | Che cosa cade |
|---|---|
| `SPECIFICHE.md:133-139` | «il traguardo dei 40 ms probabilmente non è raggiungibile su GNOME… Mutter ne consegna 37» ⇒ `[M]` **60,04** con monitor 120 / freno 90 |
| `DECISIONI.md` §2.5 (r. 981, riquadro 997), r. 873, r. 2547; §2.5-bis r. 1012 | il «tetto di Mutter accettato» va rimesso in discussione |
| `PIANO.md` fase 3, r. 442-448 | l'esperimento è fatto: l'esito non è «riesce» né «non riesce», è **«riesce con un numero diverso»** |
| `LEZIONI.md` r. 734-750 (il riquadro dei sei decimi), r. 717 (domanda 7), §6.1 r. 848 | il battimento va sostituito dalla quantizzazione sui tick, ⚠ **marcata `[R]`** |
| `gnome.md` §8.2 r. 316-325, §13 r. 482 | ⛔ *diceva «**M3 si può chiudere**»: **no**. Il fatto è `[M]`, la causa `[R]`, il riscontro su una seconda scena non c'è ⇒ **M3 resta mezza**. Corretto il 13 ago 2026, stesso rilievo* |
| ⭐⭐ `LEZIONI.md` §1.1 | **la trappola n. 1 è tornata a mordere il risultato che la citava**: il banco aveva scritto `scena_sul_mio_monitor: false` nel proprio file e nessuno l'ha guardato. ⇒ *un banco che dichiara la propria invalidità non serve a niente se chi legge guarda solo il risultato* — scritto come **§1.1-bis** |

⚠ **E il 60 non è il 40 ms**: la cadenza non è il ritardo (`LEZIONI.md` §6.2). I 60 fotogrammi
tolgono un ostacolo; il numero lo fa lo step 5.

## Dallo step 3 — il prodotto (6 punti su 7 chiusi; 13 controlli di certificazione, 13 verdi; giro dal vivo 8 verdi 1 rosso)

| Dove | Che cosa va scritto |
|---|---|
| `src/main.c` §«il deposito del video» | il prezzo dichiarato il 12 agosto **è pagato**, e la cura non è «un deposito per sessione»: è **nessun deposito** |
| `src/webtransport.h` | il riquadro di `wt_video_deposita` — la funzione non esiste più |
| `RCP.md` §2.3 | ⛔ la misura del 13 agosto: con `initial_max_streams_uni = 6` la sessione **cade** con `STREAM_LIMIT_ERROR` |
| `RCP.md` §5.1/§6.2 | ⛔ l'abbandono ha **due forme osservabili** — stream azzerato **e** buco nei `numero` — e quale delle due il client vede dipende da se un byte era uscito |
| `LEZIONI.md` §1.1 | ⭐ un **terzo punto**: *la scena deve stare sul monitor che si sta catturando*. Su un palco con monitor virtuale non è quello dell'utente. Costo: due giri buttati (step 3) più due (step 1) |
| `banchi/01-b12-guasti.py` + registro | i banchi nuovi `03-b14…03-b18` vanno **aggiunti al catalogo** con le impronte |

## ⛔ Il verde sospetto — CHIUSO, ed era peggio di un falso verde

**Il verde non era falso nel merito: era prodotto dallo STRUMENTO, e non era mai stato provato
capace di arrossire.** Su Xvfb i quadri non girano, e in Blink l'evento `resize` si consegna
**dentro** il giro di rendering ⇒ senza quadri non arriva mai. A svegliare la conduttura era
`Page.captureScreenshot`, cioè `fotografa()`, chiamata solo `if args.copia` — ⛔ **un'opzione di
comodo di stampa**, con effetto collaterale non dichiarato.

| banco ORIGINALE, prodotto SANO | esito |
|---|---|
| **senza** `--copia` | ⛔ **ROSSO, 5 pretese cadute** — fra cui «la tela è stata RICOMPOSTA (1 → 1)» |
| con `--copia` | verde (1 → 3) |

⛔ **E il buco strutturale**: `GIRO_GUASTO=vista-piu-larga` ⇒ le **quattro** pretese di quel blocco
**non erano mai state innestate con nessun guasto**. Verdi da sempre, senza che nessuno sapesse se
sapessero fare altro.
⭐ **Curato**: il quadro si batte apposta (5 battiti fissi, non «finché diventa verde»); una spia
del palco conta quadri ed eventi; ⭐ **si giudica prima il palco** — se il `resize` non è arrivato
il banco dice *«IL PALCO, NON IL PRODOTTO»* e si ferma; due guasti nuovi (`ridimensiona-sordo`,
`deposito-perso`) accusano 5 e 4 pretese. Tre giri: sano verde · guasti rossi · risanato **9 giri,
5 scene sane verdi, 4 pagine guaste rosse**.
⏳ `[?]` **resta**: che il quadro arrivi **da solo** quando l'utente trascina una finestra vera. Su
Xvfb non si produce nessun quadro ⇒ oggi il banco misura *«dato un quadro, il prodotto segue la
finestra»*, e il limite è scritto in testa al banco.
⚠ **Stessa trappola armata, oggi non vulnerabile**: `banchi/02-giudizio-catena.py` (r. 336, r. 431).
Regge perché nessuna sua pretesa passa da un quadro — ma chi ve ne aggiunga una ci cade.

## ⛔ La scena che correva a vuoto — CHIUSA (43 righe verdi, 0 rosse)

**Causa unica**: `buffer_libero()` chiamava `wl_display_dispatch()` **da dentro un gestore di
eventi** ⇒ `disegna()` annidata ⇒ da un `wl_surface.frame` in volo se ne fanno due, e si moltiplica.
⚠ Si accende **solo fuori da casa sua**: serve che i tre buffer siano occupati insieme, cioè un
compositore più carico — quel che succede quando accanto gira una cattura.

| | sano | guasto innestato | risanato |
|---|---|---|---|
| `fidato` | true | **false** | true |
| `frame` in volo, max | **1** | **18** (fino a 26) | 1 |
| disegni/s a 60 Hz | 60 | **461,7** (fino a 1034) | 60 |

⭐ **E i due sintomi erano lo stesso difetto**: una scena in corsa a vuoto non torna al ciclo
principale ⇒ ignora `--secondi` (6 chiesti, **146 vissuti**) ⇒ il banco la **uccide** ⇒ la morte
cade a metà scrittura ⇒ `seq` del seqlock resta **dispari per sempre**. Il lettore vecchio falliva
**3 su 3**, non «ogni tanto». ⛔ **La mia diagnosi del seqlock in contesa era sbagliata**: 200
letture su 200 riuscite con la scena a 1034 disegni/s.
⭐ Il rilevatore misura **la causa**, non il ritmo: *«i `wl_surface.frame` in volo non possono mai
essere più di 1»* — un invariante di protocollo, che non ha bisogno di sapere a che frequenza va il
monitor. E lo **stato d'uscita porta il verdetto** (2 = letto ma NON fidato), così `set -e` ferma
chi legge `.disegni` senza guardare `fidato`.

⛔ **RIGA NUOVA PER I DOCUMENTI**: *ogni cella di ritmo misurata con `03-scena` **prima** del 13
agosto va rifatta o marcata `[?]`* — la scena poteva correre a vuoto senza dirlo.
⭐ **Le celle che contano dello step 1 reggono**: `banchi/03-b14-esiti.jsonl` usa `03-b14-scena`
(EGL, sua), e la matrice dei tetti rifatta con la cura è **invariata** (60,0-60,2 disegni/s,
0 attese).

> ⛔ ⚠ *Questa riga diceva: «**Il riscontro incrociato dello step 1 regge** […] ⇒ l'accordo entro il
> 4 % fra due scene indipendenti tiene». **Non regge**, e per la ragione che la riga sopra dichiara:
> la seconda scena del riscontro **è** `03-scena`. In `banchi/03-b14-esiti-scena2.jsonl` la cella
> **D** porta `scena_sul_mio_monitor: false`, `palco_stabile: false` e **1 fotogramma in 25 s**, e
> il controllo di **ritorno** non torna (52,84 contro 80,28). ⇒ ⛔ **il 61,4 ha una scena sola.**
> Corretta il 13 agosto 2026, rilievo del coordinatore della fase 3.*

## ⛔⛔ Dallo step 5 — L'ANELLO DEL RITARDO. **SFORA**, e il muro è NOSTRO

**Mediana 74,6 ms** (min 50,4 · p05 58,1 · p95 101,2 · p99 138,1), 6 giri verdi, ~800 campioni
ciascuno, errore d'orologio **±0,63 ms**. ⛔ **Pezzo cieco 16-40 ms NON compreso** ⇒ sullo schermo
dell'utente **90-115 ms**. ⚠ E su Xvfb quel cieco **non esiste**: la stima vale per l'utente, non
per il banco. ⚠ Non è input→vetro (`input` = 0 in 953 su 953): è **cattura → vetro**, con **P1** al
posto dell'input.

| tratto | mediana |
|---|---|
| disegno → cattura (`pts` di Mutter) | 16,66 |
| ⛔ **cattura → primo byte in pagina** | **39,17** |
| il filo | 0,32 |
| stream completo → `decode()` | 0,08 |
| decodifica | 7,58 |
| richiamo → disegno finito (2 `drawImage`) | 10,51 |

⭐ **Ha spostato il confine del numero nella direzione scomoda**: la prima stesura chiudeva al
richiamo del decodificatore, regalandosi ~11 ms nostri e misurabili. Il numero è salito da 63,8 a
74,6 e l'ha lasciato salire.
**Certificazione: banco 31 su 31, ponte 11 su 11.** P1 verde (N=25 → +25,08; N=60 → +58,58), e
⭐ l'iniezione è **fuori dal prodotto**, con l'ancora d'orologio che **non ci passa** — se ci
passasse P1 passerebbe anche a banco rotto. P3 verde **sui pixel veri**: 234 fotogrammi in
movimento, 0 falsi positivi.
⛔ **P5 NON ESEGUITO, e lo dice**: dopo tre iniettori, `scavalcati = 0` non è «l'anello regge», è
«il fenomeno non si è presentato». Prima lo dichiarava verde.

### ⛔ Il muro NON è di Mutter — refutata la mia stessa riga
- la scena disegna **59,98/s con 0 attese** (uscita confermata) ⇒ non è suo;
- ⛔ il figlio del prodotto consegna **23,93/s con ZERO attese a vuoto**: **non aspetta MAI Mutter**;
- il codificatore è **in software** e lo dichiara il prodotto stesso (libsvtav1 / libx265);
- quota di Mutter: **16,66 su 74,6 = 22 %**. ⇒ **58 ms su 74,6 sono nostri**, ~39 nel tratto
  cattura→filo, dominato dal codificatore in software.

### ⛔⛔ E LA CURA DELLO STEP 1 NON È RAGGIUNGIBILE DAL PRODOTTO OGGI
`MOVIMENTO_FPS 60` è una **costante di compilazione** (`src/figlio.c:1465`), `main.c` non ha
nessuna opzione di cadenza, e ⛔ **`RecordVirtual` non prende la frequenza** (`src/mutter.h:82`):
tutti e quattro i monitor virtuali sono **1920×1080@60**, confermato da `03-scena --uscite`.
⇒ Il «monitor 120 / freno 90» dello step 1 è **`[M]` sul banco e NON attuabile dal prodotto**.

### Righe nuove
| dove | perché |
|---|---|
| `SPECIFICHE.md` §3.2 | la `[?]` sui 40 ms **è misurata, e la causa non è quella**: 22 % Mutter, **78 % nostro** |
| `SPECIFICHE.md` §3.2 + `CODER.md` §1-bis | ⛔ **dove finisce la misura**: al **disegno finito**, non al richiamo del decodificatore — 11 ms su un tetto di 50 |
| `DECISIONI.md` §2.5, §2.4 | il muro dei 37 come causa del ritardo |
| `DECISIONI.md` §1.5 r. 26, `RCP.md` §7.5 | la funzione di banco **non dà il ritardo noto**: `BANCO_ACCESO 0`, il ramo ACCETTATA è uno stub |
| `web.md` §6.1 | «tutto in un worker dedicato» — ⛔ `src/pagina.html` **non ha nessun worker**, e `desynchronized` è **spento** (`:407`) |
| `web.md` §8, §6.2 | il pezzo cieco **su Xvfb non esiste** |
| `LEZIONI.md` §1.2/§2.2 | ⭐ **una certificazione può essere verde perché prova il giudice nell'unità sbagliata** (quella del lettore invece dell'acquisizione) |
| `LEZIONI.md` §1.9 | «zero fuori ordine» non è «regge», è «non si è presentato» |
| `LEZIONI.md` §1.13 | P1 a blocchi confonde ritardo e deriva: si **intreccia**, non si allarga la tolleranza |
| `gnome.md` §8.2/§13 | il collo sulla catena vera è **il codificatore in software**, non `maxFramerate` |

⏳ `[?]`: P5 sulla catena vera · **il secondo motore** (solo Chrome 151 misurato, §11.5 ne vuole
due) · il cieco · se il decodificatore di Chrome su Xvfb sia hardware · quanto scenderebbe con un
codificatore hardware · la coda (p99 fra 101 e 307 ms fra un giro e l'altro, causa non isolata).

## Decisioni aperte per il coordinatore

- **Due scene esistono**: `banchi/03-scena.c` (step 2 — `wl_shm`+`xdg-shell`, marca a 144 bit,
  quattro conti fra cui le **attese**, verifica `wl_surface.enter`) e `banchi/03-b14-scena.c`
  (step 1 — EGL). Da decidere se ne sopravvive una sola. ⇒ Chiesto allo step 1 di rigirare la
  cella decisiva con la scena dello step 2 e riportare i due numeri accanto.

---

## ⛔ Il worker di `web.md` §6.1 — attuato, misurato, RESPINTO (13 agosto 2026, sera)

`[M]` stessa macchina, stessa sessione, **stessa pagina** (cambia solo l'interruttore), stesso
strumento rigirato per il «prima» e per il «dopo» (`banchi/03-b19-ritardo-worker.py`).

| ritardo disegno→vetro | n | p05 | **mediana** | p95 | p99 |
|---|---|---|---|---|---|
| PRIMA-A (thread principale) | 432 | 58,85 | **73,66** | 99,53 | 218,46 |
| PRIMA-B (ripetuto) | 492 | 53,93 | **67,79** | 88,51 | 98,16 |
| **DOPO (worker)** | 483 | 84,48 | **101,30** | 126,13 | 157,82 |

⇒ **+27,6 / +33,5 ms di mediana.** Lo scarto fra i due «prima» è 5,9 ms: l'effetto lo supera di
cinque volte. Errore d'orologio ±0,63-0,65 ms.

### ⭐ La scomposizione — ed è QUI che sta il −3,44 ms

| tratto (mediana, ms) | PRIMA-A | PRIMA-B | DOPO | Δ |
|---|---|---|---|---|
| stream completo → `decode()` | 0,07 | 0,06 | **10,23** | **+10,2** ⛔ |
| ⭐ **la decodifica** | **7,17** | 6,13 | ⭐ **3,73** | ⭐ **−3,44 / −2,40** |
| richiamo → disegno finito (`drawImage` ×2) | 9,63 | 9,11 | **27,19** | **+17,6** ⛔ |
| **somma dei tre** | 16,87 | 15,30 | **41,15** | **+24,3 / +25,9** |

⇒ ⭐ **`web.md` §6.1 non è sbagliata per intero: è sbagliata a metà.** La **decodifica** fuori dal
thread principale guadagna davvero **−3,44 ms** (7,17 → 3,73) — il decodificatore consegna prima
quando non contende. È la **tela** che affonda il conto.

### I fotogrammi dipinti, obbligatori accanto (`LEZIONI.md` §6.2)

| | catena vera (P7) | saturazione 1080p | saturazione 480p |
|---|---|---|---|
| thread principale | 22,8-24,2 /s | **127,6** /s | **230,6** /s |
| worker | **26,3** /s | **33,9** /s (−73,4 %) | **56,4** /s (−75,5 %) |

⚠ Le due grandezze dicono cose **opposte**: sulla catena vera il worker dipinge **di più** (coda),
ma a saturazione il tetto **crolla di tre quarti**.

### ⭐⭐ Il meccanismo, ed è la scoperta che cambia una REGOLA
Costo extra per fotogramma **13,4 ms a 480p** e **21,7 ms a 1080p**; e a 480p il worker si ferma a
**56,4 dipinti/s ≈ il quadro dei 60 Hz**, mentre il thread principale ne fa 230,6.
⇒ **`transferControlToOffscreen` impegna la tela al ritmo del quadro: è un `requestAnimationFrame`
implicito.** Il worker prescritto da §6.1 reintroduce **in silenzio** proprio il salto di quadro che
§6.1 vieta a voce alta — ⛔ **la prescrizione conteneva la propria smentita**, e nessuna rilettura
del documento poteva accorgersene senza misurarla.

⏳ `[?]` **il più grosso**: tutto è su **Xvfb, in software, senza GPU**. La penale è in gran parte
sincronizzazione al quadro ⇒ su hardware vero il conto va rifatto **prima** di seppellire §6.1.
⏳ `[?]` un `WebTransport` aperto **dentro** il worker toglierebbe i +10,2 del tratto 4, **non** i
+17,6 del tratto 6.
⭐ **Il codice resta in albero dietro `#video=worker`, SPENTO**, così il giorno della GPU vera il
numero si rifà senza riscrivere niente.
