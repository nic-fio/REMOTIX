package motore

import (
	"errors"
	"fmt"
)

// Gravita e Natura di un messaggio (§6.6.9).
type Gravita string
type Natura string

const (
	INFO      Gravita = "INFO"
	AVVISO    Gravita = "AVVISO"
	BLOCCANTE Gravita = "BLOCCANTE"

	ServeAzione       Natura = "SERVE_AZIONE"
	Riprovabile       Natura = "RIPROVABILE"
	Recuperabile      Natura = "RECUPERABILE"
	ServeAnnullamento Natura = "SERVE_ANNULLAMENTO"
	Fatale            Natura = "FATALE"
)

// Codice è una voce del catalogo dei codici: stabile, mai riusata per un altro significato.
type Codice struct {
	Gravita Gravita `json:"gravita"`
	Natura  Natura  `json:"natura"`
	Testo   string  `json:"testo"`
	Rimedio string  `json:"rimedio,omitempty"`
}

// Messaggio è un codice nel suo contesto: quel che la CLI stampa, il registro annota, il
// certificato conserva, e ogni futura interfaccia mostra (§6.6.9).
type Messaggio struct {
	Codice    string  `json:"codice"`
	Gravita   Gravita `json:"gravita"`
	Natura    Natura  `json:"natura"`
	Testo     string  `json:"testo"`
	Rimedio   string  `json:"rimedio,omitempty"`
	Dettaglio string  `json:"dettaglio,omitempty"`
}

