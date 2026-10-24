package engine

import (
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
	"time"
)

// DECISIONS §11.50: the network side's system user remotix — preflight, certification,
// post-upgrade report, uninstall --purge.

// ⭐ 16 Oct 2026 (rxtest installer --tests interrupt, debian13): a failed installation is rolled
// back with purge, and the system user remotix the packages' scripts made goes with them; a
// person's account called remotix is never touched.
func TestRollbackDropsTheNewNetUser(t *testing.T) {
	t.Run("system user removed", func(t *testing.T) {
		root := t.TempDir()
		prepareMachine(t, root)
		env := fakeEnvironment(root)
		var calls []string
		env.Run = fakeAccountsRun(root, &calls)
		appendTo(t, filepath.Join(root, "etc/passwd"), sysRemotix)
		appendTo(t, filepath.Join(root, "etc/group"), "remotix:x:990:\n")
		if err := dropNewNetUser(&Context{Env: env, Purge: true}); err != nil {
			t.Fatal(err)
		}
		if _, ok := ReadAccount(env, NetUser); ok {
			t.Fatal("the user remotix is still in /etc/passwd")
		}
		if strings.Join(calls, ";") != "userdel remotix" {
			t.Fatalf("commands: %q", calls)
		}
	})
	t.Run("a person's account stays", func(t *testing.T) {
		root := t.TempDir()
		prepareMachine(t, root)
		env := fakeEnvironment(root)
		var calls []string
		env.Run = fakeAccountsRun(root, &calls)
		appendTo(t, filepath.Join(root, "etc/passwd"), "remotix:x:1005:1005::/home/remotix:/bin/bash\n")
		if err := dropNewNetUser(&Context{Env: env, Purge: true}); err != nil {
			t.Fatal(err)
		}
		if _, ok := ReadAccount(env, NetUser); !ok || len(calls) != 0 {
			t.Fatalf("a person's account was touched: %q", calls)
		}
	})
}

const sysRemotix = "remotix:x:990:990:REMOTIX network side:/:/usr/sbin/nologin\n"

func appendTo(t *testing.T, f, line string) {
	t.Helper()
	b, err := os.ReadFile(f)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(f, append(b, line...), 0o644); err != nil {
		t.Fatal(err)
	}
}

// fakeAccountsRun: userdel/groupdel/useradd/groupadd on the fake machine's /etc/passwd and /etc/group.
func fakeAccountsRun(root string, calls *[]string) Executor {
	return func(_ time.Duration, name string, args ...string) (string, int, error) {
		*calls = append(*calls, name+" "+strings.Join(args, " "))
		user := args[len(args)-1]
		drop := func(f string) {
			b, _ := os.ReadFile(filepath.Join(root, f))
			var keep []string
			for _, l := range strings.Split(strings.TrimSuffix(string(b), "\n"), "\n") {
				if !strings.HasPrefix(l, user+":") {
					keep = append(keep, l)
				}
			}
			os.WriteFile(filepath.Join(root, f), []byte(strings.Join(keep, "\n")+"\n"), 0o644)
		}
		opt := map[string]string{}
		for i := 0; i+1 < len(args); i++ {
			if strings.HasPrefix(args[i], "-") && !strings.HasPrefix(args[i+1], "-") {
				opt[args[i]] = args[i+1]
			}
		}
		switch name {
		case "userdel":
			drop("etc/passwd")
			drop("etc/group") // USERGROUPS_ENAB yes
		case "groupdel":
			drop("etc/group")
		case "groupadd":
			b, _ := os.ReadFile(filepath.Join(root, "etc/group"))
			os.WriteFile(filepath.Join(root, "etc/group"), append(b, user+":x:"+opt["-g"]+":\n"...), 0o644)
		case "useradd":
			b, _ := os.ReadFile(filepath.Join(root, "etc/passwd"))
			l := strings.Join([]string{user, "x", opt["-u"], opt["-g"], opt["-c"], opt["-d"], opt["-s"]}, ":") + "\n"
			os.WriteFile(filepath.Join(root, "etc/passwd"), append(b, l...), 0o644)
		default:
			return "", -1, ErrNotAllowed
		}
		return "", 0, nil
	}
}

