# F4-A7 — La pagina, modo classico

*Anello A7 della fase 4. Scritto il 14 agosto 2026, a banco fermo.*
*Banco: `banchi/04-b27-classico.py` · `banchi/04-b27-lancia.sh` — esiti in
`banchi/04-b27-esiti.jsonl`, byte in `banchi/04-b27-registro.jsonl`.*
*Codice: `src/pagina.html`, **solo** l'ancora `F4-INPUT-CLASSICO` più due regole di `<style>`.*

---

## 1. Che cosa cambia per l'utente

**Dentro la pagina il mouse e la tastiera comandano il desktop remoto**: una freccia sola —
disegnata dalla pagina, che si muove alla velocità della mano e non della rete — `Ctrl+C` che
**copia invece di scrivere una `c`**, e nessun tasto che resta premuto quando si cambia finestra.

---

## 2. Serve una decisione di Nic?

⭐ **Sì, una sola, e ha due strade con un prezzo diverso: gli accenti COMPOSTI.**

| | |
|---|---|
| ✅ **quel che già funziona** | su una disposizione italiana `à` è un tasto **diretto**: viaggia come `LETTERA` U+00E0 — `[M]` 14 agosto 2026, caso `B2ter-accento` |
| ⛔ **quel che NON funziona** | i **tasti morti** e l'IME (`^`+`e` → `ê`, la tastiera di Android, il cinese): oggi non producono niente, e la pagina lo **dichiara** invece di falsificare (ripiego `composizione`) |

`STUDI.md` §web §1.2 C aveva previsto esattamente questo scontro, e il prezzo è vero: per avere la
composizione serve **un elemento modificabile con il fuoco**, e un elemento sopra la tela **fa
cadere il percorso overlay** su cui è costruito tutto §6 di `STUDI.md` §web.

> **La domanda per Nic**: la fase 4 deve saper scrivere `ê` con `^`+`e`, o basta che scriva le
> lettere che la sua tastiera ha per intero? ⚠ Non è una domanda tecnica: è quanto vale, per chi
> usa il desktop remoto tutti i giorni, la composizione — contro il ritardo del disegno.

⚠ E una cosa **si giudica usando, non leggendo** (`DECISIONI.md` §5-bis.3): il **guadagno** del
puntatore è a 1,0 — la freccia sta sotto la mano, senza accelerazione. Se all'uso sembra lenta o
nervosa, quel numero è `CL_GUADAGNO` ed è un `[?]` dichiarato.

---

## 3. Che cosa ho MISURATO

**La scena, per intero** — `[M]` 14 agosto 2026, 09:30-10:0x, macchina **CHUWI** (non 192.168.0.2:
qui non serviva il server), sessione **GNOME Wayland** dell'utente `nicfio`
(`XDG_SESSION_TYPE=wayland`, ⚠ Chrome ignora `DISPLAY` e non gli è stato forzato
`--ozone-platform=x11`), **Chrome 151.0.7922.137**, pagina del **prodotto** servita con le tre
intestazioni di isolamento fra origini come le manda `src/pagina.c` (`crossOriginIsolated: true`,
verificato dalla pagina). Porte 7661 (servitore) e 7662 (diagnosi).

⛔ **Il giudizio si fa sui BYTE, da fuori dal browser** (`CODER.md` §3.8): la pagina spedisce i
messaggi a un servitore, che li decodifica con un lettore **scritto dalla tabella di `RCP.md` §7.3
e non ricopiato dal prodotto**. Il registro della pagina non entra in nessun verdetto.
⭐ Il giudice si certifica da sé prima di ogni misura — **sano → otto guasti → risanato**, e ogni
guasto dev'essere visto (`python3 banchi/04-b27-classico.py --certifica`, senza browser).

**Esito: `[M]` 19 casi su 19 VERDI, e su DUE giri di fila** — ⚠ due giri e non uno perché i primi
tre rossi di questo banco erano tutti e tre **suoi**, non del prodotto (§4), e un giro solo non
distingue una misura buona da una fortunata.

### Le cinque tesi del mandato

