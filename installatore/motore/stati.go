package motore

import "sort"

// State of an operation (§6.6.2).
type State string

const (
	NEW                       State = "NEW"
	TRUSTED                   State = "TRUSTED"
	EXAMINED                  State = "EXAMINED"
	EVALUATED                 State = "ASSESSED"
	PLANNED                   State = "PLANNED"
	APPROVED                  State = "APPROVED"
	ACQUIRED                  State = "ACQUIRED"
	RUNNING                   State = "RUNNING"
	INTERRUPTED               State = "INTERRUPTED"
	APPLIED                   State = "APPLIED"
	VERIFYING                 State = "VERIFYING"
	VERIFIED                  State = "VERIFIED"
	CONFIRMED                 State = "CONFIRMED"
	CONFIRMED_WITH_CONDITIONS State = "CONFIRMED_WITH_CONDITIONS"
	ROLLING_BACK              State = "ROLLING_BACK"
	ROLLED_BACK               State = "ROLLED_BACK"
	PARTIALLY_ROLLED_BACK     State = "PARTIALLY_ROLLED_BACK"
	BLOCKED                   State = "BLOCKED"
	RIFIUTATA                 State = "REFUSED"
)

// transitions: the ONLY valid ones, those of the design of §6.6.2. ⛔ no state is skipped.
//
// BLOCKED means ONLY «nothing has been touched» (§6.6.2) and is final. When the machine has already
// been touched and resume finds a DONE step undone by others (§6.6.3, last line), the state
// is INTERRUPTED with the code RX-RIPRESA-001: one leaves it with continue_it or rollback (the
// coordinator's decision, 30 Sep). APPLIED and VERIFIED can go to ROLLING_BACK («red»).
var transitions = map[State][]State{
	NEW:          {TRUSTED, BLOCKED},
	TRUSTED:      {EXAMINED, BLOCKED},
	EXAMINED:     {EVALUATED, BLOCKED},
	EVALUATED:    {PLANNED, BLOCKED},
	PLANNED:      {APPROVED, RIFIUTATA, BLOCKED},
	APPROVED:     {ACQUIRED, BLOCKED},
	ACQUIRED:     {RUNNING, BLOCKED},
	RUNNING:      {APPLIED, INTERRUPTED, ROLLING_BACK},
	INTERRUPTED:  {RUNNING, ROLLING_BACK},
	APPLIED:      {VERIFYING, ROLLING_BACK},
	VERIFYING:    {VERIFIED, ROLLING_BACK},
	VERIFIED:     {CONFIRMED, CONFIRMED_WITH_CONDITIONS, ROLLING_BACK},
	ROLLING_BACK: {ROLLED_BACK, PARTIALLY_ROLLED_BACK},
}

// Valid says whether da → a is a transition of the design.
func Valid(da, a State) bool {
	for _, x := range transitions[da] {
		if x == a {
			return true
		}
	}
	return false
}

// Finale: the states one never leaves.
func Finale(s State) bool {
	switch s {
	case CONFIRMED, CONFIRMED_WITH_CONDITIONS, ROLLED_BACK, PARTIALLY_ROLLED_BACK, RIFIUTATA, BLOCKED:
		return true
	}
	return false
}

// AllStates, in alphabetical order (for the tests).
func AllStates() []State {
	seen_items := map[State]bool{}
	for da, aa := range transitions {
		seen_items[da] = true
		for _, a := range aa {
			seen_items[a] = true
		}
	}
	var r []State
	for s := range seen_items {
		r = append(r, s)
	}
	sort.Slice(r, func(i, j int) bool { return r[i] < r[j] })
	return r
}
