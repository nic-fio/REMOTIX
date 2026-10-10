# Fase 20 — Le prestazioni, da capo

*Piano scritto il **5 ottobre 2026**, mentre girava il banco NVIDIA. ⛔ **Da approvare dall'utente prima di
qualunque misura** (`fasi/19-nvidia.md` §6: *«la campagna di prestazioni si rifà da zero, una volta, a
architettura finita, con un piano approvato prima dall'utente»*). Parte **dopo** la NVIDIA: se la NVIDIA
trova un difetto nella strada Vulkan, la cura tocca anche la Radeon, e le misure fatte prima andrebbero
buttate.*

---

## 1. La domanda, e le due cose nuove

La domanda resta quella della fase 16: **quanto carico regge REMOTIX continuando a funzionare?** Le misure
della fase 16 sono state tolte dai documenti (DECISIONI §10.26: *«con questo cambio architetturale i numeri
sono completamente invalidati»*): da allora REMOTIX non usa più ffmpeg (fase 18), codifica solo sulla scheda e
sulla Radeon passa da Vulkan (fase 19).

Due cose nuove rispetto alla fase 16:

1. **Il risultato diventa la tabella pubblica** (DECISIONI §10.30, *«la capacità si dichiara, non si
   limita»*): per ogni macchina misurata, una riga **«uso ottimale fino a X utenti, degrado da Y»**. «Ottimale»
   = l'ultimo livello GREEN di §5; «degrado» = il primo DEGRADED.
2. **Due strade, due curve**: Intel = **VA-API**, Radeon = **Vulkan** (risposta dell'utente, 4 ott: *«sono due
   strade del prodotto, ognuna coi suoi numeri»*).

## 2. Che cosa si riusa così com'è (approvato il 25 set, fase 16)

Il metodo della fase 16 si riprende **senza cambiarlo**, perché era già approvato e perché così i numeri
nuovi si confrontano coi vecchi dove serve:

| pezzo | fase 16 | qui |
|---|---|---|
| l'impianto | browser veri sul server, un `labwc` per utente, input dal browser | uguale (§4 della 16) |
| i quattro lavori | A navigazione · B file manager · C terminale · D video 4K, a rotazione | uguale (§5 della 16) |
| la salita | gradini **1 → 4 → 8 → 12 → 16**, 10 min a gradino, 30 min all'ultimo, ricerca a metà | uguale (§6 della 16) |
| il controllo | ritardo, fotogrammi, blocchi, video, audio, nascita, controllo funzionale corto, memoria | uguale (§7 della 16) |
| la scala | 4K → 3K → 2K → Full HD se il 4K va in FAIL | uguale (§8 della 16) |
| **le soglie** | GREEN / DEGRADED / FAIL | ⛔ **uguali, e non si toccano** (§9 della 16) |
| registro e rapporto | `banchi/16-stress/registro.jsonl`, rapporto generato | uguale, campagne nuove `f20-*` |

## 3. I passi

0. **Il server riavviato e rifatto pulito** (la risposta di Claude all'utente, 5 ott: il riavvio conviene
   qui, non prima). Radice in RAM rifatta con la ricetta (`provisiona.sh`, chiave, pacchetti, le 4 scatole),
   poi si **guarda** che sia vuoto: niente processi, inquilini, compositori rimasti.
   ⭐ **7 ott, decisione dell'utente** (*«cerchiamo di accelerare i tempi»*): **niente riavvio** — si guarda
   che il server sia vuoto (processi, inquilini, compositori) e si parte appena il binario è deciso, senza
   aspettare la fine del noleggio NVIDIA (il rischio dichiarato: una cura nata là nelle ultime ore
   costringerebbe a rifare le salite già fatte).
   ⭐ **7 ott 08:19, PARTITA**: `sudo systemd-run --unit=r20-campagna … 16-campagna.sh intel-f20 amd-f20`
   (coda per scheda: 4K → 3K → 2K → Full HD su GNOME, KDE, XFCE, LXQt; video D = il file 4K locale, 30 fps).
   Binario `e2b1afae` = commit **`716e35b`** (letto dalla salita: «commit del prodotto: 716e35b»), pagina
   `ae66b9b4`. Prima: rete di casa 732 + 733 PASS, 0 FAIL; e la prova A/B di F-030 Firefox (primo fotogramma
   nero) — vecchio `5c186779` 4 su 12, nuovo 3 su 12 ⇒ non viene dalle cure della notte, ⏳ resta aperto.
   Server guardato vuoto (nessun inquilino, nessun giro, nessun browser). Per fermarla: `touch
   /media/REMOTIX/misure/fase16/FERMA` (fra una salita e l'altra) o `sudo systemctl stop r20-campagna`.
   ⛔ **8 ott 10:20 UTC, il server incastrato** (riavviato dall'utente): Intel **finita** (16 salite, 04:37),
   Radeon finiti GNOME (4 misure) e KDE 4K; si è piantato in `amd-f20-3k-kde`, ripetizione del livello 12,
   dopo un «attore morto» alle 10:09 e il livello 12 FAIL (5 GREEN · 1 DEGRADED · 7 FAIL). Il journal stava
   in RAM ⇒ la causa non è dimostrata; il quadro è quello del 28 set (fasi/16 §17.3: RAM finita con 13
   sessioni e 13 browser-cliente sulla stessa macchina). ⇒ È un limite **del banco** (i browser-cliente
   stanno sul server), da dichiarare come tale, non del prodotto. La salita interrotta resta in
   `amd-f20-3k-kde-interrotta`. Radice rifatta con la ricetta (pacchetti, earlyoom, storage.conf, linger,
   `provisiona.sh` di `716e35b` + `/etc/ld.so.conf.d/remotix-prodotto.conf` → `rete11/prodotto/lib`:
   verifica OK; swap `/media/swapfile` 32 GB riattivato alle 10:50, il riavvio l'aveva tolto), e **ripresa alle 10:42** con lo stesso binario: unità `r20-ripresa`
   (`misure/fase16/ripresa-8ott.sh`: Radeon KDE 3K → 2K → Full HD, poi XFCE e LXQt da 4K). Fermarla:
   `FERMA` come sopra o `sudo systemctl stop r20-ripresa`.
1. **Il commit del giorno**, identificato, con la **suite corta di regressione** della fase 15 sui 4 desktop
   coi due browser. Non verde ⇒ non si misura.
2. **L'impianto rimesso in piedi sul prodotto di oggi**: i banchi `16-*` sono di prima della fase 18 e 19
   (pagina con WebGL2, niente ffmpeg, strada Vulkan). Ogni misuratore con la sua prova, come allora: un
   misuratore che non ha mai dato rosso non misura.
3. **Una salita di prova** corta (4 utenti, 5 min a livello) per tarare: non conta.
   **6 ott, prima prova** (Radeon, GNOME, 4K, binario `5c186779`, banchi `d9c86d6`): due difetti del banco,
   nessuno del prodotto, e tutti e due corretti in `16-salita.py`:
   - *livelli da 3 min* = 1 di assestamento + 2 di controllo corto ⇒ il tratto della memoria era **vuoto**,
     «NON MISURATO» ⇒ DEGRADED al primo gradino, salita ferma a 0. Ora la prova fa 4 min, e la salita
     **rifiuta** livelli più corti di controllo + 2 min.
   - *seconda prova, livelli da 4 min*: la serie della memoria ha 60 punti in 59 s, e `16-classifica` ne
     vuole più di 60 s ⇒ ancora NON MISURATO. La prova passa a **5 min** (2 min di memoria).
   - il ritardo input → fotogramma a 4K su GNOME/Radeon, 1 utente: **53–55 ms** (soglia verde 50). Non è un
     peggioramento: nella fase 16 era 55–59 (`amd-4k-gnome`, `amd-b-4k-gnome`). È la ragione per cui la
     scala scende; la terza prova si fa a 2K, dove un utente sta sui 23 ms e i gradini possono salire.
   - **terza prova, 2K, 5 min** (`prova-f20-prova-amd-gnome-2k`): 1, 2, 4 utenti **tutti GREEN**, la memoria
     misurata (remotix 95 → 96 MB, sessioni 2303 → 2301 MB in 119 s). La salita va da capo a fondo.
   - **le altre tre prove a 2K** (6 ott, 16:50–17:45), una per desktop, le due strade coperte:
     KDE/Intel e XFCE/Intel 1-2 GREEN, 4 DEGRADED non significativo; LXQt/Radeon 1 GREEN, 2 DEGRADED
     significativo poi GREEN alla ripetizione, 4 GREEN. Tutti i DEGRADED sono un **blocco dell'immagine di
     1.03–1.16 s** (soglia 1 s) in un attore solo: misura vera, da guardare nella campagna, non difetto del
     banco. ⇒ **l'impianto è tarato su 4 desktop × 2 schede**; resta solo il binario finale.
   - *«commit del prodotto: ?»*: la salita lo cercava solo in `src/16-prodotto` (fermo al 26 set). Ora legge
     anche `rete11/prodotto/VERSIONE` = `<commit> <md5 a 8>`, valida solo se l'md5 è quello del binario.
     ⇒ **passo fisso della campagna**: compilato il binario finale, si copia in `rete11/prodotto` e si
     scrive accanto `VERSIONE`.
4. **Le campagne, una configurazione alla volta** (le prestazioni non si misurano in parallelo):
   Intel = VA-API su GNOME, KDE, XFCE, LXQt; poi Radeon = Vulkan, stesso ordine.
4b. ⭐ **Il confronto con xrdp, a parità di macchina** (deciso dall'utente l'8 ott: *«sono curioso di vedere
   come siamo messi e soprattutto avere dei dati oggettivi di confronto»*). ⛔ Oggi «siamo avanti a xrdp» è
   un giudizio (fasi/08 §2.5, 22 ago, un utente, a occhio), non una misura, e in rete non esiste un banco di
   carico di xrdp. **Una salita sola**, non la matrice (~3 giorni, scartata per costo): **XFCE, 2K, Intel** —
   XFCE è nativo su X11, cioè a casa di xrdp, e non lo penalizza; il 2K è il formato che dichiariamo; noi lì
   facciamo **10** (`intel-f20-2k-xfce`). Stessa scena, stessi gradini, stesse soglie; i clienti sono
   **FreeRDP** (il browser non parla RDP) ⇒ CPU, RAM, scheda e cadute si confrontano uno a uno; ritardo e
   fotogrammi si leggono in altro modo e vanno dichiarati come tali. Costo: ~½ giornata per adattare il
   banco + ~2 ore di salita. Parte **dopo** la campagna, con `r20-ripresa` finita. Esce una riga: «a 2K su
   XFCE, stessa macchina: REMOTIX 10, xrdp N». Se è vicino, l'utente decide se allargare.
   ⭐ **8 ott sera, la scelta dell'utente: la versione completa** (§7, ~2 giorni + ~3 ore di macchina), non
   quella ridotta (solo rottura, CPU e RAM): *«pensavo ad una suite completa anche per xrdp, avremmo un
   confronto pieno»*. ⚠ «Pieno» ha un limite di costruzione: saltati, buchi e audio **non esistono** dal lato
   xrdp (§7.3), e nessun lavoro in più li fa comparire. ⛔ **Vincolo dell'utente**: *«che la suite di test
   non blocchi il lavoro sul sistema di licensing»* (DECISIONI §10.30) ⇒ la **licenza viene prima**; il banco
   xrdp si scrive accanto, senza togliere ore alla licenza, e prende il server solo quando la licenza non lo
   usa. Le due cose non si toccano: il confronto usa le misure **già fatte** di `716e35b`, quindi un binario
   nuovo con la licenza non obbliga a rifare nulla.
5. **Il rapporto** e **la tabella pubblica** (§5).

**Quanto dura**, dalla fase 16: ~1 ora e 10 per salita ⇒ ~9 ore di macchina nel caso migliore (8 salite),
~35 se si scende per tutta la scala. A blocchi, anche di notte, e ⛔ **mai mentre l'utente usa il server**.

### 3-bis. Dopo la campagna: le due stranezze (9 ott 2026)

**1. Radeon 4K, GNOME e KDE «0 utenti»: è il driver, e la cura c'è.** `[M]` Nei registri di `amd-f20-4k-gnome` la
Radeon usa la strada **Vulkan** con **RADV 25.0.7** (Debian 13), e REMOTIX chiede `ULTRA_LOW_LATENCY`
(`src/vulkanvideo.c:629`). Il progetto `~/Documenti/AMD` (§5-ter) ha misurato che RADV 25.0.7 la accetta ma non la
traduce al firmware; da Mesa **25.1** sì. Con un utente il livello era DEGRADED per il solo ritardo (51-56 ms,
soglia 50), tutto il resto verde: l'anomalia A3 (gruppi di 5 fotogrammi da 31 ms).
Salite ripetute con **`mesa-vulkan-drivers 26.1.6-1~bpo13+1`** (il **backport ufficiale di Debian 13**) installato
nella scatola prima del server (`16-salita.py --mesa-vulkan-deb`, `misure/fase16/mesa26-9ott.sh`, campagne
`amd-m26-4k-*`, binario `716e35b` invariato):

| Radeon GNOME 4K, 1 utente | RADV 25.0.7 (`amd-f20`) | **RADV 26.1.6** (`amd-m26`) | Intel, per confronto |
|---|---|---|---|
| classe | DEGRADED (due volte) | **GREEN** | GREEN |
| ritardo p95 | 53,95 / 55,72 ms | **21,45 ms** | 35,18 ms |
| NOSTRO p95 dei p95 | 45,0 / 46,7 ms | **12,4 ms** | 26,2 ms |

**Le 4 salite a 4K, finite il 9 ott alle 11:13** (ultimo livello buono, RADV 25.0.7 → 26.1.6): GNOME **0 → 4**,
KDE 0 → 0 (foto vecchia di 1,6-2,2 s con un utente, tetto 1 s), XFCE **2 → 0** e LXQt **3 → 0** (input perso:
2 tasti su 11 e 1 su 13 con un utente, ritardo buono a 33 ms; confermato dalla ripetizione).
⇒ ⛔ **Chiusa qui, per decisione dell'utente (9 ott): Mesa 26 non è nel perimetro**, era solo la verifica della causa.
La causa di A3 su GNOME è il driver, non REMOTIX. I tasti persi su XFCE e LXQt compaiono **solo** con Mesa 26, quindi
anche loro vengono dal driver. Il prodotto resta su RADV 25.0.7 di Debian 13 e la tabella pubblica riporta le misure
`amd-f20`.

**2. «Buono 12, verde vero 1» (es. Intel XFCE Full HD): non è una contraddizione.** «Buono» ammette un DEGRADED non
significativo (al massimo un attore su quattro); «verde vero» li vuole tutti verdi. A 4, 8 e 12 utenti c'era **un
solo attore** DEGRADED, sempre per il **blocco dell'immagine** di 1,06-1,11 s (soglia 1 s). `[M]` Nel caso
`intel-f20-fhd-xfce/livello-04` (utente 1, profilo A, che batte testo) il **server risponde a ogni tasto in 23-40 ms**
(registro: `input id=1524…1545` → `fotogramma SPEDITO`), nessun fotogramma saltato, nessun input perso. `[?]` Il
secondo «fermo» nasce **prima** del server o nel confronto fra l'ora dei tasti ricostruita dall'attore
(`ore_dei_tasti`, dal ritorno della catena di Marionette) e l'ora dei dipinti della pagina: **da verificare** prima
di chiamarlo difetto, con l'attore che scrive ogni impulso e il dipinto che gli attribuisce.

⭐ **10 ott 2026, mattina — verificato sui file, senza toccare il server** `[M]`: in `intel-f20-fhd-xfce` i blocchi sopra
soglia sono 7 (livelli 4, 8, 12: utente 1 profilo A, utente 7 e 3 profilo C), tutti 1,05-1,13 s, tutti **Firefox**,
con 0 fotogrammi saltati e 0 errori. Nelle **stesse righe** di `stato.jsonl` (5 s) il **giro della pagina** (tasto →
fotogramma, misurato dalla pagina) ha il massimo a **24,7-47,5 ms**, e l'eco del terminale a 24-25 ms. ⇒ Lo schermo ha
risposto: il secondo «fermo» **non è del server REMOTIX**. Sta fra Marionette e Firefox: o l'ora dei tasti ricostruita
da `ore_dei_tasti` (che presume la catena eseguita senza fermate), o Firefox stesso fermo sulla macchina carica (gli
attori girano sul server). I blocchi 0,7-1,5 s su Firefox compaiono **su tutti i desktop** (da 0 a 15 per salita,
livelli 1-8); Chrome, che batte i tasti uno per uno via CDP con l'ora vera, non li ha mai fuori dal video.
⇒ ⚠ **Nel confronto con xrdp pesa contro REMOTIX**: l'attore di xrdp batte con XTEST, ora vera, e questo errore non
ce l'ha. Le celle «verde vero» di REMOTIX tagliate **solo** da un blocco Firefox: Intel XFCE Full HD (1, buono 12),
GNOME 3K (1, buono 4), XFCE 3K (4, buono 8). ⏳ Cura proposta: l'ora del tasto la scrive la **pagina** (l'evento
`keydown`), non la ricostruisce l'attore; e le salite già fatte si riclassificano dai file, senza rifarle.

## 4. Il limite dei 16, dichiarato

Il prodotto oggi ha **16 sessioni fisse nel programma** (`MAX_ATTACCATE` in `src/rcp.c`, DECISIONI §1.11).
Questa campagna misura fino a 16, come la fase 16. **Oltre 16** si misura solo dopo il lavoro «limite deciso
all'avvio» (DECISIONI §10.30), e su una macchina più grande della nostra: oggi non si può.

## 5. Che cosa esce

- **La matrice** della fase 16: desktop × scheda, con ultimo livello GREEN, punto di rottura, gradino della
  scala.
- **La tabella pubblica**, una riga per scheda (e per desktop, se differiscono). ✅ Sta nella **documentazione
  tecnica** (la guida al dimensionamento), **non nella home** del sito (utente, 9 ott: *«nella homepage del prodotto
  di certo le prestazioni non vengono riportate»*); la home ci rimanda con un collegamento:

  | macchina | scheda e strada | misura dello schermo | ottimale fino a | degrado da |
  |---|---|---|---|---|
  | i5-13500T, 31 GB | Intel UHD 770 · VA-API | 4K | … | … |
  | i5-13500T, 31 GB | AMD RX 6800 · Vulkan | 4K | … | … |

  ⚠ **La RAM è 31 GB, non 64** (letto con `free` sul server, 7 ott durante la campagna): la tabella va
  corretta prima di pubblicarla.
  ⚠ **Intel: 256 MB di memoria video nel BIOS** (annotato dall'utente, 7 ott). Su Linux servono solo all'avvio;
  dopo, la scheda prende la memoria dalla RAM comune quando serve (memoria condivisa vista a 16 GB durante le
  salite). ⇒ non è il limite del 4K: lì cedono ritardo e fotogrammi (velocità di copia e compressione), non la
  memoria. Da provare a parte, a campagna finita: Intel 4K su un desktop, 256 MB contro il massimo del BIOS.
  ⚠ Con la dichiarazione della fase 16, che resta vera: il server fa girare **anche gli N browser**, quindi i
  numeri sono un **limite inferiore**; la rete non è misurata.
- ⛔ I numeri **non** si scrivono nelle SPECIFICHE come promesse: restano obiettivi di progetto
  (DECISIONI §10.26).

## 6. Domande per l'utente, prima di partire (una per volta)

1. **Il perimetro**: 4 desktop × 2 schede (~9–35 ore), oppure prima un desktop per scheda (~2–9 ore) e gli
   altri dopo?
2. **Il video dei lavori D**: YouTube 4K come allora, o subito il file 4K locale (non cambia sotto i piedi, e
   rende le salite ripetibili)?
3. **La scala**: si scende fino al Full HD come allora, o ci si ferma al 2K?

**Risposte dell'utente (6 ottobre 2026):**
- 1 ✅ **4 desktop × 2 schede = 8 salite: Intel e Radeon** del server di casa (confermato dall'utente).
- 3 ✅ **si scende fino al Full HD**.
- 2 ✅ **il video: il file 4K locale** (un film libero della Blender Foundation, CC-BY), scelto per la
  ripetibilità fra le 8 salite. ⚠ La rete NON è una ragione: il server ha una linea da 10/2 Gb/s (detto
  dall'utente).

## 7. Il banco xrdp: il piano

### 7.0 ⭐ 9 ott 2026, pomeriggio: le decisioni dell'utente, e quel che è già misurato

**Le quattro decisioni** (la licenza è sospesa, quindi il banco xrdp ha via libera, anche sul server):
1. *«i test su xrdp devono rispecchiare quelli su remotix: 4 DE, Intel e Radeon»* ⇒ **la matrice intera**:
   8 salite, 4K → Full HD, come `intel-f20` e `amd-f20`. Il punto 4b di §3 (una sola salita XFCE 2K) è superato.
2. *«fai in modo che la suite lavori in modo autonomo sul server»* ⇒ la stessa struttura di REMOTIX:
   `16-campagna.sh` → `16-coda.sh` → `16-salita.py --sistema xrdp`, in un'unità systemd, con `FERMA` e la ripresa.
3. *«e soprattutto evita che il server si blocchi»* ⇒ §7.7.
4. *«mi aspetto che l'intera suite duri meno dei 3 giorni di remotix»* ⇒ le due campagne di REMOTIX hanno occupato la
   macchina per ~50 ore (Intel ~22, Radeon ~28). Con lo stesso protocollo la durata dipende da dove cede xrdp:
   stima **1½-2½ giorni**. ⛔ Niente tetto che tronchi le salite, perché romperebbe la comparabilità. La coda
   scrive a ogni salita il **preventivo** delle ore rimaste, così uno sforamento si vede subito.

**Il primo pezzo di §7.6 è fatto e misurato** `[M]` (9 ott, 16:00-16:10):
- **una ricetta sola**, `banchi/11-scatole/Contenitore.xrdp` (`ARG DESKTOP`), costruita **sopra** l'immagine delle
  misure (`rete11/<desktop>:p0`); `11-accendi.sh costruisci|accendi <desktop>-xrdp`. Più xrdp
  0.10.1-3.1+deb13u2, xorgxrdp 1:0.10.2-1 e pipewire-module-xrdp 0.2-2. Per stare su X11, ogni desktop riceve il suo
  pezzo di Debian: GNOME `gnome-session-xsession` (Mutter 48), KDE `kwin-x11` (Plasma 6.3.6), XFCE `xfwm4` e
  `xfce4-settings`, LXQt `openbox`;
- **le 8 combinazioni nascono fino al desktop** con `xfreerdp3 /gfx` in un Xvfb 2560×1440 sull'ospite, e le 8 foto
  sono guardate. Il registro di Xorg dice `rdpPreInit: /dev/dri/renderD128` con `name [amdgpu]` sulla Radeon, quindi
  la sessione disegna sulla scheda giusta. ⇒ Rischio 3 di §7.6: **chiuso**;
- **la tastiera arriva** dal canale RDP (`xdotool type` nel terminale, visto nella foto);
- **la sonda XDamage vede i disegni di FreeRDP**: 63 eventi in 5 s mentre si scrive, 1 a riposo (l'orologio).
  ⚠ Due condizioni, scoperte sbagliando: `d.damage_query_version()` prima di tutto (senza, **zero** eventi e
  nessun errore), e il danno va chiesto sulla **finestra di FreeRDP**, non sulla radice (la radice non riceve i
  disegni dei figli). ⇒ Rischio 2: **chiuso**;
- ⛔ **la porta 3389 è una sola per tutto l'ospite** (`--network=host`). Al primo giro una scatola xrdp rimasta
  accesa ha risposto al posto delle altre tre, e le foto sembravano giuste ma erano tutte di XFCE. ⇒ Prima di
  accendere, la salita spegne **ogni** `rete11-*-xrdp` e vuole la 3389 libera; la foto della nascita si confronta
  col desktop atteso.
- sull'ospite: `freerdp3-x11` 3.15.0+dfsg-2.1+deb13u3, `xvfb` 2:21.1.16-1.3+deb13u4, `xdotool`, `python3-xlib`
  0.33-3, `x11-apps`. ⚠ La radice è in RAM: dopo un riavvio vanno reinstallati (la salita lo controlla).

### 7.7 ⛔ Il server non si deve bloccare

Un server bloccato significa riavvio, e il riavvio perde la chiave ssh e il provisioning: la campagna resta ferma
finché l'utente non mette mano. Con xrdp il rischio sale, perché i clienti FreeRDP decodificano **sul processore
dell'ospite**: a 4K, 16 utenti significano 16 decodifiche RemoteFX più 16 Xorg. ⇒ Quattro reti, dalla più esterna:
1. **la guardia della memoria** nella salita: ogni 2 s legge `MemAvailable` e `/proc/pressure/memory`. Sotto
   **3 GiB** liberi, o con `full avg10` sopra **20 %**, il livello si chiude subito come **rottura «risorse
   dell'ospite»** (dichiarata nella classifica, non mescolata con le soglie di §9) e si sgombera. ⚠ Il REMOTIX di
   `716e35b` non aveva questa guardia: nella tabella la si dichiara, e si guarda nei `risorse.jsonl` della campagna
   REMOTIX se ci sarebbe mai scattata;
2. **chi muore prima:** i clienti (Xvfb e FreeRDP) nascono con `OOMScoreAdjust=+800`, quindi se il kernel deve
   uccidere qualcosa uccide un cliente (un gradino rosso), non `sshd` né la coda;
3. **chi non muore mai:** `sshd` e l'unità della coda ricevono `OOMScoreAdjust=-900` con un drop-in in `/run`
   (sparisce al riavvio come tutto il resto, e la campagna lo rimette);
4. **la coda non si ferma per un processo ucciso:** `OOMPolicy=continue`, come in `16-coda.sh`.
⇒ Il limite di quanti clienti regge l'ospite resta quello di §7.6 rischio 1, e il recinto `browser` lo mostra.

### 7.8 Il banco è scritto e provato; la campagna NON è partita (9 ott, sera)

**Che cosa c'è** (commit `31d5b50` e seguenti, in `banchi/16-stress/`):
- `16-attore-rdp.py`: lo stesso ritmo e gli stessi quattro lavori di `16-attore.py`. FreeRDP `/gfx` a tutto
  schermo in un Xvfb, le mani con XTEST, la foto dall'Xvfb, la sonda XDamage sulla finestra di FreeRDP
  (raffiche a 5 ms). Con `--controllo` fa il controllo corto ridotto di §7.3 (accesso, schermo, tastiera), con
  un inquilino per livello (`c16<9NN>u99`), e se la nascita fallisce salva `~/.xsession-errors` e il registro di
  Xorg;
- `16-compositori-rdp.sh` (un Xvfb per utente, con `oom_score_adj` 800);
- `--sistema xrdp` in `16-salita.py` (la scatola, la 3389, xrdp acceso, i registri di xrdp, le versioni dei
  pacchetti, `dpkg --verify` per dimostrare che la configurazione è quella del pacchetto, la guardia di §7.7,
  sshd a −900), in `16-risorse.py` (i recinti di §7.4) e in `16-classifica.py` (le voci di §7.3; registro
  `registro-xrdp.jsonl`);
- in `16-coda.sh` e `16-campagna.sh`: `REMOTIX_16_SISTEMA=xrdp` e il preventivo delle ore scritto in `campagna.log`
  dopo ogni salita.
Tutte le certificazioni passano: attore-rdp, classifica 38 su 38 (4 nuove per xrdp), risorse 21 su 21.

**Misurato** `[M]`, prova XFCE 2K Intel (`prova-x20-xfce-2k`, gradini 1, 2, 4 da 5 minuti):
- livelli 1, 2 e 3: **GREEN**. Ritardo impulso → disegno, p95 dal lato di chi guarda: 17-41 ms; nascita
  2,6-2,7 s; video D 24,8 dipinti/s (0,83·f). Le quattro foto del livello 4 sono state guardate e sono giuste:
  A naviga, B Thunar, C terminale, D il film a tutto schermo;
- livello 4: **FAIL, due volte su due**, e ogni volta per la stessa voce, cioè il controllo corto: la quinta
  sessione non nasce.

**⛔ La scoperta: con una sessione che guarda il video, xrdp non fa più entrare nessuno.** `[M]` Riprodotta
**senza il banco**, con soli `xfreerdp3` e Firefox a mano:

| sessioni già aperte | il film 4K gira in una? | la sessione dopo | scheda |
|---|---|---|---|
| 6 in fila, tutte ferme | no | nascono tutte e 6 | Intel |
| 1 | sì | nasce | Intel e Radeon |
| 4 | sì | **la 5ª e la 6ª muoiono subito** | Intel e Radeon |

Ogni volta l'**Xorg della sessione nuova va in crash** in xorgxrdp (`rdpCapture`, `(EE) Backtrace` in
`~/.xorgxrdp.NN.log`), `startxfce4` esce con 1, e FreeRDP riceve `ERRINFO_LOGOFF_BY_USER`. Non dipende dal nome
dell'inquilino, dal banco o dalla scheda grafica.
⇒ Nella salita il profilo D entra quarto. Da lì in poi nessun utente nuovo nasce, e **ogni salita di xrdp si
fermerebbe a 3 utenti**, su tutti i desktop e a tutte le misure, per un crash e non per le risorse. La campagna
(32 salite, ~1 giorno) produrrebbe soprattutto questo numero, ripetuto 32 volte.

**La decisione è dell'utente**, prima di partire:
1. **si misura così**: è xrdp come lo installa Debian 13, ed è un risultato vero (a un cliente con 4 colleghi,
   uno dei quali guarda un video, xrdp rifiuta l'accesso). La campagna dirà 3 ovunque, più CPU, RAM e
   ritardo fino a 3;
2. **prima si guarda il crash** (~½ giornata): se viene da glamor (xorgxrdp disegna sulla scheda) basta provare
   senza, ma è una modifica a `xorg.conf` di xrdp, cioè **fuori** dalla regola «configurazione del pacchetto»
   di §7.5, e andrebbe dichiarata;
3. **si cambia l'ordine degli utenti** solo per xrdp (D entra per ultimo). ⛔ Non lo consiglio: la scena non
   sarebbe più la stessa, e il crash arriverebbe comunque al livello dopo.

⭐ **La scelta dell'utente (9 ott, sera): la 1.** *«se xrdp ha dei difetti meglio: vuol dire che il nostro prodotto
e' migliore»*. ⇒ **Campagna partita il 9 ott alle 17:47** (unità `r20-xrdp`, `16-campagna.sh intel-x20 amd-x20`,
`REMOTIX_16_SISTEMA=xrdp`), con la configurazione del pacchetto (`dpkg --verify` pulito).
⏳ **Dopo la campagna, un'ora: il crash fuori dalla scatola.** xrdp installato sull'ospite, 4 sessioni con una che
guarda il film, poi la 5ª. Le misure valgono in ogni caso; il controllo decide come si racconta il crash. Se
compare anche fuori dalla scatola, «xrdp non fa entrare il quinto» si scrive. Se non compare, si dichiara come
limite della prova in contenitore e si torna dall'utente.

*Scritto l'**8 ottobre 2026** sera, sul portatile, leggendo il banco `banchi/16-stress/`; il server non
è stato toccato (gira `r20-ripresa`). Serve al punto 4b di §3. ⛔ Niente codice prima che la campagna
sia finita e questo piano sia letto.*

⚠ **La stima di §3 punto 4b era troppo bassa.** «Mezza giornata per adattare il banco» non regge: l'attore
di oggi parla con la **pagina** (Marionette/CDP, la sonda dei dipinti, il diario), e per FreeRDP quella
parte va rifatta. Stima onesta in §7.6: **~2 giorni di lavoro + ~3 ore di macchina**.

### 7.9 ⚠ Prima lettura della campagna xrdp, Intel (10 ott 2026, mattina, a campagna in corso) `[M]`

Letta dai file, senza toccare il server. Due cose cambiano quel che si può dire.

1. **La maggior parte delle rotture di xrdp è l'ACCESSO del controllo, non l'esperienza di chi lavora.** A 4K,
   su tutti e quattro i desktop, il livello 1 è FAIL **solo** perché la sessione di controllo (utente 99, una
   seconda connessione FreeRDP) esce durante l'accesso con `ERRINFO_LOGOFF_BY_USER`; l'utente che lavora è
   **GREEN**. Lo stesso motivo chiude quasi tutti i livelli 2 e 4 a 3K e 2K, e 7-8 in Full HD XFCE/GNOME.
   ⛔ ⇒ «A 4K xrdp non regge nemmeno una persona» **non si può scrivere**: una persona lavora bene, è la
   **seconda che non riesce a entrare**. ❓ Se è un limite vero di xrdp (un secondo accesso che fallisce, che per
   un cliente è un difetto vero) o un difetto del banco (l'utente di controllo, sesman, la risoluzione) è **da
   riprodurre a mano** a campagna finita: una sessione xrdp a 4K aperta, poi un secondo accesso.
   Rotture d'altra natura, che sembrano vere: KDE perde l'input (2-3 azioni su 2-3 senza effetto, 2K e Full HD) e
   GNOME Full HD a 4 utenti (blocco 6,4 s, ritardo p95 3,98 s).
2. **Con un utente solo il ritardo è pari, xrdp un poco avanti.** Ritardo tasto → immagine, p95, dal lato di chi
   guarda (REMOTIX: il giro della pagina, ultimi 200 campioni della sessione; xrdp: XDamage, §7.3):

   | Intel, 1 utente | GNOME | KDE | XFCE | LXQt |
   |---|---|---|---|---|
   | 4K | 54 / 48 | 55 / 53 | 53 / 34 | 67 / 31 |
   | 3K | 48 / 39 | 48 / 44 | 45 / 34 | 60 / 40 |
   | 2K | 43 / 37 | 43 / 41 | 40 / 32 | 40 / 41 |
   | Full HD | 39 / 35 | 39 / 39 | 37 / 33 | 36 / 44 |

   (ms, REMOTIX / xrdp). ⚠ Il giro della pagina comprende decodifica e disegno nel browser, XDamage su Xvfb no
   (§7.3): parte del distacco è il metro. ⇒ Il vantaggio di REMOTIX misurato è la **tenuta sotto carico**, non
   la risposta del singolo utente.
3. **Il video e il peso: qui REMOTIX è avanti, e combacia con l'impressione dell'utente** (10 ott: *«remotix mi
   sembra più reattivo, più leggero. Riprodurre un video ad alta risoluzione su xrdp è un'esperienza peggiore»*).
   A 4 utenti, l'utente del video (film 4K a 30 fps): REMOTIX **29,9-30,0 dipinti/s**, 0 saltati; xrdp
   **24,7-24,9** (2K e Full HD; classe GREEN per entrambi, soglia 0,8 di f) ⇒ xrdp perde ~1 fotogramma su 6.
   Processore della macchina, livello 4: REMOTIX **10,7-12,5 %**, xrdp **12,4-30,0 %** (Full HD GNOME 11 contro
   30, KDE 12 contro 26, XFCE 11 contro 18), e il numero di REMOTIX comprende browser veri come clienti, quello di
   xrdp clienti FreeRDP più leggeri: il distacco vero è più largo. REMOTIX sposta il lavoro sulla scheda (a 4
   utenti: disegno 19-62 %, video 11-24 %).

### 7.1 Come nasce oggi una sessione, e che cosa cambia

| oggi (REMOTIX) | xrdp | chi lo fa |
|---|---|---|
| scatola `rete11-xfce` rifatta da zero (`11-accendi.sh`), dentro `rete11-server` | **la stessa scatola** con in più `xrdp` e `xorgxrdp` (immagine derivata `rete11-xfce-xrdp`, costruita **una volta**), `rete11-server` **fermo**; `xrdp` e `xrdp-sesman` accesi coi file di Debian **come sono** | `16-salita.py --sistema xrdp` |
| inquilino `c16NNNuN` creato dall'attore (`suite.Sessione`), PAM della scatola | **uguale**: sesman passa da PAM (`/etc/pam.d/xrdp-sesman` → `common-auth`), l'inquilino è lo stesso | riuso |
| un **labwc senza schermo** per utente (`16-compositori.sh`), dentro un browser | un **Xvfb** per utente (`:2NN`, 2560×1440) con dentro **`xfreerdp3`** a tutto schermo: `/v:127.0.0.1 /u:… /p:… /cert:ignore /gfx /f /sound:sys:fake /wm-class:remotix-rdp-NN` | `16-compositori-rdp.sh` (nuovo) |
| l'input: Marionette/CDP sulla tela della pagina | **`xdotool`** sul display dell'Xvfb (mouse, tasti, rotella): l'input passa **dal canale RDP**, come quello dell'utente | `Mani` nuova |
| la foto: la tela della pagina | la foto dell'Xvfb (`xwd -root` → PIL), **1:1 col desktop** (niente conversione foto → desktop) | `foto_pil` nuova |
| i dipinti: la sonda nella pagina (ogni 10 ms l'ora di ogni cambio) | **XDamage sull'Xvfb** (`python3-xlib`): ogni volta che FreeRDP disegna, l'ora. ⭐ È la **stessa misura dal lato di chi guarda** | sonda nuova |

⭐ **Perché xfreerdp in Xvfb e non sdl-freerdp nel labwc.** Con Xvfb l'input si inietta con `xdotool`,
che è collaudato; nel labwc servirebbero `wtype` e un puntatore virtuale, mai provati nel banco. ⚠ **Il
prezzo, da dichiarare:** FreeRDP decodifica RemoteFX **sul processore** e non usa la scheda Intel. Oggi i
browser stanno sulla Intel insieme al server; con xrdp no. Sulla scheda xrdp è **avvantaggiato**, sul
processore **svantaggiato**.

**Il nuovo attore** è `16-attore-rdp.py`, non una modifica di `16-attore.py`. Riusa `Ritmo` (stessi semi,
stesse scelte nello stesso ordine) e **tutti e quattro i lavori di `16-lavori.py`**: usano solo `dorme`,
`verifica`, `impulso`, `mani.*`, `foto_pil`, `s.nella_sessione`, `sc.dentro`, `chi`, `desktop`. Di questi
cambiano tre cose:
- `nella_sessione`: `DISPLAY=:N` dell'Xorg dell'inquilino (letto da `ps -u <inquilino>`), `XAUTHORITY`,
  il bus di sessione da `/proc/<xfce4-session>/environ`, senza `MOZ_ENABLE_WAYLAND`;
- `Mani`: xdotool con le stesse pause e la stessa battitura del `Ritmo`;
- la foto: dall'Xvfb.

La riga di stato si scrive **nello stesso schema** (`stato.jsonl`, `nascita.json`), così la classifica la legge.

### 7.2 La scena di lavoro: uguale

I quattro profili A/B/C/D girano **dentro la sessione XFCE** come oggi. I file si preparano allo stesso modo
(`prepara`), le applicazioni sono le stesse (`firefox-esr --kiosk`, `thunar`, `xfce4-terminal`) e
il video è lo stesso file 4K locale (`/rete11/.c16-video/`). Le verifiche guardano **il disco** (il quaderno,
la cartella creata, la storia di bash) e **non sanno** se davanti c'è REMOTIX o xrdp.
⚠ L'unica differenza è che XFCE gira **su X11**, perché xrdp non conosce Wayland. È l'ambiente naturale di xrdp
(§3 punto 4b), e la sessione la sceglie un `~/.xsession` con `startxfce4` scritto da `prepara`.

### 7.3 Le misure, una per una

| voce (§9, soglie ferme) | xrdp | come |
|---|---|---|
| **ritardo input → fotogramma** | ⚠ **in altro modo** | dal lato di chi guarda: p95 al secondo fra l'**impulso** (tasto, clic, tacca) e il **primo dipinto** XDamage dopo. ⛔ Il REMOTIX della campagna è giudicato dal **lato server** («NOSTRO» + 9 ms). ⇒ Nel confronto si mette accanto il **giro** di REMOTIX (`stato.jsonl` → `giro`, il ritardo comando → fotogramma della pagina, **già registrato** in `intel-f20-2k-xfce`): lato cliente contro lato cliente. ⚠ Il giro della pagina include decodifica e disegno, XDamage su Xvfb no: leggero vantaggio a xrdp, dichiarato |
| **fotogrammi saltati** | ⛔ **non misurato** | FreeRDP riscontra ogni fotogramma (FRAME_ACKNOWLEDGE): xrdp **non manda** quelli che non può, non li salta. Non c'è un «consegnati contro dipinti» da contare |
| **blocco più lungo dell'immagine** | ✅ **uguale** | stessa funzione (`attese_impulsi`, `pausa_piu_lunga`), ma con i dipinti XDamage |
| **buchi nella catena del video** | ⛔ **non misurato** | è un contatore della nostra pagina, non ha un equivalente |
| **video: dipinti al secondo** | ⚠ **in altro modo** | le raffiche XDamage al secondo nella finestra del video (raffiche separate da più di 5 ms). ⚠ xrdp ha `rfx_frame_interval=32 ms` di serie (≈31 al s): col film a 30 fps **non lo penalizza** |
| **audio udibile** | ⛔ **non misurato** (ma **acceso**) | `pipewire-module-xrdp` nella sessione e `/sound:sys:fake` nel cliente: l'audio **viaggia**, così il carico è pari, ma nessuno lo suona e quindi non si conta |
| **nascita** | ⚠ **in altro modo** | dall'avvio di xfreerdp (con utente e parola: niente schermata di accesso) al **primo dipinto con il pannello di XFCE**, cioè una foto non degenere; stesse soglie |
| **caduta, riavvio, errore** | ✅ **equivalente** | xfreerdp esce o scrive `ERRCONNECT_*`; in `/var/log/xrdp.log` e `xrdp-sesman.log` compaiono «connection problem» o «session … terminated» |
| **controllo funzionale corto** | ⚠ **ridotto** | `16-controllo-corto.py` prova le funzioni F-0xx della pagina e qui non serve. ⇒ Una 17ª sessione FreeRDP entra, batte un comando, lo trova nella storia ed esce: **accesso, tastiera, schermo**, nient'altro |
| **crescita della memoria** | ✅ **uguale** | da `risorse.jsonl` |
| **l'input arriva** (verifiche dei lavori) | ✅ **uguale** | gesto → effetto sul disco; ⭐ è **il numero più confrontabile** fra i due |

### 7.4 Le risorse: i recinti di `16-risorse.py`

| recinto | REMOTIX | xrdp |
|---|---|---|
| `remotix` (il server) | `rete11-server` + i figli `remotix` | `xrdp`, `xrdp-sesman`, `xrdp-sesexec`, `xrdp-chansrv`, per nome dell'eseguibile, dentro la scatola. ⭐ **Qui** si fa la compressione RemoteFX, sul processore |
| `sessioni` | compositore e applicazioni degli inquilini | **uguale**, e dentro c'è anche **`Xorg` + xorgxrdp** dell'inquilino, che fa la **cattura** (`rdpCapture`, con glamor sulla Intel) |
| `browser` (chi guarda) | Firefox/Chrome col segno `remotix-ff-`/`remotix-cr-` | `xfreerdp3` col segno `remotix-rdp-` (già previsto: `--segni-browser`) |
| `labwc_cliente` | i labwc senza schermo | gli **Xvfb** dei clienti (una riga in più nel riconoscimento) |

⛔ La divisione fra «server» e «sessioni» non è la stessa nei due sistemi: da noi copia il figlio
`remotix`, in xrdp copia `Xorg`. ⇒ Il confronto si fa sui **totali della scatola** (CPU, RAM, scheda),
che il campionatore misura già dal cgroup. I recinti spiegano i totali, ma non si mettono uno accanto
all'altro.

### 7.5 I pacchetti (Debian 13) e la configurazione

| dove | pacchetto | versione | nota |
|---|---|---|---|
| scatola | `xrdp` | 0.10.1-3.1+deb13u2 | ⭐ **compilato SENZA H.264**: nessun legame a x264/OpenH264, niente `gfx.toml` (letto sul portatile, stessa versione di Debian 13). Comprime con **RemoteFX** sul processore, e così si misura: è **xrdp come lo installa Debian 13** |
| scatola | `xorgxrdp` | 1:0.10.2-1 | con **glamor** e `DRMDevice /dev/dri/renderD128` di serie ⇒ la sessione disegna sulla Intel, come la nostra |
| scatola | `pipewire-module-xrdp` | 0.2-2 | l'audio della sessione |
| ospite | `freerdp3-x11` | 3.15.0+dfsg-2.1+deb13u3 | il cliente |
| ospite | `xvfb` · `xdotool` · `python3-xlib` · `x11-apps` | 2:21.1.16 · 1:3.20160805 · 0.33-3 · 7.7 | schermo finto, input, XDamage (⚠ `Xlib.ext.damage` da verificare), `xwd` |

**Configurazione:** quella di Debian **com'è**. Le eccezioni sono tre, tutte necessarie per far partire la prova e non per renderla più veloce:
`startwm.sh` → `startxfce4` (tramite `~/.xsession`), la porta 3389 libera sull'ospite (⚠ **da guardare** prima, con
`--network=host`), e `rete11-server` fermo. ⛔ Niente ritocchi a `xrdp.ini` (intervalli dei fotogrammi,
`max_bpp`): se li tocchiamo noi, il confronto non vale. Un xrdp ricompilato con x264 sarebbe un'**altra**
prova, da proporre all'utente solo se il risultato lo chiede.

**`16-salita.py --sistema xrdp`**: il controllo del server vuoto è lo stesso, più la porta 3389. La scatola
si rifà da zero con l'immagine `-xrdp`, senza `prodotto` e senza tetto. Al posto di commit e binario, in
`livello.json` vanno le versioni dei pacchetti. `server.log` diventa l'estratto di `xrdp.log` e
`xrdp-sesman.log`, e la classifica gira con `--sistema xrdp`. **Tutto il resto non cambia**: gradini 1,4,8,12,16,
10 minuti (30 l'ultimo), ripetizione, ricerca a metà, scatola pulita fra le ripetizioni.

### 7.6 Quanto costa, e i rischi

| pezzo | ore |
|---|---|
| immagine `rete11-xfce-xrdp`, xrdp acceso nella scatola, **una sessione a mano** fino al desktop | 2 |
| `16-attore-rdp.py` (Xvfb, xdotool, XDamage, foto, schema di stato) + certifica senza server | 6 |
| `16-compositori-rdp.sh`, `16-risorse.py` (segno e Xvfb), `16-classifica.py --sistema xrdp` | 3 |
| `16-salita.py --sistema xrdp` | 2 |
| prove sul server: 1, 2, 4 utenti da 5 minuti (come §3 punto 3) | 3 |
| **lavoro** | **~16 ore ≈ 2 giorni** |
| **la salita** (XFCE 2K Intel, fino a ~11-12 utenti con la ricerca a metà) | **~2½-3 ore di macchina** |

**I rischi:**
1. ⚠ **I clienti potrebbero cedere prima del server.** 11-12 FreeRDP che decodificano RemoteFX a 2K, col
   video, **sul processore della stessa macchina**. Se succede, la misura diventa un limite **del banco**.
   Il recinto `browser` lo fa vedere, e va dichiarato com'è, senza farlo passare per un numero di xrdp.
2. ✅ **La sonda XDamage: provata l'8 ott sera** sul portatile, in un contenitore Debian 13 (`python3-xlib`
   0.33, Xvfb, `xclock -update 1`): l'estensione c'è, gli eventi arrivano, **~1 raffica al secondo** come
   l'orologio. ⚠ La chiamata è `finestra.damage_create(livello)`, non `display.damage_create`. ⇒ Il rischio
   scende; resta da vederla con FreeRDP che disegna davvero. Il testo di prima, per memoria: Il ripiego sono i registri di FreeRDP
   (`WLOG_LEVEL=DEBUG` sul canale rdpgfx), ma è probabile che nella build di Debian i messaggi dei
   fotogrammi siano spenti. Senza dipinti non si misurano né il ritardo né il blocco ⇒ va provata **per prima**.
3. ⚠ **xrdp dentro la scatola podman** (systemd, PAM, `pam_systemd`, Xorg come utente, glamor sulla
   Intel, Firefox con VA-API su X11) non è mai stato provato. Lo decide la sessione fatta a mano del
   primo pezzo; se non regge si torna dall'utente **prima** di scrivere il resto.

⚠ **Che cosa NON dirà il confronto:** saltati, buchi e audio. Il ritardo lo dirà **dal lato di chi guarda per
tutti e due**, non con il numero della tabella REMOTIX. ⭐ **Che cosa dirà bene:** dove si rompe ciascuno
(stesse soglie per le voci misurate), quanta CPU, RAM e scheda costa ogni utente, e se l'input arriva.
