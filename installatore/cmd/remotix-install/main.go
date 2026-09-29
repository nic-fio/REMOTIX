// remotix-install: il motore d'installazione di REMOTIX, e la sua riga di comando
// (fasi/17-l-installatore.md §6.0, §6.6). Binario statico: gira da root su ogni distribuzione
// prima che sia installato qualunque pacchetto (fase 0 TRUST), senza Python né librerie.
//
// T4, prima parte: verifica (fasi 1-2, sola lettura), piano (fase 3, un piano di PROVA),
// approva, applica (fasi 4-8 sulle sole azioni di prova), riprendi, annulla, stato.
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
	case "catalogo":
		err = mostraCatalogo(arg)
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
	operazioni, catalogo, lingua string
	porta                        int
}

func (c *comuni) aggiungi(fs *flag.FlagSet) {
	fs.StringVar(&c.operazioni, "operazioni", "/var/lib/remotix/operazioni", "dove stanno le operazioni")
	fs.StringVar(&c.catalogo, "catalogo", "", "un catalogo al posto di quello incorporato")
	fs.IntVar(&c.porta, "porta", 7447, "la porta di REMOTIX (TCP e UDP)")
	fs.StringVar(&c.lingua, "lingua", "", "it o en (già letta in main)")
}

func (c *comuni) leggiCatalogo() (*motore.Catalogo, error) {
	b := catalogo.Incorporato
	if c.catalogo != "" {
		var err error
		if b, err = os.ReadFile(c.catalogo); err != nil {
			return nil, err
		}
	}
	return motore.LeggiCatalogo(b)
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
	cat, err := c.leggiCatalogo()
	if err != nil {
		return 1, err
	}
	amb := motore.AmbienteVero()
	fid, errF := motore.VerificaFiducia(cat, time.Now(), true) // verifica non tocca niente: la firma si dice, non blocca
	prof := motore.Preflight(amb, motore.OpzioniPreflight{Porta: c.porta, Pacchetti: cat.Componenti()})
	rap := motore.Valuta(cat, prof)
	if *comeJSON {
		stampaJSON(map[string]any{"formato": motore.Formato, "fiducia": fid, "profilo": prof, "compatibilita": rap})
	} else {
		stampaRapporto(fid, prof, rap)
	}
	if errF != nil {
		return 1, errF
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
	fmt.Printf("%s\n\n", T("cli.catalogo", r.Catalogo.Versione, r.Catalogo.Scadenza))
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
	pacchetto := fs.String("pacchetto", "", "installazione: il pacchetto di REMOTIX (file .deb/.rpm/.pkg.tar.zst)")
	depositi := fs.String("deposito", "", "installazione: archivi di terzi col consenso (D5), separati da virgola: epel, rpmfusion, packman")
	senzaCinture := fs.Bool("senza-cinture", false, "installazione: senza le tre cinture (D4)")
	nomi := fs.String("pacchetti", "", "prova: pacchetti dai depositi da far installare (separati da virgola)")
	if _, err := argomenti(fs, arg); err != nil {
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
	if *installa {
		o := motore.OpzioniInstallazione{Pacchetto: *pacchetto, ApriFirewall: *apri, SenzaCinture: *senzaCinture, Porta: c.porta}
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
	return mostraPiano(p, uscita)
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
	for _, m := range p.NonFatto {
		fmt.Printf("\n%s\n", T("cli.non_fatto", m.Codice, m.Testo, m.Dettaglio))
	}
	fmt.Printf("\n%s\n", T("cli.per_applicarlo", *uscita, *uscita))
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
	senzaFirma := fs.Bool("senza-firma", false, "procedere anche se la firma del catalogo non si verifica (oggi non esiste: T8)")
	pos, err := argomenti(fs, arg)
	if err != nil {
		return 2, err
	}
	cat, err := c.leggiCatalogo()
	if err != nil {
		return 1, err
	}
	m := &motore.Motore{Amb: motore.AmbienteVero(), Cartella: c.operazioni, Catalogo: cat, SenzaFirma: *senzaFirma,
		Porta: c.porta, Ev: &motore.Eventi{W: os.Stdout, JSON: *eventi}}
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

// aggiornato: chiamato dagli script del pacchetto dopo un aggiornamento (DECISIONI §10.12). ⛔ Non
// fa mai fallire il gestore di pacchetti: dice, e restituisce 0. Riaccende il servizio solo se
// era acceso (try-restart): i desktop sopravvivono al riavvio del servizio (§5.2, T2); la
// configurazione «provata prima» e il ritrovare le sessioni sono T7.
func aggiornato(arg []string) (int, error) {
	fs := flag.NewFlagSet("aggiornato", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	if _, err := argomenti(fs, arg); err != nil {
		return 0, err
	}
	cat, err := c.leggiCatalogo()
	if err != nil {
		fmt.Fprintln(os.Stderr, "remotix-install aggiornato:", err)
		return 0, nil
	}
	m := &motore.Motore{Cartella: c.operazioni, Catalogo: cat}
	if in, err := m.ControllaInstallazione(); err != nil {
		fmt.Println(err)
	} else {
		fmt.Println(T("cli.certificata", in.Operazione, in.Stato))
	}
	amb := motore.AmbienteVero()
	prof := motore.Preflight(amb, motore.OpzioniPreflight{Porta: c.porta, Pacchetti: cat.Componenti()})
	rap := motore.Valuta(cat, prof)
	for _, x := range rap.Messaggi {
		if x.Gravita == motore.BLOCCANTE {
			fmt.Println(motore.Msg("RX-INST-002", x.Codice+" "+x.Testo).Testo, x.Codice)
		}
	}
	if err := amb.Bus.RiavviaSeAttiva("remotix.service"); err != nil {
		fmt.Fprintln(os.Stderr, "remotix-install aggiornato:", T("cli.riaccensione")+":", err)
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
	fmt.Print(T("cli.catalogo_info", cat.Versione, cat.Sequenza, cat.Emesso, cat.Scadenza, cat.MotoreMinimo, cat.Digest, cat.Firma.Nota))
	return nil
}