| | Tesi | Esito |
|---|---|---|
| 1 | il puntatore lo disegna la pagina, `cursor: none`, mouse da **Pointer Lock** | ✅ **confermata e attuata**. Lock agganciata `[M]`; il `cursor: none` è legato a `body[data-disposizione="classico"]` e vale **anche senza lock** — è lì che i due puntatori tornerebbero |
| 2 | coordinate = **indici di pixel** sulla tela, conversione del client, **per difetto** | ✅ **confermata, e provata dove fa male**: spinto oltre il bordo con la lock esce **1919, 1079** e **mai 1920** `[M]`. A cinque fattori di scala l'attesa è ricalcolata in Python: a `1279×719` il valore vero è **1918,5** — dove `round` e `ceil` direbbero 1919 e chiuderebbero la sessione al pixel dopo |
| 3 | `Ctrl+C` è un comando: 4 `POSIZIONE_TASTO`, **zero `LETTERA`**; Maiusc e AltGr no | ✅ **confermata** `[M]`: `29↓ 46↓ 46↑ 29↑`, zero lettere. E `Maiusc+a` → **una `LETTERA` U+0041 e zero posizioni** |
| 4 | la lock si spegne alla perdita del fuoco ⇒ **la pagina rilascia tutto** | ✅ **confermata** `[M]`: premuti Ctrl e il pulsante sinistro, tolto il fuoco **con una scheda vera che passa davanti** (non un `blur()` finto), escono i due rilasci. E il gemello negativo tiene: a fuoco tenuto **non esce nessun rilascio** |
| 5a | l'`id` cresce di ≥1 su **tutto** il canale, non uno per tipo | ✅ **confermata** `[M]`: da 1, strettamente crescente su 30 messaggi di cinque tipi diversi |
| 5b | l'`istante` è millisecondi × 1000, «l'orologio della pagina è in millisecondi» | ⛔ **la REGOLA è rispettata, la sua PREMESSA è falsa** — vedi il riquadro |

> ### ⛔ La premessa dell'`istante` è falsa su Chrome — `[M]` 14 agosto 2026
>
> `RCP.md` §7.3 (rilievo R1.27) motiva «millisecondi × 1000» così: *«in una pagina l'orologio
> monotono è in millisecondi e la sua grana è deliberatamente ingrossata»*.
>
> **Misurato su 4000 letture di fila di `performance.now()`, sulla pagina del prodotto servita con
> l'isolamento fra origini vero:** lo scarto minimo non nullo è **0,005 ms = 5 µs**, e
> `crossOriginIsolated` è `true`. Senza le tre intestazioni la grana è **0,1 ms**.
>
> ⇒ L'orologio è **200 volte più fine** di quel che la regola presuppone, e scrivendo
> `round(ms) × 1000` **buttiamo via la precisione che abbiamo** — proprio nel campo che esiste
> «per sapere quando l'utente ha mosso la mano» e che serve alla diagnosi del ritardo (il tetto è
> 50 ms: 5 µs contro 1000 µs non è una sfumatura).
>
> ⭐ **Non l'ho cambiato di mia iniziativa**: sul filo comanda `RCP.md`, e questa è una richiesta ad
> A3 / al coordinatore. Oggi la pagina fa quel che §7.3 dice, alla lettera. ⚠ E la cura giusta
> **non** è «scrivi i microsecondi veri»: è *«scrivi l'istante troncato alla grana che l'orologio
> ha davvero»*, che è la formulazione che non fa credere a una precisione che non c'è **e** non
> butta quella che c'è. La grana si misura in tre righe (il banco lo fa già).

### E la rotella — dove la mia prima stesura era sbagliata, e lo ha detto lo strumento

| | |
|---|---|
| **il segno** | ✅ `[M]` girando **in su** parte **+120**; in giù **−120**. ⛔ **Invertito qui una volta sola**: il server ne fa la sua metà (§7.3), e chi invertisse due volte farebbe scorrere lo schermo al contrario |
| ⛔ **i mezzi scatti** | ✅ `[M]` mezzo scatto → **+60**, non 0 e non 120. ⚠ **Ma ci sono arrivato al secondo tentativo**: la prima stesura leggeva `wheelDelta`, che *sembra* la sorgente giusta perché è già in unità da 120 |
| ⛔ **e `wheelDelta` mente** | `[M]` 14 agosto: `deltaY = −100 → wheelDeltaY = 120`; `deltaY = −50 → wheelDeltaY = **120**`. Conta gli **scatti arrotondati**, non la quantità ⇒ mezzo scatto ne uscirebbe **gonfiato a uno intero**. Adesso si legge `deltaY` con `deltaMode`, e il rapporto fra le due letture dà la costante: **100 px = uno scatto** su Chrome `[M]`, `[?]` altrove |

**Dove si ricontrolla**: `bash banchi/04-b27-lancia.sh` (certifica il giudice, apre Chrome, misura,
giudica). Il verdetto si rifà sui byte già registrati, senza browser:
`python3 banchi/04-b27-classico.py --verdetto banchi/04-b27-registro.jsonl`.

---

## 4. ⛔ Che cosa NON ha funzionato

