package engine

import (
	"strconv"
	"strings"
)

// Comparing PACKAGE versions (after D14: an installation package moved further
// ahead by a system upgrade is still «complete», action_packages.go). Two algorithms, those of the managers themselves: dpkg (Debian, Ubuntu) and rpmvercmp
// (rpm, and pacman which uses the same one). ⚠ CompareVersions (profile.go) stays the simple one for
// «human» versions (GNOME 48, OpenSSL 3.5.1): here there are epochs, revisions, tildes.

// ComparePackages compares two package versions of the family: -1, 0, 1.
func ComparePackages(family, a, b string) int {
	if family == "debian" {
		return compareDeb(a, b)
	}
	return compareRpm(a, b)
}

func sign(x int) int {
	switch {
	case x < 0:
		return -1
	case x > 0:
		return 1
	}
	return 0
}

func digit(c byte) bool  { return c >= '0' && c <= '9' }
func letter(c byte) bool { return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') }

// epoch: "2:1.0-1" → 2, "1.0-1".
func epoch(v string) (int, string) {
	if i := strings.Index(v, ":"); i >= 0 {
		n, _ := strconv.Atoi(v[:i])
		return n, v[i+1:]
	}
	return 0, v
}

// lastDash: "1.0-2+deb13" → "1.0", "2+deb13".
func lastDash(v string) (string, string) {
	if i := strings.LastIndex(v, "-"); i >= 0 {
		return v[:i], v[i+1:]
	}
	return v, ""
}

func compareDeb(a, b string) int {
	ea, va := epoch(a)
	eb, vb := epoch(b)
	if ea != eb {
		return sign(ea - eb)
	}
	ua, ra := lastDash(va)
	ub, rb := lastDash(vb)
	if c := verrevcmp(ua, ub); c != 0 {
		return c
	}
	return verrevcmp(ra, rb)
}

func debOrder(s string, i int) int {
	if i >= len(s) {
		return 0
	}
	c := s[i]
	switch {
	case digit(c):
		return 0
	case letter(c):
		return int(c)
	case c == '~':
		return -1
	}
	return int(c) + 256
}

// verrevcmp: dpkg's algorithm (lib/dpkg/version.c).
func verrevcmp(a, b string) int {
	i, j := 0, 0
	for i < len(a) || j < len(b) {
		diff := 0
		for (i < len(a) && !digit(a[i])) || (j < len(b) && !digit(b[j])) {
			ac, bc := debOrder(a, i), debOrder(b, j)
			if ac != bc {
				return sign(ac - bc)
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
		for i < len(a) && digit(a[i]) && j < len(b) && digit(b[j]) {
			if diff == 0 {
				diff = int(a[i]) - int(b[j])
			}
			i++
			j++
		}
		if i < len(a) && digit(a[i]) {
			return 1
		}
		if j < len(b) && digit(b[j]) {
			return -1
		}
		if diff != 0 {
			return sign(diff)
		}
	}
	return 0
}

func compareRpm(a, b string) int {
	ea, va := epoch(a)
	eb, vb := epoch(b)
	if ea != eb {
		return sign(ea - eb)
	}
	ua, ra := lastDash(va)
	ub, rb := lastDash(vb)
	if c := rpmvercmp(ua, ub); c != 0 {
		return c
	}
	return rpmvercmp(ra, rb)
}

// rpmvercmp: rpm's algorithm (rpmio/rpmvercmp.c), which pacman uses too (alpm_pkg_vercmp).
func rpmvercmp(a, b string) int {
	if a == b {
		return 0
	}
	i, j := 0, 0
	sep := func(c byte) bool { return !digit(c) && !letter(c) && c != '~' && c != '^' }
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
		yes, sj := i, j
		num := digit(a[i])
		if num {
			for i < len(a) && digit(a[i]) {
				i++
			}
			for j < len(b) && digit(b[j]) {
				j++
			}
		} else {
			for i < len(a) && letter(a[i]) {
				i++
			}
			for j < len(b) && letter(b[j]) {
				j++
			}
		}
		pa, pb := a[yes:i], b[sj:j]
		if pb == "" {
			if num {
				return 1
			}
			return -1
		}
		if num {
			pa, pb = strings.TrimLeft(pa, "0"), strings.TrimLeft(pb, "0")
			if len(pa) != len(pb) {
				return sign(len(pa) - len(pb))
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
