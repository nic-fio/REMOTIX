package engine

import (
	"path/filepath"
	"sort"
	"strings"
)

// The encoding routes on the card (phase 19, DECISIONI §10.27). REMOTIX encodes ONLY on the
// card («no cpu without a card», the user's words): without a capable card it is not installed,
// and the preliminary check says so before touching anything, with the reason. The route is chosen
// by CAPABILITY, not by brand; the verdict is «at least one active route has a capable card».
//
//   - «vulkan» (Vulkan Video): the first per §10.27 — AMD with RADV (`[M]` 1 Oct 2026: Radeon RX
//     6800, Mesa 25.0.7, H.264 and HEVC on the server), NVIDIA with the proprietary driver (`[?]` not tried:
//     the lab does not have one), Intel when Mesa makes it stable (today ANV encodes only behind
//     ANV_DEBUG=video-encode: it stays on VA-API). ⭐ ACTIVE since 1 Oct 2026: the product tries it BEFORE
//     VA-API (`src/encoder.c`, `h264_card`/`hevc_card`) and `remotix --encoding-test`
//     says which route did the encoding (`route`).
//   - «vaapi» (VA-API, libva): Intel and AMD, with the distribution's driver or with the one from the
//     third-party repository the catalogue names (H264Platform, D5).
//
// ⛔ The preliminary check does NOT launch programs and does NOT open the card (R1, RX-H264-001): here
// what is on disk is read (the VA drivers, the Vulkan drivers). The REAL test — an encoded
// frame — is done by REMOTIX's binary in 7a, after installation, and it is the one that counts.

// EncodeRoute: a way of having the card encode H.264.
type EncodeRoute struct {
	Nome string
	// Active: REMOTIX already uses it. A route that is declared and not active detects, but saves no
	// machine from refusal
	Active bool
	// Detect: in PREFLIGHT, read-only (R1): writes the route's facts into the profile
	Detect func(a *Environment, p *ProfileV, fam string)
	// Cards: the vendors of THIS machine's cards that the route can make encode on this
	// platform (pl nil: there is no catalogue yet, judged from the profile alone). A card whose
	// driver comes from a third-party repository counts: the «no» to the repository is stopped by D5 (RX-H264-006).
	// A card that is there but of unknown vendor counts as «?»: the real test is in 7a
	Cards func(pl *PlatformV, p *ProfileV) []string
}

// EncodeRoutes: in the order of preference of §10.27.
var EncodeRoutes = []EncodeRoute{
	{Nome: "vulkan", Active: true, Detect: detectVulkan, Cards: vulkanCards},
	{Nome: "vaapi", Active: true, Detect: h264, Cards: vaapiCards},
}

// encode: the routes in PREFLIGHT, then the verdict from the profile alone (the catalogue redoes it in Evaluate,
// where it also knows which drivers the distribution can provide).
func encode(a *Environment, p *ProfileV, fam string) {
	var enabled_ones []string
	for _, s := range EncodeRoutes {
		s.Detect(a, p, fam)
		if s.Active {
			enabled_ones = append(enabled_ones, s.Nome)
		}
	}
	p.Detected("encoding.routes", strings.Join(enabled_ones, ","), "encoding_routes.go (phase 19)")
	if cod, det := VerdictCard(nil, p); cod != "" {
		p.Con(cod, det)
	}
}

// detectVulkan: the probe of the Vulkan Video route, read-only: the installed Vulkan drivers are the
// loader's ICD files (/usr/share/vulkan/icd.d, /etc/vulkan/icd.d), and the file name tells the driver
// — `radeon_icd.x86_64.json` (RADV, AMD), `nvidia_icd.json` (the proprietary driver),
// `intel_icd.x86_64.json` (ANV), `lvp_icd` (llvmpipe: no video), `virtio_icd`… The normalised list
// (without `_icd` and without the architecture) is written in encode.vulkan.icd; «none» if there is
// no file: the loader would see no card, and the route is not here.
func detectVulkan(a *Environment, p *ProfileV, _ string) {
	seen_items := map[string]bool{}
	var icd []string
	for _, g := range []string{"/usr/share/vulkan/icd.d/*.json", "/etc/vulkan/icd.d/*.json"} {
		v, _ := filepath.Glob(a.P(g))
		for _, x := range v {
			n := icdName(filepath.Base(x))
			if n != "" && !seen_items[n] {
				seen_items[n] = true
				icd = append(icd, n)
			}
		}
	}
	sort.Strings(icd)
	value := strings.Join(icd, ",")
	if value == "" {
		value = "none"
	}
	p.Detected("encoding.vulkan.icd", value, "/usr/share/vulkan/icd.d")
	p.Place(Fatto{KeyId: "encoding.vulkan", Val: "active", State: DETECTED, Source: "encoding_routes.go (phase 19)",
		Nota: "Vulkan Video, tried BEFORE VA-API by the product; the real test is in 7a (remotix --encoding-test, field «strada»)"})
}

// icdName: «radeon_icd.x86_64.json» → «radeon», «nvidia_icd.json» → «nvidia»; "" if it is not an ICD.
func icdName(file string) string {
	n := strings.TrimSuffix(file, ".json")
	i := strings.Index(n, "_icd")
	if i < 0 {
		return ""
	}
	return n[:i]
}

