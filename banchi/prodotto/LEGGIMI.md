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
