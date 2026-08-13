# CORSIA E — L'anello rimisurato

> ## ⭐⭐⭐ IL MURO È CADUTO — 14 agosto, colpo secco alle 20:53
>
> *Il rapporto qui sotto è stato scritto alle 22:19 del 13, e la seconda metà della cura alle sonde
> è entrata alle **22:22**. ⇒ **Avevo misurato con la pagina curata a metà**: `SONDE` erano già
> `Main`, `SONDE_MISURA` erano ancora `Rext` — ed è esattamente il sintomo che avevo trovato,*
> «hevc non ha dipinto nemmeno alla tela minima di §4.5 (320×240)»*, perché quel 320×240 **è** il
> primo gradino di `SONDE_MISURA`.*
>
> **Con la pagina di adesso (`b41e4f16…`) la sessione vive.** Misurato aprendo una sessione vera
> con lo stesso palco del banco:
>
> | | prima (pagina a metà) | ⭐ adesso |
> |---|---|---|
> | `video.misura_massima` dichiarata dal client | ⛔ **320×240** | ⭐ **3840×2160** |
> | codec negoziato | hevc (ma cieco) | ⭐ **hevc**, profondità 8 |
> | tela concessa | ⛔ 320×240 | ⭐ **1920×1080** |
> | fotogrammi | ⛔ **0 consegnati, 0 dipinti** | ⭐ **157 consegnati, 157 dipinti** |
> | il flusso vero | — | `codec 1, «hev1.2.4.L123.90»`, 10 bit |
>
> ⇒ ⛔ **La riga «la configurazione B non è misurabile» qui sotto è SUPERATA.** Resta scritta perché
> è il verbale di quel che si sapeva alle 22:19, e perché il modo in cui è caduta — *una cura
> entrata tre minuti dopo la consegna* — è la ragione per cui le date si scrivono accanto ai numeri.
>
> ⭐⭐ **E i tre giri adesso isolano MEGLIO di quanto il piano sperasse.** Con la pagina di adesso
> **A negozia HEVC in software**, quindi:
>
> | confronto | isola | perché è pulito |
> |---|---|---|
> | **C → A** | il **CODEC** (AV1 sw → HEVC sw) | ⚠ ma porta dentro **due** cambiamenti: il codec **e** la pagina (C usa quella vecchia) |
> | ⭐⭐ **A → B** | **solo l'HARDWARE**, a codec costante | HEVC software contro HEVC hardware, **stessa pagina, stesso palco, stesso banco**: ⛔ **un solo cambiamento** |
>
> ⇒ Il piano temeva di dover confrontare *«AV1 in software contro HEVC in hardware»* e di doverlo
> dichiarare un confronto sporco. **Non lo è più**, ed è la differenza fra un numero e un numero con
> un asterisco.
>
> ### ⛔⛔ E IL BANCO SI È RIFIUTATO DI NUOVO — perché vedeva **sé stesso** come vicino
>
> Al primo lancio di A l'arbitro ha detto: *«NON SONO SOLO — NIC-OS: un vicino mangia CPU:
> **remotix** (pid 402734) al **67,8 %**»*.
>
> ⛔ Quel `remotix` era **il figlio del prodotto che il banco stesso aveva appena acceso**, e quel
> 67,8 % **era la misura**: x265 che codifica 1920×1080 in software. ⇒ *Un arbitro che conta il
> prodotto come vicino rifiuta il banco **per il fenomeno che il banco esiste per misurare**.*
>
> ⭐ **La cura, e i suoi confini**: il banco adesso dichiara come **propri** i processi letti dal
> **suo** pidfile sul server (`/media/REMOTIX/tmp/03-b17/pid`) più figli e nipoti, li toglie dai
> vicini e **richiama `_giudica()` dell'arbitro** — non lo riscrive.
> ⛔ **E toglie SOLO quelli**: sulla stessa macchina girano i tre prodotti dell'utente (7448, 7501,
> 7561) e restano vicini a tutti gli effetti. *La differenza fra «tolgo me stesso» e «tolgo chiunque
> si chiami come me» è la differenza fra una cura e un atteso allargato.*
> `[M]` verificato dal vivo: miei pid **[402639, 402645, 402734]**, vicini altrui **nessuno**,
> verdetto **SOLO: True**.
>
> ⚠ **E la certificazione è stata rifatta prima di misurare**, perché il banco era cambiato:
> `--certifica` **PROMOSSO 54 su 54**. *(Il ciclo completo sano → guasto → risanato è in fondo.)*

*Scritto in due tempi, e si legge in due tempi.*

> ⚠ **COME È FATTO QUESTO FILE.** La prima metà è il verbale del **13 agosto, ore 22:19**, quando
> il muro dei zero fotogrammi sembrava insuperabile. La seconda è la **notte del 14**, quando il
> muro era già caduto — *tre minuti dopo che avevo consegnato*. ⛔ **Le righe superate non sono
> state cancellate**: un verbale non si riscrive, si rettifica accanto. Dove una conclusione è
> caduta, c'è scritto **da che cosa** e **quando**.
>
> ⇒ Chi ha fretta legga: **il riquadro qui sotto**, poi **«I TRE GIRI DELLA NOTTE»**, poi
> **`A → B`**. Il resto è il come ci si è arrivati, e le trappole che ci sono in mezzo.

### Dove sta che cosa

| | |
|---|---|
| ⭐⭐ **il numero della fase** | **«IL GIRO SUL DEPOSITO»** — l'albero che l'utente giudicherà |
| ⭐⭐ **la risposta del piano** (E1·E2·E3·E4) | **«CHE COSA DICE QUESTA NOTTE ALLA FASE 3»** |
| ⭐ **il confronto che chiude la fase** | **«`A → B`»** — una sola variabile, il binario |
| ⭐ **i tre giri e come si leggono** | **«I TRE GIRI DELLA NOTTE»** |
| ⛔ **le riserve sul numero** | **«MA IL NUMERO NON SI PUÒ COMPRARE»** e **«CHE COSA RESTA `[?]`»** |
| ⛔ **gli errori miei, trovati e curati** | **«CHE COSA NON HA FUNZIONATO»** (due, uno per notte) |
| ⚠ **il verbale del 13, superato** | tutto ciò che porta *«(13 agosto)»* o sta dentro un blocco richiudibile |

---

## ⛔⛔⛔ In una riga — *(scritto il 13 alle 22:19; il punto 2 è caduto tre minuti dopo)*

**Il banco `03-b17` non misura sull'Xvfb: misura sul DESKTOP VERO DELL'UTENTE.** Provato con la
controprova che non passa dal browser — `xlsclients` sullo schermo che il banco stesso accende dice
**zero clienti**. ⇒ ⛔ **I 74,58 ms del 13 agosto sono stati presi sul desktop dell'utente**, con la
sua GPU e **con la contesa del suo desktop dentro il numero** — che è esattamente la contaminazione
per cui §0-bis esiste.

E c'è un secondo muro, indipendente: **con la pagina curata la sessione consegna ZERO fotogrammi**
— HEVC viene negoziato, il client non lo decodifica, la tela crolla a **320×240** e il prodotto si
rifiuta (giustamente) di spedire un 1920×1080 dentro un'intestazione da 320×240.

⇒ ⛔ **La configurazione B — il «dopo» in hardware — NON è misurabile oggi**, e non per colpa del
codificatore: il codificatore hardware non viene mai raggiunto.

> ## ⭐⭐⭐ E LA NOTTE DEL 14 IL «DOPO» È STATO MISURATO — ecco il risultato in cinque righe
>
> | | |
> |---|---|
> | ⭐⭐ **la codifica in hardware funziona** | la chiave costa **4 894 µs** contro **114 533 µs** in software — **23 volte meno**, letto dal prodotto. Il tratto della codifica passa da **61,8 a 30,4 ms** |
> | ⭐⭐ **il ritmo raddoppia** | **14,5 → 30,2** fotogrammi al secondo |
> | ⭐ **e gli altri quattro tratti restano dove sono** | Mutter −0,01 · filo −0,07 · decodifica −0,72 ⇒ **la sottrazione è pulita, l'architettura è assolta** |
> | ⛔ **ma il totale è 75,23 ms e SFORA** | e — scomodo — è ancora **peggio** dei **72,40** di AV1 in software |
> | ⛔⛔ **perché il collo si è SPOSTATO sul DISEGNO** | il passaggio a HEVC porta il disegno da **9,1 a 25,1 ms**: la codifica ne ha tolti 31, il disegno ne ha aggiunti 16 |
>
> ⛔ **E il numero si consegna con una riserva scritta**: su B **P1 è rosso** (iniettati 25 → +29,58;
> iniettati 60 → +70,18), e ⭐ **il ponte non c'entra** — il suo scarto di consegna è **0 µs** a
> mediana, p95 e max. ⇒ **Non compro il numero**: si consegna con il suo metro dichiarato rosso.

⚠ *(Le righe qui sotto sono del 13 e restano per il verbale; il «dopo» è nel riquadro qui sopra.)*

⭐ **Quel che invece si è misurato, ed è solido:**

| | |
|---|---|
| **il «prima» di oggi** | **72,397 ms** di mediana (n = 508), col palco dichiarato accanto, in una finestra esclusiva verificata sulle **due** macchine |
| ⭐ **i cinque tratti** | Mutter **16,66** · **codifica+filo 39,82 (il 55 %)** · filo **0,26** · decodifica **6,32** · disegno **9,11** ⇒ **il numero del 13 agosto regge**, misurato di nuovo e con un altro banco |
| ⭐ **il controllo che salva la fase** | il binario **hardware**, con la stessa pagina, dà **73,68 ms**: ⛔ **+1,3 ms, cioè niente** — perché la sessione negozia AV1 e **AV1 in hardware non esiste**. Chi avesse acceso l'albero di B così com'era consegnato avrebbe scritto *«l'hardware non serve»* |
| ⛔ **e un errore mio, trovato e curato** | il banco stampava *«renderD128 aperto ⇒ la codifica passa dall'HARDWARE»*: **falso**, ed era una deduzione travestita da misura |

---

## 📐 IL GIRO SUL DEPOSITO — `E3-deposito-hw-5punti`

