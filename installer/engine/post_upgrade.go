package engine

import (
	"encoding/json"
	"path/filepath"
	"sort"
)

// AFTER A SYSTEM UPGRADE (DECISIONI §10.23, D14): REMOTIX is upgraded when
// the administrator upgrades the machine (apt upgrade, dnf upgrade, zypper up, pacman -Syu), like every
// other program. The engine has no update system of its own: no timer, no
// «do_update» command. The scripts of the remotix and remotix-install packages, at every version change (even
// backwards, with the manager's commands), call `remotix-install post-upgrade`, which:
//   - RECORDS the versions of REMOTIX's packages installed now (aggiornamenti.json, next to the
//     operations): the «check» of the installation's packages accepts them, and `certify` stays
//     green even after going back to a previous version;
//   - says whether the installation is still certified and whether the machine has a BLOCKING reason.
// The restart that does not close the desktops is done by the remotix package's script (try-restart), not by the
// engine: a service stopped by the administrator stays stopped.

// AnnotatedVersionsFile: the versions recorded after the last change.
const AnnotatedVersionsFile = "recorded-versions.json"

// AnnotateVersions writes the installed versions of REMOTIX's packages (not the missing ones).
func (m *Engine) AnnotateVersions() (map[string]string, error) {
	if m.Env == nil || m.Env.Pacchetti == nil {
		return nil, Error("RX-PACCHETTI-003", "")
	}
	v, err := m.Env.Pacchetti.Vers(RemotixPackages)
	if err != nil {
		return nil, err
	}
	r := map[string]string{}
	for n, x := range v {
		if x != "" {
			r[n] = x
		}
	}
	return r, WriteJSON(filepath.Join(filepath.Dir(m.Folder), AnnotatedVersionsFile),
		map[string]any{"format": Schema, "object": "recorded-versions", "versions": r, "written": now()})
}

// updatedVersions: those recorded by the last `updated` (empty if none).
func updatedVersions(folderOp string) map[string]string {
	var x struct {
		Vers map[string]string `json:"versions"`
	}
	ReadJSON(filepath.Join(filepath.Dir(filepath.Dir(folderOp)), AnnotatedVersionsFile), &x)
	return x.Vers
}

// ---------------------------------------------------------------- small helpers

func sortedKeys(m map[string]string) []string {
	r := make([]string, 0, len(m))
	for k := range m {
		r = append(r, k)
	}
	sort.Strings(r)
	return r
}

func contains(l []string, x string) bool {
	for _, y := range l {
		if y == x {
			return true
		}
	}
	return false
}

func hasCode(m []Message, c string) bool {
	for _, x := range m {
		if x.Codice == c {
			return true
		}
	}
	return false
}

func jsonCompact(v any) string {
	b, _ := json.Marshal(v)
	return string(b)
}
