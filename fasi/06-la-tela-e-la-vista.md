# Fase 6 — La tela e la vista

⭐ **Aperta il 16 agosto 2026, sera**, col suo documento e **prima di una riga di codice**
(`PIANO.md` §0.1). Il piano è `PIANO.md` §«Fase 6 — La tela e la vista»; il modello di questo
documento è `PIANO.md` §0.2.

> **La scena che l'utente giudicherà**: *«ridimensiona la finestra e l'immagine si adatta senza che
> le finestre dentro si muovano. Poi si riattacca da una macchina con un altro schermo e ritrova la
> sessione adattata — e ci scrive dentro.»*

---

## 0 · Che cosa deve produrre questa fase, e che cosa NON deve rifare

⛔ **Tre quarti del lavoro di questa fase sono già fatti e misurati**, nella **coda della fase 4**
(`FASI.md` §04-si-comanda, 15 agosto 2026). ⇒ Quelle quattro righe **si rimisurano, non si
rifanno**:

| | stato che arriva dalla fase 4 |
|---|---|
| la **tela concordata all'attacco** | ✅ `[M]` 1264×800 in una finestra 1265×800, scala **1,000** |
| il **riattacco a misura diversa** | ✅ `[M]` `SESSIONE` concede la tela che il palco ha già, **0** fotogrammi scartati |
| la **vista che riscala** | ✅ c'era dalla fase 2; la scala vale 1 quando le due tele combaciano |
| ~~il **ridimensionamento a caldo**~~ | ⛔ **USCITO dal prodotto il 17 agosto 2026** (`DECISIONI.md` §5.1-bis). Era `[M]` 6 ms su Mutter e **impossibile** su KWin ≤ 6.7.4: l'utente ha tolto l'eccezione invece di mantenerla |

⛔ **E quel che resta APERTO, che è il lavoro vero di questa fase:**

1. ⛔ **il banco del riattacco che BATTE UN TASTO e MUOVE IL PUNTATORE dopo** — `[M]` il 15 agosto
   si è visto nel registro che al cambio di geometria `libei` **ricrea** i dispositivi assoluti e
   che `input.c` li riaggancia, ⛔ **ma un banco che lo provi non c'è**. `PIANO.md` lo chiede con
   queste parole: *«è la forma "una prova verde col difetto vivo" esattamente dove si presenta»*;
2. ⛔ **la disposizione di tastiera rinegoziata al riattacco** (`SPECIFICHE.md` §7.3): su Mutter un
   cambio di keymap **distrugge e ricrea** il dispositivo tastiera, e il puntatore al dispositivo
   vecchio smette di funzionare **senza errore** `[R]` (`STUDI.md` §gnome §9);
3. ⛔ **l'ordine fra la nascita dei dispositivi e le applicazioni già aperte**: un cliente Wayland
   partito **prima** che i dispositivi di input esistano **non riceve niente** `[M]` 10 agosto —
   e al riattacco i dispositivi si distruggono e si ricreano **sotto applicazioni che nessuno
   riavvierà**;
4. ⛔ **il ripiego su KWin ≤ 6.7.4 DICHIARATO NEL REGISTRO** (`SPECIFICHE.md` §6.3): si verifica
   **che la riga ci sia**, non che «funzioni lo stesso». KDE è la fase 11 e su questa macchina non
   c'è: si prova sull'ospite finto, come il caso 11 di `banchi/04-b31`;
5. ⏳ **la riga che manca a `RCP.md` §7.1**: che cosa fa il server quando **il palco cambia misura
   da sé**, senza che nessun `ADATTA_TELA` gliel'abbia chiesto. Oggi il server richiama il palco e
   **non manda nessun `TELA`** — funziona, ma è una regola del prodotto che l'arbitro non nomina;
6. ⚠ **i banchi RCP/1 non esercitano la strada nuova**: `01-b3-cliente.py` e `01-b4-validatore.py`
   restano verdi perché il filo non è cambiato, ⛔ ma **nessuno dei due manda un `ADATTA_TELA`**;
7. `[?]` **le tre cose che nessuno ha misurato sui numeri del browser** (`SPECIFICHE.md` §6.1-bis):
   lo **zoom di pagina** (su Chrome `screen.width` non cambia con lo zoom — ma da quando la tela è
   la **finestra**, quel conto è ancora sbagliato?), l'**arrotondamento** che può produrre un lato
   **dispari** che `RCP.md` §4.5 rifiuta, e il **mezzo pixel** del `margin: 0 auto`;
> ### ⛔ E UN OTTAVO PUNTO È STATO TOLTO — *rilievo dell'utente, 16 agosto 2026*
>
> Questo elenco portava **il multi-monitor** (`SPECIFICHE.md` §6.5), con una sottofase sua — la
> **6.7**, «il multi-monitor parametrico» — che doveva verificare che l'implementazione restasse
> *«parametrica su N»*.
>
> ⛔ **L'utente l'ha fermata**: *«il multimonitor non è previsto dal progetto. Sei andato fuori
> strada»*. Ed è la lettura giusta di §6.5, che lo dichiara **fuori scopo come funzione**: un banco
> speso per una funzione che non si fa è processo che non serve.
>
> ⭐ **Quel che di quel mandato resta, e resta perché è la fase 6 e non il multi-monitor**: le
> **coordinate quando la scala non vale 1** (tela e vista diverse, `?adatta=no`, e l'istante del
> ridimensionamento). ⇒ Passato alla sottofase **6.5**, che possiede già `pagina.html` e le
> proporzioni di §6.2. ⚠ È lo stesso difetto che ha reso il mouse inutilizzabile sul DeX per due
> giorni: nasce da una scala data per scontata, e oggi non si vede perché la scala vale 1 per
> costruzione.

---

## 0-bis · ⛔ COME SI LAVORA IN QUESTA FASE — le regole per i sei banchi in parallelo

*Il lavoro è diviso in **sei sottofasi**, ciascuna affidata a un agente che ne fa **tutti e
quattro** i passi: **sviluppo → test con misure → debug → test di verifica con misure**. Il numero
non è sei per gusto: il vincolo che lega è **`SPECIFICHE.md` §5.1 — una sola sessione grafica per
utente**, e ogni sottofase che tocca un desktop vero se ne porta uno suo.*

> ### ⛔ DUE ERRORI DEL COORDINATORE, SCRITTI QUI PERCHÉ NON SI PERDANO — *16 agosto 2026, sera*
>
> | | |
> |---|---|
> | ⛔ **una sottofase è nata fuori strada** | la **6.7**, sul multi-monitor «parametrico su N». L'ha fermata l'utente: *«il multimonitor non è previsto dal progetto»*. ⇒ Sette agenti diventano **sei**, e la parte che resta (le coordinate quando la scala non vale 1) passa alla **6.5** |
> | ⛔⛔ **e quattro mandati sono partiti senza `LEZIONI.md` §1.15** | *«Su Xvfb `requestAnimationFrame` non gira MAI»*, `[M]` 13 agosto 2026 — e in **Blink** l'evento `resize` si consegna **dentro** il giro di rendering, quindi senza quadri **non arriva mai**. ⇒ Avevo mandato a misurare **il cammino che segue la finestra** su un palco dove quel cammino **non viene eseguito**, e il banco sarebbe stato **verde**. Corretto a caldo, con le tre cure di §1.15: si batte il quadro apposta · **si giudica prima il palco** (*«IL PALCO, NON IL PRODOTTO»*, e ci si ferma) · il limite si scrive **in testa al banco** |
>
> ⚠ **La causa è una sola, e vale più dei due errori**: i mandati citavano `LEZIONI.md`,
> `REVIEWER.md` e `STUDI.md` **prendendo le citazioni da altri documenti**, senza aprirli. Le
> citazioni reggevano tutte — ⛔ ma quel che non c'era in nessuna di esse, cioè §1.15, non poteva
> comparire. *Una citazione di seconda mano porta quel che qualcuno ha già trovato utile, e mai quel
> che non sapeva di cercare.*

