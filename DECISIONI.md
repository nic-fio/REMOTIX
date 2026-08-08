# DECISIONI — il registro di quel che è stato deciso, e da chi

*Aperto l'8 agosto 2026, al primo giorno di REMOTIX_V2.*

Questo documento non spiega e non convince: **registra**. A che serve, in una riga: una
decisione presa a voce e non scritta è una decisione che fra due settimane nessuno sa più
se era stata presa, e che il primo dubbio riapre da capo.

Ogni voce dice **che cosa**, **quando**, **perché** — e soprattutto **con che grado di
certezza**, perché la differenza fra «l'utente ha detto sì» e «è una conseguenza che ho
tratto io» è precisamente la differenza che `LEZIONI.md` §2.3-quater dice di non perdere.

| Marca | Significato |
|---|---|
| ✅ **Deciso** | l'utente ha detto sì, esplicitamente. Non si riapre senza una misura che la smentisca |
| 🔸 **Derivato** | conseguenza logica di una decisione ✅, scritta nei documenti ma mai pronunciata. Se sbaglio, si corregge senza discussione |
| ❓ **Aperto** | domanda posta, risposta non ancora data. **Non è una decisione**: è un buco che qualcuno deve chiudere |

E le marche delle *ragioni* restano quelle di `CODER.md` §5: `[M]` misurato, `[R]` letto nel
codice, `[S]` letto in una specifica, `[?]` ipotizzato.

---

## 1. Il protocollo

### 1.1 ✅ RDP muore. Il protocollo è nostro.

*8 agosto 2026. «Windows e tutto quello lo riguarda muore».*

La riga `== NO WINDOWS ==` non è una nota a margine: è la leva che toglie i tre muri contro
cui v1 si è fermato, e che erano tutti e tre di RDP e non del problema — il tetto a H.264
(`v1/documenti/SPECIFICA.md` §5.1), il client Android che decodificava in software, e il
colore pieno irraggiungibile.

**Il prezzo, accettato:** il protocollo va progettato oltre che scritto, e i client vanno
scritti da zero — quello Android è un progetto a sé, non una funzionalità.

**Che cosa decade con RDP:** EGFX, `MapSurfaceToOutput`, RemoteFX Progressive, AVC444, NLA e
CredSSP, MS-RDPEDISP, `ERRINFO_*`, FreeRDP 3 come vincolo, la matrice dei tre client altrui,
e `v1/documenti/REFERENCE.md` quasi per intero.

### 1.2 🔸 Il protocollo si chiama FILO

*8 agosto 2026, per delega: «rinominalo in quello che ti pare».*

È la parola che i documenti usano già per il protocollo (`CODER.md` §0: «per chi tocca il
filo»). Corta, greppabile in maiuscolo, nella lingua del progetto, e significa quel che è.
In codice: `libfilo`, `filo_frame_t`, `FILO/1`.

L'alternativa offerta e non scelta era **RXP** (*Remotix eXchange Protocol*). Cambiare nome
adesso costa niente; fra un mese costa un `sed` su tutto.

### 1.3 🔸 La sessione non conosce il codec: lo negozia la connessione

Discende da 1.1 e da §4. Il palco produce fotogrammi; ogni connessione ci attacca il proprio
codificatore con le capacità del **suo** client. Se il codec fosse una proprietà della
sessione, riprendere da un dispositivo diverso — telefono la mattina, portatile il pomeriggio
— richiederebbe di rifare la sessione, che è esattamente ciò che la persistenza deve evitare.

---

## 2. I numeri

### 2.1 ✅ Minimo: 480p · 25 fps · 24 bit — ed è una garanzia, non un traguardo

*8 agosto 2026.*

Diceva «30 fps a 1080p», ed era il numero di v1 — che lo superava già `[M]`: la cattura di
Mutter consegnava 37 fotogrammi, KWin 60.

Il cambiamento è di **natura** più che di valore: il minimo smette di essere un'asticella da
inseguire e diventa il **livello sotto cui non si scende e non si stacca**, per quanto brutta
sia la linea. Nasce dal caso della rete mobile (§3.1), non da una rinuncia sulla qualità.

**Conseguenza già applicata** (`CODER.md` §1): la regola che governa le scelte tecniche è stata
sdoppiata, perché un'asticella che ogni scelta supera non filtra più niente. Verso l'alto
filtra il desiderato; verso il basso vincola il minimo.

