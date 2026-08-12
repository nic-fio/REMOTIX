# P2.6 — Il montaggio: i cinque anelli messi insieme

*Sesta e ultima sotto-fase della fase 2. Scritta il **12 agosto 2026**, la sera.
Porta di questo giro: **7561**. ⛔ 7448 e 7501 contate prima e dopo.*

> ⭐ **In una riga**: il cliente di prova indipendente riceve **UN fotogramma, conforme** (uscita
> **0**, era **5**), e ⭐⭐ **il desktop compare dentro una scheda di Chrome** — codificato AV1,
> passato per WebTransport, dipinto sulla tela di `src/pagina.html`.

---

## 1. Che cosa e' stato innestato, e dove

| file | che cosa | righe |
|---|---|---|
| `src/Makefile` | i quattro sorgenti nuovi, le cinque librerie (⛔ `gio-2.0` **una volta sola**), le sei intestazioni nel bersaglio `dipendenze`, le quattro dipendenze d'oggetto | +60 |
| `src/main.c` | `sessione_assicura()` prima dell'aiutante · `primo_fotogramma()` — cattura, due codifiche, deposito · `--rilievo DIR` · la costante `TELA_L/TELA_A` in **un posto solo** | +330 |
| `src/webtransport.c` | i **quattro ganci** del canale video, il **preambolo** `40 54`+sessione, il deposito dei due flussi, `video_forse()`, il tetto della coda | +330 |
| `src/webtransport.h` | `wt_video_deposita()` / `wt_video_svuota()` | +22 |
| `src/registro.h` | ⚠ **due righe**: `REG_SESSIONE` (che `P2-1` §6.2 chiedeva di portare qui) e `REG_VIDEO` | +2 |
| `src/sessione.h` | ⚠ **una riga tolta**: il `#define REG_SESSIONE` provvisorio | −1 |
| `banchi/02-montaggio-accendi.sh` | il server della fase 2 sulla 7561, **fuori dal contenitore** | nuovo |
| `banchi/02-montaggio-terreno.sh` | la scena sull'host: PAM, l'utente `prova`, il gruppo `shadow` | nuovo |
| `banchi/02-montaggio-scheda.sh` | ⭐ il browser vero contro il prodotto: la fotografia della scheda | nuovo |
| `banchi/02-filo-cliente.py` | ⛔ **curato**: il giudice dal vivo accusava il server di un difetto suo (§4.2) | +45 |

⛔ **Non toccati**: `RCP.md`, `src/rcp.c`, `src/rcp.h`, `src/pagina.html`, `src/cattura.*`,
`src/mutter.*`, `src/codificatore.*`, `src/sessione.c`. Nessun `git` che scrive.

### ⭐ La forma scelta per il fotogramma, e la ragione

⛔ **Si cattura e si codifica UNA VOLTA, all'accensione**, e si depositano **due** flussi (HEVC e
AV1); quando una sessione arriva a `SESSIONE` si spedisce quello del codec negoziato.

| perche' non si cattura quando serve | `cattura_prendi()` ASPETTA il prossimo fotogramma, e su un desktop fermo l'attesa arriva al suo tetto. Dentro il ciclo `poll` fermerebbe **tutte** le connessioni insieme (`CODER.md` §4.4) — la forma appena curata su PAM, nel punto in cui farebbe piu' male |
| perche' i depositi sono **due** | il codec si sa solo alla negoziazione di §4.3, cioe' **dopo** l'accensione: codificare li' rimetterebbe nel ciclo i 100 ms di x265 e i 44 di SVT-AV1. `[M]` |
| perche' e' un deposito di **processo** | l'immagine appartiene al palco, cioe' alla sessione grafica — invariante **I4**, non alla connessione |

⇒ Nel ciclo `poll` non si aspetta niente e non si codifica niente: `video_forse()` sceglie fra due
blocchi gia' pronti e chiama `rcp_video_spedisci()`.

---

