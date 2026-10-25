# PIANO — REMOTIX 1.5, passo 1: un banco di prestazioni piccolo, validato sulla 1.0

## Obiettivo
Un banco che dica, per un desktop alla volta, quanto costa e come va REMOTIX con 1, 2, 4 e 8 utenti al 3K,
e che dia **lo stesso risultato due volte di fila sulla 1.0**. È il metro con cui ogni punto della 1.5 sarà
giudicato «non peggio della 1.0».

## Perché un banco nuovo e non 16-stress
16-stress (10.000 righe) è quello che ha ingannato il primo tentativo della 1.5. Il banco nuovo è piccolo
(obiettivo: meno di 500 righe), usa solo pezzi già provati dalla suite che ora passa (i driver dei browser di
12-real-clients.py, la creazione degli utenti di suite.py, i box di 11-start.sh) e misura poche cose.

## Cosa misura (per ogni gradino 1 → 2 → 4 → 8 utenti, 5 minuti per gradino)
- **lato server**: CPU e memoria del prodotto per sessione (dai processi del box), uso della GPU;
- **lato utente**: fotogrammi al secondo ricevuti, ritardo delle immagini (come F-003), banda;
- **scena fissa e ripetibile**: la stessa animazione in ogni sessione, con un seme fisso.
Risultato: una riga per gradino in un file CSV, più un rapporto breve.

## Passi
1. Il `programmatore` (Sonnet) scrive `benches/30-perf/30-perf.py` e il suo rapporto, partendo dai pezzi
   della suite. Prova a secco con 1 utente.
2. Validazione sulla 1.0, su un desktop (proposta: XFCE, il più leggero, poi gli altri uno alla volta):
   **due giri completi**; devono coincidere entro una tolleranza decisa **prima** (proposta: CPU e memoria
   ±5 %, fotogrammi ±5 %, ritardo medio ±15 %).
3. Se non coincidono: si corregge il banco (non si misura altro) e si rifà il punto 2.
4. Quando coincide su tutti e quattro i desktop: i numeri della 1.0 diventano il riferimento, commit.

## Regole durante le misure
- Server tranquillo: niente llama-swap, niente build, niente suite (l'analisi dei log in quelle ore va ad
  Haiku); annuncio in /media/server-share.txt.
- Memoria: guardiano come nella suite (stop sotto 6 GB); a 8 utenti al 3K va misurata, non supposta.
- Prima di ogni giro il banco controlla che il server sia vuoto (nessun altro utente, nessuna scena vecchia):
  se non lo è, si ferma e lo dice.

## Rischi
- La tolleranza potrebbe non essere raggiungibile per il ritardo (dipende dal momento): in quel caso si
  misura la variabilità e se ne parla prima di allargarla.
- 8 utenti al 3K potrebbero non stare in memoria con i browser sullo stesso server: lo dirà il primo giro.

## Criteri di completamento
- Due giri concordi sulla 1.0 per ognuno dei 4 desktop, entro la tolleranza.
- Rapporto con i numeri di riferimento della 1.0. Nessuna modifica a `src/`.

## Stima
Scrittura del banco: qualche ora di Sonnet più la revisione. Misure: per desktop 2 giri × 4 gradini × 5 min
≈ 45 min, quindi ~3 ore di server per i quattro desktop (si fanno di notte o mentre si scrive altro).

## Decisioni dell'utente (22 ott 2026)
- 3K = **2880×1620** (16:9).
- Scheda del server: **prima Intel** (come la suite), **poi Radeon**.
- Tolleranza: CPU e memoria per sessione ±5 %, fotogrammi al secondo ±5 %, ritardo medio ±15 %.
- Primo punto di prodotto della 1.5, dopo questo passo: **F-011** (riga verde in fondo con Chrome 156,
  percorso WebGL della pagina).

---

# PIANO — passo 2 (approvato il 22 ott 2026, parte dopo il passo 1): F-011, riga verde con Chrome 156

## Obiettivo
Con Chrome 156 e il percorso WebGL di serie della pagina, nessuna riga verde in fondo all'immagine; Firefox
invariato; prestazioni non inferiori alla 1.0 (tolleranze del passo 1).

## Causa (verificata il 22 ott)
Chrome 156 importa il `VideoFrame` in WebGL con l'area codificata più alta di quella visibile (es. 2082 contro
2064): campionando l'ultima riga visibile, la pagina mescola le righe di riempimento. Codificatore e
decodificatore sono sani (`?canvas=2d` e `?canvas=bmp` passano).

## Passi
1. Il `programmatore` legge in `src/page.html` il percorso WebGL2 (`texImage2D(VideoFrame)`, coordinate di
   texture, filtro) e prova due cure: (a) coordinate ristrette di mezzo texel al bordo visibile; (b) filtro
   NEAREST. Sceglie quella che fa passare F-011 senza toccare le altre righe.
2. Desktop: prima GNOME (dove si vede), poi verifica che kde, xfce, lxqt non cambino.
3. Verifica rapida: F-011 e F-003 su gnome con chrome e firefox (`15-round.py --desktop gnome --tests f011,f003`).
4. Prima del commit: giro completo della suite (nessuna cella verde della 1.0 diventa rossa) e misura A/B con
   30-perf su gnome contro il riferimento della 1.0, dentro le tolleranze. Poi `revisore`.

## Rischi
La restrizione potrebbe tagliare l'ultima riga vera: F-011 controlla proprio quella. Il filtro NEAREST
potrebbe cambiare la resa sotto ridimensionamento: lo guardano F-011 e F-018.

## Criteri di completamento
F-011 PASS su 4 desktop × 2 browser; suite completa senza regressioni; prestazioni entro le tolleranze.

---

# Lavori pronti in coda per i test (scritti e approvati dal revisore il 22 ott, non compilati)
- **F-011** — `src/page.html` nella copia principale (shader: `vis/textureSize`, clamp a mezzo texel, highp).
  Dubbio del revisore: se la riga sbagliata fosse già nella texture (texture = visibile), la cura non basta; lo dice F-011 dal vivo.
- **/diary (§11.10, cambiata il 22 ott)** — ramo `lavoro-diary`: decisione dell'utente «eliminalo del tutto» (nessun banco lo usa):
  niente /diary nemmeno nelle build BENCH; resta la riga locale nel #logbook della pagina, letta dai banchi. BENCH e `.flags` restano per BENCH_MARK.
- **Correzioni piccole (§11.6)** — ramo `lavoro-piccole`: 7 punti, explicit_bzero su password e appunti, BENCH_MARK sotto BENCH,
  annullamento degli aggiornamenti in uninstall.go (+2 test Go da eseguire). Fondere DOPO diary (Makefile identico).
- **D-006** — ramo `lavoro-d006`: chiavi time/counts/trimmed e testi.
Prima del commit di ciascuno: compilazione (normale e BENCH=1, `strings` senza /diary né BENCH_MARK), test Go nel
contenitore, verifica rapida dei test toccati, suite completa, misura A/B con 30-perf contro il riferimento della 1.0.

# Difetti aperti trovati, da trattare a parte
- `src/clipboard_kde.c` read_text (già nella 1.0): non scarta i NUL in mezzo; `last_byte` > `strlen(last)` e la copia di
  riserva in `clipboard_kde_reply` legge oltre il buffer.
- F-003 su kde/firefox: ritardo > 1 s solo con 4 desktop in parallelo (2 giri su 3); da guardare con 30-perf su KDE.
- La scena di 30-perf satura il motore Render della Intel tra 2 e 4 utenti: per il requisito «8 utenti» serve una variante
  con scena leggera (da proporre dopo la validazione).
- DECISIONS §11.41 cita una cura (`6fa5fd60`) che non è in questa base: aggiornare la voce al commit di F-011.

---

# PIANO — §11.9: QUIC Retry e Stateless Reset (approvato il 22 ott 2026; codice ora, test a misura finita)
- **Obiettivo**: chiudere i due vuoti dichiarati in `src/transport.c` («No address validation with Retry», «DECLARED
  FALLBACK» per lo Stateless Reset), come da DECISIONS §11.9 (docs/1.5/DECISIONS-11.md righe 179-204).
- **Cosa**: un Initial senza nostro token riceve un Retry (token di 10 s) e nessuna connessione; con token valido,
  `original_dcid`/`retry_scid` nei parametri; token vecchio o di altro indirizzo → INVALID_TOKEN; illeggibile → ignorato.
  Pacchetto short-header per dcid sconosciuto → Stateless Reset (token dal segreto statico e dal dcid, un byte più corto
  di ciò che è arrivato, al massimo 100/s). Segreto statico in `<certificates>/quic-secret` (0600); se non leggibile o
  scrivibile, segreto della corsa e dichiarato. Dcid del client legato alla connessione (niente seconda connessione
  per un Initial ripetuto). Lunghezza minima del reset contata giusta (Chrome manda pacchetti da 39 byte).