### 2.2 ✅ Desiderato: 4K · 60 fps · 10 bit per canale

*8 agosto 2026. «direi che 10 bit è la scelta giusta».*

Diceva «profondità colore 32 bit», che non è una grandezza esistente: 32 bpp sono 24 bit di
colore più 8 di alfa, e l'alfa non si trasmette. L'intenzione dell'utente era *«massima
qualità»*, e sotto quella parola stavano due leve distinte:

| Leva | Cura | Prezzo |
|---|---|---|
| **10 bit per canale** | le strisce sulle sfumature | quasi nulla, e in hardware ovunque — decoder Android compreso |
| **4:4:4** | il testo colorato sfrangiato `[M]` v1 §5.2 | ~50 % di banda, **nessun decoder Android in hardware** |

Scelto il 10 bit: la massima qualità ottenibile **su entrambi i client insieme**, in hardware.

### 2.3 🔸 Il 4:4:4 resta una `[?]`, non una promessa

Sarebbe un'opzione per il solo client Linux su GPU capaci (NVIDIA sì, Intel a volte, AMD no).
Ma **nessuno ha misurato quanto si veda davvero la differenza** sul desktop dell'utente:
vale `LEZIONI.md` §2.3-quater. Si decide su un banco che metta le due immagini a confronto, e
a giudicare è l'utente (§7.3), dietro un interruttore spento di suo (§2.4).

---

## 3. La rete e la degradazione

### 3.1 ✅ I 30 Mbps non sono un pavimento: sono uno scenario

*8 agosto 2026. «il server deve poter fare il suo meglio per offrire la migliore esperienza
possibile a client che si collegano da connessioni critiche (come da una rete mobile).
Ovviamente non pretendo i miracoli come 4K a 300 kbps».*

Scritti come «banda minima 30 mbps» dicevano al programmatore l'opposto dell'intenzione — che
sotto i 30 non si va. Il requisito vero è **l'adattamento**, non una soglia.

Gli scenari da servire:

| Collegamento | Banda | Ritardo e perdita | Che cosa fa il server |
|---|---|---|---|
| fisso buono | 30+ Mbps | bassi | punta al desiderato |
| fisso modesto, WiFi | 5–15 Mbps | medi | **spende tutto quel che c'è** |
| mobile critico | < 2 Mbps, variabile | alti, con perdita | tiene il minimo, **e non stacca** |

### 3.2 🔸 L'invariante I1, riscritta

Il ritmo **non cala mai** per prudenza, per risparmio o perché la scena è ferma. Cala **solo**
quando la misura dimostra che la linea non porta, e ogni discesa è dichiarata nel registro.

La ferita della fase 10 di v1 resta protetta — il divieto di risparmiare è intatto — ma non
impedisce più di cedere quando cedere è l'unica cosa sensata. Vietata l'euristica prudente,
obbligatorio l'adattamento misurato.

*Applicata in `CODER.md` §2 e `REVIEWER.md` §3, che vanno in coppia.*

### 3.3 ✅ Sotto il minimo si calano i fotogrammi. Mai sgranare, mai staccare.

*8 agosto 2026. «continuare a calare i fotogrammi, mai staccare».*

Su un desktop **degradare nel tempo è meglio che degradare nello spazio**: a pochi fotogrammi
al secondo ognuno resta nitido e il testo si legge — è lento ma ci si lavora. Sgranando
l'immagine il testo diventa illeggibile e non ci si fa più niente. E a ritmo basso si possono
spendere più bit su ciascun fotogramma: la lentezza si paga una volta sola.

### 3.4 🔸 «Segni di vita» si verifica dal lato che riceve

Un client è vivo se **arrivano suoi pacchetti**, non se noi non abbiamo ricevuto errori
(`LEZIONI.md` §1.7). QUIC lo fa di suo, col proprio battito e il proprio tempo di inattività:
non va inventato, va letto dal lato giusto.

---

## 4. La sessione

### 4.1 ✅ La sessione sopravvive al client; è l'utente a chiudere e riprendere

*8 agosto 2026. «è l'utente da solo che capisce che è meglio chiudere il client (tenendo la
sessione aperta) e continuare quando la situazione migliora».*

