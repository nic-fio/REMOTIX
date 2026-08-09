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

## 0. Il principio che ha prodotto le altre

### 0.1 ✅ Si dipende dal compositore, non dal suo contorno

*8 agosto 2026. «Voglio evitare di smettere di correre dietro ai compositor e cominciare a
dover inseguire i display manager».*

Sta in cima perché non è una decisione fra le altre: è il criterio con cui se ne prendono
diverse, e almeno tre di quelle scritte qui sotto discendono da questa.

| | |
|---|---|
| **si insegue** | il **compositore**, perché solo lui consegna i fotogrammi e accetta l'input. `mutter.c` e `kwin.c` esistono per questo e continueranno a esistere |
| **non si insegue** | il **contorno**: blocca-schermo, demoni di inattività, gestori dell'energia, display manager. Fanno la stessa cosa in quattro modi, con quattro configurazioni che si riscrivono da sole |

**La prova, prima di appoggiarsi a un meccanismo:** *quante implementazioni diverse dovrei
inseguire, e quanto mi costa farla da me?* Quattro divergenti e un costo piccolo ⇒ si fa da
noi, una volta sola.

⚠ **Non è un permesso di riscrivere.** `logind`, PAM, PipeWire, `libei`, `xkbcommon`, QUIC:
uno solo ciascuno, uguale ovunque. Lì vale `CODER.md` §4.1 senza sconti, e scrivere il nostro
sarebbe il difetto che quella regola vieta.

**Dove ha già deciso:** §4.3 (il blocco è nostro invece di quello dei desktop), §5.1
(ridimensionare non tocca il compositore), e in negativo §1.1 — smettere di inseguire i client
altrui era lo stesso ragionamento applicato al filo.

*Scritta anche in `CODER.md` §4.1-bis, con la verifica corrispondente in `REVIEWER.md` E11 —
le due devono restare in coppia, altrimenti è una regola non verificata.*

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

### 1.2 ✅ Il protocollo si chiama RCP — *Remotix Control Protocol*

*8 agosto 2026, scelto dall'utente.*

```
librcp.so
rcp_frame_t · rcp_connect() · rcp_session_t
stretta di mano:  RCP/1
```

Due nomi provvisori l'hanno preceduto nello stesso pomeriggio e sono stati scartati: **FILO**
(«proprio non si può sentire») e **RXP**. Sono citati qui solo perché chi ritrova quei nomi in
un appunto sappia che si parlava di questo, e non di altro.

⚠ **Una collisione minore, da sapere prima di battezzare i binari**: `rcp` è il nome di un
comando Unix storico — la copia remota della famiglia `rsh` — oggi quasi ovunque disinstallato
e mai attivo di suo. Non tocca né il protocollo né la libreria; riguarda solo l'eventuale
comando a riga di comando, che conviene chiamare `remotix` e non `rcp`.

⭐ **E il nome dice una cosa giusta**: *Control*, non *Display*. Il protocollo non porta solo
pixel — porta input, appunti, geometria, congedo e stato della sessione, e il video è uno dei
suoi canali. È la differenza fra RCP e ciò che RDP faceva credere di essere.

### 1.3 ✅ La fiducia nel server: ricordata in silenzio, mai confermata a mano

*9 agosto 2026. «Se inserisco i dati fondamentali (ip, porta, userid e password) so che quel
server è mio. La sicurezza va bene, ma qui non stiamo costruendo un sistema basato su standard
militari».*

**Nessun confronto di impronte, nessuna autorità di certificazione, nessun dominio.** L'utente
digita indirizzo, porta, utente e password, e basta.

Il certificato serve comunque — QUIC pretende TLS, non esiste l'opzione «senza» — quindi il
server se ne genera uno autofirmato all'installazione. Il client, al primo collegamento, lo
**accetta in silenzio e se lo ricorda**; dalle volte successive, se cambia, avvisa. È quel che
fa SSH, e non si vede finché non serve: costa **zero interazione** e copre tutti i collegamenti
tranne il primo.

