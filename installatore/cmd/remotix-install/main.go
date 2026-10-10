// remotix-install: il motore d'installazione di REMOTIX, e la sua riga di comando
// (fasi/17-l-installatore.md §6.0, §6.6). Binario statico: gira da root su ogni distribuzione
// prima che sia installato qualunque pacchetto (fase 0 TRUST), senza Python né librerie.
//
// Dal 10 ott 2026 (DECISIONI §10.36): cinque comandi — check, install, uninstall, status, tui — e
// REMOTIX che non modifica il sistema (dice cosa manca). Si consegna dentro un file `.run` (il
// pacchetto unico): `sudo sh remotix-<versione>.run` estrae e lancia `install`; dopo, il motore resta
// sulla macchina col pacchetto remotix-install. Aggiornare = rilanciare il .run nuovo.
package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"remotix/installatore/catalogo"
	"remotix/installatore/motore"
)

func main() {
	uso := motore.T("cli.uso", motore.VersioneMotore, motore.Formato)
	if len(os.Args) < 2 {
		fmt.Fprint(os.Stderr, uso)
		os.Exit(2)
	}
	cmd, arg := os.Args[1], os.Args[2:]
	var err error
	codice := 0
	switch cmd {
	case "check":
		codice, err = verifica(arg)
	case "install":
		codice, err = installa(arg)
	case "uninstall":
		codice, err = disinstalla(arg)
	case "status":
		codice, err = stato(arg)
	case "tui":
		codice, err = tuiCmd(arg)
	// nascosti: li usano il comando di rilascio e gli script dei pacchetti
	case "catalog":
		err = mostraCatalogo(arg)
	case "post-upgrade":
		codice, err = aggiornato(arg)
	case "version", "--version":
		fmt.Println(motore.VersioneMotore, motore.Formato)
	case "help", "--help", "-h":
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
	operazioni, catalogo, pacchetti string
	porta                           int
}

func (c *comuni) aggiungi(fs *flag.FlagSet) {
	fs.StringVar(&c.operazioni, "state-dir", "/var/lib/remotix/operations", "where the operations are kept")
	fs.StringVar(&c.catalogo, "catalog", "", "a catalogue given by hand, instead of the engine's (the administrator's responsibility)")
	fs.IntVar(&c.porta, "port", 7447, "the REMOTIX port (TCP and UDP)")
	// la cartella packages/ del .run: la passa il .run stesso
	fs.StringVar(&c.pacchetti, "bundle", "", "the packages folder of the REMOTIX .run file (given by the .run itself)")
}

// fonti: da dove viene il catalogo (fase 0 TRUST): quello del motore, o quello dato a mano.
func (c *comuni) fonti() *motore.FontiFiducia {
	return &motore.FontiFiducia{Incorporato: catalogo.Incorporato, Esplicito: c.catalogo}
}

func (c *comuni) fidati() (*motore.Catalogo, *motore.Fiducia, error) {
	return c.fonti().Fidati(time.Now())
}

// motore: il motore sulla macchina vera, con gli eventi stampati per chi guarda.
func (c *comuni) motore() *motore.Motore {
	return &motore.Motore{Amb: motore.AmbienteVero(), Cartella: c.operazioni, Fonti: c.fonti(),
		Porta: c.porta, Ev: &motore.Eventi{W: os.Stdout}}
}

// argomenti: le opzioni possono stare prima o dopo i nomi.
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

// T: il catalogo dei testi del motore (in inglese, DECISIONI §10.35).
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

func daRoot() error {
	if os.Geteuid() != 0 {
		return fmt.Errorf("%s", T("cli.root"))
	}
	return nil
}

// chiedi: la domanda, dallo stdin (come apt): sì solo con «y» o «yes».
func chiedi(domanda string) bool {
	fmt.Print(domanda + " [y/N] ")
	r, _ := bufio.NewReader(os.Stdin).ReadString('\n')
	r = strings.ToLower(strings.TrimSpace(r))
	return r == "y" || r == "yes"
}

func verifica(arg []string) (int, error) {
	fs := flag.NewFlagSet("check", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	comeJSON := fs.Bool("json", false, "profile and report as JSON")
	if _, err := argomenti(fs, arg); err != nil {
		return 2, err
	}
	cat, fid, errF := c.fidati() // check non scrive niente (R1)
	if errF != nil {
		if *comeJSON {
			stampaJSON(map[string]any{"format": motore.Formato, "trust": fid})
		} else if fid != nil {
			stampaFiducia(fid)
		}
		return 1, errF
	}
	amb := motore.AmbienteVero()
	prof := motore.Preflight(amb, motore.OpzioniPreflight{Porta: c.porta, Pacchetti: cat.Componenti()})
	rap := motore.Valuta(cat, prof)
	if *comeJSON {
		stampaJSON(map[string]any{"format": motore.Formato, "trust": fid, "profile": prof, "compatibility": rap})
	} else {
		stampaRapporto(fid, prof, rap)
	}
	if len(rap.Mancano) > 0 {
		return 1, nil
	}
	for _, e := range rap.Desktop {
		if e.Livello != motore.NON_SUPPORTATA && e.Installato != "absent" && e.Installato != "unknown" && e.Installato != "" {
			return 0, nil
		}
	}
	return 1, nil
}

func stampaRapporto(fid *motore.Fiducia, p *motore.Profilo, r *motore.Rapporto) {
	fmt.Printf("%s\n\n", T("cli.titolo"))
	fmt.Printf("%s: %s — %s\n", T("cli.distribuzione"), r.Piattaforma, r.Riconosciuta)
	fmt.Printf("%s\n\n", T("cli.fiducia", fid.Catalogo.Versione, fid.Sequenza, fid.Fonte))
	fmt.Printf("%s\n", T("cli.desktop"))
	for _, e := range r.Desktop {
		inst := e.Installato
		switch inst {
		case "absent":
			inst = T("cli.non_installato")
		case "unknown":
			inst = T("cli.non_si_sa")
		default:
			inst = T("cli.installato", inst)
		}
		fmt.Printf("  %-11s %-28s %s\n", e.Nome, inst, e.Livello)
		for _, m := range e.Motivi {
			fmt.Printf("      %s: [%s] %s %s\n", T("cli.perche"), m.Codice, m.Testo, m.Dettaglio)
		}
		for _, k := range e.Condizioni {
			fmt.Printf("      %s %s: %s\n", T("cli.condizione"), k.Codice, k.Testo)
		}
		for _, n := range e.Note {
			fmt.Printf("      %s: %s\n", T("cli.nota"), n)
		}
	}
	stampaMancano(r.Mancano)
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

// stampaMancano: quel che manca, e che l'amministratore deve mettere (DECISIONI §10.36).
func stampaMancano(m []motore.Messaggio) {
	if len(m) == 0 {
		return
	}
	fmt.Printf("\n%s\n", T("cli.mancano"))
	for _, x := range m {
		fmt.Printf("  [%s] %s", x.Codice, x.Testo)
		if x.Dettaglio != "" {
			fmt.Printf(" %s", x.Dettaglio)
		}
		fmt.Println()
	}
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

// sistemaAperta: un'operazione non finita (§10.36: mai un sistema a metà). Un'installazione o un
// aggiornamento si ANNULLANO (prima il rimedio del gestore, nel passo dei pacchetti); una
// disinstallazione si porta a termine. Poi chi ha chiamato riparte da capo, col suo piano e la sua
// domanda: nessun ritentare automatico.
func sistemaAperta(m *motore.Motore) error {
	ap, err := m.Aperta()
	if err != nil || ap == nil {
		return err
	}
	var p motore.Piano
	_ = motore.LeggiJSON(filepath.Join(ap.Cartella, "plan.json"), &p)
	var op *motore.Operazione
	if p.Mestiere == "uninstallation" {
		fmt.Println(T("cli.aperta_disinstalla", ap.ID))
		op, err = m.Riprendi()
	} else {
		fmt.Println(T("cli.aperta_annulla", ap.ID))
		op, err = m.Annulla()
	}
	if op != nil {
		fmt.Printf("%s\n\n", T("cli.operazione", op.ID, op.Stato))
	}
	if err != nil {
		return err
	}
	if fin, _ := op.Finita(); !fin {
		return motore.Errore("RX-STATO-001", op.ID+" is "+string(op.Stato))
	}
	return nil
}

// installa: controllo → simulazione del gestore → piano coi pacchetti esatti → «Proceed? [y/N]» →
// esecuzione → verifica → servizio acceso. Su una macchina con REMOTIX già installato è un
// aggiornamento (i pacchetti del .run, e basta).
func installa(arg []string) (int, error) {
	fs := flag.NewFlagSet("install", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	utenti := fs.String("users", "", "the people to add to the graphics card groups, comma separated (empty: everyone on the machine)")
	if _, err := argomenti(fs, arg); err != nil {
		return 2, err
	}
	if err := daRoot(); err != nil {
		return 1, err
	}
	m := c.motore()
	if err := sistemaAperta(m); err != nil {
		return 1, err
	}
	cat, fid, err := c.fidati()
	if err != nil {
		if fid != nil {
			stampaFiducia(fid)
		}
		return 1, err
	}
	m.Catalogo = cat
	prof := m.Profilo()
	rap := motore.Valuta(cat, prof)
	o := motore.OpzioniInstallazione{Pacchetti: c.pacchetti, Porta: c.porta}
	if *utenti != "" {
		o.Utenti = strings.Split(*utenti, ",")
	}
	if in, err := m.ControllaInstallazione(); err == nil && in != nil {
		o.Aggiornamento = true
	}
	p, err := motore.PianoInstallazione(prof, rap, cat, m.Amb, o)
	if err != nil {
		return 1, err
	}
	mostraPiano(p)
	if motore.Bloccato(p) {
		fmt.Printf("\n%s\n", T("cli.bloccato"))
		return 1, nil
	}
	if motore.NienteDaFare(p) {
		fmt.Printf("\n%s\n", T("cli.gia_installato", motore.VersioneMotore))
		return 0, nil
	}
	fmt.Println()
	if !chiedi(T("cli.procedo")) {
		fmt.Println(T("cli.niente_toccato"))
		return 1, nil
	}
	return applica(m, p)
}

// applica: il piano approvato adesso da chi ha risposto «sì», dalla cartella dei piani.
func applica(m *motore.Motore, p *motore.Piano) (int, error) {
	dir := filepath.Join(filepath.Dir(m.Cartella), "plans")
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return 1, err
	}
	file := filepath.Join(dir, p.ID+".json")
	if err := motore.ScriviJSON(file, p); err != nil {
		return 1, err
	}
	op, err := m.Applica(file, true, chi())
	if op != nil {
		fmt.Printf("\n%s\n  %s\n", T("cli.operazione", op.ID, op.Stato), op.Cartella)
	}
	if err != nil {
		return 1, err
	}
	switch op.Stato {
	case motore.CONFERMATA, motore.CONFERMATA_A_CONDIZIONI:
		if p.Mestiere == "installation" {
			fmt.Println(T("cli.router", m.Porta))
		}
		return 0, nil
	}
	return 1, nil
}

func mostraPiano(p *motore.Piano) {
	fmt.Println(T("cli.piano", p.Mestiere, p.Piattaforma))
	for i, a := range p.Azioni {
		fmt.Printf("  %d. %s  [%s]\n", i+1, a.Descrizione, a.Reversibilita)
	}
	if len(p.Pacchetti) > 0 {
		fmt.Printf("\n%s\n", T("cli.pacchetti"))
		for _, a := range p.Pacchetti {
			esito := a.Esito
			if a.Prima != "" {
				esito += " (" + a.Prima + ")"
			}
			fmt.Printf("  %-36s %-28s %-10s %s\n", a.Nome, a.Versione, esito, a.Origine)
		}
	}
	for _, x := range p.Dichiarate {
		fmt.Printf("\n%s\n", T("cli.dichiarato", x))
	}
	for _, k := range p.Condizioni {
		fmt.Printf("\n%s %s: %s\n", T("cli.condizione"), k.Codice, k.Testo)
	}
	var mancano []motore.Messaggio
	for _, m := range p.NonFatto {
		if m.Gravita == motore.BLOCCANTE {
			mancano = append(mancano, m)
		} else {
			fmt.Printf("\n%s\n", T("cli.non_fatto", m.Codice, m.Testo, m.Dettaglio))
		}
	}
	stampaMancano(mancano)
}

// disinstalla: il piano della disinstallazione dal registro dell'installazione confermata, la
// domanda, e via. Una disinstallazione interrotta si porta a termine; un'installazione interrotta si
// annulla (e quello è già togliere REMOTIX).
func disinstalla(arg []string) (int, error) {
	fs := flag.NewFlagSet("uninstall", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	purge := fs.Bool("purge", false, "also remove the configuration (like apt purge)")
	if _, err := argomenti(fs, arg); err != nil {
		return 2, err
	}
	if err := daRoot(); err != nil {
		return 1, err
	}
	m := c.motore()
	if ap, err := m.Aperta(); err != nil {
		return 1, err
	} else if ap != nil {
		return 0, sistemaAperta(m)
	}
	cat, _, err := c.fidati()
	if err != nil {
		return 1, err
	}
	m.Catalogo = cat
	p, err := m.PianoDisinstallazione(m.Profilo(), *purge)
	if err != nil {
		return 1, err
	}
	mostraPiano(p)
	fmt.Println()
	if !chiedi(T("cli.procedo_togli")) {
		fmt.Println(T("cli.niente_toccato"))
		return 1, nil
	}
	return applica(m, p)
}

// stato: le operazioni, e — se REMOTIX è installato — i controlli di allora rifatti adesso (§6.6.11,
// R29): GREEN solo se tutto è PASS e non c'è nessuna condizione; uscita 0 solo se GREEN.
func stato(arg []string) (int, error) {
	fs := flag.NewFlagSet("status", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	comeJSON := fs.Bool("json", false, "the certification as JSON")
	if _, err := argomenti(fs, arg); err != nil {
		return 2, err
	}
	m := &motore.Motore{Amb: motore.AmbienteVero(), Cartella: c.operazioni, Porta: c.porta}
	if !*comeJSON {
		ops, err := m.Elenco()
		if err != nil {
			return 1, err
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
	}
	if _, err := m.ControllaInstallazione(); err != nil {
		if !*comeJSON {
			fmt.Printf("\n%s\n", T("cli.non_installato_ora"))
		}
		return 1, nil
	}
	cat, _, err := c.fidati()
	if err != nil {
		return 1, err
	}
	m.Catalogo = cat
	r, err := m.Certifica()
	if err != nil {
		return 1, err
	}
	if *comeJSON {
		stampaJSON(r)
	} else {
		fmt.Printf("\n%s\n", T("cli.certifica", r.Operazione, r.Esito))
		for _, k := range r.Controlli {
			fmt.Printf("  %-8s %s — %s\n", k.Esito, k.ID, k.Dettaglio)
		}
		for _, k := range r.Condizioni {
			fmt.Printf("  %s %s\n", k.Codice, k.Testo)
		}
	}
	if r.Esito != "GREEN" {
		return 1, nil
	}
	return 0, nil
}

// aggiornato: chiamato dagli script dei pacchetti remotix e remotix-install a ogni cambio di
// versione: annota le versioni installate, dice se l'installazione è certificata e se la macchina
// ha un motivo BLOCCANTE. ⛔ Non fa mai fallire il gestore di pacchetti: dice, e restituisce 0. Il
// riavvio che non chiude i desktop lo fa lo script del pacchetto remotix (try-restart).
func aggiornato(arg []string) (int, error) {
	fs := flag.NewFlagSet("post-upgrade", flag.ContinueOnError)
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
		fmt.Fprintln(os.Stderr, "remotix-install post-upgrade:", err)
	} else {
		var r []string
		for _, n := range motore.PacchettiRemotix {
			if v[n] != "" {
				r = append(r, n+" "+v[n])
			}
		}
		fmt.Println(T("cli.versioni_annotate", strings.Join(r, ", ")))
	}
	cat, _, err := c.fidati()
	if err != nil {
		fmt.Fprintln(os.Stderr, "remotix-install post-upgrade:", err)
		return 0, nil
	}
	prof := motore.Preflight(amb, motore.OpzioniPreflight{Porta: c.porta, Pacchetti: cat.Componenti()})
	rap := motore.Valuta(cat, prof)
	for _, x := range append(rap.Messaggi, rap.Mancano...) {
		if x.Gravita == motore.BLOCCANTE {
			fmt.Println(motore.Msg("RX-INST-002", x.Codice+" "+x.Testo).Testo, x.Codice)
		}
	}
	return 0, nil
}

func mostraCatalogo(arg []string) error {
	fs := flag.NewFlagSet("catalog", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	tabella := fs.Bool("table", false, "the supported-versions tables, in markdown")
	if _, err := argomenti(fs, arg); err != nil {
		return err
	}
	cat, _, err := c.fidati()
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
