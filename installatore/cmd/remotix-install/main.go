// remotix-install: REMOTIX's installation engine, and its command line
// (fasi/17-l-installatore.md §6.0, §6.6). Static binary: it runs as root on every distribution
// before any package is installed (phase 0 TRUST), without Python or libraries.
//
// Since 10 Oct 2026 (DECISIONI §10.36): five commands — check, install, uninstall, status, tui — and
// REMOTIX that does not modify the system (it says what is missing). It is delivered inside a `.run` file (the
// single package): `sudo sh remotix-<version_v>.run` extracts and launches `install`; afterwards, the engine stays
// on the machine with the remotix-install package. Upgrading = relaunching the new .run.
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
	use := motore.T("cli.use", motore.EngineVersion, motore.Schema)
	if len(os.Args) < 2 {
		fmt.Fprint(os.Stderr, use)
		os.Exit(2)
	}
	cmd, arg := os.Args[1], os.Args[2:]
	var err error
	code_v := 0
	switch cmd {
	case "check":
		code_v, err = verify(arg)
	case "install":
		code_v, err = install(arg)
	case "uninstall":
		code_v, err = uninstall(arg)
	case "status":
		code_v, err = state(arg)
	case "tui":
		code_v, err = tuiCmd(arg)
	// hidden: used by the release command and by the packages' scripts
	case "catalog":
		err = showCatalog(arg)
	case "post-upgrade":
		code_v, err = updated(arg)
	case "version", "--version":
		fmt.Println(motore.EngineVersion, motore.Schema)
	case "help", "--help", "-h":
		fmt.Print(use)
	default:
		fmt.Fprint(os.Stderr, use)
		os.Exit(2)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "remotix-install:", err)
		if code_v == 0 {
			code_v = 1
		}
	}
	os.Exit(code_v)
}

// common: the options of all the commands.
type common struct {
	operations, catalogo, packets string
	port                          int
}

func (c *common) insert(fs *flag.FlagSet) {
	fs.StringVar(&c.operations, "state-dir", "/var/lib/remotix/operations", "where the operations are kept")
	fs.StringVar(&c.catalogo, "catalog", "", "a catalogue given by hand, instead of the engine's (the administrator's responsibility)")
	fs.IntVar(&c.port, "port", 7447, "the REMOTIX port (TCP and UDP)")
	// the packages/ folder of the .run: the .run itself passes it
	fs.StringVar(&c.packets, "bundle", "", "the packages folder of the REMOTIX .run file (given by the .run itself)")
}

// sources: where the catalogue comes from (phase 0 TRUST): the engine's, or the one given by hand.
func (c *common) sources() *motore.TrustSources {
	return &motore.TrustSources{Embedded: catalogo.Embedded, Explicit: c.catalogo}
}

func (c *common) trusted() (*motore.Catalog, *motore.Attestation, error) {
	return c.sources().Trusted(time.Now())
}

// motore: the engine on the real machine, with the events printed for whoever is watching.
// Before an operation is open (the plan's simulation) the engine's waits are printed too.
func (c *common) motore() *motore.Engine {
	m := &motore.Engine{Amb: motore.RealEnvironment(), Folder: c.operations, Sources: c.sources(),
		Port: c.port, Ev: &motore.Events{W: os.Stdout}}
	m.Amb.Avvisa = func(x motore.Message) { m.Ev.Message("", x) }
	return m
}

// call_args: the options can come before or after the names.
func call_args(fs *flag.FlagSet, arg []string) ([]string, error) {
	var positional []string
	for {
		if err := fs.Parse(arg); err != nil {
			return nil, err
		}
		if fs.NArg() == 0 {
			return positional, nil
		}
		positional = append(positional, fs.Arg(0))
		arg = fs.Args()[1:]
	}
}

// T: the catalogue of the engine's texts (in English, DECISIONI §10.35).
var T = motore.T

func chi() string {
	for _, v := range []string{"SUDO_USER", "USER", "LOGNAME"} {
		if s := os.Getenv(v); s != "" {
			return s
		}
	}
	return fmt.Sprintf("uid %d", os.Getuid())
}

