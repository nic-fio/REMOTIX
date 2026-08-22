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
la tela girata al palco, clic → fotogramma, l'accesso — **si ripetono a banchi fermi** prima di
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

> ## ⛔⛔ I NUMERI DI QUESTA SEZIONE SONO STATI REVISIONATI IL 21 AGOSTO 2026, E MOLTI NON REGGONO
>
> *«Chi scrive un banco lo certifica nello stesso giro»* non basta: **chi lo certifica da solo si
> assolve**. La revisione avversariale — il momento che `PIANO.md` §0.4 chiedeva e che questa fase
> non aveva avuto — dice che **cinque banchi su sei non reggono come certificazione**, e quali
> misure cadono con loro. ⇒ **Leggi §5.5 prima di fidarti di un numero qui sotto.**

*Sei banchi nuovi, uno per sottofase, ciascuno **certificato dal suo autore nello stesso giro** con
guasti innestati in una **copia** — la regola nata l'11 agosto (*«chi scrive un banco lo certifica
nello stesso giro, o il conto non cala mai»*).*

| banco | che cosa monta | casi | il controllo positivo |
|---|---|---|---|
| `06-b33-*` (6.1) | terreno `provai6`/7781 · **testimone Wayland** e `gnome-terminal` **aperti prima** dello stacco · cliente che stacca, riattacca a misura diversa e **solo allora** batte, punta e clicca | 7 | **5 guasti** in copia di `input.c`: G2→C2 · G3→R1,R2 · G4→C6 · G5→C3,C4 · ⭐ **G1 non accende niente**, e vedi §5 |
| `06-b34-*` (6.2) | terreno `provat6`/7721 · ⭐ **l'atteso lo calcola il prodotto** (`tastiera_posizioni_per()` chiamata da fuori) · testimone che registra **il carattere**, non il conteggio | 6 | **2 guasti**: «la keymap si legge una volta sola» → rosso sul caso dichiarato · «i tasti se ne vanno col dispositivo» → ⛔ **verde lo stesso**, e vedi §5 |
| `06-b35-*` (6.3) | terreno `provap6`/7731 · scena che si muove a **50 ms** · cliente che manda `ADATTA_TELA` e conta i `TELA` | 5 giri | ⛔ ~~5 guasti su 5~~ → **3 confermati stabili (G1 G2 G3, 3 giri su 3) · 1 non discriminante (G4) · 1 INTERMITTENTE (G5, 2 su 3)**, `[M]` 22 agosto. ⭐ E il quarto conto — «non giudicati» — esiste apposta: prima G5 sarebbe **sparito da tutte e tre le colonne** senza una riga che lo dicesse. 📖 §5.9 |
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
| **la tela girata al palco** *(⛔ era etichettata «ridimensionamento a caldo»: vedi §5.14)* | ~6 ms (`[M]` 15 ago) | **5 ms** · **4 ms** di mediana su 9 cambi (3-13) | 6.1 · 6.3 |
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

### 4.3-bis · ⛔⭐ 17 AGOSTO 2026 — la stessa pagina **senza** il ridimensionamento a caldo

*`DECISIONI.md` §5.1-bis: la funzione è uscita dal prodotto. Le due righe qui sopra sono la misura
di ieri e restano come storia; queste sono la misura di oggi, sulla pagina che la fase consegna.*

⛔ **Perché rimisurare tutto e non solo le due scene toccate**: dalla pagina è stato **tolto
codice**, e le altre quattro scene la leggono. Una regressione lì non l'avrebbe vista nessuno.

| | `[M]` 17 agosto 2026, `06-b37`, ogni scena in un'invocazione sua |
|---|---|
| ⭐ **la batteria intera** | **12 combinazioni su 12 verdi** — sei scene (`numeri` · `pixel` · `sfora` · `coordinate` · `modi` · `voce`) per due motori (Chrome, Firefox), **zero righe rosse** |
| ⭐ i modi di `?adatta=`, **rovesciati di senso** | `no` **0** · predefinito **0** · `segui` **0**, con **4 `resize` su 4** arrivati in tutti e tre ⇒ la tela **non si tocca a sessione viva**, nemmeno con l'indirizzo vecchio |
| ⭐⭐ **i controlli positivi**, che ieri non c'erano | **spia VEDE** in tutti i giri (una `chiedi_tela` chiamata a mano viene contata) e `typeof tela_forse_chiedi` = **`undefined`**. ⛔ Senza di loro quei tre zeri sarebbero stati verdi **anche a spia rotta** |
| la voce spenta, V4 con la domanda nuova | dopo un `COMPOSITORE_INCAPACE` iniettato: **4 resize arrivati, 0 arrivi a `chiedi_tela`**, `tela_spenta` = `True`, e la dichiarazione all'utente esce: *«Questo desktop non sa cambiare misura: l'immagine viene adattata alla finestra dal browser»* |
| il palco, giudicato prima del prodotto | **183-184 quadri in 3 s · 6 `resize` battuti → 6 arrivati** (`LEZIONI.md` §1.15 non si riproduce qui) |
| ⏱ **quanto costa rifarla** | **~35 s a scena** · ~3 min 30 s un motore · **~7 minuti** la batteria intera su due motori |

> ### ⛔ E UN DIFETTO DEL BANCO, NON DEL PRODOTTO — da curare, non curato
>
> `bash banchi/06-b37-lancia.sh tutti tutte` dà **dodici rossi finti**: dopo la prima scena il
> browser non si riapre («nessuna finestra X per il pid …») perché `spegni_motore` uccide il pid
> del wrapper e non quello che tiene la finestra. ⭐ **I banchi si sono comportati bene** — si sono
> fermati invece di misurare, cioè hanno distinto «zero» da «non ho guardato» — ⚠ ma chi lancia
> quella riga la prossima volta perde mezz'ora a cercare un difetto che non c'è.
> ⇒ **Finché non è curato, si lancia una scena per volta.**

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
| ⛔ **D · i millisecondi, a macchina ferma** — ⚠ **NON RICALCOLABILI, vedi §5.6** | riprendere i cinque numeri | la tela girata al palco **4 ms** di mediana (3-7, n=10) · Mutter **39,5 ms** · giro intero lato server **44,5 ms**, **10/10 ADATTATA** · `SESSIONE`→1° fotogramma **25 ms** col palco in piedi e **203-220 ms** da montare (era 335) · **0** scartati, **0** fuori misura |

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

### 4.9 · ⭐⭐⭐ LA CACCIA AGLI ARTEFATTI È CHIUSA — 17 agosto 2026 sera, e **la colpa non era nostra**

*Per due giorni l'utente ha visto **blocchi rettangolari** nelle zone ferme del desktop, e la
caccia ha ucciso sette ipotesi una per volta (l'elenco stava nel riquadro di ripresa di
`PIANO.md`). ⛔ L'ottava non era nell'elenco, perché **stava dopo l'ultimo punto che un programma
sa leggere**.*

