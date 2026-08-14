# F4-A9 — Le scorciatoie che il browser si tiene

*Anello **A9** della fase 4, **14 agosto 2026**. Sonda **S3**. Banco `banchi/04-b29-*`, esiti riga
per riga in `banchi/04-b29-esiti.jsonl`, tavola con `python3 banchi/04-b29-tavola.py`.*

> ## ⭐ In quattro righe
>
> 1. ⛔ **Gli stati sono tre e il secondo è il peggiore — ed è largo**: `[M]` **18 combinazioni su
>    42** su Chrome in finestra arrivano alla sessione remota **e** fanno agire anche il browser.
>    Una prova che guardasse solo il lato della sessione le avrebbe dichiarate **tutte verdi**.
> 2. ⭐ **E il caso peggiore si spegne con una riga**: `preventDefault()` nella pagina lo porta a
>    **0**, su tutti e due i motori.
> 3. ⭐ **Poi lo schermo intero con la Keyboard Lock spegne il resto — su Chrome**: le riservate del
>    browser vanno **8 → 0**. ⛔ **Su Firefox 140 ESR no**: quel motore **non ha nessuna delle due
>    forme della lock**, e a schermo intero **peggiora** (5 → 7).
> 4. ⛔ **Quel che resta non è del browser: è del compositore del client** — `Super`, `Super+D`,
>    `Alt+Tab`, `Alt+F2`, `Alt+F4`, `Ctrl+Alt+Canc`. **Nessuna API le riprenderà mai** ⇒ i bottoni
>    a schermo sono **un requisito** *(O7)*, e sono nella pagina e verificati.
>
> ⚠ **Su Safari non ho misurato niente e non deduco niente: `[?]`.**

---

## 0. ⛔ Come ho misurato, e perché in un altro modo non valeva

**Si inietta dalla porta da cui entra una tastiera vera.** `org.gnome.Mutter.RemoteDesktop`
(`NotifyKeyboardKeycode`, codici **evdev**, cioè posizioni) — non da CDP `Input.dispatchKeyEvent`,
e non da `xdotool`.

⛔ **Non è una preferenza di stile: è la condizione perché la misura esista.** Quel che questa sonda
deve misurare è lo strato degli **acceleratori del browser**, che sta *sopra* la pagina e *sotto* il
compositore. Un tasto iniettato dentro il processo di rendering entra **sotto** quello strato: darebbe
«consegnata» a tutto, e la tavola sarebbe verde e falsa.

**Le due colonne, mai una sola.** Per ogni combinazione:

| | la domanda | come si legge |
|---|---|---|
| 1 | **è arrivata alla pagina?** | un `keydown` con quel `code` **e** quei modificatori |
| 2 | **il browser ha fatto anche il suo?** | la scheda che muore · il documento che rinasce · il fuoco perso · la scheda nascosta · lo schermo intero cambiato · `beforeprint` · la geometria che salta (i DevTools) · **e su Chrome il conto dei bersagli del protocollo di debug, che è un secondo strumento indipendente** |

⛔ **E il palco è scritto in ogni riga**: motore, versione, piattaforma delle finestre, **schermo
intero letto ALLA BATTUTA** (non come era stato montato), **lock chiesta / concessa / viva alla
battuta**, e **lo stato del fuoco prima e dopo**.

> ### ⭐⭐ IL FUOCO NON È IL CONTORNO DELLA MISURA: È UNA DELLE GRANDEZZE
>
> È la prima cosa che questo banco mi ha insegnato, e me l'ha insegnata **facendomi sbagliare**:
> i primi giri davano *«non consegnata»* a **tutto**, e il motivo non era il browser — la finestra
> non aveva il fuoco della tastiera.
>
> ⛔ **E vale doppio proprio qui**, perché la Keyboard Lock **si spegne da sola quando la pagina
> perde il fuoco** (O10). ⇒ In un palco «con lock» ogni combinazione che apre qualcosa **uccide la
> lock**, e le prove successive girerebbero *senza* lock sotto l'etichetta *«con lock»* —
> `CODER.md` §3.9, due comportamenti sotto la stessa etichetta. La cura è nel banco: la lock si
> **ricompra prima di ogni prova** e ogni riga porta `lock_viva_alla_battuta`.
>
> ⇒ Da cui il **cancello del fuoco**: se la pagina non ha il fuoco, **non si inietta** e si scrive
> `NON-MISURATA`. Non è prudenza — è che la battuta finirebbe *nella finestra di qualcun altro*, e
> `Ctrl+W` chiuderebbe una scheda dell'utente.

**I controlli** (`CODER.md` §3.3), rifatti **in ogni palco**, e se non passano il palco non si crede:

| | | deve dare |
|---|---|---|
| **positivo** | `Ctrl+Alt+G` | **consegnata e non riservata** — se non arriva, la catena è rotta |
| **negativo** | `Super` | **non consegnata** (GNOME se lo tiene sopra la testa del browser) ⭐ **e si vede**: la panoramica si apre e la pagina perde il fuoco. È la prova che l'iniezione **è arrivata** anche quando la pagina non ha visto niente |
| **negativo 2** | `Ctrl+W` in finestra | **non consegnata**, e la scheda **muore**: il negativo di livello *browser*, mentre `Super` è quello di livello *compositore* |

⭐ **E c'è un controllo positivo gratis su ogni riga**: `modificatori_visti`. Se la pagina ha visto
il `keydown` di `Control` ma non quello di `W`, l'iniezione è arrivata **fin dentro la pagina** e a
fermarsi è stata la **combinazione**. ⛔ Su tutte le righe `non-consegnata` misurate, **nessuna** è
uno zero muto: ognuna porta o i modificatori visti, o un effetto del browser, o tutt'e due.
*Uno zero senza un caso che sappia dare diverso da zero non è una misura* (`CODER.md` §3.10).

