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

I tre tipi (§10.30, nome «gold» dall'8 ott): **trial** 1 utente · 30 giorni · chiunque; **full** illimitati ·
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
(Da confermare, §7 domanda 5.)

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

### 3.3 Le domande (API)

| domanda | chi la fa | che cosa fa |
|---|---|---|
| `POST /v1/attiva` | il prodotto | prima volta: con «trial» registra la trial (se la macchina non l'ha già avuta); con un codice lega la licenza alla macchina. Torna l'attestato |
| `POST /v1/controlla` | il prodotto, ogni N ore | rinnova l'attestato; registra l'avvio; se la licenza è sospesa o scaduta lo dice |
| `POST /v1/pagamento/rinnova` · `/sospendi` | il pagamento (parte 4) | sposta la scadenza di un anno / sospende |
| `…/v1/vendita/*` | lo strumento (parte 3) | crea, revoca, elenca |

⛔ **Tutte in HTTPS** (certificato Let's Encrypt del dominio del VPS, §7 domanda 4). Le domande del prodotto
sono anonime ma legate al codice; quelle di pagamento e vendita hanno una **chiave segreta** ciascuna.

### 3.4 I cloni

La tecnica dei «processes» (§10.30): ogni avvio del prodotto ha un identificativo casuale suo. Se sulla stessa
licenza **e sullo stesso `machine-id`** risultano **due avvii vivi** (entrambi controllati entro N ore),
è una macchina clonata o un identificativo copiato. ⚠ Che cosa fare in quel caso è una **decisione tua**
(§10 domanda 6): avvisare chi vende, oppure sospendere la seconda.

## 4. Parte 3 — lo strumento di chi vende

Un comando, `remotix-licenze`, sul portatile:
- `crea full --cliente "…" --macchina <machine-id>` · `crea gold --macchina <machine-id> --nota "server di prova"`;
- `revoca <codice>` · `sospendi` / `riattiva`;
- `elenco` (licenze, macchine, ultimo controllo, cloni sospetti) · `storia <codice>`.

Parla col VPS con la sua chiave segreta. ⚠ Finché il pagamento non c'è (§10.30), **le full si creano a mano da
qui**.

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

| # | passo | ore |
|---|---|---|
| 0 | le risposte alle domande di §10 (almeno 1, 4, 5, 6) e `RCP.md` aggiornato coi due motivi e il messaggio del codice | 3 |
| 1 | **le chiavi**: radice e chiave del VPS di prova, il certificato, ripresi dalla catena A | 4 |
| 2 | **il servizio** (Go): base dati, `attiva`, `controlla`, attestato firmato, cloni, trial già date | 14 |
| 3 | **lo strumento** di chi vende | 5 |
| 4 | **l'ingresso del pagamento** (le due domande, senza processore) | 2 |
| 5 | **il prodotto, il messaggero** (processo a parte, libcurl, proxy, attestato su disco, verifica in C) | 10 |
| 6 | **il prodotto, l'accesso** (stato in memoria, `0x11`/`0x12`, la regola di 1 utente in trial) | 6 |
| 7 | **la pagina** nei tre stati, il campo del codice, l'identificativo della macchina; le frasi in `pagina.html` | 6 |
| 8 | **i banchi** di §7, col servizio finto in contenitore; la suite corta e le salite con la gold di prova | 10 |
| 9 | **pacchetti e installatore**: libcurl fra le dipendenze delle tre famiglie, il tetto in `REMOTIX_OPZIONI`, la chiave vera nel comando di rilascio | 5 |
| 10 | **il VPS vero**: il servizio, l'unità, il certificato, la copia di riserva della base dati | 4 |
| 11 | `SPECIFICHE.md` (stati della pagina, riservatezza: il server manda codice e `machine-id`), `DECISIONI.md` §10.30 riallineata su `MAX_ATTACCATE` | 3 |
| | **totale** | **~72 ore ≈ 9 giorni di lavoro** |

⚠ La stima è di chi non ha ancora scritto una riga: il messaggero (passo 5) e la pagina (passo 7) sono i due
punti dove la storia del progetto dice che si sbaglia per difetto.

## 9. Che cosa resta fuori

- **il pagamento vero** (processore, IVA, fatture): in sospeso per decisione dell'utente (§10.30);
- **il contratto di vendita** della full: è una domanda (§10 domanda 3);
- **la prova di capacità per il cliente** (§10.30, il programma accanto al server): è un lavoro suo, non della
  licenza; si fa dopo;
- un **pannello web** per chi vende: lo strumento a riga di comando basta finché i clienti si contano a mano;
- difese contro chi modifica il binario: §10.30 lo dichiara, la licenza tiene onesti gli onesti.

## 10. Domande per l'utente, una per volta

1. **La tolleranza se la rete manca**: quanti giorni il server continua a far entrare senza riuscire a parlare
   col VPS? (⚠ Va più lunga del tempo per rimettere in piedi il VPS, §10.30; e ogni quante ore si ricontrolla.)
2. **La tolleranza a rinnovo mancato**: quanti giorni dopo la scadenza della full, prima della finestra «abbonamento
   scaduto, rinnova» (§10.30, ancora 🔸 da confermare)?
3. **Il contratto di vendita** della full: quale testo (§10.30: per la trial c'è PolyForm Free Trial, per la full
   nessun testo standard)?
4. **Il VPS**: fornitore, sistema operativo, **dominio** con cui i clienti lo raggiungono (serve al certificato
   HTTPS e va scritto nel prodotto), chi ha l'accesso.
5. **Le sessioni aperte quando la licenza scade**: restano fino all'uscita (proposta) o si chiudono?
6. **Il clone scoperto**: si avvisa solo chi vende, o si sospende la seconda copia da sola?
7. **Che cosa compra la full oltre a utenti e durata**: gli aggiornamenti sono compresi finché l'abbonamento è
   attivo, e dopo la scadenza il prodotto si aggiorna ancora?