*⭐ **È il numero della fase**: gira sull'albero che l'utente giudicherà domattina, non su una sua
copia. Binario `b4597b96…` costruito dal deposito di stanotte (`codificatore.c` `dcc7ed3a…`, 11
riferimenti VA-API), pagina `b41e4f16…` — **la stessa dei giri A e B**, non toccata dal travaso.*

⭐ **La finestra era aperta su tutt'e due**, verificata prima di accendere: carico **0,23** su CHUWI
e **0,13** su NIC-OS, **zero** vicini affamati, **zero** porte altrui.

⛔ **E il giro ha CINQUE punti** (`0 · 5 · 10 · 25 · 60`) invece di due, apposta per decidere P1 con
le previsioni **scritte prima di misurare**:

| ipotesi | previsione a `N=5` | a `N=10` |
|---|---|---|
| ⭐ errore **proporzionale** (`1,142·N − 1,31`) | **+4,4** | **+10,1** |
| ⛔ **ginocchio** oltre una soglia | **sotto** la retta, vicino a **+5** | vicino a **+10** |

### ⭐ La codifica in hardware, sul deposito, **verificata con la regola doppia**

```
codec negoziato: hevc (1) · tela 1920×1080
nodo di rendering: renderD128 APERTO
PRIMO fotogramma: codec 1, «hev1.2.4.L120.B0», 10 bit,
                  caricamento sulla GPU 3933 us, codifica 5105 us
⇒ ⭐ codifica: IN HARDWARE — codec HEVC E nodo renderD128: le due cose insieme
```

### ⛔⛔ E il giro ha SMENTITO tutt'e due le mie ipotesi — poi ha detto la verità

Le salite del tratto 2 **non** stanno sulla retta del +14 % **e non** sono N esatto: sono
**sotto** N (−1,28 dove chiedevo 5; +5,23 dove chiedevo 10). ⇒ Nessuna delle due previsioni regge.

⭐ **E la causa non era in nessuna delle due**: la mediana per **quarti del giro base** la mostra
subito, e si vede **prima** di guardare P1:

| | 1° quarto | 2° | 3° | 4° | fotogrammi > 1,5× la mediana |
|---|---|---|---|---|---|
| **B** (copia) | 76,5 | 77,3 | 72,8 | 75,1 | 4,1 % |
| ⛔ **D** (deposito) | **130,3** | **165,2** | 79,2 | 77,6 | ⛔ **32,5 %** |

⇒ ⛔ **Un TRANSITORIO D'AVVIO**, lungo circa metà giro. Gonfia la mediana base (85,3 invece di 78)
e per questo tutte le salite risultano **più piccole** di N. *Non era il ponte, non era la
saturazione, non era un errore proporzionale: era la partenza.*

⭐ **E il ponte è scagionato, stavolta col dato giusto** — letto **mentre ritardava**, non a giro
finito: scarto di consegna **18 µs** di mediana, 89 al p95, 1015 al massimo, a `ritardo_ms` 0, 5 e
25. *La cura che avevo messo nel banco ha dato la risposta al primo giro in cui è servita.*

### ⭐⭐ IL NUMERO — a regime, e con P1 **VERDE**

⛔ **Il taglio è una scelta fatta dopo aver visto i dati, e va difesa o ritirata.** La difendo con
tre cose, non con una:

| | |
|---|---|
| **1. il transitorio si vede PRIMA di P1** | la tabella dei quarti qui sopra non guarda P1: guarda solo il giro base |
| **2. il taglio NON fabbrica verde** | applicato ai giri **sani** cambia poco — B **−1,56** · C **−0,54** · A **+0,99** — e cambia molto **solo** su D (**−7,17**), cioè solo dove il transitorio c'è |
| ⭐⭐ **3. e non è un passe-partout** | ⛔ **B resta ROSSO anche a regime** (+6,98 e +12,11). Se «seconda metà» fosse il trucco per far tornare il verde, avrebbe salvato anche B. **Non lo salva.** |

⇒ Con la **stessa tolleranza** (±3 ms, **non toccata**), sulla seconda metà:

| ritardo iniettato | salita | scarto |
|---|---|---|
| 5 ms | +2,40 | −2,60 ✅ |
| 10 ms | +11,42 | +1,42 ✅ |
| 25 ms | +25,91 | +0,91 ✅ |
| 60 ms | +61,46 | +1,46 ✅ |

> ## ⭐⭐⭐ **78,1 ms** — il numero della fase 3
>
> *Giro `E3-deposito-hw-5punti`, albero del **deposito**, codifica HEVC **in hardware**, n = **379**,
> **P1 VERDE**, finestra esclusiva verificata sulle due macchine prima e dopo, palco identico ai
> due estremi.*
>
> | | |
> |---|---|
> | **mediana** | **78,115 ms** |
> | distribuzione | p25 **73,9** · p75 **84,7** · p95 **96,1** · media **80,1** — ⭐ **pulita**, niente coda |
> | col pezzo cieco `[?]` | **94,1 – 118,1 ms** sullo schermo di un utente |
> | contro 50 e contro 40 | ⛔ **SFORA** tutt'e due |
> | ritmo | **30,01** fotogrammi al secondo |

### ⛔ E i quattro giri affiancati, **a parità di trattamento** (seconda metà di ciascuno)

| tratto (mediane, ms) | **C** AV1 sw | **A** HEVC sw | **B** HEVC hw *copia* | ⭐ **D** HEVC hw **deposito** |
|---|---|---|---|---|
| campioni | 254 | 188 | 400 | **379** |
| ⭐ **ritmo** | 21,98 | 14,60 | 30,22 | ⭐ **30,01** |
| 1 disegno → cattura (**Mutter**) | 16,658 | 16,626 | 16,610 | **16,604** |
| 2 cattura → primo byte (**codifica**) | 39,671 | ⛔ 63,223 | 30,064 | ⭐ **31,784** |
| 3 il filo | 0,250 | 0,310 | 0,255 | **0,190** |
| 4 stream → `decode()` | 0,065 | 0,075 | 0,090 | **0,080** |
| 5 **la decodifica** | 6,315 | 1,485 | 0,760 | ⭐ **0,730** |
| 6 **il disegno** | ⭐ 9,070 | ⛔ 28,985 | 24,675 | ⛔ **27,995** |
| **7 TOTALE** | **71,862** | **109,770** | **73,672** | ⭐ **78,115** |
| **P1** | ✅ verde | — | ⛔ **rosso** | ⭐ **VERDE** |

⇒ ⭐⭐ **`A → D`, cioè HEVC software → HEVC hardware sullo stesso deposito**: totale **109,77 →
78,12** (**−31,7 ms**), tratto della codifica **63,22 → 31,78** (**−31,4**), ritmo **14,6 → 30,0**
(**×2,06**), e ⭐ **gli altri tratti fermi** (Mutter −0,02 · filo −0,12 · decodifica −0,76).
**L'architettura è assolta.**

⇒ ⛔ **Ma `C → D` resta +6,3 ms**: HEVC in hardware è ancora **peggio** di AV1 in software, e la
ragione è **una sola riga della tabella**: il disegno, **9,07 → 28,00**.

> ### ⛔⛔⛔ **Il collo di bottiglia della fase 3 è il DISEGNO — 28,0 ms su 78,1, il 36 %**
>
> La codifica hardware ha fatto il suo lavoro e ha ceduto 31 ms. ⛔ Ma il codec che la rende
> possibile ne aggiunge **19 sul disegno**, e l'hardware ne recupera **uno solo** (28,99 → 28,00).
> ⇒ *Oggi la codifica costa **5 ms** e il disegno ne costa **28**.*

---

## 📐 I TRE GIRI DELLA NOTTE — A · B · C

⛔ **Come si leggono, e va letto prima dei numeri.**

| | binario | pagina | codec negoziato | dove codifica |
|---|---|---|---|---|
| **A** il prima | software `3d2c7626` | ⭐ **di adesso** `b41e4f16` | **HEVC** | software (x265) |
| **B** il dopo | ⭐ **hardware** `7a5ee61d` | ⭐ **la stessa di A** | **HEVC** | ⇒ da misurare |
| **C** il controllo | software `3d2c7626` | ⚠ **vecchia** `ec169e5d` | **AV1** | software (SVT-AV1) |

- ⭐⭐ **`A → B` cambia UNA cosa sola: il binario.** Stessa pagina, stesso palco, stesso banco,
  stesso codec. **È il confronto su cui si chiude la fase.**
- ⚠ **`C → A` ne cambia DUE**: il codec **e** la pagina. ⇒ Serve a separare *«è il codec»* da
  *«è l'hardware»*, **non** a produrre un numero.

> ⛔ **LA REGOLA DEL VERDETTO «HARDWARE», e non si negozia**: si scrive **solo** con **nodo DRM
> aperto E codec che l'hardware sa fare**, letti **nello stesso giro**. ⭐ Nasce da un errore mio
> del giro precedente — il banco stampava *«renderD128 aperto ⇒ HARDWARE»* mentre codificava
> `av01…`, e AV1 in hardware su questa macchina **non esiste**. ⇒ Se B mostrasse `hev1…` **senza**
> `renderD128`, quello **è** il risultato: il binario ripiega in software, si scrive, e i due numeri
> **non si sottraggono**.

⚠ **E il `n` di ogni giro sta accanto a ogni mediana**: una mediana su 150 campioni e una su 500
non sono la stessa cosa, e la differenza si dichiara invece di lasciarla dedurre.

### 📐 A e C affiancati — ⛔ e il passaggio a HEVC **peggiora** il numero

*Mediane in ms. **A** = `E2-A-software-hevc` (n = **375**) · **C** = `E-C-software-av1` (n = **508**).*

| # | tratto | **C** AV1 sw | **A** HEVC sw | differenza |
|---|---|---|---|---|
| 1 | disegno → cattura (**Mutter**) | 16,664 | 16,613 | −0,05 |
| 2 | cattura → primo byte (**codifica** + filo) | 39,822 | ⛔ **61,766** | **+21,94** |
| 3 | il filo | 0,255 | 0,305 | +0,05 |
| 4 | stream → `decode()` | 0,065 | 0,080 | +0,02 |
| 5 | **la decodifica** | 6,315 | ⭐ **1,495** | **−4,82** |
| 6 | **il disegno** (`drawImage` ×2) | 9,105 | ⛔ **29,250** | **+20,15** |
| **7** | ⭐ **TOTALE** | **72,397** | ⛔ **108,778** | **+36,38** |
| | fotogrammi al secondo | 21,21 | 14,53 | −6,68 |
| | dipinti dalla pagina | 2 121 | 1 407 | −714 |

