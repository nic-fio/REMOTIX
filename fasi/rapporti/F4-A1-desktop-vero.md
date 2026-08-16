# F4 · A1 — Il desktop vero, portato dentro il prodotto

*14 agosto 2026. Anello **A1** della fase 4, ⭐ la priorità decisa dall'utente.
Banco `banchi/04-b20-*`, porta **7601**, utente di banco **`provaa1`** (uid 1002).
⛔ `nicfio` e `prova` non sono stati toccati: le loro sessioni sono ancora una ciascuna,
e le porte 7448 · 7501 · 7561 · 7571 sono rimaste a due ascoltatori dall'inizio alla fine.*

---

## 1. Che cosa cambia per l'utente

⭐ **Collegandosi vede il suo desktop — barra, orologio, dock, finestre — e non più uno
schermo azzurro vuoto.**

*(Si guarda adesso: `https://192.168.0.2:7601/` come `provaa1`, parola `provaa1-2026`.
Il server è lasciato acceso apposta, con una finestra che scrive l'ora.)*

---

## 2. Serve una decisione di Nic?

**No** sulla cura. ⚠ **Sì su una cosa sola, e non è tecnica**: la cura fa nascere una sessione
che, **finché nessuno si collega, non ha nessuno schermo**. Per una macchina che serve *solo* da
remoto è giusto; se un giorno la vuoi anche usare da davanti, o vuoi che un programma parta e
disegni prima che tu ti colleghi, quella sessione non ha dove disegnare. ⇒ **Serve sapere da te
se REMOTIX serve una macchina SOLO remota** (allora è finita così) **o anche una macchina che
lavora da sola** (allora ci vuole una seconda strada, e va progettata).

---

## 3. Che cosa ho MISURATO

### 3.1 ⛔⛔ La tesi che mi era stata data è **vera sui pixel e falsa come causa**

> *«Togliendo `--virtual-monitor` da `sessione.c:650` e cambiando il controllo di `sessione.c:668`,
> l'utente vede il suo desktop vero, e non si rompe nient'altro.»*

| | |
|---|---|
| «l'utente vede il desktop vero» | ⭐ **VERO**, e misurato: §3.3 |
| «basta cambiare `:650` e `:668`» | ⛔ **FALSO**: la cura è in **quattro** posti, §3.4 |
| «non si rompe nient'altro» | ⛔ **FALSO**: con due soli, `sessione_assicura()` **distrugge la sessione giusta a ogni chiamata**, §3.4 |
| «cambiare `:650` fa vedere il desktop **oggi**» | ⛔ **FALSO**: quella riga **non la esegue nessuno**, §3.2 |

### 3.2 ⛔ `sessione.c:650` non è mai stato eseguito su questa macchina

`[R]` `scrivi_dropin()` è chiamata **solo** da `sessione_assicura()`; e `sessione_assicura()`
**non la chiama nessuno nel prodotto**: `main.c:519-535` l'ha tolta il 12 agosto («il palco non si
prende più qui»), e `figlio.c:1870-1875` dichiara di **guardare e non toccare** — chiama
`sessione_stato()`, che non scrive niente. ⇒ Il prodotto vivo **non crea nessuna sessione: riusa
quella che trova**.

`[M]` 14 agosto 2026, 06:30 — chi chiede davvero `--virtual-monitor` su questa macchina:

```
/etc/systemd/user/org.gnome.Shell@wayland.service.d/remotix-headless.conf
[Service]
ExecStart=
ExecStart=/usr/bin/gnome-shell --headless --no-x11 --virtual-monitor 1920x1080
```

⛔ Un drop-in **di sistema**, root, del 12 agosto, che vale per **qualunque utente** — e nessun
`user.control/…/zz-remotix-monitor.conf` esisteva né per uid 1000 né per 1001. ⇒ ⭐ **È
esattamente «la riga di configurazione che si può perdere» che l'invariante I7 vieta**, e la
protezione che `sessione.h` racconta di aver messo nel programma **nel programma non c'è ancora
arrivata**: c'è la funzione, non c'è chi la chiama.

`[M]` lo stesso momento, i tre utenti:

| utente | riga di comando della Shell | monitor (`GetCurrentState`) |
|---|---|---|
| `nicfio` 1000 | `--headless --no-x11 **--virtual-monitor 1920x1080**` | **3**: `Meta-0` *MetaVirtualMonitor* + due *Virtual remote monitor* |
| `prova` 1001 | `--headless --no-x11` | **1**: `Meta-0` *Virtual remote monitor* ⇒ ⭐ è il `RecordVirtual` del 7571, e la shell ci sta sopra |

