package motore

import (
	"encoding/json"
	"path/filepath"
	"sort"
)

// DOPO UN AGGIORNAMENTO DEL SISTEMA (DECISIONI §10.23, D14): REMOTIX si aggiorna quando
// l'amministratore aggiorna la macchina (apt upgrade, dnf upgrade, zypper up, pacman -Syu), come ogni
// altro programma. Il motore non ha un sistema di aggiornamento suo: niente timer, niente comando
// «aggiorna». Gli script dei pacchetti remotix e remotix-install, a ogni cambio di versione (anche
// all'indietro, coi comandi del gestore), chiamano `remotix-install aggiornato`, che:
//   - ANNOTA le versioni dei pacchetti di REMOTIX installate adesso (aggiornamenti.json, accanto alle
//     operazioni): il «controlla» dei pacchetti dell'installazione le accetta, e `certifica` resta
//     verde anche dopo un ritorno a una versione precedente;
//   - dice se l'installazione è ancora certificata e se la macchina ha un motivo BLOCCANTE.
// Il riavvio che non chiude i desktop lo fa lo script del pacchetto remotix (try-restart), non il
// motore: un servizio fermato dall'amministratore resta fermo.

// FileVersioniAnnotate: le versioni annotate dopo l'ultimo cambio.
const FileVersioniAnnotate = "recorded-versions.json"

// AnnotaVersioni scrive le versioni installate dei pacchetti di REMOTIX (quelli che mancano no).
func (m *Motore) AnnotaVersioni() (map[string]string, error) {
	if m.Amb == nil || m.Amb.Pacchetti == nil {
		return nil, Errore("RX-PACCHETTI-003", "")
	}
	v, err := m.Amb.Pacchetti.Versioni(PacchettiArchivio)
	if err != nil {
		return nil, err
	}
	r := map[string]string{}
	for n, x := range v {
		if x != "" {
			r[n] = x
		}
	}
	return r, ScriviJSON(filepath.Join(filepath.Dir(m.Cartella), FileVersioniAnnotate),
		map[string]any{"format": Formato, "object": "recorded-versions", "versions": r, "written": ora()})
}

// versioniAggiornate: quelle annotate dall'ultimo `aggiornato` (vuoto se nessuno).
func versioniAggiornate(cartellaOp string) map[string]string {
	var x struct {
		Versioni map[string]string `json:"versions"`
	}
	LeggiJSON(filepath.Join(filepath.Dir(filepath.Dir(cartellaOp)), FileVersioniAnnotate), &x)
	return x.Versioni
}

// ---------------------------------------------------------------- piccoli aiuti

func chiaviOrdinate(m map[string]string) []string {
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

func haCodice(m []Messaggio, c string) bool {
	for _, x := range m {
		if x.Codice == c {
			return true
		}
	}
	return false
}

func jsonCompatto(v any) string {
	b, _ := json.Marshal(v)
	return string(b)
}