⚠ **La precisazione che è stata fatta e respinta, tenuta perché la decisione si capisca:** il
rischio non è digitare l'indirizzo sbagliato, è che qualcuno intercetti la connessione verso
quello giusto. La prima connessione resta scoperta. **Il rischio è stato valutato e accettato**
dall'utente per lo scenario previsto — server proprio, rete propria o VPN.

🔸 **Due conseguenze che non costano niente e non si vedono:**

1. **la password non parte prima** che il server abbia dimostrato di essere quello di ieri. È
   l'invariante I3 — la guardia parte da negato — applicata all'ordine della stretta di mano.
   Con RDP le credenziali partono presto e l'avviso sul certificato arriva quando ormai le hai
   date; qui è solo questione di cosa si scrive per primo sul filo;
2. **un certificato vero, se c'è, si usa e vale di più** — roba dell'amministratore, non
   dell'utente, e non aggiunge un passaggio a nessuno.

⚠ E una trappola già pagata da v1, da non ripetere: *«un certificato TLS condiviso uccideva il
server alla seconda connessione; una prova a connessione singola resta verde per sempre»*
(`LEZIONI.md` §2.1). Il banco della stretta di mano si fa **con due connessioni**, non con una.

### 1.4 🔸 La sessione non conosce il codec: lo negozia la connessione

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

*8 agosto 2026, proposta dall'utente.* Il valore resta, e con §4.3 il suo mestiere è chiarito:
**raccogliere le risorse**, non difendere la sicurezza — di quella si occupa lo stacco a 30
minuti. Su un server multi-utente ogni sessione dimenticata tiene memoria, GPU e un
codificatore.

### 4.3 ✅ Il blocco è di REMOTIX, non del desktop — 30 minuti senza input, poi stacco

*8 agosto 2026. «Se non arriva input dall'utente per 30 minuti la sessione si blocca:
l'utente dovrà fare il re-attach con user e password».*

Dopo 30 minuti senza input, REMOTIX **stacca il client**. Il desktop resta com'era, ma non lo
vede più nessuno: per rivederlo serve un attacco nuovo, con utente e password.

⛔ **Il blocco schermo dei desktop resta spento**, com'era in v1 — `--no-lockscreen` su KWin e
gli equivalenti sugli altri tre. Non è una svista ereditata: è una dipendenza, e ora ha una
ragione scritta. Le quattro strade del «modo A» sono queste, tutte `[R]`:

| Desktop | Che cosa succede bloccando davvero |
|---|---|
| **GNOME** | ⛔ **la revoca.** Entrando nel dialogo di sblocco, gnome-shell chiama `inhibit_remote_access()` e Mutter **chiude ScreenCast, RemoteDesktop e InputCapture, rifiutando di ricrearli** (`gnome.md` §4). C'è l'eccezione `is_headless()`, che è il nostro caso — ma è letta nel codice e **mai misurata** |
| **KDE** | ⛔ **la catena che si morde la coda.** A blocco attivo la nostra inibizione è ignorata (`powerdevilpolicyagent.cpp:509`); powerdevil spegne lo schermo a 10 minuti; con zero uscite KWin monta un output fittizio **con un filtro che inghiotte tutto l'input** (`kde.md` §10.2-10.3). Ci si blocca e non si sblocca più |
| **XFCE, LXQt** | i loro demoni di inattività, e su LXQt `enableIdlenessWatcher=false` **viene riscritto a `true`** dal demone al primo avvio (`lxqt.md`) |

**Le tre ragioni della scelta**, in ordine di peso:

1. **un comportamento solo per quattro desktop**, invece di quattro cure fragili — e tre di
   quelle cure sarebbero righe di configurazione, cioè ciò che l'invariante **I7** vieta;
2. **il conteggio è nostro e non ha incognite**: l'input lo iniettiamo noi, quindi sappiamo
   esattamente quando è passato l'ultimo. Col modo A dovremmo fidarci che il rilevatore di
   inattività di ciascun desktop veda gli eventi di `libei` — su KDE è `[R]` che sì
   (EIS → `simulateUserActivity`), sugli altri tre sarebbe da misurare;