---

## 1. Che cosa cambia per l'utente — quali tasti perderà, e su quale browser

> ### ⭐ La risposta in una riga
>
> **Su Chrome, a schermo intero e con la Keyboard Lock, l'utente non perde NIENTE di quel che il
> browser tiene** — `[M]` 14 agosto 2026: **0 combinazioni su 42** restano al browser, `Ctrl+W`,
> `Ctrl+T`, `F11`, `F12`, `Ctrl+P` comprese. **Su Firefox 140 ESR perde 7 combinazioni e non c'è
> modo di riprenderle**, perché quel motore **non ha nessuna delle due forme della lock**.
>
> ⛔ **E quel che resta perso su tutti e due è del compositore del CLIENT, non del browser**:
> `Super`, `Super+D`, `Alt+Tab`, `Alt+F2`, `Alt+F4`. ⇒ **Nessuna lock le riprenderà mai**, ed è
> esattamente la ragione per cui i bottoni a schermo sono **un requisito** (*O7*) e non un ripiego.

### 1.1 I tre strati, e vanno separati perché si curano in modo diverso

⛔ **«Il browser si tiene le scorciatoie» sono in realtà TRE cose distinte**, e questa sonda le
separa perché hanno tre cure diverse:

| strato | chi la prende | esempio `[M]` | si cura con |
|---|---|---|---|
| **compositore del client** | GNOME/Mutter, **sopra la testa del browser** | `Super`, `Alt+Tab`, `Alt+F4`, `Alt+F2` | ⛔ **niente**. Nessuna API di pagina arriva lì ⇒ **bottone a schermo** |
| **browser, riservata** | l'acceleratore scatta **prima** del rendering: la pagina non vede nemmeno il `keydown` | `Ctrl+W`, `Ctrl+T` in finestra su Chrome | schermo intero, **Keyboard Lock**, finestra d'applicazione |
| **browser, azione predefinita** | la pagina **vede** il `keydown`, ma se non lo ferma il browser fa anche il suo | `Ctrl+P`, `F5`, `Ctrl+L`, `F12` | ⭐ **`preventDefault()` nella pagina** — ed è il primo dovere del client, non una perdita |

⭐ **È il secondo stato di O8, ed è il peggiore proprio perché sembra funzionare**: la sessione
remota riceve la battuta *e* il browser stampa, ricarica, apre i DevTools. `[M]` **18 combinazioni
su 42** stanno lì su Chrome in finestra, **15 su 42** su Firefox.

### 1.2 Che cosa perde l'utente, motore per motore — ⛔ **il conto del BROWSER, separato dal compositore**

| palco | Chrome 151 `[M]` | Firefox 140 ESR `[M]` | Safari |
|---|---|---|---|
| **finestra** | **8** riservate dal browser | **5** riservate dal browser | `[?]` |
| **schermo intero (API), nessuna lock** | ⭐ **2** — e sono **esattamente `F11` e `Escape`**, cioè *«`F11` e l'uscita»* | ⛔ **7 — PEGGIORA**: tiene tutte e 5 quelle della finestra **e in più `F11` ed `Escape`** | `[?]` |
| **schermo intero + Keyboard Lock** | ⭐⭐ **0** | ⛔ **non esiste su questo motore** | `[?]` |
| **finestra d'applicazione** (`--app`, il ramo della PWA) | ⭐⭐ **0, già in finestra** | non provato | `[?]` |
| **schermo intero aperto con `F11` + lock chiesta** | **1** (`F11`), e ⛔ **la lock non c'è**: il palco è identico a quello *senza* lock | `[?]` | `[?]` |

⛔ **E in ogni palco restano perse le 5 del compositore** (`Super`, `Super+D`, `Alt+Tab`, `Alt+F2`,
`Alt+F4`), più `Ctrl+Alt+Canc` che non ho iniettato (§4.2).

### 1.3 ⭐⭐ La ricetta, e ogni gradino ha il suo numero misurato

⛔ **Il banco ha girato DUE VOLTE**: una senza `preventDefault()` — che misura *che cosa fa il
browser da solo* — e una **con**, che è quel che il prodotto fa davvero (l'ancora
`F4-INPUT-CLASSICO` chiama `preventDefault()` su ogni battuta che spedisce). La differenza fra i
due giri **è la risposta**, e non si sarebbe vista con un giro solo.

| gradino | che cosa spegne | `[M]` Chrome 151 | `[M]` Firefox 140 |
|---|---|---|---|
| **0.** nessuna cura, finestra | — | 18 nel caso peggiore + 8 riservate | 15 nel caso peggiore + 5 riservate |
| **1.** ⭐ la pagina chiama **`preventDefault()`** | ⛔ **tutto** il caso peggiore | **18 → 0** | **15 → 0** |
| **2.** ⭐ schermo intero **+ Keyboard Lock** | le riservate del **browser** | **8 → 0** | ⛔ **impossibile**: nessuna delle due forme |
| **3.** i **bottoni a schermo** *(O7)* | quel che resta, che è **del compositore del client** | 5 (+`Ctrl+Alt+Canc`) | 5 (+`Ctrl+Alt+Canc`) |

⭐ **Il gradino 1 costa una riga e vale più del gradino 2**: spegne il caso *peggiore* — quello che
l'utente non capirebbe mai da solo, perché la sessione remota **riceve davvero** la battuta.
⛔ E vale **su tutti e due i motori**, lock o non lock.

---

## 2. Serve una decisione di Nic? — ⭐ **sì, una sola, e le altre le decide la misura**

