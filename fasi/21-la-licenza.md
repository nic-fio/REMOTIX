# Fase 21 — La licenza

*Piano scritto l'**8 ottobre 2026** sera, sul portatile, mentre girava la campagna della fase 20 (il server di
casa non è stato toccato). ⛔ **Da approvare dall'utente prima di qualunque lavoro.** Le decisioni stanno in
`DECISIONI.md` §10.30 e qui **non si ripetono**: si rimanda. Questo documento dice **come** si fanno e in che
ordine. ⚠ Vincolo dell'utente (8 ott): **la licenza viene prima del banco xrdp** (`fasi/20-le-prestazioni.md`
§3 punto 4b); il banco si scrive accanto senza toglierle ore.*

---

## 1. Che cosa si costruisce, in una riga per parte

| parte | che cosa fa | dove gira | linguaggio |
|---|---|---|---|
| **1. il prodotto** | chiede la licenza, la ricorda, la ricontrolla, la fa rispettare all'accesso | sul server del cliente, dentro `remotix` | C, come il prodotto |
| **2. il servizio di licenze** | registra le macchine, risponde ai controlli, vede i cloni, ricorda le trial | sul **VPS** (§10.30, 8 ott) | Go (§3.1) |
| **3. lo strumento di chi vende** | crea full e gold, revoca, elenca le macchine | sul portatile di chi vende, parla col VPS | Go, nello stesso modulo della parte 2 |
| **4. l'ingresso del pagamento** | «rinnova» / «sospendi questa licenza», generico | sul VPS, nel servizio | Go |