3. **la sicurezza è la stessa**: l'unica strada per quel desktop passa da RCP, e RCP passa
   da PAM. La schermata di blocco chiederebbe la medesima password.

> ⚠ **E questa decisione ha una condizione di scadenza, posta dall'utente lo stesso giorno:**
> *«non escludo che un domani potremmo implementare un metodo di autenticazione molto più forte
> della semplice password, ma per il momento va bene solo questa»*.
>
> Il ragionamento del punto 3 **regge solo finché la password PAM è l'unica chiave**. Il giorno
> in cui RCP autenticasse con qualcosa di diverso — un gettone sul dispositivo, una chiave, un
> secondo fattore — il blocco del desktop smetterebbe di essere ridondante e diventerebbe una
> difesa vera, perché chiederebbe una chiave **che chi ha rubato la prima non ha**.
>
> **Chi implementa l'autenticazione forte rilegge questa voce**, e non la dà per acquisita.

### 4.4 ✅ Un client che tace è un client che si è staccato

*8 agosto 2026. «Fantasma: lo trattiamo come nel caso in cui l'utente chiude il client».*

Nessuna connessione «tiene il posto». Chi tace è staccato, chi arriva entra — senza timeout da
aspettare, senza subentro da negoziare, senza il caso «il telefono è morto in galleria e ora
non posso rientrare dalla mia sessione» che v1 aveva dovuto tamponare con keepalive stretti.

Sparisce così anche il bivio *subentro contro attesa*: non esiste più, perché non esiste il
posto occupato.

### 4.5 🔸 I tre orologi della sessione

Le decisioni 4.1-4.4 mettono in fila tre tempi diversi, che vanno tenuti distinti perché
misurano cose diverse:

| Orologio | Quanto | Che cosa scatta | Deciso in |
|---|---|---|---|
| **silenzio del client** | ❓ da fissare | il client si considera staccato | §4.4 |
| **inattività dell'utente** | **30 minuti** senza input | REMOTIX stacca il client | §4.3 |
| **abbandono della sessione** | **6 ore** senza alcun attacco | la sessione viene chiusa, con congedo pulito | §4.2 |

Sono in scala: il primo si misura in secondi, il secondo in minuti, il terzo in ore. Un utente
che lascia il client aperto e va a pranzo viene staccato dopo mezz'ora e ritrova tutto
riattaccandosi; se non torna entro le sei ore successive, la sessione viene raccolta.

⚠ **Una conseguenza da tenere d'occhio**: «input» è quel che l'utente manda, non quel che
guarda. Chi resta mezz'ora a guardare un video senza toccare nulla viene staccato. Il costo è
piccolo — riattaccarsi è rapido — ma se emergesse come fastidio, la cura è un cenno di
presenza dal client, non l'allungamento della soglia.

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

## 5-bis. L'input

### 5-bis.1 ✅ Il puntatore lo disegna il client, non il desktop

*8 agosto 2026, proposta dall'utente.*

Il dito trascina un puntatore **disegnato dal client**; un tap fa il clic sinistro sulla
posizione del puntatore, un tap a due dita il destro. Non è il «tocco diretto», dove il dito
è il puntatore: è il trackpad, e si vede dove si sta per cliccare **prima** di cliccare.

**Tre problemi diversi che questa scelta chiude insieme:**

1. ⭐ **la latenza percepita.** Il puntatore si muove alla velocità del dito, non a quella
   della rete. Su un collegamento mobile con 150 ms di ritardo è la differenza fra usabile e
   frustrante — e pesa più dei fotogrammi al secondo, che è la grandezza che di solito si
   guarda;
2. **le scie e le posizioni vecchie** del puntatore, che nascono proprio dal fatto che il
   puntatore viaggi *dentro il video* e arrivi in ritardo;
3. **la precisione.** Un dito è largo ~10 mm, i bersagli di un desktop ne misurano ~4, e nel
   tocco diretto il dito **copre il bersaglio** mentre lo si cerca. In più il passaggio del
   puntatore — da cui dipendono suggerimenti e menu — esiste solo se un puntatore c'è davvero.