// Codici: ⛔ un codice non si cambia di significato e non si riusa. Se un testo va corretto si
// corregge il testo; se il significato cambia, si prende un numero nuovo.
var Codici = map[string]Codice{
	// fase 0 — TRUST (§6.6.10)
	// ⛔ 001 e 005 sono RITIRATI con T8, 002 e 006…016 con D11 semplificata (una chiave sola, quella
	// dell'archivio, verificata dal gestore di pacchetti: DECISIONI §10.21); i codici non si riusano.
	// (Per 001 e 005: la firma c'era e si verificava sempre, --senza-firma non esiste
	//    più): restano qui perché i registri vecchi li nominano, e non si riusano.
	"RX-TRUST-001": {AVVISO, ServeAzione, "(ritirato in T8) La firma del catalogo non si poteva ancora verificare: si procedeva solo con --senza-firma.", ""},
	"RX-TRUST-002": {INFO, ServeAzione, "(ritirato: D11 semplificata, DECISIONI §10.21) Il catalogo era scaduto.", ""},
	"RX-TRUST-003": {BLOCCANTE, ServeAzione, "Il catalogo chiede un motore più nuovo di questo.", "Aggiornare il sistema (il pacchetto remotix-install), o scaricare di nuovo install.sh."},
	"RX-TRUST-004": {BLOCCANTE, Fatale, "Il catalogo non si legge o ha un formato sconosciuto.", "Reinstallare remotix-install dall'archivio di REMOTIX, o scaricare di nuovo install.sh; un catalogo dato a mano va corretto."},
	"RX-TRUST-005": {BLOCCANTE, ServeAzione, "(ritirato in T8) La fiducia nel catalogo non era verificata e non era stato chiesto di procedere lo stesso.", ""},
	"RX-TRUST-006": {INFO, ServeAzione, "(ritirato: D11 semplificata, DECISIONI §10.21) Il catalogo (o il motore) non aveva la sua firma della catena A.", ""},
	"RX-TRUST-007": {INFO, ServeAzione, "(ritirato: D11 semplificata, DECISIONI §10.21) La firma della catena A non corrispondeva.", ""},
	"RX-TRUST-008": {INFO, ServeAzione, "(ritirato: D11 semplificata, DECISIONI §10.21) La sottochiave non era certificata dalla chiave madre della catena A.", ""},
	"RX-TRUST-009": {INFO, ServeAzione, "(ritirato: D11 semplificata, DECISIONI §10.21) La sottochiave della catena A era scaduta.", ""},
	"RX-TRUST-010": {INFO, ServeAzione, "(ritirato: D11 semplificata, DECISIONI §10.21) La sottochiave della catena A era revocata.", ""},
	"RX-TRUST-011": {INFO, ServeAzione, "(ritirato: D11 semplificata, DECISIONI §10.21) Il catalogo dell'archivio era più vecchio di quello memorizzato.", ""},
	"RX-TRUST-012": {INFO, ServeAzione, "(ritirato: D11 semplificata, DECISIONI §10.21) L'elenco delle revoche non si verificava.", ""},
	"RX-TRUST-013": {INFO, ServeAzione, "(ritirato: D11 semplificata, DECISIONI §10.21) Il catalogo non si scaricava dall'archivio.", ""},
	"RX-TRUST-014": {INFO, ServeAzione, "(ritirato: D11 semplificata, DECISIONI §10.21) Il motore non corrispondeva alla sua firma della catena A.", ""},
	"RX-TRUST-015": {INFO, ServeAzione, "(ritirato: D11 semplificata, DECISIONI §10.21) Il motore non aveva accanto la sua firma della catena A.", ""},
	"RX-TRUST-016": {INFO, ServeAzione, "(ritirato: D11 semplificata, DECISIONI §10.21) Il catalogo fuori linea era più vecchio di quello memorizzato.", ""},
	"RX-TRUST-017": {BLOCCANTE, ServeAzione, "Il motore scaricato non è quello pubblicato: il suo sha256 non è quello scritto in install.sh o pubblicato accanto a lui.", "Non usare questo motore: scaricare di nuovo install.sh dal sito di REMOTIX, controllarne lo sha256 con quello pubblicato (HTTPS), e rilanciarlo."},

	// fase 1 — PREFLIGHT
	"RX-DISTRO-001":  {BLOCCANTE, ServeAzione, "Non si riesce a capire quale distribuzione è installata (/etc/os-release manca o non si legge).", ""},
	"RX-SYSTEMD-001": {BLOCCANTE, ServeAzione, "La macchina non è partita con systemd: REMOTIX usa logind e il gestore d'utente di systemd.", "REMOTIX non gira senza systemd (§3)."},
	// ⛔ 001 RITIRATO con la fase 19 (DECISIONI §10.27: niente codifica sul processore): senza scheda
	// non c'è più un ripiego, c'è il rifiuto (003). I codici non si riusano.
	"RX-GPU-001": {INFO, ServeAzione, "(ritirato: fase 19, DECISIONI §10.27) Non c'era nessuna scheda con un nodo di disegno: la codifica era in software.", ""},
	"RX-GPU-002": {AVVISO, ServeAzione, "La scheda NVIDIA usa il driver proprietario: non codifica H.264 attraverso VA-API; il video passa da Vulkan Video, se il suo driver Vulkan (ICD nvidia) c'è.", "Senza l'ICD Vulkan, il video lo codifica un'altra scheda della macchina, se ne ha una capace (condizione C-HARDWARE); altrimenti REMOTIX non si installa (RX-GPU-004)."},
	// fase 19: il controllo della scheda (strade.go, VerdettoScheda) — BLOCCANTI, prima di toccare
	"RX-GPU-003":     {BLOCCANTE, ServeAzione, "Nessuna scheda (nessun nodo di disegno /dev/dri/renderD*): REMOTIX richiede l'accelerazione hardware della codifica video, e su questa macchina non si installa.", "Installarlo su una macchina con una scheda Intel o AMD; in una macchina virtuale, passarle una scheda (passthrough o vGPU). Se la macchina ha una scheda, controllare che il suo driver sia caricato."},
	"RX-GPU-004":     {BLOCCANTE, ServeAzione, "NVIDIA col driver proprietario ma senza il suo driver Vulkan (nessun ICD nvidia): su questa scheda REMOTIX codifica solo con Vulkan Video, e senza il driver non si installa.", "Installare il driver NVIDIA completo (con l'ICD Vulkan, /usr/share/vulkan/icd.d/nvidia_icd.json), oppure una scheda Intel o AMD accanto alla NVIDIA: REMOTIX usa quella per il video."},
	"RX-GPU-005":     {BLOCCANTE, ServeAzione, "Nessuna scheda di questa macchina sa codificare il video H.264 per REMOTIX (Vulkan Video: AMD e NVIDIA; VA-API: Intel e AMD): REMOTIX non si installa.", "Installarlo su una macchina con una scheda Intel, AMD o NVIDIA; in una macchina virtuale, passarle la scheda vera (passthrough o vGPU)."},
	"RX-GPU-006":     {BLOCCANTE, ServeAzione, "La scheda c'è, ma su questa distribuzione il suo driver VA-API non codifica H.264, non c'è un driver da aggiungere che lo faccia, e in Vulkan Video non c'è (AMD senza il driver RADV; Intel non codifica in Vulkan di serie): REMOTIX non si installa.", "Le combinazioni che codificano sono nel rapporto di compatibilità (es. AlmaLinux/RHEL: Intel col driver di RPM Fusion; AMD col driver Vulkan RADV, mesa-vulkan-drivers)."},
	"RX-H264-001":    {AVVISO, ServeAzione, "Non si sa ancora se la scheda codifica H.264: il controllo non lancia programmi, e la prova col fotogramma si fa dopo l'installazione (7a), col binario di REMOTIX.", "Il controllo resta SCONOSCIUTO fino ad allora: non vale come «a posto»."},
	"RX-H264-002":    {AVVISO, ServeAzione, "La scheda non ha codificato il fotogramma H.264 di prova.", "Controllare il driver VA-API della scheda."},
	"RX-H264-003":    {AVVISO, ServeAzione, "La scheda non codifica H.264: su Fedora e sulla famiglia RHEL il driver con H.264 viene da RPM Fusion (Intel: intel-media-driver; AMD, solo Fedora: mesa-va-drivers-freeworld).", "Il comando è nel rapporto di compatibilità (condizione C-DEPOSITO, decisione D5)."},
	"RX-H264-004":    {AVVISO, ServeAzione, "La scheda non codifica H.264: su openSUSE con una scheda AMD serve la Mesa di Packman (il driver Intel ufficiale codifica già).", "Il comando è nel rapporto di compatibilità (condizione C-DEPOSITO, decisione D5)."},
	"RX-H264-005":    {INFO, ServeAzione, "(ritirato: fase 19, DECISIONI §10.27) Mancava il ripiego software (OpenH264).", ""},
	"RX-H264-006":    {BLOCCANTE, ServeAzione, "Senza l'archivio esterno per la codifica video REMOTIX non si installa (decisione D5, DECISIONI §10.20): niente è stato toccato.", "Rifare l'installazione dando il consenso all'archivio (consenso.deposito.<nome> = si)."},
	"RX-PAM-001":     {BLOCCANTE, ServeAzione, "La pila d'accesso della distribuzione non si trova.", "Controllare i file in /etc/pam.d (o /usr/lib/pam.d su openSUSE)."},
	"RX-PAM-002":     {AVVISO, ServeAzione, "La pila d'accesso della distribuzione contiene pam_faillock: tre parole sbagliate chiudono il conto, anche davanti alla macchina — per REMOTIX come per ssh.", "Decisione D3: REMOTIX segue il sistema. Si governa in /etc/security/faillock.conf; faillock --user NOME --reset sblocca."},
	"RX-PAM-003":     {INFO, ServeAzione, "Esiste già un file d'accesso «remotix».", ""},
	"RX-PAM-004":     {AVVISO, ServeAzione, "Il modulo pam_systemd non si trova: senza, il desktop non nasce.", ""},
	"RX-SELINUX-001": {INFO, ServeAzione, "SELinux è attivo e fa rispettare le regole (enforcing).", "Il comportamento di REMOTIX sotto SELinux è la tappa T6."},
	"RX-FW-001":      {AVVISO, ServeAzione, "Il firewall è acceso e la porta di REMOTIX non vi risulta aperta.", "Aprirla (decisione D6: il motore sa farlo, col consenso)."},
	"RX-FW-002":      {AVVISO, ServeAzione, "Lo stato del firewall per la porta di REMOTIX non si è potuto leggere.", "Serve essere root per leggere le regole di ufw e nftables."},
	"RX-FW-003":      {AVVISO, ServeAzione, "La porta di REMOTIX è già occupata da un altro programma.", "Scegliere un'altra porta o fermare quel programma."},
	"RX-FW-004":      {BLOCCANTE, ServeAzione, "Questo motore sa aprire la porta con firewalld e ufw: nftables non è ancora fatto.", "Aprire la porta a mano, col comando indicato."},
	"RX-FW-005":      {INFO, ServeAzione, "Da questa macchina non si può sapere se la porta è raggiungibile dalla rete (router, firewall esterni).", ""},
	"RX-LOGIND-001":  {AVVISO, ServeAzione, "logind chiude i processi di chi esce (KillUserProcesses=yes): un desktop di REMOTIX potrebbe morire.", "Effetto da misurare (§5.2); per ora si dichiara."},
	"RX-LOGIND-002":  {INFO, ServeAzione, "Il valore di KillUserProcesses non si è potuto leggere da logind.", ""},
	"RX-GRUPPI-001":  {AVVISO, ServeAzione, "Il gruppo «render» non esiste su questa macchina.", ""},
	"RX-GRUPPI-002":  {BLOCCANTE, ServeAzione, "Il gruppo richiesto non esiste.", ""},
	"RX-GRUPPI-003":  {BLOCCANTE, ServeAzione, "L'utente richiesto non esiste.", ""},
	"RX-OPENSSL-001": {BLOCCANTE, ServeAzione, "OpenSSL è più vecchia della 3.5: manca QUIC.", ""},
	"RX-OPENSSL-002": {AVVISO, ServeAzione, "La versione di OpenSSL non si è potuta leggere.", ""},
	"RX-DESKTOP-001": {BLOCCANTE, ServeAzione, "Su questa macchina non c'è un desktop supportato da REMOTIX, e non se ne è scelto uno da installare: REMOTIX non si installa.", "Rispondere sì alla domanda sul desktop (remotix-install approva --desktop gnome|kde|xfce|lxqt), o installarne uno."},
	"RX-DESKTOP-002": {AVVISO, ServeAzione, "Nessun desktop supportato è installato: prima di installare si chiederà quale aggiungere (condizione C-DESKTOP).", ""},

	// fase 2 — COMPATIBILITY (§6.6.8)
	"RX-COMPAT-001": {BLOCCANTE, ServeAzione, "Questa distribuzione è fuori da REMOTIX.", ""},
	"RX-COMPAT-002": {BLOCCANTE, ServeAzione, "Questa distribuzione non è nel catalogo: non si sa se REMOTIX ci gira.", ""},
	"RX-COMPAT-003": {BLOCCANTE, ServeAzione, "Le distribuzioni immutabili sono rimandate a dopo la fase 17 (decisione D9).", ""},
	"RX-COMPAT-004": {BLOCCANTE, ServeAzione, "Questa combinazione aspetta una decisione dell'utente.", ""},
	"RX-COMPAT-005": {BLOCCANTE, ServeAzione, "Questo desktop non è supportato su questa distribuzione.", ""},
	"RX-COMPAT-006": {BLOCCANTE, ServeAzione, "La versione del desktop è più vecchia della minima.", ""},
	"RX-COMPAT-007": {BLOCCANTE, ServeAzione, "La macchina non ha un requisito indispensabile.", ""},

	// fasi 3-4 — PLANNING, CONSENT
	"RX-PIANO-001": {BLOCCANTE, ServeAzione, "La macchina è cambiata dopo che il piano è stato fatto: il piano non vale più.", "Rifare il piano su questa macchina (remotix-install piano)."},
	"RX-PIANO-002": {BLOCCANTE, Fatale, "Il piano non si legge o ha un formato sconosciuto.", ""},
	"RX-PIANO-003": {BLOCCANTE, ServeAzione, "Il piano non è stato approvato: niente viene toccato.", "Approvarlo con remotix-install approva, o con --approva."},
	"RX-PIANO-004": {BLOCCANTE, Fatale, "Il piano contiene un'azione che questo motore non conosce.", ""},
	"RX-PIANO-005": {BLOCCANTE, ServeAzione, "L'approvazione non corrisponde a questo piano (il piano è stato cambiato dopo).", "Approvare di nuovo il piano."},

	// senza domande e senza rete (§6.6.12, T9)
	"RX-RISPOSTE-001": {BLOCCANTE, ServeAzione, "Il file di risposte non dà un consenso che su questa macchina serve: senza domande non vuol dire senza consenso, e un consenso che manca non vale «sì». Niente è stato toccato.", "Aggiungere al file di risposte la voce indicata, con «si» o «no» (le voci: remotix-install aiuto)."},
	"RX-RISPOSTE-002": {BLOCCANTE, Fatale, "Il file di risposte non si legge, ha un formato sconosciuto o contiene una voce sconosciuta.", "Correggere il file: la prima voce è «formato = remotix-risposte/1»; le voci ammesse sono in remotix-install aiuto."},
	"RX-RISPOSTE-003": {BLOCCANTE, ServeAzione, "Una risposta del file ha un valore non ammesso su questa macchina.", "Correggere il valore indicato."},
	"RX-FUORI-001":    {BLOCCANTE, ServeAzione, "Il pacchetto fuori linea non è integro: un file manca o non è quello preparato.", "Prepararlo di nuovo (remotix-install prepara-fuori-linea) e ricopiarlo per intero."},
	"RX-FUORI-002":    {BLOCCANTE, ServeAzione, "Il pacchetto fuori linea è stato preparato per un'altra macchina (impronta o pacchetti installati diversi).", "Prepararlo su una macchina collegata uguale a questa (stessa distribuzione e stessi pacchetti)."},
	"RX-FUORI-003":    {BLOCCANTE, ServeAzione, "Nel pacchetto fuori linea manca qualcosa che l'installazione chiede.", "Prepararlo di nuovo sulla macchina di riferimento, con le stesse risposte."},
	"RX-FUORI-004":    {BLOCCANTE, ServeAzione, "L'installazione senza rete non è ancora fatta per questa famiglia di distribuzioni (zypper, pacman).", "Installare dalla rete."},
	"RX-FUORI-005":    {BLOCCANTE, ServeAzione, "Un archivio di terzi (Packman, EPEL) non entra nel pacchetto fuori linea: il suo passo scarica dalla rete.", "Installare dalla rete: senza quell'archivio REMOTIX non si installa (D5, la codifica sulla scheda)."},

	// operazione, registro e ripresa (§6.6.2, §6.6.3)
	"RX-STATO-001":     {BLOCCANTE, Recuperabile, "C'è un'operazione non finita: va prima ripresa o annullata.", "remotix-install riprendi, oppure remotix-install annulla."},
	"RX-STATO-002":     {BLOCCANTE, Fatale, "Transizione di stato non valida: è un difetto del motore.", ""},
	"RX-STATO-003":     {BLOCCANTE, Riprovabile, "Un altro motore sta lavorando in questo momento.", "Aspettare che finisca."},
	"RX-STATO-004":     {BLOCCANTE, ServeAzione, "Non c'è nessuna operazione da riprendere o annullare.", ""},
	"RX-STATO-005":     {BLOCCANTE, ServeAzione, "L'operazione è in uno stato finale: non si riprende e non si annulla (per togliere REMOTIX si disinstalla).", ""},
	"RX-RIPRESA-001":   {BLOCCANTE, ServeAzione, "La macchina è cambiata durante l'operazione: un passo già fatto non c'è più o è stato cambiato da altri.", "Guardare il registro; poi riprendere o annullare."},
	"RX-RIPRESA-002":   {BLOCCANTE, ServeAzione, "L'operazione si era fermata prima di toccare la macchina: non c'è niente da riprendere.", "Rilanciare remotix-install applica col piano."},
	"RX-RIPRESA-003":   {INFO, Recuperabile, "Il registro finiva con una riga scritta a metà (interruzione): la riga è stata tolta.", ""},
	"RX-AZIONE-001":    {BLOCCANTE, ServeAnnullamento, "Un passo dell'installazione non è riuscito: l'operazione si annulla.", ""},
	"RX-AZIONE-002":    {BLOCCANTE, ServeAzione, "Un passo non si è potuto annullare: la macchina non è tornata del tutto com'era.", "L'elenco esatto di quel che resta è nel certificato."},
	"RX-AZIONE-003":    {BLOCCANTE, ServeAnnullamento, "La verifica di un passo non passa: l'operazione si annulla.", ""},
	"RX-AZIONE-004":    {BLOCCANTE, ServeAzione, "Il piano contiene un passo che questo motore conosce ma non sa ancora eseguire: ci si ferma prima di toccare la macchina.", "Il passo arriva con le fasi 5-8 del motore (T5)."},
	"RX-INST-001":      {INFO, ServeAzione, "Installazione non certificata dall'installatore (nessuna operazione CONFERMATA di remotix-install): lo si dice, a solo scopo informativo.", ""},
	"RX-INST-002":      {AVVISO, ServeAzione, "Dopo l'aggiornamento il controllo della macchina ha trovato problemi.", "remotix-install verifica"},
	"RX-AZIONE-005":    {BLOCCANTE, ServeAzione, "Un passo IRREVERSIBILE non si annulla.", ""},
	"RX-PACCHETTI-001": {BLOCCANTE, ServeAzione, "Il pacchetto non è quello del piano (sha256 diverso).", "Rifare il piano col pacchetto giusto."},
	"RX-PACCHETTI-002": {BLOCCANTE, ServeAzione, "Togliere i pacchetti di REMOTIX toglierebbe anche un pacchetto d'altri: non si tocca.", "Guardare chi dipende da quel pacchetto."},
	"RX-PACCHETTI-003": {BLOCCANTE, ServeAzione, "Il gestore di pacchetti di questa famiglia non è conosciuto dal motore.", ""},
	"RX-PACCHETTI-004": {BLOCCANTE, ServeAzione, "Il gestore di pacchetti è a metà di una transazione di prima.", "Sistemarlo col suo rimedio (dpkg --configure -a, dnf, zypper verify) e riprovare."},
	"RX-PACCHETTI-006": {INFO, ServeAzione, "Dei pacchetti portati da REMOTIX alcuni restano: li chiede qualcosa che resta (un pacchetto aggiornato dallo stesso archivio, o un programma installato dopo). Toglierli si porterebbe via anche lui.", "Se non servono più, toglierli a mano insieme a chi li chiede, col gestore di pacchetti."},
	"RX-PACCHETTI-005": {BLOCCANTE, Riprovabile, "La transazione non si è potuta risolvere o scaricare: niente è stato installato.", "Controllare la rete e i depositi, poi riprendere."},
	"RX-CINTURA-001":   {BLOCCANTE, ServeAzione, "Il file spento della cintura non c'è (il pacchetto non l'ha portato).", ""},
	"RX-SYSTEMD-002":   {BLOCCANTE, ServeAzione, "L'unità è mascherata: l'amministratore l'ha spenta apposta.", ""},
	"RX-SYSTEMD-003":   {BLOCCANTE, ServeAzione, "L'unità non esiste.", ""},
	"RX-FILE-001":      {BLOCCANTE, ServeAzione, "Il file è stato cambiato da qualcun altro durante l'operazione: non si tocca.", ""},
	"RX-AZIONE-006":    {BLOCCANTE, ServeAnnullamento, "L'installazione è stata fermata da chi installa: quel che era già fatto si annulla.", ""},

	// le interfacce (T9, DECISIONI §10.14, §10.19): TUI e GUI
	"RX-UI-001": {BLOCCANTE, ServeAzione, "Questa costruzione di remotix-install non ha la finestra (è quella statica, per le macchine senza desktop).", "remotix-install tui (nel terminale), oppure install.sh --finestra, che scarica la costruzione con la finestra."},
	"RX-UI-002": {BLOCCANTE, ServeAzione, "La finestra non si apre: non c'è una sessione grafica (né WAYLAND_DISPLAY né DISPLAY), o le sue librerie non rispondono.", "remotix-install tui, nel terminale."},
	"RX-UI-003": {BLOCCANTE, ServeAzione, "La finestra non gira da amministratore (root): chiede lei i permessi, a polkit, quando servono.", "Lanciarla come utente normale, senza sudo."},
	"RX-UI-004": {BLOCCANTE, ServeAzione, "I permessi da amministratore non sono stati dati (polkit ha rifiutato o la richiesta è stata chiusa): niente è stato toccato.", "Rilanciare e inserire la password di un amministratore."},
	"RX-UI-005": {BLOCCANTE, ServeAzione, "La parte da amministratore del motore si è interrotta.", "remotix-install stato dice a che punto è l'operazione; remotix-install riprendi o annulla."},
	"RX-UI-006": {BLOCCANTE, ServeAzione, "La TUI chiede un terminale e i permessi da amministratore.", "sudo remotix-install tui"},

	// l'aggiornamento automatico (DECISIONI §10.10, T8)
	"RX-AGG-001": {INFO, ServeAzione, "(ritirato: D14, DECISIONI §10.23) REMOTIX era all'ultima versione del canale.", ""},
	"RX-AGG-002": {INFO, ServeAzione, "(ritirato: D14, DECISIONI §10.23) C'era un aggiornamento di manutenzione.", ""},
	"RX-AGG-003": {INFO, ServeAzione, "(ritirato: D14, DECISIONI §10.23) C'era la versione annuale nuova.", ""},
	"RX-AGG-004": {INFO, ServeAzione, "(ritirato: D14, DECISIONI §10.23) C'era un aggiornamento, solo avvisato.", ""},
	"RX-AGG-005": {INFO, ServeAzione, "(ritirato: D14, DECISIONI §10.23) Gli aggiornamenti automatici erano spenti.", ""},
	"RX-AGG-006": {INFO, ServeAzione, "(ritirato: D14, DECISIONI §10.23) REMOTIX non era installato dall'installatore: niente da aggiornare.", ""},
	"RX-AGG-007": {INFO, ServeAzione, "(ritirato: D14, DECISIONI §10.23) L'archivio non rispondeva durante l'aggiornamento.", ""},
	"RX-AGG-008": {INFO, ServeAzione, "(ritirato: D14, DECISIONI §10.23) Su Arch l'aggiornamento sarebbe stato parziale.", ""},
	"RX-AGG-009": {INFO, ServeAzione, "(ritirato: D14, DECISIONI §10.23) La versione chiesta non era nell'archivio.", ""},
	"RX-AGG-010": {INFO, ServeAzione, "(ritirato: D14, DECISIONI §10.23) La configurazione degli aggiornamenti non si leggeva.", ""},
	"RX-AGG-011": {INFO, ServeAzione, "(ritirato: D14, DECISIONI §10.23) L'aggiornamento automatico era sospeso dopo un ritorno indietro.", ""},
}