⇒ ⛔⛔ **Passare da AV1 a HEVC, restando in software, costa 36 ms.** E la causa è **doppia**, e la
seconda non se l'aspettava nessuno:

| | |
|---|---|
| ⛔ **la codifica** | x265 costa **+22 ms** rispetto a SVT-AV1 sulla scena vera. ⚠ Coerente con la sonda della corsia B (libx265 *medium* 36,0 ms contro libsvtav1 preset 10 a 22,2) |
| ⭐ **la decodifica MIGLIORA di 4×** | 6,32 → **1,50 ms**: il client HEVC decodifica molto meglio di AV1 |
| ⛔⛔ **ma il disegno TRIPLICA** | 9,11 → **29,25 ms**. ⇒ **Il costo non è sparito: si è spostato dal decodificatore al disegno.** Sommando i due tratti «dal decoder al vetro»: AV1 **15,4 ms**, HEVC **30,7 ms** — il doppio |

> ⚠ **`[?]` PERCHÉ il disegno triplichi con HEVC, questa misura non lo dice.** L'ipotesi naturale è
> che la decodifica HEVC in hardware consegni un fotogramma **che vive sulla GPU**, e che i due
> `drawImage` paghino il trasferimento che il decodificatore non paga più. ⛔ **È una lettura, non
> una misura**, e va scritta come tale: il banco misura *quando* il tempo passa, non *dove*.
> ⭐ Ed è **il primo posto dove guardare** se il numero finale non basta.

⇒ ⭐ **E questo rende `A → B` ancora più importante**: dei 61,8 ms del tratto 2, la codifica
hardware dovrebbe togliere quasi tutto. Se lo fa, **il totale scende sotto C**; se non lo fa, HEVC
è un peggioramento e va detto.

> ### ⚠ E DUE RISERVE SU A, dichiarate accanto al numero e non in fondo
>
> | | |
> |---|---|
> | ⚠ **il campione è più piccolo** | **n = 375** contro i 508 di C — perché la catena consegna meno (14,5 fotogrammi al secondo contro 21,2). ⛔ Non è un difetto della misura: **è il fenomeno**. Ma una mediana su 375 e una su 508 non hanno la stessa larghezza di errore, e si dichiara |
> | ⚠ **la finestra «non ha retto» alla fine** | carico 1,70 su CHUWI e 2,08 su NIC-OS. ⛔ Ma il carico **era mio**: il mio Chrome di qua e il mio prodotto di là. ⚠ `03-solo.py` filtra i *vicini* per pid, **non il carico medio** ⇒ il criterio «carico > 1» scatta sul carico che il banco stesso produce. ⇒ **All'apertura ero solo su tutt'e due** (verificato), e il «non ha retto» finale è quel limite, non contesa d'altri |
>
> ⭐ **Quel che invece regge senza riserve**: P1 tarato (chiesti 25 → **+25,10**; chiesti 60 →
> **+60,03**), P2 al **100 %** (425 marche lette su 425 guardate, zero rifiuti), P3 zero falsi
> positivi, e **il palco identico ai due estremi**.

---

## ⭐⭐⭐ `A → B` — IL CONFRONTO SU CUI SI CHIUDE LA FASE

**Una sola variabile: il binario.** Stessa pagina (`b41e4f16`), stesso palco, stesso banco, stesso
codec negoziato (HEVC), stessa scena.

> ### ⭐ E la codifica in hardware è VERIFICATA con la regola doppia, non dedotta
>
> ```
> SERVER · nodo di rendering: renderD128 APERTO
> SERVER · PRIMO fotogramma: codec 1, «hev1.2.4.L120.B0», 10 bit,
>          caricamento sulla GPU 2804 us, codifica 4894 us
> SERVER · ⭐ codifica: IN HARDWARE — codec HEVC E nodo renderD128: le due cose insieme
> ```
>
> ⇒ ⭐⭐ **La confessione del prodotto, da sola, dice quasi tutto**: la chiave costava
> **114 533 µs** in software (giro A) e costa **4 894 µs** in hardware (giro B) — ⭐ **23 volte
> meno**, letto dal prodotto e non dal banco.

| # | tratto (mediane, ms) | **A** HEVC sw | **B** HEVC **hw** | differenza |
|---|---|---|---|---|
| | ⚠ **campioni (n)** | **375** | **799** | *(B ne consegna il doppio)* |
| 1 | disegno → cattura (**Mutter**) | 16,613 | 16,607 | −0,01 |
| 2 | cattura → primo byte (**codifica** + filo) | 61,766 | ⭐ **30,373** | ⭐⭐ **−31,39** |
| 3 | il filo | 0,305 | 0,240 | −0,07 |
| 4 | stream → `decode()` | 0,080 | 0,090 | +0,01 |
| 5 | **la decodifica** | 1,495 | ⭐ **0,775** | −0,72 |
| 6 | **il disegno** (`drawImage` ×2) | 29,250 | 25,105 | −4,15 |
| **7** | ⭐ **TOTALE** | **108,778** | ⭐ **75,230** | ⭐⭐ **−33,55** |
| | ⭐ **fotogrammi al secondo** | 14,53 | ⭐⭐ **30,18** | **×2,08** |
| | dipinti dalla pagina | 1 407 | **2 949** | ×2,10 |

⇒ ⭐⭐ **La codifica in hardware fa quel che prometteva, e sui tratti la prova è netta**: il tratto
della codifica **si dimezza** (61,8 → 30,4) e **il ritmo raddoppia** (14,5 → 30,2 al secondo).
⭐ **E gli altri quattro tratti restano dove sono** — Mutter −0,01, filo −0,07, decodifica −0,72 —
cioè **la sottrazione è pulita e l'architettura è assolta** (E2, la domanda del piano).

### ⛔⛔ MA IL NUMERO NON SI PUÒ COMPRARE, E DUE COSE LO IMPEDISCONO

**1. ⛔ P1 è ROSSO su B, e P1 è il controllo che valida il metro.**

| ritardo iniettato | salita misurata | scarto | tolleranza |
|---|---|---|---|
| 25 ms | **29,58** | ⛔ **+4,58** | ±3 |
| 60 ms | **70,18** | ⛔ **+10,18** | ±3 |

⭐ **E il ponte NON è il colpevole — verificato, non supposto**: il suo scarto di consegna, misurato
da lui stesso su 20 000 pacchetti, è **0 µs a mediana, p95 e max**. Il ponte inietta esattamente N.

> ## ⛔⛔ LA MIA PISTA È SMENTITA — e dai dati che avevo già in mano
>
> *Avevo scritto: «la catena è satura a 30 fps». ⭐ **Falso**, e la prova non ha richiesto un giro
> nuovo: bastava scomporre i giri a N≠0 dello **stesso verbale**.*
>
> | | N=0 | N=25 | N=60 |
> |---|---|---|---|
> | ⭐ **ritmo consegnato** | 30,18 | **30,01** | **30,33** |
> | tratto **2** (cattura → primo byte) | 30,373 | 57,608 | 97,572 |
> | tratto **3** (lo stream sul filo) | 0,240 | 0,210 | 0,275 |
> | tratti **1 · 4 · 5** | — | fermi entro **0,06** | fermi entro **0,06** |
> | tratto **6** (il disegno) | 25,105 | +2,05 | +0,09 |
>
> ⇒ ⛔ **Il ritmo NON cala**: se la catena si accodasse, scenderebbe. Resta piatto a 30/s.
> **La saturazione è esclusa.**
>
> ⭐⭐ **E il surplus è localizzato con precisione**: sta **tutto nel tratto 2** (+27,2 su 25
> chiesti; +67,2 su 60), e ⛔ **non nel tratto 3** — cioè **non** nel tempo che il fotogramma
> impiega a passare sul filo. ⇒ **Nasce prima che il primo byte parta**: fra il `pts` della cattura
> e l'uscita del primo pacchetto. *È il server, o è il ponte — non è la catena che si accoda.*
>
> ### ⛔ E QUI DEVO CORREGGERE ME STESSO: lo scagionamento del ponte era DEBOLE
>
> Avevo scritto *«il ponte è scagionato: scarto di consegna 0 µs»*. ⛔ **Quel dato l'ho letto a giro
> finito**, quando `metti_ritardo(a, 0, …)` aveva già rimesso il ponte a **zero**: nel file c'era
> `"ritardo_ms": 0.0`. ⇒ **Uno scarto di consegna misurato a ritardo ZERO non dice niente su come il
> ponte consegna quando ritarda.** È un dato preso in una condizione diversa da quella che volevo
> giudicare — **la stessa forma d'errore che questo banco esiste per trovare negli altri**, e
> l'ho fatta io.
>
> ⭐ **Curato nel banco**: adesso il verbale del ponte si legge **all'ultima mano di ogni N**, cioè
> **mentre ritarda**, e finisce nel verbale (`ponte_per_n`) e nella riga depositata.
>
> ### ⭐ La forma del surplus, e le previsioni da falsificare
>
> Due punti non fanno una retta, ⚠ ma danno la pendenza da mettere alla prova:
>
> | | |
> |---|---|
> | salita del tratto 2 | N=25 → **+27,235** · N=60 → **+67,199** |
> | retta per i due punti | `salita ≈ **1,142·N − 1,31**` ⇒ ⛔ **il 14,2 % in più** di quel che si chiede |
>
> ⇒ **Il giro a cinque punti (0 · 5 · 10 · 25 · 60) decide**, e le due ipotesi danno risposte
> diverse **prima** di misurare:
>
> | ipotesi | previsione a N=5 e N=10 |
> |---|---|
> | ⭐ **errore proporzionale** (il ponte consegna il 14 % in più) | **+4,4** e **+10,1** — sulla retta |
> | ⛔ **ginocchio** (qualcosa scatta oltre una soglia) | **sotto** la retta, vicini a +5 e +10 esatti |
>
> ⚠ **E `--ritardi 0,5,10,25,60` è già un parametro del banco**: non serve codice nuovo per farlo,
> serve il palco.