### 5-bis.2 🔸 Il cursore non deve MAI essere dentro l'immagine catturata — e va verificato

Discende da 5-bis.1: se lo disegna il client e c'è anche in quel che arriva, se ne vedono
**due**. v1 aveva incontrato il problema tre volte senza collegarle, e la cura è la sua:
*«non nasconderlo: renderlo invisibile»* — un tema con un cursore 1×1 ad alfa zero.

| Desktop | Il cursore è nella cattura? | Il canale della cura |
|---|---|---|
| GNOME / Mutter | **no**, lo esclude di suo (`inhibit_cursor_overlay`) | ⚠ e se servisse, **non** `XCURSOR_THEME`: Mutter non la legge, legge `org.gnome.desktop.interface cursor-theme` |
| KDE / KWin `--virtual` | **sì** `[M]` — niente piano cursore ⇒ dipinto nel framebuffer | `XCURSOR_THEME` (+ `XCURSOR_SIZE`, che KWin pretende) |
| wlroots — XFCE, LXQt | **sì, sempre** su headless; `overlay_cursor` non lo toglie, lo **forza software** | `XCURSOR_THEME`; su labwc `XCURSOR_SIZE` non è obbligatoria |

⛔ **La trappola, e va verificata invece che sperata**: su wlroots un tema che carica **zero**
cursori fa ripiegare la libreria su un tema **incorporato e visibile** — cioè due puntatori,
per un ripiego silenzioso (`REVIEWER.md` E2). Serve almeno un cursore valido, `index.theme`
**senza `Inherits=`**, e i dieci nomi che labwc chiede. E l'esito si **controlla dopo l'avvio
della sessione**: che il tema sia stato scritto non è che sia stato caricato.

*Il posto dove metterlo c'è già: l'ambiente della sessione si compone da zero, una variabile
per volta (`CODER.md` §4.5) — quindi la cura sta nel programma e non in un file, come vuole I7.*

### 5-bis.3 🔸 Il ventaglio dei gesti

I tre dell'utente più quattro che ne discendono per convenzione. Da confermare, i proposti.

| Gesto | Effetto | |
|---|---|---|
| 1 dito trascina | muove il puntatore | ✅ utente |
| 1 dito tap | clic sinistro | ✅ utente |
| 2 dita tap | clic destro | ✅ utente |
| 2 dita trascina | rotella / scorrimento | 🔸 proposto |
| tap-e-mezzo (tap, poi premi e trascina) | trascinamento e selezione | 🔸 proposto |
| 3 dita tap | clic centrale | 🔸 proposto |
| pizzico | ingrandisce la **vista** del client, non l'applicazione | 🔸 proposto |

⚠ Il *tap-e-mezzo* non è un lusso: senza, non si sposta una finestra e non si seleziona del
testo. Tap e trascinamento a due dita non si confondono — un tap è breve e fermo.

### 5-bis.4 🔸 Il canale del cursore, e il suo compromesso

Il client deve sapere **che forma** disegnare: barretta sul testo, doppia freccia sui bordi,
mano sui collegamenti. Serve quindi un canale che porti **forma e punto attivo** quando
cambiano.

Il compromesso, accettato: la **posizione** è immediata perché locale, la **forma** arriva con
un giro di rete di ritardo. Muovendo in fretta sopra un bordo, la doppia freccia compare un
attimo dopo. È il verso giusto del compromesso — il ritardo di una forma non lo nota nessuno,
quello di una posizione lo notano tutti.

### 5-bis.5 🔸 Che cosa porta il canale di input

| | |
|---|---|
| puntatore **assoluto** | sì — è il modo del trackpad di 5-bis.1 |
| puntatore **relativo** | sì — mouse veri via *Pointer Capture* di Android, che consegna delta e non posizioni |
| **scancode** | sì — tasti di controllo e tastiere fisiche |
| **Unicode** | sì, e su Android è la **strada principale** (vedi §7.10-bis) |
| **tocco multi-dito** | posto riservato, **non implementato** `[?]` |
| **stilo** (pressione, inclinazione) | fuori, per ora |