### Le cinque regole dell'isolamento

| | |
|---|---|
| ⛔ **un utente e una porta propri** | chi accende un server lo accende **suo**: `--porta`, `--ban-file`, `--comando-socket`, `--certificati` propri. Senza, il ban di `RCP.md` §4.4-bis fatto scattare da un banco mette fuori uso **tutti** gli altri, perché partono dallo stesso indirizzo |
| ⛔ **`prova` e la 7700 NON SI TOCCANO** | sono il banco dell'**utente**, l'unico posto in cui oggi si vede il desktop vero. La ricetta per farsene uno è `banchi/04-b31-terreno.sh` (utente proprio · GNOME headless **senza** `--virtual-monitor` · gruppo `render`) |
| ⛔ **si possiedono dei file, e si toccano solo quelli** | la tabella delle sottofasi dice quali. Un file di prodotto che non è tuo **non si edita**: si riferisce il difetto e si va avanti |
| ⛔ **nessun agente scrive `.md` e nessuno fa `git`** | i documenti si scrivono alla fine, a codice fermo (rilievo **R12C**); il `git` a più mani si pesta l'indice. ⇒ ⛔ **e non si producono file di rapporto**: quel che una sottofase misura torna **in questo documento**, per mano del coordinatore |
| ⚠ **l'albero sulla macchina di prova è una COPIA** | la porti tu quando parti. Se un altro agente cura un file che tu non possiedi, la sua cura **non è nel tuo albero** — ed è voluto: l'integrazione si fa alla fine, in una verifica congiunta |

### Le porte e gli utenti — ⛔ presi, e da non toccare

```
7448 · 7501 · 7561 · 7571 · 7601 · 7691       di altri anelli: si CONTANO, non si toccano
7700   il prodotto vivo, utente `prova`       ⛔ è il banco dell'UTENTE
7711-7715  banco 04-b31, utente `provao1`
```

| sottofase | macchina | utente | porte | albero sul server |
|---|---|---|---|---|
| **6.1** il riattacco che comanda | NIC-OS | `provai6` | **7781-7785** | `06-i-src` |
| **6.2** la tastiera che rinasce | NIC-OS | `provat6` | **7721-7725** | `06-t-src` |
| **6.3** il palco che cambia misura | NIC-OS | `provap6` | **7731-7735** | `06-p-src` |
| **6.4** la tela sul filo | portatile | — | 7741-7745 *(locali)* | copia locale |
| **6.5** la pagina e i numeri del browser | portatile + NIC-OS | `provaw6` | **7751-7755** | `06-w-src` |
| **6.6** l'arbitro esercita la tela | NIC-OS | `prova2` | **7761-7765** | `06-a-src` / innesto `b2` |

### ⚠ Le misure di TEMPO, con cinque banchi accesi

⛔ Cinque sessioni grafiche e cinque codificatori sullo stesso iGPU **spostano i millisecondi**. ⇒
Ogni misura di tempo porta accanto il **carico** (`uptime`), e i numeri che contano — il
ridimensionamento a caldo, clic → fotogramma, l'accesso — **si ripetono a banchi fermi** prima di
essere dichiarati. Un numero preso sotto carico e non dichiarato tale è un numero falso.

### Le trappole già pagate, che non si ripagano

1. ⛔ **il figlio senza `--parlantina` tace in silenzio**: `registro_dettaglio()` di `figlio.c`
   finisce nel nulla e i rami sembrano «non scattati». *Una diagnostica che tace non è neutra:
   mente*;
2. ⛔ **l'orologio del silenzio ruba 30 secondi alle prove**: se fra il preparare e il provocare
   passano 30 s, `SPECIFICHE.md` §5.3 ha già rilasciato tutto e si misura un'altra cosa;
3. ⛔ **la pagina rilascia da sola** su `blur`, `visibilitychange` e `pagehide`
   (`cl_rilascia_tutto`): dal browser il server non ha quasi mai niente da rilasciare, e **si
   certifica la pagina credendo di certificare il server**. Per provare il server si sostituisce
   `window.cl_rilascia_tutto` con uno stub;
4. ⛔ **il pilota del browser non sa TENERE PREMUTO** un tasto: si usa `javascript_tool` con
   `window.dispatchEvent(new KeyboardEvent("keydown", {code:"Enter"}))`, e solo i tasti
   **non-lettera** si tengono giù;
5. ⛔ **ogni utente di prova va nel gruppo `render`** — senza, il codificatore ripiega in software
   **dichiarandolo**: `[M]` 100 ms per fotogramma invece di 4,8;
6. ⚠ **l'orologio della macchina di prova è indietro di DUE ORE** rispetto al portatile;
7. ⛔ **la parola d'ordine non passa mai dalla riga di comando** (difetto **D12**): file `0600`
   scritto con `printf`, `--parola-file`, e una `trap` che lo cancella;
8. ⛔ **mai una redirezione ATTORNO a `ssh` o a `enter.sh`**: la richiesta di `sudo` va sullo
   stderr e una redirezione la mangia — il comando resta appeso per sempre, in silenzio;
9. ⛔ **il testimone del desktop vero**: dentro la sessione grafica, un terminale con
   `while IFS= read -r _; do date +%s%N >> /tmp/testimone.txt; done` — ogni `Invio` che **arriva
   al desktop** scrive una riga in nanosecondi. Un desktop **vuoto** non testimonia niente.

### Le due strade per costruire

| domanda | strada |
|---|---|
| **«compila?»** — venti secondi | `bash src/costruisci-in-contenitore.sh` sul portatile (`podman` da utente) |
| **«gira?»** — solo sulla macchina di prova | `tar` dei sorgenti nel proprio albero, poi `bash /media/REMOTIX/enter.sh --root 'bash /srv/src/<albero>/src/costruisci.sh'` |

⛔ **Il binario del contenitore NON si copia sulla macchina di prova**: è legato a
ngtcp2/nghttp3 di `/usr/local` **dentro l'immagine**.

---

## 1 · Le sette sottofasi

*Ognuna fa i quattro passi: **sviluppo · test con misure · debug · test di verifica con misure**.
⭐ E ognuna parte da un **mandato avversariale**: «parti dall'ipotesi che quel che è scritto sia
falso, e cerca la prova». Il rifiuto del mandato è ammesso, purché motivato con uno scenario
concreto.*

