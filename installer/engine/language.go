package engine

import "fmt"

// The installer speaks English only (DECISIONI §10.35, which supersedes §10.15): it is meant for
// system administrators. The texts live in catalogues, not scattered in the code: the messages of
// the codes in codes.go, the rest in texts.go, with T(key). The RX-… codes are stable.
// The catalogue's texts (reasons, notes, limits) and the actions' diagnostic details are in
// English too (catalogue 2026.10.10.12); english_test.go looks for leftover Italian in every string of
// the code and of the catalogue. Italian remains where they are NAMES and not texts: the commands and options
// (verify, install, --archivio…), the entries and values of the answers file (consenso.*, yes/no,
// stabile/has_candidate), the values of the facts (is_present, assente…) and the names of the states.

// T: the text of a key, with the arguments à la fmt.Sprintf. A missing key is a defect
// (TestTexts finds it): the key itself comes out, not a blank.
func T(key string, args ...any) string {
	t, ok := texts[key]
	if !ok {
		return "⟨" + key + "⟩"
	}
	if len(args) == 0 {
		return t
	}
	return fmt.Sprintf(t, args...)
}
