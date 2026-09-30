package motore

import (
	"strconv"
	"strings"
)

// Il confronto delle versioni dei PACCHETTI (dopo D14: un pacchetto dell'installazione portato più
// avanti da un aggiornamento del sistema è ancora «completo», azione_pacchetti.go). Due algoritmi, quelli dei gestori stessi: dpkg (Debian, Ubuntu) e rpmvercmp
// (rpm, e pacman che usa lo stesso). ⚠ ConfrontaVersioni (profilo.go) resta quello semplice per le
// versioni «umane» (GNOME 48, OpenSSL 3.5.1): qui ci sono epoche, revisioni, tilde.

// ConfrontaPacchetti confronta due versioni di pacchetto della famiglia: -1, 0, 1.
func ConfrontaPacchetti(famiglia, a, b string) int {
	if famiglia == "debian" {
		return confrontaDeb(a, b)
	}
	return confrontaRpm(a, b)
}

func segno(x int) int {
	switch {
	case x < 0:
		return -1
	case x > 0:
		return 1
	}
	return 0
}

func cifra(c byte) bool   { return c >= '0' && c <= '9' }
func lettera(c byte) bool { return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') }

// epoca: "2:1.0-1" → 2, "1.0-1".
func epoca(v string) (int, string) {
	if i := strings.Index(v, ":"); i >= 0 {
		n, _ := strconv.Atoi(v[:i])
		return n, v[i+1:]
	}
	return 0, v
}

// ultimoTrattino: "1.0-2+deb13" → "1.0", "2+deb13".
func ultimoTrattino(v string) (string, string) {
	if i := strings.LastIndex(v, "-"); i >= 0 {
		return v[:i], v[i+1:]
	}
	return v, ""
}

func confrontaDeb(a, b string) int {
	ea, va := epoca(a)
	eb, vb := epoca(b)
	if ea != eb {
		return segno(ea - eb)
	}
	ua, ra := ultimoTrattino(va)
	ub, rb := ultimoTrattino(vb)
	if c := verrevcmp(ua, ub); c != 0 {
		return c
	}
	return verrevcmp(ra, rb)
}

func ordineDeb(s string, i int) int {
	if i >= len(s) {
		return 0
	}
	c := s[i]
	switch {
	case cifra(c):
		return 0
	case lettera(c):
		return int(c)
	case c == '~':
		return -1
	}
	return int(c) + 256
}

// verrevcmp: l'algoritmo di dpkg (lib/dpkg/version.c).
func verrevcmp(a, b string) int {
	i, j := 0, 0
	for i < len(a) || j < len(b) {
		diff := 0
		for (i < len(a) && !cifra(a[i])) || (j < len(b) && !cifra(b[j])) {
			ac, bc := ordineDeb(a, i), ordineDeb(b, j)
			if ac != bc {
				return segno(ac - bc)
			}
			i++
			j++
		}
		for i < len(a) && a[i] == '0' {
			i++
		}
		for j < len(b) && b[j] == '0' {
			j++
		}
		for i < len(a) && cifra(a[i]) && j < len(b) && cifra(b[j]) {
			if diff == 0 {
				diff = int(a[i]) - int(b[j])
			}
			i++
			j++
		}
		if i < len(a) && cifra(a[i]) {
			return 1
		}
		if j < len(b) && cifra(b[j]) {
			return -1
		}
		if diff != 0 {
			return segno(diff)
		}
	}
	return 0
}

func confrontaRpm(a, b string) int {
	ea, va := epoca(a)
	eb, vb := epoca(b)
	if ea != eb {
		return segno(ea - eb)
	}
	ua, ra := ultimoTrattino(va)
	ub, rb := ultimoTrattino(vb)
	if c := rpmvercmp(ua, ub); c != 0 {
		return c
	}
	return rpmvercmp(ra, rb)
}

// rpmvercmp: l'algoritmo di rpm (rpmio/rpmvercmp.c), che usa anche pacman (alpm_pkg_vercmp).
func rpmvercmp(a, b string) int {
	if a == b {
		return 0
	}
	i, j := 0, 0
	sep := func(c byte) bool { return !cifra(c) && !lettera(c) && c != '~' && c != '^' }
	for i < len(a) || j < len(b) {
		for i < len(a) && sep(a[i]) {
			i++
		}
		for j < len(b) && sep(b[j]) {
			j++
		}
		ta, tb := i < len(a) && a[i] == '~', j < len(b) && b[j] == '~'
		if ta || tb {
			if !ta {
				return 1
			}
			if !tb {
				return -1
			}
			i++
			j++
			continue
		}
		ca, cb := i < len(a) && a[i] == '^', j < len(b) && b[j] == '^'
		if ca || cb {
			if i >= len(a) {
				return -1
			}
			if j >= len(b) {
				return 1
			}
			if !ca {
				return 1
			}
			if !cb {
				return -1
			}
			i++
			j++
			continue
		}
		if i >= len(a) || j >= len(b) {
			break
		}
		si, sj := i, j
		num := cifra(a[i])
		if num {
			for i < len(a) && cifra(a[i]) {
				i++
			}
			for j < len(b) && cifra(b[j]) {
				j++
			}
		} else {
			for i < len(a) && lettera(a[i]) {
				i++
			}
			for j < len(b) && lettera(b[j]) {
				j++
			}
		}
		pa, pb := a[si:i], b[sj:j]
		if pb == "" {
			if num {
				return 1
			}
			return -1
		}
		if num {
			pa, pb = strings.TrimLeft(pa, "0"), strings.TrimLeft(pb, "0")
			if len(pa) != len(pb) {
				return segno(len(pa) - len(pb))
			}
		}
		if c := strings.Compare(pa, pb); c != 0 {
			return c
		}
	}
	switch {
	case i >= len(a) && j >= len(b):
		return 0
	case i < len(a):
		return 1
	}
	return -1
}