| # | titolo | che cosa chiude | file di prodotto POSSEDUTI | banchi |
|---|---|---|---|---|
| **6.1** | **Il riattacco che comanda** | i punti **1** e **3** di §0: si stacca, si riattacca **a misura diversa**, e poi si **batte un tasto**, si **muove il puntatore** e si **clicca** — con un'applicazione **aperta prima**. Più la rimisura delle quattro righe della fase 4 | `src/input.c` · `src/input.h` | `06-b33-*` |
| **6.2** | **La tastiera che rinasce** | il punto **2**: `DISPOSIZIONE` (0x0009) al riattacco, la keymap che distrugge e ricrea il dispositivo, e il **carattere giusto** che arriva al testimone | `src/tastiera.c` · `src/tastiera.h` | `06-b34-*` |
| **6.3** | **Il palco che cambia misura** | la catena `figli_ritela()` → `cattura_ridimensiona()` sul **compositore vero**: ridimensionamenti ripetuti, i limiti di §4.5, e il caso **«il palco cambia da sé»** (punto 5, lato prodotto) | `src/figlio.c` · `.h` · `src/cattura.c` · `.h` · `src/mutter.c` · `.h` | `06-b35-*` |
| **6.4** | **La tela sul filo** | i punti **4** e **5** lato arbitro, su `rcp.c` **nudo** con palco finto: `COMPOSITORE_INCAPACE` **dichiarato nel registro**, il fondo di §7.1, `NON_ORA`, `MISURA_FUORI_LIMITI`, e ⛔ **le coordinate in volo** del secondo dopo `TELA(ADATTATA)` — che non ha mai provato nessuno | `src/rcp.c` · `src/rcp.h` (+ il gemello `banchi/rcp/`) | `06-b36-*`, estende `04-b31-tela.c` |
| **6.5** | **La pagina e i numeri del browser** | il punto **7**: zoom di pagina su due motori, arrotondamenti e lati dispari, il mezzo pixel del `margin: 0 auto`, la scala e `pixelated`, le bande di §6.2, `?adatta=no\|segui`, e la **voce spenta** su `COMPOSITORE_INCAPACE` | `src/pagina.html` | `06-b37-*` |
| **6.6** | **L'arbitro esercita la tela** | il punto **6**: il cliente di prova manda `ADATTA_TELA` e `VISTA`, e il validatore **sa accusare** un `TELA` mancante o non sollecitato — certificato con registrazioni guaste, ciascuna accusata sul byte dichiarato prima | *nessuno* — solo banchi | `01-b3-cliente.py`, `01-b4-validatore.py`, `01-b4-registrazioni.py`, `06-b38-*` |
| ~~6.7~~ | ~~il multi-monitor parametrico~~ | ⛔ **tolta dall'utente il 16 agosto 2026** — vedi il riquadro in §0 | — | — |

⛔ **E un terzo momento che questa fase NON ha ancora**: `PIANO.md` §0.4 vuole il revisore **in tre
momenti**, e il primo è **sul banco, prima del prodotto** — *«il banco è il primo imputato: un
difetto nel banco non lo trova niente, perché dà fiducia»* (`REVIEWER.md` §1). Qui i sei agenti
scrivono il proprio banco e lo certificano **da soli** (col guasto innestato, che è la parte che
regge). ⏳ La revisione avversariale **ristretta ai sei banchi nuovi** si propone all'utente quando i
rapporti arrivano: quel che sopravvive a questa fase sono i banchi, non le misure.

---

## 2 · Il banco

*Sei banchi nuovi, uno per sottofase, ciascuno **certificato dal suo autore nello stesso giro** con
guasti innestati in una **copia** — la regola nata l'11 agosto (*«chi scrive un banco lo certifica
nello stesso giro, o il conto non cala mai»*).*

| banco | che cosa monta | casi | il controllo positivo |
|---|---|---|---|
| `06-b33-*` (6.1) | terreno `provai6`/7781 · **testimone Wayland** e `gnome-terminal` **aperti prima** dello stacco · cliente che stacca, riattacca a misura diversa e **solo allora** batte, punta e clicca | 7 | **5 guasti** in copia di `input.c`: G2→C2 · G3→R1,R2 · G4→C6 · G5→C3,C4 · ⭐ **G1 non accende niente**, e vedi §5 |
| `06-b34-*` (6.2) | terreno `provat6`/7721 · ⭐ **l'atteso lo calcola il prodotto** (`tastiera_posizioni_per()` chiamata da fuori) · testimone che registra **il carattere**, non il conteggio | 6 | **2 guasti**: «la keymap si legge una volta sola» → rosso sul caso dichiarato · «i tasti se ne vanno col dispositivo» → ⛔ **verde lo stesso**, e vedi §5 |
| `06-b35-*` (6.3) | terreno `provap6`/7731 · scena che si muove a **50 ms** · cliente che manda `ADATTA_TELA` e conta i `TELA` | 5 giri | **5 guasti su 5** confermati, ⭐ **compreso uno dichiarato VERDE prima del giro** (G4) e la ragione per cui lo è |
| `06-b36-*` (6.4) | `rcp.c` **nudo** con palco finto **più** il canale di input e **il registro catturato** — la metà che `04-b31` non guarda | **23** | **19 guasti su 19**, ciascuno rosso **nel caso dichiarato prima** |
| `06-b37-*` (6.5) | raccoglitore HTTP con sonda dentro la pagina, **sui due motori** (niente CDP, che è solo Chrome) · verità esterna `xwininfo` · verdetti **sui pixel** (`ffmpeg x11grab`) | 7 scene | lo zoom verificato su `devicePixelRatio` **e non sul tasto premuto**; ogni zero col suo denominatore (20 punti · 2 523 colonne · 4 resize) |
| `06-b38-*` (6.6) | il cliente di prova e **l'arbitro** che esercitano la tela; mutazioni dell'arbitro stesso | **49** registrazioni | **49 accusate sul byte dichiarato prima** · 4 esiti coperti · **19 mutazioni su 19** viste |

⭐ **E due banchi vecchi sono stati riparati, non solo estesi**:

| | |
|---|---|
| ⛔ `04-b31-certifica.sh` | **l'ancora di G8 era scaduta**: il 16 agosto è nata `rcp_tela_rimanda()` fra le due funzioni che l'ancora nominava, e da allora **il più grave dei dodici guasti non si innestava più**. Il certificatore lo diceva (`??`) e nessuno lo lanciava. ⇒ Di nuovo **12 su 12** |
| ⛔⛔ `01-b3-cliente.py` ↔ `01-b4-validatore.py` | il cliente scriveva `RCPREG 0x00 0x01`, l'arbitro pretendeva la `0x02`: **dal 12 agosto ogni traccia di B3 usciva «registrazione rotta»** e le cinque verifiche di `01-b3-lancia.sh` fallivano. ⭐ **Nessuno dei due file era rotto da solo: il difetto stava fra i due** |

## 3 · Che cosa è stato sviluppato

⛔ **Nove cure di prodotto, e nessuna era in programma**: questa fase doveva **rimisurare** tre
quarti di lavoro già fatto, e ha trovato nove difetti veri sotto quel lavoro.

| file | che cosa, e chi |
|---|---|
| `src/rcp.c` · `.h` (6.4) | ⛔ **`VISTA` (`0x0008`) cadeva nel `default`**: un client conforme che dichiara di aver ridimensionato **perdeva la sessione** — alla lettera il sintomo che il rilievo R1.17 esiste per rendere impossibile. Ora c'è `case T_VISTA` (~4950), che convalida, tiene e scrive, **senza toccare la tela né il codificatore** · `ADATTA_TELA` di **lunghezza falsa** girava il ridimensionamento al palco **prima** di congedare (`misura_campi()`, R9.4 riaperto) · il palco richiamato alla tela **vecchia** mentre una richiesta era **in volo** (`tela_richiama_il_palco()`, ~2847) · il secondo di grazia che si apriva **con data zero** · la vista dell'`ATTACCA` letta e buttata, ora tenuta (`rcp_vista()`) e lo zero rifiutato |
| `src/figlio.c` (6.3) | ⛔ `GIA_COSI` col formato non ancora negoziato rispondeva **`TELA(RIFIUTATA, NON_ORA)` su una sessione sana** (`:3973-4032`): `cattura_misura_negoziata()` torna `FALSE` **senza scrivere nulla**, e per `rispondi_tela()` lo zero vuol dire «non ce l'ho fatta» · ⭐ **`input_rilascia_tutto()` prima di `cattura_ridimensiona()`** (`:3964`), la cura chiesta dalla 6.1 |
| `src/input.c` (6.1) | ⛔ il difetto **dichiarato invece che silenzioso**: `segna_orfani()` (`:630-648`) scrive **nell'istante in cui il danno si produce**; un rilascio che Mutter ingoia **non conta più come partito** (torna −1, `:256-336`); `input_rilascia_tutto()` separa «rilasciati» da «**non rilasciabili**», che prima finivano nello stesso numero **e lo assolvevano**; `input_orfani()` per il banco. ⛔ E il commento che diceva *«al ricambio si rilascia sul dispositivo nuovo, che è l'unico posto dove il rilascio arriva»* è stato **smentito e riscritto** |
| `src/pagina.html` (6.5) | ⛔⛔ **`Math.round` → `Math.floor`** in `misura_vista()` (`:1450`): a `devicePixelRatio` **non intero** il prodotto `clientWidth × dpr` chiedeva **un pixel che non esiste** ⇒ tela più larga della finestra ⇒ barra di scorrimento ⇒ −22 px di altezza ⇒ **scala 0,9651** ⇒ `auto` ⇒ **testo interpolato** · la voce «adatta il desktop» adesso **si spegne davvero** dopo `COMPOSITORE_INCAPACE` (`:2823, 3581, 3587, 3727`), dove prima ne partiva una a ogni ridimensionamento · la ripetizione della richiesta vale **solo per `NON_ORA`** (`:3784`) |
| `banchi/rcp/` | il gemello tenuto **identico byte per byte**, verificato con `cmp` |