// A person's account named remotix blocks the installation; a system user does not.
func TestPreflightNetUser(t *testing.T) {
	for _, c := range []struct {
		name, line string
		blocks     bool
	}{
		{"absent", "", false},
		{"system user", sysRemotix, false},
		{"person by uid", "remotix:x:1005:1005::/:/usr/sbin/nologin\n", true},
		{"person by shell", "remotix:x:995:995::/:/bin/bash\n", true},
		{"person by home", "remotix:x:995:995::/home/remotix:/usr/sbin/nologin\n", true},
	} {
		t.Run(c.name, func(t *testing.T) {
			root := t.TempDir()
			prepareMachine(t, root)
			os.MkdirAll(filepath.Join(root, "home/remotix"), 0o755)
			appendTo(t, filepath.Join(root, "etc/passwd"), c.line)
			p := Preflight(&Environment{Root: root, Run: noCommand}, PreflightOptions{})
			if got := hasCode(p.Messages, "RX-NETUSER-001"); got != c.blocks {
				t.Fatalf("RX-NETUSER-001 = %v, expected %v (%v)", got, c.blocks, p.Messages)
			}
			if c.blocks && Codes["RX-NETUSER-001"].Severity != BLOCKING {
				t.Fatal("RX-NETUSER-001 must be BLOCKING")
			}
			rap := Evaluate(catalogTest(t), p)
			if hasCode(rap.Messages, "RX-NETUSER-001") != c.blocks {
				t.Fatalf("the compatibility report must carry RX-NETUSER-001 = %v", c.blocks)
			}
		})
	}
}

// netMachine: a fake machine with the 1.5 package's sysusers file and remotix as the test's own uid
// (the files the test makes are the test's: without root they cannot be given to anyone else).
func netMachine(t *testing.T) (string, *Environment) {
	root := t.TempDir()
	prepareMachine(t, root)
	uid, gid := os.Getuid(), os.Getgid()
	appendTo(t, filepath.Join(root, "etc/passwd"), "remotix:x:"+strconv.Itoa(uid)+":"+strconv.Itoa(gid)+":REMOTIX network side:/:/usr/sbin/nologin\n")
	os.WriteFile(filepath.Join(root, "etc/login.defs"), []byte("UID_MIN "+strconv.Itoa(uid+1)+"\n"), 0o644)
	os.MkdirAll(filepath.Join(root, "usr/lib/sysusers.d"), 0o755)
	os.WriteFile(filepath.Join(root, netSysusers[1:]), []byte(`u remotix - "REMOTIX network side" / /usr/sbin/nologin`+"\n"), 0o644)
	os.MkdirAll(filepath.Join(root, NetDir[1:], "certificates"), 0o700)
	os.Chmod(filepath.Join(root, NetDir[1:]), 0o700)
	os.WriteFile(filepath.Join(root, NetDir[1:], "certificates/quic-secret"), []byte("x"), 0o600)
	os.WriteFile(filepath.Join(root, NetDir[1:], "ban"), []byte(""), 0o600)
	return root, &Environment{Root: root, Run: noCommand}
}

