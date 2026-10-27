package engine

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// fakeSysCards: /sys/class/drm of a fake machine. cards: entry (renderD129, card0) → "pci:driver:boot" (boot = 1/0/-)
func fakeSysCards(t *testing.T, root string, cards map[string]string) {
	t.Helper()
	for entry, spec := range cards {
		f := strings.Split(spec, ":")
		// the PCI address contains colons: pci = first 3 fields joined
		pci := strings.Join(f[:3], ":")
		driver, boot := f[3], f[4]
		dev := filepath.Join(root, "pci", pci)
		os.MkdirAll(dev, 0o755)
		os.MkdirAll(filepath.Join(root, "drivers", driver), 0o755)
		os.Symlink(filepath.Join(root, "drivers", driver), filepath.Join(dev, "driver"))
		if boot != "-" {
			os.WriteFile(filepath.Join(dev, "boot_vga"), []byte(boot+"\n"), 0o644)
		}
		e := filepath.Join(root, "sys/class/drm", entry)
		os.MkdirAll(e, 0o755)
		os.Symlink(dev, filepath.Join(e, "device"))
	}
}

func TestDesktopCardsRule(t *testing.T) {
	cases := []struct {
		name   string
		cards  map[string]string
		node   string // the chosen node, "" = none
		reason string
	}{
		{"BIOS primary card wins over the lower PCI address",
			map[string]string{"renderD128": "0000:00:02.0:i915:0", "renderD129": "0000:03:00.0:amdgpu:1"},
			"/dev/dri/renderD129", "BIOS primary"},
		{"swapped node names: the same card",
			map[string]string{"renderD129": "0000:00:02.0:i915:0", "renderD128": "0000:03:00.0:amdgpu:1"},
			"/dev/dri/renderD128", "BIOS primary"},
		{"ASPEED primary without render node: the lowest PCI address with one",
			map[string]string{"card0": "0000:05:00.0:ast:1", "renderD128": "0000:0a:00.0:amdgpu:0", "renderD129": "0000:00:02.0:i915:0"},
			"/dev/dri/renderD129", "0000:05:00.0 has no render node"},
		{"no boot_vga: the lowest PCI address, not the lowest name",
			map[string]string{"renderD128": "0000:0a:00.0:amdgpu:-", "renderD129": "0000:00:02.0:i915:-"},
			"/dev/dri/renderD129", "first card by PCI"},
		{"no card has a render node",
			map[string]string{"card0": "0000:05:00.0:ast:1", "card1": "0000:06:00.0:ast:0"},
			"", ""},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			root := t.TempDir()
			fakeSysCards(t, root, c.cards)
			cards, ch, why := DesktopCards(fakeEnvironment(root))
			got := ""
			if ch >= 0 {
				got = cards[ch].Node
			}
			if got != c.node || !strings.Contains(why, c.reason) {
				t.Errorf("chosen %q (%s), want %q (%s)", got, why, c.node, c.reason)
			}
			txt := DesktopCardsText(fakeEnvironment(root))
			if txt == "" || (c.node != "" && !strings.Contains(txt, c.node+" (")) {
				t.Errorf("text %q does not describe the cards", txt)
			}
			if c.node != "" && !strings.Contains(txt, "REMOTIX uses this one") {
				t.Errorf("the text does not say which card REMOTIX uses: %q", txt)
			}
		})
	}
}

// One card: the output does not change (no text, so neither the check nor the plan say anything).
func TestDesktopCardsOneCardSilent(t *testing.T) {
	root := t.TempDir()
	fakeSysCards(t, root, map[string]string{"renderD128": "0000:00:02.0:i915:1", "card0": "0000:00:02.0:i915:1"})
	if txt := DesktopCardsText(fakeEnvironment(root)); txt != "" {
		t.Errorf("one card must be silent, got %q", txt)
	}
	if txt := DesktopCardsText(fakeEnvironment(t.TempDir())); txt != "" {
		t.Errorf("no sysfs must be silent, got %q", txt)
	}
}