⏳ **E una decisione dell'utente in corso di attuazione** (sottofase 6.2, secondo giro):
`DECISIONI.md` §5-bis.7 — **la disposizione di tastiera la comanda il client**.

## 4 · Le misure

*Riempito strada facendo. Ogni riga: che cosa · la scena · l'atteso dichiarato PRIMA · il misurato ·
la data e l'ora · il carico della macchina.*

### ⭐⭐ 4.1 · IL TERZO CLIENT: WINDOWS — e l'ha provato l'utente, il 16 agosto 2026

> **«Ho fatto un test con Windows: anche in questo caso funziona tutto e con performance
> eccellenti.»** — l'utente, 16 agosto 2026, sera, sul prodotto vivo (porta 7700)
>
> ## ✅ **«Il test su Windows lo dichiaro superato al 100 %.»** — l'utente, 16 agosto 2026
>
> ⛔ *Non si scrive un verdetto che l'utente non ha dato: questa è la sua frase, con la data. Ed è
> un giudizio, cioè il metro di **I8** — «il metro è quel che l'utente vede, non il numero che esce
> dal banco».*
>
> ## ⭐⭐ E SU CHE FERRO — *«ricordiamoci sempre che otteniamo performance eccellenti su una Intel integrata»*
>
> *L'utente, 16 agosto 2026, subito dopo il giudizio. ⛔ E non è un complimento al ferro: è la
> **qualificazione della misura**, e senza di essa il numero non dice quanto vale.*
>
> `[M]` La scheda è la **Intel UHD 730** (`i915`, `0000:00:02.0`, `renderD128`) — un'integrata da
> ufficio. ⛔ La **Radeon RX 6800** della stessa macchina è **esclusa apposta** con una regola udev
> (`DECISIONI.md` §4.6-ter e §4.6-quinquies), per la regola di metodo che l'utente ha posto il 15
> agosto: *«i test vanno fatti sulla GPU integrata, altrimenti "trucchiamo" il gioco. La solidità
> del sistema la si vede su GPU poco potenti»*.
>
> ⇒ ⭐ **Da qui in avanti, in questo progetto, un numero di prestazione si riferisce insieme al
> ferro su cui è stato preso.** Tre sistemi client — Linux, Android/DeX e adesso Windows — giudicati
> «tutto perfetto» / «eccellenti», e dietro c'è una UHD 730.

⛔ **È un sistema operativo cliente che non era mai stato provato**: fino a stasera i client misurati
erano il portatile **Linux** e **Android/DeX**. `SPECIFICHE.md` §11.5 dichiara i **motori** (Blink ·
Gecko · WebKit) e non i sistemi: ⏳ la riga su Windows va aggiunta alla chiusura della fase.

⭐ **E la misura non è la sua frase: è il registro del server**, `[M]` 16 agosto 2026, ore 20:43
(ora della macchina di prova, indietro di due ore):

| | |
|---|---|
| il tetto del decodificatore dichiarato dal client | `video.misura_massima=3840x2160` |
| la sessione | `tela=2540x868 vista=2541x869 disposizione=it`, da `[192.168.0.21]` |
| l'invariante **I2** | *««prova» è già servito dal figlio pid 588775: NON ne nasce un secondo»* — il palco è lo stesso perché è della **sessione** (I4) |
| il flusso | `3829 fotogrammi consegnati (10 chiavi), 0 guasti`, codec 1, 60/s chiesti; `1197 spediti, 7 abbandonati` |

⛔⛔ **E il fatto che vale per questa fase: la sua finestra era DISPARI su tutt'e due i lati —
2541×869 — e la tela concessa è 2540×868**, troncata in giù di un pixel per lato. ⇒ Le due `[?]` di
`SPECIFICHE.md` §6.1-bis (l'arrotondamento che produce un lato dispari · **il mezzo pixel del
`margin: 0 auto`**) si sono presentate **insieme, su un utente vero**, e non hanno prodotto nessun
sintomo visibile. ⚠ *«Non ha visto niente» non è una misura*: la misura è carico della sottofase
**6.5**, che adesso sa **quale numero** riprodurre.

### ⭐⭐ 4.1-bis · E la scala di quel PC è il **125 %** — il primo `devicePixelRatio` NON INTERO della storia del progetto

*Dichiarata dall'utente il 16 agosto 2026. Fino a stasera ogni misura di questo progetto — Linux e
Android/DeX — era stata presa con un fattore **intero**.*

⇒ Il caso è completamente determinato, e `[R]` la lettura di `src/pagina.html` (`cornice()`, ~1889)
spiega **perché regge**:

| | |
|---|---|
| dpr | **1,25** ⇒ finestra `2541×869` fisici = `2032,8 × 695,2` CSS |
| la scala di disegno | `s = min(2541/2540, 869/868, **1**)` ⇒ ⭐ **vince il terzo termine: `s` vale esattamente 1** ⇒ `image-rendering: pixelated` **acceso**, nessun ricampionamento ⇒ **il testo resta nitido** |
| la griglia | `2540 / 1,25 = 2032` px CSS **esatti** ⇒ la tela cade sulla griglia dei pixel del dispositivo, senza frazioni |
| ⛔ il residuo | `2032,8 − 2032 = 0,8` px CSS divisi da `margin: 0 auto` ⇒ **0,4 px CSS per lato = mezzo pixel FISICO** |

⇒ ⭐ **La `[?]` del mezzo pixel non è più ipotetica: era la configurazione dell'utente, e l'utente ha
giudicato.** Con **I8** in mano quella `[?]` è **chiusa dal giudizio**. ⚠ La misura sui pixel resta
in carico alla **6.5**, e adesso risponde a un'altra domanda — non *«va bene?»*, che è deciso, ma
***«perché va bene»*** — che è quel che impedisce di romperlo domani senza accorgersene.

⏳ Resta non misurato il **150 %** (dove il terzo termine del `min` potrebbe non salvare più) e
qualunque dpr non intero **con la finestra pari**.

### 4.2 · Le quattro righe della fase 4, RIMISURATE sotto questa fase

⚠ **Tutte sotto carico** (load 0,2-2,1, fino a cinque banchi accesi insieme): ⛔ vanno **ripetute a
banchi fermi** prima di diventare i numeri della fase.

