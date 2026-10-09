# Fase 21 — La licenza

*Piano scritto l'**8 ottobre 2026** sera; ⭐ **riscritto il 9 ottobre** dopo la giornata di decisioni
sulla licenza (classe della chiave, upgrade, sito con area cliente e pannello, accessi, nomi `LICENSE_KEY` /
`INSTALL_KEY` / `HW_FINGERPRINT`). ⛔ **Da approvare dall'utente prima di qualunque lavoro.** ⏸ **Sospeso il 9 ott** (utente: *«per il momento sospendiamo qui il discorso
licenza. Attendiamo che finisca il lavoro di testing di remotix»*): si riprende da qui, con l'approvazione del piano. Le **regole** stanno in
`SPECIFICHE.md` §15 (si legge prima §15.0) e qui **non si ripetono**: questo documento dice **come** si fanno e in
che ordine. ⚠ Vincolo dell'utente (8 ott): **la licenza viene prima del banco xrdp** (`fasi/20-le-prestazioni.md`
§3 punto 4b).*

---

## 1. Che cosa si costruisce, in una riga per parte

| parte | che cosa fa | dove gira | linguaggio |
|---|---|---|---|
| **1. il prodotto** | prende la `LICENSE_KEY` dall'installatore, crea la `INSTALL_KEY`, controlla ogni ora, mostra lo stato, si ferma alla fine; il comando `remotix licenza` | sul server del cliente | C, come il prodotto; l'installatore in Go |
| **2. il servizio di licenze** | le operazioni A, C, E di §3.3: attivazioni, controlli col biglietto, sdoppiamenti, email, l'orologio | sul **VPS**, `remotix.nicfio.it/licenze/v1/` | Go (§3.1) |
| **3. il sito** | la vetrina pubblica, la richiesta delle chiavi, l'**area cliente** e il **pannello** di chi vende (§4, §4-bis) | sul VPS: pagine fisse servite da Caddy, le parti vive dal servizio | HTML/CSS dai mockup; Go |
| **4. la funzione della gold** | crea le gold, fuori dal pannello | sul VPS, un comando, solo via ssh | Go, nello stesso binario |
| **5. l'ingresso del pagamento** | «rinnova» · «sospendi» · «riattiva» · «nuova full venduta» | sul VPS, nel servizio | Go |

## 2. Parte 1 — il prodotto

### 2.1 Dove si innesta, letto nel codice

*`[R]` 8 ott; righe da rileggere prima di scrivere, il codice si muove.*

| che cosa | dove sta oggi | che cosa cambia |
|---|---|---|
| **l'accesso** | `src/autenticazione.c:212` `rcp_autentica()` (PAM), chiamata **solo dal nipote** dell'aiutante (`src/aiutante.c:23-30`); l'esito torna al filo in `src/rcp.c:~2490-2515` | **dopo** credenziali giuste il filo guarda lo stato della licenza **in memoria**: niente rete in quel punto |
| **i rifiuti** | i motivi di `CONGEDO` in `src/rcp.h:113-133` (`0x01`…`0x10`), le frasi in `src/pagina.html:896-999` | un motivo nuovo, prima in `RCP.md`: **`0x11 LICENZA`**, con lo stato (scaduta, bloccata per due copie, sospesa, revocata, mai attivata) che sceglie la frase. ⛔ Niente più `0x12` «un utente»: la trial ha utenti illimitati |
| **la pagina d'accesso** | il modulo in `src/pagina.html:600-625`; i segni in `src/pagina.c:420-433` | un segno `__LICENZA__` (stato e giorni, **innocuo**: prima delle credenziali si vede solo «Trial version — N days left»); gli stati di `SPECIFICHE.md` §15.10; gli **avvisi con «ho letto»** dei giorni lavorativi prima della scadenza; il **nome breve della copia**. ⛔ **Nessun campo per la chiave**: la mette root (§15.3 punto 7) |
| **la memoria della licenza** | `/var/lib/remotix/` (`src/main.c:1768-1770`) | `/var/lib/remotix/licenza/`: la `INSTALL_KEY` (solo root), l'attestato, il biglietto, la richiesta in volo, l'ora più recente vista |
| **il tetto delle sessioni** | `--tetto-sessioni N` (`src/main.c:2084`), predefinito 10 | ⛔ **la licenza non lo tocca**: nessuna licenza conta gli utenti |

### 2.2 Il messaggero: la rete fuori dal filo