⇒ Il desktop vero, oggi, si vede su `prova` **per via di un drop-in scritto a mano il 14 agosto**,
non per via del prodotto.

### 3.3 ⭐⭐ L'A/B, con il banco `04-b20`, dallo stesso strumento e nello stesso quarto d'ora

**Come il banco distingue la shell dallo sfondo** — la domanda che ha nascosto il difetto per due
fasi (*«è lo sfondo GNOME, è OK»*). Due indicatori di natura **diversa**, calibrati `[M]` su due
immagini vere prima di fissare le soglie:

| | che cosa misura | soglia | shell | sfondo |
|---|---|---|---|---|
| **B** — *geometrico* | il **salto** di luminanza fra due righe vicine, cercato fra la riga 20 e la 48: la barra finisce **di netto**, uno sfondo no | > 4 | **11,8** | **0,07** |
| **T** — *di contenuto* | i **fronti** orizzontali nel terzo centrale della fascia alta: è il testo dell'**orologio** | ≥ 40 | **565** | **0** |
| D — *scartato* | il dettaglio in basso al centro contro le stesse righe ai lati | — | 0,069 | 0,082 ⇒ ⛔ **non distingue, e si dichiara** |

⛔ **La prima stesura di B era sbagliata e l'ha smentita la calibrazione**: cercava un *gradino*
fra la barra scura e lo sfondo chiaro sotto. Su una sessione appena aperta GNOME è in
**panoramica**, e sotto la barra c'è grigio scuro: il gradino vale **7**, sotto soglia ⇒ il banco
avrebbe detto **VUOTO sul desktop vero**. ⇒ Non si è allargata la soglia: si è cambiata la
grandezza.

⭐ **Controllo dello strumento** (`04-b20-lancia.sh certifica`, senza prodotto e senza GNOME): due
immagini fabbricate con `ffmpeg`, una col solo sfondo colorato e una con barra + testo + icone.
Il giudice dice **VUOTO** e **SHELL**. Un giudice che non sa dire di sì non ha diritto di dire di no.

**Le misure** `[M]` 14 agosto 2026, macchina 192.168.0.2, utente `provaa1`, porta 7601,
scena dichiarata: *una finestra di terminale che scrive l'ora cinque volte al secondo*
(`04-b20-lancia.sh scena`), sessione GNOME appena aperta.

| giro | ExecStart della Shell | monitor prima → durante | fotogrammi al client in 40 s | verdetto |
|---|---|---|---|---|
| ⛔ **rosso** `rosso-scena-2` | **con** `--virtual-monitor` | 1 → **2** (`MetaVirtualMonitor` + `Virtual remote monitor`) | **0** — e il prodotto dichiara *«116 attese a vuoto, **0 guasti**»* | **NESSUN FOTOGRAMMA** |
| ⛔ **rosso** `rosso-prima-grezzo` *(lato che manda)* | idem | 1 → 2 | il fotogramma catturato | **VUOTO** — B 0,01 · T 0 |
| ⭐ **verde** `verde-scena` | **senza** (la cura) | 0 → **1** (`Virtual remote monitor`) | **205, tutti conformi** | ⭐ **SHELL** — B 5,2 · T 511 · D 0,075 contro 0/0 |
| ⭐ **verde** `verde-dopo-grezzo` *(lato che manda)* | idem | 0 → 1 | il fotogramma catturato | ⭐ **SHELL** — B **51,32** alla riga **32** · T **548** |

⭐ **E il fotogramma verde è stato guardato con gli occhi** (I8): barra con «Aug 14 07:10», campo
di ricerca, **due finestre di terminale che scrivono l'ora**, dock con Firefox, File, Terminale e
la griglia delle applicazioni. Il rosso è **solo lo sfondo Debian**, senza una riga di barra.
*(`/media/REMOTIX/tmp/04-b20/verde-scena-fotogramma.png` e `rosso-prima-grezzo-fotogramma.png`.)*

⛔⛔ **E il rosso ha una faccia peggiore di quella attesa: ZERO fotogrammi, non «un fotogramma
vuoto».** Sullo schermo in più **non cambia mai niente**, e la cattura consegna solo quando
qualcosa cambia (`cattura.h`, `framerate 0/1`). ⇒ Con `--virtual-monitor` in vigore l'utente non
riceve **un solo pixel**, e il client chiede una chiave ogni secondo per sempre. ⭐ Che lo zero sia
un vero zero e non un guasto lo dice il prodotto stesso: **`0 guasti`** accanto alle attese a vuoto
(`CODER.md` §3.10 che morde a favore nostro).

### 3.4 ⛔ La cura è in QUATTRO posti, non due — e i due in più erano quelli che rompevano