| che cosa | atteso *dichiarato prima* | `[M]` misurato | chi |
|---|---|---|---|
| tela concordata all'attacco | la misura chiesta, lati pari | **1264×800**, tre giri su tre | 6.1 |
| riattacco a misura diversa | `SESSIONE` concede **quella del palco** (I4) | **1264×800** + riga `RIPIEGO DICHIARATO (§4.5)` | 6.1 |
| fotogrammi scartati per misura | **0** | **0** in tutti i giri di tutte le sottofasi | 6.1 · 6.3 |
| ridimensionamento a caldo | ~6 ms (`[M]` 15 ago) | **5 ms** · **4 ms** di mediana su 9 cambi (3-13) | 6.1 · 6.3 |
| `SESSIONE` → primo fotogramma, palco **da montare** | ~311 ms (`[M]` 15 ago) | **335 ms** | 6.3 |
| ⭐ idem, palco **già in piedi** (I4) | — | **11 · 13 · 17 · 24 · 28 · 37 · 106 ms** | 6.3 |
| giro intero `ADATTA_TELA`→`TELA` lato server | — | **40 ms** (31-60); Mutter ne prende **32** | 6.3 |
| scala del **monitor** (lato server) | 1,000 | **1,000** su «Meta-0», e la riga si scrive **anche quando è buona** | 6.1 |
| ⛔ scala di **disegno** (lato pagina) | 1,000 e `pixelated` | **1,000** sui pixel (986 su 986) — ⚠ e vedi §4.3 | 6.5 |

### 4.3 · ⭐⭐ La pagina, i pixel e i numeri del browser — le tre `[?]` di §6.1-bis, chiuse

