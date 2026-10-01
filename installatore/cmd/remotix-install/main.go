// remotix-install: il motore d'installazione di REMOTIX, e la sua riga di comando
// (fasi/17-l-installatore.md §6.0, §6.6). Binario statico: gira da root su ogni distribuzione
// prima che sia installato qualunque pacchetto (fase 0 TRUST), senza Python né librerie.
//
// T4-T5: verifica (fasi 1-2, sola lettura), piano, approva, applica (fasi 4-8), riprendi, annulla,
// stato, disinstalla, certifica. T8: l'installazione dall'archivio firmato (--archivio). Dopo D11 e
// D14 (DECISIONI §10.21, §10.23): il catalogo è quello del motore (nel pacchetto remotix-install), e
// REMOTIX si aggiorna col sistema — il motore non ha un comando per aggiornare né un timer.
package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"sort"
	"strings"
	"time"

	"remotix/installatore/catalogo"
	"remotix/installatore/chiavi"
	"remotix/installatore/motore"
)

func main() {
	// --lingua prima di tutto: quando la parte da amministratore è rilanciata (polkit ripulisce
	// l'ambiente) la lingua arriva da qui (DECISIONI §10.15)
	for i, a := range os.Args {
		if v, ok := strings.CutPrefix(a, "--lingua="); ok {
			motore.ImpostaLingua(v)
		} else if (a == "--lingua" || a == "-lingua") && i+1 < len(os.Args) {
			motore.ImpostaLingua(os.Args[i+1])
		}
	}
	uso := motore.T("cli.uso", motore.VersioneMotore, motore.Formato)
	if len(os.Args) < 2 {
		fmt.Fprint(os.Stderr, uso)
		os.Exit(2)
	}
	cmd, arg := os.Args[1], os.Args[2:]
	var err error
	codice := 0
	switch cmd {
	case "verifica":
		codice, err = verifica(arg)
	case "piano":
		err = piano(arg)
	case "approva":
		err = approva(arg)
	case "applica", "riprendi", "annulla":
		codice, err = opera(cmd, arg)
	case "stato":
		err = stato(arg)
	case "aggiornato":
		codice, err = aggiornato(arg)
	case "disinstalla":
		err = disinstalla(arg)
	case "certifica":
		codice, err = certifica(arg)
	case "catalogo":
		err = mostraCatalogo(arg)
	case "aggiorna", "ritorna":
		// DECISIONI §10.23: REMOTIX si aggiorna (e torna indietro) coi comandi del gestore di pacchetti
		fmt.Fprint(os.Stderr, T("cli.col_sistema"))
		codice = 2
	case "installa":
		codice, err = installa(arg)
	case "prepara-fuori-linea":
		codice, err = preparaFuoriLinea(arg)
	case "gui":
		codice, err = guiCmd(arg)
	case "tui":
		codice, err = tuiCmd(arg)
	case "motore-interfaccia":
		codice, err = motoreInterfaccia(arg)
	case "versione", "--version":
		fmt.Println(motore.VersioneMotore, motore.Formato)
	case "aiuto", "help", "--help", "-h":
		fmt.Print(uso)
	default:
		fmt.Fprint(os.Stderr, uso)
		os.Exit(2)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "remotix-install:", err)
		if codice == 0 {
			codice = 1
		}
	}
	os.Exit(codice)
}

// comuni: le opzioni di tutti i comandi.
type comuni struct {
	operazioni, catalogo, archivio, canale, lingua string
	porta                                          int
	risposte, fuoriLinea                           string
}

func (c *comuni) aggiungi(fs *flag.FlagSet) {
	fs.StringVar(&c.operazioni, "operazioni", "/var/lib/remotix/operazioni", "dove stanno le operazioni")
	fs.StringVar(&c.catalogo, "catalogo", "", "un catalogo dato a mano, al posto di quello del motore (è dell'amministratore)")
	fs.StringVar(&c.archivio, "archivio", "", "l'archivio firmato di REMOTIX (URL di base)")
	fs.StringVar(&c.canale, "canale", "stabile", "il canale dell'archivio: stabile o candidato")
	fs.IntVar(&c.porta, "porta", 7447, "la porta di REMOTIX (TCP e UDP)")
	fs.StringVar(&c.lingua, "lingua", "", "it o en (già letta in main)")
	fs.StringVar(&c.risposte, "risposte", "", "il file di risposte: l'installazione senza domande (§6.6.12)")
	fs.StringVar(&c.fuoriLinea, "fuori-linea", "", "il pacchetto fuori linea (prepara-fuori-linea): l'archivio è quello, senza rete")
}