⛔ Il server è **un filo solo**: una domanda in rete con un proxy lento fermerebbe tutte le sessioni. ⇒ Un
**processo a parte**, figlio del padre come l'aiutante, che ogni **ora** (e a «controlla ora»):
- scrive la richiesta **su disco prima di spedirla** e, senza risposta, la rispedisce **identica** (§15.4);
- firma la sfida con la `INSTALL_KEY` e presenta il biglietto; manda la descrizione della macchina (§15.12);
- passa dal **proxy** (`https_proxy`, o un'opzione in `REMOTIX_OPZIONI`);
- verifica l'attestato (chiave del VPS certificata dalla radice, §6) e al filo manda solo lo stato.

**HTTPS:** ⭐ **libcurl** (proxy `CONNECT`, certificati di sistema, licenza compatibile); ⚠ dipendenza nuova del
pacchetto.

### 2.3 Il comando `remotix licenza` e l'installatore

- **L'installatore** (`installatore/`, Go: CLI, TUI, GUI) chiede la **`LICENSE_KEY`** e mostra a chi non ce l'ha
  l'indirizzo del sito; senza domande: `--license-key`. La passa al prodotto; se la rete manca, l'installazione
  finisce e dice di lanciare `remotix licenza attiva` dopo.
- **`remotix licenza`**, da root: `stato` · `attiva <chiave>` · `upgrade <chiave>` · `controlla` · `recupera`.
  Parla col messaggero, non col VPS direttamente.

## 3. Parte 2 — il servizio di licenze sul VPS

### 3.1 Il linguaggio: Go

- ⭐ **l'installatore è già in Go** (`installatore/go.mod`: `go 1.25`, con `vendor/`): stesso contenitore di
  costruzione, stessa catena, un binario statico solo da copiare sul VPS;
- la libreria standard ha già tutto quello che serve: `net/http` con TLS, `crypto/ed25519`, `encoding/json`;
- ⛔ niente framework: un binario, un'unità systemd, un file di configurazione.

### 3.2 La base dati

⭐ **SQLite** in un file solo (`modernc.org/sqlite`, Go puro, BSD: il binario resta statico), operazioni a
transazione, copia cifrata fuori dal VPS ogni giorno (§15.11).

| tabella | che cosa tiene |
|---|---|
| `licenze` | numero `RX-…`, classe (trial/full/gold), acquirente, inizio, scadenza, stato, rinnovo automatico, riferimento del pagamento |
| `chiavi` | l'**impronta cifrata** di ogni `LICENSE_KEY` emessa, la classe, usata sì/no, quando scade se mai usata (30 giorni la trial) — per sempre |
| `installazioni` | la parte pubblica della `INSTALL_KEY`, la licenza, il biglietto in corso, l'ultima risposta (per ridarla uguale), nome breve, ultima descrizione della macchina |
| `trial_impronte` | ogni `HW_FINGERPRINT` (cifrata) che ha già avuto la trial, con la sua data di fine |
| `sdoppiamenti` | scoperta, copie, RDAP, scelta o blocco, avvisi mandati |
| `clienti`, `sessioni` | l'area cliente: email, accesso Google, link usa-e-getta |
| `registro` | ogni operazione del pannello, del pagamento, della gold e dell'orologio: chi, quando, che cosa |

### 3.3 Le operazioni del servizio

*Riscritta il **9 ottobre 2026** sera, su richiesta dell'utente (*«prima definiamo le operazioni che deve svolgere
il server e poi definiamo l'interfaccia web»*): ⛔ supera la tabella dell'8 ott (`machine-id`, «avvii», controllo
ogni N ore). Le regole stanno in `SPECIFICHE.md` §15 e qui non si ripetono: ogni riga rimanda. ⏳ **Da approvare**:
le righe 🔸 sono proposte di Claude, nate dai buchi che §15 lascia.*

**A. Il prodotto** (il server del cliente; ogni domanda è firmata con la `INSTALL_KEY`)

| # | operazione | che cosa fa | §15 |
|---|---|---|---|
| A1 | **attiva con la chiave** | la classe della chiave decide la licenza (trial, full, gold); consuma la chiave (una volta, per sempre), lega la licenza alla `INSTALL_KEY`, dà attestato e primo biglietto; per la trial controlla anche l'impronta: già avuta ⇒ **stessa** data di fine, vuota ⇒ «scrivici» | 15.3, 15.7 |
| A2 | **upgrade** | su un'installazione attiva consuma una chiave di classe più alta (scala ✅ trial → full → gold); stessa `INSTALL_KEY`, l'anno parte da qui | 15.3 |
| A3 | **controlla** (ogni ora, e «controlla ora») | consuma il biglietto e ne dà uno nuovo con l'attestato; ridà **la stessa risposta** a una richiesta identica; scopre lo sdoppiamento; dice lo stato (valida, in tolleranza, sospesa, revocata, bloccata, gold doppia) | 15.4, 15.8 |
| A4 | **stato della copia indietro** | risponde senza consumare biglietti | 15.9 |
| A5 | **rilascia** | la vecchia installazione firma il rilascio per lo spostamento volontario | 15.9 |
| A6 | **chiedi il recupero** | numero di licenza + `INSTALL_KEY` nuova ⇒ email di conferma all'acquirente; rispetta «uno ogni 30 giorni» | 15.9 |
| A7 | **dammi l'elenco firmato** | indirizzi, chiavi valide e revoche, firmati dalla chiave madre | 15.11 |
| A8 | **descrivi la macchina** | dentro A1-A3: descrizione dell'hardware, IP interni, nome; il servizio tiene solo l'ultima | 15.8, 15.12 |

**B. L'acquirente** (pagine aperte da un link nell'email: la pagina **mostra**, il pulsante **conferma**)

