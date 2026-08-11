# `banchi/prodotto/` — quel che viveva **solo sul server**

*Recuperato l'11 agosto 2026, a codice fermo, prima di sincronizzare i due alberi.*

⛔ **Questi quattordici file esistevano in un posto solo**: `/media/REMOTIX/src/` sul server
192.168.0.2, che **non è un albero git** e non ha una copia da nessuna parte. Sono il lavoro della
notte del 10 agosto — la prima e unica accensione del prodotto `src/` — e nessun documento li
nomina. Un `tar` sbagliato, o una risincronizzazione con `--delete`, li avrebbe cancellati senza
che nessuno se ne accorgesse.

⚠ **Sono presi come stavano, senza toccarli.** Non sono ancora banchi: sono gli attrezzi usa-e-getta
di chi ha acceso il server quella notte, e i registri che ne sono usciti. Chi scrive il banco del
prodotto (punto 1 della sessione dell'11 agosto) li rifà nella forma che il progetto pretende —
scena dichiarata, controllo positivo, denominatore — e allora questi si buttano. **Fino a quel
momento sono l'unica prova che quel giro è avvenuto.**

---

## ⭐ Il banco c'è, ed è `banchi/01-p1-prodotto.sh` — 11 agosto 2026, 04:55 UTC

*Aggiunto dopo il primo giro verde. ⛔ **Non si butta ancora niente**, e sotto c'è la riga che dice
esattamente quanto di questa cartella è stato sostituito e quanto no.*

| attrezzo | lo rifà `01-p1-`? | |
|---|---|---|
| `avvia-server.sh` · `spegni.sh` | ✅ **sì** | l'accensione, il pid, lo spegnimento con TERM e il controllo che TERM sia bastato stanno in `01-p1-dentro.sh`, con **la porta 7448 dichiarata** e i file in `/srv/src/tmp/p1-*` invece che sparsi in `/srv/src/` |
| `fumo.sh` | ✅ **sì, e corregge un difetto** | ⛔ `fumo.sh` ha **`PORTA=${2:-7447}`**: lanciato senza argomenti accende **il prodotto sulla porta dell'innesto**, e `bsslserver` è quello che 11 banchi su 14 si aspettano lì. `01-p1-` non prende la porta da un argomento: la 7448 è scritta dentro |
| `check-env.sh` | ✅ **sì** | quel che c'è nel contenitore lo dichiara il banco, riga per riga, invece di stamparlo e basta |
| `b11-fumo.py` | — | è di B11, non del prodotto |
| ⛔ `filo.sh` | ❌ **no** | è la **stretta di mano RCP** col cliente di prova di B3 e l'arbitro di B4. `01-p1-` si ferma prima del filo, e lo dichiara: si autenticherebbe, e tre parole d'ordine sbagliate mettono l'indirizzo fuori 12 ore (B0.3) |
| ⛔ `resto.sh` | ❌ **no** | rotazione del certificato, certificato dell'amministratore, ban + pagina + sblocco. ⚠ **E una sua gamba è già morta**: la riga 83 chiama `remotix --ban … --sblocca <ind>`, e quell'opzione **non esiste più** dal rilievo R12.1 — `[M]` l'11 agosto 2026: stampa la spiegazione ed esce **2**, e `resto.sh` non guarda lo stato d'uscita |

⛔ **Quindi questa cartella non si butta**: `filo.sh` e `resto.sh` restano l'unica traccia di come si
provano il filo e il ban contro il **prodotto**, e finché non esistono i banchi che li rifanno,
buttarli toglierebbe una descrizione senza sostituirla.

## Gli attrezzi

| file | che cosa fa | data |
|---|---|---|
| `avvia-server.sh` | ⭐ **come il prodotto è stato acceso**: `remotix --indirizzo 0.0.0.0 --nome 192.168.0.2 --porta 7448 --certificati /srv/src/remotix-cert --pagina …/pagina.html --ban /srv/src/remotix-ban`, dentro il contenitore, con il pid su file. ⛔ **Porta 7448**, cioè non quella dell'innesto: i due server possono stare accesi insieme | 10 ago 23:05 |
| `spegni.sh` | lo spegne dal file del pid | 10 ago 23:07 |
| `filo.sh` (57 righe) | un giro di filo contro il prodotto | 10 ago 22:58 |
| `fumo.sh` (74) | la prova di fumo | 10 ago 22:52 |
| `resto.sh` (95) | il resto del giro | 10 ago 23:00 |
| `check-env.sh` (18) | che cosa c'è nel contenitore | 8 ago 22:20 |
| `b11-fumo.py` (45) | la prova di fumo di B11 | 10 ago 10:25 |

## I registri, e sono misure

⛔ **Questi non si rifanno: sono numeri con una data.** Se una misura futura li contraddice, la
differenza si spiega — non si sovrascrive.

| file | che cosa contiene |
|---|---|
| `b8-campioni.jsonl` (15 kB) | i campioni del secondo fisso di B8 |
| `b8-fatti.jsonl` (25 kB) | i fatti del giro di B8 |
| `b12-esiti.jsonl` | gli esiti di B12 |
| `01-s1b-visite.jsonl` | le visite dell'orologio dei sette giorni di S1b (il verdetto è del 17-18 agosto) |
| `corpo.html` · `pagina-ban.html` · `pagina-dopo.html` | ⭐ **il corpo della pagina come il browser l'ha vista**, nei tre stati: normale, bannato, dopo lo sblocco. È la sola prova su disco che la pagina del ban di §4.4-bis è stata guardata da un motore vero |