// leggiRisposte: il file di risposte, se c'è. Fissa la lingua (se non data con --lingua), e dà
// l'archivio e il canale se la riga di comando non li dice.
func (c *comuni) leggiRisposte() (*motore.FileRisposte, error) {
	if c.risposte == "" {
		return nil, nil
	}
	r, err := motore.LeggiRisposte(c.risposte)
	if err != nil {
		return nil, err
	}
	if l := r.Voci["lingua"]; l != "" && c.lingua == "" {
		motore.ImpostaLingua(l)
	}
	if c.archivio == "" && c.fuoriLinea == "" {
		c.archivio = r.Voci["archivio"]
	}
	if v := r.Voci["canale"]; v != "" {
		c.canale = v
	}
	return r, nil
}

// leggiFuoriLinea: il pacchetto fuori linea, se c'è (ogni file verificato col suo sha256); il suo
// archivio locale diventa l'archivio.
func (c *comuni) leggiFuoriLinea() (*motore.PacchettoFuoriLinea, error) {
	if c.fuoriLinea == "" {
		return nil, nil
	}
	fl, err := motore.LeggiFuoriLinea(c.fuoriLinea)
	if err != nil {
		return nil, err
	}
	c.archivio, c.canale = fl.URLArchivio(), fl.Canale
	fmt.Fprintln(os.Stderr, T("cli.fuori_linea", fl.Dir, fl.Bersaglio, fl.Canale, len(fl.Artefatti), len(fl.File), fl.Creato))
	return fl, nil
}

// opzioniInstallazione: quelle che vengono dalla riga di comando (archivio, porta).
func (c *comuni) opzioniInstallazione() motore.OpzioniInstallazione {
	return motore.OpzioniInstallazione{Archivio: c.archivio, Canale: c.canale, Chiave: chiavi.Archivio,
		Impronta: chiavi.ImprontaArchivio(), Porta: c.porta}
}

func stampaRisposte(p *motore.Piano) {
	r := p.Risposte
	if r == nil {
		return
	}
	fmt.Println(T("cli.risposte", r.File, r.Sha256[:16]+"…", len(r.Voci)))
	if len(r.Predefinite) > 0 {
		fmt.Println(T("cli.risposte_predef", strings.Join(r.Predefinite, ", ")))
	}
	if len(r.Superflue) > 0 {
		fmt.Println(T("cli.risposte_superflue", strings.Join(r.Superflue, ", ")))
	}
	if len(r.Mancanti) > 0 {
		fmt.Println(T("cli.risposte_mancanti", strings.Join(r.Mancanti, ", ")))
	}
}

// fonti: da dove viene il catalogo (fase 0 TRUST): quello del motore, o quello dato a mano.
func (c *comuni) fonti() *motore.FontiFiducia {
	return &motore.FontiFiducia{Incorporato: catalogo.Incorporato, Esplicito: c.catalogo}
}

// leggiCatalogo: la fase 0 TRUST, senza scrivere niente (verifica, piano, catalogo, certifica).
func (c *comuni) leggiCatalogo() (*motore.Catalogo, error) {
	cat, _, err := c.fidati()
	return cat, err
}

func (c *comuni) fidati() (*motore.Catalogo, *motore.Fiducia, error) {
	return c.fonti().Fidati(time.Now())
}

// argomenti: le opzioni possono stare prima o dopo i nomi di file.
func argomenti(fs *flag.FlagSet, arg []string) ([]string, error) {
	var posizionali []string
	for {
		if err := fs.Parse(arg); err != nil {
			return nil, err
		}
		if fs.NArg() == 0 {
			return posizionali, nil
		}
		posizionali = append(posizionali, fs.Arg(0))
		arg = fs.Args()[1:]
	}
}

