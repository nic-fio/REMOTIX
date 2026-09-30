package motore

// testi: il catalogo dei testi del motore e della riga di comando, per lingua (DECISIONI §10.15).
// Le chiavi sono stabili; i %s e %d seguono fmt.Sprintf e sono gli stessi nelle due lingue.
var testi = map[string]Testo{
	// stati (§6.6.2), come li dice l'avanzamento
	"stato.NUOVA":                   {"nuova", "new"},
	"stato.FIDATA":                  {"fiducia controllata", "trust checked"},
	"stato.ESAMINATA":               {"macchina esaminata", "machine examined"},
	"stato.VALUTATA":                {"compatibilità valutata", "compatibility assessed"},
	"stato.PIANIFICATA":             {"piano controllato", "plan checked"},
	"stato.APPROVATA":               {"piano approvato", "plan approved"},
	"stato.ACQUISITA":               {"tutto il necessario è pronto", "everything needed is ready"},
	"stato.IN_ESECUZIONE":           {"si applica il piano", "applying the plan"},
	"stato.INTERROTTA":              {"trovata interrotta", "found interrupted"},
	"stato.APPLICATA":               {"piano applicato", "plan applied"},
	"stato.IN_VERIFICA":             {"si verifica", "verifying"},
	"stato.VERIFICATA":              {"verificata", "verified"},
	"stato.CONFERMATA":              {"CONFERMATA", "CONFIRMED"},
	"stato.CONFERMATA_A_CONDIZIONI": {"CONFERMATA A CONDIZIONI", "CONFIRMED WITH CONDITIONS"},
	"stato.IN_ANNULLAMENTO":         {"si annulla", "rolling back"},
	"stato.ANNULLATA":               {"ANNULLATA: la macchina è com'era", "ROLLED BACK: the machine is as it was"},
	"stato.ANNULLATA_IN_PARTE":      {"ANNULLATA IN PARTE", "PARTLY ROLLED BACK"},
	"stato.BLOCCATA":                {"BLOCCATA", "BLOCKED"},
	"stato.RIFIUTATA":               {"RIFIUTATA: niente è stato toccato", "REFUSED: nothing was touched"},
	"ev.rimedio":                    {"rimedio", "remedy"},
	"ev.si_riprende":                {"si riprende", "resuming"},
	"ev.operazione":                 {"operazione %s", "operation %s"},

	// compatibilità (§6.6.8)
	"comp.nella_matrice":    {"nella matrice (%s)", "in the matrix (%s)"},
	"comp.fuori_matrice":    {"analizzata, fuori dalla matrice (%s)", "analysed, outside the matrix (%s)"},
	"comp.derivata":         {"derivata di %s (compatibile, non certificata)", "derivative of %s (compatible, not certified)"},
	"comp.esclusa":          {"esclusa", "excluded"},
	"comp.sconosciuta":      {"sconosciuta", "unknown"},
	"cond.componente":       {"l'installatore aggiunge «%s», che il desktop di serie non porta", "the installer adds «%s», which the stock desktop does not bring"},
	"cond.carattere":        {"manca un carattere scalabile: senza, labwc muore (labwc #2525)", "no scalable font: without one, labwc dies (labwc #2525)"},
	"cond.deposito_desktop": {"%s viene da %s", "%s comes from %s"},
	"cond.deposito_h264":    {"H.264 sulla scheda solo col driver di %s", "H.264 on the card only with the driver from %s"},
	"cond.deposito_base":    {"le librerie del video di REMOTIX (OpenH264, SVT-AV1) solo con %s", "REMOTIX's video libraries (OpenH264, SVT-AV1) only with %s"},
	"cond.nvidia":           {"NVIDIA col driver proprietario: niente codifica H.264 via VA-API", "NVIDIA with the proprietary driver: no H.264 encoding via VA-API"},
	"pacchetti.trattenuti":  {"i pacchetti nuovi non ci sono più, tranne quelli che restano perché li chiede chi resta: %s", "the new packages are gone, except those kept because something that stays needs them: %s"},
	"pacchetti.chiesto_da":  {"lo chiede %s", "needed by %s"},
	"cond.3d":               {"%s richiede l'accelerazione 3D della scheda: %s", "%s requires the card's 3D acceleration: %s"},
	"mot.3d":                {"%s richiede l'accelerazione 3D, e la macchina non ha una scheda (nessun nodo di rendering): %s", "%s requires 3D acceleration, and the machine has no card (no render node): %s"},
	"cond.ripiego":          {"la codifica passa al ripiego software", "encoding falls back to software"},
	"cond.ripiego_amd":      {"su %s Mesa è senza VA-API: con una scheda AMD la codifica è in software", "on %s Mesa has no VA-API: with an AMD card encoding is in software"},
	"cond.ripiego_senza":    {"nessuna scheda: la codifica è in software", "no graphics card: encoding is in software"},
	"cond.ripiego_no":       {"la scheda non codifica H.264: la codifica è in software", "the card does not encode H.264: encoding is in software"},
	"cond.desktop":          {"%s non c'è: l'installatore lo aggiunge dagli archivi della distribuzione, senza schermata d'accesso locale, solo col consenso", "%s is not there: the installer adds it from the distribution's archives, without a local login screen, only with consent"},
	"cond.desktop_rimedio":  {"rispondere «sì» alla domanda sul desktop; «no» ⇒ REMOTIX non si installa (RX-DESKTOP-001)", "answer «yes» to the desktop question; «no» ⇒ REMOTIX is not installed (RX-DESKTOP-001)"},
	"inc.openssl":           {"versione di OpenSSL", "OpenSSL version"},
	"inc.desktop":           {"desktop %s", "desktop %s"},
	"inc.h264":              {"H.264 sulla scheda (%s)", "H.264 on the card (%s)"},
	"scelta.desktop":        {"Su questa macchina non c'è un desktop supportato da REMOTIX: installarne uno? (se no, REMOTIX non si installa)", "This machine has no desktop supported by REMOTIX: install one? (if not, REMOTIX is not installed)"},

	// il piano di prova e i passi (§6.6.4)
	"np.desktop":          {"nessun desktop supportato: un'installazione vera qui chiederebbe quale aggiungere (%s; proposto %s)", "no supported desktop: a real installation would ask here which one to add (%s; proposed %s)"},
	"np.utente":           {"nessun utente indicato (--utente): il passo del gruppo «video» non c'è", "no user given (--utente): there is no «video» group step"},
	"np.firewall_no":      {"la porta %s non si apre nel firewall: non è stato chiesto (--apri-firewall; decisione D6 aperta)", "port %s is not opened in the firewall: not requested (--apri-firewall; decision D6 open)"},
	"np.firewall_nessuno": {"nessun firewall acceso: niente da aprire", "no firewall on: nothing to open"},
	"np.firewall_mano":    {"%s: aprire a mano la porta %s TCP e UDP", "%s: open port %s TCP and UDP by hand"},

	"az.file":                         {"scrivere %s", "write %s"},
	"az.file.fa":                      {"si salva il file che c'è (se c'è), si scrive il nuovo in «%s» accanto, fsync, e lo si rinomina sopra", "the existing file (if any) is saved, the new one is written to «%s» next to it, fsync, and renamed over it"},
	"az.file.verifica":                {"sha256 e permessi del file uguali a quelli del piano", "file sha256 and permissions equal to the plan's"},
	"az.file.annulla":                 {"si rimette il file salvato (o si toglie, se prima non c'era), e le cartelle create se sono rimaste vuote", "the saved file is put back (or removed, if it was not there), and created directories if left empty"},
	"az.gruppo":                       {"mettere %s nel gruppo %s", "add %s to the %s group"},
	"az.gruppo.fa":                    {"gpasswd -a %s %s (se non c'è già: altrimenti niente, e lo si annota come PREESISTENTE)", "gpasswd -a %s %s (unless already there: then nothing, recorded as PRE-EXISTING)"},
	"az.gruppo.verifica":              {"%s fra i membri di %s", "%s among the members of %s"},
	"az.gruppo.annulla":               {"gpasswd -d %s %s, solo se l'ha messo REMOTIX", "gpasswd -d %s %s, only if REMOTIX added them"},
	"az.unita":                        {"abilitare l'unità %s", "enable the unit %s"},
	"az.unita.fa":                     {"EnableUnitFiles %s sul D-Bus di systemd (senza avviarla)", "EnableUnitFiles %s on systemd's D-Bus (without starting it)"},
	"az.unita.verifica":               {"stato del file dell'unità %s = enabled", "unit file state of %s = enabled"},
	"az.unita.annulla":                {"DisableUnitFiles %s, se prima non era abilitata", "DisableUnitFiles %s, if it was not enabled before"},
	"az.fw":                           {"aprire la porta %s (TCP e UDP) nel firewall", "open port %s (TCP and UDP) in the firewall"},
	"az.fw.fa":                        {"il servizio remotix se il firewall lo conosce già, altrimenti le porte %s/tcp e /udp, vive e permanenti: firewalld sul suo D-Bus (zona predefinita), ufw col suo comando", "the remotix service if the firewall already knows it, otherwise ports %s/tcp and /udp, runtime and permanent: firewalld on its D-Bus (default zone), ufw with its command"},
	"az.fw.verifica":                  {"le regole vive e permanenti ci sono", "the runtime and permanent rules are there"},
	"az.fw.annulla":                   {"si tolgono le sole regole aggiunte da REMOTIX; una zona di firewalld che era quella di serie torna di serie", "only the rules added by REMOTIX are removed; a firewalld zone that was the stock one goes back to stock"},
	"az.fw.consenso":                  {"Aprire la porta %s (TCP e UDP) nel firewall? (decisione D6, aperta)", "Open port %s (TCP and UDP) in the firewall? (decision D6, open)"},
	"az.desktop":                      {"installare %s dagli archivi della distribuzione", "install %s from the distribution's archives"},
	"az.desktop.fa":                   {"il gruppo di pacchetti della distribuzione per %s, senza display manager e senza graphical.target: davanti al monitor la macchina resta com'era", "the distribution's package group for %s, without a display manager and without graphical.target: at the monitor the machine stays as it was"},
	"az.desktop.verifica":             {"i pacchetti installati, e il palco che parte senza schermo", "the installed packages, and the stage starting headless"},
	"az.desktop.annulla":              {"si tolgono i pacchetti installati per noi che nessun altro vuole; quelli aggiornati restano (INDIRETTA, dichiarata)", "packages installed for us that nobody else wants are removed; upgraded ones stay (INDIRECT, declared)"},
	"az.cintura":                      {"accendere la cintura %s", "switch on the safety belt %s"},
	"az.cintura.fa":                   {"copia di %s in %s (temporaneo + rinomina), annotando il file dell'amministratore se c'era", "copy of %s to %s (temporary + rename), recording the administrator's file if there was one"},
	"az.cintura.verifica":             {"sha256 uguale alla sorgente", "sha256 equal to the source"},
	"az.cintura.annulla":              {"si toglie il file (o si rimette quello dell'amministratore)", "the file is removed (or the administrator's one is put back)"},
	"az.cintura.dichiarata":           {"Le tre cinture si accendono sempre (D4, DECISIONI §4.7): da remoto e davanti al monitor la macchina non si potrà spegnere né sospendere, e i tasti non la spengono; solo root può.", "The three safety belts are always switched on (D4, DECISIONS §4.7): remotely and at the monitor the machine cannot be shut down or suspended, and the keys do not power it off; only root can."},
	"risposte.aggiornamenti_ignorata": {"consenso.aggiornamenti è ignorata: REMOTIX si aggiorna col sistema (D14)", "consenso.aggiornamenti is ignored: REMOTIX is updated with the system (D14)"},
	"risposte.cinture_ignorata":       {"consenso.cinture è ignorata: le cinture si accendono sempre (D4)", "consenso.cinture is ignored: the safety belts are always switched on (D4)"},
	"az.servizio":                     {"abilitare e accendere remotix.service", "enable and start remotix.service"},
	"az.servizio.fa":                  {"EnableUnitFiles e StartUnit di remotix.service, dopo i controlli a servizio spento (7a)", "EnableUnitFiles and StartUnit of remotix.service, after the checks with the service stopped (7a)"},
	"az.servizio.verifica":            {"attivo, la porta risponde in TCP e UDP (7b)", "active, the port answers on TCP and UDP (7b)"},
	"az.servizio.annulla":             {"StopUnit e DisableUnitFiles di remotix.service", "StopUnit and DisableUnitFiles of remotix.service"},

	"az.pacchetti":                  {"far installare %s al gestore di pacchetti della distribuzione", "have the distribution's package manager install %s"},
	"az.pacchetti.fa":               {"si risolve la transazione, si scarica tutto e si verifica (insieme risolto nel registro), poi il gestore installa dalla cache, senza rete", "the transaction is resolved, everything downloaded and verified (resolved set in the log), then the manager installs from the cache, offline"},
	"az.pacchetti.verifica":         {"ogni pacchetto dell'insieme risolto installato alla sua versione, gestore non a metà", "every package of the resolved set installed at its version, manager not half-way"},
	"az.pacchetti.annulla":          {"il gestore toglie i pacchetti NUOVI, e solo quelli (simulando prima); gli aggiornati restano e si dichiarano", "the manager removes the NEW packages, and only those (simulating first); upgraded ones stay and are declared"},
	"az.deposito":                   {"aggiungere l'archivio %s", "add the %s archive"},
	"az.deposito.fa.archivio":       {"la chiave dell'archivio e la sorgente che la nomina: apt Signed-By + un pin che dall'archivio prende solo i pacchetti di REMOTIX; dnf gpgcheck, repo_gpgcheck, includepkgs; pacman un blocco [remotix] con SigLevel Required e la chiave in pacman-key", "the archive key (chain B) and the source naming it: apt Signed-By + a pin taking only REMOTIX packages from the archive; dnf gpgcheck, repo_gpgcheck, includepkgs; pacman a [remotix] block with SigLevel Required and the key in pacman-key"},
	"az.deposito.fa.epel":           {"dnf install epel-release, e il deposito CRB acceso", "dnf install epel-release, and the CRB repository enabled"},
	"az.deposito.fa.rpmfusion":      {"dnf install del pacchetto rpmfusion-free-release della versione della macchina (e rpmfusion-nonfree-release se la scheda Intel lo chiede)", "dnf install of the rpmfusion-free-release package for the machine's version (and rpmfusion-nonfree-release if the Intel card needs it)"},
	"az.deposito.fa.openh264":       {"il deposito di OpenH264 di Cisco: acceso (Fedora), scritto in /etc/yum.repos.d con la chiave di EPEL (Alma), zypper addrepo (openSUSE)", "Cisco's OpenH264 repository: enabled (Fedora), written in /etc/yum.repos.d with the EPEL key (Alma), zypper addrepo (openSUSE)"},
	"az.deposito.fa.packman":        {"zypper addrepo di Packman (priorità 90) e refresh con la sua chiave", "zypper addrepo of Packman (priority 90) and refresh with its key"},
	"az.deposito.verifica":          {"l'archivio configurato", "the archive configured"},
	"az.deposito.annulla.archivio":  {"si tolgono i file (e la chiave da rpm o da pacman-key; il blocco da pacman.conf)", "the files are removed (and the key from rpm or pacman-key; the block from pacman.conf)"},
	"az.deposito.annulla.epel":      {"si toglie epel-release e CRB torna com'era; i pacchetti presi da lì restano (dichiarati)", "epel-release is removed and CRB goes back; packages taken from it stay (declared)"},
	"az.deposito.annulla.rpmfusion": {"si tolgono rpmfusion-free-release e rpmfusion-nonfree-release messi da noi; i pacchetti presi da lì restano (dichiarati)", "the rpmfusion-free-release and rpmfusion-nonfree-release we added are removed; packages taken from it stay (declared)"},
	"az.deposito.annulla.openh264":  {"il deposito torna com'era (spento, o il file tolto); i pacchetti presi da lì restano (dichiarati)", "the repository goes back as it was (disabled, or the file removed); packages taken from it stay (declared)"},
	"az.deposito.annulla.packman":   {"zypper removerepo packman; i pacchetti presi da lì e la chiave restano (dichiarati)", "zypper removerepo packman; packages taken from it and the key stay (declared)"},
	"ind.deposito":                  {"deposito %s tolto: i pacchetti presi da lì e gli aggiornamenti restano", "repository %s removed: packages taken from it and upgrades stay"},
	"consenso.deposito":             {"Aggiungere l'archivio di terzi %s (per il video o per il desktop)? (decisione D5)", "Add the third-party archive %s (for video or for the desktop)? (decision D5)"},
	"az.sessioni":                   {"chiudere le sessioni REMOTIX ancora aperte (%d: %s)", "close the REMOTIX sessions still open (%d: %s)"},
	"az.sessioni.fa":                {"logind TerminateSession sulle sole sessioni col servizio PAM «remotix»: le sessioni locali o ssh delle stesse persone restano", "logind TerminateSession on the sessions with PAM service «remotix» only: the same people's local or ssh sessions stay"},
	"az.sessioni.verifica":          {"nessuna di quelle sessioni è ancora aperta", "none of those sessions is still open"},
	"az.sessioni.annulla":           {"IRREVERSIBILE: il lavoro non salvato è perso, le sessioni non si riaprono", "IRREVERSIBLE: unsaved work is lost, sessions do not reopen"},
	"az.disfa":                      {"disfare: %s", "undo: %s"},
	"az.disfa.verifica":             {"com'era prima dell'installazione", "as it was before the installation"},
	"np.nessun_gruppo":              {"nessun nodo della scheda con un gruppo: nessuno da iscrivere", "no card node with a group: nobody to add"},
	"cond.codifica_ignota":          {"la codifica H.264 non è stata provata da REMOTIX (%s): vale il ripiego dichiarato", "H.264 encoding was not tested by REMOTIX (%s): the declared fallback applies"},
	"cond.ripiego_verificato":       {"la scheda non codifica H.264: REMOTIX codifica in software (%s)", "the card does not encode H.264: REMOTIX encodes in software (%s)"},
	"az.iscrizione":                 {"togliere %s dal gruppo %s (iscritto da REMOTIX alla prima connessione)", "remove %s from the %s group (added by REMOTIX at first connection)"},
	"az.iscrizione.fa":              {"gpasswd -d, se è ancora nel gruppo", "gpasswd -d, if still in the group"},
	"az.iscrizione.verifica":        {"non è più nel gruppo", "no longer in the group"},
	"az.iscrizione.annulla":         {"gpasswd -a (lo si rimette)", "gpasswd -a (added back)"},
	"ver.pam":                       {"la pila d'accesso di REMOTIX si risolve (file, inclusioni, moduli)", "the REMOTIX login stack resolves (files, includes, modules)"},
	"ver.porta":                     {"il firewall lascia passare la porta %s TCP e UDP", "the firewall lets port %s TCP and UDP through"},
	"ver.porta_nessuno":             {"nessun firewall acceso", "no firewall on"},
	"cond.pam_ignota":               {"la pila d'accesso non si è potuta controllare (%s)", "the login stack could not be checked (%s)"},
	"cond.porta_ignota":             {"non si sa se il firewall lascia passare la porta %s: controllarlo a mano", "unknown whether the firewall lets port %s through: check by hand"},
	"cond.porta_chiusa":             {"il firewall chiude %s: da fuori REMOTIX non si raggiunge finché non si apre (D6)", "the firewall closes %s: REMOTIX cannot be reached from outside until it is opened (D6)"},
	"cli.certifica":                 {"Certificazione dell'installazione %s: %s", "Certification of installation %s: %s"},
	"ver.codifica_assente":          {"la prova di codifica di REMOTIX non ha dato una risposta leggibile", "the REMOTIX encoding test gave no readable answer"},

	// operazione e certificato
	"op.chiesto":          {"chiesto da chi amministra", "requested by the administrator"},
	"op.no_desktop":       {"risposta «no» alla domanda sul desktop", "answer «no» to the desktop question"},
	"cert.titolo":         {"REMOTIX — certificato dell'operazione %s", "REMOTIX — certificate of operation %s"},
	"cert.stato":          {"stato finale", "final state"},
	"cert.mestiere":       {"mestiere", "job"},
	"cert.motore":         {"motore", "engine"},
	"cert.catalogo":       {"catalogo", "catalogue"},
	"cert.fiducia":        {"fiducia", "trust"},
	"cert.piano":          {"piano", "plan"},
	"cert.impronta":       {"impronta", "fingerprint"},
	"cert.controlli":      {"controlli", "checks"},
	"cert.condizioni":     {"condizioni", "conditions"},
	"cert.nessuna":        {"nessuna", "none"},
	"cert.non_annullato":  {"NON ANNULLATO", "NOT ROLLED BACK"},
	"cert.prodotto_prova": {"nessuno: piano di prova del motore (T4)", "none: engine test plan (T4)"},
	"cert.fiducia_no":     {"il catalogo NON si è potuto usare: l'operazione si è fermata alla fase 0", "the catalogue could NOT be used: the operation stopped at phase 0"},

	// riga di comando
	"cli.uso": {`remotix-install — il motore d'installazione di REMOTIX (versione %s, formato %s)

  remotix-install verifica  [--json] [--porta N] [--catalogo FILE]
        guarda la macchina, SENZA TOCCARE NIENTE, e dice che cosa REMOTIX ci può fare
  remotix-install piano     [--uscita FILE] [--utente NOME] [--apri-firewall] [--json]
        prepara un piano di PROVA del motore
  remotix-install piano --installa --pacchetto FILE [--utente A,B] [--deposito epel,openh264,rpmfusion,packman]
                            [--apri-firewall]
        prepara il piano dell'INSTALLAZIONE di REMOTIX
  remotix-install disinstalla [--purge]   prepara il piano della disinstallazione (dal registro)
  remotix-install approva   FILE-PIANO [--desktop gnome|kde|xfce|lxqt|no]
        scrive nel piano il consenso di chi lo lancia (per applicarlo senza domande)
  remotix-install applica   FILE-PIANO [--approva] [--eventi]
        applica il piano: si ferma se la macchina non è quella del piano
  remotix-install riprendi  [--eventi]    completa un'operazione interrotta
  remotix-install annulla   [--eventi]    annulla un'operazione non finita
  remotix-install stato                   le operazioni e il loro stato
  remotix-install aggiornato              per gli script dei pacchetti dopo un cambio di versione:
        annota le versioni, dice se l'installazione è certificata e se c'è un problema BLOCCANTE
  remotix-install certifica [--json]      rifà i controlli dell'installazione (VERDE, A_CONDIZIONI, ROSSO)
  REMOTIX si aggiorna col sistema (apt upgrade, dnf upgrade, zypper up, pacman -Syu): il motore non
        ha un comando per aggiornare; per tornare indietro, i comandi del gestore (remotix-install ritorna)
  remotix-install catalogo [--tabella]    il catalogo in uso (--tabella: le tabelle di §3.1)

  SENZA DOMANDE e SENZA RETE (§6.6.12):
  remotix-install installa --risposte FILE [--archivio URL | --fuori-linea DIR] [--eventi]
        piano dal file di risposte, registrato, e applicato: un consenso che manca ⇒ BLOCCATA
        (RX-RISPOSTE-001). Senza --risposte: mostra il piano e chiede una conferma al terminale
  remotix-install piano --installa --risposte FILE [...]   solo il piano (da leggere, o da portare
        approvato su macchine con la stessa impronta: remotix-install applica FILE-PIANO)
  remotix-install prepara-fuori-linea --archivio URL (--risposte FILE | --piano FILE) --uscita DIR
        su una macchina COLLEGATA uguale a quella senza rete: il pacchetto fuori linea (motore,
        insieme risolto, metadati firmati dei depositi); là: installa --fuori-linea DIR
  il file di risposte (formato remotix-risposte/1), una voce per riga, «#» commento:
        formato = remotix-risposte/1   lingua = it|en   porta = 7447   archivio = URL   canale = stabile
        utenti = tutti|a,b   desktop = gnome|kde|xfce|lxqt|no (solo se manca un desktop)
        consenso.firewall = si|no
        consenso.deposito.rpmfusion|packman|epel|openh264 = si|no
        (ogni consenso che su quella macchina serve va dato, «si» o «no»)

  opzioni comuni: --operazioni DIR (predefinita /var/lib/remotix/operazioni), --catalogo FILE (dato a mano),
  --lingua it|en (predefinita: dall'ambiente, LANGUAGE, LC_ALL, LC_MESSAGES, LANG)
  --eventi: gli eventi in JSON, una riga ciascuno (per le interfacce)
`, `remotix-install — the REMOTIX installation engine (version %s, format %s)

  remotix-install verifica  [--json] [--porta N] [--catalogo FILE]
        examines the machine, WITHOUT TOUCHING ANYTHING, and says what REMOTIX can do on it
  remotix-install piano     [--uscita FILE] [--utente NAME] [--apri-firewall] [--json]
        prepares an engine TEST plan
  remotix-install piano --installa --pacchetto FILE [--utente A,B] [--deposito epel,openh264,rpmfusion,packman]
                            [--apri-firewall]
        prepares the REMOTIX INSTALLATION plan
  remotix-install disinstalla [--purge]   prepares the uninstallation plan (from the log)
  remotix-install approva   PLAN-FILE [--desktop gnome|kde|xfce|lxqt|no]
        writes the consent of whoever runs it into the plan (to apply it without questions)
  remotix-install applica   PLAN-FILE [--approva] [--eventi]
        applies the plan: stops if the machine is not the plan's machine
  remotix-install riprendi  [--eventi]    completes an interrupted operation
  remotix-install annulla   [--eventi]    rolls back an unfinished operation
  remotix-install stato                   the operations and their state
  remotix-install aggiornato              for the package scripts after a version change:
        records the versions, says whether the installation is certified and whether there is a BLOCKING problem
  remotix-install certifica [--json]      runs the installation checks again (VERDE, A_CONDIZIONI, ROSSO)
  REMOTIX is updated with the system (apt upgrade, dnf upgrade, zypper up, pacman -Syu): the engine
        has no update command; to go back, the package manager commands (remotix-install ritorna)
  remotix-install catalogo [--tabella]    the catalogue in use (--tabella: the tables of §3.1)

  UNATTENDED and OFFLINE (§6.6.12):
  remotix-install installa --risposte FILE [--archivio URL | --fuori-linea DIR] [--eventi]
        plan from the answer file, logged, and applied: a missing consent ⇒ BLOCKED
        (RX-RISPOSTE-001). Without --risposte: shows the plan and asks for one confirmation at the terminal
  remotix-install piano --installa --risposte FILE [...]   only the plan (to read, or to carry
        approved to machines with the same fingerprint: remotix-install applica PLAN-FILE)
  remotix-install prepara-fuori-linea --archivio URL (--risposte FILE | --piano FILE) --uscita DIR
        on a CONNECTED machine identical to the offline one: the offline bundle (engine,
        resolved set, signed repository metadata); there: installa --fuori-linea DIR
  the answer file (format remotix-risposte/1), one entry per line, «#» comment:
        formato = remotix-risposte/1   lingua = it|en   porta = 7447   archivio = URL   canale = stabile
        utenti = tutti|a,b   desktop = gnome|kde|xfce|lxqt|no (only if a desktop is missing)
        consenso.firewall = si|no
        consenso.deposito.rpmfusion|packman|epel|openh264 = si|no
        (every consent that machine needs must be given, «si» or «no»)

  common options: --operazioni DIR (default /var/lib/remotix/operazioni), --catalogo FILE (given by hand),
  --lingua it|en (default: from the environment, LANGUAGE, LC_ALL, LC_MESSAGES, LANG)
  --eventi: the events as JSON, one line each (for the interfaces)
`},
	"cli.titolo":             {"REMOTIX — controllo della macchina (sola lettura: niente è stato toccato)", "REMOTIX — machine check (read only: nothing was touched)"},
	"cli.distribuzione":      {"Distribuzione", "Distribution"},
	"cli.catalogo":           {"Catalogo: %s", "Catalogue: %s"},
	"cli.desktop":            {"I desktop:", "The desktops:"},
	"cli.non_installato":     {"non installato", "not installed"},
	"cli.non_si_sa":          {"non si sa se c'è", "unknown whether present"},
	"cli.installato":         {"installato (%s)", "installed (%s)"},
	"cli.proposto":           {"  ← quello proposto se se ne installa uno", "  ← the one proposed if one is installed"},
	"cli.perche":             {"perché", "why"},
	"cli.condizione":         {"condizione", "condition"},
	"cli.comando":            {"comando", "command"},
	"cli.decisione":          {"(decisione %s, aperta)", "(decision %s, open)"},
	"cli.nota":               {"nota", "note"},
	"cli.senza_desktop":      {"  ⚠ Nessun desktop supportato è installato: prima di installare REMOTIX si chiederà se\n    aggiungerne uno (se la risposta è no, REMOTIX non si installa: RX-DESKTOP-001).", "  ⚠ No supported desktop is installed: before installing REMOTIX you will be asked whether\n    to add one (if the answer is no, REMOTIX is not installed: RX-DESKTOP-001)."},
	"cli.incognite":          {"Quel che NON si è potuto sapere (non vale come «a posto»):", "What could NOT be found out (it does not count as «fine»):"},
	"cli.avvisi":             {"Avvisi e problemi:", "Warnings and problems:"},
	"cli.fatti":              {"I fatti (RILEVATO = visto; VERIFICATO = provato davvero; SCONOSCIUTO = non si sa):", "The facts (RILEVATO = seen; VERIFICATO = actually tested; SCONOSCIUTO = unknown):"},
	"cli.piano_scritto":      {"Piano (%s) %s scritto in %s", "Plan (%s) %s written to %s"},
	"cli.piano_macchina":     {"Macchina: %s — impronta %s (%d elementi vincolanti)", "Machine: %s — fingerprint %s (%d binding elements)"},
	"cli.piano_passo":        {"%d. %s  [%s, %s]\n   si fa: %s\n   si verifica: %s\n   si annulla: %s\n", "%d. %s  [%s, %s]\n   done by: %s\n   verified by: %s\n   rolled back by: %s\n"},
	"cli.consenso":           {"consenso richiesto: %s", "consent required: %s"},
	"cli.non_fatto":          {"non fatto: %s %s %s", "not done: %s %s %s"},
	"cli.per_applicarlo":     {"Per applicarlo: remotix-install approva %s && remotix-install applica %s", "To apply it: remotix-install approva %s && remotix-install applica %s"},
	"cli.gia_approvato":      {"Già approvato (%s): si applica così com'è, anche su altre macchine con la stessa impronta: remotix-install applica %s", "Already approved (%s): it is applied as it is, also on other machines with the same fingerprint: remotix-install applica %s"},
	"cli.risposte":           {"Dal file di risposte %s (sha256 %s): %d voci", "From the answer file %s (sha256 %s): %d entries"},
	"cli.risposte_predef":    {"  scelte non dette dal file, al valore predefinito: %s", "  choices the file does not state, at their default: %s"},
	"cli.risposte_superflue": {"  voci senza effetto su questa macchina: %s", "  entries with no effect on this machine: %s"},
	"cli.risposte_mancanti":  {"  ⛔ consensi che servono e che il file NON dà: %s — l'operazione sarà BLOCCATA (RX-RISPOSTE-001)", "  ⛔ consents that are needed and that the file does NOT give: %s — the operation will be BLOCKED (RX-RISPOSTE-001)"},
	"cli.conferma":           {"Applicare questo piano? Scrivere «si» per confermare: ", "Apply this plan? Type «yes» to confirm: "},
	"cli.non_confermato":     {"non confermato: niente è stato toccato", "not confirmed: nothing was touched"},
	"cli.dichiarato":         {"si fa sempre: %s", "always done: %s"},
	"cli.router":             {"Da fuori della rete locale: inoltra sul router la porta %d, TCP e UDP, verso questa macchina (REMOTIX non lo fa da sé: niente UPnP).", "From outside the local network: forward port %d, TCP and UDP, on the router to this machine (REMOTIX does not do it by itself: no UPnP)."},
	"cli.senza_terminale":    {"nessun terminale per chiedere la conferma: per installare senza domande serve --risposte FILE (§6.6.12)", "no terminal to ask for confirmation: an unattended installation needs --risposte FILE (§6.6.12)"},
	"cli.fuori_linea":        {"Pacchetto fuori linea %s: %s, canale %s, %d artefatti, %d file verificati, preparato il %s", "Offline bundle %s: %s, channel %s, %d artefacts, %d files verified, prepared on %s"},
	"cli.preparato":          {"Pacchetto fuori linea pronto in %s: %d artefatti, %d file (%d MB). Impronta della macchina di riferimento %s, %d pacchetti.", "Offline bundle ready in %s: %d artefacts, %d files (%d MB). Reference machine fingerprint %s, %d packages."},
	"cli.approvato":          {"Piano %s approvato da %s (digest %s)", "Plan %s approved by %s (digest %s)"},
	"cli.serve_piano":        {"%s: serve il file del piano", "%s: the plan file is needed"},
	"cli.operazione":         {"operazione %s: %s", "operation %s: %s"},
	"cli.nessuna_op":         {"nessuna operazione in %s", "no operation in %s"},
	"cli.aperta":             {"  ← aperta: riprendi o annulla", "  ← open: resume or roll back"},
	"cli.certificata":        {"installazione certificata dall'installatore: operazione %s %s", "installation certified by the installer: operation %s %s"},
	"cli.fiducia":            {"Fiducia: catalogo %s, sequenza %d — %s", "Trust: catalogue %s, sequence %d — %s"},
	"cli.col_sistema":        {"REMOTIX si aggiorna col sistema (DECISIONI §10.23): apt upgrade · dnf upgrade · zypper up · pacman -Syu.\nPer tornare a una versione precedente, i comandi del gestore di pacchetti:\n  apt install remotix=VERSIONE remotix-install=VERSIONE   (le versioni: apt list -a remotix)\n  dnf downgrade remotix remotix-install\n  zypper install --oldpackage remotix-VERSIONE remotix-install-VERSIONE\n  pacman -U /var/cache/pacman/pkg/remotix-VERSIONE-x86_64.pkg.tar.zst (o dall'archivio)\nIl servizio riparte senza chiudere i desktop; dopo, remotix-install certifica.\n", "REMOTIX is updated with the system (DECISIONS §10.23): apt upgrade · dnf upgrade · zypper up · pacman -Syu.\nTo go back to a previous version, use the package manager commands:\n  apt install remotix=VERSION remotix-install=VERSION   (the versions: apt list -a remotix)\n  dnf downgrade remotix remotix-install\n  zypper install --oldpackage remotix-VERSION remotix-install-VERSION\n  pacman -U /var/cache/pacman/pkg/remotix-VERSION-x86_64.pkg.tar.zst (or from the archive)\nThe service restarts without closing the desktops; afterwards, remotix-install certifica.\n"},
	"cli.versioni_annotate":  {"versioni di REMOTIX annotate: %s", "REMOTIX versions recorded: %s"},
	"fid.pacchetto":          {"il catalogo del pacchetto remotix-install (lo garantisce il gestore di pacchetti, dall'archivio firmato di REMOTIX)", "the catalogue of the remotix-install package (guaranteed by the package manager, from the signed REMOTIX archive)"},
	"fid.scaricato":          {"il catalogo del motore %s (scaricato da install.sh, che lo verifica con lo sha256 pubblicato)", "the catalogue of the engine %s (downloaded by install.sh, which checks it against the published sha256)"},
	"fid.a_mano":             {"il catalogo dato a mano: %s (dell'amministratore)", "the catalogue given by hand: %s (the administrator's)"},
	"cli.catalogo_info":      {"catalogo %s (sequenza %d), emesso il %s, motore minimo %s\ndigest %s\n%s\n", "catalogue %s (sequence %d), issued on %s, minimum engine %s\ndigest %s\n%s\n"},
}
