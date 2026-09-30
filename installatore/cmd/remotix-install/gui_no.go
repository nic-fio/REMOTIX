//go:build !gui

package main

import "remotix/installatore/motore"

// ConFinestra: la costruzione statica (senza cgo) non ha la GUI: deve partire anche su una
// macchina senza desktop né librerie grafiche (DECISIONI §10.19). Lì si usa la TUI.
const ConFinestra = false

func guiCmd(arg []string) (int, error) {
	return 1, motore.Errore("RX-UI-001", "")
}
