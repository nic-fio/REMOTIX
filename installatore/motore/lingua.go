package motore

import "fmt"

// L'installatore parla solo inglese (DECISIONI §10.35, che supera §10.15): è destinato agli
// amministratori di sistema. I testi stanno in cataloghi, non sparsi nel codice: i messaggi dei
// codici in codici.go, il resto in testi.go, con T(chiave). I codici RX-… sono stabili.
// ⚠ Restano in italiano, per ora: i testi del catalogo delle combinazioni (motivi, note: sono dati,
// avranno i loro campi inglesi nella prossima versione del formato del catalogo) e i dettagli
// diagnostici che le azioni scrivono nel registro.

// T: il testo di una chiave, con gli argomenti alla fmt.Sprintf. Una chiave che manca è un difetto
// (TestTesti la trova): esce la chiave stessa, non un vuoto.
func T(chiave string, args ...any) string {
	t, ok := testi[chiave]
	if !ok {
		return "⟨" + chiave + "⟩"
	}
	if len(args) == 0 {
		return t
	}
	return fmt.Sprintf(t, args...)
}