I tre tipi (§10.30, nome «gold» dall'8 ott): **trial** ~~1 utente · 30 giorni~~ **illimitati · 14 giorni** (9 ott) · chiunque; **full** illimitati ·
1 anno con rinnovo automatico · **l'unica in vendita**; **gold** illimitati · senza scadenza · solo chi vende
(le sue macchine e quelle di prova).

## 2. Parte 1 — il prodotto

### 2.1 Dove si innesta, letto nel codice

| che cosa | dove sta oggi | che cosa cambia |
|---|---|---|
| **l'accesso** | `src/autenticazione.c:212` `rcp_autentica()` (PAM, `pam_authenticate` :247 e `pam_acct_mgmt` :253), chiamata **solo dal nipote** dell'aiutante (`src/aiutante.c:23-30`); l'esito torna al filo in `src/rcp.c:~2490-2515` | **dopo** credenziali giuste (§10.30: chi non ha un account non scopre lo stato della licenza) il filo guarda lo stato della licenza **in memoria**: niente rete in quel punto, nessun ritardo in più all'accesso |
| **i rifiuti** | i motivi di `CONGEDO` in `src/rcp.h:113-133` (`0x01`…`0x10`), le frasi in `src/pagina.html:896-999` | due motivi nuovi, da scrivere prima in `RCP.md`: **`0x11 LICENZA_SCADUTA`** (trial o full scaduta: si apre il campo del codice) e **`0x12 LICENZA_UN_UTENTE`** (trial, il posto è già preso). ⚠ `0x0E` resta generico apposta (`pagina.html:964`): la licenza **non** ci va dentro |
| **la pagina d'accesso** | il modulo in `src/pagina.html:600-625`; i segni sostituiti dal server in `src/pagina.c:420-433` (`__IMPRONTA__`, `__AVVISO__`, `__BANNATO__`) e l'elenco di controllo in `pagina.c:708` | un segno nuovo `__LICENZA__` (stato e giorni rimasti, **innocuo**: §10.30 lo vuole visibile anche prima delle credenziali); il collegamento «Hai un codice di licenza?» / «Cambia licenza»; il campo del codice; **l'identificativo della macchina** accanto al campo (serve a chi compra) |
| **il codice inserito** | — | viaggia sul canale già cifrato, in un messaggio nuovo di `RCP.md` (dopo l'autenticazione, quindi solo per chi ha un account); il filo lo passa al **messaggero** (§2.2), che lo porta al VPS |
| **la memoria della licenza** | `/var/lib/remotix/` esiste già (`src/main.c:1768-1770`: `certificati`, `ban`; `src/figlio.c:1658`) | `/var/lib/remotix/licenza/`: l'**attestato** firmato dal VPS (§2.3), l'identificativo casuale di questo avvio, l'ultima data vista (contro l'orologio che torna indietro, §10.30). Permessi come `certificati` |
| **il tetto delle sessioni** | ⭐ **è già deciso all'avvio**: `--tetto-sessioni N` (`src/main.c:2084`, `rcp_tetto_imposta()` in `src/rcp.c:932`), predefinito **10** (`src/rcp.h:97`). ⚠ `MAX_ATTACCATE` **non esiste più** dal 25 agosto (`src/rcp.c:895-902`): `DECISIONI.md` §10.30 e `fasi/20-le-prestazioni.md` §4 sono rimasti indietro | resta da fare solo la parte amministrativa: l'installatore scrive il tetto in `REMOTIX_OPZIONI` (`packaging/*/remotix.service`) e la documentazione lo dice. ⛔ **La licenza non tocca il tetto**: in trial il limite di 1 è un controllo al posto (§2.4), non un `--tetto-sessioni 1`, perché `rcp_tetto_imposta` vale una volta sola e chi attiva la full a metà giornata dovrebbe riavviare |

### 2.2 Il messaggero: la rete fuori dal filo

⛔ Il server è **un filo solo** (lo stesso motivo per cui PAM sta nell'aiutante, `src/aiutante.c:23-30`): una
domanda in rete al VPS, con un proxy lento, fermerebbe tutte le sessioni. ⇒ Un **processo a parte**, figlio del
padre come l'aiutante, che:
- all'avvio e poi ogni **N ore** (§10, domanda 1) manda al VPS: codice (o «trial»), `/etc/machine-id`,
  identificativo casuale di questo avvio, versione;
- passa dal **proxy** se c'è (`https_proxy` dell'ambiente del servizio, o un'opzione in `REMOTIX_OPZIONI`);
- riceve l'attestato firmato, lo **verifica** e lo scrive su disco; al filo manda solo lo stato («trial, 23
  giorni» · «full fino al …» · «scaduta» · «sospesa»).

**La libreria per parlare HTTPS:** ⭐ proposta **libcurl** — proxy, `https_proxy`, certificati di sistema già
fatti; licenza MIT-simile (curl), compatibile col codice chiuso (§10.30); c'è in tutte le distribuzioni del
catalogo. ⚠ È una **dipendenza nuova** del pacchetto. L'alternativa è scrivere il client HTTP sopra OpenSSL
(già dipendenza, `src/tls.c`), ma il proxy `CONNECT` e i suoi casi sono lavoro che curl ha già.

### 2.3 L'attestato

Il VPS non manda «sì/no» ma un **attestato firmato** (ed25519): tipo, scadenza, identificativo della macchina,
**valido fino a** (= ora del controllo + tolleranza). Il prodotto lo verifica con OpenSSL (`EVP_PKEY_ED25519`,
già dentro). Così:
- la **tolleranza** se la rete manca è semplice: finché l'attestato è valido si entra, anche senza VPS;
- un attestato copiato su un'altra macchina non vale (porta il `machine-id`);
- chi falsifica la risposta del VPS senza la chiave non produce un attestato valido.

### 2.4 Le regole all'accesso

| stato | prima delle credenziali | dopo credenziali giuste |
|---|---|---|
| **trial** valida | «Trial version — restano N giorni» + «Hai un codice di licenza?» | si entra se **nessun altro** è dentro, altrimenti `0x12` |
| **full / gold** valida | niente; solo «Cambia licenza», piccolo | si entra (resta il tetto tecnico) |
| **scaduta** (trial finita, full non rinnovata, attestato oltre la tolleranza) | niente | `0x11`: il campo del codice **già aperto** |
| **sospesa** dal VPS (pagamento revocato, clone) | niente | `0x11`, con la frase della sospensione |
| **mai attivata** (primo avvio senza rete) | ⛔ §10.30: **niente attivazione senza rete** | la pagina dice «il server non ha ancora potuto attivare la licenza: serve l'accesso a internet» |

⚠ **Le sessioni già aperte non si chiudono** quando la licenza scade: si nega solo l'accesso nuovo.
(Da confermare, §10 domanda 5.)

## 3. Parte 2 — il servizio di licenze sul VPS

### 3.1 Il linguaggio: Go

- ⭐ **l'installatore è già in Go** (`installatore/go.mod`: `go 1.25`, con `vendor/`): stesso contenitore di
  costruzione, stessa catena, un binario statico solo da copiare sul VPS;
- la libreria standard ha già tutto quello che serve: `net/http` con TLS, `crypto/ed25519`, `encoding/json`;
- ⛔ niente framework: un binario, un'unità systemd, un file di configurazione.

### 3.2 La base dati

⭐ **SQLite** in un file solo (con la libreria in Go puro `modernc.org/sqlite`, licenza BSD: niente cgo, il
binario resta statico). Bastano migliaia di clienti; la copia di riserva è **copiare un file**.

| tabella | che cosa tiene |
|---|---|
| `licenze` | codice, tipo (trial/full/gold), cliente, scadenza, stato (attiva/sospesa/revocata), riferimento del pagamento |
| `macchine` | `machine-id`, licenza, prima e ultima volta vista, versione |
| `avvii` | identificativo casuale di ogni avvio, macchina, ultimo controllo ⇒ i **cloni** |
| `trial_date` | ogni `machine-id` che ha già avuto la sua trial (§10.30: una macchina, una trial) |
| `registro` | ogni operazione dello strumento e del pagamento: chi, quando, che cosa |

### 3.3 Le operazioni del servizio

*Riscritta il **9 ottobre 2026** sera, su richiesta dell'utente (*«prima definiamo le operazioni che deve svolgere
il server e poi definiamo l'interfaccia web»*): ⛔ supera la tabella dell'8 ott (`machine-id`, «avvii», controllo
ogni N ore). Le regole stanno in `SPECIFICHE.md` §15 e qui non si ripetono: ogni riga rimanda. ⏳ **Da approvare**:
le righe 🔸 sono proposte di Claude, nate dai buchi che §15 lascia.*

**A. Il prodotto** (il server del cliente; ogni domanda è firmata con la chiave dell'installazione)

| # | operazione | che cosa fa | §15 |
|---|---|---|---|
| A1 | **attiva con codice** | consuma il codice (una volta, per sempre), lega la licenza alla chiave pubblica, dà attestato e primo biglietto | 15.3 |
| A2 | **chiedi la trial** | riceve impronta ed email, manda il link di conferma; se l'impronta ha già avuto la trial ridà la **stessa** data di fine; se l'impronta è vuota risponde «scrivici» | 15.7 |
| A3 | **controlla** (ogni ora, e «controlla ora») | consuma il biglietto e ne dà uno nuovo con l'attestato; ridà **la stessa risposta** a una richiesta identica; scopre lo sdoppiamento; dice lo stato (valida, in tolleranza, sospesa, revocata, bloccata, gold doppia) | 15.4, 15.8 |
| A4 | **stato della copia indietro** | risponde senza consumare biglietti | 15.9 |
| A5 | **rilascia** | la vecchia installazione firma il rilascio per lo spostamento volontario | 15.9 |
| A6 | **chiedi il recupero** | numero di licenza + chiave nuova ⇒ email di conferma all'acquirente; rispetta «uno ogni 30 giorni» | 15.9 |
| A7 | **dammi l'elenco firmato** | indirizzi, chiavi valide e revoche, firmati dalla chiave madre | 15.11 |
| A8 | **descrivi la macchina** | dentro A1-A3: descrizione dell'hardware, IP interni, nome; il servizio tiene solo l'ultima | 15.8, 15.12 |

**B. L'acquirente** (pagine aperte da un link nell'email: la pagina **mostra**, il pulsante **conferma**)

| # | operazione | §15 |
|---|---|---|
| B1 | **conferma l'email della trial** — 🔸 la trial **parte alla conferma**, non prima (altrimenti l'email non conferma niente) | 15.7 |
| B2 | **scegli la copia** fra le due attive; la tenuta riceve una chiave nuova, l'altra si ferma; sblocca anche una licenza già bloccata | 15.8 |
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
| D1 | **crea una full**: email dell'acquirente, nota ⇒ numero `RX-…` e codice, email al compratore | 15.1, 15.3 |
| D2 | **crea una gold**: nota («scatola 3») ⇒ numero e codice | 15.1 |
| D3 | **attiva una trial a mano** (la macchina senza impronta) | 15.7 |
| D4 | **rinnova a mano** (pagamento fuori processore, finché il processore non c'è) | 15.6 |
| D5 | **sospendi · riattiva · revoca** | 15.1, 15.10 |
| D6 | **gold doppia**: guarda le due copie, **disabilita una** | 15.1 |
| D7 | **licenza bloccata da 15 giorni lavorativi**: **sblocca** o **cancella definitivamente** | 15.8 |
| D8 | **3 sdoppiamenti in 90 giorni**: guarda, **revoca** o lascia | 15.8 |
| D9 | **sblocca il limite dei 30 giorni** (scambio o recupero) | 15.8, 15.9 |
| D10 | 🔸 **codice perso prima dell'uso**: annulla il vecchio e ne emette uno nuovo (i codici non si conservano in chiaro, quindi non si possono rimandare) | 15.3 |
| D11 | 🔸 **cambia l'email dell'acquirente** (assistenza), con avviso al vecchio indirizzo | — |
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
| E4 | i link (conferme, scelta) scadono | 15.8 |
| E5 | le cancellazioni: sdoppiamenti a 6 mesi, il resto a 2 anni | 15.12 |
| E6 | la copia cifrata fuori dal VPS, ogni giorno | 15.11 |

## 4. Parte 3 — il pannello di chi vende

✅ **9 ott, utente: un'interfaccia web** al posto dello strumento a riga di comando (supera §9 «pannello web
fuori»). Le operazioni sono la sezione D di §3.3. ⏳ L'interfaccia si definisce dopo le operazioni.

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