È l'invariante I4 di v1 (`palco.c`, 1.545 righe, fra il codice che sopravvive), qui promossa
da dettaglio implementativo a **comportamento promesso all'utente**.

### 4.2 ✅ Dopo 6 ore senza segni di vita la sessione viene chiusa

*8 agosto 2026, proposta dall'utente.* Il valore resta. **Ma il perché è stato contestato e
la contestazione non ha ancora risposta** — vedi §7.2: il pericolo non è che la sessione sia
aperta, è che sia *sbloccata*, e uccidere butta via il lavoro dell'utente.

---

## 5. La geometria — la tela e la vista

### 5.0 ✅ La tela nasce a ogni attacco, e sta ferma finché il client resta

*8 agosto 2026, modello dettato dall'utente.*

| Momento | Chi decide la misura | Chi adatta |
|---|---|---|
| **attacco** | il client: la sessione legge la sua risoluzione e usa quella | nessuno — è 1:1 |
| **durante la sessione** | nessuno: la tela non si muove | il **client** riscala l'immagine |
| **riattacco** da un altro dispositivo | il nuovo client, con la sua risoluzione | nessuno — di nuovo 1:1 |

Chiude la domanda che era aperta in §7.1: la tela **non** ha un valore predefinito né una
preferenza dell'utente. La detta il client, a ogni attacco.

**La virtù del modello è il caso mobile**, e viene giusto da solo: il telefono si attacca e la
tela nasce della forma del telefono — pixel veri, niente bande, niente scalatura. Nessuna
delle alternative discusse (tela fissa generosa, tela con vista scorrevole) faceva altrettanto
bene senza logica aggiuntiva.

**L'attacco funziona su tutti e quattro i desktop**, KDE compreso: la misura si scrive nella
riga di avvio del compositore (`--virtual --width W --height H`) **prima** che la sessione
parta, e la sessione parte al primo attacco.

### 5.0-bis 🔸 Il riattacco a misura diversa su KDE < 6.8: degradazione dichiarata

È l'unico punto in cui il modello non può essere servito. A sessione viva KWin 6.3.6 non
cambia misura `[M]`, e riavviarlo significherebbe uccidere la sessione — cioè distruggere
proprio il distacco che il modello offre.

**Ripiego: si tiene la tela vecchia e riscala il client.** Non costa una riga in più, perché è
lo stesso codice del punto «durante la sessione». Su Debian stabile, riattaccandosi da un
dispositivo di forma diversa, si vede il desktop della forma precedente riscalato, finché la
sessione non viene chiusa. Su GNOME, wlroots e KDE ≥ 6.8 si vede la forma nuova.

Il ripiego **si dichiara nel registro** (`CODER.md` §4.2): un ripiego silenzioso produce due
comportamenti sotto la stessa etichetta.

### 5.0-ter 🔸 `[?]` Ridurre anche la misura codificata quando la finestra è piccola

Se l'utente restringe molto la finestra, il server continua a codificare la tela intera e il
client la rimpicciolisce: quei pixel si pagano in banda senza vederli. Si **potrebbe** far
scendere anche la misura codificata sotto una certa soglia, con assestamento.

⚠ **Non è nel modello, ed è volutamente fuori**: prima va misurato se il problema esiste
davvero, e quanto pesa. Un'ottimizzazione decisa prima della misura è §7.2 di `LEZIONI.md` —
ottimizzare nella direzione sbagliata.

### 5.1 ✅ Se l'utente ridimensiona la finestra, l'immagine si riscala

*8 agosto 2026. «Tagliamo la testa al toro. Anziché correre dietro ai compositor, una scelta
che vale per tutti».*

**Ridimensionare la finestra del client non tocca mai il desktop.** Si adatta la vista; le
finestre dell'utente non si muovono. Uguale su GNOME, KDE, XFCE e LXQt.

Le tre ragioni, e la terza è quella che ha deciso:

1. su KDE 6.3.6 — cioè Debian Trixie — **non si può** ridimensionare: la misura sta nella riga
   di comando di KWin (`--virtual --width W --height H`), il modo è `const`, e
   `stream_virtual_output` risponde `Could not find output` per ogni misura `[M]` 8 ago;
2. la correzione a monte esiste (`kwin!7932`, traguardo 6.8, ottobre) ma **Debian stabile non
   aggiorna Plasma**: 6.3.6 fino a Forky. Il ripiego non è un'impalcatura temporanea, è un
   percorso di codice da mantenere per anni;
