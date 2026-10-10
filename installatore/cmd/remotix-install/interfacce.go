package main

import (
	"flag"
	"fmt"
	"os"

	"remotix/installatore/interfaccia"
	"remotix/installatore/interfaccia/tui"
	"remotix/installatore/motore"
)

// The interface (T9, fasi/17 §6.6.1, DECISIONI §10.31, §10.36):
//
//	remotix-install tui   [--port N]   as root, in the terminal (ssh, console)
//
// The window (GUI) was removed on 10 Oct 2026 (§10.31). The TUI does what `install` does: the
// port, the plan with the exact packages, the «yes», the progress, the welcome.

func tuiCmd(arg []string) (int, error) {
	fs := flag.NewFlagSet("tui", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	// --preview: the screens with sample data, to compare them with the mockup (grafica/tui-mockup/);
	// it touches nothing and does not ask for root
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
	// an unfinished operation is sorted out first (§10.36: never a half-done system), outside the TUI
	if err := sistemaAperta(c.motore()); err != nil {
		return 1, err
	}
	s := interfaccia.NuovaSessione(interfaccia.Config{Operazioni: c.operazioni, Fonti: c.fonti,
		Base: motore.OpzioniInstallazione{Pacchetti: c.pacchetti}, Chi: chi(), Modo: "by hand, in the TUI (remotix-install tui)"})
	return tui.Avvia(s)
}