func printJSON(v any) {
	b, _ := json.MarshalIndent(v, "", "  ")
	fmt.Println(string(b))
}

func daRoot() error {
	if os.Geteuid() != 0 {
		return fmt.Errorf("%s", T("cli.root"))
	}
	return nil
}

// ask: the question, from stdin (like apt): yes only with «y» or «yes».
func ask(question string) bool {
	fmt.Print(question + " [y/N] ")
	r, _ := bufio.NewReader(os.Stdin).ReadString('\n')
	r = strings.ToLower(strings.TrimSpace(r))
	return r == "y" || r == "yes"
}

func verify(arg []string) (int, error) {
	fs := flag.NewFlagSet("check", flag.ContinueOnError)
	var c common
	c.insert(fs)
	comeJSON := fs.Bool("json", false, "profile and report as JSON")
	if _, err := call_args(fs, arg); err != nil {
		return 2, err
	}
	cat, fid, errF := c.trusted() // check writes nothing (R1)
	if errF != nil {
		if *comeJSON {
			printJSON(map[string]any{"format": motore.Schema, "trust": fid})
		} else if fid != nil {
			printTrust(fid)
		}
		return 1, errF
	}
	amb := motore.RealEnvironment()
	prof := motore.Preflight(amb, motore.PreflightOptions{Port: c.port, Packets: cat.Components()})
	rap := motore.Evaluate(cat, prof)
	if *comeJSON {
		printJSON(map[string]any{"format": motore.Schema, "trust": fid, "profile": prof, "compatibility": rap})
	} else {
		printReport(fid, prof, rap)
	}
	if len(rap.Missing) > 0 {
		return 1, nil
	}
	for _, e := range rap.Desktop {
		if e.Level != motore.NOT_SUPPORTED && e.Installed != "absent" && e.Installed != "unknown" && e.Installed != "" {
			return 0, nil
		}
	}
	return 1, nil
}

func printReport(fid *motore.Attestation, p *motore.Profile, r *motore.Report) {
	fmt.Printf("%s\n\n", T("cli.heading"))
	fmt.Printf("%s: %s — %s\n", T("cli.distrib"), r.Platform, r.Recognized)
	fmt.Printf("%s\n\n", T("cli.attestation", fid.Catalog.Version, fid.Sequence, fid.Source))
	fmt.Printf("%s\n", T("cli.desktop"))
	for _, e := range r.Desktop {
		inst := e.Installed
		switch inst {
		case "absent":
			inst = T("cli.non_installato")
		case "unknown":
			inst = T("cli.non_si_sa")
		default:
			inst = T("cli.installed", inst)
		}
		fmt.Printf("  %-11s %-28s %s\n", e.Name, inst, e.Level)
		for _, m := range e.Reasons {
			fmt.Printf("      %s: [%s] %s %s\n", T("cli.reason_text"), m.Code, m.Text, m.Detail)
		}
		for _, k := range e.Conditions {
			fmt.Printf("      %s %s: %s\n", T("cli.condizione"), k.Code, k.Text)
		}
		for _, n := range e.Note {
			fmt.Printf("      %s: %s\n", T("cli.remark"), n)
		}
	}
	printMissing(r.Missing)
	if len(r.Unknowns) > 0 {
		fmt.Printf("\n%s\n", T("cli.incognite"))
		for _, x := range r.Unknowns {
			fmt.Printf("  - %s\n", x)
		}
	}
	fmt.Printf("\n%s\n", T("cli.warnings"))
	msgs := append(append([]motore.Message{}, fid.Messages...), p.Messages...)
	sort.SliceStable(msgs, func(i, j int) bool { return weight(msgs[i].Severity) > weight(msgs[j].Severity) })
	for _, m := range msgs {
		fmt.Printf("  [%s] %-9s %s", m.Code, m.Severity, m.Text)
		if m.Detail != "" {
			fmt.Printf(" (%s)", m.Detail)
		}
		fmt.Println()
		if m.Remediation != "" {
			fmt.Printf("                  %s: %s\n", T("ev.remediation"), m.Remediation)
		}
	}
	fmt.Printf("\n%s\n", T("cli.done_ones"))
	for _, f := range p.Facts {
		v := f.Value
		if f.State == motore.UNKNOWN {
			v = "?"
		}
		fmt.Printf("  %-34s %-40s %-11s %s\n", f.Key, truncate(v, 40), f.State, truncate(strings.TrimSpace(f.Source+" "+f.Note), 70))
	}
	for _, n := range r.Note {
		fmt.Printf("\n%s: %s", T("cli.remark"), n)
	}
	fmt.Println()
}