Il tocco nativo non entra perché non risolve la precisione, le applicazioni desktop lo
gestiscono male, e andrebbe verificato che l'EIS di Mutter e KWin espongano la capacità
«touch» — `libei` la prevede, che i due la offrano è `[?]`. Il **posto riservato** costa niente
adesso e fa risparmiare una riscrittura se un giorno servisse.

### 5-bis.6 ✅ Le lettere viaggiano come lettere, i tasti che non sono lettere come posizioni

*8 agosto 2026.*

| Che cosa | Come viaggia |
|---|---|
| lettere, numeri, segni — tutto ciò che si stampa | **come lettere** (carattere) |
| Invio, Tab, Esc, frecce, F1-F12, Ctrl, Alt, Maiusc, Super | **come posizioni** — non sono lettere, e stanno nello stesso posto su ogni tastiera |

**Il problema che questa scelta scioglie**, ed è quello che l'utente ha isolato da sé: una
tastiera fisica non manda lettere, manda **posizioni** — il tasto a destra della L dice «tasto
39», ed è il desktop a decidere se significa «ò» (disposizione italiana) o «;» (americana). Se
sul filo viaggiassero le posizioni, un client con tastiera americana attaccato a una sessione
italiana produrrebbe **le lettere sbagliate**: è il difetto classico di ogni desktop remoto.

Facendo viaggiare le lettere, la disposizione del *client* la applica il sistema del client, e
la nostra sessione non deve indovinare niente. Vale per **entrambi** i client, non solo per
Android — dove però è obbligatorio comunque, perché una tastiera Android non ha posizioni:
è un IME che produce testo.

⚠ **Resta la sola raggiungibilità.** Se nella disposizione della sessione un carattere non
esiste su nessun tasto — un'emoji, un alfabeto diverso — non esce **niente**, e il server lo
**dichiara nel registro**: mai una lettera diversa, mai un silenzio (`LEZIONI.md` §1.8).

