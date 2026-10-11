// fingerprint: the fingerprint of a folder for test R1 (the preliminary check touches
// nothing). One line per entry: path, type, permissions, owner, size, modification time
// in nanoseconds, link target, sha256 of the files. Independent of the engine (it does not
// import anything of its own): whoever measures must not be whoever is measured.
//
//	fingerprint /etc > prima.txt
//	fingerprint -contents /etc > prima.txt   (without the modification time of FOLDERS: adding and
//	                                        removing a file changes it, even if then everything goes back as it was)
//	fingerprint -compare prima.txt dopo.txt
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
	if len(os.Args) == 4 && os.Args[1] == "-compare" {
		os.Exit(compare(os.Args[2], os.Args[3]))
	}
	root := "/etc"
	args := os.Args[1:]
	contents := false
	if len(args) > 0 && args[0] == "-contents" {
		contents, args = true, args[1:]
	}
	if len(args) > 0 {
		root = args[0]
	}
	err := filepath.WalkDir(root, func(p string, d fs.DirEntry, err error) error {
		if err != nil {
			fmt.Printf("%s ERROR %v\n", p, err)
			return nil
		}
		info, err := os.Lstat(p)
		if err != nil {
			fmt.Printf("%s ERROR %v\n", p, err)
			return nil
		}
		st := info.Sys().(*syscall.Stat_t)
		line := fmt.Sprintf("%s %s %d:%d %d %d", p, info.Mode(), st.Uid, st.Gid, info.Size(), info.ModTime().UnixNano())
		if info.IsDir() && contents {
			line = fmt.Sprintf("%s %s %d:%d", p, info.Mode(), st.Uid, st.Gid)
		}
		switch {
		case info.Mode()&fs.ModeSymlink != 0:
			l, _ := os.Readlink(p)
			line += " -> " + l
		case info.Mode().IsRegular():
			f, err := os.Open(p)
			if err == nil {
				h := sha256.New()
				io.Copy(h, f)
				f.Close()
				line += " " + hex.EncodeToString(h.Sum(nil))
			} else {
				line += " unreadable"
			}
		}
		fmt.Println(line)
		return nil
	})
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

// compare two fingerprints: prints the differing lines, exits 1 if there are any (the minimal containers
// have no diff).
func compare(a, b string) int {
	ra, _ := os.ReadFile(a)
	rb, _ := os.ReadFile(b)
	together := func(t []byte) map[string]bool {
		m := map[string]bool{}
		for _, r := range strings.Split(string(t), "\n") {
			m[r] = true
		}
		return m
	}
	ma, mb := together(ra), together(rb)
	different := 0
	for r := range ma {
		if !mb[r] {
			fmt.Println("- " + r)
			different++
		}
	}
	for r := range mb {
		if !ma[r] {
			fmt.Println("+ " + r)
			different++
		}
	}
	if different > 0 {
		return 1
	}
	return 0
}