// printMissing: what is missing, and what the administrator must provide (DECISIONI §10.36).
func printMissing(m []motore.Message) {
	if len(m) == 0 {
		return
	}
	fmt.Printf("\n%s\n", T("cli.missing"))
	for _, x := range m {
		fmt.Printf("  [%s] %s", x.Code, x.Text)
		if x.Detail != "" {
			fmt.Printf(" %s", x.Detail)
		}
		fmt.Println()
	}
}

func weight(g motore.Severity) int {
	switch g {
	case motore.BLOCKING:
		return 2
	case motore.WARNING:
		return 1
	}
	return 0
}

func truncate(s string, n int) string {
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n-1]) + "…"
}

// systemOpen: an unfinished operation (§10.36: never a half-done system). An installation or an
// upgrade is CANCELLED (first the manager's remedy, in the packages step); an
// uninstallation is carried through. Then the caller starts over, with its plan and its
// question: no automatic retry.
func systemOpen(m *motore.Engine) error {
	ap, err := m.Open()
	if err != nil || ap == nil {
		return err
	}
	var p motore.Piano
	_ = motore.ReadJSON(filepath.Join(ap.Folder, "plan.json"), &p)
	var op *motore.Operation
	if p.Duty == "uninstallation" {
		fmt.Println(T("cli.aperta_disinstalla", ap.ID))
		op, err = m.Resume()
	} else {
		fmt.Println(T("cli.aperta_annulla", ap.ID))
		op, err = m.Rollback()
	}
	if op != nil {
		fmt.Printf("%s\n\n", T("cli.operazione", op.ID, op.State))
	}
	if err != nil {
		return err
	}
	if fin, _ := op.Ended(); !fin {
		return motore.Error("RX-STATO-001", op.ID+" is "+string(op.State))
	}
	return nil
}

// install: check → manager's simulation → plan with the exact packages → «Proceed? [y/N]» →
// execution → verification → service started. On a machine with REMOTIX already installed it is an
// upgrade (the .run's packages, and nothing else).
func install(arg []string) (int, error) {
	fs := flag.NewFlagSet("install", flag.ContinueOnError)
	var c common
	c.insert(fs)
	users := fs.String("users", "", "the people to add to the graphics card groups, comma separated (empty: everyone on the machine)")
	if _, err := call_args(fs, arg); err != nil {
		return 2, err
	}
	if err := daRoot(); err != nil {
		return 1, err
	}
	m := c.motore()
	if err := systemOpen(m); err != nil {
		return 1, err
	}
	cat, fid, err := c.trusted()
	if err != nil {
		if fid != nil {
			printTrust(fid)
		}
		return 1, err
	}
	m.Catalog = cat
	prof := m.Profile()
	rap := motore.Evaluate(cat, prof)
	o := motore.InstallOptions{Packets: c.packets, Port: c.port}
	if *users != "" {
		o.Users = strings.Split(*users, ",")
	}
	if in, err := m.CheckInstallation(); err == nil && in != nil {
		o.Update = true
	}
	p, err := motore.PlanInstallation(prof, rap, cat, m.Amb, o)
	if err != nil {
		return 1, err
	}
	showPlan(p)
	if motore.Blocked(p) {
		fmt.Printf("\n%s\n", T("cli.blocked"))
		return 1, nil
	}
	if motore.NothingToDo(p) {
		fmt.Printf("\n%s\n", T("cli.gia_installato", motore.EngineVersion))
		return 0, nil
	}
	fmt.Println()
	if !ask(T("cli.procedo")) {
		fmt.Println(T("cli.niente_toccato"))
		return 1, nil
	}
	return apply(m, p)
}

