package main

import (
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"remotix/installatore/chiavi"
	"remotix/installatore/motore"
)

// installa: l'installazione in un comando (fasi/17 §6.6.12, T9). Con --risposte FILE, SENZA
// DOMANDE: il piano dal file (le risposte e il loro sha256 dentro il piano), scritto in
// /var/lib/remotix/piani/, approvato DAL FILE e applicato; un consenso che manca ⇒ BLOCCATA
// (RX-RISPOSTE-001), niente toccato. Senza --risposte: il piano si mostra e si chiede UNA conferma
// al terminale (senza terminale non si procede: niente «sì» per scelta tacita). Con --fuori-linea
// DIR: tutto dal pacchetto fuori linea, senza rete.
func installa(arg []string) (int, error) {
	fs := flag.NewFlagSet("install", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	uscita := fs.String("output", "", "where to write the plan (default /var/lib/remotix/plans/plan-<id>.json)")
	eventi := fs.Bool("events", false, "events as JSON, one line each")
	utente := fs.String("users", "", "by hand: the people to add to the graphics card groups (empty: all)")
	apri := fs.Bool("open-firewall", false, "by hand: open the port in the firewall")
	depositi := fs.String("extra-repos", "", "by hand: third-party repositories, with consent")
	if _, err := argomenti(fs, arg); err != nil {
		return 2, err
	}
	r, err := c.leggiRisposte()
	if err != nil {
		return 1, err
	}
	fl, err := c.leggiFuoriLinea()
	if err != nil {
		return 1, err
	}
	cat, err := c.leggiCatalogo()
	if err != nil {
		return 1, err
	}
	amb := motore.AmbienteVero()
	prof := motore.Preflight(amb, motore.OpzioniPreflight{Porta: c.porta, Pacchetti: cat.Componenti()})
	rap := motore.Valuta(cat, prof)
	o := c.opzioniInstallazione()
	var p *motore.Piano
	if r != nil {
		if p, err = motore.PianoDaRisposte(r, prof, rap, cat, amb, o); err != nil {
			return 1, err
		}
	} else {
		o.ApriFirewall = *apri
		if *utente != "" {
			o.Utenti = strings.Split(*utente, ",")
		}
		if *depositi != "" {
			o.Depositi = strings.Split(*depositi, ",")
		}
		if p, err = motore.PianoInstallazione(prof, rap, cat, amb, o); err != nil {
			return 1, err
		}
	}
	if *uscita == "" {
		dir := filepath.Join(filepath.Dir(c.operazioni), "plans")
		if err := os.MkdirAll(dir, 0o700); err != nil {
			return 1, err
		}
		*uscita = filepath.Join(dir, "plan-"+p.ID+".json")
	}
	if !*eventi {
		stampaRisposte(p)
		if err := mostraPiano(p, *uscita); err != nil {
			return 1, err
		}
	}
	if r == nil {
		// a mano: una conferma al terminale, per tutto il piano (i consensi sono le sue righe)
		if st, err := os.Stdin.Stat(); err != nil || st.Mode()&os.ModeCharDevice == 0 {
			return 1, errors.New(T("cli.senza_terminale"))
		}
		fmt.Print("\n" + T("cli.conferma"))
		var risposta string
		fmt.Scanln(&risposta)
		switch strings.ToLower(strings.TrimSpace(risposta)) {
		case "yes", "y":
		default:
			fmt.Println(T("cli.non_confermato"))
			return 1, nil
		}
		p.Approvazione = &motore.Approvazione{Da: chi(), Ora: time.Now().UTC().Format(time.RFC3339),
			Modo: "by hand, at the terminal (remotix-install install)", DigestPiano: p.Digest()}
	}
	if err := motore.ScriviJSON(*uscita, p); err != nil {
		return 1, err
	}
	porta := c.porta
	if r != nil && r.Porta() != 0 {
		porta = r.Porta()
	}
	m := &motore.Motore{Amb: amb, Cartella: c.operazioni, Fonti: c.fonti(), Porta: porta, Ev: &motore.Eventi{W: os.Stdout, JSON: *eventi}}
	if fl != nil {
		if err := m.UsaFuoriLinea(fl); err != nil {
			return 1, err
		}
	}
	op, err := m.Applica(*uscita, false, chi())
	if op != nil && !*eventi {
		fmt.Printf("\n%s\n  %s\n", T("cli.operazione", op.ID, op.Stato), op.Cartella)
	}
	if err != nil {
		return 1, err
	}
	if op.Stato == motore.CONFERMATA || op.Stato == motore.CONFERMATA_A_CONDIZIONI {
		if !*eventi {
			fmt.Println(T("cli.router", porta)) // D6: il router non lo tocca nessuno, lo si dice
		}
		return 0, nil
	}
	return 1, nil
}

// preparaFuoriLinea: il pacchetto fuori linea, su una macchina COLLEGATA uguale a quella senza
// rete (R22). I passi di pacchetti vengono dal piano (--piano) o dal file di risposte (--risposte).
func preparaFuoriLinea(arg []string) (int, error) {
	fs := flag.NewFlagSet("prepare-offline", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	uscita := fs.String("output", "", "the bundle directory (new or empty)")
	filePiano := fs.String("plan", "", "the installation plan (its package steps)")
	if _, err := argomenti(fs, arg); err != nil {
		return 2, err
	}
	r, err := c.leggiRisposte()
	if err != nil {
		return 1, err
	}
	if c.archivio == "" || *uscita == "" {
		return 2, errors.New("prepara-fuori-linea --archive URL (--answers FILE | --plan FILE) --output DIR")
	}
	cat, err := c.leggiCatalogo()
	if err != nil {
		return 1, err
	}
	amb := motore.AmbienteVero()
	prof := motore.Preflight(amb, motore.OpzioniPreflight{Porta: c.porta, Pacchetti: cat.Componenti()})
	rap := motore.Valuta(cat, prof)
	var p *motore.Piano
	switch {
	case *filePiano != "":
		p = &motore.Piano{}
		if err := motore.LeggiJSON(*filePiano, p); err != nil {
			return 1, err
		}
	case r != nil:
		if p, err = motore.PianoDaRisposte(r, prof, rap, cat, amb, c.opzioniInstallazione()); err != nil {
			return 1, err
		}
	default:
		if p, err = motore.PianoInstallazione(prof, rap, cat, amb, c.opzioniInstallazione()); err != nil {
			return 1, err
		}
	}
	fl, err := motore.PreparaFuoriLinea(amb, prof, cat, p, motore.OpzioniPrepara{Archivio: c.archivio, Canale: c.canale,
		Uscita: *uscita, ChiaveArchivio: chiavi.Archivio}, func(s string) { fmt.Fprintln(os.Stderr, "  · "+s) })
	if err != nil {
		return 1, err
	}
	var peso int64
	for _, f := range fl.File {
		peso += f.Byte
	}
	fmt.Println(T("cli.preparato", fl.Dir, len(fl.Artefatti), len(fl.File), peso>>20, fl.Impronta.Digest[:16], len(fl.Pacchetti)))
	for _, a := range fl.Artefatti {
		fmt.Printf("  %-40s %-28s %s\n", a.Nome, a.Versione, a.File)
	}
	return 0, nil
}
