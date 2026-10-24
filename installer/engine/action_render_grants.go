package engine

import (
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"syscall"
)

// remove-render-grants (1.5, DECISIONS §11.4): REMOTIX gives a user's private group an ACL on
// /dev/dri/renderD* when that user's manager was born before the card groups (src/render_grant.c),
// and records it in /var/lib/remotix/render-grants («uid gid user» per line). The product takes it
// back when the desktop ends and at its own start-up; but a service stopped for good — the
// uninstallation — never starts again, and a grant left behind would outlive the account
// (`[M]` 13 Oct 2026: `userdel` left `group:1001:rw-`). So the uninstallation removes them: after
// the sessions are closed, every recorded gid out of every render node's ACL, then the record.
// EXACT reversibility: cancelled, the entries and the record are put back as they were (the product's
// start-up sweep then removes those whose desktop is gone).

func init() { registerType("remove-render-grants", newRemoveRenderGrants) }

// RenderGrantsFile: the product's record, next to the enrolments.
const RenderGrantsFile = "render-grants"

const driDir = "/dev/dri"

type renderGrant struct {
	Uid  uint32 `json:"uid"`
	Gid  uint32 `json:"gid"`
	User string `json:"user"`
}

// RenderGrants: the grants recorded by the product now.
func (m *Engine) RenderGrants() []renderGrant {
	b, err := os.ReadFile(filepath.Join(filepath.Dir(m.Folder), RenderGrantsFile))
	if err != nil {
		return nil
	}
	return parseRenderGrants(string(b))
}

func parseRenderGrants(s string) []renderGrant {
	var r []renderGrant
	for _, line := range strings.Split(s, "\n") {
		f := strings.Fields(line)
		if len(f) != 3 {
			continue
		}
		u, e1 := strconv.ParseUint(f[0], 10, 32)
		g, e2 := strconv.ParseUint(f[1], 10, 32)
		if e1 != nil || e2 != nil || g == 0 {
			continue
		}
		r = append(r, renderGrant{uint32(u), uint32(g), f[2]})
	}
	return r
}

// PlanRemoveRenderGrants prepares the plan's step, with the grants found at planning time.
func PlanRemoveRenderGrants(id string, grants []renderGrant) PlanAction {
	var names []string
	for _, g := range grants {
		names = append(names, fmt.Sprintf("%s (gid %d)", g.User, g.Gid))
	}
	if len(names) == 0 {
		names = append(names, T("az.grant.nessuna"))
	}
	return PlanAction{
		ID: id, Type: "remove-render-grants",
		Parameters:    map[string]string{},
		Description:   T("az.grant", strings.Join(names, ", ")),
		ComeSiFa:      T("az.grant.fa"),
		HowToVerify:   T("az.grant.verifica"),
		HowToUndo:     T("az.grant.annulla"),
		Reversibility: EXACT,
	}
}

type removeRenderGrants struct{}

func newRemoveRenderGrants(PlanAction) (Action, error) { return &removeRenderGrants{}, nil }

type beforeRenderGrants struct {
	Origine Origine `json:"origin"`
	Record  string  `json:"record,omitempty"`
	// the gids of the record that each node had in its ACL
	Nodes map[string][]uint32 `json:"nodes,omitempty"`
}

func (t *removeRenderGrants) Constraints(*Context) ([]string, error) { return nil, nil }

func recordPath(c *Context) string {
	return filepath.Join(filepath.Dir(filepath.Dir(c.Folder)), RenderGrantsFile)
}

func renderNodes(a *Environment) []string {
	m, _ := filepath.Glob(a.P(driDir + "/renderD*"))
	var r []string
	for _, p := range m {
		if st, err := os.Lstat(p); err == nil && st.Mode()&os.ModeCharDevice != 0 {
			r = append(r, p)
		} else if err == nil && st.Mode().IsRegular() && a.Root != "/" && a.Root != "" {
			r = append(r, p) // the tests' fake machine has files in place of the devices
		}
	}
	sort.Strings(r)
	return r
}