// T: il catalogo dei testi del motore (una lingua per volta, DECISIONI §10.15).
var T = motore.T

func chi() string {
	for _, v := range []string{"SUDO_USER", "USER", "LOGNAME"} {
		if s := os.Getenv(v); s != "" {
			return s
		}
	}
	return fmt.Sprintf("uid %d", os.Getuid())
}

func stampaJSON(v any) {
	b, _ := json.MarshalIndent(v, "", "  ")
	fmt.Println(string(b))
}

func verifica(arg []string) (int, error) {
	fs := flag.NewFlagSet("verifica", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	comeJSON := fs.Bool("json", false, "profilo e rapporto in JSON")
	if _, err := argomenti(fs, arg); err != nil {
		return 2, err
	}
	cat, fid, errF := c.fidati() // verifica non scrive niente (R1)
	if errF != nil {
		if *comeJSON {
			stampaJSON(map[string]any{"formato": motore.Formato, "fiducia": fid})
		} else if fid != nil {
			stampaFiducia(fid)
		}
		return 1, errF
	}
	amb := motore.AmbienteVero()
	prof := motore.Preflight(amb, motore.OpzioniPreflight{Porta: c.porta, Pacchetti: cat.Componenti()})
	rap := motore.Valuta(cat, prof)
	if *comeJSON {
		stampaJSON(map[string]any{"formato": motore.Formato, "fiducia": fid, "profilo": prof, "compatibilita": rap})
	} else {
		stampaRapporto(fid, prof, rap)
	}
	for _, e := range rap.Desktop {
		if e.Livello != motore.NON_SUPPORTATA {
			return 0, nil
		}
	}
	return 1, nil
}

func stampaRapporto(fid *motore.Fiducia, p *motore.Profilo, r *motore.Rapporto) {
	fmt.Printf("%s\n\n", T("cli.titolo"))
	fmt.Printf("%s: %s — %s\n", T("cli.distribuzione"), r.Piattaforma, r.Riconosciuta)
	fmt.Printf("%s\n", T("cli.catalogo", r.Catalogo.Versione))
	fmt.Printf("%s\n\n", T("cli.fiducia", fid.Catalogo.Versione, fid.Sequenza, fid.Fonte))
	fmt.Printf("%s\n", T("cli.desktop"))
	for _, e := range r.Desktop {
		inst := e.Installato
		switch inst {
		case "assente":
			inst = T("cli.non_installato")
		case "sconosciuto":
			inst = T("cli.non_si_sa")
		default:
			inst = T("cli.installato", inst)
		}
		rif := ""
		if e.Riferimento {
			rif = T("cli.proposto")
		}
		fmt.Printf("  %-11s %-28s %s%s\n", e.Nome, inst, e.Livello, rif)
		for _, m := range e.Motivi {
			fmt.Printf("      %s: [%s] %s %s\n", T("cli.perche"), m.Codice, m.Testo, m.Dettaglio)
		}
		for _, k := range e.Condizioni {
			fmt.Printf("      %s %s: %s\n", T("cli.condizione"), k.Codice, k.Testo)
			if k.Rimedio != "" {
				fmt.Printf("          %s: %s\n", T("cli.comando"), k.Rimedio)
			}
			if k.Decisione != "" {
				fmt.Printf("          %s\n", T("cli.decisione", k.Decisione))
			}
		}
		for _, n := range e.Note {
			fmt.Printf("      %s: %s\n", T("cli.nota"), n)
		}
	}
	if r.SenzaDesktop {
		fmt.Printf("\n%s\n", T("cli.senza_desktop"))
	}
	if len(r.Incognite) > 0 {
		fmt.Printf("\n%s\n", T("cli.incognite"))
		for _, x := range r.Incognite {
			fmt.Printf("  - %s\n", x)
		}
	}
	fmt.Printf("\n%s\n", T("cli.avvisi"))
	msgs := append(append([]motore.Messaggio{}, fid.Messaggi...), p.Messaggi...)
	sort.SliceStable(msgs, func(i, j int) bool { return peso(msgs[i].Gravita) > peso(msgs[j].Gravita) })
	for _, m := range msgs {
		fmt.Printf("  [%s] %-9s %s", m.Codice, m.Gravita, m.Testo)
		if m.Dettaglio != "" {
			fmt.Printf(" (%s)", m.Dettaglio)
		}
		fmt.Println()
		if m.Rimedio != "" {
			fmt.Printf("                  %s: %s\n", T("ev.rimedio"), m.Rimedio)
		}
	}
	fmt.Printf("\n%s\n", T("cli.fatti"))
	for _, f := range p.Fatti {
		v := f.Valore
		if f.Stato == motore.SCONOSCIUTO {
			v = "?"
		}
		fmt.Printf("  %-34s %-40s %-11s %s\n", f.Chiave, tronca(v, 40), f.Stato, tronca(strings.TrimSpace(f.Fonte+" "+f.Nota), 70))
	}
	for _, n := range r.Note {
		fmt.Printf("\n%s: %s", T("cli.nota"), n)
	}
	fmt.Println()
}

func peso(g motore.Gravita) int {
	switch g {
	case motore.BLOCCANTE:
		return 2
	case motore.AVVISO:
		return 1
	}
	return 0
}

func tronca(s string, n int) string {
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n-1]) + "…"
}

