# Fase 16 — Stress e capacità

*Decisa dall'utente il **25 settembre 2026**, pomeriggio, a fase 15 chiusa a zero difetti. Questo
documento fissa **prima** dei test tutto quel che la campagna farà: le decisioni, l'impianto, i
lavori, le misure, le soglie. ⛔ Le soglie di §9 si approvano prima della campagna e **non si
toccano dopo**. I test veri partono in una **sessione nuova**, da questo documento.*

---

## 1. La domanda

La fase 15 ha detto: **REMOTIX funziona** (giro 2: 329 PASS su 329, 328 guasti visti su 328).
La fase 16 chiede: **quanto carico regge REMOTIX continuando a funzionare?**

- limite di progetto: **16 utenti contemporanei**, senza licenze per utente o per sessione;
- non si presume che 16 reggano: si cerca l'**ultimo livello nominale**, i livelli di
  **degradazione**, l'eventuale **punto di rottura**;
- oltre 16 solo come **prova di sovraccarico**, classificata a parte, e mai necessaria;
- il risultato è una **proprietà della configurazione misurata** (desktop, scheda, commit,
  misura dello schermo, carico), non una promessa per ogni macchina.

⛔ La fase 16 **non** si usa per compensare un difetto funzionale: se un livello mostra un
difetto che la fase 15 avrebbe dovuto vedere, si torna alla suite.

## 2. Le decisioni dell'utente (25 settembre 2026)

| | decisione | perché |
|---|---|---|
| **i browser-cliente girano SUL SERVER** | *«è inevitabile che la macchina di test dev'essere lo stesso server su cui gira remotix»* | il tablet è un collo (grafica e Wi-Fi) e falserebbe tutto (`[M]` fase 15: in 4K il tablet perde fotogrammi, il server no; il telefono sul 2,4 GHz perdeva lo 0,6 % dei pacchetti) |
| ⇒ **conti separati** | REMOTIX · sessioni · browser misurati ciascuno per conto suo (§6) | il server fa due lavori: produce i desktop e li guarda |
| ⇒ **il risultato è un limite INFERIORE** | «N utenti su questo server, **che intanto fa girare anche gli N browser**» | con clienti separati la capacità sarebbe uguale o più alta, mai più bassa |
| **il tetto delle sessioni alzato a 16** | oggi `--tetto-sessioni 10` (fase 10) rifiuterebbe l'undicesimo | si alza per la campagna, si dichiara in ogni registrazione, poi si rimette; oltre 16 solo in sovraccarico |
| **4K per tutti** | *«puntiamo al 4K, che è il valore a cui aspira Remotix»* | è la misura delle specifiche (`prove-in-4k`) |
| **la scala delle misure** | se il 4K va in FAIL: **3K → 2K → Full HD** | vedi §8 |
| **YouTube 4K: 1 utente su 4** | rotazione fissa dei quattro profili | vedi §5 |
| **due campagne** | Intel UHD 770 integrata, poi **AMD Radeon RX 6800 16 GB** | la RX 6800 va montata sul server; prima la si prova con un utente solo (§11) |
| **la salita a gradini: 1 → 4 → 8 → 12 → 16** (25 set, sera) | *«forse avevo esagerato»*: un utente alla volta costava 24–96 ore di macchina | il punto di rottura si trova lo stesso, preciso a un utente, con la ricerca a metà (§6); si perde solo la curva utente per utente dove è tutto verde |
| **tetto a 17 durante la campagna** (25 set, sera) | scelta 1 di due: al gradino 16 il controllo corto (§7) è la 17ª sessione, per ~70 s | i 16 utenti restano 16 e il carico è uguale a quello degli altri gradini; il 17° è solo il controllo, dichiarato in ogni livello; a fine campagna il tetto torna al predefinito |
| **logging nel journal di sistema** | `journalctl`, niente sistemi propri al suo posto | vedi §12 |

## 3. Le precondizioni — tutte soddisfatte il 25 settembre 2026

- fase 15 chiusa: funzioni utente, stacco/riattacco, rientro, immagine, input, tela e misure,
  audio/video, perdita di rete, percorsi, browser (Firefox 140, Chrome 154) — **zero difetti**;
- commit certificato: `d121715` (segno `fase15-giro2-congelato`), binario `b1443a0b`; la pagina
  d'accesso nuova è `c5279e66` (264 PASS su 264 nelle prove che passano dal modulo);
