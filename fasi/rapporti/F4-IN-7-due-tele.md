# RCP/2 — l'input autosufficiente: due tele, una conversione

*Bozza del 14 agosto 2026, sera. ⛔ **Non è ancora in `RCP.md`**: è il disegno da approvare prima
di toccare l'arbitro. Deciso dall'utente nella conversazione di questa sera.*

---

## 1 · Il modello, con le sue parole

> *«Abbiamo due tele: quella del server e quella del client (la dimensione della finestra di
> rendering del browser). Bisogna solo convertire le coordinate.»*

| | |
|---|---|
| **tela del server** | `L_s × A_s` — il monitor virtuale che chiediamo a Mutter. Il server la conosce sempre, ed è sua |
| **tela del client** | `L_c × A_c` — la tela su cui la pagina dipinge, in **pixel CSS** |
| **la conversione** | `x_s = x · L_s / L_c` · `y_s = y · A_s / A_c` |

⛔ **La condizione che rende vera la parola «una»**: le due tele devono avere lo **stesso
rapporto**. Se non ce l'hanno compare un terzo rettangolo — l'immagine dentro la tela del client,
con le bande intorno — e la conversione torna a due stadi. È esattamente il nostro `bx0` di oggi.

⇒ Due modi di garantirlo, e il primo è meglio:

1. ⭐ **la tela del server si chiede della misura della tela del client** ⇒ rapporto identico,
   `scala = 1`, **la conversione è l'identità** e i pixel neri spariscono;
2. le **bande escono dal buffer** e diventano lo sfondo dell'elemento genitore ⇒ la tela del client
   *è* l'immagine, e resta una scala sola. `[R]` È quel che fanno tutti e cinque i progetti
   studiati (`F4-AND-4`).

⚠ Il **`devicePixelRatio` non entra**: coordinate in pixel CSS dentro una tela misurata in pixel
CSS, il rapporto si semplifica. `[R]` Tre conferme indipendenti stasera (xrdp lo legge e non lo usa
mai; [MS-RDPEDISP] ammette solo tre densità e l'1,2 del DeX non sarebbe rappresentabile; noVNC lo
usa in una riga sola, per una soglia).

---

## 2 · ⭐ La posizione sale nell'intestazione comune

⛔ In RCP/1 la posizione è **un tipo di messaggio** (`PUNTATORE`), e gli altri eventi non ce
l'hanno: `PULSANTE` porta il tasto, `ROTELLA` porta gli scatti, e **nessuno dei due dice dove**.
⇒ È la causa del difetto misurato il 14 agosto: il server clicca dove sta il **suo** puntatore.

In RCP/2 la posizione e la misura della tela **stanno nell'intestazione**, quindi **ogni** evento
di input è autosufficiente:

```
ogni messaggio di input
 ├── u32 id             crescente, 0 riservato = «nessun input»
 ├── u64 istante        microsecondi dell'orologio monotono del CLIENT
 ├── u32 tela_l         la misura della tela del CLIENT, in pixel CSS
 ├── u32 tela_a
 ├── u32 x              la posizione DENTRO la tela del client
 └── u32 y

e poi i campi propri del tipo:

PUNTATORE          (nessuno — la posizione è già nell'intestazione)
PULSANTE           + u16 codice · u8 premuto
ROTELLA            + i32 asse_x · i32 asse_y
LETTERA            + u32 carattere
POSIZIONE_TASTO    + u16 codice · u8 premuto
```

⚠ **Sì, anche i tasti portano la posizione**, e costa 16 byte a battuta. ⭐ Si paga volentieri: una
intestazione sola senza casi particolari è la ragione per cui questo difetto non potrà ripetersi
in un altro tipo di messaggio. E la posizione di una battuta non è inutile — dice **dove stava il
puntatore quando l'utente ha scritto**, che è esattamente il dato che stasera è mancato.

### I controlli, che il server DEVE fare

| | |
|---|---|
| `tela_l`, `tela_a` | `> 0` e `≤ 32768`; zero è `ERRORE_PROTOCOLLO` |
| `x`, `y` | `x < tela_l` e `y < tela_a`, altrimenti `ERRORE_PROTOCOLLO` |
| l'arrotondamento | il server converte e **satura** all'ultimo pixel valido del suo desktop, e **lo dichiara nel registro** la prima volta che accade |

⛔ **Non si «aggiusta» in silenzio una coordinata fuori tela.** Un client che manda `x ≥ tela_l`
ha un difetto, e nasconderlo è l'indulgenza che §3 vieta.