1. ⛔ **«E poi che cosa fa il desktop» NON è misurato.** Il banco prova che sul filo escono i byte
   giusti; che `Ctrl+C` **copi davvero** si potrà misurare solo quando la cucitura del trasporto
   (§5) esisterà e l'iniezione di A4 sarà attaccata. ⭐ Il pezzo che manca è **una riga**, e la
   firma è qui sotto. Fino ad allora, di B2 si può dire *«sul filo è un comando, non una lettera»*
   — non *«copia»*.
2. ⛔ **`unadjustedMovement` è RIFIUTATO** da Chrome 151 su Wayland `[M]`: gli spostamenti arrivano
   con l'accelerazione del sistema **già applicata**, e `SPECIFICHE.md` §7.4 vuole che l'acceleri
   il client. La pagina ripiega sulla lock normale e **lo dichiara**
   (`stato().ripieghi` → `movimento-grezzo`). ⚠ Conseguenza vera: su questa scena le accelerazioni
   sono due, e la seconda non è nostra.
3. ⛔ **La lock viene NEGATA se la pagina non ha il fuoco** `[M]`, e con dieci banchi in parallelo
   sullo stesso desktop una finestra altrui lo ruba: due giri identici, uno agganciato e uno no.
   Curato **nel banco** (si riprende il fuoco e si verifica), ma è un fatto del **prodotto** che
   riguarda A9: la Keyboard Lock ha lo stesso vincolo.
4. ⛔ **La mia prima attesa sul bordo era sbagliata, e accusava il prodotto.** Pretendevo
   `1919, 1079` a **ogni** fattore di scala. `[M]` Chrome consegna coordinate del mouse **intere**:
   in una vista larga 1361 px l'ultimo punto raggiungibile vale **1918,59** sulla tela, cioè 1918.
   ⭐ A trovarlo è stato il *controllo dello strumento* — il banco registra che cosa il browser gli
   ha davvero consegnato — e senza quello avrei «curato» un prodotto che era già giusto
   (`CODER.md` §3.11). ⚠ Nello stesso giro è venuto fuori che Chrome **collauda il bersaglio sulla
   coordinata arrotondata e la consegna troncata**: un punto a `bordo − 0,01` finisce sull'`<h1>`
   che sta sotto la tela, e l'evento alla tela non arriva mai.
5. ⛔ **E un TERZO rosso era del banco: le fasi si marcavano a TEMPO.** `[M]` con tre browser sulla
   stessa macchina uno scatto di rotella spedito nella fase «su» è arrivato dentro la fase «giù», e
   la somma dei due scatti opposti fa **zero**: rosso a un prodotto corretto. ⚠ Un'attesa a tempo
   fisso è una **grandezza sostitutiva** — la stessa famiglia P8→P20 di `LEZIONI.md` §1.13, «il
   tempo non è l'arrivo». Adesso la marca di fase aspetta che **i byte ricevuti stiano fermi**, e
   se non si fermano lo scrive.
6. ⚠ **`Input.dispatchMouseEvent` si è inceppato due volte** (nessuna risposta entro il tetto del
   cliente CDP) con dieci banchi in parallelo. È la scena, non il prodotto: adesso un colpo che non
   torna **si scrive e non uccide la misura**.
7. `[?]` **Il prezzo del puntatore disegnato non è misurato.** È un `<div>` **sopra** la tela, e
   `STUDI.md` §web §1.2 C dice che un elemento sopra la tela fa cadere il percorso overlay e la tela
   desincronizzata. **Quanto costi in fotogrammi dipinti nessuno l'ha misurato**: si misura con
   `banchi/03-b16-dipinti.py` a puntatore acceso e spento, ed è una misura di **A2**, non mia.
   ⛔ Disegnarlo *dentro* la tela — la cura vera — oggi non è possibile da qui: con `?video=worker`
   la tela è del worker.
8. ⛔ **Solo Chrome.** Firefox non è stato misurato: niente CDP, e il tempo è andato nel far dire
   la verità allo strumento. Restano `[?]` su Gecko: la grana dell'orologio, `wheelDelta`,
   l'arrotondamento delle coordinate, `unadjustedMovement`.
9. ⚠ **Con `?video=worker` la pagina non sa che tela ha.** `schermo` sul thread principale è uno
   *specchio* e `negozia()` va al worker: `schermo.tela_l` resta 0, e il modo classico ripiega su
   una tela di comodo 1920×1080 — dichiarata in `stato().tela_di_comodo`. Vale identico per A8.
   La cucitura è in §5.

---

## 5. Le cuciture che chiedo

### ⭐ La firma con cui A8 entra nel mio modo *(già cablata, nessuna modifica per lui)*