- **Dove**: ramo `lavoro-quic` (/media/REMOTIX-15/lavori/quic); codice nuovo, non quello del primo tentativo.
- **Test (a misura finita)**: compilazione; client di banco (aioquic) per il Retry; Chrome e Firefox entrano;
  riavvio del server → Chrome riceve UN reset e la pagina lo dice subito; fuzz del parser dei token se c'è un banco;
  suite completa; misura A/B 30-perf (atteso: solo un viaggio in più all'apertura).
- **Rischi**: un errore nel Retry blocca TUTTI gli accessi → la suite lo vede subito (F-001). Il reset sbagliato può
  chiudere sessioni vive → controllo che il dcid sia davvero sconosciuto.

---

# PIANO — fuzzing (§11.13, §11.20; approvato il 22 ott 2026)
- **Obiettivo**: fuzzing guidato dalla copertura dei parser che ricevono dati dalla rete PRIMA del login: messaggi RCP
  (src/rcp.c) e richieste HTTP della pagina (src/page.c). Un crash = DoS con un messaggio; un errore di memoria
  prima del login e come root = esecuzione di codice da remoto.
- **Come**: libFuzzer (clang) con AddressSanitizer + UBSan, in un'immagine di build a parte (`Containerfile.fuzz`),
  harness in `benches/fuzz/`, corpus iniziale da messaggi veri, script di corsa con `nice -n 19` e numero di core
  scelto (default 8 su 20). Ramo `lavoro-fuzz`.
- **Quando gira**: durante le suite funzionali (8 core, bassa priorità) e nei tempi morti (tutti i core); MAI
  durante le misure di prestazioni.
- **Esito**: ogni crash = un caso salvato, minimizzato e riprodotto; la correzione passa dal flusso normale.
- **Rischio**: carico sulla CPU che falsa i test sui ritardi della suite (vedi F-003 KDE): se succede, si scende di core.

---

# Regola (22 ott 2026, utente): tutte le funzionalità e tutte le prestazioni si provano con Chrome E Firefox.
Ordine dei prossimi lavori sul server (aggiornato il 22 ott sera, priorità dell'utente: banchi validati su
entrambe le schede entro la sera del 23 ott):
1. fine validazione 30-perf Intel con Chrome (~19:00 UTC);
2. catena notte (lavori/perf-radeon/notte.sh, approvata dal revisore, avviata alle 17:01 UTC): prova breve e
   validazione Firefox su Intel (4 desktop x 2 giri), box sulla Radeon, validazione Radeon Chrome e Firefox
   (1 giro per desktop, 2 su GNOME), box di nuovo sulla Intel; fine prevista ~14-15 UTC del 23 ott;
3. analisi delle misure (Argon) e commit del banco 30-perf + numeri di riferimento della 1.0;
4. pacchetto 1 (F-011, /diary, piccole, D-006): compilazione, verifiche rapide, suite completa (2 browser) con il
   fuzzing a 8 core e bassa priorità in parallelo; ripristino della 1.0 nei box; misura A/B su GNOME con Chrome e
   Firefox, su Intel e Radeon; commit;
5. §11.9 (QUIC) da solo;
6. ULTIMO PUNTO, da valutare con l'utente prima di decidere se farlo — scelta della scheda grafica. Oggi il desktop
   prende la prima scheda apribile (src/session.c card_node, per XFCE/LXQt/KDE; GNOME sceglie mutter da solo) e il
   codificatore usa sempre /dev/dri/renderD128 (src/child.c RENDER_NODE); i numeri 128/129 si scambiano tra due
   avvii. Con 2+ schede: scheda casuale, desktop e codifica possono finire su schede diverse (copia di ~1,1 GB/s
   per utente a 3K60), chi installa non può scegliere. Proposta: scheda scelta per identità (driver/indirizzo PCI)
   con impostazione per chi installa, la stessa per compositor (anche mutter) e codificatore, scritta nel log.
   Nei box (una sola scheda) non cambia i numeri; il valore si giudica con il confronto Intel/Radeon del punto 2.
7. Da valutare con l'utente — misura via Internet con 1 utente: browser (Chrome e Firefox, decodifica software)
   sulla VPS dell'utente, che raggiunge il server attraverso un collegamento WireGuard server→VPS (proposta: il server chiama la VPS, nessuna porta aperta in casa; ExpressVPN dell utente non collega due macchine).
   Misura il ritardo e la banda reali e il comportamento di un client senza GPU. È un banco nuovo, separato dal
   30-perf. VPS: OVH VPS-1 2026, Milano, 4 vCore, 8 GB, 75 GB, Debian 13, senza GPU. Configurazione di rete del server: solo con OK esplicito dell utente.

## Regola dei banchi: tre livelli (approvata dall'utente il 23 ott 2026)
La matrice completa (2 browser × 4 desktop × 2 schede, più Android) non si rifà a ogni modifica.
1. Riferimento completo: le misure della 1.0 su tutta la matrice (chiuse il 23-24 ott); si rifanno solo prima di un rilascio.
2. A ogni modifica, un campione che copre gli estremi:
   - prestazioni (30-perf): GNOME (il più pesante) e XFCE (il più leggero) × Chrome e Firefox, box sulla Intel;
     la Radeon solo se la modifica tocca GPU o codificatore;
   - funzionali Linux (15-suite): giro completo su una scheda, sull'altra solo i test essenziali (F-001, F-003, F-004, F-013);
   - funzionali Android: giro completo su GNOME, sugli altri desktop solo i test essenziali.
3. Se un campione peggiora oltre le tolleranze (CPU e memoria ±5%, fps ±5%, ritardo ±15%), si allarga a tutta la
   matrice solo per la parte colpita.

## Prima del rilascio della 1.5 — noleggio di un server con NVIDIA (deciso con l'utente il 23 ott 2026)
Un solo noleggio, condiviso con un altro progetto dell'utente che ha bisogno di NVIDIA nello stesso periodo.
- Preparazione in anticipo, a casa: lettura del carico GPU NVIDIA nel 30-perf (`nvidia-smi`), provata a secco;
  catene già scritte e collaudate (riferimento 1.0, poi 1.5: suite funzionale e prestazioni, campione dei tre livelli
  più la parte «integrata + NVIDIA» se il punto 6, scelta della scheda, sarà stato fatto); requisiti della scheda
  (NVENC moderno) da indicare all'utente prima del noleggio.
- Convivenza con l'altro progetto: le misure di prestazioni vogliono la macchina tranquilla, quindi si prenotano
  finestre separate (file condiviso come su 192.168.0.2: chi misura ha la macchina da solo; i lavori leggeri
  dell'altro progetto vanno nelle finestre senza misure).

# §11.9 QUIC — Retry e Stateless Reset (approvato dall'utente il 24 ott 2026)
Obiettivo: validazione dell'indirizzo con Retry (ferma i flood con sorgente falsificata; costo: un andata-e-ritorno
all'apertura) e Stateless Reset (dopo un riavvio del server il browser smette subito invece di aspettare 30 s).
Specifica: docs/1.5/DECISIONS-11.md righe 179-204. Codice già scritto: ramo lavoro-quic / backup/quic (src/transport.c
+344 −22, transport.h, main.c 1 riga), compila pulito (24 ott, 0 warning nuovi). Nessun conflitto con il pacchetto 1.
Passi:
1. revisione di sicurezza approfondita (token, lunghezza e tetto del Reset, file del segreto 0600, nessuno stato prima
   della validazione, segreto mai nei log); codice delicato: Opus supervisiona;
2. prova isolata: server di prova in un contenitore con rete propria su 127.0.0.1 + client aioquic
   (benches/01-b2-aioquic-client.py --no-echo): «Retry sent», «address validated with a Retry», sessione ACCEPTED;
3. unione sopra il pacchetto 1, dopo il suo commit;
4. suite completa Chrome + Firefox (ogni connessione passa dal Retry) + mirati F-019, F-020, F-016, F-025, F-026;
5. Reset: kill -9 del server, Chrome e Firefox devono accorgersene subito;
6. misura A/B a campione: Intel, GNOME e XFCE × Chrome e Firefox (non tocca GPU/codificatore → niente Radeon).
Rischi: un browser che non gestisce il Retry; permessi del file del segreto.
Fatto quando: suite verde, Reset osservato su Chrome e Firefox, misura dentro le tolleranze.
Non compreso: i limiti di connessione (DECISIONS-11.md 895-969), che dipendono dal Retry: piano a parte.
Limite dichiarato (utente, 24 ott): Retry e INVALID_TOKEN senza tetto al secondo — nessuna memoria e nessuna amplificazione, solo un po' di CPU per Initial falso; accettato, nessun tetto da aggiungere.

# Limiti di connessione (DECISIONS-11 §11.40, approvati dall'utente il 24 ott 2026, dopo §11.9)
Obiettivo: nessuno può tenere aperte tante connessioni senza login. Tetti sulle connessioni non ancora entrate
(8 per indirizzo/64, 32 per /48, 128 in tutto, 256 connessioni totali), oltre il tetto CONNECTION_REFUSED senza stato e
solo dopo il Retry; a server pieno si chiude la più vecchia non ancora alle credenziali (mai wait-verdict né entrate);
chiusura a 90 s senza login; token Retry monouso (TOKENS_KEPT 4096). Prezzo: 8 login contemporanei dietro un NAT.
Codice: dal tag 1.5-scartata (archivio sul portatile, commit 2f671726, a723eb6b, f4201ee6, d0e56764), portato a mano
sopra quic-su-p1; NON i commit successivi (wait-verdict espulso, budget log). Banco: 01-b10-flood.py + launch dal tag.
Passi: porting (ramo limiti-su-quic) → revisione di sicurezza → 01-b10 con tetti piccoli (16/4/8) 3 volte 9/9 →
tetti di default dal vivo → suite completa → A/B a campione.
Fatto quando: 01-b10 9/9 ×3, suite verde, A/B nelle tolleranze. Fuzz quic-conn: solo se si recupera rxtest (a parte).
Note della revisione di sicurezza dei limiti (24 ott, APPROVATO):
- transport.c:74 e :758 (ramo limiti-su-quic): il commento dice che address_key segue rcp_key_address(), ma qui
  rcp_key_address() toglie solo la porta (la §1.9-bis, archivio 86cfbce4 + 4c00414e, non è portata). Da fare: correggere
  il commento prima del commit del ramo; il porting della §1.9-bis (ban per /64 ecc.) è un lavoro a parte da proporre.
- reap_dead: «connection … closed (N left)» senza limite di righe; sotto churn ~200 righe in 20 s. Limite dichiarato
  oppure stessa finestra di BIRTH_LINES: da decidere.
- read_packet usa c->local come path.local invece dell'indirizzo di arrivo (transport.c ~1547, già nella 1.0): con più
  indirizzi locali la risposta e la validazione partono dall'indirizzo sbagliato. Trovato dal fuzz quic-conn il 24 ott
  (caso in benches/fuzz/quic-conn/known/local-end-1.0.bin, ramo limiti-su-quic). La correzione va proposta all'utente.

# Decisioni in attesa dell'utente (24 ott)
1. Scena «testo che scorre» in 30-perf per verificare gli 8 utenti (rimisura 1.0 su campione, ~6-9 h).
2. Limitare le righe «connection closed» sotto flood (proposta: sì, come BIRTH_LINES).
3. §1.9-bis (blocco per /64 IPv6): proposta rimandare, limite dichiarato.
4. KDE 8 utenti su Radeon: proposta dichiarare «non misurato per memoria».
5. F-031 (difetto vero del prodotto, Chrome Android emulatore): keyboard_close rifocalizza dopo hide(); proposta A:
   readOnly + inputmode none + blur, hide() dopo il blur, niente refocus alla chiusura (page.html ~12289, 12339); B se A non basta.
6. Difetto della 1.0 trovato dal fuzz: read_packet usa c->local come path.local (transport.c ~1547): correzione da proporre.
7. F-014E come test della suite (bozza in lavori/android-ev/f014e).
   Dettaglio (24 ott): anche path.remote e gli invii usano gli indirizzi di nascita: un client che cambia rete
   (Wi-Fi→dati, NAT rebinding) perde la sessione dopo 30 s. Proposta: percorso ricevuto + send_on + cb_path_validation
   (~60-80 righe, dal tentativo scartato b207ad85/70b58f66), put_source (~190) solo per il caso multi-indirizzo.
Risposte dell utente (24 ott ~07:40): 1 sì, 2 sì, 3 dopo, 5 (Android) domani col telefono, 6 sì, 7 sì.
4: limite del BANCO, non del prodotto (RAM del server: ~1,1-1,2 GB/utente il box KDE + ~1,5-2 GB/utente il Firefox di prova,
che in esercizio sta sul dispositivo dell utente). Dichiarato: «8 utenti KDE su Radeon non misurabile su questo banco;
in esercizio ~9-10 GB». Conferma con client su altra macchina o sul server NVIDIA.
- read_packet dava il segnale di vita (wt_sign_of_life) per ogni pacchetto con rv == 0, anche quelli che ngtcp2 scarta (non
  decifrabili, duplicati, da percorso sconosciuto nell'handshake): difetto già nella 1.0, trovato dal fuzz quic-conn il
  24 ott. Corretto nel ramo migrazione-su-limiti (il segnale parte solo se pkt_recv è aumentato).
F-011 (24 ott, suite p1-intel): la cura dello shader NON basta. GNOME/chrome resta FAIL (riga 2063 (0,57,0) identica a round6);
XFCE/KDE/LXQt passano solo perché il verde è più debole (XFCE (0,24,0), sotto la soglia del test). Riga già sbagliata nella foto:
sospetto conversione RGB→NV12 dell ultima riga (vadirect) o decoder di Chrome. Prove in preparazione: decodifica software del
flusso (ffmpeg) e Chrome con --disable-accelerated-video-decode. Il test F-011 va reso più severo (soglia del verde) dopo.

## Impegno con firefox-wbcodecs (24 ott)
Dopo la fine dell A/B 30-perf (stima ~15:00) mandare a firefox-wbcodecs «Radeon libera»: per loro llama-swap 1-2 h, poi una misura di ~20 min (server tranquillo). Le nostre catene pesanti aspettano la loro riga «fine».
Aggiornato: fine suite p1-intel -> mandare «finestra aperta» a firefox-wbcodecs (llama-swap max 2 h) + lanciare coda-dopo-suite.txt (solo funzionali). coda-ab.txt parte solo dopo il loro «llama-swap spento» E la fine di coda-dopo-suite. Fine A/B (~19:00) -> «Radeon libera».
F-031 cura A: ramo f031-a 4be9d715 APPROVATO (solo lettura). Domani sul telefono: provare anche appunti attivi + tocco sul canvas dopo la chiusura (paste_field_keep riprende il focus con inputmode=none: se la tastiera si riapre, rivedere paste_field_keep per Android).
F-011 cura (b): ramo f011-riga 127f69a6 (Opus, shader: ultima riga ripete la precedente se textureSize.y > vis.y) APPROVATO. Prova: pacchetto1-ab/f011-riga-prova.sh (in scrittura) dopo la suite.
F-014E: ramo f014e-int (22ea3008, 550b1b37, 396f7dae; 15-round.py DESKTOPS) APPROVATO. Da unire in pacchetto1 DOPO la suite (fast-forward: f014e-int parte da 5cf8ca10).
pacchetto1b (5cf8ca10 + F-014E + F-011 cura b + doc aa271550) APPROVATO in revisione; f011-riga-prova.sh APPROVATO e aggiunto in coda-dopo-suite.txt.
Scena text: testo-1.0-campione.sh APPROVATO; coda-testo.txt (prova breve + completo) va DOPO coda-ab e DOPO la misura di firefox-wbcodecs, prima di coda-sera.
coda-ab (pulizia tenant generica, prova-igt con pulizia P3, installatori) APPROVATA; f031a-telefono.sh APPROVATO (domani col telefono); coda-dopo-suite + f014e-p1b (KDE).
F-015C (dentro 15-f014c) chrome FAIL lxqt/kde/xfce in p1-intel: server e pagina OK (40 byte inviati, pagina «written 1»), ma wl-paste del labwc host resta sul vecchio testo; 1.0 round 6: 12/12 PASS. Da decidere con le ripetizioni (ripeti-f003-f014c): p1 KO e 1.0 OK = regressione (sospetto clipboard_kde.c, ma il testo arriva giusto al client); entrambi KO = ambiente host (labwc riavviati 05:39); entrambi OK = carico. F-003 lxqt/kde: firma da carico (finestra non allargata / canvas 1280x720), page.html p1 non tocca il ridimensionamento.
F-015C, analisi del diff 1.0 (04f6aa18)..5cf8ca10: write_to_clipboard invariata, nessun cambio di focus o permessi; il testo arriva giusto alla pagina. Ipotesi: labwc scarta set_selection di Chrome (serial) oppure il wl-copy «prima-di-P1» tiene la selezione. Gnome passa per un altro percorso (testo già servito prima del Ctrl+C). Le ripetizioni p1 contro 1.0 decidono; se resta dubbio: diagnostica wl-paste --list-types / pgrep wl-copy / userActivation nel test.
F-015C: diagnostica nel test (pacchetto1b 67c3931a+eb7d734d, APPROVATO); ripeti-f003-f014c ora gira con --ramo pacchetto1b (p1 + F-014E + F-011b + diagnostica) contro 1.0.
Fuzz 24 ott 09:32 sul ramo limiti: crash subito in wt_sign_of_life (difetto «segno di vita» della 1.0, già corretto in migrazione 9f7e2419): atteso. Rilanciato 30 min sul ramo migrazione (oracoli accesi).
Difetto 1.0 trovato dal fuzz (oracolo pacing): write_connection con buffer 64 KB e num_pkts=0 scavalca il pacing (fino a ~45 pacchetti per chiamata). Cura (Opus): ramo pacing-su-migrazione 643e9a40 (raffica = send quantum, minimo un pacchetto pieno) APPROVATO + 3a6d128c (attesa del ciclo arrotondata per eccesso) in revisione. Fuzz 30 min in corso; micro-banco pacing-ab.sh in scrittura. Da misurare con A/B prima di entrare.
pacchetto1b + 71970919 (diagnostica F-015C nella pagina) APPROVATO.
Audit nghttp3 (webtransport.c, nghttp3 1.18.0), da piano a parte: (1) close_stream non chiamata se lo stream chiude senza codice -> stato nghttp3 cresce per tutta la connessione (medio); (2) ritorni ignorati di shutdown_stream_read (QPACK_FATAL) e unblock_stream; (3) STOP_SENDING del client usa shutdown_stream_read invece di _write; (4) STREAM_NOT_FOUND da writev_stream trattato come fatale; (5) cb_rand con rand(); (6) da verificare: secondo CONNECT pre-login riarma il tetto di 5 s. Pacing fuzz 11 min: nessun crash.
Audit ngtcp2 (transport.c), da piano a parte: (1) NGTCP2_ERR_DROP_CONN da read_pkt risponde con CONNECTION_CLOSE invece di scartare in silenzio (medio, riflesso verso pacchetti non autenticati); (2) ERR_CRYPTO chiuso senza alert TLS; (3) handle_expiry: errori diversi da IDLE_CLOSE senza CONNECTION_CLOSE; (4) SSL_free dopo ngtcp2_conn_del senza SSL_set_app_data(NULL); (5) API deprecate 1.23; (6) credito stream forse doppio; (7) handshake_timeout non impostato.
audit-ngtcp2 (d624d875..8171e6c1) APPROVATO intero. audit-nghttp3: 672c9d42 e7c469f1 86af9276 b6e3c5c1 f395aff5 APPROVATI, 513b3b21 corretto da fb0c6cd6 (in revisione). Bozza per l utente: /media/REMOTIX-15/tmp/proposta-audit-bozza.md. NON entrano senza OK dell utente. Banchi: pacing-ab.sh (APPROVATO, in coda-ab), stream-churn.sh (in revisione), fuzz rcp-msg (in revisione).
10:01 rilanciata coda-dopo-suite (il primo lancio era fallito: un mio lanciatore rimasto vivo contava come test vivo).
GSO: nota /media/REMOTIX-15/tmp/nota-gso.md, conclusione: oggi non conviene (80-300 pacchetti/s misurati, ~0,1% di un core); da rivalutare oltre ~5000 pacchetti/s.
audit-tutto HEAD 3c0fa624 (pacing + audit-ngtcp2 + audit-nghttp3 con 515c2e7a/4923f68d judgments, tutti APPROVATI; fuzz-rcp c1b453b3). coda-audit.txt pronta (fuzz 30 min x2, stream-churn prova+completo): va dopo coda-testo.
audit-tutto docs §11.52 (3516661d) APPROVATO.
Audit login/PAM/ban (bozza, in verifica): 8 punti (connessioni chiuse prima del verdetto non contate; ban controllato prima del conteggio; ban per indirizzo intero su IPv6 -> /64; NAT; tabella 256; tempi denied-users; tetto PAM globale; nome utente nei log). Scelte di progetto: decide l utente (collegato a IPv6 §1.9-bis rimandato).
Audit page.html (pulito su innerHTML/eval/URL/storage). Proposte per l utente: (1) intestazioni CSP + frame-ancestors none + Referrer-Policy + Permissions-Policy in page.c:150-163 (manca anti-clickjacking sul form password); (2)/(3) appunti automatici nei due sensi senza gesto: scelta di progetto della 1.0, valutare opt-in/indicatore; (4) tetto alla tela concessa dal server (tl/ta da SESSION, page.html:6080). Modello di minaccia: server compromesso = pagina compromessa (da scrivere).
Audit login verificato dal revisore: 6 confermati + 2 parziali (2 e 7 ridotti nella 1.5 da PENDING_PER_ADDRESS 8), tutti presenti nella 1.0. Correzioni = scelte di progetto (ban per /64, conteggio dei tentativi in volo e delle connessioni chiuse, NAT/reset per utente, log del nome utente, ritardo uniforme): da proporre all utente. child.c: stringhe senza zero nei messaggi del figlio (MSG_INTRO runtime, MSG_STAGE monitor/fault) -> letture oltre la struct nel log; corretto in audit-tutto d80a4244 (in revisione), presente dalla 1.0.
audit-tutto: d3a16466 (tetto tela) e 65e78f14 (CSP/Referrer/Permissions-Policy) APPROVATI. DA FARE dopo la suite-aud: restringere connect-src a self (oggi self + https:).
Android domani: bash /media/REMOTIX-15/lavori/android-ev/f031a-telefono.sh --ramo /media/REMOTIX-15/lavori/f031-a-p1b (pacchetto1b + cura A 52f34b55; script APPROVATO).
audit-tutto: bd4840db (guardia troncamento header) e 7666cd75 (test unitario muro del figlio, 12/12) APPROVATI. HEAD audit-tutto = 7666cd75.
10:57 Ripetizioni (un giro alla volta, pacchetto1b contro 1.0): F-003 e F-014C/F-014D/F-015C tutti PASS su 4 desktop, sia p1 sia 1.0 (un giro kde p1 perso per preflight KO da build.sh). Conclusione: i FAIL di p1-intel erano carico da 4 desktop in parallelo, NON regressioni.
F-011: f011-decoder -> anche col decoder software riga 2063 (0,57,0) vs 2062 (34,33,38): non e il decoder hardware, conferma la conversione RGB di Chrome. f011-flusso: non conclusivo (survey non scritto). In corso f011-riga-prova (cura b).
11:09 f011-riga-prova: la cura (b) NON basta su Chrome (gnome riga 2063 ancora (0,57,0), xfce (0,24,0)); Firefox OK. Ipotesi: Chrome carica una texture grande quanto il visibile, già tinta. Cura (c) Opus 571c8145 (uniform trim da VideoFrame codedHeight > visibile) in revisione; da riprovare con f011-riga-prova.
F-014E su KDE: BLOCKED 2/2 (il prodotto non scrive la riga sulla copia): in analisi.
11:11 lanciata suite-aud-prova (audit-tutto, funzionale, accetta llama-swap) nella finestra di firefox-wbcodecs.
F-014E BLOCKED: g_utf8_validate_len rifiutava gia lo zero, il controllo memchr di 8031958d era irraggiungibile (comportamento corretto, riga di log sbagliata). Correzione Opus pacchetto1b 322468ea (memchr prima di UTF-8), in revisione. Cura F-011 (c) APPROVATA, pacchetto1b 3a4d447d. coda-riprova.txt (f011-riga-prova + f014e) dopo suite-aud-prova.
322468ea APPROVATO. DA FARE: stesso spostamento in clipboard.c (GNOME, codice 1.0) alla prossima occasione con prova GNOME.
11:15 suite-aud-prova VERDE (audit-tutto: CSP, pacing, audit). 11:16 riprova F-014E. Ordine: fine llama-swap (~11:53) -> coda-ab; f011-riga-prova (cura c) dopo l A/B; poi coda-testo, coda-audit.
11:21 F-014E PASS 2/2 su KDE (pacchetto1b 322468ea). 11:22 riprova F-011 cura (c).
11:33 F-011 RISOLTO con la cura (c) (f011-riga 571c8145+9b963d77, in pacchetto1b 3a4d447d): 8/8 PASS gnome/xfce x chrome/firefox, riga 2063 = 2062 (scarto 0). Per la prima volta F-011 verde su gnome/chrome (anche la 1.0 falliva).
12:10 llama-swap ancora acceso oltre le 2 h: lanciata suite-aud completa (audit-tutto, funzionale). Poi coda-ab (A/B), poi Radeon a firefox-wbcodecs, poi coda-testo, coda-audit (fuzz/stream-churn/pam-tempi).
13:20 firefox-wbcodecs: llama-swap spento, riga fine. Resta la loro misura di 20 min dopo il nostro A/B. Al termine di suite-aud: lanciare coda-ab.
24 ott 13:2x UTENTE: (1) SI, i difetti della 1.0 si correggono (rami audit, dopo i test). (2) login: spiegare in parole semplici. (3) telefono domani. Sforamento tempi accettato; continuare a sincronizzarsi con firefox-wbcodecs.

## Difese del login (decisione delegata dall utente al capo-progetto, 24 ott 13:40)
Pareri raccolti: Gemini Argon, ChatGPT, gpt-oss-20b, Laguna (LFM muto). Sintesi adottata:
A. Chiave del ban: IPv4 indirizzo intero; IPv6 il /64. In piu un limite aggregato per IPv6 /48.
B. Tentativi in volo: alla ricezione di CREDENTIALS si prenota il tentativo (contatori = falliti + in volo, controllo atomico prima di chiamare PAM). Al massimo 2 verifiche PAM contemporanee per (chiave, utente). Se la connessione cade il verdetto vero viene comunque registrato (struct flight conserva indirizzo e utente); un tentativo senza verdetto (timeout PAM / tetto 12 s) conta come fallito; un rifiuto per difetto nostro non conta.
C. Contatori a tre livelli, finestra scorrevole:
   (chiave, utente): 5 falliti in 5 min -> ban di (chiave, utente)
   chiave: 12 falliti in 5 min (qualsiasi utente) -> ban della chiave
   IPv6 /48: 30 falliti in 10 min -> ban del /48
   Durata progressiva per livello: 15 min, poi 1 h, poi 12 h (massimo); le recidive si dimenticano dopo 24 h senza ban.
   Login riuscito: azzera solo i falliti di (chiave, utente), non le recidive ne i contatori aggregati.
   La tabella non scarta mai una voce bannata; se piena rifiuta la nuova voce (e conta il rifiuto) invece di espellere un ban.
   UNBLOCK <indirizzo> toglie tutti i livelli che lo riguardano. Il file dei ban persistente passa al nuovo formato (righe vecchie lette e convertite).
   CAMBIO DI SPECIFICA rispetto alla 1.0 (12 h fisse dopo 3 errori): da scrivere in docs/1.5/DECISIONS-11.md e nel manuale.
D. Registro: utente inesistente -> "unknown user [xxxxxx]" con HMAC-SHA256 troncato a 6 esadecimali, chiave segreta del server in un file 0600 (come il segreto dei token QUIC); nessun carattere del nome in chiaro. Caratteri di controllo gia rifiutati.
Fuori da questo giro: ritardo uniforme (prima misurare con pam-tempi), punti tecnici gia coperti da PENDING_PER_ADDRESS.
Ramo: login-difese da audit-tutto. Verifica: test unitario della logica dei contatori (tempo simulato), harness rcp-msg con oracoli nuovi, suite funzionale (F-027 password e ban), pam-tempi.
Documentazione da aggiornare per le difese del login (elenco del 24 ott): docs/sources/user/ch02_installing.py 149-152, 207; technical ch14_security.py 236-316 (+556,600,615), ch05_rcp.py 265-310, 741, 842; ch03_lifecycle.py 31-38, 102, 148, 167, 514; ch13_logging.py 364 (+242,327,509); ch04_transport.py 248-270; ch09_page.py 29-38; ch02_architecture.py; ch24_glossary.py 154-174; ch17_build.py; SPECS.md 285-295; RCP.md 4.4-bis (839-965), 2252; DECISIONS.md 1.9; README.md 904-906. Rigenerare con docs/sources/build.py.
integrazione 9be508c7 = audit-tutto (30d54409) + pacchetto1b, merge pulito, build OK. Da provare: suite completa + A/B su questo ramo dopo l A/B del pacchetto 1 (o al posto delle catene qp1/mig).
Doc F-011c/F-014E pacchetto1b fc930962+9c770c61 APPROVATI; manuale tecnico audit-tutto 8da223d5+4324ba93+30d54409 APPROVATI. Da fare: F-011 cura (c) su kde e lxqt (coda-f011-kde.txt).
Difetto 1.0 trovato dal test unitario: KDE con appunti vuoti -> memchr(NULL,0,0) (UB) e testo vuoto annunciato; corretto pacchetto1b b3f8cde6 APPROVATO (in integrazione 10728a71).
integrazione 475074d3: build, unit test (12/12, clipboard 6x2), 3 fuzz build + replay semi: tutto OK. coda-audit punta ai fuzz di integrazione.
login-difese (8f56da22..28e216b6): revisione DA CORREGGERE (prenotazione persa con helper scaduto/morto e connessione chiusa; morte helper non deve contare; nomi in chiaro nel file ban -> HMAC + 0600; link-local con scope -> /64 (decisione capo-progetto); exp estremi; getpwnam dopo la prenotazione). Correzioni in corso.
coda-notte.txt scritta (integrazione: suite+A/B, poi f011 kde/lxqt, fuzz, churn, pam, pacing, b10, migrazione). coda-testo (p1-radeon + testo 1.0) e notte-radeon3 dopo.
login-difese a966e37d APPROVATO (dopo correzioni: helper morto non conta, HMAC nel file ban 0600, link-local /64). In fusione in integrazione.
integrazione a31510b4 = tutto + login-difese: build, unit (12, 6x2, 595, 14), fuzz build+replay OK.
integrazione 871c2e0a: + login-difese (testi pagina, doc, B8) + §1.9-bis chiusa (test address-key 150/150). Tutto APPROVATO, build e unit verdi. Pronta per coda-notte.
14:39 suite-aud: 0 regressioni (mancanti = test non eseguiti, come per p1). coda-ab fermata al preflight di prova-igt: righe fine di firefox-wbcodecs senza [inizio ...]; chiesto a loro. Pronta coda-ab2 (da prova-igt).
14:41 coda-ab2 avviata (prova-igt -> pulizia -> installa 30-perf -> reset -> fuzz -> pacing-ab -> ab prova -> ab completo). Poi: Radeon libera a firefox-wbcodecs (20 min), poi coda-notte + f011 kde/lxqt (gia in coda-notte) + coda-testo.
14:47 prova-igt PASS (prove 1,2,4); banco unico 30-perf INSTALLATO; reset-prova OK; fuzz 60 s OK; in corso pacing-ab, poi A/B.
pacing-ab 14:49: RTT a riposo +1 ms con il ramo pacing (arrotondamento per eccesso di 3a6d128c). Correzione Opus integrazione 1b447d3c (ppoll al ns), in revisione. Bulk = 0 byte: banco da sistemare (a1cc). ab: bug strings|grep -q con pipefail corretto in ab-pacchetto1/ab-ramo (grep -qa); A/B ripartito 14:58.
1b447d3c (ppoll) APPROVATO; da verificare con pacing-ab (RTT a riposo ~1,3 ms) nella coda della notte.
pacing-ab v3: la fase bulk non e misurabile in contenitore (niente bus di sessione, niente video); resta valido l RTT a riposo. In coda-notte pacing-ab --dopo integrazione per verificare il ppoll.
15:25 ab-p1-prova VERDE (4 giri, 1.0 ripristinata). 15:26 partito ab-p1 completo (stima ~5 h, fine ~20:30-21:00).
⚠ 15:37-15:39 una mia compilazione (2 core, nice 19) e girata durante l A/B (giro gnome chrome, intel-p1-chrome/gnome/run1): nel leggere l A/B controllare quel gradino; se fuori tolleranza, ripeterlo. Da ora: niente compilazioni durante l A/B.

## SCOPERTA 24 ott 15:45: DECISIONS-11 descrive lavoro del tentativo scartato NON presente in questo albero
117 hash citati non esistono (vengono dal tentativo 1.5 scartato). Modifiche descritte come fatte ma ASSENTI dal codice:
URGENTI (difetti 1.0 / codice nuovo): (1) §11.44 pagina: MAX_CLIENTS 32 senza scadenze -> 32 TCP inattive bloccano il login; (2) §11.48 sonda video 64x48 senza seconda prova 320x240 -> Firefox VA-API AMD rifiutato; (3) §11.29 LXQt nero dopo riavvio (pcmanfm-qt), e §11.34 dice che la 1.5.0 la contiene; (4) §11.39 codice 0x0E per rifiuto nostro + RESERVED_FOR_KNOWN; (5) §11.43 orologio 30 min azzerato da qualunque byte; (6) §11.4 loginctl terminate-user ancora in child.c; (7) rpm spec senza %ghost quic-secret/log-secret.
DECISIONI PRESE NON PORTATE: PACE, worker Firefox di default, scheda encoder (render_node), solo nodi render, filtro unchanged KDE, nome stream audio remotix-capture, KWin annidato 1280x720, ricevute tasti, margini encoder, refusal_uncounted/faillock, intera fase §11.50 separazione privilegi (rootside).
=> la stima di completamento della 1.5 va rifatta: queste voci sono parte del lavoro 1.5 da rifare.
Porting dal tentativo scartato: port-pacchetti (rpm/deb/arch segreti, render-grants) APPROVATO; port-sessioni (render_grant §11.4, disinstallatore) APPROVATO; port-pagina (serie §11.44 + sonda) in corso; port-rcp (LXQt, 0x0E, orologio 30 min, B100, known-key) in revisione. Tutti da compilare/provare dopo l A/B.
port-rcp (LXQt, 0x0E, orologio, B100, pick_victim, verdetto senza attesa, RESERVED_FOR_KNOWN) APPROVATO; in arrivo faillock 249c534a.
integrazione2 (da 5f6e0c58): merge port-pacchetti c89a1163, port-sessioni 6349f4f2, port-rcp 917e16c3 (incluso faillock 65007a7b, revisione in corso), gemello 331077a2. Da compilare dopo A/B; poi coda-notte su integrazione2.
integrazione2 HEAD 70e5bd03: + Makefile fb43b8a0 (approvato), port-scheda f155cded (approvato), port-kde 70e5bd03 (approvato). In attesa: port-rcp a560aabf/fddead5f (revisione), port-varie (revisione), port-pagina (revisione + 88b08213 in porting).
24 ott 16:05 REGRESSIONE trovata (revisore port-varie): dalla 84fdf573 la build di prodotto (senza BENCH) dichiara 5 capacità in HERE_I_AM e ne scrive 4. Corretto su integrazione2 549a9e06 (da revisionare). Le misure BENCH=1 non ne sono toccate. Da aggiungere: test della build senza BENCH (handshake con la pagina) nella verifica-rami.
integrazione2 HEAD 43e2517e: + 549a9e06 n_caps (approvato), here-i-am test a8562965/43e2517e, merge port-varie 3614a853, merge port-rcp completo c9957bad (revisione in corso). Mancano: port-pagina (revisione), fuzz-pagina (in scrittura). Inventario: /media/REMOTIX-15/tmp/inventario-mancanti.md; §11.50 rootside ~136 commit in analisi; §11.36 Firefox worker e PACE di default = decisioni da prendere.
16:08 integrazione2 43e2517e: merge port-varie e port-rcp APPROVATI. Resta port-pagina (correzioni in corso) e fuzz-pagina.
16:10 ATTENZIONE A/B: tra ~16:02 e ~16:09 git am senza nice (analisi rootside) + build-free: controllare la finestra nel passo gnome-chrome come per la build 15:37-15:39. §11.50 rootside: analisi in /media/REMOTIX-15/tmp/rootside-analisi.md, 13-19 giornate stimate; da decidere con l utente (traguardo dopo fase D + 24-privsep-cost.sh).
16:13 integrazione2 d6e976f3: + merge port-pagina 69843995 + PAGE_SECURITY ovunque 68d867d3 + Makefile d6e976f3 (in revisione). DOPO A/B: verifica-rami.sh su integrazione2 (build BENCH + prodotto + unit + fuzz replay), poi coda-notte su integrazione2 (sostituire integrazione → integrazione2 nelle righe).
16:20 integrazione2 39d8b27e tutto APPROVATO (pagina, flood test). coda-notte2.txt pronta (int2). In corso: fuzz-pagina, verifica-rami fix, rootside fasi A+B (port-rootside) ed E (port-rootside-inst).
16:30 §11.50: port-rootside-mura (fase C + rinforzi 396aeb96/90f940b5) APPROVATO; port-rootside (A+B) in revisione sicurezza; port-rootside-inst (E) correzioni in corso; port-rootside-pacch (F) in porting. Fase D (ganci) = da pianificare con l utente. integrazione2 4f64e7c8 tutto approvato.
16:31 nota A/B: un gofmt in podman (golang) lanciato da un agente intorno alle 16:28, passo gnome-firefox. Breve.
16:36 integrazione2 d0448300: + manuale sorgenti 522603f9 (revisione) + fuzz page. Nota: costante utenti 10 nel codice vs specifica 1.5 max 8 (non toccata).
16:45 §11.50 rami approvati (non compilati): port-rootside A+B (+52664b86 guardia container), port-rootside-mura C, port-rootside-inst E (81e061b4), port-rootside-pacch F (0f88d5b1, interruttore spento). Mappa fase D in scrittura (/media/REMOTIX-15/tmp/rootside-fase-D.md).
16:50 integrazione2 7347845d: + manuale 3310beda, closing-ticket test cbadf16c, here-i-am 8 varianti: APPROVATI. In corso: render-grant unit test, mappa fase D.
16:55 §11.50 fase D: mappa in /media/REMOTIX-15/tmp/rootside-fase-D.md (~63 h, D1..D7). Avvio D1 (child_birth/child_outcome) e D2 (render_grant_remotix_session) su ramo port-rootside-D: il prodotto resta un processo solo, provabile con i test di oggi. D6 (main in due metà) cambia il servizio: DA DECIDERE CON L UTENTE prima di unirlo. Domande per l utente: helper con re-exec e riavvio (consigliato sì); PACE resta spento (non portare il cambio di default dell archivio).
17:00 port-rootside-D: D1 035c7af0 + D2 21210662 APPROVATI (nessun cambio di comportamento). D3 helper in corso (port-rootside-D3), D4 in valutazione. integrazione2 50e33f6f (ricette unit allineate, revisione).
17:05 port-rootside-D: D4a 5226ca40 APPROVATO. integrazione2 50e33f6f APPROVATO (18 ricette unit estraibili).
17:15 programma dopo A/B: (1) Radeon libera a firefox-wbcodecs, loro misura 20 min; (2) coda-verifiche-int2 (~95 min); (3) se verde: coda-notte2 su integrazione2; (4) domani: coda-verifiche (rami rootside, ~6 h) di giorno.
17:20 D6 piano scritto (rootside-fase-D.md): --split spento di default, stesso binario; punto debole rollback → remotix-net-move --back in scrittura. DA DECIDERE CON L UTENTE: accendere lo split in 1.5 o spedire spento.
17:25 port-rootside-D: D5 d51b28bf APPROVATO (inerte). Prossimo: D6 con --split spento, dopo net-move --back.
17:30 prova unione rootside: /media/REMOTIX-15/tmp/rootside-unione.md, 4 conflitti banali; aggiunta a coda-verifiche.
17:40 D3 corretto 7645beb7 (esito 4 = scaduta conta), in revisione; net-move --back e3656300 in revisione; D6 in corso; D4b (via il PAM sincrono: CAMBIO voluto) in corso su port-rootside-D3. Stato per utente: /media/REMOTIX-15/tmp/stato-1.5-per-utente.md
17:50 net-move --back 3ca9efa6 APPROVATO. D6 c4f28c02 in revisione.
18:00 D6 c4f28c02 APPROVATO (split spento = identico; --split da bloccare con 78 finché incompleto). D4b 4114e15e+77705c5c in revisione.
18:10 D4b 4114e15e+77705c5c APPROVATI. D6 fix 6e325b22 (--split bloccato salvo REMOTIX_SPLIT_EXPERIMENTAL=1). In corso: ri-unione D3 in port-rootside-D + helper remoto.
18:20 firefox-wbcodecs chiude per il weekend: niente misura 20 min, niente Radeon libera da mandare. Dopo A/B: subito coda-verifiche-int2.
18:25 UTENTE: server tutto nostro (firefox-wbcodecs chiusa). Piano: A/B fino ~19:15 → coda-verifiche-int2 → coda-notte2 (+ passi Radeon: coda-testo p1-radeon, notte-radeon3) → domani coda-verifiche rami rootside + pareri LLM locali.
18:35 port-rootside-D 8d5629f3 APPROVATO (D1-D6 + D3/D4b + helper remoto; split OFF = integrazione2+D3/D4b; split ON sperimentale). Mancano per accenderlo: D7 integrazione/prove, installer+pacchetti uniti.
18:50 rootside-completo f5c81bc0 (D7 unione di tutto §11.50) in revisione; coda-verifiche = integrazione2 + rootside-completo.
16:59 NOTA: gli orari scritti a mano nelle righe sopra (17:00-18:50) erano sbagliati, avanti di ~1-2 h; da qui uso date del server.
17:00 rootside-completo f5c81bc0 APPROVATO.
17:03 banchi pam (02-pam-start/standstill) riscritti e APPROVATI su port-rootside-D3 (6ca95430); in unione verso rootside-completo.
17:04 rootside-completo ffab7609 pronto per verifica.
18:56 UTC: CORREZIONE: il server è in UTC (Italia = UTC+2). La mia nota delle 16:59 sugli «orari sbagliati» era errata. Fine A/B ~19:55 UTC = 21:55 italiane.
20:04 A/B p1 finito: fps/ritardo uguali ovunque; mem molto meglio su chrome; CPU +6-14% su xfce-chrome (sistematico), gnome-firefox 6 utenti +29% (finestra del processo sh 16:53?), xfce-firefox mem +5-16% nei gradini bassi (dentro ripetibilità 1.0). Da ripetere: xfce-chrome e gnome-firefox. Lanciata coda-verifiche-int2.
20:06 build integrazione2: 1 solo errore (rcp_logged_in), corretto 879cf5fa APPROVATO; BENCH e prodotto puliti. rootside-completo: build pulita, test-walls 11/11, test-rootside 56/56 (0e086424).
20:16 verifica integrazione2 giro 2: build OK (BENCH+prodotto), 22 PASS, 6 FAIL (child-closing, evict/orphan, log-nonblock, login-ban, wt-prelogin, fuzz-quic-conn) → in analisi.
20:20 6 FAIL corretti (5 nei test, 1 nel prodotto: 61ea9a6c 429 seconda sessione non contato prima del login) → revisione.
20:23 0b4d3bda+4be3a981 APPROVATI; giro 3 di verifica integrazione2 in corso.
20:28 VERIFICA integrazione2 4be3a981 VERDE 28/28. Lanciata coda-notte2.
20:29 coda-notte2 partita (suite-int2-prova in corso). rootside-completo d283a02b (unione integrazione2 + guardia uid0 2249b570) build OK, test-rootside 56/56, go test verde; revisione in corso; verifica completa domani.
20:30 rootside-completo d283a02b APPROVATO. Domani: coda-verifiche (rootside-completo) e misure con split spento.
23:22 SUITE int2: 692 PASS, 12 FAIL, 4 BLOCKED (intel). REGRESSIONE: T-027, T-028, T-N-1 con CHROME su tutti i desktop (PASS in 1.0 e p1); Firefox ok. In analisi (sola lettura). Coda prosegue con ab-int2.
23:24 causa regressione T-027/028/N-1: TEST non aggiornato alle nuove difese login (8f56da22: righe di log e soglie 5/12/30); il prodotto conta e rifiuta bene. Firefox non eseguito in quel giro. Test in riscrittura con le soglie vere.
23:29 test F-027/F-028/N-1 riscritto (c2766ea1+8a7f5247) APPROVATO. DOMANI: rilanciare f027 su chrome+firefox (tutti i desktop) su integrazione2, poi coda-verifiche rootside-completo.
04:55 FINE coda-notte2. Esiti:
  - ab-int2 (vs 1.0): xfce chrome VERDE (la CPU +10-14% di p1 NON si ripete: era rumore), gnome firefox VERDE, gnome chrome ROSSO solo CPU a 4 utenti +9.5% e 6 utenti +14.8% (fps/ritardo ok, mem -7..-30%), xfce firefox ROSSO mem +6..+17% (1-4 utenti entro ripetibilita' 1.0, 8 utenti +10.9%); vs p1 xfce firefox VERDE (ereditato da p1). Confronto: /media/REMOTIX-15/tmp/ab-int2-confronto.txt. Da rimisurare gnome chrome (1 run solo).
  - f011-riga-kde-lxqt: log vuoto (solo tput): NON eseguito davvero, da capire e rilanciare.
  - fuzz-child-1.0: nessun crash in 300 s. fuzz-int2-quic/rcp/child: SALTATI, binari *-build-integr2 mancanti (serve build.sh).
  - pacing-ab-int2: RTT a riposo +5.8% (entro 15%); bulk/burst/loss NON MISURABILI: il server rifiuta l'ATTACH del client di prova («malformed layout», FAREWELL 0x0b) -> client di prova da allineare (sospetto port-scheda).
  - stream-churn: girato sui rami v10/base/audit, NON su int2 (v10/base crescono 1.17 MB/1000 stream, audit piatto): verificare se int2 ha la correzione e rilanciare su int2.
  - pam-tempi: girato solo su v10 (DISTINGUIBILE: utente negato 1.1 s contro 2.0-2.2 s dei rifiuti PAM): da rilanciare su int2.
  - b10-int2 e b10-int2-default: 0/3 giri 9/9 (6/9: KO c-48, «nati mai», riga del riepilogo 10 s): da analizzare (test o prodotto?).
  - migrazione-int2-dal-vivo: FAIL: REBIND ok (6 datagrammi sul nuovo percorso) ma nessun «MOVED to» nel log del server; contrasto lim 0 come atteso. Probabile riga di log cambiata: da verificare.
04:56 parte coda-verifiche-rs (verifica-rami su rootside-completo); analisi dei punti sopra in sola lettura.
04:54 analisi (sola lettura, agente): TUTTI difetti del TEST, non del prodotto:
  - f011-riga kde/lxqt: GIRATO davvero (log in /media/REMOTIX-15/log/f011-riga-prova.out, lo script fa exec > su quel file): 8/8 giri sana=PASS guasto=PASS; righe h-1/h-2 uguali ovunque tranne kde+firefox (colonne uguali 21%, un giro scarto 5 >3): da guardare la foto (probabile contenuto vero nell ultima riga, non riempimento).
  - pacing-ab: pacing-ab-cliente.py:311 manda ATTACH con layout vuoto (rcp.c:3611 vuole 1..64) -> rifiutato da SEMPRE, anche sul ramo prima: bulk/burst/loss mai misurati. Correggere con layout "it".
  - migrazione dal vivo: 01-b2-aioquic-client.py:198 manda b"rebind" grezzo -> server lo legge come RCP oltre 1 MiB e chiude prima della validazione del percorso -> niente MOVED. «REBIND OK» del client e un falso positivo. Correggere: PING invece di byte grezzi, e PASS solo se la connessione e ancora viva.
04:59 F-011 kde+firefox: FALSO ALLARME del controllo righe uguali: ultima riga = sfumatura vera dello sfondo Plasma (Firefox 2016 righe, senza riempimento, la cura (b) non scatta); nessun salto di croma. F-011 kde/lxqt VERDE. Migliorare il controllo per Firefox (salto rispetto alla pendenza). Client pacing (layout it) e migrazione (PING + CLIENT da integrazione2 a4b9cb1f, FAIL su farewell 0x0b) corretti, in revisione. b10 c-48: ipotesi difetto PRODOTTO IPv6 (risposta senza IPV6_PKTINFO, sorgente sbagliata), anche in 1.0: verifica + correzione su ramo pktinfo in corso.
05:01 VERIFICA rootside-completo d283a02b: 29 PASS, 1 FAIL (fuzz-quic-conn replay: abort nello stub ngtcp2_conn_write_connection_close_versioned da close_refused<-transport_expired): in analisi. Doc rollback net-move Arch 32eb4667 (rootside-completo; build manuale non provato: manca pygments sul server). Proposta packaging Arch: marker back-incomplete per non cancellare net/ dopo --back fallito. Coda giorno3 (f027 ristretta, A/B gnome chrome run2-3, churn int2, pam-tempi int2) pronta, in revisione.
05:09 PARERI 3 decisioni (domanda /media/REMOTIX-15/tmp/dom5.txt; risposte tmp/parere-argon.txt, tmp/pareri-locali.txt): D1 split: Argon B, gpt-oss B, laguna A. D2 worker Firefox: A per tutti. D3 PACE: Argon B (o C dopo prova 8 utenti), gpt-oss B, laguna A. lfm muto. ChatGPT da fare (Chrome non collegato). pktinfo 52c3b599+5601b8e3 APPROVATO (rilievi minori: errno dopo ripiego, ENODEV). Packaging Arch marker d09a6738 (rootside-completo) in revisione.
05:16 PIANO DI CHIUSURA: coda-giorno3 ridotta a sola rimisura A/B (gnome chrome run2, xfce firefox run2); suite f027, churn, pam-tempi, cpu-sessione, migrazione spostati sul ramo FINALE o in notte. Ramo finale = integrazione2 + pktinfo (8760f5bc, APPROVATO) + rootside-completo (harness ae8cae45, Arch 026f15d1 APPROVATO) + rifiniture (CSP self + b1dea604 fix decoder morto, mancava nella 1.5) + doc-chiusura. ff-worker (D2) separato: DA CORREGGERE (DIARY inesistente). coda-finale.txt pronta (verifica, suite completa, cerca-csp, b10, A/B 4/6/8). prova-fusione: 1 conflitto banale transport_open_fd.
05:21 ff-worker 852ae9ab (DIARY -> ?logbook) + 4c9c78ee + 8837386d + 470b2e86: APPROVATO (revisore; 22-page-load.js e simulazione 23/23 sul tablet). Prova dal vivo in coda-notte5 (suite-ffw). finale: fusioni 73df8f53 + documenti cbf53462 (revisione: 1 riga da togliere). rifiniture 7e49f5b1 APPROVATO. rootside ae8cae45 APPROVATO. Catena code avviata dal tablet (giorno3 poi finale).
05:31 ritardo-uniforme 0cc4a48f+42a560a1 APPROVATO (pavimento 2,5 s solo per 0x07; 0x08/0x0E a 1 s): da misurare con pam-tempi in coda-notte5, NON in finale. manuale fuso in finale (c7f71815). esiti-finale.sh scritto (in revisione). banco-bulk 31deb058 (--bulk-test-mb solo BENCH) in revisione. coda-giorno3 partita 05:27:59.
05:49 finale testa b0aabae3 (upgrading §8 + PACE doc corretto), finale-ff 9a8bf465. Pronti in coda-notte5: suite-ffw su finale-ff, d2 decoder lento/veloce (prova-d2-lento.sh, hook in suite-ramo), pam-tempi v10/fin/ru, b10 ritardo-uniforme, cpu-sessione, pacing-ab bulk bb-v10 vs bb-dopo, riferimento 1.0 v3 con box_work, fuzz, testo, radeon. ab-confronta: sezione memoria informativa (d1u, box_work). 30-perf memory.stat si applica da solo a fine giorno3. risvegli: candidato, non misurato stanotte.
06:24 AUDIT split (tmp/audit-split.md): nessun passaggio a root dal protocollo; contenimento parziale: R1 CLOSE_ORPHAN chiude desktop disconnessi subito, R2 ban per utente solo nel lato rete, R4 password in chiaro nel lato rete, R5 niente CLONE_NEWNET, R7 seccomp a denylist (famiglie socket). Conferma D1=B (spento in 1.5, prima R1/R2/R5/R6/R7 per la 1.6). Rami candidati post-1.5 (tmp/candidati-dopo-1.5.md): pagina-attivi e figli-sigchld APPROVATI (in coda verifica+cpu stanotte), audio-riprova PARCHEGGIATO, risvegli in attesa del contatore giri, scadenza-unica scartato. f031-finale pronto per Android domani.
06:31 RIMISURA gnome+chrome int2 run2 (coda-giorno3): con 2 run VERDE contro la 1.0 (32 misure, 0 fuori tolleranza; CPU +4.7% a 4 utenti e +4.9% a 6, entro 5%). Il ROSSO di ieri era rumore di un run singolo. In corso xfce+firefox run2. AUDIT rete/login (tmp/audit-rete-login.md): R1 MEDIA nuovo in 1.5: tabella contatori login (256) riempibile di voci bannate -> LV_FULL per tutti i login; correzione in sviluppo su ramo login-tabella. R3: nome utente grezzo nel log di why_no (anche 1.0) -> ramo log-nome.
06:39 capsule-parser 43fdc3f1 APPROVATO (parser capsule WT lineare invece di quadratico; DoS pre-login presente anche in 1.0). login-tabella 14b12ab4 (quota 160 ban, LV_FULL irraggiungibile) in revisione. Se entrambi approvati, fusione in finale PRIMA di coda-finale.
07:04 FINALE testa 3fc45b85: + capsule-parser (parser capsule lineare, DoS pre-login anche 1.0) + login-tabella (quota 160 ban, chiavi note G2 su disco con HMAC ed epoch reale, contatore comune per sconosciute a quota piena, proprietario sempre dentro; R1 audit). finale-ff ebebb443. coda-finale parte a fine giorno3. Da fare dal vivo: G2 dopo riavvio.

- 25 ott 07:51 UTC: coda-giorno3 FINE (gc run2 VERDE, xf run2 fatto); coda-finale partita 07:50:57; patch 30-perf box_work applicata. Approvati: log-tetti f5cbb61b, ricerche-hash 478aee9b, split-r5 test 8058437e.
- 25 ott 07:55 UTC: xf run2 confronto: tutto ok tranne mem a 8 utenti +6.0% (d1u +7.8%), come prima; da decidere con ref-1.0-v3 box_work in coda-notte5.
- 25 ott ~08:15 UTC DECISIONI UTENTE: tutta sicurezza+miglioramenti nella 1.5 (dopo solo funzioni nuove); D1 = split ACCESO nella 1.5; D2 = A (Firefox worker); D3 = B (PACE spento). Code fermate (verifica-finale FAIL fuzz-quic-conn). Piano: /media/REMOTIX-15/tmp/PIANO-1.5-completa.md. Obiettivo: chiudere mercoledì 28.
- 25 ott 08:45 UTC: v15c 6036ba8d (v15 546d7c16 + v15-split 5db4b65e + split-r8b). APERTO: SELinux non provabile (nessuna macchina; qemu assente) -> R8 serve mount proc in remotix_t; decidere con l utente se VM Alma o split spento su SELinux.
- 25 ott 09:12 UTC: prova split splc su v15-split 0e1e8896: F-001 xfce PASS; controlli A-D su xfce/gnome/kde/lxqt OK=56 KO=0 (2 processi, kill lato rete con desktop vivo, riaccesso, ritrovato, abbandono). Candidato v15c a5fe62d4; R8B pid0 corretto 96399147.
- 25 ott 09:28 UTC: v15c eca62a8d: verifica 61 PASS 1 FAIL (solo ricetta pidfd-identity), child-credentials root 12/12, live 4/4 GREEN. In corso prova box splv.
- 25 ott 09:43 UTC: prova box splv su v15c (con R8+pid fix): F-001 PASS, controlli split 4 desktop 116 OK 0 KO, 1.0 ripristinata.
- 25 ott ~10:20 UTC: SELinux su VM Alma 10 enforcing: RPM v15c db126ac4 installato, servizio split avviato, 0 AVC (avvio, /proc privato, riscoperta desktop, journald, pagina, arresto, kill lato root/rete). Non provati login completo e CLOSE_ORPHAN. Risultati /media/REMOTIX-15/tmp/selinux-risultati.md
- 25 ott 11:18 UTC: v15d ac3c231d (= v15c fast-forward): verifica 69/69 verde, prova box split 4 desktop 56 OK 0 KO, SELinux Alma 0 AVC. Lanciata ORA coda-notte6 (16 passi, ~12 h) su v15c=v15d. LLM spenti per le misure.
- 25 ott 14:10 UTC: suite v15cs: radeon 80/80 uguali o migliori; intel 708 test, 649 uguali, 5 migliorati, 2 regressioni T-028 gnome-chrome (ban: 6° tentativo non bannato; fault cerca 12 = soglia vecchia, ora 20), 64 «mancanti» = test PER_BROWSER=False girati con chrome invece che firefox (ordine --browser), 52 senza riferimento. DA ANALIZZARE f027/T-028 con split.
- 25 ott 15:17 UTC: A/B v15ca (split ACCESO, tutto dentro) contro 1.0, gradini 4,6,8: gnome:chrome VERDE, xfce:firefox VERDE; a 8 utenti mem -9.5% e -12.3% (meglio), fps/ritardo/CPU entro tolleranza. Il rosso mem 8 utenti di ieri sparito.
- 25 ott 20:20 CET: A/B v15ca contro il riferimento 1.0 v3, gnome:chrome con 3 run: VERDE (CPU a 4 utenti +1.8%; il +5.3% del run 1 era rumore). xfce:firefox VERDE. Verdetto A/B: VERDE su entrambe le combinazioni.
- 25 ott 21:00 CET: suite v15cf (firefox per i test PER_BROWSER=False, 4 desktop, split): 64 test, 64 uguali alla 1.0, 0 regressioni. I 64 MANCANTI di v15cs sono coperti. Insieme a v15cs (649 uguali, 5 migliorati) e alle 2 regressioni f027 chiuse (6/6 PASS): suite contro la 1.0 VERDE.
