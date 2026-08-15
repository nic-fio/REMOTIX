# Fase 6 — La tela e la vista

*Aperta e chiusa nella stessa notte: **15 agosto 2026**, dalle 00:00 alle 07:40.*

> ## ⛔ LA RISERVA DI FORMA, IN TESTA, PERCHÉ NON SI PERDA
>
> `fasi/README.md` dice: *«il documento si apre quando si apre la fase, non quando si chiude. Un
> documento scritto dopo è un resoconto, e in un resoconto le misure si **ricordano** invece di
> essere **registrate**.»* ⛔ **Questo documento è scritto alla chiusura**, e la regola è stata
> violata: la fase non è stata aperta, è **successa** dentro il seguito della fase 4.
>
> ⚠ E va detto perché è successo, invece di scusarsene: `DECISIONI.md` §5.0-sexies aveva reso la
> tela **la cura di quattro sintomi del mouse e del video**, non un lavoro di geometria. Il mandato
> della notte (`F4-IN-12`) chiedeva un pezzo solo — `figli_ritela()` → `cattura_ridimensiona()` — e
> quel pezzo *è* metà della fase 6.
>
> ⭐ **Quel che salva le misure è che nessuna è ricordata**: ognuna viene da un registro del server
> o da un giro di banco, con la sua riga e la sua ora. Dove il numero non c'è, qui sotto c'è scritto
> `[?]` e non un ricordo.

---

## Che cosa doveva produrre

`PIANO.md` §«Fase 6 — La tela e la vista»: **la tela concordata all'attacco, la vista che riscala,
il riattacco a misura diversa.**

**Che cosa l'utente vede e giudica**: il desktop remoto riempie la finestra del browser, **senza
bande nere e senza testo sfocato**, e ritrova la sua misura quando si riattacca da un'altra
macchina.

---

## Il banco

⛔ **Scritto DOPO la prima stesura del codice, non prima** — e va detto: la regola di §0.2 vuole il
banco per primo. Quel che ha retto al posto suo è stato il mandato **avversariale** a quattro agenti
(§«che cosa non ha funzionato»), che ha trovato dieci difetti prima che il banco esistesse.

| | |
|---|---|
| `banchi/04-b31-tela.c` | monta `rcp.c` **nudo**, con un palco finto che si può far rispondere in ritardo, concedere un'altra misura, o non rispondere affatto. **18 casi**, ciascuno con l'atteso dichiarato prima |
| `banchi/04-b31-certifica.sh` | ⭐ **il controllo positivo**: innesta **11 guasti** in una copia di `rcp.c` e pretende che diventino rossi **i casi attesi** — non «che diventi rosso qualcosa» |

⛔ **E il banco è stato corretto due volte dalla misura, non il contrario**: l'atteso di G1 diceva
dieci casi e ne ha accesi sei; G9 restava verde perché un **secondo** controllo mascherava il guasto
innestato nel primo. Tutt'e due scritti accanto al guasto, con la ragione.

⚠ **Quel che questo banco NON prova, dichiarato**: non prova che il compositore ridimensioni
(quello è `[M]` di `banchi/04-in8-misura.c`), non prova che i pixel siano giusti (qui non c'è un
pixel), non prova la pagina. Prova la sola cosa che sta in mezzo, e che nessun banco guardava: **che
a ogni `ADATTA_TELA` risponda esattamente un `TELA`, e che la tela in vigore non prenda mai un
valore che nessuno ha concesso.**

---

## Che cosa è stato sviluppato

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

## Le misure

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

⭐ **E la misura che non viene da noi**: GNOME *Impostazioni → Displays*, **dentro** la sessione
remota, dichiara **«Resolution 1264 × 800 (3:2)»** e **«Scale 100%»**. È il compositore che dice la
misura che gli abbiamo chiesto.

---

## ⛔ Che cosa NON ha funzionato

### I dieci difetti trovati refutando la cura appena scritta

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

### ⛔⛔ E il difetto che ha trovato l'UTENTE, non il banco

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

### ⛔ Il quarto di secondo su ogni clic, e il numero che stava nel registro da un giorno

