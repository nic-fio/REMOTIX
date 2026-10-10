package main

import (
	"flag"
	"fmt"
	"os"

	"remotix/installatore/interfaccia"
	"remotix/installatore/interfaccia/tui"
	"remotix/installatore/motore"
)

// L'interfaccia (T9, fasi/17 §6.6.1, DECISIONI §10.31, §10.36):
//
//	remotix-install tui   [--port N]   da root, nel terminale (ssh, console)
//
// La finestra (GUI) è stata tolta il 10 ott 2026 (§10.31). La TUI fa quel che fa `install`: la
// porta, il piano coi pacchetti esatti, il «sì», l'avanzamento, il benvenuto.

func tuiCmd(arg []string) (int, error) {
	fs := flag.NewFlagSet("tui", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	// --preview: le schermate con dati d'esempio, per confrontarle col mockup (grafica/tui-mockup/);
	// non tocca niente e non chiede root
	anteprima := fs.Int("preview", 0, "")
	colori := fs.Bool("preview-color", false, "")
	if _, err := argomenti(fs, arg); err != nil {
		return 2, err
	}
	if *anteprima > 0 {
		fmt.Print(tui.Testo(tui.Anteprime(*anteprima, 0, *colori)))
		return 0, nil
	}
	if os.Geteuid() != 0 {
		return 1, motore.Errore("RX-UI-006", "uid "+fmt.Sprint(os.Geteuid()))
	}
	if st, err := os.Stdin.Stat(); err != nil || st.Mode()&os.ModeCharDevice == 0 {
		return 1, motore.Errore("RX-UI-006", "stdin is not a terminal")
	}
	// un'operazione non finita si sistema prima (§10.36: mai un sistema a metà), fuori dalla TUI
	if err := sistemaAperta(c.motore()); err != nil {
		return 1, err
	}
	s := interfaccia.NuovaSessione(interfaccia.Config{Operazioni: c.operazioni, Fonti: c.fonti,
		Base: motore.OpzioniInstallazione{Pacchetti: c.pacchetti}, Chi: chi(), Modo: "by hand, in the TUI (remotix-install tui)"})
	return tui.Avvia(s)
}
