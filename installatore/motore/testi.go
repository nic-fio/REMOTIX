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
	"cond.deposito_h264":    {"H.264 sulla scheda (e il ripiego software) solo con %s", "H.264 on the card (and the software fallback) only with %s"},
	"cond.nvidia":           {"NVIDIA col driver proprietario: niente codifica H.264 via VA-API", "NVIDIA with the proprietary driver: no H.264 encoding via VA-API"},
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

	"az.file":              {"scrivere %s", "write %s"},
	"az.file.fa":           {"si salva il file che c'è (se c'è), si scrive il nuovo in «%s» accanto, fsync, e lo si rinomina sopra", "the existing file (if any) is saved, the new one is written to «%s» next to it, fsync, and renamed over it"},
	"az.file.verifica":     {"sha256 e permessi del file uguali a quelli del piano", "file sha256 and permissions equal to the plan's"},
	"az.file.annulla":      {"si rimette il file salvato (o si toglie, se prima non c'era), e le cartelle create se sono rimaste vuote", "the saved file is put back (or removed, if it was not there), and created directories if left empty"},
	"az.gruppo":            {"mettere %s nel gruppo %s", "add %s to the %s group"},
	"az.gruppo.fa":         {"gpasswd -a %s %s (se non c'è già: altrimenti niente, e lo si annota come PREESISTENTE)", "gpasswd -a %s %s (unless already there: then nothing, recorded as PRE-EXISTING)"},
	"az.gruppo.verifica":   {"%s fra i membri di %s", "%s among the members of %s"},
	"az.gruppo.annulla":    {"gpasswd -d %s %s, solo se l'ha messo REMOTIX", "gpasswd -d %s %s, only if REMOTIX added them"},
	"az.unita":             {"abilitare l'unità %s", "enable the unit %s"},
	"az.unita.accesa":      {"abilitare e accendere l'unità %s", "enable and start the unit %s"},
	"az.unita.fa":          {"EnableUnitFiles %s sul D-Bus di systemd (senza avviarla)", "EnableUnitFiles %s on systemd's D-Bus (without starting it)"},
	"az.unita.verifica":    {"stato del file dell'unità %s = enabled", "unit file state of %s = enabled"},
	"az.unita.annulla":     {"DisableUnitFiles %s, se prima non era abilitata", "DisableUnitFiles %s, if it was not enabled before"},
	"az.fw":                {"aprire la porta %s (TCP e UDP) nel firewall", "open port %s (TCP and UDP) in the firewall"},
	"az.fw.fa":             {"addPort %s/tcp e /udp nella zona predefinita, vive e permanenti, sul D-Bus di firewalld", "addPort %s/tcp and /udp in the default zone, runtime and permanent, on firewalld's D-Bus"},
	"az.fw.verifica":       {"queryPort, vive e permanenti", "queryPort, runtime and permanent"},
	"az.fw.annulla":        {"removePort delle sole regole aggiunte da REMOTIX", "removePort of the rules added by REMOTIX only"},
	"az.fw.consenso":       {"Aprire la porta %s (TCP e UDP) nel firewall? (decisione D6, aperta)", "Open port %s (TCP and UDP) in the firewall? (decision D6, open)"},
	"az.desktop":           {"installare %s dagli archivi della distribuzione", "install %s from the distribution's archives"},
	"az.desktop.fa":        {"il gruppo di pacchetti della distribuzione per %s, senza display manager e senza graphical.target: davanti al monitor la macchina resta com'era", "the distribution's package group for %s, without a display manager and without graphical.target: at the monitor the machine stays as it was"},
	"az.desktop.verifica":  {"i pacchetti installati, e il palco che parte senza schermo", "the installed packages, and the stage starting headless"},
	"az.desktop.annulla":   {"si tolgono i pacchetti installati per noi che nessun altro vuole; quelli aggiornati restano (INDIRETTA, dichiarata)", "packages installed for us that nobody else wants are removed; upgraded ones stay (INDIRECT, declared)"},
	"az.cintura":           {"accendere la cintura %s", "switch on the safety belt %s"},
	"az.cintura.fa":        {"copia di %s in %s (temporaneo + rinomina), annotando il file dell'amministratore se c'era", "copy of %s to %s (temporary + rename), recording the administrator's file if there was one"},
	"az.cintura.verifica":  {"sha256 uguale alla sorgente", "sha256 equal to the source"},
	"az.cintura.annulla":   {"si toglie il file (o si rimette quello dell'amministratore)", "the file is removed (or the administrator's one is put back)"},
	"az.cintura.consenso":  {"Accendere le tre cinture (la macchina non si spegne, non si sospende, i tasti non la spengono)? (decisione D4, aperta)", "Switch on the three safety belts (the machine does not power off, does not suspend, keys do not power it off)? (decision D4, open)"},
	"az.servizio":          {"abilitare e accendere remotix.service", "enable and start remotix.service"},
	"az.servizio.fa":       {"EnableUnitFiles e StartUnit di remotix.service, dopo i controlli a servizio spento (7a)", "EnableUnitFiles and StartUnit of remotix.service, after the checks with the service stopped (7a)"},
	"az.servizio.verifica": {"attivo, la porta risponde in TCP e UDP (7b)", "active, the port answers on TCP and UDP (7b)"},
	"az.servizio.annulla":  {"StopUnit e DisableUnitFiles di remotix.service", "StopUnit and DisableUnitFiles of remotix.service"},

	"az.pacchetti":                  {"far installare %s al gestore di pacchetti della distribuzione", "have the distribution's package manager install %s"},
	"az.pacchetti.fa":               {"si risolve la transazione, si scarica tutto e si verifica (insieme risolto nel registro), poi il gestore installa dalla cache, senza rete", "the transaction is resolved, everything downloaded and verified (resolved set in the log), then the manager installs from the cache, offline"},
	"az.pacchetti.verifica":         {"ogni pacchetto dell'insieme risolto installato alla sua versione, gestore non a metà", "every package of the resolved set installed at its version, manager not half-way"},
	"az.pacchetti.annulla":          {"il gestore toglie i pacchetti NUOVI, e solo quelli (simulando prima); gli aggiornati restano e si dichiarano", "the manager removes the NEW packages, and only those (simulating first); upgraded ones stay and are declared"},
	"az.deposito":                   {"aggiungere l'archivio %s", "add the %s archive"},
	"az.deposito.fa.archivio":       {"la chiave dell'archivio (catena B) e la sorgente che la nomina: apt Signed-By + un pin che dall'archivio prende solo i pacchetti di REMOTIX; dnf gpgcheck, repo_gpgcheck, includepkgs; pacman un blocco [remotix] con SigLevel Required e la chiave in pacman-key", "the archive key (chain B) and the source naming it: apt Signed-By + a pin taking only REMOTIX packages from the archive; dnf gpgcheck, repo_gpgcheck, includepkgs; pacman a [remotix] block with SigLevel Required and the key in pacman-key"},
	"az.deposito.fa.epel":           {"dnf install epel-release, e il deposito CRB acceso", "dnf install epel-release, and the CRB repository enabled"},
	"az.deposito.fa.rpmfusion":      {"dnf install del pacchetto rpmfusion-free-release della versione della macchina", "dnf install of the rpmfusion-free-release package for the machine's version"},
	"az.deposito.fa.packman":        {"zypper addrepo di Packman (priorità 90) e refresh con la sua chiave", "zypper addrepo of Packman (priority 90) and refresh with its key"},
	"az.deposito.verifica":          {"l'archivio configurato", "the archive configured"},
	"az.deposito.annulla.archivio":  {"si tolgono i file (e la chiave da rpm o da pacman-key; il blocco da pacman.conf)", "the files are removed (and the key from rpm or pacman-key; the block from pacman.conf)"},
	"consenso.aggiornamenti":        {"Accendere gli aggiornamenti automatici di REMOTIX? Ogni giorno un timer fa controllare l'archivio firmato; secondo /etc/remotix/aggiornamenti.conf si applicano da soli, dal gestore di pacchetti e senza chiudere i desktop, gli aggiornamenti di sicurezza e le ricostruzioni; la versione annuale la sceglie l'amministratore (predefinito: la proposta di D14, non ancora decisa)", "Switch on automatic REMOTIX updates? Every day a timer has the signed archive checked; as /etc/remotix/aggiornamenti.conf says, security updates and rebuilds are applied automatically, by the package manager and without closing the desktops; the yearly version is chosen by the administrator (default: the D14 proposal, not decided yet)"},
	"az.aggiorna":                   {"portare i pacchetti di REMOTIX a %s: %s", "bring the REMOTIX packages to %s: %s"},
	"az.aggiorna.fa":                {"il gestore di pacchetti risolve e scarica dall'archivio firmato, poi installa quelle versioni esatte (apt install nome=versione, dnf install/downgrade dei file verificati, pacman -S/-U); il servizio riparte da sé (try-restart) e ritrova i desktop", "the package manager resolves and downloads from the signed archive, then installs those exact versions (apt install name=version, dnf install/downgrade of the verified files, pacman -S/-U); the service restarts by itself (try-restart) and finds the desktops again"},
	"az.aggiorna.verifica":          {"le versioni installate sono quelle del piano, e il servizio, se era acceso, è acceso", "the installed versions are those of the plan, and the service, if it was running, is running"},
	"az.aggiorna.annulla":           {"si torna alle versioni di prima, che l'archivio conserva", "back to the previous versions, which the archive keeps"},
	"agg.consenso_prima":            {"consenso dato all'installazione: aggiornamenti automatici = %s (%s)", "consent given at installation: automatic updates = %s (%s)"},
	"agg.consenso_ora":              {"a mano, da %s (remotix-install aggiorna/ritorna)", "by hand, by %s (remotix-install aggiorna/ritorna)"},
	"az.deposito.annulla.epel":      {"si toglie epel-release e CRB torna com'era; i pacchetti presi da lì restano (dichiarati)", "epel-release is removed and CRB goes back; packages taken from it stay (declared)"},
	"az.deposito.annulla.rpmfusion": {"si toglie rpmfusion-free-release; i pacchetti presi da lì restano (dichiarati)", "rpmfusion-free-release is removed; packages taken from it stay (declared)"},
	"az.deposito.annulla.packman":   {"zypper removerepo packman; i pacchetti presi da lì e la chiave restano (dichiarati)", "zypper removerepo packman; packages taken from it and the key stay (declared)"},
	"ind.deposito":                  {"deposito %s tolto: i pacchetti presi da lì e gli aggiornamenti restano", "repository %s removed: packages taken from it and upgrades stay"},
	"consenso.deposito":             {"Aggiungere l'archivio di terzi %s (per H.264 o per il desktop)? (decisione D5)", "Add the third-party archive %s (for H.264 or for the desktop)? (decision D5)"},
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
	"cert.firma_si":       {"firma verificata", "signature verified"},
	"cert.firma_no":       {"firma NON verificata: l'operazione si è fermata alla fase 0", "signature NOT verified: the operation stopped at phase 0"},

	// riga di comando
	"cli.uso": {`remotix-install — il motore d'installazione di REMOTIX (versione %s, formato %s)

  remotix-install verifica  [--json] [--porta N] [--catalogo FILE]
        guarda la macchina, SENZA TOCCARE NIENTE, e dice che cosa REMOTIX ci può fare
  remotix-install piano     [--uscita FILE] [--utente NOME] [--apri-firewall] [--json]
        prepara un piano di PROVA del motore
  remotix-install piano --installa --pacchetto FILE [--utente A,B] [--deposito epel,rpmfusion,packman]
                            [--apri-firewall] [--senza-cinture]
        prepara il piano dell'INSTALLAZIONE di REMOTIX
  remotix-install disinstalla [--purge]   prepara il piano della disinstallazione (dal registro)
  remotix-install approva   FILE-PIANO [--desktop gnome|kde|xfce|lxqt|no]
        scrive nel piano il consenso di chi lo lancia (per applicarlo senza domande)
  remotix-install applica   FILE-PIANO [--approva] [--senza-firma] [--eventi]
        applica il piano: si ferma se la macchina non è quella del piano
  remotix-install riprendi  [--eventi]    completa un'operazione interrotta
  remotix-install annulla   [--eventi]    annulla un'operazione non finita
  remotix-install stato                   le operazioni e il loro stato
  remotix-install aggiornato              per gli script del pacchetto dopo un aggiornamento:
        dice se l'installazione è certificata, rifà la verifica e riaccende il servizio se era acceso
  remotix-install catalogo [--tabella]    il catalogo in uso (--tabella: le tabelle di §3.1)

  opzioni comuni: --operazioni DIR (predefinita /var/lib/remotix/operazioni), --catalogo FILE,
  --lingua it|en (predefinita: dall'ambiente, LANGUAGE, LC_ALL, LC_MESSAGES, LANG)
  --eventi: gli eventi in JSON, una riga ciascuno (per le interfacce)
`, `remotix-install — the REMOTIX installation engine (version %s, format %s)

  remotix-install verifica  [--json] [--porta N] [--catalogo FILE]
        examines the machine, WITHOUT TOUCHING ANYTHING, and says what REMOTIX can do on it
  remotix-install piano     [--uscita FILE] [--utente NAME] [--apri-firewall] [--json]
        prepares an engine TEST plan
  remotix-install piano --installa --pacchetto FILE [--utente A,B] [--deposito epel,rpmfusion,packman]
                            [--apri-firewall] [--senza-cinture]
        prepares the REMOTIX INSTALLATION plan
  remotix-install disinstalla [--purge]   prepares the uninstallation plan (from the log)
  remotix-install approva   PLAN-FILE [--desktop gnome|kde|xfce|lxqt|no]
        writes the consent of whoever runs it into the plan (to apply it without questions)
  remotix-install applica   PLAN-FILE [--approva] [--senza-firma] [--eventi]
        applies the plan: stops if the machine is not the plan's machine
  remotix-install riprendi  [--eventi]    completes an interrupted operation
  remotix-install annulla   [--eventi]    rolls back an unfinished operation
  remotix-install stato                   the operations and their state
  remotix-install aggiornato              for the package scripts after an update:
        says whether the installation is certified, checks again and restarts the service if it was running
  remotix-install catalogo [--tabella]    the catalogue in use (--tabella: the tables of §3.1)

  common options: --operazioni DIR (default /var/lib/remotix/operazioni), --catalogo FILE,
  --lingua it|en (default: from the environment, LANGUAGE, LC_ALL, LC_MESSAGES, LANG)
  --eventi: the events as JSON, one line each (for the interfaces)
`},
	"cli.titolo":               {"REMOTIX — controllo della macchina (sola lettura: niente è stato toccato)", "REMOTIX — machine check (read only: nothing was touched)"},
	"cli.distribuzione":        {"Distribuzione", "Distribution"},
	"cli.catalogo":             {"Catalogo: %s (scade il %s)", "Catalogue: %s (expires on %s)"},
	"cli.desktop":              {"I desktop:", "The desktops:"},
	"cli.non_installato":       {"non installato", "not installed"},
	"cli.non_si_sa":            {"non si sa se c'è", "unknown whether present"},
	"cli.installato":           {"installato (%s)", "installed (%s)"},
	"cli.proposto":             {"  ← quello proposto se se ne installa uno", "  ← the one proposed if one is installed"},
	"cli.perche":               {"perché", "why"},
	"cli.condizione":           {"condizione", "condition"},
	"cli.comando":              {"comando", "command"},
	"cli.decisione":            {"(decisione %s, aperta)", "(decision %s, open)"},
	"cli.nota":                 {"nota", "note"},
	"cli.senza_desktop":        {"  ⚠ Nessun desktop supportato è installato: prima di installare REMOTIX si chiederà se\n    aggiungerne uno (se la risposta è no, REMOTIX non si installa: RX-DESKTOP-001).", "  ⚠ No supported desktop is installed: before installing REMOTIX you will be asked whether\n    to add one (if the answer is no, REMOTIX is not installed: RX-DESKTOP-001)."},
	"cli.incognite":            {"Quel che NON si è potuto sapere (non vale come «a posto»):", "What could NOT be found out (it does not count as «fine»):"},
	"cli.avvisi":               {"Avvisi e problemi:", "Warnings and problems:"},
	"cli.fatti":                {"I fatti (RILEVATO = visto; VERIFICATO = provato davvero; SCONOSCIUTO = non si sa):", "The facts (RILEVATO = seen; VERIFICATO = actually tested; SCONOSCIUTO = unknown):"},
	"cli.piano_scritto":        {"Piano (%s) %s scritto in %s", "Plan (%s) %s written to %s"},
	"cli.piano_macchina":       {"Macchina: %s — impronta %s (%d elementi vincolanti)", "Machine: %s — fingerprint %s (%d binding elements)"},
	"cli.piano_passo":          {"%d. %s  [%s, %s]\n   si fa: %s\n   si verifica: %s\n   si annulla: %s\n", "%d. %s  [%s, %s]\n   done by: %s\n   verified by: %s\n   rolled back by: %s\n"},
	"cli.consenso":             {"consenso richiesto: %s", "consent required: %s"},
	"cli.non_fatto":            {"non fatto: %s %s %s", "not done: %s %s %s"},
	"cli.per_applicarlo":       {"Per applicarlo: remotix-install approva %s && remotix-install applica %s", "To apply it: remotix-install approva %s && remotix-install applica %s"},
	"cli.approvato":            {"Piano %s approvato da %s (digest %s)", "Plan %s approved by %s (digest %s)"},
	"cli.serve_piano":          {"%s: serve il file del piano", "%s: the plan file is needed"},
	"cli.operazione":           {"operazione %s: %s", "operation %s: %s"},
	"cli.nessuna_op":           {"nessuna operazione in %s", "no operation in %s"},
	"cli.aperta":               {"  ← aperta: riprendi o annulla", "  ← open: resume or roll back"},
	"cli.certificata":          {"installazione certificata dall'installatore: operazione %s %s", "installation certified by the installer: operation %s %s"},
	"cli.riaccensione":         {"riaccensione di remotix.service", "restart of remotix.service"},
	"cli.fiducia":              {"Fiducia (catena A): catalogo %s, sequenza %d, sottochiave %s, radice %s, revoche %d; motore: %s", "Trust (chain A): catalogue %s, sequence %d, subkey %s, root %s, revocations %d; engine: %s"},
	"cli.fiducia_file":         {"%s: firma della catena A VALIDA per «%s» (sottochiave %s, valida dal %s al %s)", "%s: chain A signature VALID for «%s» (subkey %s, valid from %s to %s)"},
	"cli.senza_firma_ritirata": {"--senza-firma non esiste più (T8): la firma del catalogo si verifica sempre; senza rete si dà un catalogo fuori linea firmato con --catalogo FILE", "--senza-firma no longer exists (T8): the catalogue signature is always verified; without a network give a signed offline catalogue with --catalogo FILE"},
	"agg.mostra":               {"Aggiornamenti automatici (%s; il predefinito è la proposta di D14, non ancora decisa):", "Automatic updates (%s; the default is the D14 proposal, not decided yet):"},
	"agg.serve_versione":       {"ritorna: serve --versione (una versione di remotix che l'archivio conserva)", "ritorna: --versione is needed (a remotix version the archive keeps)"},
	"agg.titolo":               {"Aggiornamenti di REMOTIX — archivio %s, canale %s, automatico = %s", "REMOTIX updates — archive %s, channel %s, automatic = %s"},
	"agg.catalogo":             {"  catalogo: %s", "  catalogue: %s"},
	"cli.catalogo_info":        {"catalogo %s (sequenza %d), emesso il %s, scade il %s, motore minimo %s\ndigest %s\nfirma: %s\n", "catalogue %s (sequence %d), issued on %s, expires on %s, minimum engine %s\ndigest %s\nsignature: %s\n"},
}
