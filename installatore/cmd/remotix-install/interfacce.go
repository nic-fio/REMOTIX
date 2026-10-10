package main

import (
	"flag"
	"fmt"
	"os"

	"remotix/installatore/interfaccia"
	"remotix/installatore/interfaccia/tui"
	"remotix/installatore/motore"
)

// L'interfaccia (T9, fasi/17 §6.6.1, DECISIONI §10.14, §10.31):
//
//	remotix-install tui   [--archivio URL] …   da root, nel terminale (ssh, console)
//
// La finestra (GUI) è stata tolta il 10 ott 2026 (DECISIONI §10.31): chi installa un server lo fa
// da un terminale. Restano la riga di comando e la TUI, sullo stesso motore.

// config: le stesse opzioni della riga di comando, per la sessione del motore.
func (c *comuni) config(modo string) interfaccia.Config {
	return interfaccia.Config{Operazioni: c.operazioni, Archivio: c.archivio, Canale: c.canale,
		Fonti: c.fonti, Base: c.opzioniInstallazione(), Chi: chi(), Modo: modo}
}

func tuiCmd(arg []string) (int, error) {
	fs := flag.NewFlagSet("tui", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	if _, err := argomenti(fs, arg); err != nil {
		return 2, err
	}
	if os.Geteuid() != 0 {
		return 1, motore.Errore("RX-UI-006", "uid "+fmt.Sprint(os.Geteuid()))
	}
	if st, err := os.Stdin.Stat(); err != nil || st.Mode()&os.ModeCharDevice == 0 {
		return 1, motore.Errore("RX-UI-006", "stdin non è un terminale")
	}
	s := interfaccia.NuovaSessione(c.config("a mano, nella TUI (remotix-install tui)"))
	return tui.Avvia(s)
}
