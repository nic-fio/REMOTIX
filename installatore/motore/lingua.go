package motore

import "fmt"

// L'installatore parla solo inglese (DECISIONI §10.35, che supera §10.15): è destinato agli
// amministratori di sistema. I testi stanno in cataloghi, non sparsi nel codice: i messaggi dei
// codici in codici.go, il resto in testi.go, con T(chiave). I codici RX-… sono stabili.
// Anche i testi del catalogo (motivi, note, limiti) e i dettagli diagnostici delle azioni sono in
// inglese (catalogo 2026.10.10.12); inglese_test.go cerca l'italiano rimasto in ogni stringa del
// codice e del catalogo. Restano italiani, perché sono NOMI e non testi: i comandi e le opzioni
// (verifica, installa, --archivio…), le voci e i valori del file di risposte (consenso.*, si/no,
// stabile/candidato), i valori dei fatti (presente, assente…) e i nomi degli stati.

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
