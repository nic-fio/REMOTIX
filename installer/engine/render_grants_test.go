package engine

import (
	"os"
	"path/filepath"
	"testing"
)

// grantsInstall: the fake installation, plus what the product leaves when a REMOTIX desktop was
// born for a stale user manager (src/render_grant.c): a render node whose ACL carries the private
// group of «altro» (gid 4242) — and an entry of the administrator's (gid 77) that is not REMOTIX's —
// and the record /var/lib/remotix/render-grants.
func grantsInstall(t *testing.T) (*bench, string) {
	b := fakeInstall(t)
	node := filepath.Join(b.root, "dev/dri/renderD128")
	os.MkdirAll(filepath.Dir(node), 0o755)
	os.WriteFile(node, nil, 0o660)
	ents, err := aclRead(node)
	if err != nil {
		t.Fatal(err)
	}
	ents = append(ents, aclEntry{aclGroup, 6, 4242}, aclEntry{aclGroup, 4, 77})
	if err := aclWrite(node, ents); err != nil {
		t.Skipf("this filesystem does not take ACLs (%v)", err)
	}
	os.WriteFile(filepath.Join(filepath.Dir(b.operations), RenderGrantsFile), []byte("1001 4242 altro\n"), 0o600)
	return b, node
}

func groupsOn(t *testing.T, node string) map[uint32]bool {
	t.Helper()
	ents, err := aclRead(node)
	if err != nil {
		t.Fatal(err)
	}
	r := map[uint32]bool{}
	for _, e := range ents {
		if e.Tag == aclGroup {
			r[e.Id] = true
		}
	}
	return r
}

// ⭐ 1.5 (DECISIONS §11.4): the uninstallation removes the recorded grant and the record, and leaves
// the administrator's entry alone.
func TestUninstallRemovesRenderGrants(t *testing.T) {
	b, node := grantsInstall(t)
	pn, err := b.engine(t).UninstallPlan(fakeProfile(), false)
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, a := range pn.Azioni {
		found = found || a.Type == "remove-render-grants"
	}
	if !found {
		t.Fatal("the plan has no remove-render-grants step")
	}
	pn.Approval = &Approval{Da: "prova", Modo: "da file", DigestPiano: pn.Digest()}
	p := filepath.Join(t.TempDir(), "d.json")
	WriteJSON(p, pn)
	op, err := b.engine(t).Apply(p, false, "prova")
	if err != nil || op.State != CONFIRMED {
		t.Fatalf("%v %v %s", op.State, err, op.lastDetail())
	}
	g := groupsOn(t, node)
	if g[4242] || !g[77] {
		t.Fatalf("groups on the node after: %v (expected 77 only)", g)
	}
	if _, err := os.Stat(filepath.Join(filepath.Dir(b.operations), RenderGrantsFile)); !os.IsNotExist(err) {
		t.Fatalf("the record is still there (%v)", err)
	}
}

// Cancelled after the step, the grant and the record come back as they were.
func TestUninstallCancelledPutsGrantsBack(t *testing.T) {
	b, node := grantsInstall(t)
	pn, err := b.engine(t).UninstallPlan(fakeProfile(), false)
	if err != nil {
		t.Fatal(err)
	}
	pn.Approval = &Approval{Da: "prova", Modo: "da file", DigestPiano: pn.Digest()}
	p := filepath.Join(t.TempDir(), "d.json")
	WriteJSON(p, pn)
	killAt(t, b.root, b.operations, p, "applica", "dopo-fatta@render-grants")
	if g := groupsOn(t, node); g[4242] {
		t.Fatal("killed after the step, the grant should be gone")
	}
	if _, err := b.engine(t).Rollback(); err != nil {
		t.Fatal(err)
	}
	if g := groupsOn(t, node); !g[4242] || !g[77] {
		t.Fatalf("groups on the node after the rollback: %v (expected 4242 and 77)", g)
	}
	if b, _ := os.ReadFile(filepath.Join(filepath.Dir(b.operations), RenderGrantsFile)); string(b) != "1001 4242 altro\n" {
		t.Fatalf("the record after the rollback: %q", b)
	}
}

func TestParseRenderGrants(t *testing.T) {
	g := parseRenderGrants("1001 4242 altro\n\nbad line\n1002 0 root\n1003 x y\n1004 4243 u2\n")
	if len(g) != 2 || g[0] != (renderGrant{1001, 4242, "altro"}) || g[1].Gid != 4243 {
		t.Fatalf("%+v", g)
	}
}
