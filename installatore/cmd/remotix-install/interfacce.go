package main

import (
	"flag"
	"fmt"
	"os"
	"strings"

	"remotix/installatore/interfaccia"
	"remotix/installatore/interfaccia/tui"
	"remotix/installatore/motore"
)

// Le interfacce (T9, fasi/17 §6.6.1, DECISIONI §10.14, §10.19):
//
//	remotix-install tui   [--archivio URL] …   da root, nel terminale (ssh, console)
//	remotix-install gui   [--archivio URL] …   COME L'UTENTE, nel desktop; il motore da root è lo
//	                                             stesso eseguibile, fatto partire da systemd (D-Bus)
//	                                             col permesso di polkit
//	remotix-install motore-interfaccia …       (interno) la parte da root della finestra: JSON a righe
//
// La finestra c'è solo nella costruzione con l'etichetta «gui» (gui_si.go); quella statica
// risponde RX-UI-001 (gui_no.go).

// config: le stesse opzioni della riga di comando, per la sessione del motore.
func (c *comuni) config(modo string) interfaccia.Config {
	return interfaccia.Config{Operazioni: c.operazioni, Archivio: c.archivio, Canale: c.canale,
		Fonti: c.fonti, Base: c.opzioniInstallazione(), Chi: chi(), Modo: modo}
}

// argomentiRoot: quel che la finestra passa alla parte da root. ⚠ polkit ripulisce l'ambiente: la
// lingua va detta (DECISIONI §10.15).
func (c *comuni) argomentiRoot() []string {
	a := []string{"--lingua", string(motore.LinguaAttuale())}
	if c.archivio != "" {
		a = append(a, "--archivio", c.archivio, "--canale", c.canale)
	}
	if c.catalogo != "" {
		a = append(a, "--catalogo", c.catalogo)
	}
	if c.firmaCatalogo != "" {
		a = append(a, "--firma-catalogo", c.firmaCatalogo)
	}
	if c.operazioni != "/var/lib/remotix/operazioni" {
		a = append(a, "--operazioni", c.operazioni)
	}
	return a
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

// motoreInterfaccia: la parte da root della finestra. Si fida solo di pkexec: chi ha chiesto i
// permessi è PKEXEC_UID; senza, è chi lancia.
func motoreInterfaccia(arg []string) (int, error) {
	fs := flag.NewFlagSet("motore-interfaccia", flag.ContinueOnError)
	var c comuni
	c.aggiungi(fs)
	if _, err := argomenti(fs, arg); err != nil {
		return 2, err
	}
	if os.Geteuid() != 0 {
		return 1, motore.Errore("RX-UI-004", "uid "+fmt.Sprint(os.Geteuid()))
	}
	conf := c.config("a mano, nella finestra (remotix-install gui)")
	// chi ha chiesto i permessi: la finestra lo dice (REMOTIX_UID) — per il registro; il permesso
	// l'ha dato polkit a un amministratore
	for _, v := range []string{"REMOTIX_UID", "PKEXEC_UID"} {
		if u := os.Getenv(v); u != "" {
			conf.Chi = interfaccia.ChiDaUID(u)
			break
		}
	}
	if err := interfaccia.Servi(interfaccia.NuovaSessione(conf), os.Stdin, os.Stdout); err != nil {
		return 1, err
	}
	return 0, nil
}

// clienteFinestra: il motore per la finestra (la parte da root rilanciata con pkexec).
func clienteFinestra(c *comuni) *interfaccia.Cliente {
	cl := &interfaccia.Cliente{Argomenti: c.argomentiRoot()}
	// le prove: un altro modo di prendere i permessi (per esempio «sudo -n»), mai in produzione
	if v := os.Getenv("REMOTIX_GUI_PERMESSI"); v != "" {
		exe, _ := os.Executable()
		cl.Comando = append(strings.Fields(v), exe)
	}
	return cl
}

func guiPreliminari(arg []string) (*comuni, *flag.FlagSet, error) {
	fs := flag.NewFlagSet("gui", flag.ContinueOnError)
	c := &comuni{}
	c.aggiungi(fs)
	return c, fs, nil
}