// The certification's «network-side» check and the post-upgrade report.
func TestNetworkSideCheck(t *testing.T) {
	t.Run("before 1.5", func(t *testing.T) {
		root := t.TempDir()
		prepareMachine(t, root)
		a := &Environment{Root: root, Run: noCommand}
		if applies, code, _ := NetworkSide(a); applies || code != "" {
			t.Fatalf("without the sysusers file there is nothing to check: %v %q", applies, code)
		}
		if k := checkNetworkSide(a); k.Outcome != "PASS" {
			t.Fatalf("%+v", k)
		}
	})
	t.Run("right", func(t *testing.T) {
		_, a := netMachine(t)
		if applies, code, det := NetworkSide(a); !applies || code != "" {
			t.Fatalf("%v %q %s", applies, code, det)
		}
		k, _, failed := PlatformChecks(a, 7447)
		found := false
		for _, x := range k {
			if x.ID == "network-side" {
				found = x.Outcome == "PASS"
			}
		}
		if !found {
			t.Fatalf("the network-side check must PASS: %+v", k)
		}
		_ = failed // the fake machine has no encoding test: that one fails on its own
	})
	for _, c := range []struct {
		name, code string
		spoil      func(root string)
	}{
		{"user missing", "RX-NETUSER-002", func(root string) {
			b, _ := os.ReadFile(filepath.Join(root, "etc/passwd"))
			s := string(b)
			s = s[:strings.Index(s, "remotix:")]
			os.WriteFile(filepath.Join(root, "etc/passwd"), []byte(s), 0o644)
		}},
		{"a person's account", "RX-NETUSER-001", func(root string) {
			os.WriteFile(filepath.Join(root, "etc/login.defs"), []byte("UID_MIN 0\n"), 0o644)
		}},
		{"net/ missing", "RX-NETUSER-003", func(root string) { os.RemoveAll(filepath.Join(root, NetDir[1:])) }},
		{"net/ open", "RX-NETUSER-003", func(root string) { os.Chmod(filepath.Join(root, NetDir[1:]), 0o755) }},
		{"1.0's ban not moved", "RX-NETUSER-003", func(root string) {
			os.WriteFile(filepath.Join(root, "var/lib/remotix/ban"), nil, 0o600)
		}},
		{"1.0's certificates not moved", "RX-NETUSER-003", func(root string) {
			os.MkdirAll(filepath.Join(root, "var/lib/remotix/certificates"), 0o700)
		}},
		// review 3, F2: an administrator's certificate as links to a target remotix cannot read
		{"a link to an unreadable certificate", "RX-NETUSER-003", func(root string) {
			le := filepath.Join(root, "etc/letsencrypt/live/h")
			os.MkdirAll(le, 0o755)
			os.WriteFile(filepath.Join(le, "privkey.pem"), []byte("k"), 0o000)
			os.Symlink("/etc/letsencrypt/live/h/privkey.pem", filepath.Join(root, NetDir[1:], "certificates/page.key"))
		}},
		// review 3, F6: a 1.0 drop-in pointing the files elsewhere
		{"REMOTIX_OPTIONS --certificates outside net/", "RX-NETUSER-003", func(root string) {
			os.MkdirAll(filepath.Join(root, "etc/remotix/remotix.conf.d"), 0o755)
			os.WriteFile(filepath.Join(root, "etc/remotix/remotix.conf.d/certs.conf"),
				[]byte("REMOTIX_OPTIONS=--name h --certificates /etc/remotix/certs\n"), 0o644)
		}},
		{"REMOTIX_OPTIONS --ban-file= outside net/", "RX-NETUSER-003", func(root string) {
			os.MkdirAll(filepath.Join(root, "etc/remotix/remotix.conf.d"), 0o755)
			os.WriteFile(filepath.Join(root, "etc/remotix/remotix.conf.d/ban.conf"),
				[]byte("REMOTIX_OPTIONS=\"--ban-file=/var/lib/remotix/ban\"\n"), 0o644)
		}},
		{"a dangling link", "RX-NETUSER-003", func(root string) {
			os.Symlink("/etc/letsencrypt/live/gone/privkey.pem", filepath.Join(root, NetDir[1:], "certificates/page.key"))
		}},
	} {
		t.Run(c.name, func(t *testing.T) {
			root, a := netMachine(t)
			c.spoil(root)
			if _, code, det := NetworkSide(a); code != c.code {
				t.Fatalf("code %q (%s), expected %s", code, det, c.code)
			}
			if k := checkNetworkSide(a); k.Outcome != "FAIL" || !k.Requested || !strings.Contains(k.Detail, c.code) {
				t.Fatalf("%+v", k)
			}
		})
	}
	t.Run("REMOTIX_OPTIONS inside net/ or with their own state dir", func(t *testing.T) {
		root, a := netMachine(t)
		os.MkdirAll(filepath.Join(root, "etc/remotix/remotix.conf.d"), 0o755)
		os.WriteFile(filepath.Join(root, "etc/remotix/remotix.conf.d/a.conf"),
			[]byte("REMOTIX_PORT=8531\nREMOTIX_OPTIONS=--certificates /var/lib/remotix/net/c2\n"), 0o644)
		os.WriteFile(filepath.Join(root, "etc/remotix/remotix.conf.d/b.conf"),
			[]byte("REMOTIX_OPTIONS=--network-state-dir /srv/rx --ban-file /srv/rx/ban\n"), 0o644)
		if _, code, det := NetworkSide(a); code != "" {
			t.Fatalf("options inside the state dir must pass: %q %s", code, det)
		}
	})
	t.Run("a link to a readable certificate", func(t *testing.T) {
		root, a := netMachine(t)
		le := filepath.Join(root, "etc/letsencrypt/live/h")
		os.MkdirAll(le, 0o755)
		os.WriteFile(filepath.Join(le, "fullchain.pem"), []byte("c"), 0o644)
		os.Symlink("../../../../../etc/letsencrypt/live/h/fullchain.pem",
			filepath.Join(root, NetDir[1:], "certificates/page.pem"))
		if _, code, det := NetworkSide(a); code != "" {
			t.Fatalf("a readable link target must pass: %q %s", code, det)
		}
	})
	if os.Getuid() == 0 {
		t.Run("not remotix's", func(t *testing.T) {
			root, a := netMachine(t)
			os.Chown(filepath.Join(root, NetDir[1:], "ban"), 4242, 4242)
			if _, code, det := NetworkSide(a); code != "RX-NETUSER-003" || !strings.Contains(det, "/ban 4242:4242") {
				t.Fatalf("%q %s", code, det)
			}
		})
	}
}