**In dote**: i modificatori non sono mai stati il problema e si emulano normalmente (per «A»:
premi Maiusc, premi 30, rilascia 30, rilascia Maiusc); la ripetizione non è nostra (wlroots
scarta i tasti ripetuti, a ripetere è l'applicazione); e la disposizione dichiarata dal client
— la «questione n.7» di v1 — non serve più per *interpretare*, solo per *scegliere* (5-bis.7).

### 5-bis.7 ✅ La disposizione si rinegozia all'attacco e al riattacco, come la risoluzione

*8 agosto 2026. «Per le tastiere vale il discorso delle risoluzioni: alla creazione della
sessione o re-attach viene rinegoziata anche la tastiera».*

Stessa forma di §5.0 — il client dichiara, la sessione si adegua — ma **con due differenze che
giocano a favore**:

1. **non costa niente di visibile.** Cambiare la misura dello schermo rimescola le finestre
   dell'utente e su KWin < 6.8 non si può proprio; cambiare la disposizione non sposta nulla,
   non riavvia la cattura, non si vede;
2. **e se fallisse, la degradazione è morbida.** Grazie a 5-bis.6 una disposizione vecchia non
   produce mai caratteri sbagliati — al massimo rende irraggiungibili un paio di accenti. Una
   misura vecchia, invece, la si vede per tutta la sessione.

`[?]` **Da misurare, due cose, e nessuna è urgente:** se il cambio di disposizione a sessione
viva riesca su tutti e quattro i desktop (la nascita è certa, il cambio a caldo no); e se
convenga dare alla sessione **più disposizioni insieme** — il sistema ne accetta fino a quattro
— per coprire il caso di chi passa da un telefono italiano a un portatile americano, che
sospetto sia raro ma non l'ha misurato nessuno.

---

## 5-ter. Gli appunti

### 5-ter.1 ✅ Solo testo

*9 agosto 2026. «Per la clipboard ho idea precisa: solo testo».*

Niente immagini, niente file, niente formati ricchi. È anche quel che diceva `SPECIFICHE.md`
riga 28, qui confermato invece che ereditato.

**Perché è la scelta giusta e non una rinuncia**, scritto perché nessuno la riapra per
distrazione: il testo copre il 95 % degli usi, costa una manciata di byte, e non ha
negoziazione — una stringa è una stringa. Le immagini aprono invece una scatola intera:
quali formati, chi converte, e soprattutto **chi paga la banda** quando si copia una schermata
da 8 MB su un collegamento mobile che stiamo faticando a tenere a 480p (§3.1).

### 5-ter.2 🔸 Il codice c'è già, e copre tre desktop su quattro con un file solo

Fra le cose che sopravvivono alla morte di RDP, gli appunti sono le più intatte: muore solo il
canale RDP che li trasportava, non il modo di parlare col desktop.

| | Righe | Copre |
|---|---|---|
| `v1/remotix-c/src/appunti_wlr.c` | 796 | **KDE, XFCE e LXQt insieme** — stesso protocollo (`zwlr_data_control_manager_v1`), e `xfce.md` §8 lo dà per funzionante così com'è |
| `v1/remotix-c/src/appunti_mutter.c` | 450 | GNOME, che ha una via sua |

### 5-ter.3 🔸 Di chi sono gli appunti cambia per desktop, e una trappola è già disinnescata

`LEZIONI.md` §3, domanda 14 — *«la clipboard di chi è?»*:

| | |
|---|---|
| **GNOME** | della **sessione remota**: sta sull'oggetto RemoteDesktop, si accende con `EnableClipboard`, e senza sessione non esiste |
| **KDE, wlroots** | del **compositore**: nessun permesso, e c'è anche se REMOTIX non c'è |

⚠ **La trappola di GNOME, e perché non ci tocca più**: *«gnome-shell azzera la clipboard a ogni
blocco schermo: ci strappa la proprietà in silenzio»* (`gnome.md`). Con §4.3 — il blocco è
nostro e quello dei desktop resta spento — il caso non si presenta. **Ma torna il giorno in cui
qualcuno rimettesse il blocco del desktop**, ed è un'altra ragione per cui quella decisione va
riletta e non data per scontata.

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

### 6.3 ✅ Il server si scrive in C

*8 agosto 2026. «Confermo il C».*

⚠ **Non è un'eredità: è una decisione nuova che ripete la vecchia.** Il vincolo di v1
(`v1/documenti/SPECIFICA.md` §8-bis) aveva una ragione sola — *«gnome-remote-desktop smette di
essere un riferimento da cui trarre ispirazione e diventa un riferimento da cui trarre
codice»* — e **quella ragione è morta con RDP**: non c'è più niente da trapiantare, perché
nessuno ha scritto RCP prima di noi. La questione è stata riaperta a occhi aperti e richiusa
per un motivo diverso.

**Il motivo nuovo è il conto di §6.2**: circa 14.000 righe sopravvivono, con i loro banchi già
tarati. Il pezzo QUIC ne vale forse 2.000. Riscrivere quattordicimila righe misurate per
guadagnare l'ergonomia di duemila è uno scambio pessimo — ed è anche `LEZIONI.md` §10 in
azione, perché fra le cose che si butterebbero ci sono **4.563 righe di banchi**, e questo
progetto non è mai morto sul codice: è morto sulle misure.

**Che cosa questa decisione NON decide:** i client. Quello Android è Kotlin comunque, per via
di MediaCodec. Quello Linux è aperto — se sarà in C potrà condividere `librcp` col server, che
è un argomento a favore ma non una conclusione.

### 6.4 🔸 QUIC via `quiche`

Era l'unico argomento serio a favore di Rust, e si risolve con una libreria invece che con un
linguaggio: **`quiche`** di Cloudflare ha un'**API C**, licenza **BSD-2**, ed è in produzione
da anni. Si prende il QUIC finito senza cucire ngtcp2 a mano e senza toccare la libertà di
licenza (§7.6).

L'alternativa in C puro è `ngtcp2` (MIT), che però richiede di portarsi il TLS e montare più
pezzi. **Da confermare quando si aprirà il trasporto**, non prima: è il tipo di scelta che si
fa con un banco davanti, non su carta.

---

## 7. ❓ Le domande aperte

**Non sono decisioni.** Sono buchi, elencati perché non si perdano.

### 7.1 ~~La misura della tela alla nascita~~ → **chiusa l'8 agosto, vedi §5.0**
La detta il client a ogni attacco. Niente predefiniti, niente preferenze.

### 7.2 ~~Blocco schermo alla disconnessione~~ → **chiusa l'8 agosto, vedi §4.3**
Il blocco è di REMOTIX, non del desktop: 30 minuti senza input e il client viene staccato. Con
una condizione di scadenza scritta, da rileggere se arriverà un'autenticazione più forte.

### 7.3 ~~Il fantasma: subentro o attesa?~~ → **chiusa l'8 agosto, vedi §4.4**
Nessuna delle due: chi tace è staccato, e il posto non lo tiene nessuno. Il bivio non esiste
più. ⚠ Resta fuori, e non è stata chiesta, la terza possibilità — **due client sullo stesso
desktop insieme**: costerebbe poco con un palco persistente, ma cambia il protocollo e andrebbe
decisa prima di scriverlo, non dopo.

### 7.3-bis ❓ Dopo quanti secondi di silenzio un client è staccato?
Il primo dei tre orologi di §4.5, ed è l'unico senza un numero. Con QUIC il passaggio
WiFi → LTE **non** conta come silenzio — la connessione si porta dietro il cambio di indirizzo
— quindi la soglia deve coprire solo le interruzioni vere: la galleria, il telefono che si
spegne, la batteria che finisce.

### 7.4 Proporzioni: bande o allungamento?
Credo si risponda da sé — allungare deforma il testo e lo rende illeggibile — ma va detto.

⚠ **Il modello di §5.0 la rimpicciolisce parecchio**: siccome la tela nasce della forma del
client, all'attacco le proporzioni **combaciano sempre**. Il caso resta solo in due punti: il
ridimensionamento della finestra durante la sessione, e il ripiego di §5.0-bis su KDE vecchio.

### 7.5 ~~Il linguaggio del server~~ → **chiusa l'8 agosto, vedi §6.3**
C, confermato. Non per eredità: la ragione di v1 era FreeRDP ed è morta con RDP. La ragione
nuova è il conto del riuso, banchi compresi.

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

### 7.9 ~~La fiducia: chi autentica il server verso l'utente?~~ → **chiusa il 9 agosto, vedi §1.3**
Fiducia al primo incontro, ricordata in silenzio. Nessuna impronta da confrontare: il rischio
sulla prima connessione è stato valutato e accettato per lo scenario previsto.

### 7.10 ~~Il touch da Android~~ → **chiusa l'8 agosto, vedi §5-bis**
Era la questione aperta n.1 di v1, mai chiusa in un anno. Risposta: trackpad con puntatore
disegnato dal client; tocco nativo con il posto riservato ma non implementato.

### 7.10-bis ~~La tastiera di Android: Unicode o scancode?~~ → **chiusa l'8 agosto, vedi §5-bis.6 e §5-bis.7**
Tutt'e due, ma non come pari: le **lettere** viaggiano come lettere, e solo i tasti che lettere
non sono viaggiano come posizioni. E la domanda si è allargata da Android a entrambi i client.
Quel che segue è il ragionamento che ci ha portati lì, tenuto perché la conclusione da sola non
si capisce.
Il passeggero del touch, e pesa di più. *«Una tastiera Android non è una tastiera fisica: non
ha scancode, ha un IME che produce testo»* (`v1/documenti/client-android.md` §5.2). Il client
manda quindi **Unicode** per i caratteri stampabili e **scancode** per i tasti di controllo —
Invio, Tab, frecce, modificatori.

**Proposto: tutti e due, e l'Unicode non come ripiego ma come strada principale.** In dote
arriva la chiusura della questione n.7 di v1: la disposizione di tastiera dichiarata dal
client, su Android, **non serve** — quello che arriva è già il carattere finale.

Resta da confermare, ed è la parte che costa: la conversione da carattere a **posizione fisica
nella disposizione della sessione**, con i modificatori applicati intorno.

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
