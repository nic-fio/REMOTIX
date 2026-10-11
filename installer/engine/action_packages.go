package engine

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// installa-pacchetti: the package manager's transaction (§6.0 rule 1, §6.6.6; since 10 Oct
// 2026 without caches or sha256 of our own: «don't reinvent the wheel», DECISIONI §10.36).
//
//   - Snapshot (before the intention): the manager SIMULATES the transaction; the set (name, version,
//     origin, new/upgraded) goes into the log's intention and into resolved-set-<step>.json.
//   - Do: the manager installs — the files of the single package, with the dependencies from the
//     machine's repositories, downloaded and verified by it.
//   - Check: every package at the simulated version (or newer) ⇒ complete; none of the new ones ⇒
//     absent; otherwise (or the manager halfway through a transaction) ⇒ half-done.
//   - Repair: the manager's remedy (dpkg --configure -a…), needed before undoing.
//   - Rollback: the NEW packages are removed, and only those (the manager simulates first: if it
//     would remove others, it holds them back); the UPGRADED ones stay upgraded and are declared
//     (INDIRECT, §6.6.4). Reversibility BEST_EFFORT.
//
// parameters: file (paths of the .run's packages, comma-separated: a single transaction),
// names (comma-separated, from the machine's repositories).

func init() { registerType("install-packages", newPackages) }

// PlanPackages prepares the plan's step.
func PlanPackages(id, file, names string) PlanAction {
	var bases []string
	for _, f := range splitCommas(file) {
		bases = append(bases, filepath.Base(f))
	}
	what := strings.TrimSpace(strings.Join(bases, " ") + " " + names)
	return PlanAction{
		ID: id, Type: "install-packages",
		Parameters:    map[string]string{"file": file, "names": names},
		Description:   T("az.pacchetti", what),
		ComeSiFa:      T("az.pacchetti.fa"),
		HowToVerify:   T("az.pacchetti.verifica"),
		HowToUndo:     T("az.pacchetti.annulla"),
		Reversibility: BEST_EFFORT,
	}
}

type packets struct {
	file, names []string
}

type beforePackages struct {
	Origine     Origine    `json:"origin"`
	Manager     string     `json:"manager"`
	File        []string   `json:"files,omitempty"`
	Names       []string   `json:"names"`
	ResolvedSet []Artifact `json:"resolved_set"`
}

func newPackages(p PlanAction) (Action, error) {
	return &packets{file: splitCommas(p.Parameters["file"]), names: splitCommas(p.Parameters["names"])}, nil
}

func (a *packets) handler(c *Context) (Manager, error) {
	if c.Env.Pacchetti == nil {
		return nil, Error("RX-PACCHETTI-003", c.Env.Famiglia)
	}
	return c.Env.Pacchetti, nil
}

// Constraints: the versions installed now of the named packages, and the files of the single package (by
// name: the .run is one, and its sha256 guarantees it whole).
func (a *packets) Constraints(c *Context) ([]string, error) {
	g, err := a.handler(c)
	if err != nil {
		return nil, err
	}
	var v []string
	for _, f := range a.file {
		v = append(v, "package-file:"+filepath.Base(f))
	}
	ver, err := g.Vers(a.names)
	if err != nil {
		return nil, err
	}
	for _, n := range a.names {
		v = append(v, "package:"+n+"="+notEmpty(ver[n], "absent"))
	}
	return v, nil
}

// genuine: the paths of the files on the machine (in the tests, under the fake root).
func genuine(c *Context, file []string) []string {
	var r []string
	for _, f := range file {
		r = append(r, c.Env.P(f))
	}
	return r
}

// splitCommas: «a,b» ⇒ [a b]; empty ⇒ none.
func splitCommas(s string) []string {
	var r []string
	for _, x := range strings.Split(s, ",") {
		if x = strings.TrimSpace(x); x != "" {
			r = append(r, x)
		}
	}
	return r
}