Tutti in `src/sessione.c`, e nient'altro è stato toccato.

| | dove | prima | dopo |
|---|---|---|---|
| **1** | `scrivi_dropin()`, la riga dell'`ExecStart` | `--headless --no-x11 --virtual-monitor %ux%u` | `--headless --no-x11` |
| **2** | `scrivi_dropin()`, il controllo «scritto non è in vigore» | pretendeva `--virtual-monitor %ux%u` ⇒ ⛔ avrebbe fatto **fallire il prodotto curato** | pretende `--headless --no-x11` **e pretende l'ASSENZA di `--virtual-monitor`** ⇒ ⭐ così si accorge del drop-in di sistema di §3.2, che vale per tutti |
| **3** | `sessione_assicura()`, ramo `SESSIONE_NERA` | *«la faccio RINASCERE»* ⇒ ⛔ **avrebbe ucciso la sessione giusta a ogni chiamata, all'infinito** | non la tocca: zero monitor propri **è il fine** |
| **4** | `sessione_assicura()`, rami `SANA` / `MISURA_ALTRA` e l'attesa dopo l'avvio | `SANA` = «non tocco niente», e si aspettava **il monitor** | `SANA` = ⛔ **è il difetto** ⇒ rinasce; si aspetta la sessione **senza monitor propri** |

⭐ **Il ragionamento del punto 3-4 è quello di `sessione.h`, rovesciato**: un monitor
`MetaVirtualMonitor` esiste **solo** se qualcuno ha passato `--virtual-monitor`, cioè solo in una
sessione headless — cioè nostra. Buttarla giù non porta via niente a nessuno. ⚠ **Ma solo se i
monitor sono UNO**: se sono due c'è una cattura viva sopra (`SCELTO_DA_SE`), e farla rinascere
toglierebbe il desktop a un client attaccato (I4). Quel ramo adesso non tocca niente in nessun caso.

**La cura provata dal PRODOTTO, non dal banco** (`CODER.md` §3.6 — `banchi/04-b20-nasci.c`, 55
righe, chiama `sessione_assicura()` e restituisce il suo numero) `[M]` 14 ago 07:08:

```
⛔ LA SESSIONE HA UN MONITOR SUO («Meta-0» «MetaVirtualMonitor» 1920x1080): è il difetto del
   desktop invisibile … La faccio RINASCERE senza monitor propri
⭐ la sessione nascerà SENZA monitor propri, e lo chiede il PROGRAMMA
   (/run/user/1002/systemd/user.control/…/zz-remotix-monitor.conf)
⭐ sessione grafica pronta e SENZA monitor propri
assicura: 1 NERA: ZERO MONITOR (l'ho fatta nascere io: si)
```

⚠ **E il numero d'uscita atteso è cambiato**: la sessione remota sana adesso è **1 NERA**, non
**0 SANA**. Chi legge quel numero senza aver letto questo rapporto lo prenderà per un guasto.

### 3.5 ⛔⛔ Chi decide la misura del monitor — e che cosa succede se il client ne chiede un'altra

*(È il punto 1 delle due cose da misurare prima di crederle. Non è stato dedotto.)*

**Chi decide**: `[R]` `RecordVirtual` **non prende nessuna misura** (`mutter.h:82-86` lo dice già).
Il monitor lo crea `create_virtual_monitor()` con `video_format->size`
(`reference-gnome/mutter/src/backends/meta-screen-cast-virtual-stream-src.c:596-606`), cioè con la
misura **negoziata in PipeWire dal nostro consumatore** — che è
`cattura_avvia(…, tela_l, tela_a, …)` chiamata da `figlio.c:1898` con `TELA_L`/`TELA_A`, ⛔ **due
costanti di compilazione in `main.c:111-112`, `1920×1080`**. ⇒ ⭐ **La misura la decidiamo noi, e
oggi non è configurabile: è compilata dentro.** *(E `[R]` `ensure_virtual_monitor():634-645`
saprebbe pure cambiarla a caldo, con `meta_virtual_monitor_set_mode`, se rinegoziassimo il formato.)*

**Se il client chiede un'altra tela** — `[M]` 14 ago 07:15, client con `ATTACCA` a **1280×720**,
sessione curata, scena in movimento:

```
rcp  sessione aperta … tela=1280x720 vista=1280x720
rcp  ⭐ FASE 3: canale video ACCESO … tela 1280x720
rcp  ⛔ tela in vigore 1280x720 ma il fotogramma catturato è 1920x1080 — NON lo spedisco (§6.2)
figlio  ciclo: 145 fotogrammi consegnati (30 chiavi), 0 attese a vuoto, 0 guasti
```