Il ciclo del figlio aspettava un fotogramma fino a **250 ms**, e in quell'attesa non leggeva il
socket del padre. `[M]` 136 ms di mediana sui clic veri. ⭐ E la causa era stampata **una volta al
secondo** in una riga scritta per un'altra domanda: *«3 attese a vuoto»* = quattro giri al secondo =
250 ms per giro. È la seconda volta in due giorni che il registro aveva già il fatto
(`LEZIONI.md` §6.2-ter).

### Le tre cose che ho sbagliato di metodo, e che il banco ha corretto

- l'**atteso di G1** dichiarava dieci casi rossi e ne ha accesi sei;
- **G9 restava verde** perché un secondo controllo mascherava il guasto innestato nel primo;
- il **caso 18** non riproduceva la scena vera finché non ha avuto **due** sessioni: con una sola, il
  posto se lo riprendeva da sé e il difetto non compariva.

---

## Le decisioni prodotte

- `DECISIONI.md` **§5.0-sexies** — attuata per intero, con le misure della notte, le tre guardie
  chiuse e i quattro tempi (`RCP_TELA_ATTESA_MS`, `RCP_TELA_RICHIAMO_MS`, `TELA_FONDO_MS`,
  `RISVEGLIO_MS`);
- `DECISIONI.md` **§5.1** — vale **durante** la sessione, non all'attacco: l'inseguimento della
  finestra sta dietro `?adatta=segui`, spento di suo (I6);
- `SPECIFICHE.md` **§6.4** e `RCP.md` **§7.1** — corrette: *«mai come automatismo»* non è più vero
  all'attacco, e il perché è scritto con la data;
- `LEZIONI.md` **§7.5** (una deduzione al posto di un messaggio), **§6.2-bis** (un'attesa che
  protegge un anello è un ritardo per gli altri), **§6.2-ter** (il numero è già nel registro).

---

## Che cosa resta `[?]`

| | |
|---|---|
| ⏳ **la riga che manca a `RCP.md` §7.1** | che cosa fa il server quando il palco cambia misura **da sé**. Oggi lo richiama e non manda nessun `TELA` — funziona, ma è una regola del prodotto che l'arbitro non nomina |
| ⛔ **il banco del riattacco che BATTE UN TASTO dopo** | `PIANO.md` lo chiede per questa fase. `[M]` si è visto nel registro che `libei` ricrea i dispositivi al cambio di geometria e che `input.c` li riaggancia, ⛔ **e l'utente ha scritto in un terminale dopo un riattacco** — ma un banco che lo provi non c'è |
| ⛔ **il ripiego su KWin dichiarato nel registro** | `PIANO.md` lo chiede per questa fase e **non è verificabile**: KDE è la fase 10, e su questa macchina non c'è. Il percorso di codice esiste (`COMPOSITORE_INCAPACE`) ed è provato dal caso 11 del banco, **su un ospite finto** |
| `[?]` **il mezzo pixel del `margin: 0 auto`** | quando `clientWidth × devicePixelRatio` è dispari. ⭐ Giudizio dell'utente sul DeX: *«tutto perfetto»* ⇒ **non si presenta**, ma nessuno l'ha misurato |
| ⚠ **i 4 ms di ritardo medio aggiunto** | l'attesa di 8 ms è un **ripiego dichiarato**: la cura vera è un descrittore che la cattura scrive quando il fotogramma è pronto, nello stesso `poll()` del padre e di `libei` |
| ⚠ **il multi-monitor** | `SPECIFICHE.md` §6.5, fuori scopo come funzione |
| ⚠ **i banchi RCP/1 non esercitano la strada nuova** | `01-b3-cliente.py` e `01-b4-validatore.py` restano verdi perché il filo non è cambiato, ⛔ ma nessuno dei due manda un `ADATTA_TELA` |

---

## Il giudizio dell'utente

> **«Funziona. Niente barre nere, il desktop riempie perfettamente la finestra del browser e mouse e
> tastiera funzionano.»** — 15 agosto 2026, dal portatile Linux
>
> **«Sia su Linux sia su Android (DeX) è tutto perfetto. Ci sono i presupposti per chiudere la
> fase.»** — 15 agosto 2026, dopo la cura del ritardo

⭐ E prima, con l'immagine del desktop remoto a schermo intero: **«Questo è linux!»**