**Il sintomo, con la sua misura**: blocchi da **64×192** che si spostano col contenuto. `[M]` La
sessione vera dell'utente, **mentre li vedeva**, diceva `dipinti 23 · video 23→23 · salt 0 · buchi
0 · ord 0 · mis 0 · err 0`. ⇒ Non mancava un fotogramma: **erano corrotti i pixel dentro i
fotogrammi che arrivavano**, e nessun contatore lo poteva vedere.

#### Gli imputati, scagionati uno per uno e con la misura accanto

| imputato | la prova |
|---|---|
| la cattura / Mutter | ⭐ `scatto-ingresso.bgrx`, preso **mentre i blocchi erano in vista**: **pulito** |
| il codificatore, 300 delta in catena | gli stessi byte ridati a `ffmpeg`: **0 superblocchi rovinati su 600**, scarto medio **1,68** livelli |
| la forma dei pezzi sul filo | **300** unità temporali, **1** fotogramma ciascuna, nessuno nascosto |
| `VideoDecoder` del browser | `copyTo()` contro la verità: **0 fuori posto** su 300 fotogrammi, peggio **2,9** livelli |
| la tela **riletta** | `getImageData()` dopo il `drawImage`, **stessa tela e stessi istanti**: **0 su 180 000** superblocchi |
| ⛔⛔ la tela **DIPINTA sullo schermo** | **fotografata col cellulare: i rettangoli ci sono** |

⇒ ⭐⭐ **I pixel entrano giusti nella tela e si rompono quando la tela va allo schermo.** Nessun
programma può leggerli lì: `getImageData` legge il **magazzino** della tela, non quel che il
compositore ha **acceso**. È la forma peggiore di punto cieco, perché ogni banco che rilegge la
tela è verde **per costruzione**.

⛔ **E non è il browser**: Firefox **e** Chrome fanno lo stesso. ⛔ **E non è la GPU in generale**:
`ffplay` e YouTube — che dipingono in un **`<video>`** — sono **puliti** sulla stessa macchina e
nello stesso momento. ⇒ È la strada della **`<canvas>` 2D**.

#### ⭐⭐ La cura, misurata prima di essere creduta

Dipingere con **`createImageBitmap()` + `transferFromImageBitmap()`** su un contesto
**`bitmaprenderer`**, che il magazzino 2D non ce l'ha. **Il giudizio dell'utente sulla stessa
scena**: *«NIENTE ARTEFATTI!»*

⚠ **Che cosa comporta nel prodotto**, e non è una riga: oggi il fotogramma passa da **due** tele 2D
(`deposito_p.drawImage(f)` e poi `componi()` → `pennello.drawImage(deposito)`). ⭐ Il **cursore non
è dipinto sulla tela** — è un cursore CSS — quindi la tela visibile non deve comporre niente e
`bitmaprenderer` le basta. ⚠ Si perde il **centraggio dentro il buffer**, che si rifà col CSS, e va
**misurato il costo**: `createImageBitmap` è asincrona, e il ritardo è il numero per cui esiste la
fase 3.

#### ⚙ I tre strumenti nati in questa caccia, e restano

| | |
|---|---|
| ⭐ **lo scatto a comando** (`src/figlio.c`, `SIGUSR1`/`SIGUSR2`) | il figlio chiede una **chiave** e mette su disco, dallo stesso istante, `scatto-ingresso.bgrx` (i pixel che il codificatore ha in mano), `scatto-flusso.obu` (i byte spediti) e `scatto-uscita.bgrx`. ⛔ Non è un interruttore di prodotto: scrive solo con `--rilievo`. ⚠ Lo scatto arriva al **padre** e va **inoltrato**, perché `systemctl kill --kill-whom=main` consegna solo a lui — e `--kill-whom=all` direbbe «muori» a `gnome-shell` |
| ⭐ **`banchi/07-b48-tela-contro-verita.html`** | fabbrica una verità sintetica, la codifica con `ffmpeg`, la ridà al `VideoDecoder` del browser e confronta **`copyTo` contro la verità** *e* **`getImageData` contro la verità**. ⛔ **Non ha una riga di REMOTIX dentro**, ed è per questo che il suo verde vale |
| ⭐ **`banchi/07-b49-occhi-sulla-tela.py`** | non misura: tiene la scena in vista con **una** variabile cambiata (`gfx.webrender.software`) e la fa **guardare all'utente**. È l'unico strumento che vede dove `getImageData` è cieco |

⛔ **E il banco si è certificato da sé prima di essere creduto** (`PIANO.md` §0.3.4): coi guasti
**iniettati** — `certifica AV1` e `certifica H264` — dice *«è la decodifica: la tela ha ricevuto
pixel già rotti e li ha dipinti fedelmente»*, cioè **sa vedere il difetto che cerca**.

#### ⚠ E una misura che non c'entrava con la caccia, ma va tenuta

`[M]` Con H.264 in **hardware** su questa macchina il decodificatore converte il colore con una
scala diversa da `ffmpeg`: **5 000 superblocchi «fuori posto» su 126 fotogrammi**, peggio **30,3**
livelli — ⚠ ma **liscio e uniforme**, **+8 livelli sulle zone chiare**: *non* è un guasto a
blocchi. ⇒ Non è l'imputato di questa caccia, ma **è un colore sbagliato per l'utente**, e va
ripreso quando H.264 entra nel prodotto (`DECISIONI.md` §1.13-ter).

---

#### ⭐⭐ 4.9-bis · LA CURA È NEL PRODOTTO — 20 agosto 2026, e aspetta il giudizio

`src/pagina.html`: la tela visibile prende il contesto **`bitmaprenderer`** e il fotogramma ci
arriva con **una sola** conversione (`createImageBitmap`) invece dei **due `drawImage`** di prima.
⛔ **Spariscono tutt'e due le tele 2D**: quella del deposito — `[M]` **34,03 ms** di mediana per
fotogramma, il costo che la fase 4 aveva misurato — e quella della vista.

| che cosa cambia | e perché non rompe niente |
|---|---|
| **il deposito non c'è più** | `transferFromImageBitmap` dimensiona la tela da sé, e nessuno riscrive `width` ⇒ al ridimensionamento della finestra il fotogramma **resta**. La ragione per cui il deposito esisteva (§5.1, il nero durante un buco) cade da sola |
| **la cornice si rifà solo alla misura nuova** | è CSS, e farla a ogni fotogramma sarebbe la riorganizzazione del foglio che `adatta_vista()` evita apposta |
| ⛔ **`createImageBitmap` è asincrona** | ⇒ ogni fotogramma porta un **numero d'ordine** e una **epoca**: chi arriva dopo uno più nuovo si butta e **si conta** (`tardive`), e chi arriva da una sessione morta non dipinge sopra quella viva |
| ⛔ **e il ripiego si dichiara** | senza `bitmaprenderer` o `createImageBitmap` si torna alla tela 2D **e la riga lo dice**. ⭐ E `?tela=2d` accende la strada vecchia a richiesta: serve a **confrontare**, ed è l'unico modo di rifare quel confronto il giorno in cui il sintomo tornasse |

**`[M]` La misura di oggi, col testimone Marionette sul Firefox vero** (porta 7730, tela
1588×914, sessione `prova`): `dipinti == consegnati` (11→11, 12→12) · `salt 0` · `buchi 0` ·
`ord 0` · `mis 0` · ⭐ **`tard 0`** · `err 0` · tela tirata giù in PNG, **nitida a 1:1**.
⭐ **E il controllo delle due strade, una variabile sola**: su `/` la tela risponde
`getContext("2d") → null` (cioè il magazzino 2D **non c'è**) e la riga del registro dichiara
`bitmaprenderer`; su `/?tela=2d` risponde `2d`, `ricomposizioni 1`, e dipinge come prima.
⛔ **E un banco è stato corretto perché la sua lettura non esiste più**: `02-giudizio-catena.py`
leggeva i pixel con `t.getContext("2d")` **sulla tela del prodotto** — adesso ricopia in una tela
sua. ⚠ Quel che rilegge resta il magazzino, non lo schermo (§1.16).

⛔⛔ **E il numero che ancora NON c'è**: `[?]` **quanto costa `createImageBitmap`**. Il conto da
battere è quello del `drawImage` che ha sostituito (34,03 ms), e finché non è misurato **non si
dichiara un guadagno**. ⚠ Serve una scena in movimento, cioè l'apparecchio della fase 3.

⏳ **E manca il giudizio, che è l'unica cosa che chiude questa caccia**: nessun banco vede questo
difetto (§1.16), quindi la 4.9 resta aperta finché l'utente non guarda **il prodotto** — non il
banco — sulla sua scena.

---

#### ⛔⛔ 4.9-ter · E LA CURA HA ROTTO CHROME — 20 agosto 2026, due sintomi e una causa sola

*⭐ La cura di §5.4 era stata misurata **su Firefox soltanto**. L'utente l'ha aperta su Chrome, e
in dieci minuti sono usciti due difetti che sembravano di due famiglie diverse.*

**La causa, `[M]` in dodici righe di banco isolato:**

| | |
|---|---|
| la specifica | `transferFromImageBitmap` porta la tela alla misura dell'immagine |
| **Firefox** | ⭐ lo fa: tela 16×16 → **1588×914** (testimone Marionette) |
| ⛔ **Chrome** | **NO**: `prima=[16,16] dopo=[16,16]` con un'immagine 2544×926 |

**E i due sintomi, tutt'e due suoi:**

1. l'immagine finiva **rimpicciolita in un buffer di 16×16** e stirata dal CSS ⇒ *«non si vede più
   bene, mancano gli elementi della shell»*;
2. ⛔ **l'input moriva**: `cl_geometria()` calcola `vx = larghezza sul vetro / tela.width`, cioè
   **~124 invece di ~0,8** ⇒ ogni clic finiva in un punto fra 0 e 16, nell'angolo in alto a
   sinistra. Il registro del server lo diceva alla lettera: `PUNTATORE (5,5) · (4,5) · (3,5)`.
   L'utente: *«se clicco il quadrato del dash non compare il drawer»*.

⭐ **La cura**: la misura **si scrive**, prima del trasferimento, e si guarda quella **vera**
(`this.tela.width`) invece di fidarsi. ⇒ La riga si corregge da sé su qualunque motore, senza
chiedere a nessuno chi sia — `CODER.md` §3.9, *si chiede per nome e si verifica che sia stato dato*,
applicato all'**uscita**.

⛔ **La riga da portarsi via**: **un solo motore non è una prova, è mezza prova.** Ed è per questo
che da oggi c'è `banchi/07-b51-due-browser.py`, che fa i due giri da sé.

#### ⛔⛔⭐ 4.9-quater · IL DESKTOP SENZA SHELL — e non era nostro né della pagina

*Poi la shell è sparita anche su Firefox, con **tutti i contatori verdi**: `dipinti == consegnati`,
zero buchi, zero errori, zero tardive. La pagina dipingeva fedelmente quel che le arrivava — e quel
che le arrivava era **solo lo sfondo**.*

`[M]` Mutter, interrogato con `GetCurrentState`, ha detto la cosa che nessun registro diceva:

| monitor | misura | posizione | primario |
|---|---|---|---|
| `Meta-1` | 2544×926 | (0,0) | ⭐ **sì** — qui GNOME tiene barra e dock |
| `Meta-0` | 2532×840 | (2544,0) | ⛔ no — **ed è quello che catturavamo** |

⇒ ⛔ **Due figli di due server nostri sulla stessa sessione di `prova`** — le porte 7700 e 7730 —
ognuno col suo monitor virtuale. Su GNOME **barra e dock stanno solo sul primario**: il secondario
porta lo sfondo e basta. È il difetto «due server nostri sulla stessa sessione» della fase 4,
tornato a mordere, ⚠ **e questa volta travestito da difetto della cura appena messa**.

⭐⭐ **E adesso il prodotto lo DICE** — `src/mutter.c`, `mutter_monitor_cerca()`: se un monitor
c'era già, esce una riga che nomina il sintomo *e* la cura (*«l'utente vedrà solo lo sfondo, con
tutti i contatori verdi… quasi sempre è un altro server nostro sulla stessa sessione»*).
⛔ **E la guardia è stata provata, non creduta**: rifatto il difetto apposta con un secondo server
sulla 7740, `[M]` la riga è uscita — *«C'ERANO GIÀ 1 monitor su questa sessione (Meta-0)»*.

⚠ **Non si fallisce**: un monitor che c'era già può essere legittimo (uno schermo vero). Si dichiara.

#### ⭐⭐ 4.9-quinquies · IL BANCO CHE FA I DUE GIRI DA SÉ — `banchi/07-b51-due-browser.py`

*Nato da una frase dell'utente: «non voglio fare più test: hai il controllo del PC, sistema tutto e
fai le prove su chrome e firefox».*

Per ogni browser — Firefox col protocollo **Marionette**, Chrome col protocollo di **diagnosi
(CDP)** — quattro domande diverse: la **misura** della tela (`t.width` deve valere la tela in
vigore: è il difetto di Chrome), i **contatori**, l'**input** *letto dal capo che riceve* (si clicca
un punto noto e si legge nel registro del **server** dove è arrivato), e l'**immagine** in PNG.

⭐ **E ha due bersagli, non uno**: l'angolo *e* il centro. Col solo angolo, una conversione che
collassasse tutto nell'angolo — cioè il difetto vero — darebbe **verde**.

⛔⛔ **E la sua prima stesura era sbagliata, il che vale la pena scrivere**: confrontava il **numero
d'ordine** dell'input, che **riparte da 1 a ogni sessione** ⇒ diceva *«nessun input nuovo»* mentre
il registro del server portava il clic **arrivato giusto**. Un rosso del banco addosso a un
prodotto sano — `LEZIONI.md` §1.2. Adesso confronta le **righe nuove**.

⚠ **E aspetta che il palco sia libero fra un browser e l'altro**: `[M]` un browser ucciso non chiude
la sessione, la chiude il tempo morto di QUIC — **oltre 20 secondi** — e il secondo giro trovava il
palco occupato accusando la pagina di un difetto del banco.

**`[M]` L'esito, 20 agosto 2026, porta 7730:**

| | firefox | chrome |
|---|---|---|
| misura della tela | ⭐ buffer = tela | ⭐ buffer = tela (1584×856) |
| contatori | ⭐ `dipinti == consegnati`, zero tardive/errori | ⭐ idem |
| clic in (40,12) | ⭐ arrivato in **(40,12)** | ⭐ **(40,12)** |
| clic al centro | ⭐ arrivato in **(794,457)**, scarto **0** | ⭐ **(792,428)**, scarto **0** |
| immagine | ⭐ desktop intero, barra compresa | ⭐ idem |

⚠ **E quel che questo banco NON dice**: gira **headless**, cioè **senza GPU** ⇒ il codec negoziato
può non essere quello della sessione vera. **Gli artefatti di §4.9 non li vede e non li cerca**: il
loro strumento resta l'occhio dell'utente.

---

#### ⭐⭐⭐ 4.9-sexies · L'IMPUTATO VERO ERA IL DECODIFICATORE AV1 DI FIREFOX — 20 agosto 2026

*⛔ E la §4.9 aveva ragione a metà: la tela 2D **era** un difetto, e curarla ha ripulito Chrome. Ma
su Firefox i blocchi restavano, e la loro causa era un'altra. **Erano due difetti sovrapposti**, ed
è per questo che ogni ipotesi singola sembrava smentita.*

**Il banco che li ha separati** (`banchi/07-b52`, guidato da me, non dall'utente): si muove la
scena — la panoramica di GNOME che si apre e si chiude venti volte — e si prendono **tre immagini
dello stesso istante**.

| anello | come si guarda | esito |
|---|---|---|
| la **cattura** | `SIGUSR1` → `scatto-ingresso.bgrx`, i pixel che il codificatore ha in mano | ⭐ **pulita**: panoramica, dock, testo nitido |
| il **flusso spedito** | `scatto-flusso.obu` ridato a `ffmpeg/dav1d` — **22 delta della stessa catena** | ⭐ **pulito** |
| **Chrome**, stessi byte | 32 fotogrammi, scena mossa | ⭐ **pulito** |
| ⛔ **Firefox**, stessi byte | 31 fotogrammi, `dipinti == consegnati`, zero buchi, zero errori | ⛔ **blocchi rettangolari** |

⇒ ⭐ **Una variabile sola separa il pulito dal rotto, ed è il decodificatore.** I byte sono buoni —
lo dicono due decodificatori indipendenti — e Firefox li dipinge sbagliati **senza dichiarare
nessun errore**: `err 0`, `buchi 0`, `ord 0`, `mis 0`.

⚠ **E prima di accusarlo si è controllata la cosa nostra**: `ffprobe` sul flusso dà `Main`,
`yuv420p`, `bt709`, `tv` — cioè **8 bit**, esattamente quel che la pagina aveva chiesto
(`av01.0.13M.08`). L'ipotesi «10 bit dichiarati 8» resta morta come il 17 agosto.

#### ⭐⭐ E LA CURA ERA GIÀ DECISA: H.264 — attuato lo stesso giorno

*La decisione dell'utente del 17 agosto (§1.13-ter) era nata per un'altra ragione — Firefox per
Android non ha né HEVC né AV1 — e si è rivelata **anche** la cura di questo difetto.*

**`[M]` La misura, stessa scena e stesso banco, con H.264:** Firefox, **35 consegnati = 35
dipinti**, zero tardive, zero buchi, zero errori — ⭐ **e nessun blocco**. La stessa immagine che
un'ora prima era a pezzi.

**Che cosa è stato scritto** (il lavoro che §1.13-ter dichiarava «non ancora fatto»):

| dove | che cosa |
|---|---|
| `RCP.md` §4.3, §6.2 | `h264` nell'elenco negoziabile, `3` nel registro dei numeri. ⛔ Il `2` resta AV1 **per sempre** |
| `rcp.h` | ⭐ `RCP_CODEC_VIDEO_MAX`, perché il numero più alto stia in **un posto solo** |
| `rcp.c` | `NOSTRO_CODEC` diventa `hevc,h264` — AV1 esce dalla negoziazione |
| `codificatore.c` | `h264_vaapi` in hardware (`[M]` **1,6 ms** per fotogramma) e `libx264` come ripiego dichiarato; il lettore **Annex-B di H.264** (l'IDR sta nei *cinque* bit bassi, non nei sei di HEVC) e l'**SPS** letto fino al ritaglio, che è quel che permette di dire la profondità e la misura VERE |
| `figlio.c` | il terzo posto in **quattro** array per-codec, e la mappa numero → codec in una funzione sola |
| `pagina.html` | la sonda `h264-8` e la scala delle misure, **generate** dai due programmi di `banchi/` e non scritte a mano; `avc1.6400<livello in esadecimale>`; e le frasi all'utente che nominavano AV1 |

⛔⛔ **E i tre difetti che ha scoperto entrare, tutti della stessa famiglia — «un numero nuovo in
cinque posti, e uno resta indietro»:**

1. ⛔⛔ **quattro array per-codec erano lunghi 3** (indici 0-2): il codec **3** scriveva **fuori dai
   limiti** e sporcava la variabile accanto. Il sintomo era una riga che diceva *«§4.3: il padre ha
   negoziato 8 bit (prima **1**)»* a ogni richiesta di chiave — **un difetto di memoria travestito
   da difetto di negoziazione**, con zero fotogrammi e nessuna riga che nominasse la causa;
2. ⛔ **il figlio rifiutava il codec 3** con un tetto scritto a mano (*«che §6.2 non definisce»*) —
   e almeno questo *lo diceva*;
3. ⛔⛔ **`wt_video_diffondi()` buttava ogni fotogramma H.264 IN SILENZIO**: il figlio codificava
   (5 940 byte, CHIAVE, 1,6 ms), il padre riceveva, e lì il fotogramma spariva **senza una riga**.
   ⇒ Adesso il tetto viene da `RCP_CODEC_VIDEO_MAX` e il rifiuto **si dichiara** (una riga per
   numero, non per fotogramma).

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

### 5.5 · ⛔⛔⛔ LA REVISIONE AVVERSARIALE DEI SEI BANCHI — 21 agosto 2026, e **cinque su sei non reggono**

*È il momento che `PIANO.md` §0.4 chiedeva e che questa fase non aveva mai avuto: il revisore **sul
banco**. I sei agenti avevano scritto il proprio banco e **certificato se stessi**. ⛔ Adesso li ha
letti qualcuno che non li aveva scritti — sola lettura, nessun banco lanciato — e il conto è questo.*

| banco | verdetto | perché |
|---|---|---|
| `06-b33` riattacco | ⛔ **non regge come certificazione** | il giro `tenuto` — l'unico che porta il difetto vero — **non ha una riga sana di riferimento**, e il suo unico guasto si certifica da solo |
| `06-b34` tastiera | ⛔⛔ **non regge** | 3 casi su 7 non possono fallire, 2 calcolano il verdetto e lo buttano, e l'ancora del guasto principale **è nata scaduta** |
| `06-b35` palco | ⛔ **non regge come certificazione** | il marcatore del registro si prende **prima** che `accendi` azzeri il registro ⇒ i due conti che vengono dal registro sono **zero per costruzione** |
| `06-b36` tela sul filo | ⚠ **il banco regge, il certificatore no** | ⭐ è il migliore dei sei: orologio iniettato, registro troncato, attesi esterni, confine 1000/1001 ms. Ma il certificatore esce **0** anche se non innesta niente, e 3 casi su 23 non hanno guasto |
| `06-b37` pagina | ⛔⛔ **non regge** | ⛔ **l'unico dei sei senza NESSUN guasto innestato**, e quattro falsi verdi indipendenti |
| `06-b38` arbitro | ⚠ **le 49 e le 19 reggono, i cinque giri vivi no** | ⭐ la metà offline è la meglio costruita del deposito. `06-b38-tela.sh` è verde **contro un server che non risponde mai** |

⭐ **E il rifiuto motivato vale quanto le accuse**: di **43 ancore di guasto** verificate materialmente
sui sorgenti di oggi, **42 sono vive con molteplicità esattamente 1**. Il caso `04-b31` G8 — l'ancora
scaduta — **non si è ripetuto**, tranne una volta in `06-b34`.

#### ⛔ I quattro rilievi che tolgono il pavimento

1. **`06-b33`: il controllo positivo è morto e dichiara successo.** Il certificatore manda in modo
   `tenuto` **solo** il guasto G3; il giro sano e il risanato girano solo in modo `comanda`. ⇒ R1
   oggi è rosso perché col tasto già rilasciato non c'è più niente di premuto — non per il guasto — e
   lo script stampa lo stesso *«⭐ G3 ha acceso il caso dichiarato»*;
2. **`06-b33`: un giro completamente fallito certifica OGNI guasto.** Il confronto è
   un'**appartenenza** (`case " $R " in *" $CASO "*`), non un'uguaglianza d'insieme: se il client non
   regge la stretta di mano, tutti i casi vanno rossi, l'insieme contiene quello dichiarato, e il
   guasto risulta confermato. ⚠ Il giudice **sa** dire *«IL BANCO, NON IL PRODOTTO»*, e quel testo
   **non lo legge nessuno**;
3. **`06-b35`: il marcatore del registro precede la troncatura di UNA RIGA.** `registro-da` salva la
   lunghezza del registro, e la riga dopo `accendi` fa `: > "$LOG"`. ⇒ La regione dove stanno le
   righe della tela **viene saltata sistematicamente**: `tela_nuova_dal_palco == 0` è vero **gratis**
   (ed è la clausola che *«distingue il palco non ha obbedito da non gli è stato chiesto»*), e
   `non_spediti > 0` è **irraggiungibile** — cioè proprio l'attribuzione sbagliata che il banco
   dichiara di aver curato;
4. **`06-b34`: l'ancora del guasto B è nata scaduta**, e il ramo verde del caso 4b **è la firma della
   scena mancata**: se il ricambio avviene davvero, il contatore che il banco pretende `>= 1` vale
   **sempre 0** ⇒ il verde si ottiene **solo se la scena non è successa**. ⚠ La cura e il guasto che
   doveva provarla sono entrati **nello stesso commit**, e il guasto non è mai stato rilanciato.

#### ⛔⛔ E `06-b37`, che è un caso a sé: quattro falsi verdi, ciascuno sufficiente da solo

- **nessuna scena ha un limite INFERIORE sulla tela**: una tela 30 px più stretta della finestra —
  banda nera permanente, 30 colonne perse — lascia **12 combinazioni su 12 verdi**;
- **il ramo che attua «la voce spenta» non viene mai eseguito**: la spia sostituisce `chiedi_tela`
  **prima** di misurare, e la guardia vera sta **dentro** la funzione sostituita ⇒ il banco prova che
  *un booleano cambia valore*;
- **la «domanda vera» è un'identità algebrica**: il banco ricostruisce l'ingresso e lo confronta con
  l'uscita della funzione che quell'ingresso l'ha prodotto — scarto 0 in 93 righe su 126, per
  costruzione;
- ⛔⛔ **le coordinate: l'origine è cancellata per costruzione.** Lo scostamento fra dove l'immagine
  sta e dove la pagina crede che stia viene **sottratto** prima del confronto. ⇒ Il difetto del DeX —
  la tela dipinta 50 px a destra di dove `getBoundingClientRect()` la dichiara — **dà scarto 0 su 20
  punti su due motori**. È esattamente il difetto che quella scena nomina come propria ragione d'essere.

#### ⛔ Le misure di questa fase che CADONO, e vanno rifatte o riscritte

| dichiarazione | stato |
|---|---|
| §2 · `06-b33` «5 guasti: G2→C2 · G3→R1,R2 · G4→C6 · G5→C3,C4» | ⛔ **G3 non è certificato**; gli altri restano condizionati al rilievo 2 |
| §2 · `06-b35` «**5 guasti su 5 confermati**» | ⛔ **da rifare** dopo che la riga del marcatore è al suo posto |
| §2 · `06-b34` «6 casi · 2 guasti» | ⛔ **cade quasi tutta**: reggono il caso 1 e il caso 6. *«Un cambio di keymap distrugge e ricrea il dispositivo, e il tasto non resta giù»* **non è misurata** |
| §2 · `06-b36` «**23** casi · 19 guasti su 19» | ⛔ da riscrivere in **«20 casi su 23 certificati da 19 guasti»** |
| §2 · `06-b37` «7 scene», «20 punti · 2 523 colonne · 4 resize» | ⛔ **le scene eseguite sono 6**; il 2 523 viene da una scena mai girata sui due motori; **i 20 punti sono zeri per costruzione** |
| §2 · `06-b38` «49 accusate sul byte» | ⛔ **28 sul byte e sulla regola, 49 sull'esito**. ⭐ «19 mutazioni su 19» **regge** |
| §4.3-bis · «12 combinazioni su 12 verdi» | ⛔ **non conservata**: gli esiti nel deposito precedono di un giorno il codice di banco che l'avrebbe prodotta |
| §4.3 e §0 punto 7 · «le tre `[?]` di §6.1-bis, chiuse» | ⛔ **nessuna delle tre è chiusa**: lo zoom è assolto da una tolleranza di 2 px mentre lo scarto peggiore misurato è **esattamente 2**; il lato dispari è reso impossibile per costruzione e mai provocato; il mezzo pixel è osservato e non incrementa nessun conto |
| §0 punto 4 · «il ripiego su KWin dichiarato nel registro» | ⭐ **regge** (`06-b36` casi 1-2, ancora viva) |
| §0 punto 5 · «le coordinate in volo del secondo dopo `TELA(ADATTATA)`» | ⭐ **regge, ed è la parte più solida dei sei banchi** |
| §2 · `06-b34` «l'atteso lo calcola il prodotto» | ⛔ **non è implementato**: `06-b34-tabella.c` non è costruito né eseguito da nessuno script. ⭐ Ma l'accusa «la prova certifica se stessa» **cade lo stesso**, perché l'atteso vero è una **stringa di caratteri arbitrata da xkbcommon dentro la sessione** |

#### ⭐⭐ E la lettura che vale più dell'elenco

⚠ Dei ventidue rilievi, **uno solo** è un'ancora scaduta — la forma che §5.2 temeva e che tutti
cercavano. **Tutti gli altri hanno la stessa forma nuova, e nessuno l'aveva mai nominata:**

> ⛔ **la misura è buona, e il giudizio è staccato da lei.**

Un esito d'uscita catturato e non guardato (`b34`, `b35`, `b36`, `b38`), un atteso stampato e mai
confrontato (`b38`), un denominatore stampato e mai letto (`b38`), un contatore stampato con `inf`
invece che con `ko` (`b34`), un `case` di appartenenza invece che di uguaglianza (`b33`).

⇒ **La caccia della prossima volta non è alle ancore: è a ogni numero che un banco stampa e non
confronta.** 📖 `LEZIONI.md` §1.20.

### 5.6 · ⛔⭐ 21 agosto 2026 — **il registro mentiva sotto carico**, e ci sono voluti un attrezzo morto e un giro di banco per scoprirlo

*Nato dalla riparazione dei due attrezzi di `06-b35` chiesta da §7.1. ⭐ Il sintomo dichiarato era
«`06-b35-lancia.sh tempi` muore con `ValueError`». La causa non era nell'attrezzo.*

#### ⛔ Il difetto di PRODOTTO: tre `write()` per riga, e padre e figlio scrivono sullo stesso file

`src/registro.c` componeva ogni riga con **tre chiamate distinte** su uno `stderr` non bufferizzato
— intestazione, corpo, a-capo. ⚠ Il padre e il figlio appendono allo **stesso** registro: quando le
scritture si accavallano, un corpo finisce dopo l'a-capo altrui e nasce **una riga senza marca
temporale**.

`[M]` su un registro vero da 3,0 MB (28 035 righe): **23 righe orfane**, di cui **3 su 80** delle
«tela CHIESTA al produttore» — il **3,8 %** di una famiglia di righe su cui un attrezzo contava.

⭐ **E il controllo positivo della cura, `[M]` il 21 agosto**: sei processi che appendono allo stesso
registro, 800 righe ciascuno.

| | righe | orfane | «tela CHIESTA» trovate su 4 800 |
|---|---|---|---|
| ⛔ prima | 4 800 | **2 464** | **2 789** — cioè **il 42 % del conto era perduto** |
| ⭐ dopo | 4 800 | **0** | **4 800** |

⇒ **La cura**: la riga si compone in un buffer e si scrive con **una sola `write(2)`**. Sotto
`PIPE_BUF` (4096 byte) una `write` su un file in append è atomica rispetto alle altre; chi supera il
buffer viene **troncato con un segno**, perché *una riga tagliata si vede, una riga intrecciata no*.
⭐ In più `write(2)` è async-signal-safe, che `fprintf` non è, e il `fflush` non serve più.

⛔⛔ **E la lezione non è sul registro**: è che **lo strumento di diagnosi principale di questo
progetto si rompeva proprio sotto carico** — cioè esattamente nella scena in cui lo si interroga.
📖 `LEZIONI.md` §1.21.

#### ⛔ Un ottavo difetto del banco, e questo faceva peggio che rompere

`accendi` fa `: > "$LOG"` e **non azzera la marca** da cui gli attrezzi contano. `[M]` trovata una
marca da **825 758 byte** su un registro da **45 373**. ⚠ Non dava «zero sistematico» — dava **una
finestra arbitraria**, che è peggio: un conto plausibile e falso. L'unico esito superstite dichiara
`tela_nuova_dal_palco = 258` per un giro che cambia tela **9** volte.

#### ⛔ I numeri **D** di §4.8 non sono ricalcolabili — la finestra è perduta

⚠ Va scritto invece di essere aggirato: **4 ms · 39,5 · 44,5 · n=10** vennero da una finestra di
registro che **è stata cancellata**, e nessun file superstite la contiene. ⇒ Quel che si ricava oggi
dai registri che restano, **a macchina ferma**, con gli attrezzi riparati:

| | `[M]` 21 agosto, dagli attrezzi riparati |
|---|---|
| **la tela girata al palco** | **4,0 ms** (0-18, n=30) |
| Mutter | **35,0 ms** (29-45, n=20) |
| giro intero lato server, `ADATTATA` | **43,5 ms** (38-57, n=20) — contro i 44,5 scritti: **finestra vicina, non la stessa** |
| `NON_ORA` | **6,0 ms** (5-7, n=10) — ⛔ e prima stava sotto la stessa etichetta dell'`ADATTATA`, che è la forma E2 |

⭐ **E un numero del documento torna esatto**: §4.2, *«4 ms di mediana su 9 cambi (3-13)»*, esce
identico dagli attrezzi nuovi sullo stesso registro. ⇒ Non è tutto da rifare: è **quel** riquadro.

#### ⭐⭐ E un indizio NUOVO, a favore della tesi della contesa

`[M]` sul registro del **16 agosto**, con cinque banchi accesi: `NON_ORA` ha mediana **22 ms** e
**due casi a 3 000 ms** — la scadenza intera di §7.1. Sul **17**, a macchina ferma: **6 ms**, e
nessuno arriva al fondo. ⇒ ⭐ **La contesa muove davvero questa scena**, e il *«il verde vale sotto
carico CPU, non sotto contesa GPU»* di §7.1 ha adesso un secondo appoggio prima ancora che la scena
di contesa venga lanciata.

#### ⭐ E come sono stati certificati gli attrezzi riparati

Il calcolo a mano **riscritto in `awk`** — altro linguaggio, altro algoritmo — e confrontato
**campione per campione** su tre registri veri: **235 campioni, tutte e cinque le misure coincidono
esattamente**. ⚠ Una divergenza c'è stata, ed era **l'`awk` a sbagliare**: consumava una risposta
oltre il tetto. ⭐ Il controllo positivo di `06-b35-tempi.py` verifica anche che **l'attrezzo
vecchio, sullo stesso ingresso, muoia o sbagli** — altrimenti non controllerebbe niente.

⏳ **E il «5 guasti su 5» di §2 resta sospeso**: i cinque rilievi della revisione sul certificatore
sono chiusi (il giro sano come metro, la marca dopo l'accensione, lo stato d'uscita di
`costruisci.sh`, lo strumento che dichiara «cieco» invece di dire zero), ⛔ ma **il giro non è ancora
stato rifatto**. La scena di contesa (`06-b39-*`) è **pronta e non lanciata**: aspetta la finestra,
perché sposterebbe i millisecondi di tutti gli altri banchi accesi.

### 5.7 · ⭐⭐ 21 agosto 2026 — **la seconda porta del clic che muore, misurata**, e la cura che NON si può fare

*Banco nuovo `banchi/06-b33-risveglio.*`: collega `cattura.c` e `input.c` del **prodotto** e li chiama
da riga di comando, col testimone Wayland dentro la sessione di `provai6`. Tela 1264×800,
`MUTTER_DEBUG=eis,input`.*

| scena | `[M]` | carico |
|---|---|---|
| **S0** controllo zero, clic senza ricambi | il testimone lo vede: giù e su | 5,67 |
| **S1** tre `cattura_risveglia()`, mano alzata | ⭐ **3 risvegli → 3 ricambi** (delta `[1,1,1]`) con **0** `cattura_ridimensiona()` ⇒ **§7.1 è vera** | 1,86-2,19 |
| **S2** `BTN_LEFT` giù, **un** risveglio | ⛔ il rilascio **non arriva mai**, e **il clic fresco successivo nemmeno** ⇒ desktop morto ai clic. ⭐ La **tastiera** continua a funzionare | 1,58→10,68 |
| **S3** la stessa scena con `cattura_ridimensiona()` | **esito identico**: sono due porte sulla stessa stanza | 3,76 |
| **S4** si rompe, poi si stacca il cliente EIS | ⭐ **i clic tornano**, con lo **stesso `gnome-shell`** (pid verificato prima e dopo) | 1,39 |

#### ⭐ La catena `[R]` di §7.1-bis diventa `[M]` — e per un pelo non veniva smentita a torto

Dal giornale di Mutter, al millisecondo: `EIS: Updating viewports` **senza** nessun «Releasing
pressed buttons» accanto; poi `Dropping repeated press of button 0x110, count 2` e
`Dropping repeated release of button 0x110, count 1`. Il rilascio del pulsante tenuto **non compare
affatto**: `handle_button` lo ingoia prima che il posto lo veda.

⚠⭐ **E la precisazione vale quanto la misura**: la riga «Releasing pressed buttons» **c'è**, sei
volte — ma **al distacco**. ⛔ Una ricerca di assenza sull'intero giornale avrebbe **smentito §7.1-bis
a torto**. La lettura regge nella forma precisa: assente *accanto a `Updating viewports`*, presente
al disconnect.

#### ⛔ E l'ipotesi «la cura è più piccola di quanto sembri» è SMENTITA

*(Era del coordinatore: `button_count[]` è del **posto**, non del dispositivo, quindi un rilascio da
un dispositivo nuovo potrebbe far scendere il conto.)* ⛔ **No**: `handle_button`
(`meta-eis-client.c:612-621`) guarda `device->button_state`, che **sul dispositivo nuovo è pulito**,
e un rilascio da lì non arriva mai a `meta_seat_impl_notify_button_in_impl`. L'invariante è
`count = Σ bit vivi + trapelati`, e per consegnare un rilascio serve `count == 1` con un bit vivo,
che ha già incrementato ⇒ **irrecuperabile**. L'unica strada resta `drop_device()`.

#### Le quattro forme della cura, col prezzo — e la scelta

| | dove | prezzo |
|---|---|---|
| **A · prevenzione**: non ci si risveglia con qualcosa premuto | guardia in `figlio.c` + una finestra in `input.c/.h` | ⭐ **nessun trascinamento rotto**. ⚠ Su desktop fermo con un tasto giù la chiave non parte ⇒ **un client appena attaccato può restare bianco finché non si rilascia**. Si sana da sé, e la scena è rara: un trascinamento *muove* la scena |
| **B · si rilascia prima del risveglio** | una riga in `figlio.c` | ⛔ **taglia OGNI trascinamento su desktop fermo** — è la «cura ovvia vietata» di §7.1. Citata solo per il confronto |
| **C · recupero**: si riattacca il canale EIS quando il danno c'è | `input.c` (vede già `quanti_orfani > 0`) + `mutter_eis_riattacca()` in `mutter.c` | `[M]` funziona (S4). ⚠ Taglia il trascinamento in corso — **che però era già morto**. ⭐ Copre **le porte che non controlliamo**: `monitors-changed` (due giri), il cambio di keymap, e quel che Mutter aggiungerà |
| **D · si toglie il risveglio**: la chiave si rifà dall'ultimo fotogramma | `figlio.c` + `codificatore.c` | toglie la porta alla radice, ⛔ ma **non sostituisce** il risveglio: al login non c'è nessun fotogramma da rifare, e i 4,4 secondi tornano. E costa ~9,8 MB di copia a 2560×962 |

> ### 🔸 **Scelta del coordinatore: A + C** — derivata, non decisa dall'utente
>
> **A da sola non basta**, e la ragione è in §7.1-bis: le porte non sono una. `cattura_risveglia()`
> è quella che controlliamo; `monitors-changed` ne fa **due giri**, il cambio di keymap è un'altra, e
> la funzione che le apre tutte è entrata in **Mutter 48.5** — cioè è **nuova**, e ne arriveranno.
> ⇒ Una cura che copre solo la porta di casa nostra **scade al prossimo aggiornamento di GNOME**.
> ⚠ E il prezzo di **C** non è un prezzo: il trascinamento che taglia **era già morto** (S2).
> ⏳ **Il prezzo di A invece è visibile all'utente** — la finestra bianca finché non si rilascia — e
> i prezzi visibili li giudica lui: la riga sta qui perché la veda, non per essere già decisa.

⛔ **E un vincolo trovato misurando, che cambia il preventivo di C**: `input_apri()` **riusa il
descrittore** che `mutter.c` tiene da parte, e finché quello resta aperto Mutter non vede nessun
distacco e `drop_device()` non gira. ⇒ **La cura non sta dentro `input.c`.** `[R]`
`meta-remote-desktop-session.c:1943-1969`: `session->eis` si riusa e ogni `ConnectToEIS` aggiunge un
cliente, quindi sessione e palco non si toccano.

#### ⛔ Un fatto nuovo che tocca la certificazione di `06-b33`

Con la cura di `figlio.c:3964`, `segna_orfani()` **non gira nemmeno nel prodotto sano** ⇒ **G3 non è
più certificabile in `06-b33`**: la sua scena vive adesso in `06-b33-risveglio.sh tenuto` (caso T1).
⏳ Quel banco **non ha ancora una certificazione con guasto innestato**, ed è il buco più grosso di
questa consegna — dichiarato dall'autore per primo.

#### ⭐ E i cinque rilievi della revisione su `06-b33`: chiusi

Il mondo si **legge** dal registro; R1/R2 sono pretese **solo col difetto vivo**; **T4 nuovo** — il
clic fresco, che è il danno vero e **non lo misurava nessuno**; R1 cerca il marcatore **dei
pulsanti**; C6 conta **nella finestra del ridimensionamento** (prima `rp >= 1` era soddisfatto dai
risvegli); giro sano e risanato **in tutt'e due i modi**; **uguaglianza dell'insieme** invece di
appartenenza; l'esito del giudice propagato. ⭐ Col certificatore nuovo, **G3 accende zero casi** — e
il vecchio avrebbe stampato *«⭐ G3 ha acceso R1»*.

⛔ **E cinque difetti del banco nuovo, dichiarati dall'autore**, di cui il più grave: il rilascio del
pulsante tenuto e quello del clic fresco **non si distinguono** per posizione rispetto al `RITELA` —
l'ordine con cui Wayland consegna `configure` e `button` è **una corsa**. Il confine giusto è il
**press fresco**. Prima della correzione, T4 usciva giallo su un giro sano.

### 5.8 · ⭐⭐ 21 agosto 2026, notte — **la contesa GPU misurata, e il verdetto RIFIUTATO dal banco stesso**

*La scena che §7.1 chiedeva da giorni, girata in una finestra dedicata con tutti gli altri banchi
fermi. `[M]` Impronte dei sorgenti nel rapporto; ferro: **Intel UHD 730 integrata**.*

#### La scena è vera — certificata prima di misurare

`[M]` Un codificatore da solo fa **382 fotogrammi/s** a 1920×1080; **cinque insieme, 184 ciascuno**
⇒ la contesa sull'iGPU **c'è**, ed è **2,08×**.

#### ⛔ Ma il prodotto non se n'è accorto, e il banco **si è rifiutato di dare il verdetto**

`[M]` 18 giri sotto contesa (carico **2,57**) contro 18 a riposo (**0,41**), nella stessa ora:

| | sotto contesa | a riposo |
|---|---|---|
| **rotti** | **0 su 18** | **0 su 18** |
| ritmo fotogrammi | 51,2 ms | 55,3 ms |
| ① girata→chiesta | 4,0 ms | 5,5 ms |
| ② **Mutter** | 28,0 (22-48), ⛔ **13 oltre il tetto** | 32,0 (18-47), ⛔ **17 oltre il tetto** |
| ③ palco→spedita | 4,0 | 4,0 |
| ④ `ADATTATA` | 37,0 | 40,0 |

⇒ **Niente si è mosso**: ogni latenza è uguale o **più veloce** sotto contesa. Il testimone (che
pretende una dilatazione ≥ 15 % del ritmo visto dal client) **non è scattato**, e
`06-b41-verdetto.py` **ha rifiutato il verdetto**. ⭐ *«Non scrivo "0/18 sotto contesa GPU": sarebbe
l'etichetta senza la cosa»* — ed è esattamente il motivo per cui quel testimone è stato scritto.

⭐ **E si sa perché**: a riposo il ritmo è 55 ms ≈ **18 fotogrammi/s**, e lo detta **la scena** (un
terminale che scrive l'ora ogni 50 ms), non il codificatore. A 18/s di 1280×800 il prodotto chiede
all'iGPU circa **un cinquantesimo** di quel che chiedono i cinque carichi. ⇒ **La contesa è vera
sull'iGPU, ma in questa scena il prodotto l'iGPU quasi non lo usa.**

#### ⛔ Che cosa cambia per §7.1: **una causa è ESCLUSA con la misura**

Il **4/18 del 16 agosto** resta **non riprodotto**, ⛔ e adesso si sa che **non è la sola contesa
sull'iGPU**. Non si promuove a «curato», e non si promuove a «spiegato».

⭐ **E dove il segnale c'è, indica un altro imputato**: la latenza ② ha **13 e 17 campioni oltre il
tetto** su ~57 in **tutt'e due** le metà — cioè un quarto delle richieste al produttore **senza
risposta da Mutter entro un secondo**. È la stessa firma del 16 agosto (`NON_ORA` mediana 22 ms e due
casi a 3 000). ⇒ ⏳ **La prossima ipotesi è la contesa sul COMPOSITORE e su PipeWire — cinque
sessioni — non sull'iGPU.** Quella scena non è stata costruita.

#### ⛔ E col metro sano, il «5 guasti su 5» non regge

`[M]` Certificatore rifatto sotto contesa, carico 2,78, col **giro sano come metro** e la marca dopo
l'accensione:

```
SANO   adattate=10 non_ora=0 ms_mediano=47,45 fotogrammi=169 tela_nuova=10 non_spediti=0
G1 · G2 · G5   ATTESO-CONFERMATO      (regola sul sano = False)
G3  ⛔ ATTESO-SMENTITO      tela_nuova_dal_palco = 1, e la regola ne pretende 0
G4  ⛔ NON-DISCRIMINANTE    la regola è vera ANCHE sul sano
⇒ CONFERMATI 3 · SMENTITI 1 · NON DISCRIMINANTI 1
```

- **G3** è il difetto previsto: la terza clausola era vera **gratis** perché la marca scaduta
  rendeva vuota la finestra del registro. ✅ **Chiuso il 22 agosto, e la strada era una sola**: vedi
  §5.9;
- **G4**: §5.2 lo diceva già a parole («atteso verde per costruzione»); ⭐ adesso **lo dice il banco**,
  invece di contarlo fra i confermati;
- ⭐ **e G1 distingue ancora** col carico acceso (`regola sul sano = False`), che era il dubbio del
  coordinatore. ⚠ Col limite dichiarato: **questa** contesa al prodotto non arriva.

#### ⭐ E il rimedio a `registro.c` è verificato da un terzo

`[M]` sul giro sotto contesa: **18 righe senza marca su 12 882**, e **tutte e 18 sono di `libopus`**,
cioè di ffmpeg — **zero righe nostre spezzate**. Contro **23 su 28 035** (di cui 3 diventavano eventi)
sul registro del 16 col codice vecchio.

⛔ **E ha smascherato un difetto dell'attrezzo che conta**: chiamava quel numero *«intestazione persa
nell'intreccio»* — una **causa**, su un attrezzo che vede solo un **effetto**. ⇒ Avrebbe accusato
`registro.c` di un intreccio che non c'è più: **il rosso all'imputato sbagliato, dentro l'attrezzo
che dovrebbe smascherarlo.** Adesso separa «righe senza marca» da «**eventi** che ne arrivano», che è
l'unico numero che sposta una latenza.

#### ⛔ E il difetto peggiore della finestra è dell'autore, che l'ha dichiarato per primo

`misura` copiava i file JSON **del 16 agosto** come se fossero il giro appena fatto: sei giri nati da
**tre file di cinque giorni prima**, con dentro un ritmo perfettamente plausibile. ⭐ È stato visto
**solo** perché le due metà erano identiche **byte per byte**. ⇒ Curato: si cancella prima, si
raccoglie solo quel che è **più nuovo di una marca presa un istante prima**, e **zero giri raccolti
= ci si ferma**.

### 5.9 · ⭐⭐ 22 agosto 2026 — **G3 chiuso, e i numeri «non ricalcolabili» rifatti da capo**

#### ⛔ La terza clausola di G3 non era sbagliata di uno: **era irraggiungibile da un giro che misura**

`tela_nuova_dal_palco == 0` poteva diventare vero **solo se lo strumento non aveva guardato** — un
giro senza fotogrammi non si misura affatto (esce 5), e un giro con almeno un fotogramma ha
**sempre** la riga di nascita. ⇒ ⛔ **Era la macchina del falso verde scritta dentro l'atteso**, e
c'era **dal primo giorno del banco**: il difetto della marca scaduta (§5.6) non la creava, la
**realizzava**.

`[M]` La riga «TELA NUOVA DAL PALCO» del giro di G3 è la **riconciliazione di nascita**, e **precede**
il primo `ADATTA_TELA` — riprodotto due volte, a otto ore e a carichi diversi: **476 ms prima** il
21 agosto (carico 2,78), **461 ms prima** il 22 (carico ~0,7). Il figlio nasce al ripiego
1920×1080 e il palco **nasce** — non si ridimensiona — a 1280×800.

⭐ **E «completare il guasto» è ESCLUSO con la prova, non scartato a gusto**: quella riga non passa da
`cattura_ridimensiona()`, quindi spegnerla vorrebbe dire un secondo guasto sotto un nome solo (che
l'innestatore **vieta**), nel punto che è già di G5, e toglierebbe a G3 la scena. ⇒ **Le due strade
non portavano a lavori diversi: una delle due non esisteva.**

⭐⭐ **E la distinzione che la clausola serve REGGE**, che era la domanda vera: senza di essa G3 e G1
avrebbero la **stessa** regola, e il controllo positivo direbbe che il banco vede *un* problema
invece di *quel* problema. `[M]` stessa ora: **G1 = 8** (il palco obbedisce, la risposta si perde) ·
**G3 = 1** (al palco non arriva niente) · **SANO = 10**.

⭐ **E il `== 1` cade dalla parte giusta**: uno strumento cieco conta 0 ⇒ regola **falsa** ⇒ **rosso**.
Il vecchio `== 0` cadeva dalla parte del verde. ⇒ **Ogni modo di fallire della regola nuova è rosso**
— ed è la forma che `LEZIONI.md` §1.20 chiede.

#### ⭐ Il numero vero: **4 confermati · 0 smentiti · 1 non discriminante**

`[M]` 22 agosto, carico **0,49-1,12** (⚠ **la contesa non c'è più**: il 2,78 di ieri notte era in
buona parte del banco stesso — va letto come *«a macchina quasi ferma»*), sorgenti di prodotto
**identici byte per byte** al deposito.

#### ⭐⭐ E i numeri **D** di §4.8, dichiarati «non ricalcolabili», sono stati **RIFATTI**

⛔ Non ricostruiti dai file vecchi — *quelli sono la trappola da cui nasce il problema* — ma presi da
**tre giri nuovi** sul codice sano, con gli attrezzi riparati e il loro controllo positivo superato
prima. Carico 0,30-0,48.

| | §4.8 (17 ago) | §5.6 (dai superstiti) | ⭐ **giro nuovo, 22 ago** |
|---|---|---|---|
| ① **la tela girata al palco** | 4 ms (n=10) | 4,0 (n=30) | **6,0 ms** (0-21, **n=27**) |
| ② Mutter | 39,5 ms | 35,0 (n=20) | **32,0 ms** (15-49, n=27) |
| ③ palco → spedita | — | — | **4,0 ms** (3-39, n=28) |
| ④ giro intero, `ADATTATA` | 44,5 · 10/10 | 43,5 (n=20) | **42,0 ms** (25-59, n=27) · **27/27** |
| `SESSIONE` → 1° fotogramma | 25 ms · 203-220 da montare | — | **14 e 26 ms** · **141 ms** da montare |
| scartati · fuori misura | 0 · 0 | — | **0 · 0** (30/30 `ADATTATA`, 9/9 primo alla misura nuova = chiave) |

⇒ ⭐ **Le tre latenze del riquadro D si riconfermano tutte entro pochi millisecondi, con n quasi
triplo.** Il buco di §4.8 si chiude: quel riquadro non è più un numero perduto.

⭐ **E la cura di `registro.c` regge anche qui**: 3 righe senza marca su 3 242, **nessuna nostra**.

#### ⛔ E il 22 agosto sera il numero è sceso ancora: **3, non 4** — e l'ha abbassato chi l'aveva scritto

*Chiusi anche i due rilievi della revisione (`R5` il sentinella, `R14` l'attrezzo che butta i conti),
e con la colonna nuova è saltato fuori un fatto che prima non si vedeva.*

⛔ **G5 è intermittente**: la sua regola vuole `non_spediti > 0`, e quel numero vale **1** — un solo
fotogramma scartato. Nel terzo giro è uscito **0** con lo strumento **non** cieco (67 righe della tela
viste) ⇒ `NON MISURATO`. ⚠ Prima sarebbe **sparito da tutte e tre le colonne senza una riga che lo
dicesse**: è la ragione per cui esiste la **quarta** colonna e la riconciliazione
`CONFERMATI + SMENTITI + ND + NON GIUDICATI = guasti chiesti`.

| | 05:44 | 06:16 | 06:21, scena verificata **singola** |
|---|---|---|---|
| G1 · G2 · G3 | confermati | confermati | **confermati** |
| G4 | non discriminante | non discriminante | **non discriminante** |
| G5 | confermato | confermato | ⛔ **NON MISURATO** |
| ⇒ | 4 · 0 · 1 · 0 | 4 · 0 · 1 · 0 | **3 · 0 · 1 · 1** |

⭐ *«Non scrivo 4: sarebbe scegliere i due giri che mi piacciono.»*

> 🔸 **Decisione del coordinatore su G5: si allunga il giro, NON si riscrive l'atteso.** L'atteso non
> è sbagliato — è **la scena a essere sotto-potenza**: una scena che produce *esattamente un* evento
> non prova niente in modo ripetibile. ⛔ Riscrivere l'atteso sarebbe **adattare il metro al
> risultato**, che è la strada che questa notte ha insegnato a non prendere.
>
> ### ⭐⭐ E allungando il giro è venuto fuori che **l'evento non si moltiplica**, e il perché vale più del guasto
>
> `[M]` Sei giri, dalla scena corta a una **cinque volte più lunga**: **799 fotogrammi, tutti
> inammissibili, e un solo annuncio**. Cinque volte l'attività nel registro, **lo stesso identico 1**.
>
> ⭐ **E si sa perché, dal sorgente**: la riga sta dietro un fondo che si riarma **solo quando cambia
> la coppia (tela in vigore, misura del fotogramma)** — e sotto quel guasto **non cambia mai**. Primo
> fotogramma: la riga esce. Dal secondo al 799°: identici, fondo già armato, **silenzio**. ⇒ È **una
> volta per sessione, per costruzione**.
>
> ⛔⛔ **Quindi il numero non è quel che il suo nome promette**: `non_spediti` non è *«quanti
> fotogrammi non sono partiti»*, è *«quanti annunci distinti di disaccordo»*. Il nome dice 799, il
> valore è **1** — la forma **E2**, e ⚠ **non l'aveva vista nessuno perché 1 è un numero che sembra
> sano**.
>
> ⛔ **E il conto vero il prodotto ce l'ha e non lo dice**: `w->video_saltati` si incrementa a ogni
> fotogramma, e `wt_video_conti()` saprebbe leggerlo — ⛔ ma **quella funzione non la chiama nessuno**
> (verificato: zero chiamanti in tutto `src/`). ⇒ È `LEZIONI.md` §1.20 **dentro il prodotto**: un
> contatore che nessuno confronta.
>
> 🔸 **Decisione: si fa uscire il conto vero.** Le altre due strade sono state scartate con la
> ragione: contare un'altra riga darebbe il numero giusto nel giro buono ⛔ **e un falso rosso** nel
> giro in cui il palco non parte; lasciare com'è costa zero ⛔ e lascia in giro **un nome che promette
> una cosa e ne dice un'altra**.
>
> ### ✅ **FATTO il 22 agosto — sedici righe di codice, e il fattore è 254**
>
> `wt_video_conti()` ha finalmente un chiamante, **accanto a quello dell'audio**. ⭐ E la scoperta che
> vale più della cura sta nel commento che l'accompagna: la riga dell'audio fu scritta il **17
> agosto** per la funzione **gemella**, **con queste stesse parole**. ⇒ La cura era stata applicata a
> **uno dei due gemelli**, e nessuno aveva guardato l'altro. 📖 `LEZIONI.md` §1.25.
>
> `[M]` Stessa scena, due binari, il guasto innestato solo nell'albero di costruzione:
>
> | | consegnati | **NON SPEDITI** | **ANNUNCI** |
> |---|---|---|---|
> | sano | 1 016 | **0** | **0** |
> | col guasto | 0 | **1 017** | **4** |
>
> ⇒ ⛔ **1 017 contro 4: un fattore 254.** Prima, il solo numero leggibile era quello degli annunci —
> e lo si chiamava «non spediti».
>
> ⭐ **E l'atteso scritto prima era sbagliato, ed è rimasto scritto**: diceva «annunci = 1», come nel
> giro che aveva aperto il caso. Ne sono usciti **4**, ed è giusto: il fondo si riarma a ogni coppia
> (tela, misura) nuova, e quella scena la cambia tre volte. ⇒ **Il numero degli annunci segue le
> misure distinte, non i fotogrammi** — che è esattamente la ragione per cui non poteva fare da conto.
>
> ⚠ Dichiarato e non fatto: «non spediti» somma **tre** cause. Spezzarlo sarebbe una seconda cura —
> ⭐ ma il nome **non mente**: sono davvero i fotogrammi che non sono partiti.

#### ⛔⛔ E la scena si raddoppiava in silenzio — **per la seconda volta stanotte, la stessa forma**

`pkill -f 'banco-P6-scena'` uccide **il terminale**, non il ciclo che scrive l'ora: il titolo **non è
nella riga di comando** del processo che sopravvive. ⇒ Ogni `scena-via` lasciava un ciclo vivo e ogni
`scena` ne aggiungeva uno — `[M]` **due cicli** dopo un solo spegni/riaccendi. ⚠ Su un banco che
misura millisecondi, **una scena doppia non è la scena dichiarata**.

⭐ Curato con la guardia giusta: `scena-via` pretende **zero** superstiti e `scena` pretende
**esattamente uno** — la guardia vecchia era `> 0`, **che lasciava passare il due**. E i numeri D
erano su **un** ciclo: verificato, non sperato.

⚠ **La stessa forma è stata trovata indipendentemente in `06-b42`**: è un modo di sbagliare del
deposito, non di un banco.

#### ⭐ E i numeri D **non cambiano** dopo la cura dell'accoppiamento

① accoppia ora **per chiave**; ④ resta per ordine, ⭐ **ed è una scelta dichiarata**: la chiave non
esiste (la riga della risposta porta la tela *in vigore*, che su un `NON_ORA` è quella **vecchia**, e
accoppiare per misura butterebbe via proprio i `NON_ORA` che i guasti cercano). ⇒ La protezione è a
monte. `[M]` Ricalcolati sugli stessi registri: **identici campione per campione**, e si sa **perché**
— in quel giro `GIRATA 27 = CHIESTA 27`, zero spaiate, quindi chiave e ordine coincidevano.
⛔ **Ma è una proprietà di quella scena, non del codice vecchio**: gli altri due giri non hanno quella
garanzia.

#### ⏳ E due cose dichiarate invece che curate

- ⚠ **il valore «1» è legato alla scena, e nessuno l'aveva detto**: esiste perché il figlio nasce al
  ripiego 1920×1080 mentre la sessione del giro è 1280×800. Una scena che aprisse **proprio** a
  1920×1080 non avrebbe la riga di nascita, e l'atteso non varrebbe. ⇒ Adesso l'atteso **nomina il
  giro e la ragione**, invece di portare un numero nudo;
- ⚠ `parlantina-c-e` dà un **falso rosso sul primo giro dopo un `accendi`**: legge il registro intero,
  che `accendi` azzera. ⛔ Falso rosso, quindi direzione sicura — **dichiarato, non curato**.

### 5.10 · ⛔⛔⭐ 22 agosto — **il secondo di grazia contro il prodotto, e l'arbitro da solo NON vede l'indulgenza**

*I giri 6 e 7 di `06-b38-tela.sh`, mai puntati contro il server. `[M]` porta 7721, **quattro giri
interi 7/7 verdi**, carichi 1,16 · 1,51 · 1,57 · 2,58.*

| | giro 6 — **oltre** | giro 7 — **dentro** |
|---|---|---|
| `dt` registrato | **1 501 ms** | **251 ms** |
| il server | `CONGEDO 0x0b ERRORE_PROTOCOLLO` | ⭐ la sessione **regge** |
| l'arbitro | «oltre il secondo — e il server ha **congedato**» | ⭐ «**NON è giudicabile** da questa registrazione» |
| ⭐ **dove è finito il puntatore** | **da nessuna parte** | **(799,599)**, l'ultimo pixel della tela nuova |
| il filo | — | **`input = 1`** nel fotogramma (§6.2) |

⭐ La coordinata **non è scelta a mano**: si manda l'ultimo pixel della tela *precedente*, che **deve**
saturare esattamente su `(799,599)`.

#### ⭐ L'asimmetria degli orologi non è più un ragionamento: è una tabella

> **9 coppie su 9: il server misura di più, fra +11 e +25 ms** (LAN, carico 1,0-1,6).

⇒ Un caso «dentro» a 0,99 s sarebbe stato **1,01 s per il server**: rosso su un prodotto che ha
ragione. ⛔ La tabella sta nel banco **col divieto di usarla per avvicinarsi al confine**.

#### ⛔⛔ «L'arbitro dice conforme» non è una misura

Con un **server guasto apposta** (`TELA_GRAZIA` 1 000 → **60 000 ms**): il puntatore a 1 501 ms viene
**iniettato**, e ⛔⛔ **il validatore esce 0 e dichiara CONFORME** — onestamente, perché §7.1 lo fa
concludere **solo** se il server parla ancora sul canale di controllo, e **un server indulgente che
tace non gliene dà l'occasione**. ⭐ Il banco invece esce **1 su cinque righe rosse**, e il settimo
giro contro lo stesso server guasto resta **verde**, com'è giusto: **specifico, non paranoico**.

⇒ È la forma più forte di *«conforme non è funziona»* che questa fase abbia prodotto.

⛔ **E un difetto del banco della specie peggiore**: confrontava il puntatore con l'**ultimo**
`TELA(ADATTATA)` del file invece che con **quello che lo precede** ⇒ `dt` **negativo**, che cade sotto
il secondo, cioè nel ramo «non giudicabile». **Un puntatore oltre la grazia sarebbe stato dichiarato
dentro.** L'ha trovato il controllo positivo.

### 5.11 · ⛔⛔⭐ 22 agosto — **la «firma di Mutter» di §5.8 era un artefatto della scena**

*Il seguito della contesa: costruita la scena a cinque sessioni, ⛔ e la premessa è caduta prima della
finestra.*

`[M]` **18 giri incatenati, ZERO contesa**, carico 1,57 → 2,91: la latenza ② dà **17 campioni oltre il
tetto su 62**. ⛔ §5.8 ne aveva **13 e 17 su ~57** e li leggeva come *«un quarto delle richieste senza
risposta da Mutter entro un secondo, la stessa firma del 16 agosto»*.

⭐ **Il meccanismo, e chiude il caso**: ② accoppia **per misura chiesta**; la prima di due richieste
incatenate riceve `NON_ORA` (§7.1), quindi **il produttore non consegna mai una tela a quella
misura**, e la richiesta si accoppia con quella di un giro **successivo** — oltre il secondo. **Una
per giro.** ⭐ Controprova su 5 giri: **15 richieste, esattamente 5 spaiate ed esattamente 5
`NON_ORA`**. ⇒ Ed è anche il motivo per cui §5.8 la trovava **identica nelle due metà**: è quel che la
scena fa **per costruzione**.

#### ⭐⭐ E gli stessi 18 giri quieti danno **0 rotti su 18 — a carico PIÙ ALTO del 16 agosto**

Carico **1,57-2,91** contro lo **0,90** che §4.8 registra per il giorno del 4/18. ⇒ Si misura
«quieto» **sopra** il carico del giorno che produsse il difetto, e si ottiene **0/18**.

#### ⭐ E un contendente rende il compositore **più veloce**, non più lento

`[M]` sonda indipendente sul ciclo principale di Mutter, con client attaccato in tutt'e due i casi:
mediana **1,47 → 0,64 ms (0,44×)**, p95 **5,56 → 2,59**. ⇒ La certificazione a cinque sessioni
**fallirebbe**, e il banco rifiuterebbe il verdetto — come ha già fatto quello della GPU.

⇒ 🔸 **Scelta del coordinatore: la finestra a cinque sessioni NON si spende.** Su raccomandazione
avversariale dell'autore stesso: il 4/18 è una differenza di **esito**, e `NON_ORA` è **una corsa con
`cattura_ridimensiona()`** — la finestra in cui si ribalta si misura in **millisecondi, non in
carico**, e i 18 giri erano **tutti a 30 ms**. ⏳ La strada che resta è **setacciare l'intervallo**
(10-60 ms, molti giri per punto): costa la CPU di una sessione sola e **non disturba nessuno**.

⭐ **E la sonda del compositore è certificata**: `SIGSTOP` di 300 ms a `gnome-shell` ⇒ la sonda
registra **290,6 ms**. Prova che guarda **il compositore** e non altro.

### 5.12 · ⭐⭐ 22 agosto — **il colore dentro la sessione: sono gli STESSI PIXEL, byte per byte**

*L'ultimo anello che mancava al colore: non dal flusso al vetro, ma **dal desktop al vetro**.*

⭐⭐ **Zero canali diversi su 2 704 104**, confronto **byte per byte** fra quel che l'applicazione
dipinge e quel che il codificatore riceve.

| punto | che cosa aggiunge | medio | peggiore |
|---|---|---|---|
| dipinto → **catturato** | la cattura di Mutter | **0,000** | ⭐ **0,000** |
| dipinto → **flusso** | + conversione nostra + H.264 QP 26 + 4:2:0 | 0,334 | 3,005 |
| dipinto → **vetro** | + decodificatore hardware di Firefox | 0,342 | 2,981 |

⭐ `vetro − flusso ≤ 0,03`: **il decodificatore del browser non aggiunge nulla di misurabile** —
conferma indipendente dello 0,51 di §1.13-ter, presa **dall'altro capo**. E il residuo di ~3 livelli
non è nelle luci: **17 canali su 1 029 oltre 2,0, tutti sulle rampe di croma**, cioè il giro
RGB→YUV 4:2:0→RGB.

#### ⭐ E le tre trasformazioni sospettate, separate una per una

| | esito |
|---|---|
| **Night Light** a 1700 K, verificato attivo dal demone | ⭐ `[M]` **non entra**: 0 byte diversi |
| **effetti dello shell** | ⛔ **entrano eccome**: la *lente* dà **255 livelli**, e ⛔⛔ **la panoramica delle attività** ne dà **221,75** — un banco meno attento l'avrebbe messa in tabella come «difetto di colore» |
| **profilo ICC del compositore** | ⏳ `[?]` **non misurato**: `colord` non parte su questa macchina, quindi non c'è niente da accendere. `[R]` viaggia sulla stessa strada di Night Light, ma è **deduzione** |

⭐⭐ **E lo zero di Night Light vale perché la lente è passata**: senza quel controllo, uno zero sarebbe
indistinguibile da un banco cieco.

⭐ **E per il prodotto la questione è chiusa strutturalmente**: `sessione.c` toglie `--virtual-monitor`
e l'unico monitor della sessione è quello che monta la nostra cattura ⇒ non c'è scanout, non c'è
monitor fisico, non c'è dispositivo colore: **lo «schermo» della sessione È lo stage composto, e lo
stage composto è quel che catturiamo.**

⛔ **E il difetto del banco, dichiarato per primo**: il controllo positivo della lente **non si
accendeva** — un `echo` con apici dentro rompeva il comando remoto e **nessun `gsettings` girava**. Il
giro ha misurato «nessuna differenza» **credendo di avere l'ingranditore acceso**, cioè esattamente la
cecità che quel controllo doveva escludere. ⇒ Adesso il banco **muore** se la rilettura dal dconf non
dice quel che ha chiesto.

### 5.13 · ⭐⭐ 22 agosto — **il tetto del posto è 30 secondi, non 75** — e la frase di §5.3 sulla scheda congelata è falsa

*La `[?]` che mordeva tutti i giorni: «il posto della sessione è uno, e quello di prima resta
attaccato per una ventina di secondi» era folklore. `[M]` porta 7801, `provar7`, GNOME headless vero,
carico 0,23-1,40.*

| il client se ne va… | posto lasciato | un altro client entra |
|---|---|---|
| **congedo pulito** | ⭐ **5 ms** | subito |
| connessione chiusa senza congedo | **7 ms** | subito |
| **ammazzato** (presa chiusa) ×4 | 30,0 · 30,5 · 30,0 · **31,1 s** | idem |
| **congelato** (buco nero) ×3 | 31,1 · 31,2 · 30,0 s | idem |
| ⛔ **vivo sul filo, muto su RCP** | ⛔ **mai** | ⛔ **26 bussate su 26 respinte in 745 s** |

**Peggiore misurato: 31,2 s.** ⛔ E morire «male» non cambia niente: presa chiusa (con ICMP) e presa
muta danno gli stessi numeri — **ngtcp2 non reagisce all'ICMP**.

#### ⛔⛔ E la frase di `SPECIFICHE.md` §5.3 sulla scheda congelata è **falsa sul filo**

*«Una scheda congelata tace, quindi si stacca»* — ⛔ no: il server accende un **PING ogni 10 s**, lo
stack QUIC del client **risponde da solo** senza che la pagina esista, e ogni risposta rinnova la
vita. ⇒ **Il posto non si libera mai.** `[M]` 26 su 26 in 745 s. ⚠ Il prodotto conta i **pacchetti**,
non i byte di RCP — ed è una scelta giusta e documentata, ⛔ ma **non è quel che §5.3 racconta**.

#### ⭐ La riga per chi scrive banchi — è la cosa che serviva a tutti

> ⛔ **Dopo che un client se n'è andato male, prima di 35 secondi non riprovare.**
> ⛔⛔ **E se il suo processo è ancora vivo, 35 s non bastano: il posto resta occupato fino a mezz'ora.**
> Si verifica con `pgrep`, non con `pkill`.
> ⭐ **Ma quasi mai serve aspettare**: se il server è tuo, **riaccendilo** — i posti stanno nella
> memoria del processo, la sessione grafica vive fuori: `[M]` il primo attacco dopo un riavvio arriva
> a `SESSIONE` in **1,03 s**. ⭐ E se il client è tuo, **fallo congedare**: **5-7 ms**.

#### ⛔ E le strade sono DUE, con lo stesso numero — è il meccanismo dietro i falsi rossi

In 4 distacchi su 7 il posto l'ha lasciato **l'orologio del silenzio**; negli altri 3 la **morte della
connessione QUIC** (30,00 s esatti). ⚠ **Quale arrivi prima è testa o croce**, e lasciano **righe di
registro e stati diversi**. ⇒ Un banco che aspetta la riga «staccato per silenzio» per sapere che il
posto è libero **è rosso una volta su due**.

⭐ **E il controllo positivo, senza cui i 30 s non varrebbero niente**: con l'orologio dell'inattività
accorciato a 25 s lo stesso caso ha lasciato il posto a **19,8 s** con un congedo diverso ⇒ il banco
**sa vedere** un rilascio a un'ora diversa da 30.

⚠ **E quel che manca, dichiarato dall'autore**: nessun browser. L'ipotesi che lascia in eredità è che
i «~75 s» fossero **~45 s di Firefox che non muore + 30 s del prodotto**. Si chiude in un minuto, con
un browser in mano.

#### ⏳ Quattro cose del prodotto trovate per strada, non curate

| | |
|---|---|
| ⛔ `2 = RIPRESA` **non esce mai** | il byte è una **costante 1** nell'unico punto che costruisce il messaggio. `[M]` 12 riattacchi sullo stesso figlio: **stato 1, sempre**. È la forma **E1** ⇒ chi scrive banchi **non può** usarlo per sapere se ha un desktop nuovo |
| ⛔ le **due strade** con lo stesso numero | sopra: due righe e due stati sotto lo stesso fatto, in gara |
| ⛔ il **client vivo tiene il posto** | fino alla mezz'ora dell'inattività — misurato ≥ 745 s |
| ⏳ `[?]` **il desktop immortale** | `presenza_segna()` è chiamata **da un posto solo**, quello che riceve l'input ⇒ chi si attacca e **non tocca niente** non entra fra i presenti e **l'orologio dell'abbandono non parte**. Se è vero, ogni banco che si attacca senza digitare lascia un desktop da **477 MB** che non muore mai — ed è così che una macchina con otto banchi si riempie. ⛔ **È una lettura del codice, non una misura**: il giro che doveva provarla è saltato |

### 5.14 · ⛔ 22 agosto — **un'etichetta sbagliata ha fatto credere all'utente che una funzione tolta fosse tornata**

> *«Avevo già detto che il ridimensionamento dinamico era fuori dal progetto, e tu lo hai
> reintrodotto.»* — l'utente, leggendo un rapporto del coordinatore.

⭐ **Nel prodotto non è tornato**, verificato: il codice lo dichiara uscito in **otto punti**
(*«uscito»*, *«il fondo non c'è più»*, *«qui non parte»*), e il pezzo è stato **tolto**, non messo
dietro un interruttore. L'unica cosa che accade ridimensionando la finestra è che **l'immagine si
riscala**, che è il comportamento approvato.

⛔ **Ma il NOME è tornato**, e nei rapporti al posto peggiore: la prima delle quattro latenze di §5.6
e §5.9 era etichettata **«ridimensionamento a caldo»** e misura tutt'altro — il tempo fra la
richiesta **girata al palco** e la richiesta **arrivata al produttore**, sul cammino di `ADATTA_TELA`,
cioè quello che ogni client percorre **attaccandosi**. Una cosa che c'è, e deve esserci.

⇒ Chi leggeva *«ridimensionamento a caldo: 6 ms»* concludeva che la funzione fosse tornata.

⚠ **Ed è la stessa forma di difetto che questa notte ha corretto sei volte nei banchi** — *un nome
che promette una cosa e ne dice un'altra* — commessa dal coordinatore **nei documenti**. ⛔ Che sia
un'etichetta e non del codice non la rende meno grave: **i documenti sono quel che resta**, e un
nome sbagliato in una tabella di misure sopravvive a tutti noi.

⭐ **E a trovarla è stato l'utente leggendo, non un banco.** Nessuno dei controlli automatici poteva
vederla: nessun banco confronta il **nome** di una misura con quel che la misura fa.

⇒ **Corretta ovunque**: nel banco (`06-b35-tempi.py`, col racconto accanto) e nelle tre tabelle di
questo documento. La misura si chiama adesso **«la tela girata al palco»**.

#### ⭐ E il vocabolario, dato dall'utente

> *«Si chiama **re-scaling**.»*

⇒ **Sono due cose diverse e vanno chiamate con due nomi diversi**, sempre:

| | |
|---|---|
| ⛔ **ridimensionamento dinamico** | il desktop remoto **cambia misura** mentre l'utente trascina il bordo. **Fuori dal progetto dal 17 agosto**, e non si riapre |
| ⭐ **re-scaling** | l'immagine si **riscala** dentro la finestra, e **le finestre del desktop non si muovono**. È quel che il prodotto fa, ed è approvato |

⚠ Chiunque scriva «ridimensionamento» senza specificare quale dei due **sta per rifare questo
errore**.

### 5.15 · ⛔⛔⭐ 22 agosto 2026 — **`06-b37` rifatto: i quattro falsi verdi curati, e cinque guasti che li accendono**

*Il banco della sottofase 6.5 era l'unico dei sei **senza nessun guasto innestato** (§5.5). ⇒ Adesso
ce l'ha: `banchi/06-b37-guasti.py` + `banchi/06-b37-guasti.sh`, **7 casi su 7 su Chrome 151 e 7 su 7
su Firefox 140esr — 14 su 14** — ogni guasto rosso **nel caso dichiarato prima**, e la stessa scena
verde sul prodotto. Carico della macchina durante le certificazioni: `load average` **0,34 → 2,10**,
un giro intero **9 min 52 s** (Chrome) e **12 min 40 s** (Firefox).*

#### ⭐ I cinque guasti, e che cosa accendono

| | il guasto, in una copia di `src/pagina.html` | la scena che lo accusa | il falso verde che smaschera |
|---|---|---|---|
| **G1** | la tela chiesta è **30 px più stretta** della finestra | `numeri` A5 · `sfora` · `pixel` X1-bis | ⛔ nessuna scena aveva un **limite inferiore**: 12 combinazioni su 12 restavano verdi |
| **G2** | la guardia `if (tela_spenta)` è **aggirata** | `voce` **V5** | ⛔ la spia **sostituiva** `chiedi_tela`, e la guardia sta **dentro** la funzione sostituita |
| **G3** | `misura_vista()` torna al **`Math.round`** di prima della cura | `sfora` a dpr 1,5 (**«TAGLIATO 979 px su 980»**) | ⛔ A6 era un'**identità**: la «verità esterna» si semplificava in `round(cw·dpr)`, cioè nello stesso arrotondamento del guasto ⇒ **il difetto vero che questa fase ha curato passava sotto A6 senza toccarlo** |
| **G4** | l'immagine è dipinta **50 px fuori posto** nel buffer, e `dipinta.x` dice ancora 0 | `coordinate` **C0** | ⛔ l'origine era **sottratta per costruzione** |
| **G5** | la **parità** di `tela_da_chiedere()` è tolta | `numeri` A3 (63 tele su 63) | ⛔ il lato dispari era impossibile **per costruzione** e non veniva mai provocato |

#### ⭐⭐ E la controprova di G4 sta dentro il banco, per sempre

`06-b37-coordinate.py` misura **ogni punto due volte** — con l'origine vera e con la formula
vecchia — e stampa i due scarti accanto. `[M]` con G4 innestato, Chrome, 9 punti su 3 scene:

| | alto-sinistro | centro | basso-destro |
|---|---|---|---|
| **metodo nuovo** | **+51** · **+50** · **+51** | **+50** · **+50** · **+51** | +0 · +0 · +0 *(satura al bordo)* |
| ⛔ **metodo vecchio** (che sottraeva l'origine) | **+0** · +0 · +0 | **−1** · +0 · +0 | −1 · −1 · +0 |

⇒ ⛔ **Il metodo vecchio, con l'immagine spostata di 50 pixel, sarebbe stato VERDE su tutti e nove i
punti.** Non è più un'ipotesi della revisione: è misurato.

#### ⛔⛔ E TRE DIFETTI NUOVI DEL BANCO, che nessuno aveva ancora nominato

1. ⛔⛔ **Le quattro scene sui pixel non misuravano più NIENTE.** Mettevano il fotogramma con
   `schermo.deposito = c; schermo.componi()`, ⛔ ma `componi()` comincia con
   `if (this.bm) { … return false; }` e `this.bm` c'è su tutt'e due i motori da quando la tela è
   passata a **`bitmaprenderer`** (`DECISIONI.md` §5.4). ⇒ `[M]` 22 agosto: `sfora` su Chrome,
   **12 fotografie su 12 senza nessun marcatore**. ⭐ I banchi si sono comportati bene — dicevano «i
   marcatori non si trovano» invece di uno zero — ⚠ ma **gli esiti del 16 agosto nel deposito sono di
   prima di quel cambiamento**, e §4.3-bis li dichiarava ancora buoni. ⇒ Curato: il fotogramma passa
   da **`schermo.mostra()`**, la funzione che riceve i fotogrammi veri, e ogni riga di esito dichiara
   la **`strada`**;
2. ⛔ **`numeri` era ROSSO PER SEMPRE con un fattore del dispositivo forzato**: A1 confronta due
   zoom, con `FATTORE=` ce n'è uno solo, e quel caso faceva `guasti += 1`. ⇒ Per questo la scena non
   l'aveva mai lanciata nessuno a dpr 1,25 o 1,5. Una domanda **non posta** adesso si dichiara e non
   conta come risposta sbagliata;
3. ⛔⛔ **il banco riempiva il disco della macchina — e il disco è di tutti.** `[M]` un giro intero
   scriveva **1,5 GB** di fotogrammi grezzi (1600×1000×3 = 4,8 MB l'uno, **63 calibrazioni nella sola
   scena `numeri`**) in `/tmp`, che qui è un **tmpfs da 3,8 GB condiviso con altri otto agenti**.
   L'ha portato al **100 %**, e il giro dopo è morto con *«No space left on device»* — ⚠ su un banco
   altrui sarebbe morto **senza che nessuno capisse perché**. ⇒ Curato: i pixel si leggono da una
   **pipe**, su disco ci finiscono solo con `B37_FOTO=tieni`, e la riga di esito porta `null` invece
   di un percorso che non esiste;
4. ⚠ **e una quarta cosa, che non era un difetto ma una flaky, e valeva tre guasti**: `voce` su
   Firefox lanciata subito dopo un'altra scena moriva perché **il primo comando scadeva a 20 s** —
   la pagina si era annunciata, ⛔ ma il ciclo che chiede i comandi non era ancora partito. Il
   certificatore l'ha letta come *«il giro SANO è rosso»* e ha **rifiutato di certificare tre
   guasti**: `[M]` primo giro su Firefox **4 confermati su 7**, secondo giro **7 su 7**.
   ⇒ Curato: `aspetta_canale()` — la pagina che si annuncia e il ciclo che risponde sono **due cose
   diverse**, e adesso si aspetta la seconda. ⭐ E il certificatore si è comportato bene: ha detto
   «non certifico» invece di contare quei tre come confermati.

#### ⭐⭐ E adesso `bash banchi/06-b37-lancia.sh tutti tutte` gira davvero

`[M]` 22 agosto 2026, 09:48, carico `0,57 → 0,64`: **14 giri di scena in una sola invocazione**
(sette scene × due motori), **80 verdetti verdi e zero rossi**, `windows` compresa — che si porta
dietro il suo schermo 2600×1000 e il suo fattore 1,25 senza toccare le altre sei.
⇒ ⛔ Cade la riga *«finché non è curato, si lancia una scena per volta»*.

#### ⚠ E su Gecko c'è una riga in più da scartare, dichiarata invece che scartata in silenzio

Sotto il suo minimo **Firefox non stringe il riquadro di impaginazione**: `clientWidth` resta
grande, la finestra X si stringe lo stesso, e quel che c'è dentro **lo taglia il bordo della
finestra**. `[M]` la striscia di calibrazione esce fino a **210 px** più corta di
`clientWidth × dpr`. ⇒ **12 righe su 63** non sono una scena e si scartano — ⛔ ma il confronto che
le scarta è fra **due numeri del browser** (`clientWidth × dpr` e i pixel), non fra il banco e il
prodotto: nessun difetto della pagina può nascondersi lì, perché `misura_vista()` non entra in
nessuno dei due membri. ⇒ Su Firefox il denominatore di `numeri` è **48 righe su 63**, e le 12
scartate si stampano una per una.

#### ⚙ Che cosa è cambiato nel banco, file per file

| | |
|---|---|
| ⭐ `06-b37-guasti.py` · `.sh` | **nuovi**: i cinque guasti con l'ancora verificata (7 ancore su 7 vive, molteplicità 1) e il certificatore, che pretende **il sano verde**, **il guasto rosso** e **la frase dichiarata prima** — ⛔ non un rosso qualunque (è il rilievo 2 di §5.5 su `06-b33`) |
| `06-b37-comune.py` | la **calibrazione sui pixel** (due strisce a posizione fissa, `ox`/`oy` e la vista in pixel del dispositivo, con **due maschere** perché a dpr non intero il bordo cade a mezzo pixel) · `mostra()` per la strada del prodotto · la **marca del giro** su ogni riga di esito |
| `06-b37-numeri.py` | A2 e A6 **riscritte** su quella verità esterna, A5 **bidirezionale**, la tolleranza di A1 **derivata** invece che scelta |
| `06-b37-sfora.py` · `-pixel.py` · `-windows.py` | il **limite inferiore** (`W − ceil(dpr) ≤ disegno`), la strada del prodotto, il mezzo pixel **contato** |
| `06-b37-coordinate.py` | **C0 · l'origine** e la controprova col metodo vecchio |
| `06-b37-voce.py` · `-modi.py` | il **testo vero** di `chiedi_tela` estratto dal prodotto e installato con una `eval` diretta su un canale finto ⇒ la guardia si attraversa, e l'osservabile è `canale.manda(TIPO.ADATTA_TELA, …)` |
| `06-b37-lancia.sh` | la **settima scena** in «tutte» (con il suo schermo 2600×1000 e il suo fattore 1,25) · il difetto dichiarato in §4.3-bis — *«dopo la prima scena il browser non si riapre»* — **curato**: si aspetta che tutto quel che tiene il profilo sia morto |
| `06-b37-strumenta.py` | estrae e verifica il testo di `chiedi_tela` (58 righe), e **fallisce rumorosamente** se l'ancora non c'è |

### 5.16 · ⭐⭐ 22 agosto — **tre proposte al prodotto: due RIFIUTATE con la misura, una smentita al contrario**

*Le proposte venivano da chi aveva esercitato `cattura.c` col palco finto. ⭐ Tutte e tre sono state
messe alla prova invece che attuate, e il risultato è più utile di tre cure.*

| la proposta | l'esito |
|---|---|
| *«`cattura_ridimensiona()` dichiara successo su un flusso che muore, e `figlio.c` non ha modo di saperlo»* | ⛔ **RIFIUTATA**: la premessa è falsa. `[M]` col ciclo vero del figlio, il guasto arriva a **8,1 ms** con **stato e causa dal produttore** — non è un timeout. ⭐ E un esito «morto» restituito dalla funzione sarebbe **verde per costruzione**: la morte arriva 2 ms dopo il ritorno |
| *«serve un accessore per la divergenza»* | ⛔ **RIFIUTATA**, e con tre misure: la sola scena che accende il campo dà un **falso allarme** (i «concessi» erano la richiesta di prima, non una concessione); i due accessori che esistono **bastano** e in più sanno dire «non ancora negoziato»; e la via del contatore **non regge** — due richieste incatenate producono **una sola** risposta, quindi i conti divergono per sempre |
| *«il ramo "concesso diverso da chiesto" non si raggiunge»* | ⭐⭐ **SMENTITA AL CONTRARIO**: si raggiunge, **43 colpi su 480 catene** |

⭐⭐ **E la smentita ha trovato un difetto di prodotto**: la riga di registro diceva *«la conversione
delle coordinate nasce sbagliata e il puntatore andrà altrove»* — ⛔ e nella **sola** scena che la
accende è **falso**. ⇒ *Un registro che attribuisce la causa sbagliata costa più di un registro
muto.* Riscritta: dice il fatto, nomina i **due** moventi possibili, e manda dove il verdetto si dà
davvero.

⚠ **E la guardia della divergenza resta un commento con un `gboolean` attaccato — ma adesso il codice
lo dice**, invece di lasciar credere che qualcuno la legga.

⛔ **E un difetto del banco che l'autore ha dichiarato per primo**: il suo caso 6 *«stampava un numero
che non aveva letto»* — due zeri scritti a mano nella riga al posto della misura. ⭐ *«È esattamente
il difetto che avrei segnalato a un altro.»*

⏳ **E un guasto vero lasciato aperto, non suo da curare**: `[M]` il rimontaggio chiede al palco **la
misura che l'ha appena ucciso**, e la chiamata **riesce 3 volte su 3** mentre il palco muore 300 ms
dopo — con l'attesa corta si sceglie un **cappio**, e nessuno se ne accorge. ⚠ Sul prodotto vero è
`[?]`, perché Mutter concede tutto sotto il tetto. È **dichiarato nel codice** accanto al ramo.

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
| ✅ ~~⛔ **il difetto è a monte, in Mutter**~~ · ⛔ **e la risposta è peggio della domanda** | **CHIUSA il 21 agosto 2026** `[R]`: il difetto è vero, **nessuno l'ha mai aperto**, e **non è corretto nemmeno nel `main` di oggi** — `remove_viewport_devices()` è identica carattere per carattere fra la 48.7 che gira qui e il ramo principale di agosto 2026. ⇒ Non c'è versione da aspettare: **la cura è nostra, su ogni Mutter**. Il seguito sta in §7.1-bis |
| ✅ ~~**le richieste incatenate, da rimisurare**~~ · ⛔ **e resta un buco peggiore** | rimisurate il 17 agosto: **0 rotti su 18** (§4.8). ⛔⛔ **Ma il controllo positivo non ha reso**: togliendo la cura sospetta escono **ancora 0/18** ⇒ *non si sa che cosa tenga questa scena*, e i **4/18** della 6.3 **non sono riproducibili** a macchina ferma. ⚠ L'unica differenza rimasta è la **contesa sulla GPU** (cinque codificatori sullo stesso iGPU): finché non si ricrea, ⛔ **il verde vale «sotto carico CPU», non «sotto contesa GPU»** |
| ✅ ~~**la cura del clic non è mai stata verificata dove vive**~~ | verificata il 17 agosto su un albero solo: il rilascio è dichiarato nel registro e **tutti i clic del secondo giro arrivano**, ⭐ col controllo positivo che riproduce il difetto **a comando** |
| ✅ ~~**tutti i millisecondi sono sotto carico**~~ | ripresi a macchina ferma (load 0,07-0,13): §4.8 |
| ⛔ **tre attesi di `06-b33` sono scritti per il mondo COL DIFETTO VIVO** | T3, R1 e R2 restano **rossi con la cura** e erano **verdi senza**: con il tasto già rilasciato prima del ricambio, le righe di dichiarazione non si scrivono perché non c'è più niente di premuto. ⇒ **Va corretto l'atteso del banco, non il prodotto** — ed è un banco nato ieri, quindi il difetto è di ieri |
| ✅ ~~⚠ **due attrezzi del banco 6.3 si rompono**~~ | **CURATI il 21 agosto** e certificati contro un calcolo a mano in `awk` (235 campioni, tutti coincidenti). ⭐ La causa non era negli attrezzi: era il **registro che si intrecciava** fra padre e figlio. 📖 §5.6 |

### 7.1-bis · ⭐⭐ 21 agosto 2026 — **la catena completa del clic che muore**, letta nel sorgente di Mutter

*Tutto `[R]`, dal sorgente di `reference-gnome/mutter` (tag **48.7**, commit `f4abb824`) — ⭐ e
`[M]` la macchina di prova monta **esattamente quella**: GNOME Shell 48.7, `libmutter-16-0`
48.7-0+deb13u1, `libei1`/`libeis1` 1.3.901-1. Nessuno scarto di versione da scontare.*

#### ⭐ PERCHÉ i dispositivi si ricreano anche senza `ADATTA_TELA` — il `[?]` del §4.6 ha una causa

`meta_screen_cast_virtual_stream_src_enable()`
(`src/backends/meta-screen-cast-virtual-stream-src.c:283`) chiama
`meta_eis_viewport_notify_changed()`. ⇒ **Ogni riabilitazione dello stream ricrea i dispositivi**,
cioè **ogni `cattura_risveglia()`** — ed è il «3 risvegli, 3 ricambi, zero `ADATTA_TELA`» di §7.1,
che non era un mistero ma quella riga. ⚠ Viene dalla **MR !4622**, entrata in **Mutter 48.5**: è
recente, e noi siamo dentro la finestra.

⚠ **E c'è un secondo moltiplicatore**: `add_logical_monitor_viewports()`
(`meta-remote-desktop-session.c:388`) fa `remove_all_viewports` **poi** `take_viewports`, e
**tutt'e due** emettono `viewports-changed` ⇒ **due giri di ricambio per ogni cambio di monitor**.

#### ⛔ Il difetto è PERMANENTE, non una corsa — e Mutter ha una rete che qui NON si può raggiungere

⚠ **Questa è la parte che rende la riga di §7.1 refutabile, e per cui prima non reggeva.** Chi legge
solo *«`remove_viewport_devices()` non passa da `drop_device()`»* può rispondere: *«ma Mutter
rilascia lo stesso in `dispose`»* — e ha l'aria di avere ragione, perché
`meta_virtual_input_device_native_dispose()` chiama `release_device_in_impl()`, che rilascia **tutti**
i bottoni e i tasti tenuti giù, con tanto di riga di diagnostica.

⛔ **Su questo cammino quella rete è irraggiungibile**, e la catena è di tre anelli:

1. il `ClutterVirtualInputDevice` muore **solo** con `meta_eis_device_free()`, distruttore della
   tabella `client->eis_devices`;
2. fuori dal disconnect, l'unico che toglie una voce da quella tabella è il ramo
   **`EIS_EVENT_DEVICE_CLOSED`** (`meta-eis-client.c:987`);
3. ⭐ `[R]` **su libei 1.3.901-1, che è la versione installata**: quell'evento lo genera **soltanto**
   una `release` mandata **dal client** (`eis_device_closed_by_client()` ← `client_msg_release()`).
   `eis_device_remove()` non lo genera **mai**: mette lo stato a `DEAD` e manda `destroyed`. E il
   client non deve nemmeno chiamare `ei_device_close()` su un dispositivo rimosso dal server — lo
   dice l'intestazione pubblica di libei, e il client di prova di Mutter infatti non la chiama.

⇒ ⛔⛔ **La voce resta nella tabella per sempre**, `release_device_in_impl()` non gira mai, e
`seat_impl->button_count[BTN_LEFT]` resta **1 per sempre**. Si sana **solo al disconnect**, che è
l'unico posto da cui passa `drop_device()` — ⭐ ed è esattamente il *«si guarisce solo riaccendendo
il server»* che §4.6 aveva misurato senza sapere perché.

⚠ **E `button_count[]` è del POSTO, non del dispositivo**: è la ragione per cui la cura potrebbe
essere molto più piccola di quanto sembri — un rilascio mandato da un dispositivo **nuovo** può
ancora far scendere il conto. ⏳ Da misurare, non da dedurre.

#### ⛔ La nostra cura di oggi copre l'altro cammino

`input_rilascia_tutto()` prima di `cattura_ridimensiona()` (`figlio.c:3964`) copre il **cambio di
geometria**. ⛔ **Non** copre `cattura_risveglia()`. ⇒ La «seconda porta» di §7.1 è aperta proprio
dove la cura non arriva.

#### ⛔ A monte: nessuno l'ha mai aperto, e non è corretto nel `main` di oggi

`[R]` cercato il 21 agosto 2026 sull'API di `gitlab.gnome.org/GNOME/mutter`: le issue con `eis` e
`libei`, le **15** merge request con `eis` nel titolo dal 2023 a oggi, e una ricerca su
`remove_viewport_devices` ⇒ **niente**. Idem `gnome-remote-desktop`.

⭐ **L'unico precedente è la prova migliore che l'asimmetria non è voluta**: la MR **!3809**,
*«backends/eis-client: Release buttons on device remove»*, fusa il 14 giugno 2024, corregge una riga
sola **dentro `drop_device` e solo lì**. ⇒ L'intento a monte è dichiarato nel titolo, e il cammino
del viewport lo viola.

⛔ **E non è corretto oggi**: scaricato `meta-eis-client.c` dal ramo **`main`** (agosto 2026, serie
50/51), `remove_viewport_devices()`, `drop_device()`, `update_viewports()` e `remove_device()` sono
**identici carattere per carattere** alla 48.7. ⇒ Non c'è una versione da aspettare né una
distribuzione già a posto: **la nostra cura serve su tutte**.

⭐ *(In più, a carico di Mutter e non nostro: è anche una **perdita di memoria** — la tabella tiene
un `eis_device_unref` come distruttore, quindi `struct eis_device` e `MetaEisDevice` restano vivi a
ogni ricambio, per tutta la sessione. Lo stesso vizio ce l'hanno `remove_abs_devices()` e
`remove_touch_devices()`.)*

#### ⏳ Che cosa resta, e costa poco

⛔ **Tutta questa catena è `[R]`, non `[M]`**: è codice letto, non misurato. La conferma decisiva è
una riga di diagnostica: con `MUTTER_DEBUG=eis,input`, dopo un ricambio di viewport **a bottone
premuto**, ci si aspetta `Dropping repeated press of button 0x110, count 2` **e l'assenza** di
`Releasing pressed buttons while destroying virtual input device`. ⚠ **Se comparisse la seconda
riga, tutta la lettura cade** — ed è per questo che sta scritta qui: una catena che non sa come
essere smentita non è una diagnosi.

`[?]` Se i manutentori lo considerino un difetto di Mutter o «cosa che deve gestire il client»: non
è deducibile dal codice. ⛔ **E non è stato aperto niente a monte**: è un'azione verso l'esterno, e
la decide l'utente.

### 7.2 · Le `[?]` di misura, dichiarate invece che estrapolate

- **il DeX e la GPU vera**: il mezzo pixel non arriva ai pixel su Xvfb ⇒ `[?]` **su GPU vera e su
  Samsung DeX**. ⛔ Il telefono ce l'ha l'utente: si chiede a lui, non si aggira;
- ⛔⛔ **E una delle tre `[?]` di `SPECIFICHE.md` §6.1-bis era stata SOSTITUITA in silenzio.** Le tre
  vere sono lo **zoom** (✅ chiusa il 22 agosto, con la tolleranza *derivata* invece che scelta), il
  **lato dispari** (✅ chiusa, con un guasto innestato come controllo positivo) e ⛔⛔ **«su DeX
  `screen` risponde con lo schermo esterno o col telefono?»** — che **non l'ha mai toccata nessuno**,
  perché il telefono è dell'utente. ⚠ Al suo posto il documento aveva messo **«il mezzo pixel»**, che
  è un'altra domanda: ⇒ una `[?]` sparita e una comparsa, senza che nessuno se ne accorgesse. 📖 §5.15;
- ⛔ **«conforme» non è «funziona»**: l'arbitro certifica i byte — *«un server che rispondesse
  `TELA(ADATTATA)` senza toccare il palco passerebbe tutti e cinque i giri»*. I pixel li misura
  un altro banco, e la distinzione va tenuta;
- ✅ ~~**il secondo di grazia curato e non misurato**~~ — **CHIUSO il 22 agosto**, e ⛔ **la ragione
  per cui sembrava impossibile era sbagliata**: la grazia parte dal `TELA`, **non dalla connessione**,
  quindi i 1500 ms della stretta di mano non c'entrano. 📖 §5.10;
- ✅ ~~**codice mai esercitato su Mutter**: il ramo «concesso diverso da chiesto» e
  `MISURA DIVERGENTE`~~ — **SMENTITO il 22 agosto**: ⭐ `MISURA DIVERGENTE` (oggi `cattura.c:608`)
  **si raggiunge dall'esterno** — `[M]` **43 colpi su 480 catene**, tre spazzolate su tre. ⛔ La porta
  non è il produttore, **è il tempo**: due ridimensionamenti incatenati — *l'utente che trascina il
  bordo* — e la risposta del primo torna quando la richiesta porta già la seconda. Finestra: fra
  **200 e 800 µs**. ⇒ È una corsa, ⭐ **ma una corsa che un banco programma**: si spazzola la distanza
  fra le due chiamate. ⚠ Resta non esercitato quello di `figlio.c` (oggi `:6764`): servirebbe un
  fotogramma vero, e il palco finto non ne accoda. 📖 §5.16;
- ✅ ~~**il posto si lascia dopo ~75 s** di silenzio, non i 30 di §5.3~~ — **MISURATO il 22 agosto:
  sono 30, e il «~75» non si riproduce.** 📖 §5.13;
- ✅ ~~**le coordinate in volo sono inarbitrabili da una registrazione**~~: dal 21 agosto `RCP.md`
  §11.1 registra il **tempo**, e la regola è collaudabile — ⛔ **in un verso solo**, e §5.10 racconta
  perché quel verso non basta;
- **`?video=worker` non esercitato**; **`aioquic` non è installato sul portatile** (il cliente si
  prova in locale solo con surrogati, e il banco lo dichiara);
- ⛔ **il ripiego su KWin resta non verificabile sul vero**: KDE è la fase 11. Il percorso di codice
  è provato **sull'ospite finto**, e la **riga di registro** che lo dichiara adesso è pretesa da un
  banco (`06-b36` casi 1-2) — che è quel che `SPECIFICHE.md` §6.3 chiedeva.

### 7.3 · ✅ ~~E i tre difetti che la decisione dell'utente rende urgenti~~ — **erano già chiusi, e il documento mentiva da cinque giorni**

> ⛔ **Questa sezione elencava tre difetti che il prodotto non ha.** Misurati sul vivo il 21 agosto
> 2026 (porta 7721, utente `provat6`, sessione GNOME vera con testimone dentro, carico 0,20-0,60):

| il documento diceva | `[M]` il prodotto fa |
|---|---|
| `hu` `tr` `gr` `ua` ricevono `SESSIONE_NON_SERVIBILE` | ⭐ **aprono la sessione**, tutte e quattro |
| `it(nonesiste)` apre la sessione | ⭐ **`0x0E SESSIONE_NON_SERVIBILE`** |
| `DISPOSIZIONE` a sessione aperta chiude la connessione | ⭐ **connessione viva**, `KEYMAP CAMBIATA → de [German]`, nessun messaggio sul filo |

⇒ Li aveva chiusi la cucitura del **16 agosto**: la domanda «esiste?» va a XKB
(`webtransport.c:1626` → `tastiera.c`), la variante ci entra perché `it(nonesiste)` non compila, e
`T_DISPOSIZIONE` ha il suo `case` (`rcp.c:6207`). ⚠ Nessuno aveva riletto questa sezione, ed è la
stessa specie di difetto di `fasi/07` §8: **un documento fermo a quattro giorni fa manda a cercare un
guasto dove non c'è**.

⭐ **E non ci si è fermati a «la sessione si apre»**, che è il metro che questa fase vieta: il
testimone dentro la sessione ha registrato **il carattere**, con l'atteso calcolato da `tastiera.c`
chiamato da fuori — `hu`→`ű`,`ő` · `tr`→`ğ` · `gr`→`α` · `ua`→`ї` · `de(T3)`→`‑`, **tutti arrivati**,
più il negativo (`it` non produce `ű`, e la riga che lo dichiara c'è).

#### ⛔⭐ Ma al loro posto ce n'era uno VERO: **la forma D1 sopravvissuta alla propria cura**

La cura del 16 agosto ha tolto l'elenco fisso di venti nomi, ⛔ **e davanti al gancio è rimasto un
secondo elenco scritto a mano: l'alfabeto ammesso nel nome**, che accettava solo `[a-z0-9]`.

`[M]` Chiedendolo al sistema **attraverso il prodotto**, su tutte le **590** coppie
disposizione/variante di `evdev.lst`: **589 si compilano**, e **nove hanno una maiuscola** —
`de(T3)`, `ie(CloGaelach)`, `ie(UnicodeExpert)`, `in(tamilnet_TAB)`, `in(tamilnet_TSCII)`,
`jp(OADG109A)`, `lk(tam_TAB)`, `ru(phonetic_YAZHERTY)`, `ua(macOS)`. ⛔ Sul filo ricevevano
**`0x0B ERRORE_PROTOCOLLO`** — che è **peggio** di `SESSIONE_NON_SERVIBILE`, perché dice *«il tuo
client è rotto»* e manda a cercare il guasto dall'altra parte del filo. E `it()` (variante vuota)
prendeva `0x0E` su una stringa **fuori forma**: i due guasti di §4.5 uniti.

⇒ **Curato** (`rcp.c:2155`, e il gemello allineato byte per byte): un solo
`disposizione_carattere_ammesso()` con l'alfabeto **identico** a quello di `tastiera.c`, più il
rifiuto della variante vuota. ⚠ Due controlli di forma scritti due volte davano due risposte sotto
la stessa etichetta: è la forma **E2**. La difesa non si allenta — punto, barra, virgola e
`../../etc/passwd` restano fuori. ⭐ Prezzo dichiarato: `IT` adesso passa la forma e riceve `0x0E`
invece di `0x0B`, ed è la risposta giusta (XKB distingue le maiuscole).

⭐ **Rosso→verde certificato** sulla stessa macchina: caso 8, **7 righe rosse su 17** col binario di
prima → **17 su 17** col curato; e quattro guasti innestati che accendono il caso dichiarato.



---

## 8 · Il giudizio dell'utente

*La fase si chiude su una misura giudicata dall'utente, non su un documento completo.
⛔ Non si scrive un verdetto che l'utente non ha dato.*

✅ **Uno c'è già, ed è del 16 agosto 2026**: **«il test su Windows lo dichiaro superato al 100 %»**
— dato sul prodotto vivo, da un terzo sistema client mai provato prima, con `dpr 1,25` e la finestra
dispari su tutt'e due i lati (§4.1 e §4.1-bis).

⏳ **Quel che aspetta il suo giudizio**: la scena del **trascinamento del bordo** e quella del
**clic tenuto giù** — le due che questa fase ha aperto — dopo la verifica congiunta a banchi fermi.

## ⛔⛔ 21 agosto 2026 — **Firefox per Android non ha WebCodecs**, e il messaggio nostro mentiva

*Prima prova su un telefono vero (Samsung DeX, Android 16). L'utente: «credo che abbiamo introdotto
una regressione per quanto riguarda Firefox su Android».*

⛔ **Non era una regressione.** `[M]` Dal registro del server, parole della pagina:

```
browser: Mozilla/5.0 (Android 16; Mobile; rv:154.0) Firefox/154.0
         · schermo 2560x1080 · dpr 1 · WebCodecs NON c'e'