3. ⛔ **e anche dove funziona, fa una cosa peggiore**: ridimensionare un output ridispone le
   finestre dell'utente `[R]`. Su KWin la chiave del `PlacementTracker` contiene la geometria
   dell'output, quindi tornando a una misura già vista le finestre vengono **teleportate**
   indietro. La versione «giusta» scompiglia il lavoro; quella «rotta» lo lascia fermo.

**Conseguenze:**
- il ridimensionamento del compositore esce dal percorso critico e resta come funzione
  facoltativa («adatta il desktop a questa finestra»), spenta dove il compositore non la sa
  fare, **con la ragione dichiarata** (`CODER.md` §4.2);
- quando si scriverà, si scriverà **nella forma della negoziazione PipeWire** — decisione già
  presa in `kde.md` §8.2 — perché è una strada sola per GNOME, wlroots e KDE 6.8, e su KDE si
  accende da sé all'aggiornamento;
- ⚠ e includerà la **guardia obbligatoria** `if (misura_attuale == misura_richiesta) return;`
  (`kde.md` §8.2-bis): senza, la rinegoziazione si morde la coda. Il difetto **non si vede su
  Trixie** e compare il giorno dell'aggiornamento a 6.8, quando nessuno lo sta più cercando.

### 5.2 🔸 Il codificatore lavora alla misura della finestra, non della tela

Regalo che arriva gratis da 5.1: finestra piccola ⇒ meno pixel da codificare ⇒ **la stessa
banda rende di più**. Sul telefono in rete mobile aiuta da solo, senza logica aggiuntiva.

### 5.3 🔸 Il prezzo di 5.1, dichiarato

Tela 1080p vista da uno schermo 4K = desktop ingrandito, quindi morbido. Ingrandire non
inventa dettaglio. La via d'uscita è la voce «adatta il desktop», ed è il motivo per cui la
misura iniziale della tela conta — vedi la domanda aperta §7.1.

---

## 6. Il codice che si eredita

### 6.1 ✅ Il patrimonio di v1 è qui, e versionato

*8 agosto 2026.* Portato dal server di sviluppo, dove viveva senza versionamento e senza una
seconda copia. Verificato per impronta SHA-256, 103 file su 103.

| | |
|---|---|
| `v1/remotix-c/` | **17.481 righe di C**, 26 moduli |
| `v1/remotix-c/prove/` | **4.563 righe di banchi**, uno script per fase |
| `v1/banchi/` | **262 file** dell'indagine sulla fase 11, `misura-cattura.c` compreso |
| `v1/remotix-rust/` | 7.163 righe, ramo IronRDP chiuso il 3 agosto |
| `v1/documenti/` | PIANO, SPECIFICA, REFERENCE, protocollo-rdp, client-android, xrdp |
| `v1/calibrazione/` | le tre scene della taratura del 1 agosto |

`LEZIONI.md` è stato promosso al livello di V2: è il fondamento di `CODER.md` e `REVIEWER.md`,
che lo citano 29 volte su 20 sezioni.

### 6.2 🔸 Circa il 79 % del C sopravvive alla morte di RDP

Misurato contando le occorrenze di `freerdp|winpr|rdpContext|RDPGFX|rdpSettings` per file:
7.442 righe **pulite** (`palco`, `cattura`, `kwin`, `mutter`, `appunti_wlr`, `superficie`,
`sentinella`, `autenticazione`…), 4.570 con contaminazione superficiale, 1.781 media, e
**3.688 che muoiono** (`server.c`, 134 occorrenze, e `rete.c` che va sostituito da QUIC).

⚠ È una misura di primo livello: contare gli `#include` dice chi *tocca* FreeRDP, non chi
*dipende* da RDP. `scambio.c` e `codificatore.c` vanno letti prima di dare il 79 % per buono.

---

## 7. ❓ Le domande aperte

**Non sono decisioni.** Sono buchi, elencati perché non si perdano.

### 7.1 ~~La misura della tela alla nascita~~ → **chiusa l'8 agosto, vedi §5.0**
La detta il client a ogni attacco. Niente predefiniti, niente preferenze.