⇒ ⛔⛔ **Il server CONCEDE una tela che non sa produrre.** `rcp.c:1817-1859` concede quella chiesta,
limitandola solo a `video.misura_massima`; poi il palco cattura a 1920×1080 e `rcp` — **con
ragione**, §6.2 — rifiuta ogni fotogramma. `[M]` **145 fotogrammi prodotti, 0 spediti, e il client
resta nero per sempre senza nessun errore.** ⭐ Il rifiuto è dichiarato nel registro, quindi il
difetto non è invisibile: è **la concessione** che è sbagliata.

⚠ E c'è un secondo corno, non ancora misurato `[?]`: la misura del monitor la fissa **il primo
client che si attacca**. Un secondo client con un'altra tela, se un giorno si rinegoziasse il
formato, **ridimensionerebbe il desktop sotto il primo**.

### 3.6 ⚠ La sessione prima del primo client è NERA — e adesso è di proposito

`[M]` `sessione_assicura()` sulla sessione curata dà **1 NERA / 0 monitor**, e ci resta finché non
arriva un client. Per una sessione **solo remota** è corretto e voluto (§2). ⇒ Le righe che dicono
il contrario sono al punto **6**.

**Dove si ricontrolla tutto**: `banchi/04-b20-lancia.sh` (`certifica` · `porta` · `costruisci` ·
`utente` · `nasci` · `scena` · `accendi` · `misura <etichetta> [tela]` · `rilievo` · `spegni` ·
`pulisci`); gli esiti in `/media/REMOTIX/tmp/04-b20/04-b20-esiti.jsonl`, il registro del server in
`/media/REMOTIX/tmp/04-b20/registro.log`, le immagini giudicate accanto.

---

## 4. ⛔ Che cosa NON ha funzionato

1. ⛔ **Il primo giro rosso con la scena in movimento (`rosso-scena`) era una misura FALSA, e l'ho
   pubblicata prima di accorgermene.** Il figlio che serviva quel client era **quello di prima**:
   sopravvive al distacco (I4) e io gli avevo ucciso la sessione sotto, quindi la sua cattura era
   morta. ⇒ «0 fotogrammi» c'era, ma per la ragione sbagliata. ⭐ **Me l'ha detto il prodotto**:
   *«la cattura non consegna più (presa 2: il flusso non è attivo…): questo NON è uno zero»*.
   Rifatto con un figlio nuovo (`rosso-scena-2`), lo zero è vero e porta accanto **`0 guasti`**.
   ⚠ *Se il prodotto non avesse distinto lo zero dal guasto, questa misura sbagliata sarebbe finita
   nel rapporto come buona.*
2. ⛔ **La marca del binario diceva «è il prodotto CURATO» sopra un binario NON curato.**
   `strings … | grep -q` sotto `set -o pipefail`: `grep -q` esce presto, `strings` prende SIGPIPE,
   la pipeline esce 141 e l'`if` prende il ramo sbagliato. ⚠ **Ha sbagliato nella direzione che
   assolve**, cioè quella che non si vede. Adesso si conta invece di interrogare la pipeline.
3. ⛔ **La prima stesura dell'indicatore B avrebbe dato VUOTO sul desktop vero** (§3.3): cercava un
   gradino che in panoramica non c'è. L'ha smentito la calibrazione, non il ragionamento.
4. ⚠ **Il primo giro rosso non aveva scena in movimento**, e ho scoperto solo lì che su uno schermo
   fermo non arriva **niente** — cioè che la domanda «c'è la shell nel fotogramma?» presuppone un
   fotogramma, e che quel presupposto è proprio quello che il difetto toglie.
5. ⚠ **Il banco compilava un albero misto.** Nove anelli stanno scrivendo dentro `src/` adesso:
   l'albero del banco si prende da **`git archive HEAD`** più il solo `src/sessione.c` della
   cartella di lavoro. ⇒ Le misure di questo rapporto valgono su **HEAD + la mia cura**, e non sul
   lavoro degli altri nove.
6. ⛔ **Non ho misurato la cura sul prodotto VIVO**, e non per pigrizia: non esiste un percorso del
   prodotto che la esegua (§3.2). Tutto quel che è misurato qui passa da `04-b20-nasci.c`, che
   chiama la funzione da fuori. ⇒ **Finché il coordinatore non chiude la cucitura 5.1, la cura è
   corretta e non serve a nessuno.**

---

## 5. Le cuciture che chiedo al coordinatore

*Nessuna di queste è nei miei file. Le firme sono esatte.*