⇒ ⚠ ~~La lettura più probabile: a 30 fps la catena è satura~~ — **SMENTITA il 14 agosto**, vedi il
riquadro qui sopra. ⭐ Il riscontro che resta valido: in A (14,5/s) e in C (21,2/s) P1 torna
**perfetto** (+25,10/+60,03 e +24,92/+60,00) — **P1 cade solo su B**, e adesso si sa **in quale
tratto**.
⛔ **Quel che questo NON autorizza a dire**: che il 75,23 sia sbagliato. Il giro base è a ritardo
**zero**, e i tratti si sottraggono fra istanti dello stesso fotogramma. ⛔ Ma **P1 è rosso, e un
numero con il proprio metro rosso si consegna con la riserva scritta accanto**, non senza.

**2. ⛔⛔ E il totale è ancora PEGGIO di AV1 in software.**

| | totale | tratto 2 (codifica) | tratto 6 (disegno) | fps |
|---|---|---|---|---|
| **C** AV1 software | ⭐ **72,397** | 39,822 | ⭐ **9,105** | 21,21 |
| **A** HEVC software | 108,778 | ⛔ 61,766 | 29,250 | 14,53 |
| **B** HEVC **hardware** | **75,230** | ⭐ **30,373** | ⛔ **25,105** | ⭐ **30,18** |

⇒ ⛔⛔ **Il collo di bottiglia si è SPOSTATO: adesso è il DISEGNO.** La codifica hardware ha tolto
31 ms, ma il passaggio a HEVC ne ha aggiunti **16 sul disegno** (9,1 → 25,1) ⇒ il guadagno netto
contro la configurazione di partenza è **−2,8 ms soltanto** (72,40 → 75,23: in realtà **+2,8**,
cioè B è ancora **peggio** di C).

⭐ **E questo NON dice che l'hardware non serve**: dice che serve **e non basta**, perché nel
frattempo il codec ha spostato il costo dal decodificatore al disegno. I due effetti si vedono
separati solo perché i tre giri esistono tutti e tre.

### Il verdetto contro il tetto

| | |
|---|---|
| **B, mediana** | **75,23 ms** (n = 799) ⛔ **SFORA** contro 50 e contro 40 |
| col pezzo cieco `[?]` | **91,2 – 115,2 ms** sullo schermo di un utente |
| p95 | 110,6 ms |
| errore d'orologio | dichiarato accanto al numero nel verbale |

---

## ⛔ LE DUE PREMESSE SMENTITE, con il caso

### 1. ⛔⛔⛔ Il palco: il banco misura dove non crede di misurare

Il coordinatore ha chiesto di verificarlo. **Verificato, e confermato con tre prove indipendenti.**
L'esperimento apre il palco **con la classe `Palco` del banco**, senza cambiarle una riga:

| prova | esito |
|---|---|
| `Xvfb :88` acceso dal banco | ⭐ risponde a `xdpyinfo`: **1600×1200** |
| ⛔⛔ **`xlsclients -display :88`** | ⛔ **ZERO clienti** — nessuno è attaccato allo schermo che il banco ha acceso |
| `screen` letto **dalla pagina** | ⛔ **2560×1080** — il monitor dell'utente, non l'Xvfb |
| `webgl` letto dalla pagina | `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))` — **la GPU vera** |
| `--ozone-platform` fra le bandiere | ⛔ **nessuna** |
| ambiente | `XDG_SESSION_TYPE=wayland`, e il banco toglie `WAYLAND_DISPLAY` **ma non basta** |

⇒ ⭐ **La riga del coordinatore regge, e la sua correzione era giusta**: `--disable-gpu` contava,
ma solo perché il palco era **già quello vero in tutt'e due i bracci** dell'A/B.

⛔ **E la conseguenza sul numero della fase va detta per intero**: i 74,58 ms (e i 74,576, e i
72,19) sono stati misurati **su un browser che condivideva lo schermo, il compositore e la GPU con
il desktop su cui l'utente stava lavorando**. Non è «probabilmente contaminato»: è **misurato che
il palco non era quello dichiarato**, e nessun verbale lo diceva perché `03-b17-ritardo.py` **non
scriveva quale palco fosse**. Adesso lo scrive.

> ⭐ **E il palco NON è stato aggiustato**, per ordine del coordinatore e perché è la cosa giusta:
> spostarlo fra il «prima» e il «dopo» distruggerebbe la sottrazione, che è l'unica ragione per cui
> la corsia E esiste. ⇒ Il palco è **dichiarato**, non curato, ed entra fra i **campi portanti** che
> il banco confronta ai due estremi del giro.

### 2. ⛔⛔ Con la pagina curata la sessione consegna ZERO fotogrammi

⚠ *Non è una smentita della cura in sé — le sonde curate decodificano davvero, e la corsia B l'ha
misurato. È che **dentro la sessione vera, su questo palco, la catena finisce a zero**, e la catena
vera è l'unica che conta per la corsia E.*

Letto **nel registro del prodotto**, ancorato a questa accensione:

```
il client dichiara video.misura_massima=320x240: e' il tetto che la tela concessa DEVE rispettare
negoziato video.codec=hevc video.profondita=8
⚠ RIPIEGO DICHIARATO (§4.5): tela chiesta 1920x1080, tetto del decodificatore 320x240 — CONCESSA 320x240
⛔ tela in vigore 320x240 ma il fotogramma catturato e' 1920x1080 — NON lo spedisco (§6.2)
```

E dalla pagina, nella stessa sessione:

```
⛔ hevc non ha dipinto nemmeno alla tela minima di §4.5 (320x240): EncodingError: Decoding error.
sonda video · misura AV1: fino a 3840x2160 (6 gradini, 153 ms)
```

⇒ ⛔ **Tre fatti che non stanno insieme, e vanno guardati da chi possiede la pagina:**

1. HEVC **non dipinge** (`EncodingError` perfino a 320×240) — ⛔ e **non è la GPU**: questo browser
   ha la Intel vera (prova qui sopra);
2. eppure HEVC **viene offerto e negoziato** — `codec_buoni` doveva filtrarlo e non l'ha fatto;
3. e il fallimento di HEVC **trascina `video.misura_massima` a 320×240** anche se AV1 arriva a 4K
   ⇒ la tela crolla, e il prodotto smette di spedire.

⛔ **Il prodotto qui non sbaglia**: §4.5 e §6.2 sono rispettate alla lettera, e il rifiuto di
spedire è la cosa giusta. Il difetto è a monte, nella pagina.

⇒ ⛔⛔ **Finché questo non è chiuso, il codificatore HEVC in hardware non può essere esercitato da
nessun banco che passi dalla sessione vera**: non ci arriva un fotogramma.

---

## Le tre configurazioni, e che cosa è stato possibile — *(13 agosto; superata)*

> ⚠ **Questa sezione è del 13 e va letta come verbale, non come stato.** Le tre configurazioni sono
> poi state misurate tutte — vedi **«I TRE GIRI DELLA NOTTE»** — e il giro che conta è quello sul
> **deposito**, in testa al file.

⭐ Tre alberi costruiti sul server, **una variabile per volta** — e le impronte lo dimostrano:

| | binario | pagina | che cosa isola |
|---|---|---|---|
| **A** il prima | `3d2c7626` software | `d2892024` **di oggi** | la linea di partenza di oggi |
| **B** il dopo | `7a5ee61d` **hardware** (di B) | `d2892024` **la stessa di A** | ⇒ A→B cambia **solo il binario** |
| **C** il controllo | `3d2c7626` **lo stesso di A** | `ec169e5d` vecchia | ⇒ A→C cambia **solo la pagina** |

⛔ **E la prima cosa che questi tre alberi hanno trovato è un difetto di consegna**: l'albero di B
(`/srv/src/03-B-src/`) porta con sé **la pagina VECCHIA** (`ec169e5d`). Chi avesse acceso B così
com'era avrebbe misurato il codificatore hardware **con la pagina che negozia AV1** — cioè con il
codificatore hardware **spento**, e avrebbe chiamato il risultato «l'hardware non serve a niente».
⇒ Nell'albero di misura la pagina è **quella di oggi**, uguale ad A.

---

## ⭐ IL BANCO, PREPARATO PRIMA DI MISURARE — i quattro lavori chiesti

⛔ Tutto quel che segue vive dentro `misura()`, che vuole due macchine e un browser: **da solo non
si può girare**. ⇒ La logica sta in **funzioni pure**, e ciascuna è **certificata col guasto
dentro** — `--certifica` è passato da 38 a **54 controlli**.

### 1. ⛔ Un verbale per giro — e adesso si RIFIUTA di cancellarne uno

Il danno era già avvenuto: `--verbale` aveva un percorso fisso e `open(..., "w")` ⇒ dei
**quattordici** giri del 13 agosto ne sopravviveva **uno**. Per la corsia E sarebbe stato peggio: i
due verbali che si devono **sottrarre** avevano lo stesso nome, e il secondo avrebbe cancellato il
primo.

| | |
|---|---|
| il nome | `<lavoro>/verbali/verbale-<giro>.json` — il giro sta **dentro** il nome, e `GIRO=…` lo nomina da fuori |
| ⛔ la sovrascrittura | **alza un errore**. Certificato: si scrive il primo, si riprova lo stesso nome → eccezione **e il primo è ancora lì intatto**; cambiato il giro, i due coesistono |
| ⚠ `verbale-ultimo.json` | resta come **puntatore** (symlink), e il banco stampa che è un puntatore e non un verbale |

### 2. ⛔ Il palco dichiarato accanto al numero (`LEZIONI.md` §2.0)

Il verbale adesso porta, **dai due capi dell'anello** e con «non ho potuto guardare» dove manca:

| lato | che cosa |
|---|---|
| **CHUWI** | le **bandiere vere** del browser · `--disable-gpu` sì/no, esplicito · ⭐ `--ozone-platform` (o la sua assenza) · ⭐ **`screen` letto dalla pagina** · ⭐ **`xlsclients` sull'Xvfb** · webgl · codec negoziato · tela · WebCodecs · `crossOriginIsolated` |
| **NIC-OS** | ⭐ **quali `/dev/dri/renderD*` il prodotto ha APERTI** · la riga del `PRIMO fotogramma codificato` |

