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