## 2. ⭐ Compila pulito

```
[M] 12 agosto 2026, contenitore Debian 13 su NIC-OS
    -O2 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter -D_GNU_SOURCE
    ⭐ ZERO avvisi su 15 unita' di compilazione (grep -ci warning sul registro: 0)
    binario ba6e68bb7f0cec03…, 8 marche dentro su 8, 4 segni in pagina.html su 4
```

⚠ E **`libswscale-dev` c'era gia'** sul contenitore della macchina del prodotto
(`7:7.1.5-0+deb13u1`, stesso pacchetto sorgente di `libavcodec-dev`): il `sudo` che `P2-3` §8
prevedeva **non e' servito**. `[M]`

---

## 3. ⭐⭐ La prima misura vera: il cliente di prova riceve UN fotogramma

*Il cliente e' `banchi/02-filo-cliente.py`, dentro il contenitore, `aioquic` 1.2.0. Il server e'
sulla **7561**, sull'host. ⛔ 7448 e 7501 intatte, 2+2 ascoltatori prima e dopo.*

```
   CONNECT estesa: :status = 200
   ⭐ SESSIONE: tela concessa 1920x1080
   ACCETTATO  stream 15, 11951 byte, finito con fin: chiave n. 1, 1920x1080,
              11923 byte di dati
   guardati: 1 flussi video · 1 conformi · 0 ambigui · 0 RICHIEDI_CHIAVE spedite
   ⭐ 1 fotogrammi, tutti conformi a RCP.md                        USCITA = 0
```

⭐ **Lo zero e' diventato uno.** Ed e' letto **due volte da due programmi**: il giudice dal vivo, e
`02-filo-validatore.py` sulla registrazione — *«ACCETTATO flusso 15: chiave n. 1, 1920x1080, 11923
byte di dati · conforme: nessuna violazione in 1 flussi»*, uscita **0**.

### La catena, numero per numero — `[M]` 12 agosto 2026