// Msg costruisce un messaggio da un codice. Un codice sconosciuto è un difetto del motore, e la
// prova TestCodiciUsatiEsistono lo trova prima che arrivi a qualcuno.
func Msg(codice, dettaglio string) Messaggio {
	c, ok := Codici[codice]
	if !ok {
		panic("codice sconosciuto: " + codice)
	}
	testo, rimedio := c.Testo, c.Rimedio
	if linguaAttuale == EN {
		if e, ok := codiciInglese[codice]; ok {
			testo, rimedio = e[0], e[1]
		}
	}
	return Messaggio{Codice: codice, Gravita: c.Gravita, Natura: c.Natura, Testo: testo, Rimedio: rimedio, Dettaglio: dettaglio}
}

// ErroreRX è un errore che porta il suo codice stabile.
type ErroreRX struct{ M Messaggio }

func (e *ErroreRX) Error() string {
	if e.M.Dettaglio != "" {
		return fmt.Sprintf("%s: %s (%s)", e.M.Codice, e.M.Testo, e.M.Dettaglio)
	}
	return e.M.Codice + ": " + e.M.Testo
}

// Errore costruisce un errore con codice.
func Errore(codice, dettaglio string) error { return &ErroreRX{Msg(codice, dettaglio)} }

// CodiceDi estrae il codice da un errore, o "" se l'errore non ne ha.
func CodiceDi(err error) string {
	var e *ErroreRX
	if errors.As(err, &e) {
		return e.M.Codice
	}
	return ""
}