> ### ⛔ LA DECISIONE: i bottoni a schermo, e QUANTI
>
> `web.md` O7 dice che il bottone `Ctrl+Alt+Canc` è **un requisito, non un ripiego di fortuna**, e
> l'ho implementato. ⚠ Ma la misura dice che **le combinazioni irrecuperabili non sono una: sono
> sei**, e sono tutte del **compositore del client** — `Ctrl+Alt+Canc`, `Super`, `Super+D`,
> `Alt+Tab`, `Alt+F2`, `Alt+F4`.
>
> **La domanda per Nic**: la barra deve portarle **tutte e sei** (e allora è una barra, e occupa
> spazio sullo schermo del desktop remoto), oppure **solo `Ctrl+Alt+Canc`** (e le altre cinque si
> **dichiarano** come perdute e basta)?
>
> ⭐ **Quel che ho fatto in attesa**: la barra c'è con **cinque bottoni** — `Ctrl+Alt+Canc`,
> `Ctrl+W`, `Ctrl+T`, `Alt+F4`, `Super` — **compare da sola** quando una delle due disposizioni
> entra in vigore, e si può nascondere. ⛔ È dietro un comportamento che si vede, cioè
> l'invariante **I6**: se la scelta è un'altra, si cambia una riga.
>
> ⚠ **E non è una decisione rimandabile alla fine**: la barra sta *sopra* l'immagine del desktop
> remoto, quindi toglie pixel a quel che l'utente è venuto a guardare.

**Quel che NON serve decidere, perché l'ha deciso la misura:**

| | |
|---|---|
| ⭐ **la pagina va a schermo intero e chiede la lock** | non è un'opzione: `[M]` è la differenza fra perdere 8 combinazioni e perderne 0 |
| ⭐ **la pagina chiama `preventDefault()`** | `[M]` è la differenza che spegne il caso peggiore, quello che *sembra* funzionare |
| ⛔ **la pagina deve saper chiedere ENTRAMBE le forme della lock** | `[M]` Chrome 151 ha **solo** la vecchia; Safari 26.4 e Firefox 151 hanno **solo** la nuova `[S]`. Una pagina che ne sa una sola perde tutto su metà dei motori |
| ⭐ **un dominio fidato non compra solo l'assenza dell'avviso: compra la tastiera** | `[M]` in finestra d'applicazione le riservate del browser sono **0**, contro 8 in una scheda normale |

---

## 3. La tavola delle misure — combinazione × motore × stato (dei tre)

*Tutte `[M]` **14 agosto 2026**, GNOME/Wayland (mutter), schermo 2560×1080, iniezione da
`org.gnome.Mutter.RemoteDesktop`. Chrome **151.0.7922.137**, Firefox **140.13.0esr**.
`[?]` = riga non credibile o non provata — ⛔ **non dedotta dalla cella accanto**.*

### 3.1 Il conto, palco per palco *(42 combinazioni provate, controlli compresi)*

| motore | palco | `preventDefault` | ✅ consegnate | ⛔ **consegnate E RISERVATE** | ⚠ non consegnate | di cui del **compositore** | di cui del **browser** |
|---|---|---|---|---|---|---|---|
| Chrome 151 | finestra | no | 11 | **18** | 13 | 5 | **8** |
| Chrome 151 | finestra | ⭐ **sì** | 29 | ⭐⭐ **0** | 13 | 5 | **8** |
| Chrome 151 | schermo intero (API) | no | 17 | **18** | 7 | 5 | ⭐ **2** (`F11`, `Escape`) |
| Chrome 151 | schermo intero (API) | ⭐ **sì** | 35 | ⭐⭐ **0** | 7 | 5 | ⭐ **2** |
| Chrome 151 | schermo intero **+ lock vecchia** | no | 37 | ⭐⭐ **0** | 5 | 5 | ⭐⭐ **0** |
| Chrome 151 | schermo intero + *«lock nuova»* | no | 17 | **18** | 7 | 5 | **2** ⛔ *identico al palco senza lock* |
| Chrome 151 | schermo intero da **`F11`** + lock chiesta | no | 18 | **18** | 6 | 5 | **1** ⛔ *la lock non c'è* |
| Chrome 151 **`--app`** | finestra d'applicazione | no | 21 | 16 | 5 | 5 | ⭐⭐ **0** |
| Chrome 151 **`--app`** | schermo intero (API) | no | 20 | 16 | 6 | 5 | **1** (`Escape`) |
| Chrome 151 **`--app`** | schermo intero + lock | no | 37 | **0** | 5 | 5 | **0** |
| Firefox 140 | finestra | no | 13 | **15** | 6 | 1 | **5** |
| Firefox 140 | finestra | ⭐ **sì** | 28 | ⭐⭐ **0** | 5 | 0 | **5** |
| Firefox 140 | schermo intero (API) | no | 16 | 10 | 8 | 1 | ⛔ **7** |
| Firefox 140 | + lock (qualunque forma) | — | ⛔ **non esiste** — §3.3 | | | | |
| Safari / WebKit | tutti | — | `[?]` | `[?]` | `[?]` | `[?]` | `[?]` |

⚠ **Perché su Firefox il compositore conta 1 e non 5**: le righe di `Alt+Tab`, `Alt+F2` e `Alt+F4`
su Firefox sono state **buttate dalla regola di credibilità** (§4.1), non misurate diversamente.
⛔ Restano `[?]`, e **non si copiano dalla colonna di Chrome**.

### 3.2 ⛔ Le tre righe che cambiano una tesi