⭐ **E il palco si legge PRIMA e DOPO**: sette campi **portanti** — fra cui il nodo di rendering e
lo schermo del browser — vengono confrontati ai due estremi, perché un palco che cambia a metà giro
fa uscire un numero che sembra buono.

> ⛔⛔ **Il nodo di rendering si misura da ROOT, e ho dovuto scoprirlo sbagliando.** Il prodotto è di
> root: `ls /proc/<pid>/fd` da utente normale risponde *Permission denied*, e un lettore ingenuo
> avrebbe letto **zero nodi DRM** concludendo **«codifica in software»** — proprio sul giro in cui la
> codifica è in hardware. ⇒ La lettura passa da un'azione nuova di `03-b17-accendi.sh`, gira sotto
> `sudo`, e consegna **anche i denominatori**: quanti processi ha trovato, quanti letti, quanti
> negati. *Zero nodi con zero processi non è «software»: è «non c'era niente da guardare».*
>
> ⚠ **E quel che il prodotto NON scrive**: il **nome del componente** di codifica (`libsvtav1` /
> `hevc_vaapi`) sta in `conf.componente` e non finisce in nessun registro. ⇒ Da fuori si sa il
> codec e si sa il nodo, **non il nome**. Una riga nel registro del prodotto trasformerebbe un
> indizio in una lettura diretta.

> ⛔ **E un fossile evitato per un pelo**: il registro del prodotto è in **append** (17 MB dopo
> mezza giornata, due accensioni dentro). Un `grep | tail -1` pescava la riga del codec **del giro
> precedente** — e infatti la prima versione ha riportato `codec 2, av01…` di un'ora prima. ⇒ La
> lettura è **ancorata all'ultima riga «pronto: https://»**, cioè a questa accensione, e la prova
> che l'ancora funziona è che subito dopo diceva onestamente *«in questa accensione non ha ancora
> codificato»*.

### 3. ⛔ La finestra esclusiva, sulle DUE macchine

`03-solo.py` dichiara da sé il proprio limite — *«guarda UNA macchina sola»* — e l'anello le
attraversa tutt'e due. ⇒ Il banco legge la scena **di qua e di là** (`03-solo.py` portato sul
server) e le **unisce**, con una regola che non si negozia:

> ⛔ **se la scena dell'altra macchina non si è potuta leggere, il verdetto è NON SOLO.** Non
> «probabilmente sì»: `LEZIONI.md` §2.0 al punto in cui costerebbe un numero di fase.

⭐ Il rifiuto lo alza **`03-solo.pretendi()`**, non il banco: la parola «solo» continua a voler dire
una cosa sola ai due capi. **Nessuna bandiera per scavalcarlo** — una via d'uscita sarebbe la stessa
mossa di allargare l'atteso finché passa.

> ⭐⭐ **E ha funzionato al primo colpo: si è rifiutato, e aveva ragione su DUE cose mie.**
>
> | che cosa ha visto | che cos'era |
> |---|---|
> | ⛔ *«un vicino mangia CPU: awk al 99,7 %»* ×2 sul server | **miei**: due `awk` lasciati girare da una prima versione del lettore del palco. ⚠ Il `timeout` locale su `ssh` **non uccide il comando remoto** — lezione pagata qui |
> | ⛔ *«porte :76xx che non sono mie: 7605, 7615»* | ⛔ un **falso rosso permanente**: `03-solo.py --json` gira sul server **senza sapere quali porte sono mie**, e dalla riga di comando non si possono dichiarare ⇒ vedeva il mio ponte e il mio prodotto come estranei. Curato togliendo le mie porte e **richiamando `_giudica()` dell'arbitro**, non riscrivendolo |
>
> ⇒ ⚠ **E `03-solo.py` ha un terzo modo di sbagliare, che è del coordinatore e non mio**: `ps pcpu`
> è la **media dalla nascita** del processo, non il carico di adesso. `[M]` un `python3` appena nato
> compariva al **50,0 %** e stava allo **0,0 %** misurato su 4 s; un `firefox-esr` al **21,7 %** era
> fermo. ⇒ Un vicino che ha ciclato un'ora fa fa scattare l'arbitro **oggi**. La cura è leggere
> `/proc/<pid>/stat` due volte su una finestra dichiarata.

### 4. ⭐ Il commento che dichiarava un controllo che il codice non fa

Deciso dal coordinatore: **si stringe il commento, non il codice.** Fatto — il commento adesso dice
che gli `extra` **non bocciano**, che è una **scelta** e non una dimenticanza, e perché: stringere
il controllo adesso boccerebbe il giro sano e sposterebbe il metro **nel mezzo** della misura.

### La certificazione, rifatta **due volte**: prima di misurare e dopo l'ultima cura

⛔ Erano cambiati `pagina.html` (per mano del coordinatore) e il banco (per mano mia) ⇒ la
certificazione delle 21:30 era **scaduta**. E dopo la cura del lettore dei nodi DRM è scaduta di
nuovo. **Rifatta tutt'e due le volte**, e la seconda è quella che vale:

| passo | uscita | esito | la marca, contata |
|---|---|---|---|
| **SANO** | 0 | PROMOSSO **54/54** | 0 volte |
| **GUASTO** | 1 | BOCCIATO **53/54** | ⭐ **1 volta** |
| **RISANATO** | 0 | PROMOSSO **54/54** | 0 volte |

Copia tornata `941ce339…`, byte per byte l'originale. Marca invariata:
`rossi nessuno (attesi ['P3'])`. ⇒ La riga è in `banchi/01-b12-registro-C.jsonl` — ⛔ la **mia
scheggia**, non il registro comune.

---

## 📐 LA MISURA C — il «prima» di oggi, e **il palco è dichiarato per la prima volta**

*Giro `E-C-software-av1`, verbale `/tmp/03-b17/verbali/verbale-E-C-software-av1.json` (2,0 MB).*

> ### ⛔ IL PALCO DI QUESTO NUMERO — e va letto **prima** del numero
>
> | | |
> |---|---|
> | browser | Chrome, **`--disable-gpu` NO**, ⛔ **nessuna `--ozone-platform`** |
> | ⛔⛔ **dove stava davvero** | `screen` **2560×1080** e **0 clienti** sull'Xvfb `:85` ⇒ **sul desktop dell'utente** |
> | gpu vista dalla pagina | `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N), OpenGL ES 3.2)` — **vera** |
> | codec negoziato | **av1 (2)**, tela **1920×1080**, WebCodecs sì |
> | ⭐ nodo di rendering | ⛔ **NESSUN nodo DRM aperto** (9 processi, 9 letti, **0 negati**, letti da **root**) ⇒ **codifica in SOFTWARE**, ed è una misura |
> | codificatore confessato | `codec 2, «av01.0.09M.10», profondità 10, livello 9, promozione 8→10 dichiarata` |
> | finestra esclusiva | ⭐ **solo su tutt'e due le macchine** all'apertura |
> | orologio | errore **0,666 ms**, deriva **−0,82 ppm**, `timeOrigin` contro CDP: **9 µs** |

**I sette controlli**: P1 ✅ · P2 ✅ · P3 ✅ · **P5 non eseguito** · P6 ✅ · P7 ✅ · P8 ✅

⭐ **E P1 è il migliore mai registrato da questo banco**: chiesti 25 ms → **+24,92** (scarto −0,08);
chiesti 60 ms → **+60,00** (scarto −0,00). *Il metro è tarato.*

### Il numero

| | |
|---|---|
| **mediana** | **72,397 ms** (n = 508) |
| p95 · p99 · max | 95,19 · 217,74 · 383,85 |
| col pezzo cieco | **88,4 – 112,4 ms** sullo schermo di un utente |
| contro 50 e contro 40 | ⛔ **SFORA** tutt'e due, anche al p95 |

### ⭐ E2 — I CINQUE TRATTI AFFIANCATI (mediane, ms)

| # | tratto | mediana | quota |
|---|---|---|---|
| 1 | disegno → cattura (**Mutter**) | **16,664** | 23 % |
| 2 | cattura → primo byte in pagina (**codifica + filo**) | ⛔ **39,822** | **55 %** |
| 3 | primo byte → ultimo byte (**il filo**) | 0,255 | 0,4 % |
| 4 | stream completo → `decode()` | 0,065 | 0,1 % |
| 5 | `decode()` → richiamo (**la decodifica**) | 6,315 | 8,7 % |
| 6 | richiamo → disegno finito (**`drawImage` ×2**) | 9,105 | 12,6 % |
| **7** | ⭐ **TOTALE** | **72,397** | 100 % |
| 8 | ⛔ `[?]` disegno → pixel acceso | **16–40** *(stimato, nessuna API lo vede)* | — |

⇒ ⭐ **I quattro tratti «non di codifica» sono dove il piano li aspettava**: Mutter **16,66** (il
piano diceva 16,66), disegno **9,11** (diceva 10,51), decodifica **6,32** (diceva 7,58), filo
**0,26** (diceva 0,32). ⛔ E il tratto 2 vale **39,8 ms, il 55 %** — cioè *il numero del 13 agosto
regge oggi, con un altro banco e un'altra pagina*.

> ⚠ **E il tratto 6 misura il costo di METTERE IN CODA, non di dipingere** — rilievo della corsia D:
> obbligando Chrome a finire il lavoro (rilettura di 1 pixel) il tratto passa da 5,6 a 9,4 ms,
> cioè **due terzi del disegno sono rimandati**. ⇒ I 9,105 ms qui sopra sono un **minimo**, e il
> pezzo rimandato finisce nel pezzo cieco.

### ⭐ E3 — i fotogrammi consegnati accanto ai millisecondi

| | |
|---|---|
| ritmo consegnato | **21,21 al secondo** (intervalli, non «quanti diviso quanto») |
| dipinti dalla pagina | **2 121** in 90 s |
| costo del banco | lettura pixel **1,295 ms** mediana; ritmo 21,42 → 20,93 con la lettura (**−2,3 %**) |
| P5 | ⛔ **non eseguito**, e stavolta **misurato ai due capi**: 0 scavalcati nel campione **e** 0 `scartati_ordine` dichiarati dal prodotto su 315 consegnati |