| # | dove | che cosa, e perché |
|---|---|---|
| ⭐ **5.1** | `src/main.c` · `src/figlio.c` | ⛔ **Nessuno chiama `sessione_assicura()`**, quindi la cura non ha effetto sul prodotto vivo (§3.2). Va chiamata **dal figlio**, che è l'unico che gira come l'utente e ha il bus: in `prendi_il_palco()` (`figlio.c:1825`), al posto di `sessione_stato(tela_l, tela_a, NULL)` di `figlio.c:1875` — firma invariata: `SessioneStato sessione_assicura(uint32_t larghezza, uint32_t altezza, bool *avviata);`. ⚠ `figlio.c:1870-1874` dichiara di non volerlo fare («far NASCERE una sessione è del login vero»): **quella riga va decisa, non aggirata**. |
| ⛔ **5.2** | `src/figlio.c:1876` | Dopo la cura **`SESSIONE_SANA` è il difetto e `SESSIONE_NERA` è il caso sano.** Oggi `if (p.stato_sessione != SESSIONE_SANA)` scrive un ⚠ permanente sulla configurazione **giusta**, e tace su quella sbagliata. Il confronto va rovesciato. |
| ⛔ **5.3** | `src/sessione.h` | Il codice e il suo commento adesso **si contraddicono**, e `sessione.h` non è mio. Da riscrivere: riga **2-3** («la fa nascere CON UN MONITOR»); **19-23** (la nera come guasto); **137-138** (`SESSIONE_SANA` = «un monitor solo, del nome e della misura chiesti» ⇒ non è più il caso buono; `SESSIONE_NERA` = «il guasto M9» ⇒ non è più un guasto); **204-205** e **215-233** (il riquadro «che cosa fa, caso per caso»: SANA e NERA si scambiano). ⚠ E il nome `sessione_assicura` promette «con un monitor della misura chiesta»: `larghezza`/`altezza` adesso servono **solo** al controllo, non alla nascita — è la forma **E3** che quel file stesso denuncia, e la denuncia adesso vale per lui. |
| ⛔ **5.4** | `src/rcp.c:1817-1859` · `src/figlio.c:1898` · `src/main.c:111-112` | **La tela concessa è una promessa che nessuno mantiene** (§3.5): `[M]` 145 fotogrammi prodotti, 0 spediti, client nero e nessun errore. Due strade, e va scelta una: **(a)** concedere solo la tela che il palco sa produrre — `TELA_L`/`TELA_A` — dichiarando il ripiego che §4.5 già permette; **(b)** rinegoziare il formato PipeWire alla tela chiesta, che Mutter regge `[R]` (`ensure_virtual_monitor` + `meta_virtual_monitor_set_mode`). ⭐ La (a) è di oggi, la (b) è la cosa giusta. |
| ⛔ **5.5** | `src/figlio.c:1913-1917` | **`prendi_il_palco()` si mangia il primo fotogramma** (`cattura_prendi(cat, 5.0, …)` per il rilievo) e su una scena ferma quello è **l'unico**: il client resta nero finché qualcosa non si muove, chiedendo una chiave a vuoto (`[M]` 40 s, 0 fotogrammi, sia prima sia dopo la cura). ⇒ Il primo fotogramma va **consegnato**, non consumato. |
| ⛔ **5.6** | `src/figlio.c` (ciclo dei fotogrammi) · `src/cattura.c` | **Un figlio la cui sessione grafica muore gira a vuoto per sempre**: `[M]` 14 ago 07:12, **oltre 18 milioni** di «guasti» e ~600 000/s, con una riga di registro per secondo. Il figlio dichiara benissimo il guasto ⭐ e poi non ne trae nessuna conseguenza: dopo N prese fallite consecutive va congedato, non ritentato a mano libera. |

---

## 6. Le righe di `PIANO.md` e `STUDI.md` §gnome da riscrivere

⛔ *Non le ho toccate: sono `.md` del deposito e si scrivono a codice fermo.*