| | la tesi | la misura |
|---|---|---|
| **1** | `[R]` *«la lista riservata di Chrome è di dodici comandi; a schermo intero scende a due — `F11` e l'uscita — senza chiamare nessuna API»* | ⭐ **CONFERMATA nella forma, su Chrome**: `[M]` **8 → 2**, e le due sono **esattamente `F11` ed `Escape`**. ⚠ Otto e non dodici perché il mio campione non conteneva tutti e dodici i comandi: il **rapporto** è quello previsto, il **numero assoluto** non è confrontabile |
| **2** | la stessa riga, letta come se valesse per tutti i motori | ⛔ **FALSA su Firefox**: `[M]` a schermo intero Firefox 140 **peggiora** — da 5 riservate a **7**, perché aggiunge `F11` ed `Escape` e **non molla nessuna** delle cinque di scheda. ⇒ *«a schermo intero scende a due»* è **un fatto di Chrome**, e va scritto così |
| **3** | `[S]` *«su Firefox `Ctrl+Tab` è qui [nello stato **consegnata e riservata**]: sembra intercettabile e non lo è»* | ⛔ **FALSA**: `[M]` su Firefox 140 `Ctrl+Tab` è nel **terzo** stato, **non consegnata** — la pagina non vede nemmeno il `keydown` (i modificatori arrivano, `Tab` no). ⚠ Lo **stato di mezzo esiste eccome**, ma i suoi esempi sono altri: `Ctrl+L`, `Ctrl+F`, `F5`, `Ctrl+R`, `Ctrl+P`, `F12` |

### 3.3 Le due forme della lock, e la trappola dell'`F11` — `[M]`

| | |
|---|---|
| ⛔ **Chrome 151 NON ha la forma nuova** | `[M]` l'opzione `keyboardLock` di `requestFullscreen` **non viene nemmeno letta** (provato con un dizionario che registra chi legge la chiave), e il palco che ne risulta è **identico riga per riga** a quello senza lock: 18 riservate, 2 non consegnate. ⭐ È il ripiego silenzioso di `CODER.md` §4.2 colto sul fatto: il motore va a schermo intero **senza dire** che la lock non gliel'ha data |
| ⛔ **Firefox 140 ESR non ha NESSUNA delle due** | `[M]` `navigator.keyboard` assente **e** opzione mai letta. ⇒ I palchi «con lock» **non si sono potuti montare**, e il banco ha **rifiutato di certificarli** invece di pubblicare righe etichettate «con lock» misurate senza |
| ⛔ **La lock dopo `F11` non esiste, e non lo dice** *(O10, prima metà)* | `[M]` entrato a schermo intero con `F11`, `navigator.keyboard.lock()` **non solleva nessun errore** e il palco resta quello **senza** lock: 18 riservate contro 0. ⇒ **CONFERMATA**, ed è la trappola più insidiosa perché l'unico modo di accorgersene è misurare il comportamento, non l'esito della chiamata |
| ⛔ **La lock muore alla perdita del fuoco** *(O10, seconda metà)* | ⭐ **CONFERMATA sul banco stesso**: senza ricomprarla prima di ogni prova, metà delle righe del palco «con lock» giravano **senza** lock. Il banco adesso la ricompra e scrive `lock_viva_alla_battuta` in ogni riga |

### 3.4 La tavola completa — ogni cella è una riga di `banchi/04-b29-esiti.jsonl`

*Legenda: ✅ **consegnata** (arriva e basta) · ⛔ **RIS** = **consegnata E RISERVATA** (arriva *e* il browser fa anche il suo) · ⚠ **NO** = **non consegnata** · `[?]` = riga non credibile o palco non montato, ⛔ **non dedotta dalla colonna accanto**.*

| combinazione | Cr finestra | Cr finestra +prevDef | Cr intero | Cr intero +prevDef | Cr intero+LOCK | Cr F11 | Cr --app finestra | Ff finestra | Ff finestra +prevDef | Ff intero |
|---|---|---|---|---|---|---|---|---|---|---|
| `Alt+ArrowLeft` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `Alt+ArrowRight` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `Alt+D` | ⛔ RIS | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⛔ RIS | ✅ | ✅ |
| `Alt+F2` | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | `[?]` | `[?]` | `[?]` |
| `Alt+F4` | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | `[?]` | `[?]` | `[?]` |
| `Alt+Home` | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ⛔ RIS |
| `Alt+Tab` | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | `[?]` | `[?]` | `[?]` |
| `Ctrl+1` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `Ctrl+9` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `Ctrl+A` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `Ctrl+C` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `Ctrl+D` | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ⛔ RIS |
| `Ctrl+E` | ⛔ RIS | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `Ctrl+F` | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ⛔ RIS | ⛔ RIS | ✅ | ⛔ RIS |
| `Ctrl+H` | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ⛔ RIS | ⛔ RIS | ✅ | ✅ |
| `Ctrl+J` | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ⛔ RIS | ⛔ RIS | ✅ | ✅ |
| `Ctrl+L` | ⛔ RIS | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⛔ RIS | ✅ | ✅ |
| `Ctrl+N` | ⚠ NO | ⚠ NO | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ⛔ RIS | `[?]` | `[?]` | `[?]` |
| `Ctrl+O` | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ✅ | ✅ | ✅ | `[?]` |
| `Ctrl+P` | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ⛔ RIS | ⛔ RIS | ✅ | ⛔ RIS |
| `Ctrl+PageDown` | ⚠ NO | ⚠ NO | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠ NO | ⚠ NO | ⚠ NO |
| `Ctrl+PageUp` | ⚠ NO | ⚠ NO | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠ NO | ⚠ NO | ⚠ NO |
| `Ctrl+Q` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `[?]` | `[?]` | `[?]` |
| `Ctrl+R` | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ⛔ RIS | ⛔ RIS | ✅ | ⛔ RIS |
| `Ctrl+S` | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ⛔ RIS | ✅ | ✅ | ✅ |
| `Ctrl+Shift+I` | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ⛔ RIS | ⛔ RIS | ✅ | ⛔ RIS |
| `Ctrl+Shift+J` | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ⛔ RIS | ⛔ RIS | ✅ | ⛔ RIS |
| `Ctrl+Shift+N` | ⚠ NO | ⚠ NO | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ⛔ RIS | `[?]` | `[?]` | `[?]` |
| `Ctrl+Shift+Tab` | ⚠ NO | ⚠ NO | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠ NO | ⚠ NO | ⚠ NO |
| `Ctrl+T` | ⚠ NO | ⚠ NO | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ⛔ RIS | ⚠ NO | ⚠ NO | `[?]` |
| `Ctrl+Tab` | ⚠ NO | ⚠ NO | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠ NO | ⚠ NO | ⚠ NO |
| `Ctrl+U` | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ⛔ RIS | ⛔ RIS | ✅ | ⛔ RIS |
| `Ctrl+V` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `Ctrl+W` | ⚠ NO | ⚠ NO | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ⛔ RIS | `[?]` | `[?]` | `[?]` |
| `Ctrl+Z` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `Escape` | ✅ | ✅ | ⚠ NO | ⚠ NO | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠ NO |
| `F11` | ⛔ RIS | ✅ | ⚠ NO | ⚠ NO | ✅ | ⚠ NO | ⛔ RIS | ⛔ RIS | ✅ | ⚠ NO |
| `F12` | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ⛔ RIS | ⛔ RIS | ✅ | ⛔ RIS |
| `F5` | ⛔ RIS | ✅ | ⛔ RIS | ✅ | ✅ | ⛔ RIS | ⛔ RIS | ⛔ RIS | ✅ | ⛔ RIS |
| `Super+KeyD` | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | `[?]` | ⚠ NO |
| **controllo + Ctrl+Alt+G** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **controllo − Super** | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | ⚠ NO | `[?]` | `[?]` | `[?]` |

