//go:build gui

package main

import (
	"os"

	"remotix/installatore/interfaccia/gui"
	"remotix/installatore/motore"
)

// ConFinestra: questa costruzione ha la GUI (etichetta «gui», cgo, librerie grafiche del sistema).
const ConFinestra = true

func guiCmd(arg []string) (int, error) {
	c, fs, _ := guiPreliminari(arg)
	anteprima := fs.String("anteprima", "", "disegna le schermate fuori schermo in PNG in questa cartella (niente finestra, niente motore)")
	dati := fs.String("dati", "", "con --anteprima: la cartella con verifica.json e piano.json di una macchina")
	scala := fs.Float64("scala", 1, "con --anteprima: 1 = 1120×760, 2 = il doppio")
	if _, err := argomenti(fs, arg); err != nil {
		return 2, err
	}
	if *anteprima != "" {
		if err := gui.Anteprima(*anteprima, *dati, float32(*scala)); err != nil {
			return 1, err
		}
		return 0, nil
	}
	// R37: la finestra non gira da root
	if os.Geteuid() == 0 {
		return 1, motore.Errore("RX-UI-003", "")
	}
	if os.Getenv("WAYLAND_DISPLAY") == "" && os.Getenv("DISPLAY") == "" {
		return 1, motore.Errore("RX-UI-002", "")
	}
	if err := gui.Avvia(clienteFinestra(c)); err != nil {
		return 1, motore.Errore("RX-UI-002", err.Error())
	}
	return 0, nil
}