sonda video · ⛔ HEVC: NON arriva al pixel — questo browser non ha WebCodecs
sonda video · ⛔ H264: NON arriva al pixel — questo browser non ha WebCodecs
congedo motivo=0x09 dettaglio=nessun codec condiviso
```

⇒ `VideoDecoder` **non esiste** su quel browser, e in `pagina.html` la strada verso i pixel è
**una sola**: zero occorrenze di `MediaSource` in tutto il file. ⚠ Con AV1 sarebbe finita identica —
il passaggio a H.264 (§1.13-ter) non c'entra, e la riga di `DECISIONI.md` che diceva «così Firefox
Android funziona» era una **premessa sbagliata**, corretta qui.

### ⛔ E la cosa nostra c'era: la scritta mandava a cercare nel posto sbagliato

Il riquadro diceva *«questo browser non porta nessuno dei due codec video fino ai pixel: né HEVC né
H.264 … su Linux il decodificatore HEVC di Chrome è quello della scheda grafica»* — una spiegazione
su codec e schede grafiche, mentre la causa vera stava una riga più su ed era di un'altra specie.

⇒ Adesso la casella **«WebCodecs non c'è»** viene **prima** e si nomina: *«questo browser non ha
WebCodecs, cioè l'unico modo che REMOTIX ha di disegnare il desktop: non è una questione di codec»*.
⭐ Una scritta che manda nel posto sbagliato è peggio di nessuna scritta.

### ⏳ Che cosa resta aperto

⚠ Se Firefox per Android deve essere un motore supportato, serve un **secondo percorso di disegno**
(MSE con un `<video>`): è lavoro vero, cambia le proprietà di ritardo, e va deciso — non è un
interruttore. ⭐ Chrome per Android ha WebCodecs, e lì la strada c'è.

## ⏳ 21 agosto 2026 — **quanto costerebbe MSE**, misurato prima di scrivere il percorso

*Il vincolo dell'utente: «supportare pienamente Chrome e Firefox in Linux, Windows e Android».
⛔ Firefox per Android non ha WebCodecs, quindi coprirlo vuol dire un **secondo percorso di
disegno**: `MediaSource` con un `<video>`, a MP4 frammentato invece che ad Annex-B. ⇒ Il prezzo si
misura prima, non dopo — banco `banchi/07-b57-quanto-costa-mse.py`.*

### La misura — stesso ferro, stesso flusso (i nostri 150 fotogrammi, 2560×962, H.264 High 5.0)

| | Firefox | Chrome |
|---|---|---|
| WebCodecs, 60/s | **60,5 ms** | **50,9 ms** |
| MSE, 60/s | 285,4 ms — ⛔ **+225 ms** | 465,6 ms — ⛔ **+415 ms** |
| MSE, 10/s | 246 ms — ⚠ **+17 ms** | 570 ms — **+348 ms** |
| coda di riproduzione | 310–650 ms | 520–715 ms |

⛔ **Il tetto dichiarato è 50 ms** (`SPECIFICHE.md` §3.2). ⇒ A ritmo utile MSE lo sfonda di un
ordine di grandezza, e non per lentezza del decodificatore: il `<video>` **tiene una coda apposta**,
perché il suo mestiere è la riproduzione fluida, non il ritardo basso.

⚠ **Il limite della misura, dichiarato**: lo schermo del banco è un `Xvfb` **senza GPU**, quindi tutte
e due le strade decodificano in software. ⭐ Ma la coda di presentazione non è una proprietà della
scheda video, e il confronto è fra due strade **nello stesso identico posto**.

⚠ **E l'inseguimento non salva**: saltare al bordo vivo porta la mediana di Firefox a 265 ms con
**40 salti** su 150 fotogrammi — cioè un'immagine che scatta. Si scambia ritardo con scatti.

### ⛔ Cinque difetti del banco, e ognuno avrebbe prodotto un numero falso

Questo banco ha mentito **cinque volte** prima di misurare, e vale la pena elencarle perché sono
tutte della stessa famiglia — *lo strumento misurava se stesso*:

1. `"null"` letto come un esito: Chrome dava tre righe rosse **e funzionava**;
2. alimentare a 10/s un MP4 che si dichiara a 60 fps: il `<video>` corre a 60, resta a secco, e
   `requestVideoFrameCallback` vede **due** fotogrammi su cento;
3. misurare **l'avvio** invece del regime: mediana 2,7 s con una coda di 160 ms;
4. ⛔ **nessun gesto dell'utente**: senza un tocco il `<video>` non parte affatto — coda 3,5 s,
   *zero* fotogrammi buttati, e sembrava «MSE bufferizza» mentre era «non è mai partito»;
5. ⛔ **`ffmpeg -framerate` non vale per il demuxer H.264**: il file usciva a **25 fps** mentre lo
   alimentavo a 60, e la coda che chiamavo «di MSE» era la mia differenza di ritmo. Si vede da
   `currentTime = 5,98 s` con 150 fotogrammi: 150/25 = 6 s. ⇒ Si usa `-r`, e **si verifica con
   `ffprobe`** invece di credere alla riga di comando.

⭐ Il difetto 4 è stato trovato **da un numero incoerente**, non da un errore: «coda 3,5 s **e zero
fotogrammi buttati**» non può descrivere un decodificatore in affanno. Un banco che avesse
riportato solo la mediana non l'avrebbe mai fatto vedere.

### ⏳ Che cosa resta da decidere — e non si decide qui

⛔ Con questi numeri, «Firefox per Android pienamente supportato» e «ritardo sotto i 50 ms» **non
stanno insieme**. ⇒ La scelta è dell'utente, e le opzioni sono nominate: accettare su quel motore un
ritardo di un'altra classe, oppure dichiararlo non supportato finché Mozilla non porta WebCodecs su
Android. ⚠ La misura definitiva è sul telefono, che l'hardware ce l'ha; il banco si serve alla rete
di casa con `banchi/07-b57-servi-al-telefono.py`.

## ⭐⭐ 21 agosto 2026 — **la prima sessione Android**, e l'utente: «Chrome è un missile»

*Chrome per Android, Samsung DeX, 2560×1080. Tre minuti e mezzo di sessione vera, `[M]` dal registro
del server e dal diario della pagina.*

| | |
|---|---|
| codec negoziato | ⭐ **HEVC** (codec 1) — **non** il ripiego H.264 |
| tela | 2558×926 |
| fotogrammi | **3 178 arrivati, 3 178 dipinti** |
| saltati · buchi · fuori ordine · tardivi · errori del decodificatore | ⭐ **0 · 0 · 0 · 0 · 0** |
| input | 45 tasti, tutti arrivati |
| audio | 8 935 blocchi ricevuti, 8 933 suonati, **2 buchi** in 3 min 30 |

⭐ **Zero perdite su ogni riga che il diario conta.** È la prima volta che questo codice tocca un
telefono, e il verso video → schermo non ha un difetto da nominare.

⭐ **E la sorpresa è il codec**: il telefono ha negoziato **HEVC in hardware**, cioè la prima scelta
di `PREFERENZA` — non il ripiego. ⚠ L'H.264 di §1.13-ter resta necessario (Firefox desktop non fa
HEVC), ma su questo telefono non è servito.

### ⛔ E l'unico numero che non è buono: **la coda dell'audio, 401 → 421 ms** — ⭐ e la sera stessa l'orecchio dell'utente lo ha CONFERMATO

Il diario la riporta a ogni giro e **cresce**: 401 ms a 10:37:39, 421 ms a 10:37:49, e lì resta.
Il video, nella stessa sessione, non ha un fotogramma tardivo ⇒ non è la rete: è la coda del
percorso audio.

⛔⭐ **E la sera del 21 agosto l'utente ha ascoltato, due volte.** La prima: *«Chrome su Android
offre un'esperienza completa: audio e video perfetti»*. La seconda, un'ora dopo, su Windows:
*«**il ritardo di 400 ms tra audio e video in generale te lo confermo**»*. ⇒ Il numero **non è un
caso e non è di Android**: è `AUDIO_CUSCINO_MS = 250` in `pagina.html`, più la catena, e si sente
come **sincronia sbagliata** — non come audio sporco. 📖 La diagnosi e la cura nominata stanno in
`fasi/07-audio-e-appunti.md` §8 e §9.7-bis.

## ⭐⭐ 21 agosto 2026 — **il secondo percorso di disegno**: MP4 frammentato su MSE

*`DECISIONI.md` §7.18, dall'utente: «si costruisce». ⛔ E la ragione per cui §0.1-bis non lo vieta:
quel principio parla di un motore che **rende peggio**; qui il motore **non apre affatto**.*

⭐ **Il protocollo non si tocca**: sul filo passano gli stessi fotogrammi Annex-B di §6.2. Cambia
solo **come il client li disegna**, e il server non se ne accorge.

⭐ **E l'audio non è stato scritto**: la pagina ripiegava già su `pcm` quando manca `AudioDecoder`
(§4.3 lo impone a entrambi ed è la base sempre disponibile). ⇒ Il lavoro era **solo il video**.

### I tre pezzi

| pezzo | che cosa fa |
|---|---|
| `MuxMP4` | i fotogrammi Annex-B diventano un segmento d'inizio (`ftyp`+`moov` con l'`avcC` costruito dall'SPS/PPS visti) e un `moof`+`mdat` per fotogramma |
| `sonda_mse_una()` | la sonda **dipinge anche su questa strada** e si giudicano i pixel — ⭐ non si crede a `isTypeSupported` (`LEZIONI.md` §1.9) |
| `Schermo.mse_*` | il `<video>` prende il posto della tela, eredita classe e stile, e i fotogrammi si contano con `requestVideoFrameCallback` — l'unico posto, lì, in cui si sappia che un pixel è arrivato |

⚠ **La durata di ogni fotogramma è quella VERA**, misurata all'arrivo: un desktop non ha un ritmo
fisso — sta fermo per secondi e poi si muove — e dichiarare 60/s a un `<video>` che ne riceve tre al
secondo lo manderebbe a secco a ogni pausa. `[M]` È esattamente l'errore che il banco `07-b57` ha
fatto per primo, con `ffmpeg -framerate` che per il demuxer H.264 non vale.

### ⛔ Due errori di byte, trovati rileggendo prima di provare

1. **`trun`: versione (1 byte) e poi bandiere (3)**, non il contrario. Scritte al rovescio il
   `<video>` legge `flags = 0x030500`, cioè campi che non ci sono: ⚠ **non dà errore e non
   dipinge**.
2. **`tkhd`: mancavano quattro byte** (volume + riservato) prima della matrice, e tutto quel che
   segue scivolava.

⭐ E il muxer è stato **verificato da fuori prima di collegarlo**: i nostri 150 fotogrammi passati
dal muxer e dati a `ffprobe` → `h264, High, 2560×962, level 50, 2,372 s`, e `ffmpeg` li decodifica.
⚠ Un muxer provato solo dentro il browser avrebbe confuso «il mio MP4 è sbagliato» con «questo
motore non lo accetta».

### Lo stato misurato

| | |
|---|---|
| la strada si accende e dipinge (Firefox, `?disegno=mse`) | ⭐ sì — `<video>` 1190×704, 4 dipinti, **0 buchi**, ritardo 50 ms, 1 salto |
| la strada normale (WebCodecs) | ⭐ intatta: `07-b51` 4 controlli su 4 per motore |
| Firefox per Android | ⏳ **da provare sul telefono** — è il motore per cui esiste |

### ⛔ E il primo giro su Firefox Android è fallito — **«caricato» non vuol dire «dipinto»**

*L'utente, 21 agosto 2026: «non funziona». `[M]` E la pagina aveva già scritto il perché nel
registro del server:*

```
sonda video · ⛔ H264: NON arriva al pixel — il `<video>` ha caricato ma i pixel
              non sono quelli della sonda (sinistra 0,0,0, destra 0,0,0)