// apply: the plan approved now by whoever answered «yes», from the plans folder.
func apply(m *motore.Engine, p *motore.Piano) (int, error) {
	dir := filepath.Join(filepath.Dir(m.Folder), motore.PlansFolder)
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return 1, err
	}
	file := filepath.Join(dir, p.ID+".json")
	if err := motore.WriteJSON(file, p); err != nil {
		return 1, err
	}
	op, err := m.Apply(file, true, chi())
	if op != nil {
		fmt.Printf("\n%s\n  %s\n", T("cli.operazione", op.ID, op.State), op.Folder)
	}
	if err != nil {
		return 1, err
	}
	switch op.State {
	case motore.CONFIRMED, motore.CONFIRMED_WITH_CONDITIONS:
		if p.Duty == "installation" {
			fmt.Println(T("cli.router", m.Port))
		}
		return 0, nil
	}
	return 1, nil
}

func showPlan(p *motore.Piano) {
	fmt.Println(T("cli.piano", p.Duty, p.Platform))
	for i, a := range p.Actions {
		fmt.Printf("  %d. %s  [%s]\n", i+1, a.Description, a.Reversibility)
	}
	if len(p.Packets) > 0 {
		fmt.Printf("\n%s\n", T("cli.packets"))
		for _, a := range p.Packets {
			outcome := a.Outcome
			if a.Before != "" {
				outcome += " (" + a.Before + ")"
			}
			fmt.Printf("  %-36s %-28s %-10s %s\n", a.Name, a.Version, outcome, a.Origin)
		}
	}
	for _, x := range p.Declared {
		fmt.Printf("\n%s\n", T("cli.claimed", x))
	}
	for _, k := range p.Conditions {
		fmt.Printf("\n%s %s: %s\n", T("cli.condizione"), k.Code, k.Text)
	}
	var missing []motore.Message
	for _, m := range p.NotDone {
		if m.Severity == motore.BLOCKING {
			missing = append(missing, m)
		} else {
			fmt.Printf("\n%s\n", T("cli.non_fatto", m.Code, m.Text, m.Detail))
		}
	}
	printMissing(missing)
}

// uninstall: the uninstallation plan from the log of the confirmed installation, the
// question, and off it goes. An interrupted uninstallation is carried through; an interrupted installation is
// cancelled (and that already removes REMOTIX).
func uninstall(arg []string) (int, error) {
	fs := flag.NewFlagSet("uninstall", flag.ContinueOnError)
	var c common
	c.insert(fs)
	purge := fs.Bool("purge", false, "also remove the configuration (like apt purge)")
	if _, err := call_args(fs, arg); err != nil {
		return 2, err
	}
	if err := daRoot(); err != nil {
		return 1, err
	}
	m := c.motore()
	if ap, err := m.Open(); err != nil {
		return 1, err
	} else if ap != nil {
		return 0, systemOpen(m)
	}
	cat, _, err := c.trusted()
	if err != nil {
		return 1, err
	}
	m.Catalog = cat
	p, err := m.UninstallPlan(m.Profile(), *purge)
	if err != nil {
		return 1, err
	}
	showPlan(p)
	fmt.Println()
	if !ask(T("cli.procedo_togli")) {
		fmt.Println(T("cli.niente_toccato"))
		return 1, nil
	}
	return apply(m, p)
}