func (t *removeRenderGrants) Snapshot(c *Context) (json.RawMessage, Origine, error) {
	p := beforeRenderGrants{Origine: PREEXISTING, Nodes: map[string][]uint32{}}
	b, err := os.ReadFile(recordPath(c))
	if err != nil {
		if os.IsNotExist(err) {
			return jsonDi(p), PREEXISTING, nil
		}
		return nil, "", err
	}
	p.Record = string(b)
	grants := parseRenderGrants(p.Record)
	for _, n := range renderNodes(c.Env) {
		ents, err := aclRead(n)
		if err != nil {
			return nil, "", err
		}
		for _, g := range grants {
			if aclHasGroup(ents, g.Gid) {
				p.Nodes[n] = append(p.Nodes[n], g.Gid)
			}
		}
	}
	p.Origine = DIRECT
	return jsonDi(p), DIRECT, nil
}

func (t *removeRenderGrants) load(before json.RawMessage) (beforeRenderGrants, error) {
	var p beforeRenderGrants
	err := json.Unmarshal(before, &p)
	return p, err
}

// Do removes the recorded gids from every render node, then the record. Idempotent.
func (t *removeRenderGrants) Do(c *Context, before json.RawMessage) error {
	p, err := t.load(before)
	if err != nil || p.Origine == PREEXISTING {
		return err
	}
	for n, gids := range p.Nodes {
		for _, g := range gids {
			if err := aclRemoveGroup(n, g); err != nil && !os.IsNotExist(err) {
				return err
			}
		}
	}
	if err := os.Remove(recordPath(c)); err != nil && !os.IsNotExist(err) {
		return err
	}
	return nil
}

func (t *removeRenderGrants) Check(c *Context, before json.RawMessage) (Outcome, string, error) {
	p, err := t.load(before)
	if err != nil {
		return "", "", err
	}
	if p.Origine == PREEXISTING {
		return COMPLETE, T("az.grant.nessuna"), nil
	}
	left, total := t.left(p)
	_, errRec := os.Stat(recordPath(c))
	switch {
	case left == 0 && os.IsNotExist(errRec):
		return COMPLETE, T("az.grant.tolte"), nil
	case left == total && errRec == nil:
		return ABSENT, T("az.grant.ancora", left), nil
	}
	return A_META, T("az.grant.ancora", left), nil
}

// left: how many (node, gid) pairs of the snapshot are still in the ACLs, out of how many.
func (t *removeRenderGrants) left(p beforeRenderGrants) (int, int) {
	left, total := 0, 0
	for n, gids := range p.Nodes {
		ents, err := aclRead(n)
		for _, g := range gids {
			total++
			if err == nil && aclHasGroup(ents, g) {
				left++
			}
		}
	}
	return left, total
}

func (t *removeRenderGrants) Rollback(c *Context, before json.RawMessage) error {
	p, err := t.load(before)
	if err != nil || p.Origine == PREEXISTING {
		return err
	}
	for n, gids := range p.Nodes {
		ents, err := aclRead(n)
		if err != nil {
			if os.IsNotExist(err) {
				continue // the device is gone: nothing to put back on it
			}
			return err
		}
		for _, g := range gids {
			if !aclHasGroup(ents, g) {
				ents = append(ents, aclEntry{aclGroup, 6, g})
			}
		}
		if err := aclWrite(n, ents); err != nil {
			return err
		}
	}
	return WriteAtomic(recordPath(c), []byte(p.Record), 0o600)
}

func (t *removeRenderGrants) RolledBack(c *Context, before json.RawMessage) (bool, string, error) {
	p, err := t.load(before)
	if err != nil {
		return false, "", err
	}
	if p.Origine == PREEXISTING {
		return true, T("az.grant.nessuna"), nil
	}
	left, total := t.left(p)
	b, errRec := os.ReadFile(recordPath(c))
	ok := left == total && errRec == nil && string(b) == p.Record
	if ok {
		return true, T("az.grant.rimesse"), nil
	}
	return false, T("az.grant.non_rimesse"), nil
}