func (a *packets) Snapshot(c *Context) (json.RawMessage, Origine, error) {
	g, err := a.handler(c)
	if err != nil {
		return nil, "", err
	}
	if ok, det, err := g.Intact(); err != nil {
		return nil, "", err
	} else if !ok {
		return nil, "", Error("RX-PACCHETTI-004", det)
	}
	for _, f := range a.file {
		if _, err := os.Stat(c.Env.P(f)); err != nil {
			return nil, "", Error("RX-PACCHETTI-001", f+": "+err.Error())
		}
	}
	ins, err := g.Simulate(genuine(c, a.file), a.names)
	if err != nil {
		return nil, "", &ErrorRX{messageSimulate(err)}
	}
	p := beforePackages{Origine: PREEXISTING, Manager: g.Nome(), File: a.file, Names: a.names, ResolvedSet: ins}
	for _, x := range ins {
		if x.Outcome != "present" {
			p.Origine = DIRECT
		}
	}
	if err := WriteJSON(filepath.Join(c.Folder, "resolved-set-"+c.P.ID+".json"),
		map[string]any{"format": Schema, "object": "resolved-set", "action": c.P.ID, "manager": g.Nome(), "artifacts": ins}); err != nil {
		return nil, "", err
	}
	return jsonDi(p), p.Origine, nil
}

// messageSimulate: the manager's simulation did not succeed — RX-PACCHETTI-005 with what it says, unless
// the engine already has the reason (the manager stayed busy: RX-PACCHETTI-008).
func messageSimulate(err error) Message {
	var e *ErrorRX
	if errors.As(err, &e) {
		return e.M
	}
	return Msg("RX-PACCHETTI-005", err.Error())
}

func readPackagesBefore(before json.RawMessage) (beforePackages, error) {
	var p beforePackages
	err := json.Unmarshal(before, &p)
	return p, err
}

func (a *packets) Do(c *Context, before json.RawMessage) error {
	p, err := readPackagesBefore(before)
	if err != nil || p.Origine == PREEXISTING {
		return err
	}
	g, err := a.handler(c)
	if err != nil {
		return err
	}
	return g.Install(genuine(c, p.File), p.Names)
}

// state of the set's packages, now.
func (a *packets) count(c *Context, p beforePackages) (completed, newPresent int, err error) {
	g, err := a.handler(c)
	if err != nil {
		return 0, 0, err
	}
	ver, err := g.Vers(namesOf(p.ResolvedSet))
	if err != nil {
		return 0, 0, err
	}
	// D14 (DECISIONI §10.23): REMOTIX and its dependencies are upgraded with the system. A package
	// of the set is «complete» at the resolved version, at a NEWER one (a system upgrade
	// brought it), or at the one recorded by the last `remotix-install post-upgrade` (a rollback
	// done with the manager's commands)
	add := updatedVersions(c.Folder)
	for _, x := range p.ResolvedSet {
		v := ver[x.Nome]
		if versionEqual(v, x.Ver) || (add[x.Nome] != "" && versionEqual(v, add[x.Nome])) ||
			(v != "" && x.Ver != "" && ComparePackages(c.Env.Famiglia, v, x.Ver) > 0) {
			completed++
		}
		if x.Outcome == "new" && v != "" {
			newPresent++
		}
	}
	return completed, newPresent, nil
}

// versionEqual: the epoch «0:» does not count (dnf may write «0:2.3-1», rpm and dpkg «2.3-1»); any
// other epoch does, and every manager reports it (dpkg, pacman, and rpm through rpmEVR).
func versionEqual(a, b string) bool {
	return strings.TrimPrefix(a, "0:") == strings.TrimPrefix(b, "0:")
}

func (a *packets) Check(c *Context, before json.RawMessage) (Outcome, string, error) {
	p, err := readPackagesBefore(before)
	if err != nil {
		return "", "", err
	}
	g, err := a.handler(c)
	if err != nil {
		return "", "", err
	}
	if ok, det, err := g.Intact(); err != nil {
		return "", "", err
	} else if !ok {
		return A_META, "the package manager is half way: " + det, nil
	}
	completed, newcomers, err := a.count(c, p)
	if err != nil {
		return "", "", err
	}
	switch {
	case completed == len(p.ResolvedSet):
		return COMPLETE, fmt.Sprintf("%d packages at the resolved version", completed), nil
	case newcomers == 0 && completed == 0:
		return ABSENT, "none of the new packages", nil
	case newcomers == 0:
		return ABSENT, "none of the new packages (the upgraded ones stay)", nil
	}
	return A_META, fmt.Sprintf("%d of %d", completed, len(p.ResolvedSet)), nil
}