```

⭐ **Zero-zero-zero su tutti e due i lati è nero, non «un colore sbagliato».** ⇒ Il flusso era
giusto — il `<video>` lo aveva **caricato**, quindi il muxer funziona anche sul telefono — e a
sbagliare era **il momento della lettura**: `loadeddata` dice che il fotogramma è stato
*decodificato*, non che sia stato **presentato**, e `drawImage` da un `<video>` che non ha ancora
presentato niente copia nero.

⛔ La sonda accusava il flusso di un difetto del proprio cronometro. ⇒ Adesso fa presentare il
fotogramma (`play()` muto + `requestVideoFrameCallback` dove c'è) e **rilegge fino a dodici volte**,
e ⭐ **riconosce il nero** invece di trasformarlo in un verdetto.

⚠ È la stessa famiglia dei cinque difetti del banco `07-b57`: *lo strumento misurava se stesso*.

#### ⛔ E la seconda volta la tela era ancora nera — **due cause, tutte e due dei motori mobili**

`[M]` La riga nuova della sonda: *«il `<video>` non aveva ancora presentato niente: la tela è
tornata nera»* — dopo **dodici** riletture in un secondo e mezzo. ⇒ Non era lentezza: quel
`<video>` non presentava **mai**.

| causa | perché |
|---|---|
| il `<video>` della sonda stava **fuori dallo schermo** (`left:-9999px`) | i motori mobili non presentano quel che nessuno guarda: risparmiano batteria. ⇒ Adesso sta dentro la vista, **due pixel per due**, quasi trasparente — visibile quanto basta al motore, non all'utente |
| la sonda partiva **al caricamento della pagina** | presentare vuol dire suonare, e nessuno aveva ancora toccato niente. ⇒ Su questa strada il sondaggio si fa nel `CIAO`, cioè **dopo che l'utente ha premuto «Collegati»** |

⚠ E la seconda cura ha un effetto laterale dichiarato: su MSE la sonda costa il suo tempo **a chi si
collega** invece che al caricamento. Sulla strada di WebCodecs non cambia niente.

#### ⛔⛔ E al terzo «non è cambiato nulla» il difetto era **altrove** — banco `07-b58`

*L'utente, 21 agosto 2026: «Non è cambiato assolutamente nulla, e mi stai facendo perdere tempo con
test inutili». ⭐ Aveva ragione su tutta la riga: gli ho fatto provare tre volte **la mia sonda**,
non il prodotto — e per tre volte quel che si rompeva non era quel che gli chiedevo di guardare.*

⭐ **La cura del metodo, prima di quella del codice**: `dom.media.webcodecs.enabled = false` toglie
`VideoDecoder` **e** `AudioDecoder` a un Firefox da tavolo. `[M]` `typeof VideoDecoder ===
"undefined"` — esattamente quel che dichiara Firefox per Android. ⇒ La strada si prova **qui**, e
sul telefono ci si va una volta sola, alla fine. È il banco `07-b58`.

⚠ E quel che quel banco NON riproduce si dichiara: le regole di risparmio dei motori mobili — un
`<video>` piccolo o fuori dalla vista che non viene presentato. Per quelle l'ultima parola resta del
telefono.

**Alla prima esecuzione ha trovato in un colpo tre difetti che nessun giro sul telefono aveva
nominato:**

1. ⛔⛔ **La scala delle misure chiamava `VideoDecoder` e lanciava `ReferenceError` su ogni
   gradino** — il primo compreso — e `video.misura_massima` usciva **320×240**, la tela minima di
   §4.5. ⇒ Il server concedeva 320×240 e il desktop sarebbe apparso **in un francobollo**, senza una
   riga che lo spiegasse. Adesso su questa strada la capacità si **omette** (§4.3 lo permette): non
   si dichiara quel che non si è misurato.
2. ⛔ **`document.body.dataset.schermo = "acceso"` non veniva mai scritto**, perché su questa strada
   non si passa da `dipingi()`: la pagina sarebbe rimasta «in attesa del primo fotogramma» con il
   desktop già sullo schermo.
3. ⛔⛔ **Il risveglio del `<video>` era appeso ai fotogrammi presentati.** Un desktop sta fermo per
   secondi; il `<video>` finisce i dati, si mette in pausa, e `requestVideoFrameCallback` **smette
   di scattare** — perché scatta sui fotogrammi presentati. ⇒ La prima pausa del desktop avrebbe
   fermato l'immagine **per sempre**. Adesso si insegue anche quando arrivano dati nuovi.

⭐ **E la regola «si dichiara solo quel che dipinge» ha qui la sua prima eccezione dichiarata**
(`DECISIONI.md` §1.13, `LEZIONI.md` §1.9): su questa strada la sonda dovrebbe far *presentare* un
fotogramma a un `<video>` di prova, e sui motori mobili un `<video>` di prova **non presenta**.
⇒ Si dichiara sulla parola del motore, e il controllo si sposta dove il `<video>` è **vero**:
`Schermo.mse_veglia()` scrive in chiaro se dopo quattro secondi non è stato presentato nemmeno un
fotogramma. ⚠ La tela nera resta **spiegata**, che è l'unica cosa che la regola serviva a impedire.

#### La misura, su un browser senza WebCodecs — 25 secondi di desktop vivo

| | |
|---|---|
| fotogrammi consegnati → **dipinti** | 291 → ⭐ **250** |
| buchi | ⭐ **0** |
| coda del `<video>` | ⚠ 212 ms — coerente con il prezzo misurato in `07-b57` |
| tela | ⭐ 1270×704, **non** i 320×240 di prima |

⚠ E il banco ha avuto anche il suo difetto, dichiarato: muovere il puntatore **non fa fotogrammi**
— il cursore viaggia su un canale suo e i pixel del desktop non cambiano. `[M]` Un giro intero con
**un** fotogramma, e stava per dichiarare «non dipinge» di una strada che dipingeva quel che c'era.
⇒ Adesso apre un terminale che scorre.

#### ⛔ «Vedo il desktop ma non funziona l'input» — la tela non si nasconde

*L'utente, 21 agosto 2026, ed è la prima volta che su Firefox per Android il desktop **si vede**.*

⛔ **Tutto** l'input di questa pagina è agganciato alla `<canvas>` — `pointermove`, `mousedown`,
`wheel`, `contextmenu` e i quattro eventi del tocco — e le coordinate escono dal suo
`getBoundingClientRect()`. ⇒ Nascondendola con `display:none` per far posto al `<video>`, gli
eventi non arrivavano a nessuno e il rettangolo valeva zero: **il desktop si vede e non si
comanda**.

⭐ **La cura**: la tela resta **dov'è e com'è** — è la superficie che riceve i gesti — e diventa
**trasparente**; il `<video>` le sta **dietro**, incollato al suo rettangolo (`mse_posiziona()`, che
segue `cornice()`). ⇒ Su questa strada, per chi tocca lo schermo, non cambia niente: tocca la stessa
cosa di sempre.

⚠ E il banco ha avuto il suo difetto anche qui: cliccava a una coordinata scelta a occhio, che
cadeva fuori dalla tela — e avrebbe detto «il clic non arriva» di un clic mai dato. ⇒ Adesso il
centro della tela lo **chiede alla pagina**.

#### La misura finale, browser senza WebCodecs, desktop vivo

| | |
|---|---|
| immagine | ⭐ 351 consegnati → **196 dipinti**, **0 buchi**, tela 1270×704 |
| input | ⭐ **4 eventi al server**: la lettera, il movimento, e `PULSANTE evdev 272` premuto e rilasciato |
| coda | 50 ms |

⚠ Un fotogramma su due non viene presentato: è il `<video>` che scarta sotto un terminale che
scorre, **in software e senza GPU**. Sul telefono, che decodifica H.264 in hardware, il rapporto è
un'altra cosa — e lì la misura la fa l'utente.

#### ⛔ «Non si vede il desktop» — la cornice non veniva mai chiamata

*Subito dopo la cura dell'input: il desktop era sparito.*

⛔ `cornice()` è quel che dà alla tela la sua **misura sul vetro**, e sulla strada di WebCodecs la
chiama il disegno (`componi()`). ⇒ Su questa strada il disegno non passa di lì: la tela restava
larga **sedici pixel** — la misura con cui la `<canvas>` nasce nel documento — e il `<video>`, che
adesso le sta incollato dietro, la seguiva fedelmente **in un francobollo invisibile**.

⭐ La misura del fotogramma su questa strada si sa (è la tela concessa): si scrive in `f_l`/`f_a`,
dove le due strade la tengono, e si incornicia.

#### ⚠ E il banco era **verde** mentre l'utente non vedeva niente

`07-b58` contava i fotogrammi e leggeva i contatori: tutti buoni. ⛔ Non guardava **dove finisce
l'immagine sul vetro**, che è l'unica cosa che l'utente vede. ⇒ Adesso lo misura, e boccia due casi
distinti:

| controllo | che difetto prende |
|---|---|
| il `<video>` occupa una frazione ragionevole della finestra | il francobollo |
| il `<video>` è **incollato** al rettangolo della tela (±2 px) | i gesti che finirebbero nel posto sbagliato, perché la superficie che li riceve non sta dove si vede l'immagine |

`[M]` Adesso: `tela [1270, 704] · video [1270, 704] · finestra [1270, 705]`, 6 eventi di input al
server, 499 fotogrammi consegnati e 123 presentati, 0 buchi.

## ⭐⭐⭐ 21 agosto 2026, sera — **REMOTIX gira su Firefox per Android**

*L'utente, dopo sei giri di prove sul suo telefono: «non sei in grado di far funzionare Firefox per
android con remotix». Poi: **«Installa la suite android sdk, usa quella»**. ⭐ Aveva ragione due
volte — sul risultato e sul metodo.*

⭐ **La fotografia dell'emulatore**: dentro Firefox 154 per Android — la stessa versione del suo
telefono — c'è lo sfondo di GNOME, la barra in alto con l'ora `Aug 21 16:01`, e i due terminali
`REMOTIX-SCENA` che scorrono timestamp **vivi**. Desktop remoto, in movimento, su un browser senza
WebCodecs.

### ⛔ I tre difetti che solo Android poteva mostrare

`07-b58` (Firefox da tavolo con `dom.media.webcodecs.enabled=false`) prende quasi tutto, ma **non**
prende quel che è proprio del motore mobile. Questi tre sono usciti solo qui:

1. ⛔⛔ **La ricerca che non finisce mai.** L'inseguimento del bordo vivo scriveva `currentTime`,
   cioè una **ricerca** — e una ricerca vuole un punto di accesso casuale, cioè una chiave, che lì
   non c'è. `[M]` `cerca=true · pronto=1 · tempo=34,41 · buffer=0,00→40,34 · errore=no`, e
   **19 fotogrammi dipinti su 727**. ⇒ Non si salta più: si insegue con la **velocità**
   (`playbackRate` 1,25 finché la coda rientra). Costa un filo di accelerazione invece di uno
   scatto, e non chiede una chiave a nessuno.
2. ⛔ **La potatura del passato svuotava tutto.** `sb.remove()` per non tenere in memoria il già
   visto lasciava `buffer=nessuno` con 817 fotogrammi consegnati. ⇒ Tolta: qualche secondo di video
   in memoria è un prezzo che si paga volentieri, una pagina nera no.
3. ⛔⛔ **E `dipinti` non è «quanti se ne vedono».** `requestVideoFrameCallback` sui motori mobili è
   **strozzato**: `[M]` 46 scatti in 35 secondi mentre il desktop si muoveva. ⇒ Per due volte quel
   numero mi ha fatto credere che l'immagine fosse ferma. Il giudice, lì, è **lo schermo** — una
   fotografia — non il contatore.

### ⭐ E lo strumento resta: `banchi/07-b59-firefox-android.py`

Emulatore Android 14 con KVM, Firefox **154.0** per Android, e il giro completo da solo: accetta il
certificato, entra come «prova», lascia girare, e legge nel registro del **server** la riga che la
pagina racconta di sé — `MISURA §7.18 MSE: consegnati … dipinti … fermo= cerca= pronto= buffer=`.

⚠ E quel che **non** riproduce si dichiara: l'emulatore non ha la decodifica in hardware. ⇒ I
**numeri** del ritardo non valgono; vale il **comportamento** — dipinge o no, si ferma o no, e
perché.

⛔ **La lezione di metodo, e l'ha insegnata l'utente**: quando una prova richiede sei giri di una
persona, lo strumento sbagliato non è il prodotto — è il banco. Sei ore prima avrei potuto
installarlo.

### ⭐ Il giro completo, fatto da me — 21 agosto 2026, sera

*L'utente: «prova tu».*

| prova | esito |
|---|---|
| **Firefox 154 per Android** (emulatore, `07-b59`) | ⭐ desktop **vivo** — orologio `16:52`, terminali che scorrono; `fermo=false cerca=false pronto=3`, il tempo del video **avanza di 4,43 s in 5** |
| input da Android | ⭐ il tocco arriva: `PULSANTE codice evdev 272 rilasciato` nel registro del server |
| ritardo su Android (emulatore) | ⚠ **2,3 s** dal bordo vivo — ⛔ e il numero **non vale**: decodifica in software, scena pesante, tela 1080×2040 |
| **senza WebCodecs, da tavolo** (`07-b58`) | ⭐ **0,21 s** dal bordo vivo, 277 dipinti su 444, input e geometria verdi |
| **strada normale**, WebCodecs (`07-b51`) | ⭐ 4 controlli su 4 per motore, **intatta** |

⛔ **E il giudizio del banco è stato riscritto**, perché sbagliava: dava rosso sul contatore
`dipinti`, che su mobile è strozzato. ⇒ Adesso guarda quel che descrive davvero lo stato del
`<video>` — *sta suonando? sta cercando? ha dati? quanto è indietro?* — e ⭐ **confronta due
letture**, perché un'immagine che avanza e una ferma hanno lo stesso aspetto in una fotografia sola.

## ⛔ 21 agosto 2026, sera — **il giudizio dell'utente: Firefox per Android è incompatibile**

> *«Niente da fare, troppi problemi: disegno del desktop irregolare, input imprevedibile, dichiaro
> Firefox per Android incompatibile con REMOTIX.»*

⚠ **E la strada funziona**: il desktop si vede vivo e i tocchi arrivano — misurato poche ore prima
sullo stesso emulatore. ⛔ Ma *«funziona»* non era il traguardo: il traguardo è §0.1-bis, cioè
un'esperienza vicina a una sessione locale. A un `<video>` che **riproduce** non si può chiedere di
reagire come un decodificatore comandato a mano.

⇒ **Nel prodotto**: `VIA_MSE` non si accende più da sola. Su un browser senza WebCodecs la pagina
**dichiara che non si può**, e nomina l'alternativa (Chrome per Android). ⭐ Mezza esperienza è
peggio di un rifiuto spiegato.

⇒ **Il codice resta dietro `?disegno=mse`**, perché finché Mozilla non porta WebCodecs su Android è
l'unica prova che il problema non è nostro. Alla fase 13 si decide se buttarlo.

### ⭐ Che cosa resta di buono, e non è poco

| | |
|---|---|
| `07-b58` | REMOTIX su un browser **senza WebCodecs**, riprodotto da tavolo con una preferenza |
| `07-b59` | **Firefox per Android vero**, in un emulatore: certificato, accesso, misura e fotografia — da solo |
| `LEZIONI.md` §1.19 | chi apre chiude: i banchi lavorano sul desktop di una persona |
| la sonda che riconosce il nero, la cornice, l'input agganciato alla tela | difetti veri, curati, che valgono anche fuori da questa strada |

⛔ **E il costo si scrive**: sei giri di prove sul telefono dell'utente e una giornata, per una
strada che non entra nel prodotto. ⚠ La lezione non è «non andava fatto»: è che **la domanda "quanto
renderà?" andava misurata prima di costruire** — e il numero c'era già, dal banco `07-b57`:
centinaia di millisecondi contro un tetto di 50.