---

> ### ⚠ E LA FINESTRA ESCLUSIVA HA DETTO «NON HA RETTO» ALLA FINE — ma il vicino ero io
>
> A fine giro l'arbitro ha scritto: *«NIC-OS: alla fine non ero solo — carico 1,44; un vicino mangia
> CPU: **remotix** (pid 399985) al **91,4 %**»*.
>
> ⛔ Quel `remotix` al 91,4 % **è il prodotto che sto misurando**, e quel 91,4 % **è la misura**:
> è SVT-AV1 che codifica 1920×1080 in software. ⇒ Non è contesa, è il fenomeno.
> ⚠ Ma l'arbitro non può saperlo: `03-solo.py` prende `miei_pid`, e **il pid del prodotto sta
> sull'altra macchina** — dalla riga di comando non si dichiara. ⇒ È lo stesso falso rosso delle
> porte, un piano più in là, e va nominato prima che qualcuno lo legga come contaminazione.

---

## 📐 LA MISURA B — il binario **hardware**, con la **stessa pagina** di C

⛔ **Questo non è il «dopo» che il piano voleva, e va detto subito.** Il «dopo» vero vuole HEVC
negoziato, e HEVC negoziato **non arriva a un fotogramma** (vedi il muro n. 2). ⇒ Quel che si può
misurare stanotte è un'altra domanda, più stretta ma vera:

> **Il binario con la codifica hardware, quando la sessione negozia AV1, cambia qualcosa?**

⭐ E come A/B è pulito: **stessa pagina di C** (`ec169e5d`), **stesso palco**, stessa scena, stesso
banco ⇒ **l'unica variabile è il binario** (`3d2c7626` → `7a5ee61d`).

### La risposta: **no, non cambia niente** — ed è il controllo che salva la fase

*Giro `E-B-hardware-stessapagina`, verbale da 2,06 MB. Controlli: P1 ✅ P2 ✅ P3 ✅ **P5 non
eseguito** P6 ✅ P7 ✅ P8 ✅ · palco lo stesso ai due estremi.*

| tratto (mediane, ms) | **C** software | **B** hardware | differenza |
|---|---|---|---|
| 1 disegno → cattura (Mutter) | 16,664 | 16,649 | **−0,02** |
| 2 cattura → primo byte (**codifica** + filo) | 39,822 | **40,659** | **+0,84** |
| 3 il filo | 0,255 | 0,260 | +0,01 |
| 4 stream → `decode()` | 0,065 | 0,065 | 0,00 |
| 5 la decodifica | 6,315 | 6,315 | **0,00** |
| 6 il disegno | 9,105 | 9,155 | +0,05 |
| **7 TOTALE** | **72,397** | **73,677** | ⛔ **+1,28** |
| fotogrammi al secondo | 21,21 | 20,62 | −0,59 |

⇒ ⭐⭐ **Il binario con la codifica hardware, quando la sessione negozia AV1, non migliora niente:
peggiora di 1,3 ms.** Ed è **giusto così** — e la ragione è il pezzo seguente.

> ### ⛔⛔⛔ E QUI IL MIO STESSO LETTORE MI HA MENTITO, e l'ho corretto
>
> Il banco ha stampato: *«⭐ **renderD128** aperto/i dal prodotto ⇒ la codifica passa
> dall'HARDWARE»*. ⛔ **È falso**, e nello stesso riquadro c'era la prova:
>
> ```
> SERVER · nodo di rendering: ⭐ renderD128 aperto/i dal prodotto
> SERVER · PRIMO fotogramma codificato: codec 2, «av01.0.09M.10», … codifica 100276 us · AV1
> ```
>
> ⇒ Il nodo DRM è **aperto** e il codec è **AV1** — che su questa macchina **in hardware non
> esiste** (`av1_vaapi` esce **218**, misurato dalla corsia B). ⛔ **Un descrittore aperto dice che
> il contesto VA-API esiste, non che i fotogrammi ci passino.**
>
> ⭐ **Era una DEDUZIONE travestita da misura** — la forma d'errore che questa corsia è nata per
> togliere agli altri, rimessa dentro da me. ⇒ Curata: il banco adesso consegna il nodo **e** il
> codec, e il verdetto si fa **sui due insieme**:
> *«hardware» = nodo aperto **E** codec che l'hardware sa fare.*
> Riletti così, tutt'e due i giri dicono **⛔ IN SOFTWARE**, ed è vero.

⇒ ⛔⛔ **E questa è esattamente la trappola che il coordinatore temeva, misurata**: chi avesse
acceso l'albero di B così com'era consegnato — con la sua pagina vecchia — avrebbe visto
`renderD128` aperto, avrebbe letto **+1,3 ms**, e avrebbe scritto *«la codifica in hardware non
serve a niente»*. ⭐ **Il codec è il cancello, non il binario.**

---

## ⭐ QUEL CHE QUESTI TRE GIRI DIMOSTRANO DAVVERO

| | |
|---|---|
| ⭐ **il banco è ripetibile** | due giri indipendenti, stessa scena: i tratti 1, 3, 4, **5** e 6 coincidono entro **0,05 ms** (il 5 a **zero**). ⇒ Le differenze sopra il decimo di ms sono reali, non rumore |
| ⭐ **il metro è tarato** | P1 su C: chiesti 25 → **+24,92**, chiesti 60 → **+60,00** |
| ⭐ **il numero del 13 agosto REGGE** | il tratto della codifica vale **39,8 ms su 72,4 = il 55 %** — misurato oggi, con un altro banco, un'altra pagina e il palco dichiarato |
| ⛔ **ma il bersaglio non è stato colpito** | perché il codificatore hardware **non ha mai ricevuto un fotogramma** |
| ⛔ **e il palco non era quello che credevamo** | tutt'e tre i giri, come tutti quelli del 13 agosto, sono **sul desktop dell'utente** |

---

## ⛔ IL PALCO — la decisione, e perché è l'opposto di quel che sembrava

*Deciso dal coordinatore la notte del 14, e va scritto perché la conclusione del 13 sembrava ovvia
e non lo era.*

Sembrava che la cura fosse **forzare `--ozone-platform=x11`**, cioè andare davvero sull'Xvfb.
⛔ **Non si fa**, e la ragione è decisiva: **sul vero Xvfb non c'è GPU** ⇒ niente decodifica HEVC in
hardware sul client ⇒ **la sessione ripiegherebbe su AV1 e il codificatore hardware non verrebbe mai
esercitato**. *Cureremmo la scena distruggendo la misura.*

⭐ **E il difetto non era «misuriamo sul desktop»**: il client vero del prodotto gira su un desktop
vero con una GPU vera, quindi misurare lì è **più** rappresentativo, non meno. Il difetto era:

> ⛔ **misurare sul desktop dell'utente dicendo di essere su uno schermo finto, e mentre l'utente ci
> sta lavorando sopra.**

⇒ La cura è quella già fatta: il palco **dichiarato e verificato dall'altro capo** (bandiere,
`screen`, `xlsclients`, webgl, nodo di rendering, codec) e messo fra i **campi portanti** confrontati
ai due estremi. ⭐ E la seconda metà stanotte è gratis: **l'utente non sta lavorando**, e la contesa
che ha sporcato i 74,58 del 13 agosto **non c'è**.

---

## ⛔ RICHIESTE AL COORDINATORE — fuori dal mio perimetro

| # | dove | che cosa |
|---|---|---|
| **0** | ⛔⛔⛔ **IL DISEGNO** — `src/pagina.html`, i due `drawImage` | ⭐ **il nuovo collo di bottiglia, e vale più di ogni altra cura rimasta**: **25,1 ms su 75,2** (il 33 %). Passando da AV1 a HEVC il disegno è salito da 9,1 a 29,2, e l'hardware ne ha recuperati solo 4. ⚠ L'ipotesi (il fotogramma decodificato in hardware vive sulla GPU e i `drawImage` pagano il trasferimento) è **una lettura, non una misura**: va misurata |
| ~~**1**~~ | ✅ `src/pagina.html`, le sonde | **CHIUSA**: con la pagina `b41e4f16` la sessione negozia HEVC, concede 1920×1080 e consegna fotogrammi |
| **2** | ⛔⛔ `/srv/src/03-B-src/` | l'albero della corsia B porta la **pagina vecchia** (`ec169e5d`). Chi lo accendesse così misurerebbe l'hardware **con la pagina che negozia AV1** — cioè col codificatore hardware **spento** — e concluderebbe che non serve a niente |
| **3** | ⚠ `banchi/03-solo.py` | tre falsi rossi, tutti della stessa famiglia: (a) `ps pcpu` è la **media dalla nascita**, non il carico di adesso — `[M]` un processo al «50 %» stava allo 0,0 % su 4 s; (b) `--json` **non accetta le porte proprie**, quindi sul server ogni banco è estraneo a sé stesso; (c) e nemmeno i **pid propri** dell'altra macchina. ⇒ Le curo io **nel banco**, ma la cura giusta sta nell'arbitro |
| **4** | ⚠ `src/figlio.c` | il prodotto **non scrive il nome del componente** di codifica (`libsvtav1`/`hevc_vaapi`): sta in `conf.componente` e non finisce in nessun registro. ⇒ Da fuori software e hardware si distinguono **solo** dal nodo DRM aperto. Una riga lo renderebbe una lettura diretta |
| **5** | ⚠ `03-b17-ritardo.py` (mio, ma è una decisione) | il banco **non passa `--ozone-platform`** ⇒ misura sul desktop dell'utente. ⛔ **Non l'ho toccato**, per ordine: spostare il palco fra il prima e il dopo distruggerebbe la sottrazione. **È il primo lavoro di chi riprende**, e va fatto **prima** del prossimo «prima» |

---

## 🧭 L'ORDINE IN CUI SI RIPRENDE — ⭐ riscritto la notte del 14, coi numeri in mano