⭐ **Le due colonne che riassumono tutto**: `Cr intero+LOCK` non ha **nemmeno un** ⛔ né un ⚠ che non sia del compositore; e ogni colonna `+prevDef` non ha **nemmeno un** ⛔.

---

## 4. ⛔ Che cosa NON ha funzionato

### 4.1 I giri buttati, e perché

| | che cosa | come me ne sono accorto |
|---|---|---|
| ⛔ | **Il primo giro intero di Chrome è stato buttato.** La pagina armava il gesto con `gesto_in_attesa = o`, cioè un oggetto la cui `azione` valeva `"gesto"` e non `"schermo_intero"`: nessun ramo lo riconosceva, **non faceva niente**, e rispondeva **`riuscita: true`**. ⇒ Tre palchi su cinque hanno girato con la pagina **in finestra credendosi a schermo intero** | ⭐ **dalla verifica, non dal codice**: il pilota non si fida della riuscita dichiarata e rilegge `document.fullscreenElement` dalla pagina. È `CODER.md` §3.9 — *chiedi il componente per nome, e verifica che abbia obbedito* — ed è l'unica ragione per cui quel giro è stato buttato invece di pubblicato |
| ⛔ | **Un palco intero perso per l'angolo caldo di GNOME.** Il puntatore veniva parcheggiato in alto a sinistra prima di contare: lì c'è l'**angolo caldo**, che apre la panoramica delle Attività, che si prende il fuoco — e la prova dopo risultava «non misurata». ⇒ Adesso si parcheggia in **basso a destra** | dal cancello del fuoco, che ha rifiutato di misurare invece di stampare zeri |
| ⛔ | **«Il browser non prende il fuoco» su un browser sanissimo.** Un giro interrotto da `timeout` lasciava una finestra **a schermo intero e in cima a tutto**; il giro dopo apriva la sua *dietro* quella, e il clic di messa a fuoco finiva nella finestra vecchia | dal fatto che l'esito era «non aperto» invece di essere sbagliato. ⇒ Adesso si ammazzano i resti **per profilo** (mai `pkill chrome`: spegnerebbe quello dell'utente) |
| ⚠ | **`Escape` nel ripristino distruggeva il palco che doveva ripristinare**: a schermo intero da API `Escape` **esce dallo schermo intero**. ⇒ Adesso prima si guarda, e si tocca solo se è rotto | dal confronto fra il palco montato e il palco letto alla battuta |
| ⚠ | **`GetCurrentState` letto male**: nel monitor *logico* l'indice 2 è la **scala** e il 3 la **trasformazione**. Il banco stampava «schermo 1x0» **e girava lo stesso** | perché un numero sbagliato non si annuncia (`CODER.md` §3.10) |
| ⛔ | **Il salvaschermo ferma il banco, e non con un errore che lo dica**: dopo 10 minuti GNOME annerisce, e da lì `RemoteDesktop.CreateSession` risponde **«Session creation inhibited (0)»** — un messaggio che non nomina né il salvaschermo né l'inattività. ⇒ Adesso il banco sveglia lo schermo e **trattiene l'inattività con un inibitore**, ⛔ **non** riscrivendo `idle-delay`: una preferenza dell'utente riscritta da un banco è l'invariante **I7** al rovescio | dal fatto che moriva all'avvio invece che a metà |
| ⚠ | **Una debolezza del mio strumento, e la dichiaro invece di correggerla in silenzio**: `lock_viva_alla_battuta` si leggeva da un battito vecchio fino a 500 ms, quindi **poteva dire «no» su una lock viva**. ⚠ Mentiva **verso il pessimismo**, cioè nel verso in cui gli errori non si notano. ⇒ Corretto (si aspetta un battito nuovo), ma ⛔ **le righe della campagna di Chrome sono state scritte prima della correzione**: lì il campo attendibile è `lock_ricomprata.ok`, non `lock_viva_alla_battuta` | rileggendo le righe del palco «con lock», dove `Ctrl+T` e `Ctrl+W` risultavano consegnate con la lock dichiarata morta |