// state: the operations, and — if REMOTIX is installed — the checks of then redone now (§6.6.11,
// R29): GREEN only if everything is PASS and there is no condition; exit 0 only if GREEN.
func state(arg []string) (int, error) {
	fs := flag.NewFlagSet("status", flag.ContinueOnError)
	var c common
	c.insert(fs)
	comeJSON := fs.Bool("json", false, "the certification as JSON")
	if _, err := call_args(fs, arg); err != nil {
		return 2, err
	}
	m := &motore.Engine{Amb: motore.RealEnvironment(), Folder: c.operations, Port: c.port}
	if !*comeJSON {
		ops, err := m.List()
		if err != nil {
			return 1, err
		}
		if len(ops) == 0 {
			fmt.Println(T("cli.nessuna_op", c.operations))
		}
		for _, op := range ops {
			fin, _ := op.Ended()
			is_open := ""
			if !fin {
				is_open = T("cli.is_open")
			}
			fmt.Printf("%s  %-24s%s\n", op.ID, op.State, is_open)
		}
	}
	if _, err := m.CheckInstallation(); err != nil {
		if !*comeJSON {
			fmt.Printf("\n%s\n", T("cli.non_installato_ora"))
		}
		return 1, nil
	}
	cat, _, err := c.trusted()
	if err != nil {
		return 1, err
	}
	m.Catalog = cat
	r, err := m.Certify()
	if err != nil {
		return 1, err
	}
	if *comeJSON {
		printJSON(r)
	} else {
		fmt.Printf("\n%s\n", T("cli.certify", r.Operation, r.Outcome))
		for _, k := range r.Checks {
			fmt.Printf("  %-8s %s — %s\n", k.Outcome, k.ID, k.Detail)
		}
		for _, k := range r.Conditions {
			fmt.Printf("  %s %s\n", k.Code, k.Text)
		}
	}
	if r.Outcome != "GREEN" {
		return 1, nil
	}
	return 0, nil
}

// updated: called by the scripts of the remotix and remotix-install packages at every version
// change: records the installed versions, says whether the installation is certified and whether the machine
// has a BLOCKING reason. ⛔ It never makes the package manager fail: it says, and returns 0. The
// restart that does not close the desktops is done by the remotix package's script (try-restart).
func updated(arg []string) (int, error) {
	fs := flag.NewFlagSet("post-upgrade", flag.ContinueOnError)
	var c common
	c.insert(fs)
	if _, err := call_args(fs, arg); err != nil {
		return 0, err
	}
	amb := motore.RealEnvironment()
	m := &motore.Engine{Amb: amb, Folder: c.operations}
	in, err := m.CheckInstallation()
	if err != nil {
		// REMOTIX was not installed by the installer: nothing to record (§10.12)
		fmt.Println(err)
		return 0, nil
	}
	fmt.Println(T("cli.certificata", in.Operation, in.State))
	if v, err := m.AnnotateVersions(); err != nil {
		fmt.Fprintln(os.Stderr, "remotix-install post-upgrade:", err)
	} else {
		var r []string
		for _, n := range motore.RemotixPackages {
			if v[n] != "" {
				r = append(r, n+" "+v[n])
			}
		}
		fmt.Println(T("cli.versioni_annotate", strings.Join(r, ", ")))
	}
	cat, _, err := c.trusted()
	if err != nil {
		fmt.Fprintln(os.Stderr, "remotix-install post-upgrade:", err)
		return 0, nil
	}
	prof := motore.Preflight(amb, motore.PreflightOptions{Port: c.port, Packets: cat.Components()})
	rap := motore.Evaluate(cat, prof)
	for _, x := range append(rap.Messages, rap.Missing...) {
		if x.Severity == motore.BLOCKING {
			fmt.Println(motore.Msg("RX-INST-002", x.Code+" "+x.Text).Text, x.Code)
		}
	}
	return 0, nil
}

func showCatalog(arg []string) error {
	fs := flag.NewFlagSet("catalog", flag.ContinueOnError)
	var c common
	c.insert(fs)
	table := fs.Bool("table", false, "the supported-versions tables, in markdown")
	if _, err := call_args(fs, arg); err != nil {
		return err
	}
	cat, _, err := c.trusted()
	if err != nil {
		return err
	}
	if *table {
		fmt.Print(motore.VersionTable(cat))
		return nil
	}
	fmt.Print(T("cli.catalogo_info", cat.Version, cat.Sequence, cat.Emitted, cat.EngineMinimum, cat.Digest, cat.Provenance))
	return nil
}

func printTrust(f *motore.Attestation) {
	fmt.Println(T("cli.attestation", f.Catalog.Version, f.Sequence, f.Source))
	for _, m := range f.Messages {
		fmt.Printf("  [%s] %s %s", m.Code, m.Severity, m.Text)
		if m.Detail != "" {
			fmt.Printf(" (%s)", m.Detail)
		}
		fmt.Println()
	}
}