func piano(arg []string) error {
	fs := flag.NewFlagSet("piano", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	uscita := fs.String("uscita", "", "dove scrivere il piano (predefinito piano-<mestiere>.json)")
	utente := fs.String("utente", "", "prova: chi mettere nel gruppo video; installazione: le persone da iscrivere ai gruppi della scheda, separate da virgola (vuoto: tutte le persone della macchina)")
	apri := fs.Bool("apri-firewall", false, "mettere nel piano l'apertura della porta (D6)")
	comeJSON := fs.Bool("json", false, "stampa anche il piano in JSON")
	installa := fs.Bool("installa", false, "il piano dell'INSTALLAZIONE di REMOTIX (invece del piano di prova)")
	pacchetto := fs.String("pacchetto", "", "installazione: il pacchetto di REMOTIX da un file (.deb/.rpm/.pkg.tar.zst), invece dell'archivio")
	depositi := fs.String("deposito", "", "installazione: archivi di terzi col consenso (D5), separati da virgola: epel, rpmfusion, packman")
	nomi := fs.String("pacchetti", "", "prova: pacchetti dai depositi da far installare (separati da virgola)")
	if _, err := argomenti(fs, arg); err != nil {
		return err
	}
	r, err := c.leggiRisposte()
	if err != nil {
		return err
	}
	if _, err := c.leggiFuoriLinea(); err != nil {
		return err
	}
	cat, err := c.leggiCatalogo()
	if err != nil {
		return err
	}
	amb := motore.AmbienteVero()
	prof := motore.Preflight(amb, motore.OpzioniPreflight{Porta: c.porta, Pacchetti: cat.Componenti()})
	rap := motore.Valuta(cat, prof)
	var p *motore.Piano
	if r != nil {
		// senza domande: le scelte e i consensi SOLO dal file (le opzioni di consenso della riga di
		// comando non valgono: il consenso è quello scritto)
		p, err = motore.PianoDaRisposte(r, prof, rap, cat, amb, c.opzioniInstallazione())
		if err != nil {
			return err
		}
		if *uscita == "" {
			*uscita = "piano-" + p.Mestiere + ".json"
		}
		stampaRisposte(p)
		return stampaPiano(p, *uscita, *comeJSON)
	}
	if *installa {
		o := motore.OpzioniInstallazione{Pacchetto: *pacchetto, ApriFirewall: *apri, Porta: c.porta}
		if *pacchetto == "" && c.archivio != "" {
			o.Archivio, o.Canale, o.Chiave, o.Impronta = c.archivio, c.canale, chiavi.Archivio, chiavi.ImprontaArchivio()
		}
		if *utente != "" {
			o.Utenti = strings.Split(*utente, ",")
		}
		if *depositi != "" {
			o.Depositi = strings.Split(*depositi, ",")
		}
		p, err = motore.PianoInstallazione(prof, rap, cat, amb, o)
	} else {
		if *utente == "" {
			*utente = os.Getenv("SUDO_USER")
		}
		o := motore.OpzioniPianoProva{Utente: *utente, ApriFirewall: *apri, Porta: c.porta, Pacchetti: *nomi}
		if *depositi != "" {
			o.Depositi = strings.Split(*depositi, ",")
		}
		p, err = motore.PianoDiProva(prof, rap, cat, amb, o)
	}
	if err != nil {
		return err
	}
	if *uscita == "" {
		*uscita = "piano-" + p.Mestiere + ".json"
	}
	return stampaPiano(p, *uscita, *comeJSON)
}

// disinstalla: il piano della disinstallazione, dal registro dell'installazione confermata.
func disinstalla(arg []string) error {
	fs := flag.NewFlagSet("disinstalla", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	uscita := fs.String("uscita", "piano-disinstallazione.json", "dove scrivere il piano")
	purge := fs.Bool("purge", false, "togliere anche la configurazione (come apt purge)")
	comeJSON := fs.Bool("json", false, "stampa anche il piano in JSON")
	if _, err := argomenti(fs, arg); err != nil {
		return err
	}
	cat, err := c.leggiCatalogo()
	if err != nil {
		return err
	}
	amb := motore.AmbienteVero()
	m := &motore.Motore{Amb: amb, Cartella: c.operazioni, Catalogo: cat, Porta: c.porta}
	p, err := m.PianoDisinstallazione(m.Profilo(), *purge)
	if err != nil {
		return err
	}
	return stampaPiano(p, *uscita, *comeJSON)
}

func stampaPiano(p *motore.Piano, uscita string, comeJSON bool) error {
	if err := motore.ScriviJSON(uscita, p); err != nil {
		return err
	}
	if comeJSON {
		stampaJSON(p)
		return nil
	}
	if err := mostraPiano(p, uscita); err != nil {
		return err
	}
	if p.Approvazione != nil { // già approvato (dal file di risposte): si applica così com'è
		fmt.Printf("\n%s\n", T("cli.gia_approvato", p.Approvazione.Modo, uscita))
	} else {
		fmt.Printf("\n%s\n", T("cli.per_applicarlo", uscita, uscita))
	}
	return nil
}

func mostraPiano(p *motore.Piano, uscitaFile string) error {
	uscita := &uscitaFile
	fmt.Println(T("cli.piano_scritto", p.Mestiere, p.ID, *uscita))
	fmt.Printf("%s\n\n", T("cli.piano_macchina", p.Piattaforma, p.Impronta.Digest[:16], len(p.Impronta.Elementi)))
	for i, a := range p.Azioni {
		fmt.Print(T("cli.piano_passo", i+1, a.Descrizione, a.Tipo, a.Reversibilita, a.ComeSiFa, a.ComeSiVerifica, a.ComeSiAnnulla))
	}
	for _, x := range p.Consensi {
		fmt.Printf("\n%s\n", T("cli.consenso", x))
	}
	for _, x := range p.Dichiarate {
		fmt.Printf("\n%s\n", T("cli.dichiarato", x))
	}
	for _, m := range p.NonFatto {
		fmt.Printf("\n%s\n", T("cli.non_fatto", m.Codice, m.Testo, m.Dettaglio))
	}
	return nil
}

func approva(arg []string) error {
	fs := flag.NewFlagSet("approva", flag.ContinueOnError)
	desktop := fs.String("desktop", "", "la risposta alla domanda sul desktop, se il piano la fa")
	fs.String("lingua", "", "it o en (già letta in main)")
	pos, err := argomenti(fs, arg)
	if err != nil {
		return err
	}
	if len(pos) != 1 {
		return errors.New(T("cli.serve_piano", "approva"))
	}
	arg = pos
	var p motore.Piano
	if err := motore.LeggiJSON(arg[0], &p); err != nil {
		return err
	}
	if *desktop != "" {
		if err := p.Rispondi("desktop", *desktop); err != nil {
			return err
		}
	}
	p.Approvazione = &motore.Approvazione{Da: chi(), Ora: time.Now().UTC().Format(time.RFC3339), Modo: "da file (remotix-install approva)", DigestPiano: p.Digest()}
	if err := motore.ScriviJSON(arg[0], &p); err != nil {
		return err
	}
	fmt.Println(T("cli.approvato", p.ID, p.Approvazione.Da, p.Approvazione.DigestPiano[:16]))
	return nil
}

func opera(cmd string, arg []string) (int, error) {
	fs := flag.NewFlagSet(cmd, flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	eventi := fs.Bool("eventi", false, "eventi in JSON, una riga ciascuno")
	approvaOra := fs.Bool("approva", false, "il consenso è dato adesso, da chi lancia il comando")
	pos, err := argomenti(fs, arg)
	if err != nil {
		return 2, err
	}
	// l'archivio del piano: un archivio locale di un pacchetto fuori linea si ritrova da lì
	if cmd == "applica" && len(pos) == 1 && c.archivio == "" {
		var p motore.Piano
		if motore.LeggiJSON(pos[0], &p) == nil && p.Archivio != nil {
			c.archivio, c.canale = p.Archivio.URL, p.Archivio.Canale
			// un archivio locale di un pacchetto fuori linea: si installa da quello (R22)
			if c.fuoriLinea == "" {
				c.fuoriLinea = motore.DaURLArchivio(p.Archivio.URL)
			}
		}
	}
	fl, err := c.leggiFuoriLinea()
	if err != nil {
		return 1, err
	}
	m := &motore.Motore{Amb: motore.AmbienteVero(), Cartella: c.operazioni, Fonti: c.fonti(),
		Porta: c.porta, Ev: &motore.Eventi{W: os.Stdout, JSON: *eventi}}
	if fl != nil {
		if err := m.UsaFuoriLinea(fl); err != nil {
			return 1, err
		}
	}
	if cmd != "applica" {
		// riprendi e annulla non ripassano dalla fase 0: il catalogo per il profilo è quello verificato
		if m.Catalogo, err = c.leggiCatalogo(); err != nil {
			return 1, err
		}
	}
	var op *motore.Operazione
	switch cmd {
	case "applica":
		if len(pos) != 1 {
			return 2, errors.New(T("cli.serve_piano", "applica"))
		}
		op, err = m.Applica(pos[0], *approvaOra, chi())
	case "riprendi":
		op, err = m.Riprendi()
	case "annulla":
		op, err = m.Annulla()
	}
	if op != nil && !*eventi {
		fmt.Printf("\n%s\n  %s\n", T("cli.operazione", op.ID, op.Stato), op.Cartella)
	}
	if err != nil {
		return 1, err
	}
	switch op.Stato {
	case motore.CONFERMATA, motore.CONFERMATA_A_CONDIZIONI:
		if !*eventi && op.Piano != nil && op.Piano.Mestiere == "installazione" {
			fmt.Println(T("cli.router", m.Porta)) // D6
		}
		return 0, nil
	case motore.ANNULLATA:
		if cmd == "annulla" {
			return 0, nil
		}
	}
	return 1, nil
}

func stato(arg []string) error {
	fs := flag.NewFlagSet("stato", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	if _, err := argomenti(fs, arg); err != nil {
		return err
	}
	m := &motore.Motore{Cartella: c.operazioni}
	ops, err := m.Elenco()
	if err != nil {
		return err
	}
	if len(ops) == 0 {
		fmt.Println(T("cli.nessuna_op", c.operazioni))
	}
	for _, op := range ops {
		fin, _ := op.Finita()
		aperta := ""
		if !fin {
			aperta = T("cli.aperta")
		}
		fmt.Printf("%s  %-24s%s\n", op.ID, op.Stato, aperta)
	}
	return nil
}

// aggiornato: chiamato dagli script dei pacchetti remotix e remotix-install a ogni cambio di
// versione (DECISIONI §10.12 punto 4, §10.23): annota le versioni installate, dice se l'installazione
// è certificata e se la macchina ha un motivo BLOCCANTE. ⛔ Non fa mai fallire il gestore di
// pacchetti: dice, e restituisce 0. Il riavvio che non chiude i desktop lo fa lo script del pacchetto
// remotix (try-restart), non il motore.
func aggiornato(arg []string) (int, error) {
	fs := flag.NewFlagSet("aggiornato", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	if _, err := argomenti(fs, arg); err != nil {
		return 0, err
	}
	amb := motore.AmbienteVero()
	m := &motore.Motore{Amb: amb, Cartella: c.operazioni}
	in, err := m.ControllaInstallazione()
	if err != nil {
		// REMOTIX non è installato dall'installatore: niente da annotare (§10.12)
		fmt.Println(err)
		return 0, nil
	}
	fmt.Println(T("cli.certificata", in.Operazione, in.Stato))
	if v, err := m.AnnotaVersioni(); err != nil {
		fmt.Fprintln(os.Stderr, "remotix-install aggiornato:", err)
	} else {
		var r []string
		for _, n := range motore.PacchettiArchivio {
			if v[n] != "" {
				r = append(r, n+" "+v[n])
			}
		}
		fmt.Println(T("cli.versioni_annotate", strings.Join(r, ", ")))
	}
	cat, _, err := c.fidati()
	if err != nil {
		fmt.Fprintln(os.Stderr, "remotix-install aggiornato:", err)
		return 0, nil
	}
	prof := motore.Preflight(amb, motore.OpzioniPreflight{Porta: c.porta, Pacchetti: cat.Componenti()})
	rap := motore.Valuta(cat, prof)
	for _, x := range rap.Messaggi {
		if x.Gravita == motore.BLOCCANTE {
			fmt.Println(motore.Msg("RX-INST-002", x.Codice+" "+x.Testo).Testo, x.Codice)
		}
	}
	return 0, nil
}

func mostraCatalogo(arg []string) error {
	fs := flag.NewFlagSet("catalogo", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	tabella := fs.Bool("tabella", false, "le tabelle di §3.1, in markdown")
	if _, err := argomenti(fs, arg); err != nil {
		return err
	}
	cat, err := c.leggiCatalogo()
	if err != nil {
		return err
	}
	if *tabella {
		fmt.Print(motore.TabellaVersioni(cat))
		return nil
	}
	fmt.Print(T("cli.catalogo_info", cat.Versione, cat.Sequenza, cat.Emesso, cat.MotoreMinimo, cat.Digest, cat.Provenienza))
	return nil
}

// certifica: rifà, in sola lettura, i controlli dell'installazione confermata (§6.6.11, R29):
// VERDE solo se tutto è PASS e non c'è nessuna condizione; uscita 0 solo se VERDE.
func certifica(arg []string) (int, error) {
	fs := flag.NewFlagSet("certifica", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	comeJSON := fs.Bool("json", false, "in JSON")
	if _, err := argomenti(fs, arg); err != nil {
		return 2, err
	}
	cat, err := c.leggiCatalogo()
	if err != nil {
		return 1, err
	}
	m := &motore.Motore{Amb: motore.AmbienteVero(), Cartella: c.operazioni, Catalogo: cat, Porta: c.porta}
	r, err := m.Certifica()
	if err != nil {
		return 1, err
	}
	if *comeJSON {
		stampaJSON(r)
	} else {
		fmt.Println(T("cli.certifica", r.Operazione, r.Esito))
		for _, k := range r.Controlli {
			fmt.Printf("  %-8s %s — %s\n", k.Esito, k.ID, k.Dettaglio)
		}
		for _, k := range r.Condizioni {
			fmt.Printf("  %s %s\n", k.Codice, k.Testo)
		}
	}
	if r.Esito != "VERDE" {
		return 1, nil
	}
	return 0, nil
}

func stampaFiducia(f *motore.Fiducia) {
	fmt.Println(T("cli.fiducia", f.Catalogo.Versione, f.Sequenza, f.Fonte))
	for _, m := range f.Messaggi {
		fmt.Printf("  [%s] %s %s", m.Codice, m.Gravita, m.Testo)
		if m.Dettaglio != "" {
			fmt.Printf(" (%s)", m.Dettaglio)
		}
		fmt.Println()
	}
}
