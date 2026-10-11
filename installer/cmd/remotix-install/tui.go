package main

import (
	"flag"
	"fmt"
	"os"

	"remotix/installer/engine"
	"remotix/installer/ui"
	"remotix/installer/ui/tui"
)

// The interface (T9, phases/17 §6.6.1, DECISIONI §10.31, §10.36):
//
//	remotix-install tui   [--port N]   as root, in the terminal (ssh, console)
//
// The window (GUI) was removed on 10 Oct 2026 (§10.31). The TUI does what `install` does: the
// port, the plan with the exact packages, the «yes», the progress, the welcome.

func tuiCmd(arg []string) (int, error) {
	fs := flag.NewFlagSet("tui", flag.ContinueOnError)
	var c common
	c.add(fs)
	// --preview: the screens with sample data, to compare them with the mockup (design/tui-mockup/);
	// it touches nothing and does not ask for root
	preview := fs.Int("preview", 0, "")
	colors := fs.Bool("preview-color", false, "")
	if _, err := call_args(fs, arg); err != nil {
		return 2, err
	}
	if *preview > 0 {
		fmt.Print(tui.Testo(tui.Previews(*preview, 0, *colors)))
		return 0, nil
	}
	if os.Geteuid() != 0 {
		return 1, engine.Error("RX-UI-006", "uid "+fmt.Sprint(os.Geteuid()))
	}
	if st, err := os.Stdin.Stat(); err != nil || st.Mode()&os.ModeCharDevice == 0 {
		return 1, engine.Error("RX-UI-006", "stdin is not a terminal")
	}
	// an unfinished operation is sorted out first (§10.36: never a half-done system), outside the TUI
	if err := systemOpen(c.engine()); err != nil {
		return 1, err
	}
	s := ui.FreshSession(ui.Config{Operations: c.operations, Fonti: c.sources,
		Base: engine.InstallOptions{Pacchetti: c.packets}, Chi: chi(), Modo: "by hand, in the TUI (remotix-install tui)"})
	return tui.Launch(s, c.port)
}
