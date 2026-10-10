package motore

import (
	"encoding/json"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"testing"
)

// English only (DECISIONI §10.35): every text that reaches the administrator — the codes' details,
// the verification outcomes, the facts' notes, lines written into system files, the catalogue's texts — is in
// English. The names follow the repo's conventions.

// italiano: accents, or words that do not exist in English.
var italiano = regexp.MustCompile(`(?i)[àèéìòù]|\b(non|niente|nessun[oa]?|della|delle|dello|degli|del|dei|nel|nella|nelle|negli|sul|sulla|dal|dalla|il|lo|gli|una|uno|che|con|senza|ancora|già|prima|dopo|adesso|ora|sono|anche|oppure|manca|mancano|serve|servono|questa|questo|quel|quella|ogni|tutti|tutte|fra|tra|né|ci|si|da|di|quando|sempre|mai|altri|altre|alcune|qui|dove|chi|cosa|tocca|vale|deve|può|essere|scheda|pacchetto|pacchetti|deposito|depositi|macchina|utente|utenti|archivio|motore|piano|riga|voce|valore|cartella|chiave|impronta|regola|regole|versione|sconosciut[oa]|abilitat[oa]|accesa|acceso|accesi|letto|legge|leggibile|scaricato|gestore|modulo|moduli|file\s+di|disfare|rimandat[ea]|immutabili|distribuzioni|gruppi|sessione|sessioni|sotto|tappa|nucleo|carattere|scalabile|qualunque|fatto|fatta|ripresa|modifica|alla|alle|allo|agli|nello|quello|quelli|mentre|troppo|vecchia|vecchio|nuovo|nuova|nuovi|cambiata|cambiato|fallita|fermata|rimasto|rimasta|toglie|togliere|tolto|tolti|aggiunto|aggiunti|indietro|rispetto|fuori|dentro|diverso|diversa|vuoto|stesso|stessa|soltanto|codifica|prova|provata|provato|strada|campo)\b`)

// identificativo: keys, names of actions and packages, options, paths (they are not texts).
var identificativo = regexp.MustCompile(`^[A-Za-z0-9_.:/\-\[\]=<>@*+,%]*$`)

// vocabolario: the values of the facts and answers compared in the code (a name, not a text).
var vocabolario = map[string]bool{
	"present": true, "absent": true, "none": true, "with": true, "without": true, "unknown": true,
	"yes": true, "sì": true, "no": true, "all": true, "stable": true, "candidate": true, "open": true,
	"closed": true, "vuota": true,
	// not ours: zypper's output in Italian, which gestore.go recognises (like the English one)
	"il pacchetto installato ": true,
}

// nomiDentro: the interface's names inside an English text — options, answer entries, commands,
// values between «», states in capitals, paths — are removed before looking for Italian.
var nomiDentro = regexp.MustCompile(`--[\w-]+|\b[\w<>-]+(\.[\w<>-]+)+\b|«[^»]*»|\bremotix-install [\w-]+|\b[A-Z][A-Z_-]{2,}\b|\S*/\S+|\S+-<\S+|[\w.<>-]+ ?= ?[\w|,<>./:-]+|\w+(\|\w+)+|\b[a-z0-9]+(-[a-z0-9]+)+\b`)

func testoItaliano(s string) bool {
	t := strings.TrimSpace(s)
	if t == "" || identificativo.MatchString(t) || vocabolario[t] || vocabolario[s] {
		return false
	}
	return italiano.MatchString(nomiDentro.ReplaceAllString(s, " "))
}

func TestSoloIngleseNelCodice(t *testing.T) {
	var file []string
	for _, g := range []string{"*.go", "../interfaccia/*.go", "../interfaccia/tui/*.go", "../cmd/remotix-install/*.go"} {
		m, _ := filepath.Glob(g)
		file = append(file, m...)
	}
	sort.Strings(file)
	trovati := 0
	for _, f := range file {
		if strings.HasSuffix(f, "_test.go") {
			continue
		}
		fs := token.NewFileSet()
		af, err := parser.ParseFile(fs, f, nil, 0)
		if err != nil {
			t.Fatal(err)
		}
		saltare := map[*ast.BasicLit]bool{}
		for _, im := range af.Imports {
			saltare[im.Path] = true
		}
		ast.Inspect(af, func(n ast.Node) bool {
			switch x := n.(type) {
			case *ast.Field:
				if x.Tag != nil {
					saltare[x.Tag] = true
				}
			case *ast.BasicLit:
				if x.Kind != token.STRING || saltare[x] {
					return true
				}
				s, err := strconv.Unquote(x.Value)
				if err != nil {
					s = x.Value
				}
				if testoItaliano(s) {
					trovati++
					t.Errorf("%s: Italian left: %q", fs.Position(x.Pos()), s)
				}
			}
			return true
		})
	}
	_ = trovati
}

func TestSoloIngleseNelCatalogo(t *testing.T) {
	b, err := os.ReadFile("../catalogo/catalogo.json")
	if err != nil {
		t.Fatal(err)
	}
	var c any
	if err := json.Unmarshal(b, &c); err != nil {
		t.Fatal(err)
	}
	var cammina func(percorso string, v any)
	cammina = func(percorso string, v any) {
		switch x := v.(type) {
		case map[string]any:
			for k, w := range x {
				if k == "fonte" { // references to our documents: for us, the engine does not show them
					continue
				}
				cammina(percorso+"."+k, w)
			}
		case []any:
			for i, w := range x {
				cammina(percorso+"["+strconv.Itoa(i)+"]", w)
			}
		case string:
			if testoItaliano(x) {
				t.Errorf("catalogo%s: Italian left: %q", percorso, x)
			}
		}
	}
	cammina("", c)
}

// The detector itself: an Italian it does not see is not a test.
func TestRivelatoreItaliano(t *testing.T) {
	for _, s := range []string{"c'era già: non si tocca", "riga 3: voce sconosciuta «x»", "niente da disfare: x",
		"Mesa di openSUSE (senza H.264)", "com'era prima"} {
		if !testoItaliano(s) {
			t.Errorf("not seen: %q", s)
		}
	}
	for _, s := range []string{"already there: left untouched", "consent.repo.epel", "--non-interactive",
		"intel-media-va-driver-non-free", "present", "line 3: unknown entry «x»", "%s: %q",
		"give consent (consent.repo.<name> = yes)", "Updates will come from there too, with the system's"} {
		if testoItaliano(s) {
			t.Errorf("false alarm: %q", s)
		}
	}
}