| # | | perché in quest'ordine |
|---|---|---|
| **1** | ⛔⛔⛔ **il DISEGNO**: perché `drawImage` costa **28,0 ms** con HEVC e **9,1** con AV1 | è **il 36 % del numero** e nessuno lo stava guardando. ⚠ Vale più di tutto il resto messo insieme: la codifica in hardware ne costa ormai **5** |
| **1-bis** | ⚠ **due cure del BANCO, piccole e già identificate** | (a) `regime()` deve buttare **il transitorio della sessione**, non solo quello di ogni fetta — stanotte l'ho aggirato dichiarando il taglio; (b) `misura()` deve **depositare la riga anche se la stampa esplode**, o un'eccezione costa il verbale di registro **uscendo con lo stesso codice di un rosso legittimo** |
| **2** | ⛔ **il giro a CINQUE punti sull'albero del DEPOSITO** — `--ritardi 0,5,10,25,60` | ⭐ è **il prossimo giro**, e vale doppio: misura **la configurazione che l'utente giudica**, non una sua parente. Decide fra *«errore proporzionale del 14 %»* e *«ginocchio»*, con le previsioni **scritte prima** |
| **3** | ⚠ il resto del tratto 2 | in B vale **30,4 ms** di cui la codifica confessata è **~5** ⇒ ci sono **~25 ms** fra cattura e primo byte che **non sono codifica**, e non sono mai stati scomposti |
| **4** | ⚠ e solo dopo, il tetto | ⛔ oggi **SFORA**, e sforerebbe anche a codifica gratis |

⭐ **E quel che NON va rifatto**: il banco è certificato, i tre alberi sono sul server con le
impronte dichiarate, e i tre verbali esistono tutti — uno per giro, nessuno ha cancellato l'altro.

<details>
<summary>L'ordine scritto il 13 (superato dai fatti, tenuto per il verbale)</summary>

### 🧭 L'ORDINE IN CUI SI RIPRENDE — e il primo passo non è misurare

⛔ **Non si rimisura finché il muro n. 2 non è caduto**: un giro in più su AV1 non aggiunge niente
a quel che c'è già qui, e un giro su HEVC oggi consegna zero fotogrammi.

| # | | perché in quest'ordine |
|---|---|---|
| **1** | ⛔⛔ **la pagina**: HEVC deve dipingere nella sessione vera, e `video.misura_massima` non deve crollare per colpa sua | senza, **nessuna** misura del codificatore hardware è possibile |
| **2** | ⚠ **decidere il palco, e dichiararlo una volta per tutte** — Xvfb vero (`--ozone-platform=x11`, niente GPU) **oppure** desktop dell'utente (GPU vera, contesa vera) | ⛔ e **poi** rifare il «prima»: il numero di stanotte vale solo contro un «dopo» preso sullo stesso palco |
| **3** | ⭐ **il «prima» e il «dopo» di fila, nella stessa finestra esclusiva** | il banco adesso scrive il palco nel verbale e confronta i campi portanti ai due estremi: se qualcosa si sposta, lo dice |
| **4** | ⚠ e solo allora **E2 · E3 · E4** hanno un senso | i cinque tratti affiancati valgono se il tratto 2 è davvero cambiato |

⭐ **E il lavoro di stanotte non va rifatto**: il banco è pronto, certificato, e i tre alberi sul
server sono già lì con le impronte dichiarate. Quel che manca è **un fotogramma HEVC**.

</details>

---

## 🧹 LO STATO IN CUI LASCIO LA MACCHINA — ⭐ notte del 14

| | |
|---|---|
| prodotto · ponte · scena | **spenti**, *«nessun figlio MIO orfano»* |
| ⛔ **porte protette** | contate dopo l'ultimo giro: restano **solo** `7448 · 7501 · 7561`. **Non toccate** |
| ⛔⛔ **i verbali sono AL SICURO, e non era scontato** | stavano su `/tmp` di CHUWI, che e' **tmpfs**: un riavvio e le prove del numero della fase sparivano — ⛔ *esattamente il modo in cui il 13 agosto ne sono andati perduti tredici su quattordici*. ⇒ Copiati su **`/media/REMOTIX/tmp/03-b17/verbali-E/`** (disco vero, 1,7 TB liberi), e **verificati per impronta**: tutti e cinque identici byte per byte. ⚠ **Non nel deposito**: sono 12 MB, e in git non ci vanno |
| ⭐ **i cinque verbali** | `E2-A-software-hevc` (1,3 MB) · `E2-B-hardware-hevc` (2,7 MB) · `E-C-software-av1` (2,0 MB) · `E-B-hardware-stessapagina` (2,1 MB) — **uno per giro, nessuno ha cancellato l'altro** |
| gli alberi sul server | `03-b17-src` (A) · `03-b17-src-hw` (B) · `03-b17-src-av1` (C) — restano in piedi, con le impronte in questo rapporto |
| il banco | **certificato**: 54/54 → 53/54 (marca 1 volta) → 54/54, impronta `9d2648ce…` |
| il registro | tre righe nella **scheggia** `banchi/01-b12-registro-C.jsonl` — ⛔ non nel registro comune |

⛔ **Non ho committato**: lo fa il coordinatore.

<details>
<summary>Lo stato del 13 (per il verbale)</summary>

### LO STATO IN CUI LASCIO LA MACCHINA

| | |
|---|---|
| prodotto e ponte | **spenti**, *«nessun figlio MIO orfano»* |
| scena Wayland | spenta |
| ⛔ **porte protette** | **7448 · 7501 · 7561** contate prima e dopo **ogni** passo: presenti tutt'e tre, ⭐ **e nessun'altra 76xx accesa**. Non toccate |
| ⚠ **due `awk` miei** | erano rimasti al 99,7 % sul server: **uccisi**, e il carico è tornato sotto 1 prima di misurare |
| gli alberi sul server | `03-b17-src` (A, sw + pagina di oggi) · `03-b17-src-hw` (B, hw) · `03-b17-src-av1` (C, sw + pagina vecchia) — ⚠ **restano in piedi apposta**, con le impronte in questo rapporto |
| i verbali | ⭐ `/tmp/03-b17/verbali/verbale-E-C-software-av1.json` (2,04 MB) e `verbale-E-B-hardware-stessapagina.json` (2,06 MB) — **uno per giro, e nessuno ha cancellato l'altro** |

⛔ **Non ho committato**: lo fa il coordinatore.

---

</details>

## I file toccati