// --- the ACL, read and written as the kernel stores it (system.posix_acl_access): a 4-byte
// version (2), then 8-byte entries {tag, perm, id}, little endian, sorted by tag and id; the mask
// is the union of the group class. The same format as src/render_grant.c: no setfacl, no libacl.

const (
	aclXattr     = "system.posix_acl_access"
	aclVersion   = 2
	aclUserObj   = 0x01
	aclUser      = 0x02
	aclGroupObj  = 0x04
	aclGroup     = 0x08
	aclMask      = 0x10
	aclOther     = 0x20
	aclUndefined = 0xFFFFFFFF
)

type aclEntry struct {
	Tag, Perm uint16
	Id        uint32
}

func aclRead(path string) ([]aclEntry, error) {
	buf := make([]byte, 4+8*64)
	n, err := syscall.Getxattr(path, aclXattr, buf)
	if err != nil {
		if errors.Is(err, syscall.ENODATA) {
			st, e := os.Stat(path)
			if e != nil {
				return nil, e
			}
			m := uint16(st.Mode().Perm())
			return []aclEntry{{aclUserObj, (m >> 6) & 7, aclUndefined}, {aclGroupObj, (m >> 3) & 7, aclUndefined},
				{aclOther, m & 7, aclUndefined}}, nil
		}
		if errors.Is(err, syscall.ENOENT) {
			return nil, os.ErrNotExist
		}
		return nil, err
	}
	if n < 4 || (n-4)%8 != 0 || binary.LittleEndian.Uint32(buf) != aclVersion {
		return nil, fmt.Errorf("%s: ACL in an unknown format", path)
	}
	var r []aclEntry
	for off := 4; off < n; off += 8 {
		r = append(r, aclEntry{binary.LittleEndian.Uint16(buf[off:]), binary.LittleEndian.Uint16(buf[off+2:]),
			binary.LittleEndian.Uint32(buf[off+4:])})
	}
	return r, nil
}

func aclHasGroup(ents []aclEntry, gid uint32) bool {
	for _, e := range ents {
		if e.Tag == aclGroup && e.Id == gid {
			return true
		}
	}
	return false
}

func aclWrite(path string, ents []aclEntry) error {
	var unite uint16
	named, mask := false, -1
	for i, e := range ents {
		if e.Tag == aclGroupObj || e.Tag == aclUser || e.Tag == aclGroup {
			unite |= e.Perm
		}
		if e.Tag == aclUser || e.Tag == aclGroup {
			named = true
		}
		if e.Tag == aclMask {
			mask = i
		}
	}
	if mask < 0 && named {
		ents = append(ents, aclEntry{aclMask, 0, aclUndefined})
		mask = len(ents) - 1
	}
	if mask >= 0 {
		ents[mask].Perm = unite
	}
	sort.Slice(ents, func(i, j int) bool {
		if ents[i].Tag != ents[j].Tag {
			return ents[i].Tag < ents[j].Tag
		}
		return ents[i].Id < ents[j].Id
	})
	buf := make([]byte, 4+8*len(ents))
	binary.LittleEndian.PutUint32(buf, aclVersion)
	for i, e := range ents {
		binary.LittleEndian.PutUint16(buf[4+8*i:], e.Tag)
		binary.LittleEndian.PutUint16(buf[4+8*i+2:], e.Perm)
		binary.LittleEndian.PutUint32(buf[4+8*i+4:], e.Id)
	}
	return syscall.Setxattr(path, aclXattr, buf, 0)
}

func aclRemoveGroup(path string, gid uint32) error {
	ents, err := aclRead(path)
	if err != nil {
		return err
	}
	var keep []aclEntry
	for _, e := range ents {
		if !(e.Tag == aclGroup && e.Id == gid) {
			keep = append(keep, e)
		}
	}
	if len(keep) == len(ents) {
		return nil
	}
	return aclWrite(path, keep)
}