| `[?]` di `SPECIFICHE.md` §6.1-bis | esito | `[M]` |
|---|---|---|
| **lo zoom di pagina falsa la tela** | ⭐ **CHIUSA — non falsa più** | stessa tela chiesta a **100 · 150 · 50 %**, su Chrome 151 e Firefox 140esr, 21 larghezze, scarto **2 px**. ⛔ Ma la frase era falsa **per un'altra ragione**: non lo zoom, l'**arrotondamento** |
| **l'arrotondamento può produrre un lato dispari** | ⭐ **CHIUSA, con un difetto trovato e curato** | ⛔ a `dpr 1,5`: **4 larghezze su 12** (Chrome) e **2 su 12** (Firefox) chiedevano una tela **più larga della finestra** ⇒ scala **0,9651**, `auto`, testo interpolato, e in Firefox **una colonna del desktop tagliata**. ⇒ Dopo la cura (`Math.floor`): **0 su 48** e **0 su 36** |
| **il mezzo pixel del `margin: 0 auto`** | ⭐ **CHIUSA** | **esiste** (`rect.left` = **0,500 px fisici**, riprodotto nella configurazione esatta dell'utente) e ⭐ **non arriva ai pixel**: **0 colonne grigie su 2 523** — il motore aggancia alla griglia. Resta `[?]` **solo su GPU vera e su DeX** |

⭐ **Il caso dell'utente Windows, riprodotto in laboratorio**: `dpr 1,25`, finestra `2559×977`, vista
`2541×869`, tela `2540×868` ⇒ **s = 1,000000** (i rapporti valgono 1,000394 e 1,001152: ⛔ **a
tenere la scala è il tappo del `Math.min`, non i rapporti**), `pixelated`, disegno **2540 px**,
**0 colonne grigie su 2 523**.
⇒ ⭐ **Il numero di guardia della fase**: *se `image-rendering` si legge `auto`, il testo è tornato
interpolato*.

| e le altre scene della pagina | `[M]` |
|---|---|
| «si impagina, non si stira» (§6.2) | scarto di proporzione **0,00-0,07 %**; bande **nere e fuori dal buffer**; a scala 0,70 il prezzo del non-1 si vede: **52,5 %** (Chrome) e **29,7 %** (FF) di colonne sfumate |
| ⭐ **le coordinate a scala ≠ 1** | **20 punti su due motori, scarto peggiore 1 px** (solo Firefox, angolo basso-destro a s=0,707); col ridimensionamento **0 px dopo l'assestamento**, ⚠ e un transitorio di **97 px** mentre l'immagine cambia misura sotto il dito |
| i tre modi di `?adatta=` | `no` **0** · spento di suo **0** · `segui` **4 su 4**, con i 4 `resize` arrivati in tutti e tre — ⇒ **I6 rispettata** |
| la voce spenta su `COMPOSITORE_INCAPACE` | ⛔ prima: **non fingeva mai il successo, ma non si spegneva** (5 `ADATTA_TELA` dopo il rifiuto) ⇒ dopo la cura **0 e 0**, guardia attiva 4/4 |

### 4.4 · La tela sul filo, e l'arbitro

| | `[M]` |
|---|---|
| `06-b36` su `rcp.c` nudo | primo giro **15/20 · 5 rossi** ⇒ dopo le cure **23/23**, e **19 guasti su 19** |
| `04-b31`, il banco della fase 4 | **19/19** e **12/12** (era 11/12 per l'ancora scaduta) |
| l'arbitro contro il **prodotto** | **5 giri su 5 conformi**, 6 coppie `ADATTA_TELA`/`TELA` chiuse — `rcp.c` `8ce10fe5…`. ⭐ E il caso più promettente ha dato il contrario: `ADATTA_TELA(1281×800)` riceve **`TELA(ADATTATA, 1280×800)`** — il server arrotonda al pari **e lo dichiara nel campo** |
| il validatore certificato | **49 registrazioni su 49** accusate sul byte dichiarato prima · 4 esiti coperti (conforme 13 · non conforme 28 · rotta 7 · niente da giudicare 1) · **19 mutazioni su 19** |
| i limiti di §4.5 sul palco vero | 320×240 **ADATTATA** · 318×240 **RIFIUTATA** · 1281×801 → **1280×800** · 7682×4320 **RIFIUTATA** · col tetto del client 3842×2160 → **3840×2158**, ripiego dichiarato |
| le **coordinate in volo** (§7.1, mai provate prima) | dentro il secondo: **saturate e scritte** · **1000 ms dentro, 1001 ms `ERRORE_PROTOCOLLO`** · l'errore vero non è coperto dalla grazia |
| il palco che cambia **da sé** | **zero `TELA` non sollecitati, mai** (filo: 3 cambi di fila; prodotto: richiamato, **torna in 37 ms**, 0 fotogrammi di misura sbagliata al client) |

### 4.5 · La tastiera al riattacco

| scena | atteso *dichiarato prima* | `[M]` misurato |
|---|---|---|
| sessione `it`, riattacco dichiarando `it` | `aèò\@a` due volte | ✅ identico (controllo positivo) |
| sessione `it`, riattacco dichiarando **`us`** / **`de`** | se §7.3 è vera, i caratteri cambiano | ⛔ **identico a `it`** ⇒ §7.3 **refutata**: vedi `DECISIONI.md` §5-bis.7 |
| ⭐ la **sessione** passa `it`→`de` a palco vivo | keymap riletta ⇒ `azy\a` | ✅ **`azy\a`**, `ricambi_tastiera` 0→1, impronta `8315b8d9`→`d1c54543` |
| distacco col **Maiusc premuto davvero**, riattacco | rilasciato ⇒ minuscole | ✅ `rilascio al distacco: 1`, testimone **`az`** |
| idem, ma **il dispositivo muore col tasto giù** | rilascio sul dispositivo **nuovo** | ✅ `ricambi_tastiera` 4→5, `az` |
| disposizioni malformate · ignote · con variante | `ERRORE_PROTOCOLLO` · `SESSIONE_NON_SERVIBILE` · — | ✅ `0x0b` × 4 · `0x0e` × 3 · ⛔ **`it(nonesiste)` apre la sessione** |

### 4.6 · ⛔⛔ Il difetto che nessun registro dichiarava — il clic che muore

| | `[M]` 16 agosto 2026, banco `06-b33` |
|---|---|
| la scena | `BTN_LEFT` **tenuto giù** → `ADATTA_TELA` → i dispositivi si ricreano → si rilascia |
| che cosa succede | il rilascio del **tasto** arriva, quello del **bottone** no ⇒ ⛔ **e il giro successivo, identico a uno che era stato verde su tutto, non consegna più NESSUN clic — per sempre** |
| come si guarisce | ⭐ solo riaccendendo il server (che forza `drop_device`) |
| la catena, tutta `[R]` **dentro Mutter** | `remove_viewport_devices()` (`meta-eis-client.c:197-206`) **non passa da `drop_device()`** · `handle_button()` (`:612-621`) **ingoia in silenzio** il rilascio per un pulsante non premuto *su quel* dispositivo · `update_button_count()` (`meta-seat-impl.c:899-908`) è **del posto**: il press del dispositivo morto lo tiene a 1, e **non scende mai a zero** |
| ⇒ | ⭐ È *«su Android il mouse non prende più i click»* (l'utente, 15 agosto) **per una causa diversa da quella curata allora** |
| la cura | **una riga**: `input_rilascia_tutto()` **prima** di `cattura_ridimensiona()` — applicata, `figlio.c:3964` |
| ⛔ **e non basta** | `[M]` i dispositivi si ricreano **anche senza cambiare misura**: ogni `cattura_risveglia()` (400 ms, scena ferma e chiave dovuta) è seguito 8-24 ms dopo da un ricambio — **3 risvegli, 3 ricambi**, con **zero `ADATTA_TELA`**. ⇒ Cioè **proprio mentre l'utente tiene premuto il mouse su un desktop fermo**, e la cura ovvia (rilasciare a ogni risveglio) **distruggerebbe ogni trascinamento** |

### 4.7 · ⭐⭐ La decisione dell'utente ATTUATA — `Ctrl+Z` da una tastiera tedesca

*`DECISIONI.md` §5-bis.7, confermata dall'utente il 16 agosto 2026 e attuata la notte stessa.
⛔ Il numero della scena non è un carattere: è una **scorciatoia**, perché le lettere viaggiano come
lettere (§5-bis.6) e a spostarsi sono le **posizioni**.*

| scena | atteso *dichiarato prima* | `[M]` |
|---|---|---|
| client dichiara `de`, sessione `it`, si batte il `Ctrl+Z` di una tastiera tedesca (evdev **21**) | rinegoziata ⇒ **`1a`** (annulla) · non rinegoziata ⇒ **`19`** (rifai) | ⭐ **`1a`** |
| ⛔ la stessa scena **con la cura tolta** | **`19`** | **`19`** — e il server **predice il sintomo da sé**: *«RIPIEGO DICHIARATO (§5-bis.7): … le SCORCIATOIE no: `Ctrl+Z` finirà sul tasto che quella posizione ha nell'ALTRA disposizione»* |
| riattacco dichiarando `us` su sessione `it` | `a\@a` (`è`/`ò` non esistono su `us`) | **`a\@a`** — ⚠ ieri era `aèò\@a` |
| `DISPOSIZIONE` (`0x0009`) a sessione aperta | connessione **viva**, keymap cambiata | **viva**, `KEYMAP CAMBIATA → de [German]` — ⚠ ieri: congedo `0x0b` |
| `hu` · `tr` (che la macchina **ha**) | ora **accettate** | sessione aperta — ⚠ ieri `SESSIONE_NON_SERVIBILE` |
| `it(qwertz)` · `it(nonesiste)` | ora **rifiutate** | `0x0e` — ⚠ ieri **aprivano** |
| `de(neo)` | accettata e caricata | `de+neo` → **`[German (Neo 2)]`** |

⛔ **E la catena attraversa un confine di processo**: i byte del client stanno nel **padre**, `libei`
sta nel **figlio**. ⇒ Cinque file su otto non appartenevano a chi ha scritto la cura, e la parte
mancante è stata **consegnata come patch** (`banchi/06-b34-cucitura.py`, 13 pezzi con ancore
verbatim) invece che applicata di nascosto mentre un altro agente lavorava sugli stessi file.
⭐ **Applicata dal coordinatore il 17 agosto 2026, a banchi fermi**: il prodotto compila **senza
avvisi** e `04-b31` resta **19 su 19**.

⚠ **Due limiti dichiarati**: `input_disposizione()` è **di GNOME** (`libei` non ha un verso
client→server per la keymap, e Mutter non offre un setter: la leva è `input-sources`) ⇒ **su KWin
non funzionerà**, e il posto giusto è `mutter.c` col gemello `kwin.c` — è lavoro della fase 11. E
`gsd-keyboard` può risovrascriverci: non si previene (è *«il contorno»* di `CODER.md` §4.1-bis), **si
misura**.

⛔ **E la domanda che questa decisione promuove a domanda principale**: la pagina **indovina** la
disposizione dalla lingua del browser (`src/pagina.html:2585-2624`, `[?]` dichiarata lì dal codice
stesso). Finché il server la buttava non faceva danno; adesso che **obbedisce**, una disposizione
indovinata male **cambia la tastiera all'utente per davvero**.

### 4.8 · ⭐⭐⭐ LA VERIFICA CONGIUNTA — 17 agosto 2026, **a macchina ferma**

*Sei agenti hanno lavorato in parallelo, ciascuno nel suo albero: ⛔ **nessuno aveva mai misurato il
prodotto con le cure degli altri dentro**. Questa è la sola misura che le guarda tutte insieme, e su
una macchina in silenzio — perché tutti i millisecondi di ieri sera erano presi con **cinque banchi
e cinque codificatori** sullo stesso iGPU.*

| | |
|---|---|
| il silenzio | load **0,90 → 0,12** (0,07-0,13 durante le misure): spenti i server 7721 e 7731 e tre sessioni GNOME |
| l'albero | uno solo, `06-i-src`, costruito sulla macchina di prova. Impronte **identiche al deposito**: `rcp.c 283ffe7b` · `figlio.c ca7b6a97` · `input.c 51a8ef08` · `tastiera.c e7590d32` · `pagina.html 55bc9e77` |
| ⛔ `prova` e la 7700 | **mai toccati**: gli stessi due pid dall'inizio alla fine, e la porta risponde ancora |

| scena | atteso *dichiarato prima* | `[M]` misurato |
|---|---|---|
| ⭐ **A · il trascinamento del bordo** | **0 rotti su 18** | ⭐ **0 su 18** — la 1ª richiesta `NON_ORA` **subito**, la 2ª `ADATTATA`, tela finale = quella della **seconda** in **31,7 ms** di mediana (23,8-45,3) · **0** fuori misura · **0** scartati · ⛔ **nessuna attesa dei 3 s**. E **0 su 10** anche a 5 ms di distanza, e **0 su 10** sotto carico CPU **10,9** |
| ⭐ **B · il clic tenuto giù** | il rilascio arriva, e i clic del **secondo giro** arrivano tutti | ⭐ registro: *«RILASCIATI 2 fra tasti e pulsanti PRIMA di ridimensionare»* · e nel secondo giro, **senza riaccendere il server**, il testimone vede **tutti e nove gli atti, clic compreso** |
| ⭐ **C · la tastiera che comanda** | **`1a`** | ⭐ **`1a`**, con la catena intera nel registro: `§5-bis.7 «de» chiesta` → `tastiera TOLTA (ricambio 1)` → `KEYMAP CAMBIATA → de [German]` |
| **D · i millisecondi, a macchina ferma** | riprendere i cinque numeri | ridimensionamento a caldo **4 ms** di mediana (3-7, n=10) · Mutter **39,5 ms** · giro intero lato server **44,5 ms**, **10/10 ADATTATA** · `SESSIONE`→1° fotogramma **25 ms** col palco in piedi e **203-220 ms** da montare (era 335) · **0** scartati, **0** fuori misura |

⭐ **E il controllo positivo ha reso dove contava**: spenta la riga di `figlio.c:3964` e ricompilato,
il caso del clic torna **DIFETTO_VIVO** — nel secondo giro **non arriva più nessun bottone**, solo i
tasti, cioè §4.6 alla lettera. Riaccesa, torna tutto.

⛔⛔ **Ma sul trascinamento il controllo positivo NON ha reso, e va detto forte**: togliendo la cura
della 6.4 (`rcp.c:2847`, il richiamo alla misura **in volo**) escono **ancora 0 su 18**. ⇒ **Non è
quella cura a tenere questa scena**, e i **4 su 18** misurati dalla 6.3 **non sono stati
riprodotti** — né a 10-35 ms, né a 5 ms, né sotto carico CPU 10,9. ⚠ La differenza che resta fra le
due misure è la **contesa sulla GPU**: quel giorno c'erano cinque codificatori sullo stesso iGPU, e
a macchina ferma quella condizione non si ricrea. ⇒ ⛔ **Il verde di A vale «a macchina ferma e
sotto carico CPU», non «sotto contesa GPU»**, ed è così che va letto finché qualcuno non riproduce
la scena originale.

| i banchi del filo, rifatti sul codice di adesso | |
|---|---|
| `04-b31` · `06-b36` · `01-b4` · `06-b38` | **19/19 + 12/12** · **23/23 + 19/19** · **49/49** · **19/19** ⇒ ⭐ **nessuna regressione di integrazione**, e la costruzione da zero non emette **un solo avviso** |

---

## 5 · ⛔ Che cosa NON ha funzionato

*Si riempie anche quando fa una brutta figura. ⭐ E in questa fase la parte più istruttiva non sono
i difetti del prodotto: sono i **banchi che erano verdi senza guardare**.*

### 5.1 · I due mandati avversariali che sono stati SMENTITI dalla misura

| la frase da refutare | esito |
|---|---|
| *«il riattacco riaggancia i dispositivi e tutto funziona»* (6.1) | ⭐ **regge** sull'input normale: l'applicazione aperta prima dello stacco riceve **tutto**, con le coordinate esatte. ⛔ È falsa **solo** per lo stato *tenuto giù* — ed è lì che stava il difetto |
| *«la catena `figli_ritela()` → `cattura_ridimensiona()` regge»* (6.3) | ⛔ **FALSA**: con due `ADATTA_TELA` a 25-35 ms — *«chi trascina un bordo ne manda proprio due di fila»*, e il codice stesso lo chiama «IL caso» — **4 giri su 18** (poi 2/18) lasciano il desktop **non adattato**, e il client aspetta il fondo di **3 s** per ricevere `NON_ORA`. ⚠ Invece *«i fotogrammi scartati sono zero»* **regge**: 0 in tutti i giri |
| *«da quando la tela è la finestra, lo zoom non falsa più niente»* (6.5) | ⭐ **vera** — ⛔ ma nel posto sbagliato: a rompere la nitidezza era l'**arrotondamento**, non lo zoom |
| *«il prodotto viola §7.1 in almeno un caso della tela»* (6.6) | **non confermata** sui cinque casi esercitati contro il prodotto |

### 5.2 · ⛔ I banchi che erano verdi senza guardare — sei, e nessuno se n'era accorto

1. ⛔⛔ **`04-b31-certifica.sh`, guasto G8**: l'ancora era **scaduta** dal 16 agosto (una funzione nuova
   si era interposta fra le due che nominava) ⇒ **il più grave dei dodici guasti non si innestava
   più**. Il certificatore lo dichiarava con `??`, e nessuno lo lanciava;
2. ⛔⛔ **`01-b3` e `01-b4` parlavano formati diversi** dal 12 agosto (`RCPREG 0x00 0x01` contro
   `0x02`): **ogni** traccia del cliente usciva «registrazione rotta» e cinque verifiche fallivano.
   ⭐ *Nessuno dei due file era rotto da solo: il difetto stava fra i due*;
3. ⛔ **il validatore chiudeva sessioni sane**: la grazia di §6.2 era scritta, importata e
   **irraggiungibile**, perché nessuno diceva al giudice del fotogramma che una `ADATTA_TELA` era in
   volo;
4. ⛔ **`06-b34`, controllo positivo B**: rompendo il rilascio, il conto diventa `0` **ma il
   carattere arriva lo stesso** ⇒ `[M]` **Mutter rilascia da sé i tasti su un dispositivo che
   distrugge**, e il compositore ci copriva il guasto. Il verdetto è stato **spostato di grandezza**
   invece di essere lasciato verde;
5. ⛔ **`06-b35`, guasto G4**: dichiarato **VERDE prima del giro**, perché su Mutter «chiesto» e
   «concesso» coincidono sempre ⇒ quel banco **non copre** il difetto n° 5 dei dieci del 15 agosto,
   e lo scrive;
6. ⛔ **`06-b33`, guasto G1**: rompendo *un solo* meccanismo del ricambio non cambia niente — la
   robustezza è **ridondante** (tre riletture della regione). ⭐ Diventato un **non-guasto misurato**,
   ⚠ col limite dichiarato: *nessun caso protegge il singolo meccanismo*.

### 5.3 · Le figure peggiori degli agenti, tenute perché sono il metodo

- ⛔ un giro ha mandato l'input **sul canale di controllo** e il server ha congedato: difetto **del
  banco**, e il registro lo diceva in una riga (`CODER.md` §3.11 in atto);
- ⛔ tre giri col **testimone vuoto**: i caratteri finivano nella **casella di ricerca di GNOME**
  perché nessuna finestra aveva il fuoco, e un `Invio` ha lanciato Nautilus. Scoperto
  **fotografando il desktop**, non ragionandoci ⇒ da lì il preludio e i **canarini**;
- ⛔ `umask 077` rendeva il binario guasto `0700 root`: il figlio usciva con **37**, e il banco stava
  per scrivere cinque *«SMENTITO»* accusando il prodotto **dei propri permessi**;
- ⛔ un `grep` ha estratto **`1002`** — un uid — credendo di estrarre una parola d'ordine: cinque
  `RESPINTO` e **il ban di §4.4-bis fatto scattare da un difetto del banco**. ⚠ Il colore non lo
  diceva: l'ha detto **il denominatore nuovo** (*«0 coppie chiuse»*);
- ⛔ una **pipe attorno a `enter.sh`** si è mangiata la richiesta di `sudo`: dieci minuti appesi in
  silenzio — è la trappola **8** del §0-bis di questo documento, scritta e poi calpestata;
- ⛔ e due attesi **corretti sulla misura**, con la ragione scritta accanto invece che allargati per
  farli tornare.

### 5.4 · ⛔ E un errore del coordinatore che ha rischiato di sviare quattro banchi

Ho spedito a quattro agenti un allarme su `LEZIONI.md` §1.15 — *«su Xvfb `requestAnimationFrame` non
gira MAI, e in Blink il `resize` non arriva»* — ⛔ **e non si è riprodotto**: `[M]` 16 agosto 2026,
sonda `06-b37`, **184 quadri in 3 s e 6 `resize` su 6**, su tutti e due i motori.
⚠ *Non si tocca §1.15*: quella misura è del 13 agosto ed è vera per la scena che descriveva. ⭐ Ma la
**guardia** che ho preteso resta, e ha reso: `giudica_palco()` ha **fermato un giro** in cui la scena
non stava producendo quel che il banco credeva (4 `resize` su 6, per passi da 1 px che non cambiano
la vista in pixel CSS). ⇒ *Un allarme sbagliato che lascia dietro uno strumento giusto.*

---

## 6 · Le decisioni prodotte

- ✅ **`DECISIONI.md` §5-bis.7** — *la disposizione di tastiera la comanda il client, e il server la
  applica*: **confermata dall'utente il 16 agosto 2026**, messo davanti alle tre strade. ⛔ E il
  riquadro nuovo di quella voce porta la misura che l'ha resa necessaria: era una decisione **✅ dell'8
  agosto mai attuata**;
- ⏳ **`RCP.md` §7.1** — la riga mancante sul **palco che cambia misura da sé** ha adesso **due
  stesure proposte e misurate** (dalla 6.4 sul filo, dalla 6.3 sul compositore vero), da fondere:
  nessun `TELA` non sollecitato · non adottare · non spedire fotogrammi di misura diversa ·
  richiedere la tela in vigore con un'attesa che cresce · scriverlo nel registro · ⛔ **e non
  richiamare mai il palco mentre una richiesta del client è in volo**;
- ⏳ **`RCP.md`**, altre sei righe consegnate dagli agenti e non ancora scritte: il confine del
  secondo di grazia (`<` o `<=`), le due tele dentro lo stesso secondo, i limiti della **vista** che
  §4.5 non nomina, che cosa risponde il server a `VISTA` (⛔ *niente*, e perché un `TELA` di cortesia
  ucciderebbe la sessione), `COMPOSITORE_INCAPACE` non dichiarato **permanente**, e ⛔ **la
  contraddizione §7.1 contro §4.2** su `ADATTA_TELA` seguito dal FIN del client;
- ⏳ **`SPECIFICHE.md` §6** — cinque righe proposte dalla 6.5, fra cui la chiusura delle tre `[?]` di
  §6.1-bis e il **numero di guardia** della nitidezza;
- ⏳ **`SPECIFICHE.md` §11.5** — Windows non è dichiarato fra i client (la sezione nomina i **motori**,
  non i sistemi).

---

## 7 · Che cosa resta `[?]`

### 7.1 · ⛔ Aperto e con una misura in mano — il lavoro che viene

| | |
|---|---|
| ⛔⛔ **il ricambio dei dispositivi che NON dipende dalla tela** | `[M]` ogni `cattura_risveglia()` (400 ms, scena ferma, chiave dovuta) ricrea i dispositivi di `libei`: **3 risvegli, 3 ricambi**, con **zero `ADATTA_TELA`**. ⇒ Il clic che muore ha una **seconda porta**, aperta proprio quando l'utente tiene premuto il mouse su un desktop fermo, e la cura ovvia distruggerebbe ogni trascinamento. ⏳ **La forma giusta va decisa**, e non è di una sottofase sola |
| ⛔ **il difetto è a monte, in Mutter** | `remove_viewport_devices()` dovrebbe passare da `drop_device()`. `[?]` se sia già noto o corretto a monte: **nessuno ha guardato**, e nessuno ha aperto niente |
| ✅ ~~**le richieste incatenate, da rimisurare**~~ · ⛔ **e resta un buco peggiore** | rimisurate il 17 agosto: **0 rotti su 18** (§4.8). ⛔⛔ **Ma il controllo positivo non ha reso**: togliendo la cura sospetta escono **ancora 0/18** ⇒ *non si sa che cosa tenga questa scena*, e i **4/18** della 6.3 **non sono riproducibili** a macchina ferma. ⚠ L'unica differenza rimasta è la **contesa sulla GPU** (cinque codificatori sullo stesso iGPU): finché non si ricrea, ⛔ **il verde vale «sotto carico CPU», non «sotto contesa GPU»** |
| ✅ ~~**la cura del clic non è mai stata verificata dove vive**~~ | verificata il 17 agosto su un albero solo: il rilascio è dichiarato nel registro e **tutti i clic del secondo giro arrivano**, ⭐ col controllo positivo che riproduce il difetto **a comando** |
| ✅ ~~**tutti i millisecondi sono sotto carico**~~ | ripresi a macchina ferma (load 0,07-0,13): §4.8 |
| ⛔ **tre attesi di `06-b33` sono scritti per il mondo COL DIFETTO VIVO** | T3, R1 e R2 restano **rossi con la cura** e erano **verdi senza**: con il tasto già rilasciato prima del ricambio, le righe di dichiarazione non si scrivono perché non c'è più niente di premuto. ⇒ **Va corretto l'atteso del banco, non il prodotto** — ed è un banco nato ieri, quindi il difetto è di ieri |
| ⚠ **due attrezzi del banco 6.3 si rompono** | `06-b35-lancia.sh tempi` (`ValueError`) e `06-b35-terreno.sh:395` (`integer expression expected`): i tempi della verifica sono stati calcolati **a mano dal registro** |

### 7.2 · Le `[?]` di misura, dichiarate invece che estrapolate

- **il DeX e la GPU vera**: il mezzo pixel non arriva ai pixel su Xvfb ⇒ `[?]` **su GPU vera e su
  Samsung DeX**. ⛔ Il telefono ce l'ha l'utente: si chiede a lui, non si aggira;
- ⛔ **«conforme» non è «funziona»**: l'arbitro certifica i byte — *«un server che rispondesse
  `TELA(ADATTATA)` senza toccare il palco passerebbe tutti e cinque i giri»*. I pixel li misura
  un altro banco, e la distinzione va tenuta;
- **il secondo di grazia curato e non misurato** (la data zero): per provarlo servirebbe un orologio
  che parte sotto il secondo, e la stretta di mano ne consuma già 1500. ⛔ **Nessun caso cieco
  scritto apposta**: un verde per costruzione è peggio di nessun caso;
- **codice mai esercitato su Mutter**: il ramo *«concesso diverso da chiesto»* (`figlio.c:4585`) e
  `MISURA DIVERGENTE` (`cattura.c:543`) — 17 richieste su 17 concesse esatte. Provabili **solo col
  palco finto**;
- **il posto si lascia dopo ~75 s** di silenzio, non i 30 di §5.3: `[?]` quale sia il tetto vero;
- **le coordinate in volo sono inarbitrabili da una registrazione**: `RCP.md` §11.1 non registra il
  **tempo**, e la regola del secondo non è collaudabile da un `.rcpreg`;
- **`?video=worker` non esercitato**; **`aioquic` non è installato sul portatile** (il cliente si
  prova in locale solo con surrogati, e il banco lo dichiara);
- ⛔ **il ripiego su KWin resta non verificabile sul vero**: KDE è la fase 11. Il percorso di codice
  è provato **sull'ospite finto**, e la **riga di registro** che lo dichiara adesso è pretesa da un
  banco (`06-b36` casi 1-2) — che è quel che `SPECIFICHE.md` §6.3 chiedeva.

### 7.3 · E i tre difetti che la decisione dell'utente rende urgenti

*Sottofase 6.2, secondo giro, in corso.*

1. ⛔ `rcp.c:1970` — l'**elenco fisso** rifiuta disposizioni che la macchina **ha**: `hu`, `tr`, `gr`,
   `ua` ricevono `SESSIONE_NON_SERVIBILE`. ⇒ Con §5-bis.7 attuata, **un utente ungherese si vedrebbe
   negare la sessione**. *«Curare D1 senza D3 significa spedire una regressione»*;
2. ⛔ la **variante fra parentesi** non la controlla nessuno: `it(nonesiste)` apre la sessione;
3. ⛔ `DISPOSIZIONE` (`0x0009`) **a sessione aperta chiude la connessione** — lo stesso `default` in
   cui cadeva `VISTA`, ed è il messaggio con cui la disposizione si cambierebbe **senza staccarsi**.

---

## 8 · Il giudizio dell'utente

*La fase si chiude su una misura giudicata dall'utente, non su un documento completo.
⛔ Non si scrive un verdetto che l'utente non ha dato.*

✅ **Uno c'è già, ed è del 16 agosto 2026**: **«il test su Windows lo dichiaro superato al 100 %»**
— dato sul prodotto vivo, da un terzo sistema client mai provato prima, con `dpr 1,25` e la finestra
dispari su tutt'e due i lati (§4.1 e §4.1-bis).

⏳ **Quel che aspetta il suo giudizio**: la scena del **trascinamento del bordo** e quella del
**clic tenuto giù** — le due che questa fase ha aperto — dopo la verifica congiunta a banchi fermi.