---

## 3 · Che cosa sparisce, e perché è il punto

| oggi (RCP/1) | domani (RCP/2) |
|---|---|
| il client tiene uno **specchio** del puntatore del server | ⛔ non c'è più niente da rispecchiare |
| `cl_manda_puntatore()` **tace** se il pixel non è cambiato | ⛔ non serve: ogni evento porta la sua verità |
| il clic parte dalla posizione **del server** | ⭐ il clic parte da **dove l'utente ha cliccato** |
| tre stadi di conversione, sul **client** | ⭐ uno, sul **server**, dove vive la misura autorevole |
| `devicePixelRatio` dentro la catena | fuori |
| un ridimensionamento va **coordinato** fra i due lati | ⭐ si sistema da sé: la misura viaggia con l'evento |

⭐ E la conseguenza che riguarda il difetto aperto: **su Chrome per Android l'hover non arriva**
(noVNC #1727), e con RCP/2 **smette di essere un problema di correttezza**. Il puntatore non
scorrerà finché Chrome non consegna i movimenti, ma **puntare e cliccare colpisce il punto
giusto**, perché il clic non dipende più da dove il server crede di stare.

---

## 4 · La compatibilità, che è il vincolo posto dall'utente

`[R]` `RCP.md:2181`: *«Dentro una versione maggiore si cresce solo per capacità, mai aggiungendo
campi a messaggi esistenti… Un tipo nuovo obbligatorio è **una versione maggiore nuova**»*.

⇒ Questo è un cambio **obbligatorio e universale** — non una particolarità di Android — quindi la
strada scritta nell'arbitro è **RCP/2**: percorso `/rcp/2`, `CIAO(2)`.

⭐ **E il client browser non può restare indietro**: `[R]` `src/pagina.c:158` manda
`Cache-Control: no-store`, quindi la pagina non finisce mai in memoria del browser e il client è
**sempre** quello che il server ha appena consegnato. Lo scenario che `RCP.md` §9 temeva — *«il
giorno in cui un telefono resta indietro»* — per questo client **non può accadere**.

⛔ **Chi invece può restare indietro sono le nostre sei implementazioni di RCP/1**, che il
documento conta apposta: `src/rcp.c`+`rcp.h`, la gemella `banchi/rcp/` (il `Makefile` le verifica
identiche byte per byte), `banchi/01-b3-cliente.py`, `banchi/01-b4-validatore.py`,
`src/pagina.html`, `banchi/01-b11-pagina.html`.

⇒ **Il server parla tutt'e due le versioni** finché i banchi non sono aggiornati — che è
precisamente ciò per cui il meccanismo delle versioni esiste. ⚠ Non è una doppia strada
permanente: è una transizione, e va chiusa con una data.

---

## 5 · L'ordine dei lavori

| # | dove | che cosa |
|---|---|---|
| 1 | `RCP.md` | §2.2 ammette `/rcp/2`; §7.3 in versione 2 come sopra; §9 registra la versione nuova |
| 2 | ⛔ `src/cattura.c` · `src/pagina.html` | **le bande fuori dal buffer della tela** — precondizione: senza, il server non può convertire perché non sa dove finisce l'immagine |
| 3 | `src/rcp.c` + `banchi/rcp/` | la lettura di RCP/2 e la conversione; RCP/1 resta |
| 4 | `src/pagina.html` | `CIAO(2)`, i mittenti nuovi, e via lo specchio del puntatore |
| 5 | `banchi/01-b3-cliente.py` · `01-b4-validatore.py` | aggiornati alla versione 2 |

⚠ **Il 2 è quello che può rompere il desktop**, che oggi funziona: va misurato prima e dopo, sul
portatile, non solo sul DeX.

---

## 6 · Quel che questa bozza non dice

- ⛔ **Non risolve l'hover mancante** su Chrome per Android: quello è di Chrome, e RCP/2 lo rende
  innocuo, non lo cura.
- ⚠ **Non è misurato** che il difetto delle coordinate sparisca: è dedotto dal meccanismo. La
  prova è una sessione sul DeX in cui **puntare e cliccare colpisce**.
- `[?]` Non ho verificato quanto costi a Mutter cambiare la misura del monitor virtuale **a
  sessione aperta**: `F4-IN-2` dice che gnome-remote-desktop lo fa con `pw_stream_update_params()`
  senza rifare la sessione, ma da noi non è mai stato provato.