| file | riga | che cosa dice oggi | perché è da riscrivere |
|---|---|---|---|
| `PIANO.md` | **399** | *«`--virtual-monitor WxH` **non è opzionale**, perché in headless la sessione parte altrimenti **viva, completa e nera**»* | ⛔ Vero solo per una sessione che deve vivere **senza nessuno che la catturi**. Per una sessione **solo remota** è il contrario: `--virtual-monitor` è **vietato**, perché la shell finisce sul monitor sbagliato. `[M]` §3.3 |
| `PIANO.md` | **402-404** | *«una prova da fare **guasta di proposito**: senza `--virtual-monitor`, per imparare che aspetto ha il guasto»* | ⛔ Quella non è più «la prova guasta»: è **la configurazione giusta**. Il guasto da imparare adesso è l'opposto — la sessione che **si prende un monitor suo** — e ha un aspetto peggiore: non uno schermo nero, ma **uno schermo pieno di sfondo e zero fotogrammi consegnati** |
| `PIANO.md` | **591-593** | il riquadro della fase 4: *«la cura è in DUE posti»* | ⛔ Sono **quattro** (§3.4), e i due in più sono quelli che, da soli, rompevano |
| `STUDI.md` §gnome | **108-109** (§3.1) | *«⛔ **E `--virtual-monitor` non è opzionale**: in headless `needs_outputs=false`, quindi senza quell'opzione la sessione parte **viva, completa e nera**»* | Il **fatto** resta vero `[R]`+`[M]`; ⛔ è la **conseguenza** che è rovesciata: per REMOTIX quella sessione nera è quella giusta, perché il monitor lo monta `RecordVirtual` e **GNOME ci mette la shell sopra** — misurato `[M]` 14 ago 2026 |
| `STUDI.md` §gnome | **111-112** | *«**La forma**: … drop-in … con `gnome-shell --headless --virtual-monitor WxH`»* | ⛔ La forma per REMOTIX è `gnome-shell --headless --no-x11`, **senza** monitor |
| `STUDI.md` §gnome | **551** (§13, M9) | *«prova **guasta di proposito**: `SHELL` non vuota, e `--virtual-monitor` assente»* | ⛔ L'assenza di `--virtual-monitor` non è più metà di un guasto. M9 resta valida per la sola `SHELL` non vuota |

---

## ⭐ La riga da portarsi via

*Il difetto stava **fra** due pezzi, e la sua cura sta in un terzo posto che nessuno dei due
guardava.* `sessione.c` faceva bene a dare un monitor a una sessione che deve vivere da sola;
`mutter.c` faceva bene a montarne uno per catturarlo. ⛔ **E la macchina non eseguiva né l'uno né
l'altro: eseguiva una riga in `/etc/systemd/user/`** — cioè precisamente la cosa che l'invariante
I7 vieta, rimessa lì il 12 agosto per curare la sessione nera, e diventata due giorni dopo la causa
dello schermo vuoto.

⇒ **Una protezione scritta nel programma non protegge finché qualcuno non la chiama.**

---
---

# APPENDICE — Che cosa succede allo schermo QUANDO IL CLIENT SI STACCA

*14 agosto 2026, pomeriggio. ⭐ Nata da una **demolizione di Nic**: alla domanda «va bene che la
sessione nasca nera?» ha risposto* «la domanda non ha senso: la sessione si crea quando qualcuno si
collega, e deve lavorare anche quando nessuno guarda lo schermo — altrimenti che senso ha la
persistenza della sessione?» *⇒ Ha ragione su tutt'e due i pezzi. **Prima del primo client la
sessione non esiste** (nasce quando PAM dice sì), quindi «nasce nera» non era un caso da decidere.
E il caso vero era **l'altro capo**, che né lui né io avevamo guardato.*

## A.1 ⭐ Che cosa cambia per l'utente

**Niente, e questa volta è la risposta buona**: chiude la scheda, va a fare altro, riapre — e
ritrova **la stessa finestra, con l'ora andata avanti**. Due volte di fila.

## A.2 Serve una decisione di Nic?

**No.** ⭐ E la domanda di prima (§2 di questo rapporto, «la macchina è solo remota?») **cade**:
Nic ha ragione, la sessione nasce col primo attacco e da quel momento **ha sempre uno schermo**.
⇒ Il punto §2 va letto come chiuso da questa appendice.

## A.3 ⛔ LA TESI È FALSA, e la misura lo dice in tre modi indipendenti

> *«Con la cura, un client che si stacca porta via l'unico monitor della sessione: da quel momento
> la sessione sopravvive senza avere dove disegnare, e le applicazioni aperte se ne accorgono.»*

⛔ **Refutata.** Il monitor **non se ne va**: `RecordVirtual` è tenuto aperto dal **figlio**, che
sopravvive al distacco per costruzione (`figlio.c:1821-1824`, *«il palco, preso una volta e
TENUTO… chi smonta il palco è la morte del figlio, non la caduta di una connessione»*). ⇒ L'esito è
**B**, non **A**.

**La scena, per intero** — `banchi/04-b20-stacco.sh giro`, macchina 192.168.0.2, utente `provaa1`,
porta 7601, sessione fatta nascere dal **prodotto curato** (`sessione_assicura` → `1 NERA`), scena
dichiarata: *una finestra `gnome-terminal` che scrive l'ora cinque volte al secondo sullo schermo
**e su un file***. ⛔ Il file non è un doppione: con nessuno collegato lo schermo non si può
guardare, e senza il file *«l'applicazione è andata avanti»* e *«non ho potuto vederlo»* avrebbero
la stessa faccia.

