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
	// ⛔ 001 e 005 sono RITIRATI con T8 (la firma c'è e si verifica sempre, --senza-firma non esiste
	//    più): restano qui perché i registri vecchi li nominano, e non si riusano.
	"RX-TRUST-001": {AVVISO, ServeAzione, "(ritirato in T8) La firma del catalogo non si poteva ancora verificare: si procedeva solo con --senza-firma.", ""},
	"RX-TRUST-002": {BLOCCANTE, ServeAzione, "Il catalogo delle combinazioni supportate è scaduto.", "Scaricare il motore o il catalogo aggiornati."},
	"RX-TRUST-003": {BLOCCANTE, ServeAzione, "Il catalogo chiede un motore più nuovo di questo.", "Scaricare il motore aggiornato."},
	"RX-TRUST-004": {BLOCCANTE, Fatale, "Il catalogo non si legge o ha un formato sconosciuto.", "Scaricare di nuovo il motore o il catalogo."},
	"RX-TRUST-005": {BLOCCANTE, ServeAzione, "(ritirato in T8) La fiducia nel catalogo non era verificata e non era stato chiesto di procedere lo stesso.", ""},
	"RX-TRUST-006": {BLOCCANTE, ServeAzione, "Il catalogo (o il motore) non ha la sua firma, o la firma non si legge: senza firma non si procede.", "Scaricare di nuovo il catalogo con il suo file .firma accanto, o dare un catalogo fuori linea firmato (--catalogo FILE, con FILE.firma)."},
	"RX-TRUST-007": {BLOCCANTE, ServeAzione, "La firma non corrisponde: il catalogo (o il motore) è stato alterato, o la firma è di un'altra cosa.", "Non usare questo file: scaricarlo di nuovo da REMOTIX e controllare da dove arriva."},
	"RX-TRUST-008": {BLOCCANTE, ServeAzione, "La chiave che ha firmato non è certificata dalla chiave madre di REMOTIX scritta nel motore.", "Non usare questo file: non viene da REMOTIX, o il motore è troppo vecchio per la chiave nuova."},
	"RX-TRUST-009": {BLOCCANTE, ServeAzione, "La chiave che ha firmato è scaduta (o non è ancora valida).", "Scaricare il catalogo aggiornato, firmato con la chiave in corso; controllare anche l'orologio della macchina."},
	"RX-TRUST-010": {BLOCCANTE, ServeAzione, "La chiave che ha firmato è stata REVOCATA da REMOTIX.", "Scaricare il catalogo firmato con la chiave nuova; non usare niente firmato con quella revocata."},
	"RX-TRUST-011": {AVVISO, ServeAzione, "Il catalogo ricevuto è più vecchio di uno già verificato su questa macchina: si tiene il più recente.", "Se è stato dato a mano, darne uno più recente; se viene dall'archivio, lo specchio può essere indietro."},
	"RX-TRUST-012": {BLOCCANTE, ServeAzione, "L'elenco delle chiavi revocate non è firmato dalla chiave madre, o è alterato.", "Non si procede finché l'elenco non si verifica: scaricarlo di nuovo da REMOTIX."},
	"RX-TRUST-013": {AVVISO, Riprovabile, "Il catalogo aggiornato non si è potuto scaricare dall'archivio: si usa il più recente già verificato.", "Controllare la rete; il controllo si ripete al prossimo giro."},
	"RX-TRUST-014": {BLOCCANTE, ServeAzione, "Il motore che gira non corrisponde alla sua firma.", "Non usare questo motore: reinstallarlo dall'archivio di REMOTIX."},
	"RX-TRUST-015": {INFO, ServeAzione, "Il motore non ha accanto la sua firma: la sua autenticità l'ha verificata chi l'ha scaricato (lo script d'ingresso) o il gestore di pacchetti (catena B).", ""},
	"RX-TRUST-016": {BLOCCANTE, ServeAzione, "Il catalogo dato fuori linea è più vecchio di uno già verificato su questa macchina.", "Dare il catalogo più recente."},

	// fase 1 — PREFLIGHT
	"RX-DISTRO-001":  {BLOCCANTE, ServeAzione, "Non si riesce a capire quale distribuzione è installata (/etc/os-release manca o non si legge).", ""},
	"RX-SYSTEMD-001": {BLOCCANTE, ServeAzione, "La macchina non è partita con systemd: REMOTIX usa logind e il gestore d'utente di systemd.", "REMOTIX non gira senza systemd (§3)."},
	"RX-GPU-001":     {AVVISO, ServeAzione, "Non c'è nessuna scheda con un nodo di disegno (/dev/dri/renderD*): la codifica sarà in software.", "Se la macchina ha una scheda, controllare che il suo driver sia caricato."},
	"RX-GPU-002":     {AVVISO, ServeAzione, "La scheda NVIDIA usa il driver proprietario: non codifica H.264 attraverso VA-API.", "La codifica passerà al ripiego software (condizione C-HARDWARE)."},
	"RX-H264-001":    {AVVISO, ServeAzione, "Non si sa ancora se la scheda codifica H.264: il controllo non lancia programmi, e la prova col fotogramma si fa dopo l'installazione (7a), col binario di REMOTIX.", "Il controllo resta SCONOSCIUTO fino ad allora: non vale come «a posto»."},
	"RX-H264-002":    {AVVISO, ServeAzione, "La scheda non ha codificato il fotogramma H.264 di prova.", "Controllare il driver VA-API della scheda."},
	"RX-H264-003":    {AVVISO, ServeAzione, "La scheda non codifica H.264: su Fedora e sulla famiglia RHEL serve RPM Fusion.", "Il comando è nel rapporto di compatibilità (condizione C-DEPOSITO, decisione D5)."},
	"RX-H264-004":    {AVVISO, ServeAzione, "La scheda non codifica H.264: su openSUSE serve Packman.", "Il comando è nel rapporto di compatibilità (condizione C-DEPOSITO, decisione D5)."},
	"RX-H264-005":    {AVVISO, ServeAzione, "Non c'è nemmeno il ripiego software (libx264) nella ffmpeg di questa macchina.", ""},
	"RX-PAM-001":     {BLOCCANTE, ServeAzione, "La pila d'accesso della distribuzione non si trova.", "Controllare i file in /etc/pam.d (o /usr/lib/pam.d su openSUSE)."},
	"RX-PAM-002":     {AVVISO, ServeAzione, "La pila d'accesso della distribuzione contiene pam_faillock: tre parole sbagliate chiudono il conto, anche davanti alla macchina.", "Decisione D3, aperta."},
	"RX-PAM-003":     {INFO, ServeAzione, "Esiste già un file d'accesso «remotix».", ""},
	"RX-PAM-004":     {AVVISO, ServeAzione, "Il modulo pam_systemd non si trova: senza, il desktop non nasce.", ""},
	"RX-SELINUX-001": {INFO, ServeAzione, "SELinux è attivo e fa rispettare le regole (enforcing).", "Il comportamento di REMOTIX sotto SELinux è la tappa T6."},
	"RX-FW-001":      {AVVISO, ServeAzione, "Il firewall è acceso e la porta di REMOTIX non vi risulta aperta.", "Aprirla (decisione D6: il motore sa farlo, col consenso)."},
	"RX-FW-002":      {AVVISO, ServeAzione, "Lo stato del firewall per la porta di REMOTIX non si è potuto leggere.", "Serve essere root per leggere le regole di ufw e nftables."},
	"RX-FW-003":      {AVVISO, ServeAzione, "La porta di REMOTIX è già occupata da un altro programma.", "Scegliere un'altra porta o fermare quel programma."},
	"RX-FW-004":      {BLOCCANTE, ServeAzione, "Questo motore sa aprire la porta solo con firewalld: ufw e nftables non sono ancora fatti.", "Aprire la porta a mano, col comando indicato."},
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
	"RX-PACCHETTI-005": {BLOCCANTE, Riprovabile, "La transazione non si è potuta risolvere o scaricare: niente è stato installato.", "Controllare la rete e i depositi, poi riprendere."},
	"RX-CINTURA-001":   {BLOCCANTE, ServeAzione, "Il file spento della cintura non c'è (il pacchetto non l'ha portato).", ""},
	"RX-SYSTEMD-002":   {BLOCCANTE, ServeAzione, "L'unità è mascherata: l'amministratore l'ha spenta apposta.", ""},
	"RX-SYSTEMD-003":   {BLOCCANTE, ServeAzione, "L'unità non esiste.", ""},
	"RX-FILE-001":      {BLOCCANTE, ServeAzione, "Il file è stato cambiato da qualcun altro durante l'operazione: non si tocca.", ""},

	// l'aggiornamento automatico (DECISIONI §10.10, T8)
	"RX-AGG-001": {INFO, ServeAzione, "REMOTIX è all'ultima versione del suo canale.", ""},
	"RX-AGG-002": {INFO, ServeAzione, "C'è un aggiornamento di manutenzione (sicurezza o ricostruzione): si applica da solo, come dice la configurazione.", ""},
	"RX-AGG-003": {AVVISO, ServeAzione, "C'è la versione annuale nuova: non si applica da sola, la sceglie l'amministratore.", "remotix-install aggiorna --annuale"},
	"RX-AGG-004": {AVVISO, ServeAzione, "C'è un aggiornamento, ma la configurazione dice di non applicarlo da solo (solo avviso).", "remotix-install aggiorna --applica"},
	"RX-AGG-005": {INFO, ServeAzione, "Gli aggiornamenti automatici sono spenti dalla configurazione.", ""},
	"RX-AGG-006": {BLOCCANTE, ServeAzione, "REMOTIX non è installato dall'installatore: non c'è niente da aggiornare da qui.", "Installare con remotix-install."},
	"RX-AGG-007": {BLOCCANTE, Riprovabile, "L'archivio di REMOTIX non risponde, o la sua firma non si verifica (il gestore di pacchetti lo rifiuta).", "Controllare la rete; se il gestore parla di firme, NON forzare: l'archivio può essere stato alterato."},
	"RX-AGG-008": {BLOCCANTE, ServeAzione, "Su Arch l'aggiornamento toccherebbe anche pacchetti non di REMOTIX (un aggiornamento parziale, che Arch non sostiene): non si applica da solo.", "pacman -Syu, poi remotix-install aggiorna"},
	"RX-AGG-009": {BLOCCANTE, ServeAzione, "La versione chiesta non è nell'archivio di REMOTIX.", "remotix-install aggiorna --controlla dice le versioni che ci sono."},
	"RX-AGG-010": {BLOCCANTE, ServeAzione, "La configurazione degli aggiornamenti non si legge.", "Correggere /etc/remotix/aggiornamenti.conf (remotix-install aggiorna --mostra)."},
	"RX-AGG-011": {AVVISO, ServeAzione, "L'aggiornamento automatico è sospeso fino a questa versione: l'amministratore ci è tornato indietro (remotix-install ritorna). Una versione più nuova riparte da sola.", "remotix-install aggiorna --applica (toglie la sospensione)"},
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