| # | operazione | §15 |
|---|---|---|
| B0 | **chiedi una chiave trial**: email (obbligatoria), nome e azienda (facoltativi), ✅ utente 9 ott ⇒ la chiave arriva per email (🔸 e così l'email è confermata, senza link a parte). ✅ **Solo dal sito** del servizio (utente, 9 ott); l'installatore chiede solo la `LICENSE_KEY` | 15.7 |
| B1 | **compra una full**: dalla pagina del servizio (`remotix.nicfio.it`, «Acquista»); chi compra può non essere l'amministratore. ⏳ I dati dipendono dal processore. Finché non c'è, la crea chi vende (D1) | 15.3 |
| B2 | **scegli la copia** fra le due attive; la tenuta riceve una `INSTALL_KEY` nuova, l'altra si ferma; sblocca anche una licenza già bloccata | 15.8 |
| B3 | **conferma il recupero** | 15.9 |
| B4 | **rinnovo automatico sì/no** — 🔸 lo tiene il processore di pagamento, qui solo il collegamento; ⏳ dipende dal processore | 15.6 |

**C. Il pagamento** (con la sua chiave segreta)

| # | operazione | §15 |
|---|---|---|
| C1 | **rinnova** la licenza N di un anno (sblocca anche una scaduta in tolleranza o ferma) | 15.6 |
| C2 | **sospendi** · 🔸 **riattiva** (un addebito respinto e poi pagato) | 15.10 |
| C3 | 🔸 **nuova full venduta** ⇒ come D1, con l'email al compratore | 15.3 |

**D. Chi vende** (il pannello web; ogni operazione finisce nel registro con chi, quando, perché)

| # | operazione | §15 |
|---|---|---|
| D1 | **crea una full**: email dell'acquirente, nota ⇒ numero `RX-…` e chiave, email al compratore | 15.1, 15.3 |
| D2 | ⛔ **non dal pannello**: la gold si crea con una **funzione dedicata** del servizio (✅ utente, 9 ott: *«le licenze gold vengono rilasciate tramite una funzione dedicata del server delle licenze. Non seguono una strada normale»*). 🔸 Un comando sul VPS, raggiungibile solo via ssh con la chiave del portatile: chi viola il pannello non crea gold. Nota («scatola 3») ⇒ numero e chiave | 15.1 |
| D3 | **dai una chiave trial a mano** (la macchina senza impronta, o chi ha bisogno di più giorni) | 15.7 |
| D4 | **rinnova a mano** (pagamento fuori processore, finché il processore non c'è) | 15.6 |
| D5 | **sospendi · riattiva · revoca** | 15.1, 15.10 |
| D6 | **gold doppia**: guarda le due copie, **disabilita una** | 15.1 |
| D7 | **licenza bloccata da 15 giorni lavorativi**: **sblocca** o **cancella definitivamente** | 15.8 |
| D8 | **3 sdoppiamenti in 90 giorni**: guarda, **revoca** o lascia | 15.8 |
| D9 | **sblocca il limite dei 30 giorni** (scambio o recupero) | 15.8, 15.9 |
| D10 | 🔸 **chiave persa prima dell'uso**: annulla la vecchia e ne emette una nuova (le chiavi non si conservano in chiaro, quindi non si possono rimandare) | 15.3 |
| D11 | 🔸 **cambia l'email dell'acquirente** quando il cliente non ha più accesso alla vecchia (di norma lo fa lui dall'area cliente), con avviso al vecchio indirizzo | — |
| D12 | **guarda**: elenco e ricerca (numero, email, stato, ultimo contatto), la storia di una licenza, le copie, il registro | — |
| D13 | 🔸 **la cassetta «da decidere»**: D6, D7, D8 e le trial «scrivici» in un posto solo, così niente aspetta in silenzio | — |

⛔ **Fuori dal pannello**: tutto quel che firma la **chiave madre** (certificare la chiave del VPS, l'elenco firmato
delle revoche, §15.11). Resta un comando sul portatile: se il pannello venisse violato, la radice non c'è.

**E. L'orologio del servizio** (da solo, ogni ora)

| # | operazione | §15 |
|---|---|---|
| E1 | le email della scadenza: 3°, 2° e ultimo giorno lavorativo prima (l'ultimo alle 11 e alle 16), poi una al giorno alle 11 nella tolleranza; si fermano al rinnovo | 15.6 |
| E2 | l'avviso 7 giorni prima dell'addebito automatico | 15.6 |
| E3 | sdoppiamenti: un'email al giorno per 7 giorni lavorativi, poi **blocco**; a 15 giorni lavorativi la licenza va nella cassetta di chi vende | 15.8 |
| E4 | i link (scelta, recupero) e le chiavi trial mai usate (30 giorni) scadono | 15.8 |
| E5 | le cancellazioni: sdoppiamenti a 6 mesi, il resto a 2 anni | 15.12 |
| E6 | la copia cifrata fuori dal VPS, ogni giorno | 15.11 |

## 4. Parte 3 — il pannello di chi vende

✅ **9 ott, utente: un'interfaccia web**, parte riservata del sito (§4-bis). Le operazioni sono la sezione D di
§3.3, la gold esclusa (funzione dedicata via ssh). ✅ Mockup `grafica/sito-mockup/console.html`.

## 4-bis. Il sito `remotix.nicfio.it`

✅ **9 ott, utente**: *«remotix.nicfio.it sarà anche la landing page del progetto, aperto al pubblico e dove si
"pubblicizza" il prodotto, in modo simile ad esempio a phonestra. Bisogna prevedere delle sotto-sezioni riservate»*.

🔸 **Come si monta**, sullo stesso VPS e con lo stesso schema dei siti che ci sono già (`~/Documenti/VPS`: Caddy,
file statici in `/srv/www/<sito>`, HTTPS da Let's Encrypt, l'utente `progetti` che pubblica):
- le **pagine pubbliche** sono **file statici**, come phonestra: niente CMS, niente da violare;
- tutto quel che è dinamico è **il servizio in Go**, dietro Caddy, sotto percorsi suoi.

| sezione | per chi | che cosa c'è | accesso |
|---|---|---|---|
| **pubblica** | tutti | il prodotto, le prestazioni, i prezzi, i documenti, **«Prova gratis»** e **«Acquista»** (B0, B1) | libero |
| `/licenze/v1/` | il server del cliente | le domande A1-A8; non è una pagina | firme (`INSTALL_KEY`) |
| ✅ **area cliente** (utente, 9 ott: *«prevedere un'area cliente ci semplifica parecchie cose»*) | chi ha comprato o chiesto una trial | le sue licenze: numero, classe, stato, scadenza, copie attive; **scelta della copia** (B2); **conferma del recupero** (B3); rinnova; rinnovo automatico sì/no (B4); cambio email (D11 diventa sua) | ✅ (utente, 9 ott) **link all'email, senza password**, che vale sempre: si scrive l'email, arriva un link che vale una volta e per poco, e apre l'area per qualche ora; più **«Accedi con Google»** come scorciatoia (l'email arriva già verificata). ⛔ Niente password, niente Facebook; Microsoft per ora no (dubbio dell'utente), si può aggiungere dopo. Le email della scelta e del recupero portano **qui**, non a pagine a parte |
| **pannello** | chi vende | le operazioni D1-D13 (non la gold, D2) | ✅ **passkey oppure «Accedi con Google»** (utente, 9 ott: *«passkey e/o google»*). 🔸 Le condizioni: Google vale **solo per l'account di chi vende**, scritto nella configurazione, e quell'account deve avere la **verifica in due passaggi**; ogni operazione che crea, rinnova, revoca o cancella manda **subito un avviso a chi vende** (se non l'ha fatta lui, lo sa in un minuto); se si perde l'accesso, un comando via **ssh** sul VPS dà un link per registrare una passkey nuova. ⚠ Con due porte il pannello è forte quanto la più debole: l'account Google |

✅ **Tutto il sito è in inglese, pannello compreso** (utente, 9 ott). Mockup in `grafica/sito-mockup/`. ✅ Visti e approvati per ora
la pagina d'accesso e l'area cliente (utente, 9 ott: *«semplice, elegante e senza fronzoli … al momento mi sembrano ok»*).

🔸 **Due parti riservate, costruite insieme e tenute separate** (utente, 9 ott: *«ci sono due versioni della parte
riservata: quella dei clienti registrati e quella mia»*): **le pagine sono le stesse** (la scheda di una licenza, la
sua storia, le copie), e il pannello ci aggiunge i pulsanti di chi vende; ma **ingresso, sessione e controllo dei
permessi sono separati** (indirizzo suo, accesso suo). ⇒ Meno lavoro, e un errore nell'area cliente non apre il
pannello.

## 5. Parte 4 — l'ingresso del pagamento

Due domande generiche, `rinnova` e `sospendi`, con il riferimento della licenza. ⛔ **Nessun processore scelto**
(§10.30: in sospeso): quando si sceglierà (Polar/Paddle o Stripe), si scrive solo il **traduttore** dai suoi
avvisi a queste due domande. Il prodotto non cambia.

## 6. Le chiavi, e dove stanno

⭐ Proposta di §10.30 (8 ott): **radice fuori linea, chiave del VPS certificata**.

| chiave | dove sta | che cosa firma |
|---|---|---|
| **radice** ed25519 | ⛔ **mai sul VPS**: sul portatile, in `.chiavi/` (ignorata da git, come D10 dell'installatore, `fasi/17-l-installatore.md` D10) + copia di riserva fuori dal computer | solo i **certificati** delle chiavi del VPS, con scadenza; e le revoche |
| **chiave del VPS** ed25519 | sul VPS | gli attestati |
| la pubblica della radice | **dentro il prodotto**, scritta alla costruzione | — |

- ⭐ **Il modello c'è già, nel deposito**: la «catena A» dell'installatore — radice ed25519 fuori linea che
  certifica sottochiavi con scadenza, revoche firmate dalla radice (commit `6773a66`: `installatore/motore/firma.go`,
  `installatore/strumenti/chiavi-a/main.go`). È stata **tolta** il 30 set con D11 (`6612256`) perché
  all'installatore bastava la chiave dell'archivio; qui serve davvero. Si riprende da lì, in Go per lo strumento
  e il VPS; nel prodotto la verifica è in C (OpenSSL).
- ⚠ Se il VPS viene violato: si revoca la sua chiave e se ne certifica una nuova, **senza ricompilare il prodotto**.
  Se si perde la **radice**, invece, serve una versione nuova del prodotto: va custodita con la copia di riserva.
- ⚠ **Chiavi DI PROVA e chiavi vere**: come l'installatore, si costruisce con la pubblica di prova per i banchi
  e con quella vera solo nel comando di rilascio. Un pacchetto con la chiave di prova **non deve uscire**: il
  comando di rilascio lo controlla.

## 7. Come si prova, senza VPS vero

- ⭐ **Il servizio finto è il servizio vero**, in un contenitore podman sul portatile, con chiavi di prova, un
  **orologio spostabile** (14 giorni in un minuto) e una **posta finta** che raccoglie le email per guardarle.
- **Il prodotto lo trova** con un'opzione (`--licenze-url`), che il pacchetto non mette mai.
- **I casi**: trial nuova · trial già data alla stessa impronta (stessa fine) · impronta vuota («scrivici») ·
  chiave usata due volte · upgrade trial → full → gold · scadenza, avvisi, tolleranza, fine con i desktop vivi ·
  rinnovo dal «pagamento» · VPS spento dentro e oltre i 14 giorni · proxy (squid in un contenitore) · guasto a metà
  controllo (mai un falso clone) · clone con scelta, senza scelta (blocco a 7 giorni lavorativi) e a 15 · gold
  doppia · recupero · VPS tornato a un salvataggio vecchio · chiave del VPS revocata · orologio della macchina
  indietro · area cliente e pannello nel browser (Marionette, come i banchi della pagina).
- ⚠ **I banchi di oggi** prendono una **gold di prova** dal servizio finto, come ogni cliente.

## 8. I passi, in ordine

*Rifatta il **9 ottobre 2026** sera (la stima del mattino era ~122 ore). Entrano: il sito (vetrina, area cliente,
pannello, accessi con link all'email, Google e passkey), la funzione della gold, l'upgrade, l'installatore che
chiede la chiave, il comando `remotix licenza`. Escono: il campo della chiave nella pagina, il link di conferma
della trial (la chiave per email conferma l'indirizzo), il limite di un utente.*

| # | passo | ore |
|---|---|---|
| 0 | `RCP.md`: `0x11 LICENZA` e i messaggi della licenza | 1 |
| 1 | **le chiavi**: radice fuori linea, chiave del VPS di prova, l'elenco firmato (indirizzi, chiavi, revoche), dalla catena A | 6 |
| 2 | **il formato dei messaggi**: binario a lunghezze fisse, firmato; esempi comuni C/Go; fuzzing dei due lettori | 6 |
| 3 | **il servizio** (Go): A1-A8 (attivazione per classe, upgrade, biglietto con consumo atomico e risposta ripetibile, recupero, rilascio), le impronte della trial, gli sdoppiamenti coi nomi brevi e RDAP, l'orologio E1-E6, il ritorno a un salvataggio vecchio | 32 |
| 4 | **la posta dal VPS**: Postfix in uscita, SPF/DKIM/DMARC, PTR, i testi in inglese, prove verso Gmail/Microsoft/Yahoo | 6 |
| 5 | **il sito pubblico**: le pagine fisse dai mockup, i testi, la richiesta della chiave (B0) | 8 |
| 6 | **l'area cliente**: link all'email, «Accedi con Google», la scheda della licenza, scelta della copia, recupero, rinnovo automatico, cambio email | 14 |
| 7 | **il pannello**: passkey e Google (solo il tuo account), D1-D13, la cassetta «da decidere», l'avviso a ogni operazione, la registrazione via ssh | 14 |
| 8 | **la funzione della gold** (comando via ssh) e **l'ingresso del pagamento** (rinnova, sospendi, riattiva, nuova full) | 4 |
| 9 | **il prodotto, il messaggero** (processo a parte, libcurl, proxy, richiesta su disco, biglietto, ora fidata, `HW_FINGERPRINT` con le scritte di fabbrica scartate, descrizione della macchina) | 16 |
| 10 | **il prodotto, l'accesso e il comando** `remotix licenza`: stati, fine con i desktop vivi, copia rimasta indietro | 10 |
| 11 | **la pagina d'accesso**: gli stati di §15.10, gli avvisi con «ho letto», il nome breve della copia | 8 |
| 12 | **l'installatore**: la `LICENSE_KEY` in CLI, TUI e GUI, `--license-key`, il caso senza rete | 5 |
| 13 | **i banchi** (§7) e la suite corta con la gold di prova | 16 |
| 14 | **pacchetti**: libcurl nelle tre famiglie, la chiave vera solo nel comando di rilascio | 4 |
| 15 | **il VPS vero**: Caddy col sito, il servizio, l'unità, la posta, le copie cifrate fuori | 6 |
| 16 | `SPECIFICHE.md`, `DECISIONI.md` §10.30, la **bozza dell'informativa** (da far controllare a un legale) | 5 |
| | **totale** | **~161 ore ≈ 20 giorni di lavoro** |

⚠ La stima è di chi non ha ancora scritto una riga: il servizio (3), il messaggero (9) e l'area cliente col
pannello (6, 7) sono i punti dove la storia del progetto dice che si sbaglia per difetto. ⚠ Il passo 4 dipende da
OVH (porta 25, PTR). ⚠ «Accedi con Google» chiede di registrare REMOTIX presso Google (un'ora, account di chi vende).

## 9. Che cosa resta fuori

- **il pagamento vero** (processore, IVA, fatture): in sospeso per decisione dell'utente (§10.30);
- **il contratto di vendita** della full: è una domanda (§10 domanda 3);
- **la prova di capacità per il cliente** (§10.30, il programma accanto al server): è un lavoro suo, non della
  licenza; si fa dopo;
- ~~un **pannello web** per chi vende~~ ⛔ rientrato il 9 ott su richiesta dell'utente (§4);
- **la documentazione tecnica** (con la guida al dimensionamento e la tabella delle prestazioni, `fasi/20` §5): il
  sito ci rimanda, ma si scrive a parte;
- «Accedi con Microsoft»: dubbio dell'utente, si aggiunge dopo se serve;
- difese contro chi modifica il binario: §10.30 lo dichiara, la licenza tiene onesti gli onesti.

## 10. Domande per l'utente, una per volta

*⚠ Storia (8-9 ott): le risposte sono confluite in `SPECIFICHE.md` §15, che vale sopra questa sezione.*

1. **La tolleranza se la rete manca**: quanti giorni il server continua a far entrare senza riuscire a parlare
   col VPS? (⚠ Va più lunga del tempo per rimettere in piedi il VPS, §10.30; e ogni quante ore si ricontrolla.)
   ✅ **8 ott: 14 giorni, controllo ogni 24 ore** (utente: *«ok 14 giorni»*, dopo aver proposto 3). Il confronto
   che l'ha deciso: Microsoft 365 30 giorni, Adobe annuale 99, KMS 180 — la tolleranza protegge il cliente dai
   guasti **nostri**, e 3 giorni avrebbero bloccato tutti i clienti insieme dopo un fine settimana col VPS giù.
   L'attestato vale quindi «ultimo contatto riuscito + 14 giorni». ⭐ Con un **avviso all'amministratore dal primo
   controllo fallito** (pagina d'accesso e registro), con i giorni che restano.
2. **La tolleranza a rinnovo mancato**: quanti giorni dopo la scadenza della full, prima della finestra «abbonamento
   scaduto, rinnova» (§10.30, ancora 🔸 da confermare)?
   ✅ **8 ott: 14 giorni** (utente: *«ok 14 giorni»*), con l'avviso sulla pagina d'accesso **da 7 giorni prima
   della scadenza**. Un rinnovo che fallisce è quasi sempre una carta scaduta o rifiutata, e i processori
   ritentano da soli per una-due settimane: non si ferma chi sta solo cambiando carta.
3. **Il contratto di vendita** della full: quale testo (§10.30: per la trial c'è PolyForm Free Trial, per la full
   nessun testo standard)?
   ⏳ **8 ott: sospesa** (utente), insieme al pagamento: chi incassa decide che cosa resta da scrivere (Polar o
   Paddle vendono loro e hanno le loro condizioni d'acquisto, a noi resta la licenza d'uso; con Stripe il
   venditore siamo noi). ⛔ Non blocca il lavoro: la vendita aspetta comunque il pagamento.
4. **Il VPS**: fornitore, sistema operativo, **dominio** con cui i clienti lo raggiungono (serve al certificato
   HTTPS e va scritto nel prodotto), chi ha l'accesso.
   - ✅ **fornitore: OVH** (utente, 8 ott). ⚠ La base dati delle licenze è l'unica cosa che non si ricostruisce
     (chi ha pagato, quali macchine): va salvata **fuori dal VPS**, ogni giorno — il caso da coprire è quello
     di Strasburgo (incendio del centro OVH, marzo 2021: chi aveva le copie nello stesso centro le ha perse).
   - ✅ **sistema: Debian 13 «trixie»** (utente, 8 ott): lo stesso del server di prova e del portatile ⇒ il
     servizio finto in contenitore (§7) si costruisce sulla stessa base, e quello che passa lì vale sul VPS.
   - ✅ **indirizzo: `remotix.nicfio.it`** (utente, 8 ott: *«al momento appoggiamoci a remotix.nicfio.it»*), il
     servizio di licenze sotto un percorso con la versione (`https://remotix.nicfio.it/licenze/v1/…`), così lo
     stesso nome può servire più tardi anche l'archivio dei pacchetti. ⚠ Un dominio dedicato era la proposta di
     Claude (il nome è scritto nel prodotto, i firewall delle aziende lo autorizzano per nome, lega il prodotto
     al nome personale); `remotix.com` è già registrato, `.it`/`.eu` da verificare.
     ⭐ **Obbligatorio nel piano, per questa scelta: il cambio d'indirizzo firmato.** Il servizio può dire al
     prodotto, dentro l'attestato firmato, «da ora in poi chiedi a X»; il prodotto lo ricorda in `/var/lib/remotix`
     e ci passa. Un dominio nuovo domani = tenere acceso il vecchio qualche mese, nessun cliente da aggiornare.
   - ✅ **accesso: ssh** (utente, 8 ott). Le credenziali in `~/VPS.ssh`, stesso formato di `~/SERVER.ssh`
     (righe «chiave: valore»), ⛔ mai nel deposito. Il VPS si tocca solo al passo dell'installazione del
     servizio, dopo le prove sul servizio finto.
5. **Le sessioni aperte quando la licenza scade**: restano fino all'uscita (proposta) o si chiudono?
   ✅ **8 ott, deciso con l'utente** (idea sua, presa da RootSpeak; le due correzioni di Claude accettate: *«ok»*):
   - ⭐ **si disabilita solo REMOTIX, mai l'accesso al server** (ssh, login locale, PAM del sistema restano
     intatti): il server è del cliente, l'amministratore che deve rinnovare non va chiuso fuori, e un blocco
     nato da un guasto nostro (VPS giù) non deve fermare macchine altrui;
   - **alla scadenza** (= fine della tolleranza, non la data dell'abbonamento) si chiudono i **collegamenti**,
     i **desktop restano vivi** col lavoro dentro; al ricollegamento la finestra della licenza; dopo il
     rinnovo ognuno rientra e trova tutto com'era. Nessuno perde lavoro, nessuno continua senza licenza;
   - **gli avvisi prima**, col comportamento di RootSpeak (insiste, «ho letto», non blocca mai) ma **mostrati
     nella pagina di REMOTIX** sopra il desktop, non con `zenity`: la pagina la guardano tutti, è uguale sui
     quattro desktop (niente eccezioni per compositore), e RootSpeak resta un prodotto gratuito a sé;

     | quando | chi | cosa |
     |---|---|---|
     | da 7 giorni prima | l'amministratore | registro e pagina d'accesso: è lui che rinnova |
     | ultimi 3 giorni | tutti gli utenti collegati | **3 messaggi nelle 24 ore**, con «ho letto» |
     | alla scadenza | tutti | collegamenti chiusi, desktop vivi, finestra della licenza al ritorno |

   - **Il codice di RootSpeak si riusa** (utente: *«il codice è mio e lo puoi riutilizzare»*; è suo, quindi
     entra in un prodotto chiuso senza vincoli): `src/text.c` `clean_text` (pulizia del testo dai caratteri
     di controllo), il modello dei tre stati e dei rinvii (inviato, consegnato, confermato; promemoria a
     intervalli) e il registro degli eventi (`src/event.c`). ⚠ **Non** si riusa la consegna (terminali,
     `zenity`, agganci della shell): da noi il canale è la pagina. Il codice preso si traduce ai nomi e alle
     convenzioni di REMOTIX (italiano), con la provenienza scritta in testa al file.
6. **Il clone scoperto**: si avvisa solo chi vende, o si sospende la seconda copia da sola?
   ⏳ **8 ott sera, IN SOSPESO: l'utente ci pensa** (*«qui serve del tempo per pensarci su un attimo»*). Dove
   eravamo arrivati:
   - ⛔ **scartato dall'utente**: «il primo che attiva tiene il posto» (posto vivo, battito ogni 15 min,
     rilascio dopo un'ora) — *«eliminiamo il discorso della data di attivazione, e restiamo sul server fisico»*;
   - ⭐ **la direzione dell'utente**: legarsi al **server fisico**, ispirandosi a Microsoft e migliorandolo;
   - 🔸 **la proposta di Claude, da approvare**: impronta a 5 componenti (`product_uuid`, seriale della scheda
     madre, modello del processore, seriale del disco di sistema, scheda di rete principale), valida con
     **3 su 5** e aggiornata da sola quando un pezzo cambia; **spostamento dalla pagina d'accesso** senza
     account né email (la vecchia si libera all'istante, 1 ogni 30 giorni); al VPS **solo le impronte
     cifrate**, mai i seriali; messaggio che dice **quale** componente è cambiato;
   - ⚠ **il limite dichiarato**: sulle macchine virtuali il ferro è finto e si copia col clone (anche Microsoft
     lì usa altro). Due strade: **(a)** accettarlo e dichiararlo; **(b)** consigliata da Claude: col controllo
     di 24 ore già deciso, due copie vive con la stessa impronta ⇒ **solo un avviso a chi vende**, nessun blocco.
   ⚠ Se si sceglie l'impronta, `/etc/machine-id` da solo (§10.30) non basta più e va riscritto §10.30.
   - 🔸 **8 ott sera, lo schema portato dall'utente**: all'attivazione l'installazione **genera una coppia di
     chiavi**, il servizio lega la licenza alla **chiave pubblica** e rende un attestato firmato (prodotto, tipo,
     scadenza, installazioni massime, identificativo dell'installazione, funzioni); a ogni contatto
     l'installazione **dimostra di avere la chiave privata**. Giudizio di Claude: ✅ regge ed è una base migliore
     dell'impronta (prova crittografica invece di valori dichiarati, niente seriali al VPS, nessun falso
     allarme se cambia un disco); ⚠ ma **da sola non ferma i cloni**: la chiave privata è un file e si copia col
     disco. ⇒ **controproposta: la chiave privata nasce DENTRO il TPM 2.0** e non ne può uscire; un disco
     copiato su un altro computer non la porta con sé. Letto l'8 ott: `/sys/class/tpm/tpm0`, versione **2**, sia
     sul portatile sia sul server di prova. ⚠ Limiti: senza TPM (molti VPS, macchine vecchie) si ricade su
     chiave in un file + impronta 3/5; un TPM azzerato (BIOS, cambio di scheda madre) = installazione nuova
     ⇒ lo spostamento dalla pagina d'accesso serve anche qui; un TPM virtuale può essere copiato col clone
     della macchina virtuale ⇒ resta l'avviso (b).
7. **Che cosa compra la full oltre a utenti e durata**: gli aggiornamenti sono compresi finché l'abbonamento è
   attivo, e dopo la scadenza il prodotto si aggiorna ancora?
   ✅ **9 ott** (utente: *«una licenza full scaduta si comporta come una trial, semplicemente il sistema smette di
   funzionare»*): finita la tolleranza di 14 giorni, la full scaduta **si ferma** come la trial; la domanda sugli
   aggiornamenti dopo la scadenza non si pone. Aggiornamenti compresi finché la full è attiva.
   - **Avvisi prima della scadenza anche per la trial** (utente), come la full: amministratore da 3 giorni prima
     (la trial ne dura 14), utenti collegati 3 messaggi al giorno negli ultimi 3 giorni, nella pagina.
   - ✅ **Il controllo ogni 60 minuti, non ogni 24 ore** (utente). ⭐ Migliora: uno sdoppiamento si scopre entro
     un'ora e le 72 ore della scelta partono prima; lo stato di una licenza revocata o rinnovata arriva subito.
     Costo trascurabile: 1000 clienti = 24 mila controlli al giorno, un piccolo VPS li regge. ⚠ Due regole che
     ne vengono: la **tolleranza resta 14 giorni dall'ultimo controllo riuscito** (non cambia); e se il VPS non
     risponde l'avviso all'amministratore parte **una volta**, poi **una al giorno**, non ogni ora. Anche la copia
     rimasta indietro chiede il suo stato ogni ora (senza consumare biglietti).

> ⭐ **Le regole in vigore della licenza stanno in `SPECIFICHE.md` §15** (9 ott): questo documento resta il piano
> di lavoro e la storia delle domande.

## 11. Il confronto con ChatGPT: la soluzione su cui si è convenuto (8 ott 2026, notte)

*Chiesto dall'utente: «intavola un serrato confronto tecnico con ChatGPT … fino a quando non avete una soluzione
su cui concordate». Modello **GPT-5.6 Sol**, ragionamento al massimo, 3 turni, chiuso con «CONVERGED». Costo
≈ 2,6 $ (102 mila parole-unità in ingresso, 69 mila in uscita). ⛔ È una **proposta tecnica concordata fra due
modelli**, non una decisione: le scelte che toccano il commercio e le regole restano all'utente (§11.3). La
trascrizione non si conserva; qui c'è il risultato.*

### 11.1 Che cosa cambia rispetto alla domanda 6

- ⭐ **La licenza si lega alla «storia» dell'installazione, non al ferro.** Una macchina è un server fisico **o
  una macchina virtuale** (in cloud il ferro sotto non si vede e cambia). ⇒ Corregge «server fisico».
- ⭐ **Il cricchetto** (proposta di ChatGPT, al posto dell'«avviso a chi vende»): a ogni controllo (24 ore) il
  servizio consuma il gettone attuale e ne dà uno nuovo, usabile **una volta**. Un clone parte con lo stesso
  gettone: uno dei due va avanti, l'altro resta indietro ed è scoperto. Vale anche sulle macchine virtuali, dove
  il ferro è finto. ⛔ **Non** è il «posto vivo ogni 15 minuti» scartato dall'utente.
- ⭐ **Spostare REMOTIX su un server nuovo spegnendo il vecchio funziona da solo**, senza scrivere a nessuno:
  è la stessa storia che continua. Due copie accese insieme invece si separano e una resta indietro.
- **Niente impronta del ferro né integrazioni coi cloud nella prima versione** (troppo lavoro per uno; il
  cricchetto copre i cloni). **TPM in una seconda versione**, come rinforzo sui server fisici.

### 11.2 Il disegno, in breve

1. All'attivazione l'installazione crea una **coppia di chiavi** (ed25519, file leggibile solo da root); la
   licenza si lega alla chiave pubblica; ogni controllo **firma una sfida** del servizio.
2. L'**attestato firmato** porta tipo, scadenza commerciale, fine della tolleranza, «valido fino a» (mai più di
   **14 giorni**, controllato anche dal prodotto, gold compresa), storia e numero del gettone.
3. **Gold**: stesso meccanismo, nessuna scadenza commerciale (campo esplicito), revocabile.
4. **Chiavi**: radice fuori linea → chiave del VPS che firma solo gli attestati; indirizzi, chiavi valide e
   revoche in un **elenco firmato dalla radice**; due indirizzi di riserva nel prodotto. HTTPS normale, proxy sì.
5. **Formato dei messaggi**: binario semplice a lunghezze fisse, firmato, con esempi comuni C/Go e fuzzing.
6. **Mai un falso clone per un guasto**: la richiesta si scrive su disco **prima** di spedirla e, senza
   risposta, si rispedisce **identica**; il servizio ricorda l'ultima risposta e la ridà uguale.
7. Solo il servizio REMOTIX tocca lo stato della licenza; «controlla ora» passa da lui.
8. **La copia rimasta indietro** (clone, o backup ripristinato) non viene allungata: lavora fino al suo «valido
   fino a» e mostra all'amministratore un messaggio **neutro** («copia più vecchia, ripristinata?»).
9. **Il recupero** (ripristino da backup, server morto): chiave nuova + codice di licenza + **conferma via email
   all'acquirente** (la pagina mostra, il pulsante conferma). Uno ogni 30 giorni; tu puoi sbloccarlo a mano.
   ⛔ Niente pulsante solo locale: chi clona lo premerebbe e ruberebbe la licenza al cliente vero.
10. **Spostamento volontario**: la vecchia installazione firma il rilascio, la nuova si attiva.
11. **Se il VPS torna a un salvataggio vecchio**: i server dei clienti presentano l'ultima prova **firmata dal
    servizio** e lui si rimette in pari; mai fidarsi di numeri dichiarati dal cliente.
12. **Trial**: email verificata mai usata **e**, se c'è, l'impronta esatta di scheda madre (UUID + seriale) mai
    usata; reinstallare durante la trial ridà la stessa data di fine.
13. **Email dal VPS senza servizi a pagamento** (Postfix solo in uscita, SPF/DKIM/DMARC, rDNS): va bene se OVH
    lascia aperta la porta 25 e impostare il PTR, e se le prove verso Gmail/Microsoft/Yahoo passano; altrimenti
    serve un inoltro. ⚠ Da verificare sul VPS.
14. **Il VPS**: operazioni a transazione, copie cifrate fuori dal VPS, registro delle attivazioni e dei
    recuperi; pagina di recupero raggiungibile anche a licenza scaduta.
15. **TPM (seconda versione)**: chiave nata nel TPM, senza toccarne la proprietà né i PCR; un TPM guasto porta
    al recupero, mai a una chiave in file di nascosto.

### 11.3 Le decisioni che restano all'utente

1. **«Licenza legata alla storia dell'installazione»** al posto di «legata al ferro», con lo spostamento libero
   spegnendo il vecchio server.
   ✅ **9 ott: accettata** (utente: *«la tua proposta è migliorativa»*), con le tre aggiunte nate dalla sua
   proposta «al massimo 2 chiavi uguali attive, dopo 14 giorni la chiave si invalida» (⛔ scartata: invalidare
   la licenza punisce la vittima di un clone — e diventa un'arma per bloccare un concorrente — e una chiave
   ricavata dal ferro riapre i falsi allarmi e non distingue le macchine virtuali clonate):
   - **due copie scoperte** ⇒ **subito un'email all'acquirente** col link di recupero già pronto, e un avviso a
     chi vende;
   - **entro 14 giorni** si ferma la copia **senza** la conferma dall'email dell'acquirente; ⛔ **la licenza non
     si invalida mai da sola**;
   - **chi ci riprova**: la stessa licenza sdoppiata **3 volte in 90 giorni** va a chi vende, che guarda e
     decide se revocare. Una persona decide, non un automatismo.
   ✅ **9 ott, la full: SCEGLIE IL CLIENTE** (idea dell'utente, con le aggiunte di Claude accettate: *«certo»*):
   - **due copie attive** ⇒ email all'acquirente con i dati delle due e un **link a una pagina di scelta**;
     **72 ore** per scegliere, promemoria dopo 24;
   - ogni copia riceve un **nome breve** («copia A · 4F7K»), mostrato anche sulla sua pagina d'accesso: su una
     macchina virtuale clonata le impronte sono **identiche**, ed è il nome a farle riconoscere;
   - **i dati per scegliere, leggibili da una persona**: nome breve; giorno e ora della scoperta e dell'ultimo
     contatto; **IP pubblico** con fornitore, paese e città approssimata (da **RDAP**, il whois strutturato);
     **IP interni e nome della macchina** (due copie dietro lo stesso router hanno lo stesso IP pubblico);
     **descrizione dell'hardware** (marca e modello della scheda madre, processore, memoria, dischi) — ⚠ l'impronta
     cifrata non dice niente a una persona: si manda la descrizione, l'impronta resta per il confronto;
   - **senza scelta entro 72 ore**: resta la copia col biglietto più recente, l'altra si ferma; ⛔ la licenza **non
     si invalida mai**; una scelta arrivata dopo vale comunque (uno scambio ogni 30 giorni);
   - **scelta fatta** ⇒ la copia tenuta riceve una **chiave nuova** (altrimenti, con la stessa chiave, le due si
     scambierebbero il posto), l'altra si ferma; i suoi desktop restano vivi fino allo spegnimento;
   - ⛔ **l'impronta descrive, non decide**: a legare la licenza restano chiave e biglietto (cambiare un disco non
     fa di un cliente una macchina nuova);
   - ⚠ **riservatezza**: IP, nome della macchina e hardware di una copia finiscono nell'email dell'acquirente (anche
     quelli di chi ha clonato). Si fa per prevenire le frodi, e va **dichiarato nell'informativa** del prodotto.
2. **Un clone può lavorare fino a 14 giorni** prima di fermarsi.
3. **Una trial per email verificata** (oltre che per macchina): anche un'azienda che prova su due server usa due
   email.
   ✅ **9 ott, la trial semplificata dall'utente** (sostituisce la proposta dell'email):
   - **14 giorni, utenti illimitati** (*«così un'azienda può effettivamente valutare le vere potenzialità del
     prodotto»*); scaduta, REMOTIX si ferma e serve la full. ⇒ Sparisce il conteggio degli utenti dal programma.
     ⚠ Claude consigliava 30 giorni per i prodotti da azienda; scelta dell'utente: 14.
   - **legata alla firma dell'hardware** (UUID e seriale della scheda madre, confronto esatto), **niente email**;
   - **niente doppioni**: due copie attive della stessa trial ⇒ la trial si disabilita (nessuno ha pagato, nessuna
     vittima da proteggere).
   - ✅ **L'impronta si ricava da più elementi dell'hardware** (utente, 9 ott: *«l'impronta si ricava da elementi
     multipli dell'hardware»*; la genera il client, quindi c'è sempre): UUID e seriale della scheda madre,
     seriale del disco di sistema, indirizzo della scheda di rete. Le **scritte di fabbrica** («To be filled by
     O.E.M.», «Not Specified», tutti zeri) **si scartano** prima del calcolo: altrimenti macchine diverse
     avrebbero la stessa impronta e un cliente innocente risulterebbe un doppione. ⇒ Nel caso raro in cui
     non resta niente di distintivo, la trial **non parte da sola**: «questa macchina non può avviare la prova
     automatica: scrivici», e chi vende la attiva a mano dallo strumento delle licenze. **Niente email.**
     ⚠ Dichiarato: una macchina virtuale **nuova** in cloud ha un'impronta nuova, quindi una trial nuova; si
     accetta.
4. La trial resta «al meglio»: email usa-e-getta e macchine virtuali nuove in cloud la aggirano.
5. **Un recupero ogni 30 giorni**, e che cosa ti basta per sbloccarlo a mano.
6. **Email spedite dal VPS** con il loro rischio di consegna, e il recupero a mano se un'email non arriva.
7. **La gold deve comunque farsi sentire almeno ogni 14 giorni.**
   ✅ **9 ott, la gold semplificata** (utente): nessuna scadenza, nessun avviso, nessun rinnovo; **una per
   macchina** resta. Due copie attive ⇒ **avviso a chi vende con tutti i dettagli** e **chi vende disabilita una
   delle due** (utente: *«devo avere la facoltà di disabilitare uno dei doppioni»*). Senza rete: **14 giorni**,
   come le altre (utente, 9 ott; Claude proponeva 90). Regole in `SPECIFICHE.md` §15.1.
   ✅ **9 ott: i codici di attivazione non si riutilizzano mai** (utente). Conseguenza (Claude): il recupero, che
   nel disegno concordato chiedeva di reincollare il codice, usa invece il **numero di licenza** (non segreto) più
   la conferma via email; il codice attiva una volta sola. `SPECIFICHE.md` §15.3.
8. Per quanto si tengono email degli acquirenti, impronte delle trial e registri (riservatezza).
   ✅ **9 ott: 2 anni** (utente: *«almeno 2 anni»*), ⚠ ma come **tetto, non come minimo** (correzione di Claude: per
   il GDPR i dati personali si tengono **non oltre** il necessario, e il periodo va scritto nell'informativa):
   - email dell'acquirente, licenze e registro delle attivazioni: **2 anni dalla fine del rapporto** (ultima
     scadenza della full);
   - impronte delle trial: **2 anni dalla trial** (servono a non darne una seconda);
   - dati di uno sdoppiamento (IP, RDAP, nomi delle macchine, hardware): **6 mesi** dalla scelta, poi resta solo
     «sdoppiamento del giorno X, risolto così»;
   - ⚠ fatture e documenti fiscali seguono la legge (in Italia 10 anni), ma li tiene chi incassa: si decide col
     pagamento. ⛔ Claude non è un legale: l'informativa va fatta controllare prima della vendita.
9. Quando fare il TPM; le integrazioni coi cloud solo se i clienti le chiedono.
   ✅ **9 ott: il TPM esce dal piano** (utente: *«non credo che possiamo farci affidamento: non tutte le VM sono
   configurate per avere il TPM»*). Coerente con la regola «niente eccezioni per compositore»: una protezione che
   c'è solo su una parte delle macchine non regge il disegno. Il disegno vale **uguale ovunque** (chiave in un
   file, biglietto giornaliero, scelta del cliente). Si riapre solo se gli sdoppiamenti diventano un problema
   vero. Fuori anche le integrazioni coi cloud.

✅ **La stima di §8 è stata rifatta il 9 ott: ~122 ore** (era ~72).
