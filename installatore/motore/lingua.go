package motore

import (
	"fmt"
	"os"
	"strings"
)

// L'installatore è BILINGUE, italiano e inglese (DECISIONI §10.15). La lingua si legge
// dall'ambiente nell'ordine LANGUAGE, LC_ALL, LC_MESSAGES, LANG: italiano se la prima indicata è
// «it», inglese in ogni altro caso. Quando la parte da amministratore viene rilanciata (polkit
// ripulisce l'ambiente) la lingua si passa esplicitamente (--lingua); il file di risposte potrà
// fissarla. I codici RX-… sono gli stessi nelle due lingue.
//
// I testi stanno in cataloghi per lingua, non sparsi nel codice: i messaggi dei codici in
// codici.go (italiano) e codici_en.go (inglese); il resto in testi.go, con T(chiave).
// ⚠ Restano in italiano, per ora: i testi del catalogo delle combinazioni (motivi, note: sono dati,
// avranno i loro campi inglesi nella prossima versione del formato del catalogo) e i dettagli
// diagnostici che le azioni scrivono nel registro.

// Lingua: "it" o "en".
type Lingua string

const (
	IT Lingua = "it"
	EN Lingua = "en"
)

var linguaAttuale = LinguaDaAmbiente(os.Getenv)

// LinguaDaAmbiente: la prima variabile indicata decide.
func LinguaDaAmbiente(getenv func(string) string) Lingua {
	for _, v := range []string{"LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"} {
		x := strings.TrimSpace(getenv(v))
		if x == "" {
			continue
		}
		primo, _, _ := strings.Cut(x, ":") // LANGUAGE può essere «it:en»
		if primo == "it" || strings.HasPrefix(primo, "it_") || strings.HasPrefix(primo, "it.") || strings.HasPrefix(primo, "it@") {
			return IT
		}
		return EN
	}
	return EN
}

// ImpostaLingua fissa la lingua (--lingua, file di risposte). Una lingua sconosciuta vale inglese.
func ImpostaLingua(l string) {
	if strings.HasPrefix(l, "it") {
		linguaAttuale = IT
	} else {
		linguaAttuale = EN
	}
}

// LinguaAttuale: quella in uso.
func LinguaAttuale() Lingua { return linguaAttuale }

// Testo: un testo nelle due lingue.
type Testo struct{ It, En string }

func (t Testo) S() string {
	if linguaAttuale == IT || t.En == "" {
		return t.It
	}
	return t.En
}

// T: il testo di una chiave nella lingua attuale, con gli argomenti alla fmt.Sprintf. Una chiave
// che manca è un difetto (TestTesti la trova): esce la chiave stessa, non un vuoto.
func T(chiave string, args ...any) string {
	t, ok := testi[chiave]
	if !ok {
		return "⟨" + chiave + "⟩"
	}
	if len(args) == 0 {
		return t.S()
	}
	return fmt.Sprintf(t.S(), args...)
}