| misura | ora | monitor | nome | orologio: pid · righe · ultima | asserz. | verdetto |
|---|---|---|---|---|---|---|
| `attaccato-1` *(client attaccato)* | 07:37:12 | **1** | `Virtual remote monitor` | **465823** · 154 · 07:37:12 | 2 | **B** |
| `subito-dopo-stacco-1` | 07:37:36 | **1** | idem | **465823** · 267 · 07:37:36 | 2 | **B** |
| `dopo-attesa-1` *(+240 s, nessuno collegato)* | 07:41:36 | **1** | idem | **465823** · **1427** · 07:41:36 | 2 | **B** |
| `riattaccato-1` | 07:42:03 | **1** | idem | **465823** · 1557 · 07:42:03 | 2 | **B** |
| `subito-dopo-stacco-2` | 07:42:06 | **1** | idem | **465823** · 1572 · 07:42:06 | 2 | **B** |
| `dopo-attesa-2` *(+240 s)* | 07:46:06 | **1** | idem | **465823** · **2733** · 07:46:06 | 2 | **B** |
| `riattaccato-2` | 07:46:33 | **1** | idem | **465823** · 2863 · 07:46:33 | 2 | **B** |
| `contatori-corretti` | 07:48:44 | **1** | idem | **465823** · 3497 · 07:48:44 | 2 | **B** |

**I tre modi indipendenti in cui la tesi cade:**

1. ⭐ **Il monitor non è mai sparito.** Otto letture di `GetCurrentState` su undici minuti, dal
   client attaccato ai quattro minuti di solitudine: **sempre 1 monitor, sempre `Virtual remote
   monitor`**. ⛔ Mai `0`. ⇒ Esito **B — il monitor c'è, e nessuno lo cattura**, che non è un
   difetto: è **I4 mantenuta**.
2. ⭐ **L'applicazione ha continuato a lavorare mentre nessuno guardava.** Il ciclo dell'ora ha
   scritto **1160 righe fra 07:37:36 e 07:41:36** — i 240 s di solitudine a 4,8 righe/s, cioè
   esattamente il suo ritmo, senza un buco. ⇒ Non si è accorta di niente, perché non c'era niente
   di cui accorgersi.
3. ⭐ **Nessuna asserzione di `libmutter`.** `[M]` **2** righe di asserzione e **7** critiche,
   **costanti dalla prima all'ultima misura** — zero crescita. ⛔ E non sono nemmeno della sessione
   viva: portano tutte l'ora **07:35:22** e il pid **464439**, cioè il `gnome-shell` che il prodotto
   stava **congedando** durante la rinascita. Il `gnome-shell` vivo (**465076**) non ha scritto una
   riga in tutta la scena. *(Sono `Gjs-CRITICAL`/`GLib-CRITICAL` di smontaggio, non il difetto di
   v1.)*

⭐ **E il riattacco restituisce il desktop, non uno schermo vuoto** — giudicato dal banco `04-b20`
sul fotogramma **decodificato dal client**:

| | fotogrammi ricevuti | B (bordo) | T (orologio) | verdetto |
|---|---|---|---|---|
| `riattacco-1` | **120, tutti conformi** | 5,19 alla riga 44 | **494** | ⭐ **SHELL** |
| `riattacco-2` | 120 → chiave 1920×1080 | **13,71** alla riga 36 | **503** | ⭐ **SHELL** |

⭐ **E che sia LA STESSA finestra, non una nuova**: il pid dell'orologio è **465823 all'inizio e
465823 alla fine**, e le righe scritte sono passate da 154 a 3497. ⛔ Il pid è il discrimine: una
finestra nuova avrebbe un pid nuovo, e uno schermo con una finestra qualunque sarebbe passato per
buono.

## A.4 ⭐ I controlli positivi, fatti PRIMA di credere alle misure

⛔ *«Tutto bene» e «non ho saputo guardare» hanno la stessa faccia.*

| controllo | esito |
|---|---|
| **lo strumento vede un monitor che c'è di sicuro?** | ⭐ `GetCurrentState` → **1**, con i nomi ⇒ sì |
| **lo strumento sa dire che un'applicazione è MORTA?** | ⭐ un'**esca** con lo stesso nome del vero orologio, vista viva (pid 475906), uccisa, e lo strumento la dichiara morta ⇒ sì |

⚠ L'esca porta **lo stesso nome** del soggetto apposta: così si prova *esattamente* lo strumento
che poi si usa, non uno che gli somiglia.