| file | che cosa |
|---|---|
| `banchi/03-b17-ritardo.py` | verbale per giro · palco dichiarato (bandiere, ozone, `screen`, `xlsclients`, webgl, codec, nodi DRM) · finestra esclusiva sulle due macchine · confronto del palco ai due estremi · il commento di `certifica()` · **la cura del «nodo aperto ⇒ hardware»** · 16 controlli nuovi |
| `banchi/03-b17-accendi.sh` | l'azione **`palco`**: legge i nodi DRM **da root** e consegna i denominatori |
| `banchi/03-b17-lancia.sh` | porta `03-solo.py` sul server · passa `D` (l'albero) e `GIRO` (il nome) · non passa più `--verbale` |
| ⭐ **e la notte del 14** | il riconoscimento dei **propri processi** sull'altra macchina (`--pid-file-la`) · il quarto ramo del verdetto sulla codifica (HEVC **in software**) · tre giri A/B/C con i verbali separati |
| ⭐⭐ **e in preparazione del giro a cinque punti** | ⛔ **il ponte si legge MENTRE ritarda** (`--verbale-ponte`, una lettura per ogni N, all'ultima mano) — prima lo leggevo a giro finito, cioè a ritardo zero, e non diceva niente · ⭐ **quando P1 è rosso il banco stampa DOVE va il surplus**, tratto per tratto e col ritmo a ogni N: *«se il ritmo NON cala, non è saturazione»* |
| `banchi/01-b12-registro-C.jsonl` | la **scheggia** della corsia: `03-b17` ri-certificato, con dentro le tre misure |
| `banchi/03-b17-esiti.jsonl` | le righe depositate dai giri (misure e certificazioni) |

---

## ⛔⛔⛔ E IL GIRO CHE HA PRODOTTO IL NUMERO È MORTO CON UN'ECCEZIONE — mia

*Trovato **dopo** aver consegnato i numeri, controllando una cosa banale: **che numero è finito nel
registro degli esiti?** ⇒ **Nessuno.** La riga non c'era.*

```
File "banchi/03-b17-ritardo.py", line 1804, in verdetto
    if not d or not d.get("n"):
AttributeError: 'float' object has no attribute 'get'
```

⛔ **Nel blocco nuovo della diagnosi di P1 avevo riusato il nome `d`** — che in `stampa_verdetto()`
è **la distribuzione** — sovrascrivendola con un float.

⛔⛔ **E la parte grave non è l'errore: è come si è nascosto.** L'eccezione ha fatto uscire Python
con **codice 1** — ⭐ **esattamente lo stesso codice di un P1 rosso legittimo**. ⇒ Il giro
*sembrava* finito bene con un rosso atteso, e invece:

| | |
|---|---|
| ⛔ **la riga di misura non è stata depositata** | il registro non aveva **nessuna** traccia del numero della fase |
| ⛔ **e nessuno se ne sarebbe accorto** | uscita 1 su un giro con P1 rosso è **quel che ci si aspetta** |

⇒ ⛔ **È la trappola n.4 del catalogo** — *«`RuntimeError` fa uscire Python con 1, lo STESSO codice
di un caso rosso»* — **rifatta da chi la stava curando**, e nello stesso blocco scritto per
diagnosticare P1.

⭐ **Quel che salva i numeri**: il verbale era **già scritto** quando l'eccezione è scattata (§7-ter
lo scrive prima di stampare) e **tutto quel che ho consegnato viene dal verbale**, non dalla stampa.
⇒ I numeri sono intatti e riverificabili.

| la cura | |
|---|---|
| la variabile si chiama **`salto`** | e il commento dice perché, con la data |
| `--verdetto` sul verbale D | ⭐ **arriva in fondo**, uscita **1** — che qui è il P1 rosso **vero** |
| la riga mancante | ⭐ **depositata a mano**, marcata `MISURA — ⛔ riga DEPOSITATA A MANO`, con dentro il motivo, il numero del giro intero **e** quello a regime |

⚠ **E resta un difetto che non ho curato, perché non ho potuto provarlo**: `misura()` non ha un
`try/except` attorno alla stampa, quindi **un'eccezione dopo il verbale costa sempre la riga di
registro**. ⇒ La cura è avvolgere `stampa_verdetto()` e depositare comunque; ma un giro per provarla
stanotte non c'è più, e **un banco curato che nessuno ha visto arrossire non è curato**.

---

## ⛔ CHE COSA NON HA FUNZIONATO — la notte del 14

| | |
|---|---|
| ⛔⛔⛔ **il giro del numero è morto con un'eccezione MIA, mascherata da rosso legittimo** | uscita **1**, come un P1 rosso ⇒ **la riga di registro non è stata depositata e nessuno se ne sarebbe accorto**. Trovato controllando *«che numero è finito nel registro?»*. ⭐ I numeri sono salvi (vengono dal verbale, scritto prima), la variabile è stata rinominata, la riga depositata a mano |
| ⛔⛔ **P1 rosso su B** | il controllo che valida il metro non torna proprio sul giro che produce il numero. ⛔ **Il numero si consegna con la riserva, non senza**. ⭐ Sul **deposito** invece P1 torna **verde** a regime |
| ⛔⛔ **e ho scagionato il ponte con un dato preso nella condizione sbagliata** | avevo letto il suo verbale **a giro finito**, cioè con `ritardo_ms = 0`: uno scarto di consegna nullo **a ritardo zero** non dice niente su come consegna quando ritarda. ⇒ **Il ponte NON è scagionato.** Curato: adesso il banco lo legge **mentre ritarda**, una volta per ogni N |
| ⛔ **e la mia spiegazione di P1 era sbagliata** | dicevo *«saturazione a 30 fps»*. **Falso**, e si vedeva nei dati che avevo: il ritmo **non cala** (30,18 · 30,01 · 30,33). ⭐ La diagnosi vera — il surplus è **tutto nel tratto 2 e non nel tratto 3** — l'ho trovata **senza un giro nuovo**, e adesso **la stampa il banco** ogni volta che P1 è rosso |
| ⛔ **il banco si è rifiutato di misurare — due volte, e la seconda aveva ragione su di me** | vedeva **il proprio prodotto** come vicino affamato (67,8 % di CPU = x265 che codifica). Curato riconoscendo i **propri** pid dal **proprio** pidfile, e solo quelli |
| ⛔ **una mia riga di verdetto era ambigua su A** | diceva *«codec e nodo non concordano»* per uno stato **perfettamente coerente** (HEVC in software non apre nodi DRM). ⇒ Mancava il quarto ramo; aggiunto **dopo** le misure, per non spostare il metro nel mezzo |
| ⚠ **la finestra «non ha retto» alla fine di A** | ma il carico era **mio**: `03-solo.py` filtra i vicini per pid, **non il carico medio** ⇒ il criterio «carico > 1» scatta sul carico che il banco stesso produce |
| ⚠ **l'uscita del banco resta bufferata** | durante un giro da 13 minuti non si vede una riga finché non finisce: chi sorveglia è cieco. Non falsa nulla, ma va curato |

---

## ⛔ CHE COSA NON HA FUNZIONATO — la notte del 13

| | |
|---|---|
| ⛔⛔ **la configurazione A non esiste** | il «prima con la pagina di oggi» **non si può misurare**: con quella pagina la sessione consegna **zero fotogrammi**. ⇒ Il «prima» consegnato è **C** (pagina vecchia, AV1), e va confrontato solo con un «dopo» preso **sulla stessa pagina** |
| ⛔⛔ **il «dopo» vero non è misurabile** | il codificatore HEVC in hardware **non riceve un fotogramma** finché la pagina non sa negoziare HEVC con una tela sana. Non è un ritardo di consegna: è un muro a monte |
| ⛔ **due `awk` miei impazziti sul server** | una prima versione del lettore del palco accumulava 17 MB in una variabile. Il `timeout` **locale** su `ssh` **non uccide il comando remoto**: sono rimasti al 99,7 % finché l'arbitro non li ha visti. ⚠ Lezione: chi lancia comandi remoti li deve **contare**, non fidarsi del proprio timeout |
| ⛔ **il mio lettore del nodo DRM nasceva cieco** | da utente normale `ls /proc/<pid>/fd` dà *Permission denied* ⇒ avrebbe scritto **«software»** su un giro in hardware. Curato passando da root e portando **i denominatori** |
| ⛔ **e pescava un fossile** | il registro del prodotto è in **append**: la prima versione ha riportato il codec **di un'ora prima**. Curato ancorando all'accensione |
| ⚠ **l'uscita del banco è bufferata** | `print` senza flush: guardando il file durante il giro non si vede niente per minuti. Non ha falsato nulla, ma rende cieco chi sorveglia |

---

## 🎯 CHE COSA DICE QUESTA NOTTE ALLA FASE 3

| domanda del piano | risposta misurata |
|---|---|
| **E1** — l'anello con la codifica in hardware | ⭐ **75,23 ms** (n = 799), ⛔ con **P1 rosso** dichiarato |
| **E2** — i cinque tratti affiancati, non il totale | ⭐⭐ **gli altri quattro restano dove sono** (Mutter −0,01 · filo −0,07 · decodifica −0,72 · e il disegno **scende** di 4,15) ⇒ **l'architettura è assolta**: tolta la codifica, nulla di nascosto è emerso |
| **E3** — i fotogrammi accanto ai millisecondi | ⭐⭐ **14,53 → 30,18 al secondo**, dipinti **1 407 → 2 949**. ⛔ Senza questo numero, il −33 ms sembrerebbe metà della notizia: **il ritmo è l'altra metà** |
| **E4** — quanto vale il tratto della codifica | ⭐ **61,77 → 30,37 ms** nel tratto 2; e la confessione del prodotto: **114,5 → 4,9 ms** per la chiave |
| ⛔ **il tetto dei 50 ms** | **SFORA**, e sforerebbe anche togliendo tutta la codifica residua |

> ### ⛔⛔ E LA RIGA CHE LA FASE DEVE PORTARSI DIETRO
>
> *Il piano diceva: «39 ms sono la codifica, il pezzo grosso è aggredibile». **Era vero.** La
> codifica è stata aggredita e ha ceduto 31 ms.*
>
> ⛔ **Ma il totale non è sceso**, perché il codec che rende possibile l'hardware — HEVC — **sposta
> 16 ms sul disegno**. ⇒ **Il collo di bottiglia della fase 3 non è più la codifica: è il disegno**
> (25,1 ms su 75,2, il **33 %**), e nessuno lo stava guardando.
>
> ⭐ E si vede **solo** perché i tre giri esistono tutti e tre: con A e B soli si sarebbe letto
> «−33 ms, vittoria»; con C e B soli, «+2,8 ms, l'hardware non serve». **Sono tutt'e due sbagliate.**

---

## ⛔ CHE COSA RESTA `[?]`

| | |
|---|---|
| ⭐ ~~**il numero con la codifica in hardware**~~ | ✅ **MISURATO la notte del 14: 75,23 ms**, ⛔ con P1 rosso dichiarato accanto |
| ⛔ **quanto vale davvero il 75,23** | ⚠ `[?]` **la larghezza dell'errore**: il metro, su questo giro, non è tarato. ⭐ **Ma il surplus è localizzato** (tutto nel tratto 2, zero nel 3) e il ritmo non cala ⇒ resta `[?]` **la causa**, non più *dove*. Il giro a cinque punti la decide |
| ⛔ **il ponte è colpevole o innocente?** | ⚠ `[?]`, e il mio scagionamento era **nullo** (letto a ritardo zero). ⭐ Adesso il banco legge il ponte **mentre ritarda**: la risposta esce dal prossimo giro **senza lavoro in più** |
| ⛔⛔ **perché il DISEGNO costa 28 ms con HEVC e 9 con AV1** | `[?]`, ed è **il primo lavoro che resta**: **28,0 su 78,1 = il 36 %**, contro i **5 ms** che ormai costa la codifica |
| ⛔ **perché la copia di B ha P1 rosso e il deposito no** | `[?]`: sullo stesso hardware e con la stessa pagina, la copia sbaglia di +6,98 e +12,11 **anche a regime**, il deposito sta entro ±3. ⚠ Qualcosa è cambiato nel travaso, e **non sappiamo che cosa** |
| ⚠ **il transitorio d'avvio** | `[?]` **da dove venga**: mezzo giro a 130-165 ms prima di assestarsi a 78. ⛔ E il banco **non lo butta**: `regime()` scarta l'assestamento di ogni *fetta*, non quello della *sessione* |
| ⛔⛔ **i 74,58 / 74,576 del 13 agosto** | ⚠ vanno riletti con la riserva del palco: **presi sul desktop dell'utente**, con la sua contesa dentro. ⭐ Il valore di oggi (**72,40**) è preso **sullo stesso palco** ⇒ i due si confrontano fra loro, ⛔ ma nessuno dei due è «l'anello su un palco pulito» |
| ⚠ **quanto pesa il palco sul numero** | `[?]`: nessuno ha ancora misurato l'anello su un Xvfb vero (`--ozone-platform=x11`). ⚠ Là **non c'è GPU** ⇒ il numero cambierebbe, e non è detto in quale verso |
| ⚠ **il tratto 6 (il disegno)** | i **9,105 ms** sono un **minimo**: due terzi del disegno sono **rimandati**, e finiscono nel pezzo cieco |
| ⚠ **P5** | ⭐ non è più `[?]`: è `[M]` che il fenomeno **non si presenta** — 0 visti **e** 0 dichiarati dal prodotto. Resta `[?]` che cosa farebbe l'anello su una rete che riordinasse davvero |
| ⚠ **E4 — quanto vale il tratto della codifica in hardware** | ⭐ **misurato la notte del 14** — vedi la tabella `A → B` |
| ⛔ **`[?]` perché il DISEGNO triplichi con HEVC** | 9,11 → **29,25 ms** passando da AV1 a HEVC in software. L'ipotesi (il fotogramma decodificato in hardware vive sulla GPU e i `drawImage` pagano il trasferimento) è **una lettura, non una misura**. ⭐ È il primo posto dove guardare dopo la codifica: **20 ms sono più di quanto valga qualunque altra cura rimasta** |