- ⚠ il commit della campagna sarà **quello del giorno** (con journald e il tetto configurabile
  già c'è): lo si identifica e si fa girare **prima** la suite corta di regressione (§13).

## 4. L'impianto: il percorso vero, tutto sulla stessa macchina

**utente automatico → browser vero (Firefox o Chrome) → API del browser → WebTransport/HTTP3/QUIC
→ RCP → REMOTIX → sessione grafica vera → applicazione vera**

| pezzo | come | perché |
|---|---|---|
| **un compositore per utente** | 16 `labwc` senza schermo, ognuno a 3840×2160, uno per browser | `[M]` fase 15: una finestra di Chrome coperta da un'altra smette di disegnare (foto appese fino a 17 min) — con 16 finestre 4K nello stesso compositore misureremmo quello |
| **i browser** | alternati: gli utenti dispari Firefox, i pari Chrome | i due motori serviti (`SPECIFICHE` §11.5) |
| **gli utenti** | inquilini nuovi `c16uNN`, uno per livello, nella scatola del desktop sotto prova (`rete11-<desktop>`) | come la suite: nati da zero, sgomberati alla fine |
| **l'automazione** | l'input arriva **dal browser** (Marionette/CDP, eventi veri), come nella suite; le applicazioni si lanciano dentro la sessione come l'utente | nessun cliente finto: il percorso è quello di un utente |
| **la rete** | locale al server (il browser si collega a `192.168.0.2`) | ⚠ non misura il Wi-Fi: la rete vera è una questione a parte (§15) |

**Chi fa gli utenti** (proposta dell'utente del 25 set: *«sub-agenti per simulare gli utenti che
si collegano a quel server»*, e la forma scelta):

- ogni utente è un **attore indipendente**: un suo processo, il suo browser, il suo compositore,
  il suo orologio — partono e lavorano **in parallelo e senza sincronia fra loro**, come persone
  diverse; nessun direttore unico che li fa muovere a turno;
- l'attore è un **programma**, non un agente di intelligenza artificiale: un agente impiega
  secondi a decidere ogni gesto (il ritmo dell'input diventerebbe quello del modello, non di una
  persona), non rifà mai due volte la stessa cosa (le salite non si potrebbero ripetere né
  confrontare Intel/Radeon) e per 16 utenti × 3 ore costerebbe moltissimo;
- il **realismo** viene dal ritmo: pause, ordine delle azioni e velocità di battitura variano
  come in una persona, estratti da un **seme** fissato per utente — ogni salita è diversa dentro
  e identica fra una campagna e l'altra;
- i **subagenti** si usano dove rendono: costruire in parallelo i quattro lavori e i misuratori;
  e, durante la campagna, uno per sessione a **leggere le evidenze** di un livello DEGRADED o FAIL
  e cercarne la causa mentre la salita è ferma.

⛔ Il cliente Python e gli script che imitano un browser **non** fanno carico: possono solo
aiutare a diagnosticare (§4 del documento dell'utente).

## 5. I quattro lavori, e come si distribuiscono

Gli utenti entrano **a gradini** (§6); il lavoro di ciascuno è fissato dal suo numero e **non
cambia** in nessuna campagna:

| utente | profilo | che cosa fa, in ciclo, per tutta la durata |
|---|---|---|
| 1, 5, 9, 13 | **A — navigazione** | un browser dentro la sessione (Firefox ESR della scatola) apre pagine in giro fra un elenco fisso (testo, immagini, una pagina lunga che scorre), clicca, scorre con la rotella |
| 2, 6, 10, 14 | **B — file manager** | il file manager del desktop: apre cartelle, ne crea e ne cancella in una cartella di prova, apre e chiude finestre, cambia vista |
| 3, 7, 11, 15 | **C — terminale** | il terminale del desktop: comandi con uscita (`ls`, `find`, `top` per qualche secondo, un file di testo che scorre), battuti dalla tastiera del browser |
| 4, 8, 12, 16 | **D — YouTube 4K** | un video YouTube in 4K a schermo intero, sempre lo stesso (fissato nel piano d'esecuzione), riprodotto in Firefox ESR dentro la sessione, **per tutta la salita** |

⇒ a 16 utenti: **4 video 4K** e 12 lavori d'ufficio. ⚠ Il video pesa sulla stessa scheda che
codifica e disegna: è voluto, è l'uso vero. `[?]` Serve internet dal server: `[M]` 25 set
raggiungibile. Se YouTube cambia qualcosa sotto (pubblicità, qualità automatica), si ripiega su
**un file video 4K locale** fisso, dichiarato — la scelta si fa nel piano d'esecuzione e non cambia
fra le campagne.

## 6. La salita e i controlli

**PREPARARE → AVVIARE → SALIRE AL GRADINO → 10 MINUTI → CONTROLLARE → REGISTRARE → RIPETERE**
sui gradini **1 → 4 → 8 → 12 → 16** utenti (decisione dell'utente, 25 set sera), oppure fino a un
limite reale dimostrato. Gli utenti di un gradino entrano uno dopo l'altro, ciascuno quando il
precedente ha il primo fotogramma (così si misura anche la nascita sotto carico).

1. scatola rifatta da zero, server acceso col tetto a 16, nessun altro carico sul server;
2. si accende il primo utente e il suo lavoro;
3. **10 minuti** di lavoro continuo (il carico è **cumulativo**: chi c'era continua);
4. **controllo** (§7) negli ultimi 2 minuti del livello;
5. si registra (§10), poi si sale al gradino successivo;
6. **all'ultimo gradino (16) il livello dura 30 minuti**, non 10: è la prova delle perdite di
   memoria a pieno carico, che coi gradini radi non si vede più salendo.

**La ricerca a metà**: se un gradino va in FAIL (dopo la ripetizione di §14), si prova a metà
fra l'ultimo gradino buono e quello rotto, e si stringe finché si sa l'ultimo livello GREEN
**preciso a un utente** (es. 8 buono, 12 FAIL ⇒ 10; 10 buono ⇒ 11; 10 FAIL ⇒ 9). Ogni livello
della ricerca riparte da scatola pulita coi suoi N utenti.

**Regola di non-prosecuzione**: se un controllo dice **DEGRADED significativo** o **FAIL**, non si
sale in automatico: il livello si osserva, si documenta, si diagnostica, si classifica e si
**ripete** nelle stesse condizioni (§14). Lo scopo non è arrivare a 16 a ogni costo.

⚠ Durata: 5 gradini (l'ultimo da 30 minuti) più 0–2 livelli di ricerca ≈ **1 ora e 10 per salita**.
Quattro desktop × due schede ≈ **9 ore** di misure nel caso migliore, ~35 con tutta la scala (§8),
contro le 24–96 del piano a un utente alla volta. Si fanno a blocchi, anche di notte.

## 7. Il controllo di ogni livello

**Il comportamento, misurato in ogni sessione:**

| che cosa | da dove |
|---|---|
| l'immagine si aggiorna | foto della tela di ogni browser a intervalli: cambia quando il lavoro cambia; nessun blocco lungo |
| fotogrammi dipinti, saltati, buchi | il diario della pagina (`dipinti`, `video X→Y`, `salt`, `buchi`) — mandato al server ogni 5 s, già esiste |
| **ritardo input → fotogramma** | quello che il prodotto misura dal suo lato (`SPECIFICHE` §3.2: **tetto 50 ms**, traguardo 40 ms), più una sonda dal browser di un utente-sentinella |
| l'input arriva | ogni lavoro batte e clicca: il suo effetto si vede (testo nel terminale, cartella creata) |
| l'audio (utenti D) | il diario della pagina (`suonati`, `BUCHI`, `mancati`) |
| nascita di un utente nuovo | tempo dall'accesso al primo fotogramma del nuovo utente |
| **controllo funzionale corto** | su UN utente per livello, a rotazione: accesso già fatto → input (F-004/F-007 ridotti) → immagine (F-003 ridotto) → appunti (F-014) — le funzioni certificate devono restare in piedi |
| errori | registro del server (RCP, WebTransport/QUIC, sessione), console dei browser, journal |

**Le risorse, per recinto** (cgroup di systemd: `remotix` · `sessioni` · `browser`):

| risorsa | misure |
|---|---|
| **processore** | totale, per recinto, per sessione; carico medio; processi e thread |
| **memoria** | totale, per recinto, per sessione (PSS); crescita nel livello (indizio di perdita) |
| **scheda grafica** | uso dei motori (disegno, video: codifica e decodifica) **per processo**, dal kernel (`/proc/<pid>/fdinfo` drm-engine); frequenza; temperatura; strozzatura. Intel: `intel_gpu_top` (da installare). AMD: fdinfo amdgpu, `radeontop` o `amdgpu_top` |
| **memoria video** | RX 6800: VRAM usata; Intel: memoria condivisa |
| **rete** | byte ricevuti/spediti per sessione (il registro QUIC di REMOTIX: `persi`, `spediti`, ritrasmissioni) |
| **REMOTIX** | sessioni vive, rifiuti, code del codificatore, fotogrammi abbandonati, «budget», tempi di nascita |

## 8. La scala delle misure

| gradino | misura dello schermo di ogni utente |
|---|---|
| 4K | 3840×2160 |
| 3K | 3200×1800 |
| 2K | 2560×1440 |
| Full HD | 1920×1080 |

Se un gradino arriva al **FAIL con N utenti**, il gradino successivo **riparte da 1 utente e
risale sugli stessi gradini** (§6): ogni misura ha la sua curva completa e confrontabile. Si scende finché si arriva a 16
nominali o si finisce la scala.

## 9. Le soglie — ✅ APPROVATE dall'utente il 25 set 2026 (sera), ora ferme

*Proposta del 25 settembre 2026. Un valore alto di una risorsa **da solo non è un FAIL**: la
classificazione nasce dal comportamento, e le risorse servono a spiegarlo.*

| misura (per sessione, nel controllo del livello) | **GREEN** | **DEGRADED** | **FAIL** |
|---|---|---|---|
| ritardo input → fotogramma (prodotto, p95) | ≤ 50 ms (il tetto di §3.2) | 50–150 ms | > 150 ms, o input perso |
| fotogrammi saltati dalla pagina | ≤ 2 % | 2–10 % | > 10 % |
| blocco più lungo dell'immagine con lavoro in corso | ≤ 1 s | 1–3 s | > 3 s, o immagine ferma |
| buchi nella catena del video (chiavi richieste) | 0 | ≤ 1 al minuto | > 1 al minuto |
| video 4K (utenti D): fotogrammi dipinti al secondo, **in proporzione alla frequenza del video scelto** (f) | ≥ 0,8·f | 0,4·f – 0,8·f | < 0,4·f |
| audio (utenti D): suono udibile | ≥ 99 % | 95–99 % | < 95 % |
| nascita di un utente nuovo (accesso → primo fotogramma) | ≤ 5 s | 5–15 s | > 15 s, o rifiuto |
| controllo funzionale corto | tutto PASS | — | un FAIL |
| sessione caduta, riavvio, errore RCP/QUIC che stacca | nessuno | — | uno qualunque |
| memoria dei recinti `remotix` e `sessioni` nel livello, a lavoro stabile (il recinto `browser` si **registra** ma non classifica: la cache di un Firefox che naviga cresce da sola) | crescita ≤ 5 % | 5–15 % (si segnala) | > 15 % e continua (perdita) |

**Quale ritardo classifica** — `[M]` diagnosi del 25 set sera (scatola xfce, 1 utente, terminale,
460 lettere; evidenze in `/media/REMOTIX/misure/fase16/diagnosi-eco/`). Il giro della pagina
(tasto → fotogramma che lo porta) in 4K fa **45 / 54 ms** (p50/p95), ma dentro c'è lavoro che non
è nostro:

| tratto (4K, p50/p95 ms) | | di chi |
|---|---|---|
| la pagina manda il tasto → il terminale lo riceve | 4,9 / 8,7 | **nostro** (limitato dal `poll` di 8 ms del figlio, `figlio.c` `MOVIMENTO_ATTESA_S`) |
| il terminale disegna l'eco | 10,2 / 16,6 | applicazione |
| il compositore compone e ce lo copia | 14,5 / 19,0 | compositore |
| conversione + codifica + spedizione → pagina | 14,0 / 14,9 | **nostro** |
| decodifica e disegno nel browser (fuori dal giro) | Firefox 38, Chrome 3,4 | browser |

⇒ Il **pezzo nostro** è ~19 / 24 ms, sotto il tetto di 50. Quindi, come dicono §7 («quello che il
prodotto misura dal suo lato») e la riga qui sotto («prodotto»): **classifica il ritardo del
prodotto** = p95 dei massimi al secondo della riga del figlio `TRATTO cattura → byte fuori` + 9 ms
(il tetto costruttivo del tratto d'ingresso). ⚠ Sulla strada wlroots quella riga conta la copia
due volte (~4 ms in più): è dal lato prudente e non si corregge durante la campagna. Il **giro della
pagina** (`giro_eco`, solo battitura) si **registra** come ritardo dell'esperienza e non classifica.
Candidata di cura per dopo la campagna: il socket del padre nello stesso `poll` del figlio
(~4 ms p50, ~8 ms p95).

**Il livello** è GREEN se **tutte** le sessioni sono GREEN; DEGRADED se almeno una è DEGRADED e
nessuna FAIL; FAIL se almeno una è FAIL. **DEGRADED significativo** = più di un quarto delle
sessioni DEGRADED, o una sola misura oltre metà della fascia DEGRADED.

## 10. Che cosa si registra

Come la fase 15, un **registro a sole aggiunte**, `banchi/16-stress/registro.jsonl`, una riga per
**livello** e una per **sessione in quel livello**:

`campagna` (es. `intel-4k-gnome`) · `livello` (1, 4, 8, 12, 16 e quelli della ricerca) · `utente` · `profilo` · `browser` e versione
· `desktop` · `scheda` e driver · `misura` · `commit` · binario · pagina · kernel · `inizio` ·
`durata_s` · tutte le misure di §7 · `classe` (GREEN/DEGRADED/FAIL) · `ragione` · `evidenze`.

Le **evidenze** stanno sul server in `/media/REMOTIX/misure/fase16/<campagna>/livello-NN/`: foto
di ogni tela, diario delle pagine, registro del server e journal tagliati sul livello, le serie
delle risorse (una riga al secondo), console dei browser. Devono bastare a dire **che cosa
succedeva** nel momento della degradazione.

Il **rapporto** si genera dal registro (come `15-rapporto.py`): la curva di ogni campagna, la
matrice finale, i colli di bottiglia.

## 11. Le due campagne

| | Intel integrata | Radeon RX 6800 |
|---|---|---|
| scheda | Intel UHD 770 (i5-13500T) | AMD RX 6800, 16 GB |
| codifica | VA-API, iHD (`[M]` fase 11) | VA-API, radeonsi — ⚠ **mai provata**: prima un accesso con un utente, che il codificatore AMD parta davvero |
| ordine | GNOME, KDE, XFCE, LXQt | stesso ordine, stesse condizioni |
| si registra | CPU, GPU, driver, RAM, kernel, distribuzione, browser, misura, rete, commit | idem, più VRAM |

⚠ Il server ha la radice in RAM: montare la scheda vuol dire un riavvio, e il riavvio perde
chiave ssh e pacchetti (`riavvio-perde-la-chiave-ssh`) — la ricetta è pronta.

**La matrice finale:**

| desktop | Intel iGPU | Radeon RX 6800 |
|---|---:|---:|
| GNOME | ultimo livello GREEN · punto di rottura · gradino | idem |
| KDE | … | … |
| XFCE | … | … |
| LXQt | … | … |

Ogni casella rimanda alla sua salita nel registro. Il confronto Intel/Radeon si fa **sui dati**:
livello nominale, degradazione, CPU, RAM, GPU, VRAM, rete, errori, tempi di nascita e primo
fotogramma, stabilità — senza conclusioni oltre quel che i dati mostrano.

## 12. Il journal di sistema (lavoro da fare prima)

Oggi REMOTIX scrive su un file suo (`registro.log`, dallo standard output). Nella fase 16:

- il registro va nel **journal** (`journalctl -u <unità>`), con i campi strutturati utili
  (area, inquilino, livello di gravità) — il file resta solo se chi amministra lo chiede;
- eventi: avvio/arresto, sessioni, trasporto, orologi, rientri, RCP, codifica, input, permessi,
  configurazione, anomalie;
- ⛔ **mai** parole d'ordine, gettoni, chiavi, contenuto dello schermo o dell'input (le battute
  si registrano come «tasto», mai come carattere).

## 13. Prima della campagna

0. **server riavviato** (deciso dall'utente il 25 set, per partire puliti), `/media` intatto:
   la radice in RAM va rifatta coi passi 0, 1, 5, 6 e 7 della ricetta
   (`riavvio-perde-la-chiave-ssh`: rotta, chiave, pacchetti dell'ospite, `provisiona.sh`,
   `storage.conf` e le quattro scatole) — contenitore di compilazione, librerie e immagini stanno
   su `/media` e restano; poi si **guarda** che il server sia vuoto (niente processi, inquilini,
   compositori rimasti) prima della prima misura;
   `[M]` **fatto il 25 set sera**: radice verificata da `provisiona.sh verifica`, scatole su
   `b1443a0b`/`c5279e66`, fumo F-001/F-002 **16 PASS su 16** (4 desktop × 2 browser). Alla
   ricetta mancavano tre pezzi, ora aggiunti: `labwc` e `wlr-randr` (dalla cache apt),
   Chrome (`/media/REMOTIX/cache/chrome.deb`) e `~/SERVER.ssh` sul server (0600: la suite ci
   legge la parola di sudo — la copia la fa l'utente);
1. il journal (§12) e il tetto configurabile, con la **suite corta di regressione** della fase 15
   (accesso, input, immagine, appunti, «Esci», orologi — sui 4 desktop coi due browser) su quel
   commit;
2. l'impianto: 16 compositori, i tre recinti, le serie delle risorse, i quattro lavori
   automatici, il controllo funzionale corto, il registro e il rapporto — ogni pezzo **con la
   sua prova**, come nella suite (un misuratore che non ha mai dato rosso non misura);
3. una **salita di prova** corta (4 utenti, 3 minuti a livello) per tarare l'impianto, che non
   conta;
4. le soglie di §9 **approvate dall'utente**.

## 14. Anomalie e ripetizioni

1. preservare le evidenze; 2. non cambiare niente subito; 3. analizzare; 4. cercare la causa;
5. **ripetere nelle stesse condizioni**; 6. confrontare. Se REMOTIX cambia: nuovo commit, suite
corta di regressione, e **si rifà la salita interessata**. Un FAIL resta legato alla sua
configurazione (desktop, scheda, commit, lavoro, utenti, sintomo) e non si generalizza.

### Anomalia A1 — Firefox in 4K salta i fotogrammi già con un utente (25 set, notte)

`[M]` salita di prova (GNOME 4K, 1 utente, Firefox cliente): 489 consegnati, 433 dipinti, **11,5 %
saltati ⇒ FAIL** già al primo gradino; Chrome nelle stesse condizioni 3–6 %. Diagnosi (evidenze in
`/media/REMOTIX/misure/fase16/diagnosi-ff-hw/`): il Firefox cliente decodifica **già in hardware**
(VA-API, 2,3 ms di motore video a fotogramma, come Chrome); il collo è la strada di disegno della
pagina: in Firefox 140 `createImageBitmap(VideoFrame)` fa una **rilettura sincrona dalla GPU**
(~34 ms a 4K, sul thread principale, bug Mozilla 1788206), la coda del decodificatore supera 2 e la
pagina salta (`saltati_coda`). Con la decodifica software si scende al 12 %, ancora sopra il 10.
⇒ È un limite del **prodotto con Firefox in 4K** (la pagina), non del server né del carico: la
campagna lo misura così com'è, e al 4K ogni gradino con un utente Firefox ne risente.
Cura candidata, da misurare dopo la campagna: disegno con **WebGL2 `texImage2D(VideoFrame)`**
(via DMA-BUF senza rilettura in ESR 140; stima < 2 ms), banco pronto in
`banchi/16-stress/16-banco-tela.html` (vie `bmp` e `gl`, criteri: disegno < 3 ms, saltati < 5 %, e
la foto del vetro col testimone per escludere i blocchi della 2D).

### Anomalia A2 — in LXQt il terminale apre `dash`, non la shell dell'utente (27 set)

`[M]` Il profilo C su LXQt non lavorava: qterminal apriva **`/bin/sh` (dash)**, senza `.bashrc`
né storia. Causa (corretta il 28 set, `[M]` su una sessione XFCE viva): fuori da GNOME le sessioni nascono **senza `SHELL`** — l'ambiente si compone da zero e non la mette; su GNOME è **`SHELL=` vuota** di proposito (`src/sessione.c`
~1682, `src/figlio.c` ~1159 — voluta per la trappola della shell di login di `gnome-session`), e
qtermwidget senza `SHELL` ripiega su `/bin/sh`; thunar/xfce4-terminal, konsole e gnome-terminal
leggono la shell da passwd e non se ne accorgono. ⇒ **È un difetto funzionale del prodotto**
(un utente LXQt che apre il terminale non trova la sua shell), che la fase 15 non ha visto: è
**D-022**, da curare DOPO la campagna (la trappola è solo di GNOME: fuori da GNOME, `SHELL` dalla
riga di passwd) con la sua prova nella suite. Per non fermare la campagna su un difetto che non
tocca la capacità, l'attore apre `qterminal -e bash` — **dichiarato**, ed è l'unico punto in cui
il banco non usa il prodotto come lo userebbe una persona.

### Anomalia A3 — Radeon, 4K: ritardo a picchi e tela larga 3824 senza immagine (27 set)

`[M]` `amd-4k-gnome` (binario 45d048c8, Radeon RX 6800, radeonsi 25.0.7), **1 utente**:
- **ritardo**: NOSTRO mediana **9,1–9,3 ms** ma p95 dei p95 **45–50 ms** (max 60 ms), sulla Intel
  allo stesso livello restava verde fino a 3 utenti ⇒ DEGRADED a 1 utente, due volte. Il lavoro
  normale è veloce; sono picchi. `[?]` Chi li fa (codifica VCN, la copia dalla scheda, il
  compositore): da misurare dopo la campagna, prima di giudicare la Radeon in 4K.
- **tela 3824 × 2064**: il controllo con **Chrome** (finestra 3840×2073, tela 3824) non ha mai
  avuto un fotogramma: 99 volte «il flusso MOSTRA 3840x2064 … la tela è 3824x2064» e 99 volte «il
  codec 1 non ha consegnato il fotogramma dalla SCHEDA». Mutter ha dato un monitor largo 3840
  invece dei 3824 chiesti, e il figlio rifiuta la misura diversa. Con Firefox (altra larghezza)
  il controllo passava. Sulla Intel lo stesso Chrome nasceva. ⇒ **difetto funzionale del
  prodotto** sulla Radeon (una tela larga non multipla di 64 resta nera): **D-023**, da curare
  dopo la campagna con la sua prova nella suite. Evidenze:
  `misure/fase16/amd-4k-gnome/livello-01-ripetizione/journal-err.jsonl`.
  ⭐ **Causa e cura, 27 set**: non è Mutter, è il **driver** — `hevc_vaapi` su radeonsi dichiara
  nel flusso il multiplo di 64 senza finestra di conformità (lo fa anche `ffmpeg` da riga di
  comando: 2544 → 2560), mentre H.264 sulla stessa scheda è giusto; Chrome sceglie HEVC. La
  cura scrive la cornice nell'SPS con `hevc_metadata` (§17.1). ⇒ **Tutte le sessioni Chrome
  della campagna Radeon col binario 45d048c8 sono nere per D-023**: quei gradini misurano il
  difetto, non la capacità, e si rifanno col binario curato.

### Anomalia A4 — il PageDown «perso» su KDE era dell'attore (27 set)

`[M]` A 1 utente, su tutte le campagne fatte: **KDE 14 PageDown senza effetto su 49** (Intel e
Radeon), gli altri desktop **0 su 172**; clic, battitura e rotella su KDE: 0 persi. Il tasto
**arriva** al server (`POSIZIONE_TASTO` premuto e rilasciato nel registro). Tutti i persi
vengono **dopo una rotella** (o dopo un altro PageDown perso); dopo un clic o una navigazione,
mai. Causa: `aspetta()` dell'attore tornava alla prima riga buona e perdeva le posizioni dopo,
quindi dopo una rotella credeva la pagina a metà mentre era in fondo, e sceglieva PageDown su una
pagina che non poteva scendere. Su KDE la rotella sposta di più (`scroll_discrete`, 144 unità) e
il fondo si tocca più spesso. ⇒ **Difetto del banco, non del prodotto**; cura in §17.2. Ha fatto
FAIL `amd-freq-*` e ha pesato su `intel-b-4k-kde` e `amd-4k-kde`. ⚠ Le frecce su/giù che
l'utente aveva notato a mano restano una domanda separata: questo banco non le prova.
`[M]` **Verifica, 27 set sera** (`amd-b-4k-kde`, attore curato): 10 PageDown, **0 persi**; il
gradino da 1 utente cede ora solo per il ritardo (A3, NOSTRO p95 ~41 ms + 9), non più per input.

### Anomalia A3, seconda metà — il ritardo della Radeon NON è la frequenza (27 set)

`[M]` KDE 4K, 1 utente, binario 28a947f5, due gradini per condizione: NOSTRO p95 dei p95
**39,3 / 38,6 ms** con `power_dpm_force_performance_level=auto`, **37,5 / 42,0 ms** con `high`;
mediana 8,8 ms in tutti e quattro. ⇒ Ipotesi smentita; la scheda è tornata su `auto`. `[?]`
Resta da capire da dove vengono i picchi (la codifica ha mediana dei p95 ~20 ms).

`[M]` **Dove stanno i picchi** (registro del server, `amd-freq-auto/livello-01`, 3322 fotogrammi):
la codifica è bimodale — mediana **8,7 ms**, p99 **31 ms** — e i lenti arrivano **a gruppi di 5
consecutivi da 31 ms**, ogni 12–40 s, su delta piccolissimi (300–1500 byte); la Intel sullo stesso
lavoro: p99 8,7 ms, max 10,4. 11 gruppi su 13 cominciano entro 1,5 s da un'azione che fa
ridisegnare la pagina (clic, rotella, tasto). `[?]` **Ipotesi**, da verificare: su radeonsi la
conversione RGB → NV12 del VPP gira sugli **shader** (coda grafica), in fila dietro al
ridisegno del desktop della sessione; sulla Intel la fa un blocco dedicato (VEBOX). Se è così,
la cura candidata è una priorità alta per il contesto VPP, o la conversione dentro il
codificatore dove la scheda lo permette. I tempi sono presi dalla chiamata di codifica, che
comprende l'attesa del VPP.

⛔ **Ipotesi SMENTITA, 29 set** (agente a refutare, sorgenti di Mesa 25.0.7 e registri):
- su radeonsi il VPP **non converte**: dal 16° fotogramma `postproc.c` registra la sorgente RGB e
  torna (EFC), e la conversione RGB→NV12 la fa il **VCN dentro la codifica** leggendo il buffer
  lineare del compositore (conversione misurata 0,03 ms, contro 8,6 ms di VEBOX sulla Intel);
- i gruppi sono **sempre 5 fotogrammi** (64 su 64), ~8,7 + 22 ms, **qualunque la dimensione**
  (300 B come 480 KB) e **anche distanziati nel tempo** (un gruppo su GNOME dura 1,2 s): conta
  fotogrammi, non tempo;
- **per sessione**: in `amd-b-4k-kde` u99 fa 5×31 ms mentre u1, sulla stessa scheda e lo stesso
  VCN, codifica a 8,5 ms negli stessi istanti; scheda grafica al 2–6 %.
  ⇒ Niente coda comune, niente priorità da alzare. `[?]` Candidate: l'attesa implicita sul buffer
  del compositore di quella sessione, il buffer lineare da 30 MB in memoria di sistema (GTT), o
  lo stato del contesto VCN. **Esperimenti proposti**: (1) misurare prima — attesa esplicita della
  barriera del DMA-BUF (`DMA_BUF_IOCTL_EXPORT_SYNC_FILE`) fuori da «codifica», e codifica divisa
  in invio/ricezione; (2) spegnere l'EFC (un `vaProcess` in più all'apertura: Mesa lo disattiva
  per sempre) così il VCN legge una NV12 in VRAM, al costo di ~1–2 ms di copia. Da fare prima di
  giudicare il 4K della Radeon.

`[M]` **I due esperimenti, 29 set mattina** (ramo `a3-esperimenti`, commit `18b6437`, binari
`3e510160` e `39e3ed86`; KDE 4K Radeon, 1 utente, due gradini ciascuno; evidenze
`misure/fase16/a3-misura-kde`, `a3-senza-efc-kde`):
1. **la barriera del compositore NON c'entra**: aspettata esplicitamente e misurata a parte, vale
   0,37 ms sui fotogrammi normali e **0,02 ms su quelli lenti**; e i 22 ms in più stanno **tutti
   dentro `avcodec_send_frame`** (ricezione 0,0 ms): con `async_depth=1` è il VCN che codifica;
   ancora 100 e 105 fotogrammi lenti per gradino;
2. **l'EFC NON c'entra**: spento (conversione vera, 0,75 ms mediana), i gruppi da 5 × 31 ms restano
   identici — 95 e 106 lenti per gradino, codifica p99 31,1–31,3 ms.
⇒ Il ritardo è **dentro la codifica del VCN** della Radeon, una sessione per volta, 5 fotogrammi
ogni 12–40 s. Resta da provare: le superfici con il tiling della scheda (invece del lineare), la
codifica in un contesto nuovo; e, se nessuna delle due, è un comportamento del driver/firmware da
segnalare a Mesa con la scena riprodotta. Il 4K della Radeon nel riepilogo resta con questa riserva.

`[M]` **Gradino 1 (29 set 2026): Mesa 26.1.6 non cura.** Scatola KDE con Mesa 26.1.6 da
`trixie-backports`, stesso binario `4fb3287d`, KDE 4K Radeon 1 utente, due gradini da 6 min
(`a3-mesa26-kde`): **100 e 102** codifiche > 20 ms (con 25.0.7: 100 e 105), a raffiche di 5, mediana
31,0 ms. ⇒ Il manuale NON può dire «Radeon: serve Mesa ≥ X»; il prossimo passo per chi vuole aiutare
il driver è la riproduzione minima senza REMOTIX (dossier §6.2). La scatola è tornata a Mesa 25.0.7
(ricostruita dall'immagine).

✅ **Decisione dell'utente, 29 set 2026**: *«è fuori dal nostro ambito»* — A3 **non si aggira** in
REMOTIX; si documenta nei minimi particolari per poterlo portare agli sviluppatori del driver:
**`fasi/16-a3-radeon-vcn.md`** (macchina, catena, misure, ipotesi escluse, riproduzione, bozza del
rapporto per Mesa). Il 4K della Radeon nel riepilogo è limitato dal driver, e lo si dichiara.

### Nota A5 — KDE Full HD sulla Radeon: il video dell'utente 4 si ferma 1–3 s (28 set, notte)

`[M]` `amd-b-fhd-kde`, livelli 12 e 16: l'unico DEGRADED è l'utente 4 (profilo D, video 4K,
Chrome), «blocco più lungo dell'immagine» 1,1–2,7 s, mentre i fotogrammi **arrivano e si
dipingono tutti** (6622 consegnati = 6622 dipinti, 0 buchi). Lo stesso utente su GNOME Radeon
(0,11 s) e su KDE Intel (0,08 s) è verde ⇒ **non è la cura D-023** (attiva anche su GNOME). `[?]`
Ipotesi: il lettore video dentro la sessione KDE si ferma (l'immagine arriva ma non cambia). Da
guardare dopo la campagna, prima di chiudere KDE Full HD Radeon a 15.

⭐ **Chiusa, 29 set (agente a refutare, registri dei livelli)**: è il **riavvio del file del video**.
Il lettore gira il file da ~634 s con `loop`; ogni blocco dell'utente 4 cade a t≈630–634 o t≈0–6 s
del lettore, ogni ~10,5 min, e il lettore stesso conta 60–90 fotogrammi persi a ogni giro. Lo
stesso succede su GNOME Radeon (2,8–4,4 s) e KDE Intel (1,5 s): KDE Radeon era DEGRADED solo
perché le sue finestre di giudizio cadevano sul giro. Lato nostro, nel buco: la cattura gira
(«attese a vuoto» +123/s), i fotogrammi consegnati restano fermi (il compositore non dà danno),
nessuna chiave richiesta, rete pulita; i buchi al server coincidono al millisecondo con quelli
dell'attore (2,685 contro 2,68 s). ⇒ **Non è REMOTIX**, è il banco. Cura del banco (non fatta):
un file più lungo del livello (`ffmpeg -stream_loop`, senza ricodifica), o le righe attorno al
giro dichiarate ed escluse. Sul riepilogo pesa poco: tocca il numero severo di KDE Full HD Radeon.
⭐ **Cura del banco fatta, 29 set**: `video/bbb_sunflower_2160p_30fps_x4.mp4`, lo stesso file
concatenato 4 volte senza ricodifica (`ffmpeg -stream_loop 3 -c copy`, 2538 s = 42 min, sha256 in
`video/SHA256SUMS`), più lungo di qualunque livello; `16-coda.sh` lo usa di serie. `[M]` provato
il 29 set (`a5-video-lungo-kde`, KDE Full HD Radeon, 4 utenti, 12 min: col file vecchio il giro
sarebbe caduto a 10,5 min, dentro la finestra 10–12): utente 4 **GREEN, blocco 0,08 s**, livello
tutto GREEN (5 su 5).

### Le frecce su/giù (segnalate dall'utente a mano) — studio del 29 set

Lettura del codice (agente), **nessuna prova ancora**. Le frecce passano da `POSIZIONE_TASTO`, che
tiene uno stato in pagina e nel server (le lettere no): un difetto di stato colpisce le frecce e
risparmia la battitura. Meccanismi in ordine: (1) in pagina un rilascio perso lascia il codice in
`cl_tasti_premuti` e la pressione dopo si scarta in silenzio (`cl_su_keyup` torna subito quando
`cl_nel_modulo`); (2) su Mutter/KWin la tastiera di libei in pausa o ricambiata
(`tastiera_attiva` falso) scarta la pressione; (3) fra padre e figlio il socket non bloccante
scarta un input su `EAGAIN` quando il figlio è in ritardo; (4) le frecce del tastierino con
BlocNum spento arrivano come KP_8/KP_2; (5) tasti scartati come composizione IME. `[M]` nei
registri di tutta la campagna: **0** input non partiti verso il figlio, **1** ricambio di
tastiera (u2). Prossimo passo: la prova mirata di 200 frecce con i conti di pagina e server.

## 15. Limiti dichiarati

- **il server fa anche da cliente**: il risultato è un limite inferiore (§2);
- **la rete non è misurata**: browser e server sulla stessa macchina. Come REMOTIX regge una rete
  che perde pacchetti (`[M]` 0,6 % sul Wi-Fi a 2,4 GHz, fase 15) è una domanda a parte, da
  aggiungere dopo (strozzatura dal tablet, `wondershaper-sul-tablet`);
- **YouTube** è un servizio esterno: se cambia, si passa al file locale dichiarato (§5);
- la **prova oltre 16** è sovraccarico, fuori dalla certificazione.

## 16. Criterio di successo dei 16 utenti

Per **una** configurazione, il requisito è verificato quando: 16 sessioni vere sono attive
insieme · ognuna col suo lavoro · chi c'era continua · il controllo dei 16 è completo e **GREEN**
secondo §9 · le evidenze sono raccolte · il risultato è legato a un commit · la salita è
riproducibile o documentata abbastanza da rifarla.

⚠ **Gli orari**: i registri del server, le cartelle delle misure e le righe `[hh:mm:ss]` delle salite
sono in **UTC** (il server non ha un fuso impostato); l'ora italiana (CEST, settembre) è **UTC + 2**.

## 17. Le modifiche della fase 16 — il registro per il manuale tecnico

*Richiesta dell'utente, 26 set 2026: ogni modifica si annota qui, perché a fine lavori se ne scrive
il **manuale tecnico** di REMOTIX. Una riga per modifica: che cosa, perché, la misura, il commit, e se
è **installata** (nel binario o nella pagina delle scatole) o no. Le decisioni dell'utente stanno in
`DECISIONI.md` §9.*

### 17.1 Il prodotto (`src/`)

| commit | che cosa | perché | misura | installata |
|---|---|---|---|---|
| `62753e7` | **registro nel journal** (`--journal`): protocollo nativo del journal, una `sendmsg` per riga, non bloccante; campi `REMOTIX_AREA`, `REMOTIX_INQUILINO`, `CODE_FILE`, `CODE_LINE`, `SYSLOG_IDENTIFIER=remotix`; gravità 3/4/6 dal segno ⛔/⚠ in testa al corpo; la parlantina NON va al journal; il figlio lo riceve dal padre (`argv[16]`) | §12, DECISIONI §9.1 | 33 righe su 33 con i campi; stderr identico senza l'opzione | sì, da `bdde6bb1` |
| `62753e7` | **l'input non si scrive**: `rcp.c` (e il gemello `banchi/rcp/rcp.c`), `tastiera.c`, `input.c` — niente `U+XXXX` né codici di tasto, salvo modificatori e pulsanti | §12, DECISIONI §9.2 | audit di tutte le chiamate `registro_*` | sì |
| `62753e7` | `Makefile`: ogni oggetto dipende da `registro.h` | `registro.h` è diventato di macro (`__FILE__`/`__LINE__`) e una costruzione a metà non collegava | — | — |
| `ebc9dcd` | **riga «NOSTRO nel secondo»** del figlio: p95, massimo e mediana di *copia → byte fuori* sui soli fotogrammi di quel secondo | la riga TRATTO usa un anello di 512 fotogrammi (un picco resta dentro 8–17 s) e comincia dal `pts` del compositore; §3.2 chiede il **pezzo nostro** | diagnosi del giro in 4K: nostro ~19/24 ms su 45/54 (§9, «Quale ritardo classifica») | sì, da `4cba76f6` |
| `97e94fe` | **entrypoint del codificatore scelto sulla capacità dichiarata** dal driver: `EncSliceLP` se c'è (Intel, identico), se no `EncSlice` piena (radeonsi), dichiarato; il software solo se non c'è nessuno dei due | la Radeon non ha la bassa potenza ⇒ il prodotto codificava in software | Radeon: «in HARDWARE · radeonsi · EncSlice, piena», NOSTRO p95 17–29 ms | sì, `3fe94e8b` (binario della campagna Intel) |
| `86598d6` | **primo fotogramma della scheda giudicato a campione** (griglia 64×64, tetto 250 ms) invece di leggere tutta la lastra DMA-BUF | su una scheda discreta la lastra è in VRAM: leggerla dalla CPU costava **63,7 s** e la sessione non nasceva | `[M]` 26 set, Radeon, XFCE e GNOME 4K: **5,7–6,2 ms** (prima 63,7 s), codifica `h264_vaapi` in HARDWARE su radeonsi, sessioni GREEN | sì, `45d048c8` |
| `ea0f82a` | **strada di disegno WebGL2** nella pagina (`?tela=gl`): `texImage2D(VideoFrame)` sincrono, `close()` subito, quad a schermo intero, stessi contatori | anomalia A1: in Firefox `createImageBitmap(VideoFrame)` rilegge dalla GPU (~34 ms a 4K) ⇒ 11–50 % saltati con 1 utente | da misurare; poi sguardo dell'utente contro i quadrati (DECISIONI §9.4) | **no** (candidata) |

| (questo commit) | **la regola del salto pesata col costo del disegno**: si salta il disegno se `coda > 2` **e** `coda × costo_disegno() > 16 ms` (costo = mediana della parte sincrona del richiamo, + il vetro sulla strada asincrona); più i contatori `cq`/`cu` (coda alla consegna e all'uscita), `dec8`, `eta`, `ric` nel diario | la regola «coda > 2» (14 ago 2026) salvava i 34 ms del disegno 2D; con WebGL (0,26 ms) non salva niente e buttava il 12 % | Firefox di serie: salta come prima (15 = i fotogrammi a coda ≥ 3), ritardo invariato (36,8 ms); Chrome e WebGL: non scatta; da validare su KDE 4K con `?tela=gl` | **no** |

| (questo commit) | **WebGL2 diventa la strada di disegno di serie** per tutti i browser; `?tela=bmp` (o `2d`, `desincronizzata`) rimette le strade di prima per confronto; senza WebGL2 la pagina ripiega su `bitmaprenderer` e lo scrive | anomalia A1; DECISIONI §9.4 | giudizio dell'utente allo schermo (KDE, Firefox, video 4K e acquario WebGL a 30 000 pesci): «l'immagine è perfetta: qualità ottima, 45 fps costanti, nessuno scatto» — niente blocchi 64×192 | dopo la suite corta |

| (questo commit) | **D-023, la cornice che il driver non scrive**: se il primo SPS di un contesto dichiara una misura più grande della tela di meno di un blocco (64), `codificatore.c` fa passare i pacchetti con l'SPS (le chiavi) da `hevc_metadata`/`h264_metadata` con `crop_right`/`crop_bottom`, e lo dichiara (riga «⭐ D-023»); qualunque altra differenza resta rifiutata da `forma_va_bene()` | anomalia A3: sulla Radeon (radeonsi 25.0.7) `hevc_vaapi` dichiara il multiplo di 64 senza finestra di conformità (anche da `ffmpeg` a riga di comando) ⇒ ogni sessione HEVC — Chrome — a una tela non multipla di 64 restava **nera** | `banchi/16-stress/16-d023-cornice.sh`, 4 tele vere × 2 codec: Radeon **8 PASS** (PSNR 47 dB, l'immagine è 1:1), senza la cura **HEVC 4 FAIL su 4**; Intel 8 PASS, la cura non scatta mai | **sì**, binario **`28a947f5`** (da `678a2da`), 27 set: suite corta sulla Radeon, 4 desktop × 2 browser, **352 PASS su 352**; nei registri delle scatole la cura è scattata 62 volte, 0 flussi rifiutati |

| (questo commit) | **D-022, la `SHELL` fuori da GNOME**: `sessione.c`, in coda all'ambiente della sessione, `SHELL` dalla riga di passwd dell'utente per KDE, XFCE e LXQt (GNOME resta vuota: trappola di `gnome-session`); senza shell in passwd lo dice | anomalia A2: `[M]` in una sessione XFCE viva `labwc` e `xfce4-panel` senza `SHELL`, `systemd --user` con `/bin/bash`; qterminal ripiegava su `/bin/sh` | `banchi/15-suite/15-f032-la-shell-dell-utente.py` (F-032): sui 4 desktop la `SHELL` della sessione (vuota su GNOME), e su LXQt `qterminal` lanciato con l'ambiente del pannello apre `bash`: **4 PASS**, guasto rosso sui 4; col binario di prima (28a947f5) LXQt **FAIL** («SHELL della sessione None») | **sì**, binario **`4fb3287d`**, 29 set (dopo la campagna); suite corta con F-032 in parallelo sui 4 desktop: 328 PASS, 4 FAIL, 36 BLOCKED — le 16 combinazioni rosse **rifatte una alla volta: 16 su 16 PASS**. I rossi erano quasi tutti «utente o parola d'ordine non corretti» con `pam_unix: user unknown` per un inquilino creato 7 s prima (`[M]` gnome 04:40:04 creato, 04:40:11 sconosciuto) e solo col giro in parallelo: `[?]` difetto del banco o dell'ambiente, da capire; il 26 set lo stesso giro era 352/352 |
**Binario e pagina della campagna nuova** (da `e4e05dc`): binario **`45d048c8`**, pagina **`fb9a18f3`** —
suite corta estesa (accesso, input, immagine, appunti, «Esci», orologi, più tela all'attacco, video,
stacco e riattacco, riattacco a misura diversa; 4 desktop × 2 browser): **352 PASS su 352**, 26 set.

### 17.2 L'impianto di prova (banchi e scatole)

| commit | che cosa | perché |
|---|---|---|
| `8e7f9ec` | `11-accendi.sh server`: `--journal` e il tetto da `REMOTIX_TETTO_SESSIONI` | §12 e §2 (tetto a 17) |
| `87f614e` | `11-accendi.sh accendi`: `REMOTIX_SCHEDA=intel|amd`, una scheda sola dentro la scatola | campagna Radeon (§11) |
| `8f7bbd8` | i nodi della scheda entrano **anche col nome vero** quando non sono `card0`/`renderD128` | `[M]` libdrm ricostruisce il nome dal numero del nodo: senza quel nodo il compositore non annunciava il DMA-BUF e la VA-API non si apriva (Radeon: 205 ms → 17–29 ms) |
| vari | `banchi/16-stress/`: attore, risorse, classifica, salita, controllo corto, compositori, coda, rapporto, banco della tela | l'impianto di §4–§10; corretto dopo una revisione avversaria (6 difetti) e dopo le prime salite vere (§14) |
| (questo commit) | lavoro C su LXQt: `qterminal -e bash`, e l'attore controlla la shell sotto il terminale | anomalia A2 (D-022, difetto del prodotto: `SHELL=` vuota ⇒ dash) — aggiramento dichiarato del banco, la cura del prodotto è dopo la campagna |
| (questo commit) | lavoro B su LXQt: la cancellazione è Maiusc+Canc e «y» (pcmanfm-qt: il Canc del menu non scattava; «No» è il bottone predefinito del dialogo), foto al fallimento | `[M]` 27 set: «input perso: cancella» dava FAIL a LXQt già a 2 utenti — difetto del banco, non del prodotto; le salite LXQt 4K e 3K si rifanno |
| `07-b46` | `REMOTIX_FF_PREFS`: preferenze in più nel profilo Firefox dei banchi | per ripetere una misura con la decodifica software |
| (questo commit) | `16-lavori.py`, attore A: `aspetta()` legge TUTTO il gruppo di righe del quaderno prima di tornare, e prima di scegliere rotella o tasto l'attore rilegge la posizione | anomalia A4: il PageDown «perso» su KDE era dell'attore (posizione vecchia, pagina già in fondo). In vigore sul server dalle **13:58 UTC del 27 set**, cioè dal secondo utente di `amd-b-4k-gnome` in poi (l'utente 01 di quel gradino è partito alle 13:55 col codice di prima) |

### 17.3 L'ambiente del server (volatile: rootfs in RAM)

Alla ricetta di rifacimento dopo un riavvio si aggiungono: `labwc`, `wlr-randr`, Chrome da
`/media/REMOTIX/cache/chrome.deb`, `~/SERVER.ssh` (0600) sul server, `loginctl enable-linger nicfio`
(la coda notturna vive senza sessioni ssh), e l'unità della coda con `TimeoutStopSec=1200`,
`KillMode=mixed`, `OOMPolicy=continue`.

⛔ **Il blocco del 28 set, 08:42 (06:42 UTC)**: `amd-b-3k-xfce`, gradino da 16 utenti (17 sessioni
e 17 browser-cliente sulla stessa macchina): la RAM è finita, il killer del nucleo uccideva Chrome
a ripetizione fra stalli RCU, e il sistema è rimasto **incastrato** — ping sì, ssh e REMOTIX no —
finché l'utente lo ha riavviato. Evidenze: foto della console (utente), l'ultima riga della salita
«controllo corto: BLOCKED» alle 06:41:49 UTC. ⇒ Due cambi d'ambiente, dal 28 set 09:05:
- **swap da 16 a 32 GB** (l'utente, sul disco): non cambia i limiti misurati, che cadono dove la
  RAM finisce; allunga il tempo prima del killer;
- **`earlyoom`** (`/etc/default/earlyoom`: `-m 5 -s 100 -r 60`, preferisce i processi di Chrome e
  Firefox, evita `remotix`, `systemd`, `sshd`, `podman`, `conmon`, i compositori, `python3`): con
  la RAM disponibile sotto il 5 % chiude un browser **prima** che la macchina si incastri. Un
  browser chiuso è un FAIL di quel livello, com'era prima; la differenza è che la notte continua.
  ⚠ Va nella ricetta dopo ogni riavvio (il rootfs è in RAM).