func (a *packets) Repair(c *Context, before json.RawMessage) error {
	g, err := a.handler(c)
	if err != nil {
		return err
	}
	if ok, _, err := g.Intact(); err == nil && ok {
		return nil
	}
	return g.Repair()
}

func (a *packets) Rollback(c *Context, before json.RawMessage) error {
	p, err := readPackagesBefore(before)
	if err != nil || p.Origine == PREEXISTING {
		return err
	}
	g, err := a.handler(c)
	if err != nil {
		return err
	}
	if ok, _, err := g.Intact(); err == nil && !ok {
		if err := g.Repair(); err != nil {
			return err
		}
	}
	ver, err := g.Vers(namesOf(p.ResolvedSet))
	if err != nil {
		return err
	}
	var newcomers []string
	for _, x := range p.ResolvedSet {
		if x.Outcome == "new" && ver[x.Nome] != "" {
			newcomers = append(newcomers, x.Nome)
		}
	}
	remove, _, err := held(g, newcomers, newcomers, c.Purge)
	if err != nil {
		return err
	}
	if len(remove) > 0 {
		return g.Remove(remove, c.Purge)
	}
	return nil
}

func (a *packets) RolledBack(c *Context, before json.RawMessage) (bool, string, error) {
	p, err := readPackagesBefore(before)
	if err != nil {
		return false, "", err
	}
	if p.Origine == PREEXISTING {
		return true, "already there: left untouched", nil
	}
	g, err := a.handler(c)
	if err != nil {
		return false, "", err
	}
	ver, err := g.Vers(namesOf(p.ResolvedSet))
	if err != nil {
		return false, "", err
	}
	var all_items, still []string
	for _, x := range p.ResolvedSet {
		if x.Outcome == "new" {
			all_items = append(all_items, x.Nome)
			if ver[x.Nome] != "" {
				still = append(still, x.Nome)
			}
		}
	}
	via, stays, err := held(g, still, all_items, c.Purge)
	if err != nil {
		return false, "", err
	}
	if len(via) > 0 {
		return false, fmt.Sprintf("%d new packages still installed", len(via)), nil
	}
	if len(stays) > 0 {
		return true, "[RX-PACCHETTI-006] " + T("pacchetti.trattenuti", strings.Join(stays, ", ")), nil
	}
	return true, "the new packages are gone", nil
}

// held: of the NEW packages to remove, those that can be removed and those that stay
// because something that stays requires them — a package UPGRADED by the same step, or a program
// installed later.
// Removing them would take that away too (`[M]` 30 Sep, leap16-kde: `zypper rm` of libx264 & co.
// dragged 53 packages, Plasma included). ⇒ They are not removed, and they are declared (§6.6.4: what
// remains indirectly is stated). A package is held back if removing it ALONE would remove something
// outside «ours» (the new ones of the same step): whoever depends on it in turn holds it back
// too, because the manager's simulation follows the whole chain.
func held(g Manager, candidates, our []string, purge bool) (via, stays []string, err error) {
	if len(candidates) == 0 {
		return nil, nil, nil
	}
	others, err := g.SimulateRemove(candidates, purge)
	if err != nil {
		return nil, nil, err
	}
	if len(notIn(others, our)) == 0 {
		return candidates, nil, nil
	}
	for _, n := range candidates {
		a, err := g.SimulateRemove([]string{n}, purge)
		if err != nil {
			return nil, nil, err
		}
		if len(notIn(a, our)) > 0 {
			stays = append(stays, n+" ("+T("pacchetti.chiesto_da", strings.Join(notIn(a, our), ", "))+")")
		} else {
			via = append(via, n)
		}
	}
	return via, stays, nil
}

// Indirect: the packages UPGRADED for us stay upgraded (§6.6.4): they are declared.
func (a *packets) Indirect(before json.RawMessage) []string {
	p, err := readPackagesBefore(before)
	if err != nil {
		return nil
	}
	var r []string
	for _, x := range p.ResolvedSet {
		if x.Outcome == "upgraded" {
			r = append(r, x.Nome+" "+x.Before+" → "+x.Ver)
		}
	}
	return r
}