### 4.2 ⛔ Che cosa non ho potuto misurare affatto

| | | perché | con che strumento si chiude |
|---|---|---|---|
| ⛔ | **`Ctrl+Alt+Canc` non è stata iniettata** | su GNOME è legata alla **finestra di disconnessione**, che dopo 60 s **disconnette la sessione dell'utente**. ⛔ *Un banco non spegne la macchina su cui gira* | non si chiude, e **non serve chiuderla**: la sua sorte si legge dal caso `Super` — quel che prende il compositore, il browser non lo vede mai. ⭐ È esattamente la ragione per cui O7 chiede un **bottone a schermo** invece di una scorciatoia |
| ⛔ | **`Ctrl+Shift+W`** (chiude la finestra) | avrebbe chiuso il browser a ogni riga senza aggiungere niente a `Ctrl+W` e `Alt+F4`, già misurate | una macchina dedicata |

### 4.3 ⛔ I motori che NON ho avuto sotto mano — `[?]`, e non dedotti

⛔ **Un motore non provato si scrive `[?]`. Non si deduce dagli altri: quel che si perde su Chrome
non è quel che si perde su Safari** (`SPECIFICHE.md` §11.5).

| motore | stato | con che strumento si chiuderebbe |
|---|---|---|
| **WebKit / Safari** (incluso Safari 26.4, che ha la forma nuova `[S]`) | ⛔ **`[?]` per intero** — nessun ferro Apple sul banco | un Mac con Safari 26.4+, e questo stesso banco: l'iniezione si riscrive su `CGEventPost`, il resto della sonda è la stessa pagina |
| **iPhone** — «schermo intero parziale in tutte le versioni» *(O9)* | `[S]`, non verificato | un iPhone e la stessa pagina: basta leggere `document.fullscreenEnabled` e provare `requestFullscreen` |
| ⭐ **Keyboard Lock su DeX** | ⛔ **`[?]`, e resta la `[?]` che pesa di più** perché DeX è **l'uso primario dichiarato** (`DECISIONI.md` §5-bis.0) | un telefono Samsung con Android 16 QPR1+ e un DeX: la pagina è già pronta (`banchi/04-b29-pagina.html`), il pilota va sostituito con una tastiera **fisica** e un osservatore via `chrome://inspect` |
| ⭐ **PWA su Chrome per Android** | ⛔ **`[?]`** — ⚠ e **non si deduce dalla misura della finestra d'applicazione su Linux**, che è un altro sistema di finestre e un'altra regola di riserva | lo stesso telefono, la pagina **installata** (serve un certificato fidato: dietro l'eccezione il Service Worker non si installa `[R]`) |
| **Firefox ≥ 151**, che ha la forma nuova `[S]` | ⛔ **`[?]`** — sul banco c'era **Firefox 140 ESR** | un Firefox 151 e questo stesso banco, senza cambiare una riga |
| **Edge** | `[?]` — non installato | idem |

### 4.4 ⛔ Il giro di Firefox che è stato buttato, e come me ne sono accorto

Il **primo** giro di Firefox è uscito *«non consegnata»* su **tutte e 42** le combinazioni,
`Ctrl+C` compreso. ⛔ Numeri perfettamente verosimili — *«Firefox si tiene tutto»* — e interamente
falsi.

⭐ **A salvarlo è stato un campo per riga**: `modificatori_visti` diceva **«nemmeno i modificatori
sono arrivati»**, che è la firma dell'**iniezione che non entra**, non della scorciatoia riservata.
Con i timbri accanto, la ricostruzione è esatta:

| ora | | |
|---|---|---|
| **08:32:30** | controllo **positivo** `Ctrl+Alt+G` | ✅ **consegnata** — la catena funzionava |
| **08:32:32** | controllo **negativo** `Super` | apre la panoramica di GNOME, che si prende la tastiera |
| **08:32:34 → 08:33:51** | tutte le altre 40 | ⛔ **nessuna arriva**, e Firefox continua a dichiarare **`fuoco: true`** per tutto il tempo |

⛔ **Da cui due fatti, e il secondo è il più utile:**

1. `[M]` **`document.hasFocus()` non è un testimone attendibile su Firefox 140 / Wayland**: resta
   `true` mentre la tastiera è altrove. ⚠ Ed è una `[?]` che riguarda **anche il prodotto**, non
   solo il banco: la nostra pagina non può fidarsi di `hasFocus()` per decidere se sta ricevendo;
2. ⭐ **il controllo negativo si era rotto il palco da solo.** Il `Super` che *deve* essere preso dal
   compositore fa esattamente il danno che poi impedisce di misurare. ⇒ Adesso il ripristino chiude
   sempre quel che ha aperto, **e** il cancello si prova invece di fidarsi.

⇒ **La cura, ed è il pezzo di metodo che porto via da questa sonda**: non si chiede alla pagina se
**crede** di avere il fuoco — le si chiede di **dimostrare che riceve i tasti**, ora, con un `F9`
innocuo, **prima di ogni singola battuta**. Se non lo dimostra, si scrive `NON-MISURATA`.

⛔ **E la regola che ne discende governa la tavola**: *una riga è una misura solo se si può
dimostrare che la battuta è arrivata da qualche parte* — la pagina ha visto la combinazione, **o**
il browser ha fatto qualcosa di visibile, **o** la pagina ha visto almeno un modificatore.
`[M]` su **594 righe** di misura scritte, **74 sono state buttate** da questa regola, e sono contate in
`banchi/04-b29-tavola.py`.

### 4.5 Che cosa ho messo nella pagina, e la cucitura che ho ASSUNTO da A7

Tutto dentro l'ancora `F4-SCORCIATOIE` di `src/pagina.html`, e **niente fuori**.

| | |
|---|---|
| ⭐ **il catalogo misurato** | le 9 righe `[M]` (famiglia × palco) generate da `banchi/04-b29-tavola.py --js`. ⛔ Costruito sul giro **con** `preventDefault()`, perché è quel che l'utente vedrà; dove quel giro manca, la voce si mostra come `[?]` invece che come perdita |
| ⭐ **le due forme della lock** | si prova **prima la nuova** (WHATWG), e l'opzione si passa dentro un oggetto che **registra se è stata letta** — l'unico modo di distinguere «me l'ha data» da «ha fatto finta di niente». Se non è letta, si ripiega su `navigator.keyboard.lock()`, e il ripiego si **dichiara** |
| ⭐ **le due trappole O10** | lo schermo intero da `F11` si riconosce dalla geometria (piena **e** `fullscreenElement` nullo) e si dichiara che lì la lock non esiste; alla perdita del fuoco la lock si segna **morta** e al ritorno si **ricompra**, dichiarando l'esito |
| ⭐ **la barra che dichiara** | compare da sola quando una delle due disposizioni entra in vigore, e dice **quel che si perde su questo motore, in questo palco, adesso** — non un elenco generico. Se il motore non è nel catalogo dice `[?]`, non tace |
| ⭐ **i cinque bottoni** *(O7)* | `Ctrl+Alt+Canc`, `Ctrl+W`, `Ctrl+T`, `Alt+F4`, `Super` |
| ⛔ **e non si finge mai** | se il canale non è cucito i bottoni si mostrano **spenti con la ragione scritta**; un `code` che non è in tabella **non si spedisce** |

**La verifica del bottone, `[M]` 14 agosto 2026** — perché un requisito asserito non è un requisito:
un clic su `Ctrl+Alt+Canc` produce **sei** messaggi `POSIZIONE_TASTO` (`0x0105`) con `id` crescente —

    29↓  56↓  111↓  111↑  56↑  29↑

cioè Ctrl, Alt, Canc premuti in ordine e rilasciati in ordine inverso, **come posizioni** e non come
lettere (`SPECIFICHE.md` §7.3).

> #### ⚠ LA CUCITURA CHE HO ASSUNTO DA A7 — la firma esatta, perché non sia una sorpresa
>
> ```js
> cl_spedisci(CL_TIPO.POSIZIONE_TASTO, codice_evdev, giu ? 1 : 0, ms)
> CL_POSIZIONE[code]        // KeyboardEvent.code → evdev
> CL_TIPO.POSIZIONE_TASTO   // 0x0105
> ```
>
> ⛔ **Non ho chiesto nulla di nuovo ad A7**: uso quel che c'è già, e la presenza si verifica a
> runtime (`sc_filo_cucito()`). ⚠ Se A7 rinomina `cl_spedisci`, i bottoni **si spengono e lo
> dicono** invece di rompersi in silenzio — ma vale la pena saperlo prima.
>
> ⭐ **E la divisione con A7 è netta**: lo **schermo intero** e la **Keyboard Lock** sono miei
> (sono le due leve che decidono *che cosa arriva*); il **rilascio dei tasti premuti alla perdita
> del fuoco** è suo, ed è già scritto — **non l'ho duplicato**.

### 4.6 Il secondo strumento, e dove non c'è

⛔ Su **Chrome** ogni riga ha due strumenti: la pagina *e* il conto dei bersagli del protocollo di
debug. Su **Firefox 140 ESR** `--remote-debugging-port` **non serve `/json/list`**: `[M]` il secondo
strumento **non c'è**, e le righe di Firefox stanno su un solo strumento. ⚠ È scritto in ogni riga
(`secondo_strumento: false`) e non dedotto dal silenzio.

---

## 5. Le righe da riscrivere, col numero

⛔ **Non le ho toccate io**: `SPECIFICHE.md` e `web.md` sono del deposito e le riscrive il
coordinatore a codice fermo. Qui c'è la riga esatta, che cosa dice, e che cosa dovrebbe dire.

### 5.1 `SPECIFICHE.md` §7.3-bis

| riga | dice adesso | ⇒ va riscritta così |
|---|---|---|
| **596** | `keyboardLock` è entrato nello standard WHATWG… Chrome ed Edge restano sulla forma vecchia — la pagina deve saperle entrambe `[S]` | ⭐ **CONFERMATA e da promuovere a `[M]` per la metà misurabile**: `[M]` 14 ago 2026 **Chrome 151.0.7922.137 non legge nemmeno l'opzione `keyboardLock`**, e il palco che ne esce è identico a quello senza lock; `[M]` **Firefox 140 ESR non ha nessuna delle due forme**. La metà su Safari 26.4 / Firefox 151 resta `[S]` |
| ⛔ **597** | `[R]` la lista riservata di Chrome è di **dodici** comandi; **a schermo intero scende a due** — `F11` e l'uscita — **senza chiamare nessuna API**. Firefox ne ha **sei**, Safari **zero** | ⛔ **Da spaccare in due, perché letta così sembra una legge dei browser e invece è un fatto di Chrome.** Proposta:<br>• `[M]` **su Chrome 151 il crollo c'è ed è quello previsto**: in finestra **8 delle 42 provate** non arrivano affatto; a schermo intero **2**, ed è **esattamente `F11` ed `Escape`** — senza chiamare nessuna API;<br>• ⛔ `[M]` **su Firefox 140 ESR NON crolla: PEGGIORA.** In finestra ne tiene **5**, a schermo intero **7** (aggiunge `F11` ed `Escape` e non molla le altre);<br>• Safari resta `[S]` **zero**, e diventa `[?]` finché non c'è un Mac. |
| ⛔ **605** | `consegnata e riservata` … **su Firefox `Ctrl+Tab` è qui**: *sembra intercettabile e non lo è* | ⛔ **L'esempio è FALSO e va sostituito.** `[M]` su Firefox 140 `Ctrl+Tab` sta nel **terzo** stato: la pagina non vede il `keydown` (i modificatori arrivano, `Tab` no). ⭐ Lo stato di mezzo **esiste ed è largo** — `[M]` **18 su 42** su Chrome in finestra, **15 su 42** su Firefox — e i suoi esempi veri sono `Ctrl+L`, `Ctrl+F`, `F5`, `Ctrl+R`, `Ctrl+P`, `F12`, `Ctrl+S` |
| **598** | ⭐ e in una PWA installata è vuota `[R]` | ⭐ **Da promuovere a `[M]` per il desktop**: `[M]` 14 ago 2026, Chrome 151 aperto con `--app=` (lo stesso ramo «Apps mode» del codice letto), **0 riservate dal browser già in finestra**, `Ctrl+W`/`Ctrl+T`/`Ctrl+N` comprese, contro 8 in una scheda normale. ⚠ **La metà Android resta `[?]` e non si deduce da qui** |
| **611** e **615-619** | *«Quel che si perde davvero, e non si recupera»* — `Ctrl+Alt+Canc`, l'uscita da schermo intero, iPhone, macOS, Android/DeX | ⚠ **Manca la riga che la misura mette in cima**: `[M]` **quel che non si recupera è del COMPOSITORE DEL CLIENT, non del browser** — su GNOME/Wayland `Super`, `Super+D`, `Alt+Tab`, `Alt+F2`, `Alt+F4` restano perse **in tutti e cinque i palchi**, lock compresa. ⇒ **La riga `Ctrl+Alt+Canc` non è un caso isolato: è il capofila di una famiglia**, e il bottone a schermo serve a tutta la famiglia |
| **616** | l'uscita da schermo intero — **ovunque, per costruzione** | ⚠ **Non è «ovunque»**: `[M]` su Chrome 151 **con la lock, `Escape` e `F11` arrivano alla pagina** (0 riservate). L'uscita resta garantita dalla **pressione prolungata** di `Escape`, non dalla battuta singola. ⇒ va detto così, perché come è scritta contraddice la riga 597 dello stesso paragrafo |
| **624-628** | ⚠ le due trappole della lock *(O10)* | ⭐ **CONFERMATE tutt'e due, `[M]`**, e la prima con il numero: entrato con `F11`, `lock()` **non solleva errore** e il palco resta quello senza lock — **18 riservate contro 0** |
| **630-631** | `[?]` Keyboard Lock su **DeX**, PWA su **Chrome per Android** | ⛔ **Restano `[?]` tutt'e due** — non ho né telefono né DeX. ⚠ **La seconda NON va chiusa con la mia misura `--app`**: una finestra d'applicazione su Linux non è una PWA su Chrome per Android. Lo strumento che le chiude è in §4.3 |

### 5.2 `web.md`

| riga | dice adesso | ⇒ |
|---|---|---|
| **301** | la stessa affermazione 12 → 2 / Firefox 6 / Safari 0 `[R]` | stessa spaccatura della riga 597 di `SPECIFICHE.md` |
| ⛔ **308** | `Ctrl+Alt+Canc` — **ovunque, e non è recuperabile** | ⛔ **Contraddice già O8-O10 nello stesso documento** (§8-bis O7 dice il contrario), e adesso anche la misura: è **recuperabile dall'interfaccia**, e il bottone esiste ed è verificato `[M]` (§4.5 di questo rapporto). ⇒ *«non dal filo, ma dall'interfaccia»* |
| **302** | `// In Apps mode, no keys are reserved` `[R]` | ⭐ `[R]` → **`[M]` sul desktop** (vedi 598) |
| **482-483** | il piano delle misure **S3a** (lock su DeX) e **S3b** (PWA su Chrome per Android) | restano **aperte**; ⭐ **il banco è pronto e gira**: `banchi/04-b29-*`, e sul telefono cambia solo l'iniettore |
| **§5** intestazione (riga **291**) | *«96 `[R]`, 103 `[S]`, 23 `[?]`, **zero `[M]`**»* | ⭐ **non è più vero**: da oggi S3 ha **520 righe `[M]` credibili** (su 594 scritte) su disco in `banchi/04-b29-esiti.jsonl`, su **due motori** e **cinque palchi** |

### 5.3 `PIANO.md` e `fasi/04-si-comanda.md`

| | |
|---|---|
| `fasi/04-si-comanda.md` riga **50** | la sottofase **A9** può passare da ⏳ a ✅ per i **due motori sul ferro**, con la `[?]` di Safari e quella di DeX/Android **esplicite** |
| `fasi/04-si-comanda.md` riga **93** | la `[?]` n. 3 (lock su DeX, PWA su Chrome per Android) **resta aperta**, e adesso ha il banco pronto accanto |
| `PIANO.md` riga **621-624** | *«qui si scopre che cosa il browser si tiene: `Ctrl+W`, `Ctrl+T`, `F11`»* ⇒ ⭐ **si può chiudere con il numero**: `[M]` con schermo intero e lock su Chrome **non si perde nessuna delle tre**; si perdono le cinque del **compositore** |