```js
window.REMOTIX_CLASSICO = {
  entra(perche: string): boolean,   // ⭐ è questa: la chiama entra_nel_classico(perche)
  esci(): boolean
}
```

⚠ `entra()` **non chiede la lock**: un gesto dell'utente non c'è al caricamento, e la lock si
chiede al primo clic sulla tela. `esci()` rilascia tutto quel che è premuto e sgancia.

**E la cucitura che A8 chiedeva a me è fatta**, con la sua firma esatta più due aggiunte:

```js
window.REMOTIX_PUNTATORE = {
  muovi(x_tela, y_tela), mostra(), nascondi(),
  forma({larghezza, altezza, punto_x, punto_y, rgba}),   // ⚠ per A6: CURSORE_FORMA (§7.2)
  geometria()                                            // tela ↔ vetro, un'autorità sola
}
```

⭐ Da qui la freccia è **una sola**: il dito di A8 e il mouse mio spingono lo stesso puntatore
(`DECISIONI.md` §5-bis.8). Il suo `<div>` di ripiego si nasconde da sé.
🔸 **Proposta ad A8**, non un obbligo: `tocco_geometria()` e la mia sono la stessa mappatura scritta
due volte (E2). Con `REMOTIX_PUNTATORE.geometria()` ne resta una.

### ⛔ La cucitura che manca, ed è del coordinatore — una riga in `collega()`

È **la stessa che chiede A8**, e va scritta **una volta sola** dopo `SESSIONE`
(`RCP.md` §2.5: *uno* stream unidirezionale, aperto dal client, tenuto aperto):

```js
/* ⛔ §2.5: UNO stream unidirezionale, aperto DOPO SESSIONE e tenuto aperto. */
const flusso_input = await wt.createUnidirectionalStream();
const scrittore_input = flusso_input.getWriter();
let input_id = 0;
window.REMOTIX_INPUT = {
  /* §7.3: cresce di almeno uno su TUTTO il canale — 0 è riservato. */
  prossimo_id: () => (input_id = input_id >= 0xFFFFFFFF ? 1 : input_id + 1),
  manda: (tipo, corpo) => {
    scrittore_input.write(inquadra(tipo, corpo))
      .catch((e) => nota("il canale di input non ha accettato un messaggio: " + e));
  },
};
```

e alla fine della sessione (dentro `wt.closed`, accanto a `fine_sessione`):

```js
window.REMOTIX_INPUT = null;   /* ⛔ così le due disposizioni DICHIARANO il ripiego
                                  invece di scrivere su uno stream morto */
```

| | |
|---|---|
| ⚠ **l'ordine** | un solo `getWriter()` serializza le scritture: senza, i messaggi possono uscire in ordine diverso da quello in cui l'utente ha mosso la mano, e l'`id` che torna nei fotogrammi non vorrebbe più dire niente |
| ⚠ **un contatore solo** | `prossimo_id` sta **qui** e non nei due modi: due contatori sono la cosa che §7.3 vieta in una riga |
| ⚠ **niente `await` per messaggio** | `manda` non si aspetta: un puntatore che aspetta la rete è esattamente il ritardo che il puntatore disegnato esiste per togliere |

### ⚠ La seconda cucitura, piccola — la tela quando il video sta nel worker

In `src/pagina.html`, dove le chiamate si dirottano al worker (`if (VW) { … }`), `negozia` e
`tela_adattata` devono lasciare la misura anche sullo specchio:

```js
schermo.negozia = function (codec, prof, stringa, tl, ta) {
  schermo.tela_l = tl; schermo.tela_a = ta;   /* ⛔ la tela la devono sapere anche i due modi */
  VW.chiama("negozia", [codec, prof, stringa, tl, ta]);
};
```

### 🔸 E una richiesta ad A3 / al coordinatore, non un difetto

Il riquadro di §3 sull'`istante`: la premessa di `RCP.md` §7.3 (R1.27) è falsa su Chrome `[M]`.
Da decidere **sul filo**, non nella pagina — e la pagina si adegua in una riga (`cl_istante_us`).

---

## Che cosa ho toccato

| | |
|---|---|
| `src/pagina.html` | **solo** dentro `⬇⬇ ANCORA F4-INPUT-CLASSICO`, con `Edit`, mai riscrivendo il file; più **due** regole nel `<style>`: `body[data-disposizione="classico"] #schermo { cursor: none }` e `#puntatore` |
| `banchi/04-b27-classico.py` · `banchi/04-b27-lancia.sh` | il banco e il suo lanciatore |
| `banchi/04-b27-esiti.jsonl` · `banchi/04-b27-registro.jsonl` | gli esiti e i byte |

⛔ Nessun `git`, nessun `.md` del deposito, nessun file di un altro anello.