| anello | misura |
|---|---|
| **sessione** | `Meta-0` / `MetaVirtualMonitor` / 1920×1080@60 — *«c'e' gia' e ha il monitor chiesto: non la tocco (I4)»* |
| **monitor del flusso** | ⭐ `Meta-1` / «Virtual remote monitor» — **1 monitor prima del montaggio, 2 dopo** |
| **cattura** | 1920×1080, **stride 7680 LETTO**, 8 294 400 byte, **BGRx a 8 bit**, buffer in memoria, range *non conclusivo* (min 36/63/78 · max 133/160/180: e' uno sfondo, non una mira) |
| **codifica HEVC** | **11 923 byte**, chiave, `hev1.2.4.L120.90`, profondita' nel flusso 10, livello 120 · conversione **4,8 ms**, codifica **100,3 ms** |
| **codifica AV1** | **9 746 byte**, chiave, `av01.0.08M.10`, livello 8 · conversione **5,0 ms**, codifica **40,6 ms** |
| **promozione 8→10** | ⭐ **dichiarata dal prodotto**, in registro, per tutt'e due i codec |
| **filo** | 28 byte di intestazione + 11 923 di dati su uno stream unidirezionale nuovo, chiuso con **FIN** |
| **dall'accensione al deposito** | **~330 ms** in tutto (13.029 → 13.356) |

---

## 4. ⭐⭐ Il confronto a pixel

### 4.1 Il metro, certificato — **12 guasti su 12**

`bash banchi/02-giudizio-confronto.sh certifica`, `[M]` 12 agosto 2026, CHUWI: **stato 0**.

```
sano  → PROMOSSO      M1a PSNR-Y 56,75 dB (soglia 45)   M2 Δ = −0,07 dB (soglia −0,5)
        M0 (0,0) col margine di 29,57 dB · M3 49,82 dB · M6 Δ +13,62 dB
i dodici guasti:
  nero 1 · nero-doppio 2 (M-V, e non 1: PSNR infinito) · riga 1 · colonna 1 ·
  precedente 1 · otto-bit 1 (M7) · piani 1 (M4) · gamma 1 · blocco 1 (M3) ·
  matrice 1 (M-C) · dopo-reset 1 (M8) · ribaltato 1
risanato → PROMOSSO
⭐ 12 su 12, e sano → guasto → risanato ha chiuso il cerchio
```

⚠ **E questo certifica il METRO, non la catena del prodotto**: gira sulla catena finta (mira →
libx265 → ffmpeg → «pagina»). I due numeri veri sono qui sotto.

### 4.2 ⭐ La catena del PRODOTTO contro il lettore indipendente

*I file li scrive il prodotto stesso con `--rilievo`: `cattura.bgrx` (8 294 400 byte),
`flusso-hevc.265`, `flusso-av1.obu`. Il lettore indipendente e' `ffmpeg`.*

| | PSNR-RGB | PSNR-Y (709) | scarto massimo |
|---|---|---|---|
| **HEVC** decodificato ⟷ catturato | **49,22 dB** | **48,27 dB** | 15 |
| **AV1** decodificato ⟷ catturato | **49,29 dB** | **48,27 dB** | 22 |

⇒ ⭐ **La codifica non ha perso l'immagine**: a CRF 20 su un desktop vero i due codec danno lo
stesso PSNR-Y a due centesimi di dB. ⚠ E questo e' il **termine `riferimento ⟷ cattura`** del metro
di F2.6, non il metro intero: manca il termine `pagina`, che si legge solo da dentro la pagina.

### 4.3 ⭐⭐ E il desktop dentro la scheda — i pixel DIPINTI

`bash banchi/02-montaggio-scheda.sh` · `[M]` 12 agosto 2026, Chrome 151 su **Xvfb `:78`
2048×1280**, contro `https://192.168.0.2:7561/`, utente `prova`.

```
Ammesso, sessione nuova, tela 1920×1080, desktop sconosciuto
sonda video · ⛔ HEVC: NON arriva al pixel su questo browser
sonda video · AV1: arriva al pixel (8 e 10 bit, «av01.0.13M.08»)
video · negoziato: codec av1 («av01.0.13M.08»), 8 bit, tela 1920x1080
video · decodificatore configurato per 1920x1080 con «av01.0.13M.08» (riconfigurazione n. 1)
⇒ e sulla tela c'e' lo sfondo del desktop.        banchi/02-montaggio-copie/4-scheda.png
```

**Il numero**, ritagliando la tela dalla fotografia (544×306, rapporto **1,7778** esatto) e
confrontandola col fotogramma catturato ridotto alla stessa misura:

```
miglior scorrimento  dx = 0  dy = 0        PSNR-RGB  41,55 dB
```

⛔ **E questo NON e' il metro di F2.6, e va detto invece di lasciarlo credere.** Ci passano in mezzo
la perdita di AV1, il ridimensionamento 1920→544 dentro la pagina, il mio ridimensionamento per il
confronto e la fotografia di uno schermo finto. ⭐ Quel che dimostra e' **l'allineamento**: lo
scorrimento migliore e' `(0,0)` su una griglia di 7×7, cioe' l'immagine dipinta e' **quella**, nel
posto giusto. Il metro a due piani vuole `getImageData` **dalla pagina**, e quello e' il pezzo che
manca (§7).

---

## 5. ⛔ Le cuciture che NON combaciavano, e chi aveva promesso male

### 5.1 ⛔ `P2-2-cattura.md` — `mutter_monitor_cerca()` nel punto sbagliato

Le righe da innestare di `P2-2` §«il montaggio del palco» mettono `mutter_monitor_cerca()` **fra**
`cattura_avvia()` e `cattura_prendi()`, con accanto la ragione giusta: *«solo adesso il monitor
esiste»*.

`[M]` innestata li', su una sessione **perfettamente sana**, il prodotto ha scritto:

```
⚠ non ho saputo dire quale schermo sia il nostro
```

⛔ **E' lo stesso rosso che F2.2 aveva gia' pagato e curato**, ricomparso di un passo piu' in la'.
La condizione vera non e' *«ho chiesto il flusso»*: e' **«sto davvero leggendo»**, e il fatto che lo
dimostra e' **un fotogramma in mano**. Spostata **dopo** `cattura_prendi()`:

```
⭐ il nostro schermo si chiama «Meta-1» (prodotto «Virtual remote monitor»),
   monitor 1 prima del montaggio e 2 dopo
```

⇒ ⚠ **Ha promesso male F2.2/P2.2**, ed e' `LEZIONI.md` §1.13 applicata a una sequenza: si nomina la
grandezza vera del fenomeno, non quella che gli somiglia. ⭐ La correzione e' **una riga spostata**,
ed e' nel codice con la data e il numero accanto.

### 5.2 ⛔⛔ `banchi/02-filo-cliente.py` — il giudice dal vivo ha accusato il server

Primo giro contro un server che spedisce davvero:

```
[ERRORE_PROTOCOLLO] stream 15, 11951 byte, finito con fin: un fotogramma prima di
  `SESSIONE`: §2.5 vieta al server di aprire uno stream video prima di averla spedita
```

⛔ **Il server aveva fatto esattamente quel che §2.5 gli impone.** Il difetto: `cli.contesto` lo
poneva il guidatore **dopo** `await attendi(cli, "SESSIONE")` — cioe' quando `asyncio` riprende la
coroutine, che e' **dopo** che tutti gli eventi di quel volo di pacchetti sono stati smistati. Il
fotogramma, che il server apre nella riga subito dopo `SESSIONE`, arriva nello stesso volo e trova
`contesto is None`.

⭐ **A dire di chi era la colpa e' stato il secondo lettore**: `02-filo-validatore.py`, sulla
**stessa** registrazione, ha detto *«ACCETTATO … conforme»*, uscita 0. ⚠ E che i due arbitri dello
stesso banco dicessero cose opposte sugli stessi byte **e' una misura, non un incidente**.

⇒ ⚠ **Ha promesso male il banco di P2.4**, ed e' la **seconda volta** che quel cliente punta il rosso
sul server (la prima e' §4 di `P2-4-filo.md`). ⭐ Curato: il contesto si pone in `_sfoglia()`, cioe'
guardando i **byte** del canale di controllo nello stesso istante sincrono in cui arrivano.

### 5.3 ⛔⛔ `P2-1-sessione.md` `[?]` 1 — **dove gira il server**: chiusa, e con una scoperta dietro

`[M]` il chroot di `enter.sh` monta `/proc`, `/sys`, `/dev` e `/srv/src` — **e non `/run`**:
`/media/REMOTIX/devroot/run/user` **non esiste**. ⇒ Dentro il contenitore non ci sono ne' il bus di
sessione, ne' PipeWire, ne' `systemd --user`, e i tre anelli nuovi non hanno con chi parlare.

**Verificato sul server di casa riacceso** (7448, dentro il contenitore), `[M]` 19:46:47:

```
sessione ⛔ non ho nemmeno il bus di sessione (Cannot autolaunch D-Bus without X11 $DISPLAY):
           non e' «non c'e' la sessione», e' «non ho potuto guardare»
avvio    ⛔ nessuna sessione grafica con un monitor (5 LETTURA IGNOTA): il server parte
           lo stesso, ma non c'e' niente da catturare
video    ⛔ nessun monitor virtuale da catturare … nessuna sessione vedra' un pixel
```

⭐ **Il ripiego funziona come dichiarato**: il server parte, la pagina e l'autenticazione della fase 1
funzionano, e ogni riga dice perche'. ⇒ Il prodotto della fase 2 gira **fuori dal contenitore**, che e'
anche dove girera' davvero: accanto alla sessione grafica dell'utente. Il binario e' **lo stesso**
(host e chroot sono tutt'e due Debian 13, glibc 2.41-12+deb13u3); cambia solo `LD_LIBRARY_PATH`,
perche' `ngtcp2` 1.25 sta in `/media/REMOTIX/src/b2/...` e nei pacchetti c'e' la **1.11 con lo stesso
soname**.

### 5.4 ⛔⛔⛔ E la scoperta che nessun rapporto aveva previsto: **root non parla col bus di sessione**

```
[M] sudo env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
        gdbus call --session --dest org.gnome.Mutter.ScreenCast …
    → ⛔ «Error connecting: The connection is closed», uscita 1
```

⇒ **Una tensione vera del prodotto, e questa fase e' la prima a metterla sul tavolo:**

| per fare questo | serve essere |
|---|---|
| verificare con PAM la parola d'ordine di un utente **qualunque** (`pam_unix` fuori da root passa da `unix_chkpwd`, che verifica **solo** la parola di chi lo invoca) | ⛔ **root** |
| parlare col bus di sessione, con PipeWire e con `systemd --user` di quell'utente | ⛔ **quell'utente** |

⛔ **Le due cose non stanno nello stesso processo**, e oggi il prodotto le chiede tutt'e due allo
stesso albero: `aiutante.c` interroga PAM e `cattura.c` legge PipeWire. ⇒ Il prodotto vero avra'
bisogno della forma che ha gia' usato una volta — **un processo per utente**, come l'aiutante di
`DECISIONI.md` §1.10 ma **al contrario**: il padre root autentica, il figlio scende all'uid
dell'utente e prende il palco. ⭐ **E' una decisione del coordinatore, non una riga di codice.**

⚠ Per questo giro la scena si e' scelta dal lato che non puo' cedere — processo a **uid 1000** — e il
pezzo che manca si e' comprato con due righe di configurazione **della macchina di prova**,
dichiarate in `banchi/02-montaggio-terreno.sh`: l'utente `prova` sull'host (parola **pubblica** dei
banchi, e passata lo stesso da un file `0600` — difetto D12) e `nicfio` nel gruppo `shadow`. ⛔ La
seconda **non regala niente**: `nicfio` ha gia' `sudo`.

### 5.5 ⚠ La tela si negozia per sessione, e il deposito e' uno solo

`[M]` primo giro col browser su uno schermo finto **1600×1000**: la pagina dichiara
`video.misura_massima = screen.width × dPR` (`src/pagina.html` riga 1390), §4.5 permette al server
di **ridurre**, e la tela concessa e' **1600×900**. Il deposito e' 1920×1080 ⇒ `video_forse()`
**rifiuta di spedire**, e lo scrive:

> *«tela in vigore 1600x900 ma il fotogramma catturato e' 1920x1080 — NON lo spedisco:
> l'intestazione di §6.2 direbbe una misura e i pixel ne porterebbero un'altra»*

⭐ **La guardia ha fatto il suo mestiere** (meglio nessun fotogramma che uno che mente), ⛔ **ma il
buco non e' di nessun rapporto: e' fra due di essi.** P2.1/P2.2 catturano a una misura fissa; RCP §4.5
lascia negoziare la tela per sessione; nessuno dei sei ha scritto che cosa succede quando le due non
combaciano. ⇒ Oggi si compra allargando lo schermo del banco (2048×1280); la cura vera e'
`codificatore_ridimensiona()` per sessione, ed e' **lavoro della fase 3**, non di questa.

### 5.6 ⚠ Un tetto mio che avrebbe morso al posto di quello di `RCP.md`

`WT_CODA_MAX` valeva **2 MiB**. §6.2 dichiara **legale** un fotogramma fino a **16 MiB**, e
`rcp_video_apri()` rifiuta esattamente sopra quel numero. ⇒ Un fotogramma legale da 3 MiB sarebbe
stato rifiutato **dal limitatore di `webtransport.c`**, non dal tetto del protocollo — e il sintomo
sarebbe stato un buco, una `RICHIEDI_CHIAVE`, una chiave ancora piu' grossa: **la spirale di §5.2,
provocata da una costante nostra**, cioe' l'invariante **I1** rotta in silenzio. Alzato a **17 MiB**
(16 del fotogramma + 1 per il canale di controllo), col prezzo dichiarato nel codice.

---

## 6. ⛔ Una regola di `RCP.md` che, applicandola, non ha retto

*Il mandato chiedeva di fermarsi e scriverlo. `RCP.md` **non e' stato toccato**.*

### P20 — `§2.5` · *«nessuno stream video prima di aver spedito `SESSIONE`»*: **il lato che riceve non lo puo' giudicare cosi'**

**Il caso concreto, misurato oggi.** Il server spedisce `SESSIONE` sul canale di controllo e apre lo
stream del primo fotogramma nella riga subito dopo — §5.2 gliene fa un obbligo. I due viaggiano su
**due stream QUIC indipendenti** e arrivano nello stesso volo di pacchetti. ⛔ Il client li smista in
un ordine che **non e' l'ordine del filo**, ma quello in cui il suo strato di rete gli consegna gli
eventi — e su `aioquic` il fotogramma e' arrivato al giudice **prima** che `SESSIONE` fosse
interpretata.

⇒ Un client conforme che applicasse §2.5 alla lettera **chiude con `ERRORE_PROTOCOLLO` una sessione
in cui nessuno ha sbagliato**. ⚠ E' la stessa famiglia di P13 e della regola del cambio di tela
(`P2-5-pagina.md` §5): *«due stream QUIC indipendenti, e niente ne ordina la consegna»*.

> **Testo proposto**, da aggiungere a §2.5 accanto alla riga del divieto:
>
> ⛔ **E il divieto vincola CHI MANDA, non chi giudica.** «Prima di `SESSIONE`» significa *prima che
> i byte di `SESSIONE` siano stati **scritti sul filo***. ⚠ Chi riceve non puo' misurarlo
> sull'ordine in cui il proprio strato di rete gli consegna gli eventi: il canale di controllo e lo
> stream del fotogramma sono due stream QUIC indipendenti, e RFC 9000 non ne ordina la consegna. ⇒
> Un client dichiara la violazione **solo** se, quando il fotogramma arriva, i byte di `SESSIONE`
> **non sono ancora arrivati** — non se non li ha ancora interpretati.

---

## 7. ⛔ Che cosa manca ancora perche' l'utente veda il proprio desktop

| # | che cosa manca | di chi e' |
|---|---|---|
| 1 | ⛔ **il metro a due piani sulla catena vera**: serve `getImageData` **dalla pagina** e un canale che riporti i pixel al banco. Oggi la pagina del prodotto non spedisce esiti a nessuno (ed e' giusto), e i banchi di F2.5 leggono i pixel solo dentro il **loro** guscio | F2.5 + F2.6, e una decisione: se la pagina debba avere un modo dichiarato di consegnare i pixel a un banco |
| 2 | ⛔ **la mira sul monitor virtuale**: il metro di F2.6 vuole la sua scena (marcatori d'angolo, riquadri a luminanza uguale, rampe). Su un desktop qualunque M-V, M3, M4 e M7 non hanno dove guardare. Serve mandare la mira su `Meta-1` **per nome** — e adesso il nome c'e' | F2.6 |
| 3 | ⛔ **il server deve girare accanto alla sessione dell'utente**, e la coppia root/utente va decisa (§5.4) | ⚠ **il coordinatore** |
| 4 | ⛔ **la tela negoziata contro la cattura a misura fissa** (§5.5) | fase 3 |
| 5 | ⚠ **HEVC su una GPU vera**: su Xvfb non c'e', e il ripiego AV1 funziona. Il numero di HEVC attraverso il prodotto **non e' stato preso di proposito** | F2.5, un giro solo |
| 6 | ⚠ **un fotogramma che si aggiorna**: oggi e' quello dell'accensione. La fase 2 e' un'immagine ferma, e questo e' il confine dichiarato | fase 3 |

---

## 8. Il conto del catalogo, e lo stato del terreno

| | |
|---|---|
| **7448** (prodotto di casa) | ⭐ **riacceso sul binario nuovo** `ba6e68bb…`, `01-casa-7448.sh stato` → *«sta eseguendo il binario che c'e' sul disco»*. 2 ascoltatori |
| **7501** (bersaglio di P5) | ⭐ **non toccata**, 2 ascoltatori prima e dopo |
| **7561** (questo giro) | accesa e **lasciata accesa**, perche' e' quella su cui si vede il desktop |
| **terreno** | `01-b0-terreno.sh prodotto` → ⭐ **13 controlli su 13** |
| **allineamento** | `attrezzi-allinea-prodotto.sh` → sorgenti, binario e processo dicono la stessa cosa |

### Le certificazioni che questa ricostruzione fa scadere — elencate, e **non tutte rifatte**

⛔ *«Scaduta» non e' «fallita», e non e' nemmeno «pulita».* Il binario e' cambiato, e
`attrezzi-allinea-prodotto.sh` porta `src/` intero: **le nove `[ricostruisce]` del catalogo scadono
tutte** — **B2, B3, B5, B6, B7, B8, B10, P5, P5R** — piu' quelle misurate sui processi accesi.

| rifatta | esito |
|---|---|
| ⭐ **terreno prodotto** | 13 su 13 |
| ⭐ **B3** (la stretta di mano su due connessioni, contro il **7448 nuovo**) | **tre giri su tre**, e `01-b4-validatore.py` dichiara **CONFORME** tutt'e due le tracce, 6 messaggi su 6 |
| ⭐ **F2.6 — il metro a pixel** | 12 guasti su 12, sano → guasto → risanato |
| ⭐ **F2.4 — gli arbitri** | il cliente e il validatore girati contro il prodotto vero, e d'accordo |

⛔ **Restano scadute e da rifare**: **B2, B5, B6, B7, B8, B10, B13, P5, P5R**. ⚠ E il catalogo era
**15 su 15**: oggi non lo e' piu', e dirlo pieno sarebbe la cosa peggiore che questo rapporto possa
fare. ⭐ La scadenza ha una causa sola e dichiarata — *il prodotto e' cambiato* — e non un rosso.

⚠ **E una cosa che nessuno ha ancora rifatto**: l'innesto in `b2/ngtcp2/examples` **non e' stato
ricostruito**, quindi la **7447** gira ancora sul `rcp.c` di prima. `banchi/rcp/` sul server e' stato
allineato (e' il gemello che il `Makefile` confronta); `attrezzi-allinea-innesto.sh allinea` e' il
passo che manca.

---

## 9. Il giudizio dell'utente

⏳ **Da dare, e adesso c'e' che cosa guardare.**

⭐ **Il server e' acceso sulla 7561 e mostra il desktop.** Da un browser sulla rete di casa:

```
https://192.168.0.2:7561/        utente: prova     parola: parola-di-prova
```

⚠ **Tre cose da sapere prima di guardarlo**, o si giudica la scena invece del prodotto:

1. ⛔ **la finestra del browser dev'essere su uno schermo di almeno 1920×1080**, o §4.5 concede una
   tela piu' piccola e il fotogramma non parte (§5.5) — e il registro nella pagina lo dice;
2. ⚠ **l'immagine e' ferma, ed e' quella dell'accensione del server**: la fase 2 e' un'immagine
   ferma, e il ciclo dei fotogrammi e' della fase 3;
3. ⚠ **su un browser senza GPU si usa AV1**, e il riquadro della pagina lo dichiara: e' il ripiego
   negoziato di `DECISIONI.md` §1.13, non un difetto.

⛔ E il metro non e' nessun numero di questo rapporto: e' **che sia il suo desktop**.