### 7.2 Blocco schermo alla disconnessione — contro-proposta a §4.2
Il rischio di una sessione persistente non è che sia aperta (per entrare serve PAM), è che sia
**sbloccata**. Bloccare lo schermo appena il client se ne va chiude il pericolo in dieci
secondi invece che in sei ore, e **non butta via il lavoro dell'utente**. Le sei ore
resterebbero, con un altro mestiere: raccogliere le risorse, non difendere la sicurezza — e
allora diventano una politica configurabile, con quel valore come predefinito, e con un
**congedo pulito** invece di un colpo secco.

### 7.3 Il fantasma: subentro o attesa?
Se il telefono muore in galleria e un'ora dopo apro il portatile, la connessione morta mi
tiene fuori dalla mia sessione? **Subentro** (chi arriva ha ragione, stesso utente
autenticato), **attesa** (la vecchia tiene il posto per un tempo dichiarato), o **insieme**
(due client sullo stesso desktop — costa poco con un palco persistente, ma cambia il
protocollo e va deciso prima, non dopo).

### 7.4 Proporzioni: bande o allungamento?
Credo si risponda da sé — allungare deforma il testo e lo rende illeggibile — ma va detto.

⚠ **Il modello di §5.0 la rimpicciolisce parecchio**: siccome la tela nasce della forma del
client, all'attacco le proporzioni **combaciano sempre**. Il caso resta solo in due punti: il
ridimensionamento della finestra durante la sessione, e il ripiego di §5.0-bis su KDE vecchio.

### 7.5 Il linguaggio del server
Raccomandato **C**, per non buttare le ~14.000 righe che sopravvivono, con **`quiche`**
(API C, licenza BSD-2) per il QUIC — che era l'unico argomento serio a favore di Rust.
**Non confermato dall'utente**: sta qui perché non venga dato per deciso.

### 7.6 La licenza
Da decidere. Un vincolo è già emerso: **niente x265** (GPL-only) come ripiego software, per
non incatenare tutto il server. Con SVT-AV1 (BSD-3) e FFmpeg senza `--enable-gpl` la scelta
resta libera.

### 7.7 Multi-tenant: quanti utenti insieme?
In v1 era **fuori scope** (§4.2); in V2 entra in una riga. Non è un problema di protocollo, è
di GPU: quattro sessioni a 4K60 non stanno su un'integrata. Il numero decide se serve una coda
di codifica condivisa.

### 7.8 La latenza
**Non è nominata in `SPECIFICHE.md`**, ed è *la* metrica di un desktop remoto — più dei
fotogrammi. 60 fps con 200 ms sono inusabili; 30 fps con 40 ms sono ottimi. Serve un numero da
tasto a pixel, misurato dal lato che riceve (`LEZIONI.md` §1.7).

### 7.9 La fiducia: chi autentica il server verso l'utente?
PAM autentica l'utente verso il server; niente fa il contrario. Certificato autofirmato con
fiducia al primo incontro? Impronta da confrontare? Senza, la prima connessione è un
uomo-in-mezzo gratuito.

### 7.10 Il touch da Android: mouse emulato o touch vero?
Questione aperta n.1 di v1, mai chiusa. Va decisa **prima** di scrivere FILO: sono due canali
di input diversi.

### 7.11 La clipboard: bidirezionale?
`SPECIFICHE.md` dice «server-client», che si legge in un verso solo. E su KDE la clipboard
**appartiene al compositore** e c'è anche senza di noi (`LEZIONI.md` §3, domanda 14).

### 7.12 Il «fuori scope»
V1 aveva un §4 che diceva cosa **non** si fa — dischi, stampanti, X11, multi-monitor — ed è il
paragrafo che protegge dallo scivolamento. Qui c'è solo `NO WINDOWS`.

### 7.13 Cinnamon
Nell'elenco con un punto interrogativo, ben messo: su Wayland è ancora sperimentale e Muffin
eredita i difetti di Mutter senza le sue correzioni. Proposto **fuori scope rivalutabile**.

---

## Come si tiene questo documento

Una voce ❓ che riceve risposta **si sposta** nella sezione che le compete e cambia marca; non
si risponde in fondo. Una voce 🔸 che l'utente conferma diventa ✅. Una voce ✅ si riapre solo
con una misura che la smentisce — e allora si riscrive **nello stesso momento**, con la data e
la fonte (`CODER.md` §5).