- ⭐ **Il servizio finto è il servizio vero**, in un contenitore podman sul portatile, con chiavi di prova e un
  orologio spostabile (per far scadere trial e full in un minuto invece che in 30 giorni o un anno).
- **Il prodotto lo trova** con un'opzione (`--licenze-url`), che il pacchetto non mette mai.
- **I casi**, uno per banco: trial nuova · trial già data sulla stessa macchina · trial scaduta → codice → si
  entra · full scaduta e rinnovata dal «pagamento» · VPS spento dentro e oltre la tolleranza · proxy (squid in un
  contenitore) · attestato copiato su un'altra macchina · clone (due avvii vivi) · chiave del VPS revocata ·
  orologio della macchina riportato indietro · secondo utente in trial (`0x12`).
- ⚠ **I banchi di oggi** (la suite corta, le salite della 16) aprono fino a 16 sessioni: senza licenza si
  fermerebbero a 1. ⇒ Le scatole di prova prendono una **gold di prova** dal servizio finto, come ogni cliente
  (§10.30: niente versione speciale del programma).

## 8. I passi, in ordine

*Rifatta il **9 ottobre 2026** dopo le decisioni di §10 e §11 (la stima del piano scritto l'8 ott era ~72 ore).
Entrano: il biglietto giornaliero (qui orario), la scelta del cliente con la pagina e le email, il recupero, la
posta dal VPS, il formato dei messaggi con le prove comuni C/Go. Escono: il TPM, il conteggio degli utenti
(trial a utenti illimitati), le integrazioni coi cloud.*

| # | passo | ore |
|---|---|---|
| 0 | `RCP.md` coi motivi di chiusura e i messaggi della licenza | 1 |
| 1 | **le chiavi**: radice fuori linea, chiave del VPS di prova, l'**elenco firmato dalla radice** (indirizzi, chiavi, revoche), ripresi dalla catena A | 6 |
| 2 | **il formato dei messaggi**: binario a lunghezze fisse, firmato; esempi comuni C/Go; fuzzing dei due lettori | 6 |
| 3 | **il servizio** (Go): attivazione, controllo orario col **biglietto** (consumo atomico, risposta ripetibile, prova firmata per il ritorno a un salvataggio vecchio), sdoppiamenti coi **nomi brevi**, la **pagina di scelta** (72 ore, promemoria a 24, scelta tardiva, 1 ogni 30 giorni, 3 in 90 a chi vende), recupero e spostamento, trial senza doppioni, RDAP, cancellazioni a 6 mesi e 2 anni | 30 |
| 4 | **la posta dal VPS**: Postfix solo in uscita, SPF/DKIM/DMARC, PTR, i testi delle email, prove verso Gmail/Microsoft/Yahoo | 6 |
| 5 | **lo strumento** di chi vende: crea full e gold, revoca, trial a mano, sblocco del limite dei 30 giorni, gli sdoppiamenti da guardare | 7 |
| 6 | **l'ingresso del pagamento** (rinnova/sospendi, senza processore) | 2 |
| 7 | **il prodotto, il messaggero** (processo a parte, libcurl, proxy): richiesta scritta su disco prima di partire, biglietto, ora fidata, impronta da più fonti con le scritte di fabbrica scartate, descrizione dell'hardware, IP interni | 16 |
| 8 | **il prodotto, l'accesso**: stato della licenza, alla scadenza collegamenti chiusi e desktop vivi, la copia rimasta indietro | 6 |
| 9 | **la pagina**: i tre stati, il campo del codice, gli **avvisi alla RootSpeak** con «ho letto» (trial e full), il nome breve della copia, «Recupera», lo spostamento | 10 |
| 10 | **i banchi**: servizio finto e posta finta in contenitore; guasti a metà controllo, cloni, ritorno del VPS a un salvataggio vecchio, scelta e mancata scelta; la suite corta e le salite con la gold di prova | 16 |
| 11 | **pacchetti e installatore**: libcurl nelle tre famiglie, la chiave vera nel comando di rilascio | 5 |
| 12 | **il VPS vero**: servizio, unità, certificato, posta, copie cifrate fuori dal VPS | 6 |
| 13 | `SPECIFICHE.md`, `DECISIONI.md` §10.30 riallineata, **la bozza dell'informativa** sulla riservatezza (da far controllare) | 5 |
| | **totale** | **~122 ore ≈ 15 giorni di lavoro** |

⚠ La stima è di chi non ha ancora scritto una riga: il servizio (passo 3), il messaggero (passo 7) e la pagina
(passo 9) sono i punti dove la storia del progetto dice che si sbaglia per difetto. ⚠ Il passo 4 dipende da OVH
(porta 25 aperta, PTR impostabile): se OVH non lo permette serve un inoltro, ed è una decisione dell'utente.

## 9. Che cosa resta fuori

- **il pagamento vero** (processore, IVA, fatture): in sospeso per decisione dell'utente (§10.30);
- **il contratto di vendita** della full: è una domanda (§10 domanda 3);
- **la prova di capacità per il cliente** (§10.30, il programma accanto al server): è un lavoro suo, non della
  licenza; si fa dopo;
- ~~un **pannello web** per chi vende~~ ⛔ rientrato il 9 ott su richiesta dell'utente (§4);
- difese contro chi modifica il binario: §10.30 lo dichiara, la licenza tiene onesti gli onesti.

## 10. Domande per l'utente, una per volta

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
