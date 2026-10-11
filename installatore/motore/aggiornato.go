package motore

import (
	"encoding/json"
	"path/filepath"
	"sort"
)

// AFTER A SYSTEM UPGRADE (DECISIONI §10.23, D14): REMOTIX is upgraded when
// the administrator upgrades the machine (apt upgrade, dnf upgrade, zypper up, pacman -Syu), like every
// other program. The engine has no update system of its own: no timer, no
// «aggiorna» command. The scripts of the remotix and remotix-install packages, at every version change (even
// backwards, with the manager's commands), call `remotix-install aggiornato`, which:
//   - RECORDS the versions of REMOTIX's packages installed now (aggiornamenti.json, next to the
//     operations): the «controlla» of the installation's packages accepts them, and `certifica` stays
//     green even after going back to a previous version;
//   - says whether the installation is still certified and whether the machine has a BLOCKING reason.
// The restart that does not close the desktops is done by the remotix package's script (try-restart), not by the
// engine: a service stopped by the administrator stays stopped.

// AnnotatedVersionsFile: the versions recorded after the last change.
const AnnotatedVersionsFile = "recorded-versions.json"

// AnnotateVersions writes the installed versions of REMOTIX's packages (not the missing ones).
func (m *Motore) AnnotateVersions() (map[string]string, error) {
	if m.Amb == nil || m.Amb.Pacchetti == nil {
		return nil, Errore("RX-PACCHETTI-003", "")
	}
	v, err := m.Amb.Pacchetti.Versions(RemotixPackages)
	if err != nil {
		return nil, err
	}
	r := map[string]string{}
	for n, x := range v {
		if x != "" {
			r[n] = x
		}
	}
	return r, WriteJSON(filepath.Join(filepath.Dir(m.Cartella), AnnotatedVersionsFile),
		map[string]any{"format": Formato, "object": "recorded-versions", "versions": r, "written": ora()})
}

// updatedVersions: those recorded by the last `aggiornato` (empty if none).
func updatedVersions(folderOp string) map[string]string {
	var x struct {
		Versions map[string]string `json:"versions"`
	}
	LeggiJSON(filepath.Join(filepath.Dir(filepath.Dir(folderOp)), AnnotatedVersionsFile), &x)
	return x.Versions
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

func contiene(l []string, x string) bool {
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