// The install plan still starts ONE unit, remotix.service: the split lives inside it (§11.50,
// no second unit to enable), and nothing in the plan names a network unit.
func TestNoSecondUnit(t *testing.T) {
	root := t.TempDir()
	prepareMachine(t, root)
	env := fakeEnvironment(root)
	prof := fakeProfile()
	cat := catalogTest(t)
	p, err := InstallPlan(prof, Evaluate(cat, prof), cat, env, InstallOptions{Pacchetti: singlePackage(t, root), Porta: 7447})
	if err != nil {
		t.Fatal(err)
	}
	services := 0
	for _, a := range p.Azioni {
		if a.Type == "start-service" {
			services++
			if a.Parameters["unit"] != "remotix.service" {
				t.Errorf("start-service on %v", a.Parameters)
			}
		}
		if strings.Contains(string(CanonicalJSON(a)), "remotix-network") {
			t.Errorf("a second unit in the plan: %+v", a)
		}
	}
	if services != 1 {
		t.Fatalf("%d start-service steps, expected 1", services)
	}
}

// uninstall: a plain one keeps the system user and declares it; --purge removes it and its
// group after the packages, never a person's account; the rollback puts it back.
func TestUninstallSystemUser(t *testing.T) {
	t.Run("plain keeps it", func(t *testing.T) {
		b := fakeInstall(t)
		appendTo(t, filepath.Join(b.root, "etc/passwd"), sysRemotix)
		pn, err := b.engine(t).UninstallPlan(fakeProfile(), false)
		if err != nil {
			t.Fatal(err)
		}
		for _, a := range pn.Azioni {
			if a.Type == "remove-system-user" {
				t.Fatalf("a plain uninstallation removes the user: %+v", a)
			}
		}
		if !strings.Contains(strings.Join(pn.Declared, "\n"), "the system user remotix stays") {
			t.Fatalf("the plan must declare the user that stays: %q", pn.Declared)
		}
	})
	t.Run("a person's account is never in the plan", func(t *testing.T) {
		b := fakeInstall(t)
		appendTo(t, filepath.Join(b.root, "etc/passwd"), "remotix:x:1005:1005::/:/bin/bash\n")
		pn, err := b.engine(t).UninstallPlan(fakeProfile(), true)
		if err != nil {
			t.Fatal(err)
		}
		for _, a := range pn.Azioni {
			if a.Type == "remove-system-user" {
				t.Fatalf("a person's account in the purge plan: %+v", a)
			}
		}
	})
	t.Run("purge removes it", func(t *testing.T) {
		b := fakeInstall(t)
		appendTo(t, filepath.Join(b.root, "etc/passwd"), sysRemotix)
		appendTo(t, filepath.Join(b.root, "etc/group"), "remotix:x:990:\n")
		os.MkdirAll(filepath.Join(filepath.Dir(b.operations), "net/certificates"), 0o700)
		e := b.engine(t)
		pn, err := e.UninstallPlan(fakeProfile(), true)
		if err != nil {
			t.Fatal(err)
		}
		at, packages := -1, -1
		for i, a := range pn.Azioni {
			switch {
			case a.Type == "remove-system-user":
				at = i
				if a.Reversibility != BEST_EFFORT || !strings.Contains(a.Description, "uid 990") {
					t.Errorf("%+v", a)
				}
			case a.ID == "undo-packages":
				packages = i
			}
		}
		if at < 0 || packages < 0 || at < packages {
			t.Fatalf("the user is removed AFTER the packages: step %d, packages %d", at, packages)
		}
		pn.Approval = &Approval{Da: "prova", Modo: "da file", DigestPiano: pn.Digest()}
		pd := filepath.Join(t.TempDir(), "uninstall.json")
		WriteJSON(pd, pn)
		var calls []string
		e.Env.Run = fakeAccountsRun(b.root, &calls)
		op, err := e.Apply(pd, false, "prova")
		if err != nil || op.State != CONFIRMED {
			t.Fatalf("uninstallation: %v %v %s", op.State, err, op.lastDetail())
		}
		if _, ok := ReadAccount(e.Env, NetUser); ok {
			t.Fatal("the user remotix is still in /etc/passwd")
		}
		if g, _ := ReadGroups(filepath.Join(b.root, "etc/group")); g["remotix"] != [2]string{} {
			t.Fatal("the group remotix is still in /etc/group")
		}
		if strings.Join(calls, ";") != "userdel remotix" {
			t.Fatalf("commands: %q", calls)
		}
		if _, err := os.Stat(filepath.Join(filepath.Dir(b.operations), "net")); !os.IsNotExist(err) {
			t.Fatalf("--purge: /var/lib/remotix/net is still there (%v)", err)
		}
	})
	t.Run("rollback puts it back", func(t *testing.T) {
		root := t.TempDir()
		prepareMachine(t, root)
		appendTo(t, filepath.Join(root, "etc/passwd"), sysRemotix)
		appendTo(t, filepath.Join(root, "etc/group"), "remotix:x:990:\n")
		var calls []string
		env := fakeEnvironment(root)
		env.Run = fakeAccountsRun(root, &calls)
		ap, ok := PlanRemoveSystemUser(env, "system-user")
		if !ok {
			t.Fatal("no step for a system user")
		}
		a, _ := NewAction(ap)
		c := &Context{Env: env, Folder: t.TempDir(), P: ap}
		before, origin, err := a.Snapshot(c)
		if err != nil || origin != DIRECT {
			t.Fatalf("%v %v", origin, err)
		}
		if err := a.Do(c, before); err != nil {
			t.Fatal(err)
		}
		if e, _, _ := a.Check(c, before); e != COMPLETE {
			t.Fatalf("after Do: %v", e)
		}
		if err := a.Do(c, before); err != nil { // idempotent
			t.Fatal(err)
		}
		if err := a.Rollback(c, before); err != nil {
			t.Fatal(err)
		}
		if ok, det, _ := a.RolledBack(c, before); !ok {
			t.Fatalf("not back: %s (%q)", det, calls)
		}
		u, _ := ReadAccount(env, NetUser)
		if u.Uid != 990 || u.Gid != 990 || u.Home != "/" || u.Shell != "/usr/sbin/nologin" {
			t.Fatalf("put back as %+v", u)
		}
	})
}

