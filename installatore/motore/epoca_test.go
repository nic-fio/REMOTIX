package motore

import (
	"encoding/json"
	"strings"
	"testing"
	"time"
)

// rpmFake: an rpm database answering «rpm -q --qf» the way rpm does — it expands %{NAME},
// %{VERSION}, %{RELEASE}, %{ARCH} and the conditional %|EPOCH?{%{EPOCH}:}|, which prints nothing
// for a package without an epoch. The other commands (rpm -qa, zypper verify) answer «all fine».
func rpmFake(db map[string][3]string) func(time.Duration, string, ...string) (string, int, error) {
	return func(_ time.Duration, label_name string, arg ...string) (string, int, error) {
		if label_name != "rpm" || len(arg) < 3 || arg[0] != "-q" || arg[1] != "--qf" {
			return "", 0, nil
		}
		var b strings.Builder
		for _, n := range arg[3:] {
			p, ok := db[n]
			if !ok {
				b.WriteString("package " + n + " is not installed\n")
				continue
			}
			epoch := ""
			if p[0] != "" {
				epoch = p[0] + ":"
			}
			r := strings.NewReplacer("%|EPOCH?{%{EPOCH}:}|", epoch, "%{EPOCH}", p[0], "%{NAME}", n,
				"%{VERSION}", p[1], "%{RELEASE}", p[2], "%{ARCH}", "x86_64", `\n`, "\n")
			b.WriteString(r.Replace(arg[2]))
		}
		return b.String(), 0, nil
	}
}

// The RPM epoch (Fedora, Alma, openSUSE): dnf and zypper resolve «1:1.7.0-9.fc44»; the check must
// read the installed one with its epoch, or every package that has one stays «missing» —
// `[M]` installa-91, fedora44: «packages: HALF_DONE 104 of 112», the 8 being libglvnd ×4,
// libogg, libtheora, libvisual, libvorbis.
func TestEpochRpm(t *testing.T) {
	db := map[string][3]string{
		"libglvnd":     {"1", "1.7.0", "9.fc44"},
		"libglvnd-egl": {"1", "1.7.0", "9.fc44"},
		"libogg":       {"2", "1.3.6", "2.fc44"},
		"libvorbis":    {"1", "1.3.7", "14.fc44"},
		"nettle":       {"", "3.10.1", "1.fc44"},
		"zlib-ng":      {"0", "2.2.4", "3.fc44"},
	}
	together := []Artifact{
		{Name: "libglvnd", Version: "1:1.7.0-9.fc44", Outcome: "new"},
		{Name: "libglvnd-egl", Version: "1:1.7.0-9.fc44", Outcome: "new"},
		{Name: "libogg", Version: "2:1.3.6-2.fc44", Outcome: "new"},
		{Name: "libvorbis", Version: "1:1.3.7-14.fc44", Outcome: "new"},
		{Name: "nettle", Version: "3.10.1-1.fc44", Outcome: "new"},
		{Name: "zlib-ng", Version: "2.2.4-3.fc44", Outcome: "new"},
	}
	for _, fam := range []string{"fedora", "suse"} {
		a := &Environment{Root: t.TempDir(), Family: fam, Run: rpmFake(db)}
		a.Packets = ChooseHandler(a, fam)

		v, err := a.Packets.Versions([]string{"libglvnd", "nettle", "zlib-ng", "absent"})
		if err != nil {
			t.Fatal(err)
		}
		for n, expected_val := range map[string]string{"libglvnd": "1:1.7.0-9.fc44", "nettle": "3.10.1-1.fc44", "zlib-ng": "0:2.2.4-3.fc44", "absent": ""} {
			if v[n] != expected_val {
				t.Errorf("%s: %s installed as %q, want %q", fam, n, v[n], expected_val)
			}
		}

		before, _ := json.Marshal(beforePackets{Origin: DIRECT, Handler: a.Packets.Name(), ResolvedSet: together})
		c := &Context{Amb: a, Folder: t.TempDir() + "/ops/op1"}
		es, det, err := (&packets{}).Verify(c, before)
		if err != nil || es != COMPLETE {
			t.Errorf("%s: every package at the resolved version: %s %q %v, want COMPLETE", fam, es, det, err)
		}

		// a different epoch is a different version: an older epoch is not complete
		prior := map[string][3]string{}
		for k, x := range db {
			prior[k] = x
		}
		prior["libogg"] = [3]string{"1", "1.3.6", "2.fc44"}
		a.Run = rpmFake(prior)
		if es, det, _ := (&packets{}).Verify(c, before); es != A_META || det != "5 of 6" {
			t.Errorf("%s: libogg at an older epoch: %s %q, want HALF_DONE 5 of 6", fam, es, det)
		}
	}
}

func TestSameVersion(t *testing.T) {
	for _, c := range []struct {
		a, b string
		ok   bool
	}{
		{"1:1.7.0-9.fc44", "1:1.7.0-9.fc44", true},
		{"0:2.2.4-3", "2.2.4-3", true},
		{"1.7.0-9.fc44", "1:1.7.0-9.fc44", false},
		{"2:1.3.6-2", "1:1.3.6-2", false},
	} {
		if versionEqual(c.a, c.b) != c.ok {
			t.Errorf("versionEqual(%q, %q) = %v", c.a, c.b, !c.ok)
		}
	}
}
