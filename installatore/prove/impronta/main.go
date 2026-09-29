// impronta: l'impronta di una cartella per la prova R1 (il controllo preliminare non tocca
// niente). Una riga per voce: percorso, tipo, permessi, proprietario, dimensione, ora di modifica
// in nanosecondi, destinazione dei collegamenti, sha256 dei file. Indipendente dal motore (non
// importa niente di suo): chi misura non deve essere chi è misurato.
//
//	impronta /etc > prima.txt
//	impronta -contenuti /etc > prima.txt   (senza l'ora di modifica delle CARTELLE: aggiungere e
//	                                        togliere un file la cambia, anche se poi tutto torna com'era)
//	impronta -confronta prima.txt dopo.txt
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
	"syscall"
)

func main() {
	if len(os.Args) == 4 && os.Args[1] == "-confronta" {
		os.Exit(confronta(os.Args[2], os.Args[3]))
	}
	radice := "/etc"
	args := os.Args[1:]
	contenuti := false
	if len(args) > 0 && args[0] == "-contenuti" {
		contenuti, args = true, args[1:]
	}
	if len(args) > 0 {
		radice = args[0]
	}
	err := filepath.WalkDir(radice, func(p string, d fs.DirEntry, err error) error {
		if err != nil {
			fmt.Printf("%s ERRORE %v\n", p, err)
			return nil
		}
		info, err := os.Lstat(p)
		if err != nil {
			fmt.Printf("%s ERRORE %v\n", p, err)
			return nil
		}
		st := info.Sys().(*syscall.Stat_t)
		riga := fmt.Sprintf("%s %s %d:%d %d %d", p, info.Mode(), st.Uid, st.Gid, info.Size(), info.ModTime().UnixNano())
		if info.IsDir() && contenuti {
			riga = fmt.Sprintf("%s %s %d:%d", p, info.Mode(), st.Uid, st.Gid)
		}
		switch {
		case info.Mode()&fs.ModeSymlink != 0:
			l, _ := os.Readlink(p)
			riga += " -> " + l
		case info.Mode().IsRegular():
			f, err := os.Open(p)
			if err == nil {
				h := sha256.New()
				io.Copy(h, f)
				f.Close()
				riga += " " + hex.EncodeToString(h.Sum(nil))
			} else {
				riga += " illeggibile"
			}
		}
		fmt.Println(riga)
		return nil
	})
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

// confronta due impronte: stampa le righe diverse, esce 1 se ce ne sono (nei contenitori minimi
// non c'è diff).
func confronta(a, b string) int {
	ra, _ := os.ReadFile(a)
	rb, _ := os.ReadFile(b)
	insieme := func(t []byte) map[string]bool {
		m := map[string]bool{}
		for _, r := range strings.Split(string(t), "\n") {
			m[r] = true
		}
		return m
	}
	ma, mb := insieme(ra), insieme(rb)
	diversi := 0
	for r := range ma {
		if !mb[r] {
			fmt.Println("- " + r)
			diversi++
		}
	}
	for r := range mb {
		if !ma[r] {
			fmt.Println("+ " + r)
			diversi++
		}
	}
	if diversi > 0 {
		return 1
	}
	return 0
}
