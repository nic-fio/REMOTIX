package engine

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// DesktopCard: one graphics card of this machine as REMOTIX sees it (DECISIONS §11.37 addendum, 27 Oct 2026).
type DesktopCard struct {
	Node    string // /dev/dri/renderD128; "" = the card has NO render node (an ASPEED service card, say)
	PCI     string // 0000:03:00.0
	Driver  string
	BootVGA bool // the BIOS primary card (sysfs boot_vga = 1)
}

// DesktopCards: the machine's cards in PCI-address order, and the index of the one REMOTIX gives the desktop
// (labwc, KWin's host, and the encoder's fallback) with the product's rule (src/card_pick.c): the BIOS primary
// card if it has a render node, otherwise the card with the lowest PCI address that has one. ⚠ The installer
// cannot run the product's card_can_draw() (it creates a buffer on the card): «capable» here means «has a render
// node»; the final check is the service's, in its log. chosen = -1: no card with a render node.
func DesktopCards(a *Environment) (cards []DesktopCard, chosen int, why string) {
	seen := map[string]int{}
	entries, _ := filepath.Glob(a.P("/sys/class/drm") + "/*")
	sort.Strings(entries)
	for _, v := range entries {
		base := filepath.Base(v)
		isRender := strings.HasPrefix(base, "renderD")
		if !isRender && !(strings.HasPrefix(base, "card") && !strings.Contains(base, "-")) {
			continue
		}
		l, err := os.Readlink(filepath.Join(v, "device"))
		if err != nil {
			continue
		}
		pci := filepath.Base(l)
		i, ok := seen[pci]
		if !ok {
			i = len(cards)
			seen[pci] = i
			c := DesktopCard{PCI: pci}
			if d, err := os.Readlink(filepath.Join(v, "device", "driver")); err == nil {
				c.Driver = filepath.Base(d)
			}
			cards = append(cards, c)
		}
		if isRender {
			cards[i].Node = "/dev/dri/" + base
		}
		if b, err := os.ReadFile(filepath.Join(v, "device", "boot_vga")); err == nil && strings.TrimSpace(string(b)) == "1" {
			cards[i].BootVGA = true
		}
	}
	sort.SliceStable(cards, func(i, j int) bool { return cards[i].PCI < cards[j].PCI })
	chosen = -1
	primary := -1
	for i, c := range cards {
		if c.BootVGA {
			primary = i
		}
	}
	if primary >= 0 && cards[primary].Node != "" {
		return cards, primary, "it is the BIOS primary card"
	}
	for i, c := range cards {
		if c.Node != "" {
			if primary >= 0 {
				return cards, i, fmt.Sprintf("the BIOS primary card %s has no render node, so the first card with one by PCI address", cards[primary].PCI)
			}
			return cards, i, "no BIOS primary card is reported, so the first card by PCI address"
		}
	}
	return cards, -1, ""
}

// DesktopCardsText: the lines for `check` and the install plan; "" on a machine with one card (nothing changes there).
func DesktopCardsText(a *Environment) string {
	cards, chosen, why := DesktopCards(a)
	if len(cards) < 2 {
		return ""
	}
	var b strings.Builder
	for i, c := range cards {
		node := c.Node
		if node == "" {
			node = "no render node"
		}
		driver := c.Driver
		if driver == "" {
			driver = "?"
		}
		mark := ""
		if i == chosen {
			mark = "  <- REMOTIX uses this one"
		}
		fmt.Fprintf(&b, "%s (%s, driver %s%s)%s; ", node, c.PCI, driver, map[bool]string{true: ", BIOS primary"}[c.BootVGA], mark)
	}
	list := strings.TrimSuffix(b.String(), "; ")
	if chosen < 0 {
		return T("cards.none", list)
	}
	return T("cards.list", list, cards[chosen].Node, why)
}