## A.5 ⛔ Che cosa NON ha funzionato — tre numeri del banco che mentivano

*Nessuno dei tre entrava nel verdetto, ⛔ e proprio per questo nessuno li avrebbe controllati.*

1. ⛔ **Il conteggio dei monitor era il DOPPIO del vero.** `GetCurrentState` elenca ogni schermo
   **due volte** — nell'array dei monitor e in quello dei monitor *logici* — e la prima stesura non
   divideva: ha scritto **«monitor: 2»** su una sessione che ne aveva **uno**. ⚠ Ha sbagliato nella
   direzione che **rassicura** («ce n'è più di quanti credessi»), cioè quella che non si vede.
   ⭐ Le due righe di `04-b20-persistenza.jsonl` scritte alle 07:37 **portano ancora il numero
   doppio e restano lì**: i nomi accanto permettono di ricavare il vero, e cancellarle sarebbe
   cancellare la prova dell'errore. Rimisurato col contatore corretto: **1**.
2. ⛔ **Il contatore dei clienti non era scritto male: NON ESISTEVA.** Prima contava
   `ss -tn state established` — su **TCP**, e il filo è QUIC ⇒ zero sempre. Corretto in `ss -uan`,
   **zero un'altra volta**: QUIC vive su **un solo socket UDP non connesso**, quindi `ss` non ha
   *nessuna* riga per client (`[M]` verificato con un client attaccato: 0 prima, 0 durante).
   ⇒ Cura: `LEZIONI.md` §1.6, **non si deduce, si chiede al componente** — si legge «(ne restano N)»
   dal registro del prodotto.
3. ⛔ **Il mio JSONL non era JSON valido**: il campo `nomi` porta dentro le virgolette di `busctl`
   senza sfuggirle, e `json.loads` si rifiuta di leggerlo. ⚠ Un banco che scrive esiti che nessuno
   riesce a rileggere ha misurato per sé.

⚠ E una quarta, di metodo: **il registro della Shell non esisteva al primo tentativo.**
`gnome-session` non lancia `gnome-shell` — fa partire l'unità d'utente — quindi i messaggi di Mutter
non ereditano nessuna redirezione e vanno al journal, che su questa macchina non c'è (rootfs in
RAM). Serve un drop-in `StandardOutput=append:`, ⛔ **e vale solo dalla nascita successiva**: la
prima volta ho misurato le asserzioni su un file vuoto, e «zero asserzioni» voleva dire «nessuno
stava scrivendo».

## A.6 La fase 4 può chiudersi con questo aperto?

⭐ **Sì, e non c'è niente di aperto**: la tesi è refutata, la persistenza del palco allo stacco
**funziona già** e ha il suo banco. ⛔ **Non ho curato niente** — non c'era da curare, e `PIANO.md`
mette la persistenza alla fase 5.

⚠ **Quel che resta alla fase 5**, e non è quel che ci si aspettava:

| | |
|---|---|
| ⛔ **il palco muore col FIGLIO, non con la sessione** | Il monitor sopravvive perché il figlio vive. ⇒ **Se il figlio muore, il palco se ne va** — e `[M]` §5.6 di questo rapporto racconta un figlio che, perduta la sessione grafica, gira a vuoto 600 000 volte al secondo invece di essere congedato. **Chi lo congederà toglierà il monitor a una sessione viva**, che è esattamente il difetto di v1 preso dall'altro capo. La fase 5 lo trova già scritto qui |
| `[?]` **i tre orologi** (`SPECIFICHE.md` §5.3) | provati per **11 minuti**, non per 6 ore: l'orologio dell'abbandono non è stato sfiorato |
| `[?]` **la sessione locale che prevale** (I2) | non provata: `provaa1` non ha mai avuto una sessione locale |

**Dove si ricontrolla**: `bash banchi/04-b20-lancia.sh persistenza` (≈12 minuti, fa i sette passi
due volte); gli esiti in `/media/REMOTIX/tmp/04-b20/04-b20-persistenza.jsonl`, il registro della
Shell in `/run/user/1002/mutter.log`, le immagini `riattacco-1-fotogramma.png` e
`riattacco-2-fotogramma.png`.

## A.7 ⭐ La riga da portarsi via

*La domanda sbagliata non era «va bene che nasca nera?»: era **una domanda su un istante che non
esiste**.* La sessione nasce con il primo client, e da quel momento uno schermo ce l'ha sempre.
⇒ ⭐ **Il caso da misurare non era il primo istante: era il secondo attacco** — e lo si è visto solo
perché qualcuno ha rifiutato la domanda invece di risponderle.
