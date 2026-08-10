# MANDATO — revisione avversariale del 10 agosto 2026

## 0. Che cosa si revisiona

Tutto quel che è stato scritto **oggi**, dal server minimo su `ngtcp2` fino alla chiusura di B11:
**9.078 righe aggiunte** in 36 file, dal commit `63cff5e` (ore 08:00) a `e5d54f9` (ore 15:59).

L'intervallo si legge così:

```
git -C /home/nicfio/Documenti/REMOTIX_V2 diff 63cff5e~1 HEAD -- <file>
git -C /home/nicfio/Documenti/REMOTIX_V2 log --format='%h %s' 63cff5e~1..HEAD
```

## 1. Le regole, che sono vincolanti

⛔ **Prima di scrivere un solo rilievo si legge [`REVIEWER.md`](../../REVIEWER.md)** — è la regola
vincolante di quel documento. Da lì valgono, senza sconti:

- il verdetto ha **sempre** la forma *«questo contraddice X»*, mai *«questo è giusto»*;
- **il banco è il primo imputato** (§1): un difetto nel prodotto lo trova un banco buono; un
  difetto nel banco non lo trova niente, **perché dà fiducia**;
- le cinque domande al banco (§1), il catalogo delle forme d'errore **E1..E11** (§2), gli
  invarianti **I1..I8** (§3);
- **non si misura, non si riscrive, non si supplisce** (§5);
- una revisione verde si dichiara come **«non ho trovato niente»**, non come approvazione.

E da [`PIANO.md`](../../PIANO.md) §0.4: si prova a **rompere**, non a confermare. Per ogni
invariante che il codice tocca si costruisce **l'ingresso concreto** che lo violerebbe; se non
riesce, lo si dichiara — è informazione anche quella.

⚠ **Non ti viene dato il ragionamento di chi ha scritto il codice**, ed è voluto: `PIANO.md` §0.4
pratica 1. I commenti nel codice sono parte del codice e li leggi; ma un commento che spiega
perché una riga è giusta **non è una prova che lo sia**, ed è esso stesso materiale da
contraddire.

## 2. Gli arbitri contro cui si misura la coerenza

| documento | che cosa arbitra |
|---|---|
| [`RCP.md`](../../RCP.md) | il protocollo sul filo: tipi, stati, motivi, DEVE e NON DEVE |
| [`SPECIFICHE.md`](../../SPECIFICHE.md) | che cosa fa il prodotto, e gli invarianti |
| [`DECISIONI.md`](../../DECISIONI.md) | le decisioni, con ✅ (dell'utente) 🔸 (derivate) ❓ (aperte) |
| [`LEZIONI.md`](../../LEZIONI.md) | i difetti già pagati, per numero |
| [`fasi/01-filo-nudo.md`](../01-filo-nudo.md) | che cosa questa fase dichiara di aver misurato |
| [`CODER.md`](../../CODER.md) | le regole di chi scrive |

Le convenzioni del progetto valgono anche per te: si scrive **in italiano**, e ogni affermazione
porta una marca — `[M]` misurato, `[R]` letto nel codice, `[S]` letto in una specifica, `[?]`
ipotizzato.

## 3. ⛔ I difetti NOTI e ancora APERTI

Sono fatti, non ipotesi: dichiarati qui perché tu **non li riscopra** e perché tu possa cercare
quel che sta **accanto** a loro. Se ne trovi altre facce, o altri punti che ne condividono la
forma, quelli sono rilievi.

1. **`01-b3-rcp-innesta.py --togli` esce con 0 lasciando l'innesto applicato.** `[M]` 10 agosto
   2026: dopo `--togli`, la riapplicazione ha stampato *«l'innesto c'è già: non si tocca niente»*.
   ⚠ *Rettifica delle 16:20 — la prima stesura di questo mandato diceva «dichiara di togliere e non
   toglie», e non è esatto*: `--togli` rimuove `CMakeLists.txt` e i tre file copiati, **stampa** che
   i `.cc/.h` vanno rimessi con l'altro innesto, e **poi esce 0**. Restano da giudicare due cose, e
   sono rilievi tuoi se lo sono: che l'uscita sia 0 su un albero che in quello stato **non compila**,
   e che il `git checkout` chiamato lì dentro **non abbia il codice d'uscita controllato**.
   `ricostruisci()` in `01-b11-guasto.sh` è l'unico chiamante che rispetta l'ordine dichiarato.
2. **Il conteggio «482 righe / 333 di codice»** dello strato WebTransport, citato in `README.md`,
   è **di prima** della lettura della capsula di chiusura, e non è stato rifatto. Con tutt'e due gli
   innesti applicati l'esempio porta **972 righe aggiunte, 618 di codice** `[M]` — un numero che
   **non è confrontabile** con 482/333, che era del solo strato B2. ⚠ Il paragrafo che oggi sta in
   `README.md` su questo punto è scritto sulla descrizione sbagliata del punto 1, ed è esso stesso
   materiale da contraddire.
3. **Il registro del server si legge con `tail -600`** (`01-b11-guasto.sh`, azione `registro`): i
   conteggi del secondo testimone stanno dentro quella finestra. Era `tail -60`, e con una riga in
   più nel filtro «i guasti serviti» sono scesi da 26 a 21 senza che il server cambiasse niente.
4. **La rotazione automatica del certificato a quattordici giorni non ha banco.** Cambiarlo a mano
   è provato; che il server rigeneri **prima** della scadenza no.
5. **`lsquic` e `SETTINGS_WT_MAX_SESSIONS`**: previsione aperta dopo due misure, non chiusa.
6. **B11 ha dato verdetti diversi fra giri identici** il 10 agosto (`congedo:0x00` invece di
   `0x0b`; `GIA_ATTIVA_REMOTA` sul caso successivo). Due cause sono state curate — la chiusura di
   §3.1 che correva contro la risposta della pagina, e il posto tenuto per tutto lo smontaggio del
   trasporto. ⚠ **Non è dimostrato che fossero le sole.**

## 4. La forma del verdetto

Quella di `REVIEWER.md` §4, senza varianti:

```
DOVE:             file e riga, o funzione
COSA CONTRADDICE: una lezione (LEZIONI.md §x), una regola, un invariante (I1..I8),
                  una sezione di RCP.md, o un altro pezzo di codice
COME SI DIMOSTRA: il caso concreto che fa emergere la contraddizione — un input,
                  non un'ipotesi
MARCA:            [R] contraddizione confermata da una regola già scritta
                  [?] sospetto non ancora confermato
```

⛔ **Un rilievo senza «come si dimostra» è un'ipotesi, non un difetto**, e come tale va marcato `[?]`.

## 5. Che cosa consegni

1. **Il rapporto intero** in `fasi/rapporti/R<N>-<tua-area>.md`, con tutti i rilievi nella forma di
   §4, i `[R]` prima dei `[?]`.
2. **Come testo di ritorno**, e nient'altro: l'elenco ordinato dei rilievi, **uno per riga**, nella
   forma `[R] percorso:riga — contraddice X — si dimostra con Y`. Al massimo **quindici**, i più
   gravi per primi. ⚠ Niente preamboli, niente riassunti del codice, niente complimenti.
3. Se non hai trovato niente in un'area, lo dici con **quelle parole** — *«non ho trovato niente»* —
   e dichiari **che cosa hai provato a rompere e non sei riuscito a rompere**.

⛔ **Non modifichi nessun file** fuori dal tuo rapporto. La cura è del coder.
