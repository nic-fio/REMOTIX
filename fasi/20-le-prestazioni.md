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
1. **Il commit del giorno**, identificato, con la **suite corta di regressione** della fase 15 sui 4 desktop
   coi due browser. Non verde ⇒ non si misura.
2. **L'impianto rimesso in piedi sul prodotto di oggi**: i banchi `16-*` sono di prima della fase 18 e 19
   (pagina con WebGL2, niente ffmpeg, strada Vulkan). Ogni misuratore con la sua prova, come allora: un
   misuratore che non ha mai dato rosso non misura.
3. **Una salita di prova** corta (4 utenti, 3 min a livello) per tarare: non conta.
4. **Le campagne, una configurazione alla volta** (le prestazioni non si misurano in parallelo):
   Intel = VA-API su GNOME, KDE, XFCE, LXQt; poi Radeon = Vulkan, stesso ordine.
5. **Il rapporto** e **la tabella pubblica** (§5).

**Quanto dura**, dalla fase 16: ~1 ora e 10 per salita ⇒ ~9 ore di macchina nel caso migliore (8 salite),
~35 se si scende per tutta la scala. A blocchi, anche di notte, e ⛔ **mai mentre l'utente usa il server**.

## 4. Il limite dei 16, dichiarato

Il prodotto oggi ha **16 sessioni fisse nel programma** (`MAX_ATTACCATE` in `src/rcp.c`, DECISIONI §1.11).
Questa campagna misura fino a 16, come la fase 16. **Oltre 16** si misura solo dopo il lavoro «limite deciso
all'avvio» (DECISIONI §10.30), e su una macchina più grande della nostra: oggi non si può.

## 5. Che cosa esce

- **La matrice** della fase 16: desktop × scheda, con ultimo livello GREEN, punto di rottura, gradino della
  scala.
- **La tabella pubblica**, una riga per scheda (e per desktop, se differiscono):

  | macchina | scheda e strada | misura dello schermo | ottimale fino a | degrado da |
  |---|---|---|---|---|
  | i5-13500T, 64 GB | Intel UHD 770 · VA-API | 4K | … | … |
  | i5-13500T, 64 GB | AMD RX 6800 · Vulkan | 4K | … | … |

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