// ⭐ lane 1, 16 Oct 2026: a --page the network side cannot read is RX-NETUSER-003 (the root side
// refuses to start with it): under /tmp, or a file remotix (uid 990, no group) cannot read; the
// package's page, readable by everyone, passes.
func TestNetPageUnreadable(t *testing.T) {
	root := t.TempDir()
	prepareMachine(t, root)
	env := fakeEnvironment(root)
	conf := filepath.Join(root, "etc/remotix/remotix.conf.d")
	if err := os.MkdirAll(conf, 0o755); err != nil {
		t.Fatal(err)
	}
	pub := filepath.Join(root, "opt/rx/page.html")
	priv := filepath.Join(root, "opt/rx/private.html")
	if err := os.MkdirAll(filepath.Dir(pub), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(pub, []byte("x"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(priv, []byte("x"), 0o600); err != nil {
		t.Fatal(err)
	}
	cases := []struct {
		opt  string
		want bool
	}{
		{"--page /opt/rx/page.html", false},
		{"--page=/opt/rx/page.html", false},
		{"--page /tmp/page.html", true},
		{"--page /opt/rx/private.html", true},
		{"--page /opt/rx/missing.html", true},
	}
	for _, c := range cases {
		line := "REMOTIX_OPTIONS=\"--verbose " + c.opt + "\"\n"
		if err := os.WriteFile(filepath.Join(conf, "10-page.conf"), []byte(line), 0o644); err != nil {
			t.Fatal(err)
		}
		bad := netPageUnreadable(env, 990, 990)
		if (len(bad) > 0) != c.want {
			t.Errorf("%s: flagged %v, want %v (%q)", c.opt, len(bad) > 0, c.want, bad)
		}
	}
}
