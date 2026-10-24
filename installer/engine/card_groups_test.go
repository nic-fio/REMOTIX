package engine

import (
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

// fakeNodes: the /dev/dri of a fake machine, each node with the gid a real distribution gives it
// (nodeGid is replaced for the test: the files themselves carry the gid of whoever runs the test).
func fakeNodes(t *testing.T, root string, gids map[string]uint32) {
	t.Helper()
	d := filepath.Join(root, "dev/dri")
	os.MkdirAll(d, 0o755)
	byPath := map[string]uint32{}
	for n, g := range gids {
		p := filepath.Join(d, n)
		if err := os.WriteFile(p, nil, 0o660); err != nil {
			t.Fatal(err)
		}
		byPath[p] = g
	}
	old := nodeGid
	nodeGid = func(fpath string) (uint32, bool) {
		g, ok := byPath[fpath]
		return g, ok
	}
	t.Cleanup(func() { nodeGid = old })
}

func writeGroup(t *testing.T, root, content string) {
	t.Helper()
	os.MkdirAll(filepath.Join(root, "etc"), 0o755)
	if err := os.WriteFile(filepath.Join(root, "etc/group"), []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}

// DECISIONS §11.38: the installer enrols in the render nodes' group only, like the product's
// first-login enrolment — card* (group «video») is not looked at; the group is the node's real one.
func TestCardGroupsRenderOnly(t *testing.T) {
	cases := []struct {
		name  string
		group string
		nodes map[string]uint32
		want  []string
	}{
		{"Debian/Ubuntu/Fedora: card0 in video, renderD128 in render",
			"root:x:0:\nvideo:x:44:\nrender:x:991:\n",
			map[string]uint32{"card0": 44, "renderD128": 991}, []string{"render"}},
		{"two cards, the same group, counted once",
			"root:x:0:\nvideo:x:44:\nrender:x:991:\n",
			map[string]uint32{"card0": 44, "card1": 44, "renderD128": 991, "renderD129": 991}, []string{"render"}},
		{"a distribution where the render node's group has another name",
			"root:x:0:\nvideo:x:44:\ngpu:x:507:\n",
			map[string]uint32{"card0": 44, "renderD128": 507}, []string{"gpu"}},
		{"a distribution that gives the render node to video",
			"root:x:0:\nvideo:x:44:\n",
			map[string]uint32{"card0": 44, "renderD128": 44}, []string{"video"}},
		{"a render node owned by root: nobody to add",
			"root:x:0:\nvideo:x:44:\n",
			map[string]uint32{"card0": 44, "renderD128": 0}, nil},
		{"no render node at all (only card0)",
			"root:x:0:\nvideo:x:44:\nrender:x:991:\n",
			map[string]uint32{"card0": 44}, nil},
		{"a gid with no name in /etc/group is skipped",
			"root:x:0:\nvideo:x:44:\n",
			map[string]uint32{"card0": 44, "renderD128": 4321}, nil},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			root := t.TempDir()
			writeGroup(t, root, c.group)
			fakeNodes(t, root, c.nodes)
			if got := CardGroups(fakeEnvironment(root)); !reflect.DeepEqual(got, c.want) {
				t.Errorf("CardGroups = %v, want %v", got, c.want)
			}
		})
	}
	// a machine without /dev/dri at all
	root := t.TempDir()
	writeGroup(t, root, "root:x:0:\nvideo:x:44:\nrender:x:991:\n")
	if got := CardGroups(fakeEnvironment(root)); len(got) != 0 {
		t.Errorf("without /dev/dri: %v", got)
	}
}

// The plan follows: the people of the machine get one add-user-to-group step for render, none for
// video; with no render node the plan says that nobody is added.
func TestInstallPlanGroupsRenderOnly(t *testing.T) {
	for _, withNode := range []bool{true, false} {
		root := t.TempDir()
		prepareMachine(t, root)
		nodes := map[string]uint32{"card0": 44}
		if withNode {
			nodes["renderD128"] = 991
		}
		fakeNodes(t, root, nodes)
		env := fakeEnvironment(root)
		prof := fakeProfile()
		cat := catalogTest(t)
		p, err := InstallPlan(prof, Evaluate(cat, prof), cat, env, InstallOptions{Pacchetti: singlePackage(t, root), Porta: 7447})
		if err != nil {
			t.Fatal(err)
		}
		var groups []string
		for _, a := range p.Azioni {
			if a.Type == "add-user-to-group" {
				groups = append(groups, a.ID)
			}
		}
		none := false
		for _, m := range p.NotDone {
			none = none || m.Testo == T("np.nessun_gruppo")
		}
		if withNode {
			if !reflect.DeepEqual(groups, []string{"group-prova-render", "group-altro-render"}) &&
				!reflect.DeepEqual(groups, []string{"group-altro-render", "group-prova-render"}) {
				t.Errorf("with renderD128: group steps %v", groups)
			}
			for _, g := range groups {
				if strings.HasSuffix(g, "-video") {
					t.Errorf("a video step: %s", g)
				}
			}
			if none {
				t.Errorf("np.nessun_gruppo with a render node")
			}
		} else if len(groups) != 0 || !none {
			t.Errorf("without renderD*: steps %v, «nobody to add» %v", groups, none)
		}
	}
}