// vulkanCards: the vendors of this machine's cards that Vulkan Video can make encode: AMD with
// RADV's ICD (`radeon`), NVIDIA with the proprietary driver and its ICD (`nvidia`). ⛔ Intel NO: ANV
// encodes only behind ANV_DEBUG=video-encode (experimental, §10.27) ⇒ it stays on VA-API. A card
// without its ICD does not count: the loader would not see it, and the 7a test would say «none».
// ⚠ That the ICD is there does not mean it encodes: `[?]` the minimum Mesa version with RADV encoding
// by default is not measured (`[M]` 25.0.7 yes); 7a is what tells.
// ⭐ With the catalogue (pl), for AMD the platform is needed too: the `radeon` ICD counts only where the official
// RADV encodes (VulkanEncoding); where Mesa is built without codecs (Fedora, RHEL, openSUSE:
// `all_free`) it is not enough, and the AMD card is judged by the VA-API route. Without the ICD the AMD card does not
// count: the engine does not install the driver (DECISIONI §10.36), VerdictCard says so.
func vulkanCards(pl *PlatformV, p *ProfileV) []string {
	if p.V("gpu.nodes") == "none" {
		return nil
	}
	card_vendors, known := cardVendors(p)
	if !known {
		return nil
	}
	icd := map[string]bool{}
	for _, n := range strings.Split(p.V("encoding.vulkan.icd"), ",") {
		icd[n] = true
	}
	var r []string
	amd := icd["radeon"]
	if pl != nil && !contains(pl.H264.VulkanEncoding, "AMD") {
		amd = false
	}
	if card_vendors["AMD"] && amd {
		r = append(r, "AMD")
	}
	if card_vendors["NVIDIA"] && icd["nvidia"] && p.V("gpu.nvidia_proprietary") == "yes" {
		r = append(r, "NVIDIA")
	}
	return r
}

// CardOnRoute: the route `name` (active) can make a card of vendor `f` encode on
// this machine. It serves whoever must say whether a card stays OUT (the NVIDIA's condition
// C-HARDWARE): with Vulkan the proprietary NVIDIA with its ICD is no longer out.
func CardOnRoute(name, f string, pl *PlatformV, p *ProfileV) bool {
	for _, s := range EncodeRoutes {
		if s.Nome != name || !s.Active {
			continue
		}
		for _, x := range s.Cards(pl, p) {
			if x == f {
				return true
			}
		}
	}
	return false
}

// vaapiCards: the Intel and AMD cards that encode H.264 via VA-API on this platform.
func vaapiCards(pl *PlatformV, p *ProfileV) []string {
	if p.V("gpu.nodes") == "none" {
		return nil
	}
	card_vendors, known := cardVendors(p)
	if !known {
		return []string{"?"}
	}
	intel, amd, _ := driverFamily(p)
	without := map[string]bool{"Intel": intel == "without", "AMD": amd == "without"}
	var r []string
	for _, f := range []string{"Intel", "AMD"} {
		if !card_vendors[f] {
			continue
		}
		if pl != nil && !pl.H264.encodesFor(f, without[f]) {
			continue
		}
		r = append(r, f)
	}
	return r
}

// VerdictCard: the card check (phase 19). "" if at least one ACTIVE route has a capable
// card (or if it is not known: unread nodes are not a refusal); otherwise the BLOCKING code and the
// detail, from the most precise case to the most general.
func VerdictCard(pl *PlatformV, p *ProfileV) (code, detail string) {
	nodes := p.V("gpu.nodes")
	if nodes == "" {
		return "", ""
	}
	for _, s := range EncodeRoutes {
		if s.Active && len(s.Cards(pl, p)) > 0 {
			return "", ""
		}
	}
	card_vendors, _ := cardVendors(p)
	var names []string
	for f := range card_vendors {
		names = append(names, f)
	}
	sort.Strings(names)
	switch {
	case nodes == "none":
		return "RX-GPU-003", ""
	case p.V("gpu.nvidia_proprietary") == "yes":
		// the proprietary NVIDIA encodes ONLY in Vulkan: if we are here, its ICD is not there
		return "RX-GPU-004", strings.Join(names, ", ") + "; ICD Vulkan: " + notEmpty(p.V("encoding.vulkan.icd"), "none")
	case card_vendors["Intel"] || card_vendors["AMD"]:
		// there is a card of the VA-API route, but on this platform it does not encode and no driver
		// of the catalogue completes it (AMD on RHEL and derivatives; a driver without H.264 and nothing to add)
		// — and it is not in Vulkan (AMD without RADV's ICD, or with the distribution's codec-less
		// RADV; Intel is not there by default)
		var d []string
		if pl != nil && pl.H264.AmdWithoutVaapi && card_vendors["AMD"] {
			d = append(d, "AMD on "+pl.Nome+": Mesa built without VA-API")
		}
		if f := p.V("h264.driver_family"); f != "" {
			d = append(d, f)
		}
		d = append(d, "ICD Vulkan: "+notEmpty(p.V("encoding.vulkan.icd"), "none"))
		return "RX-GPU-006", strings.Join(d, "; ")
	}
	return "RX-GPU-005", strings.Join(names, ", ")
}
