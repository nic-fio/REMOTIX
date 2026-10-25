package ui

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"math/big"
	"os"
	"path/filepath"
	"testing"
	"time"
)

// pemFile writes a self-signed certificate at root/rel and returns its fingerprint as FingerprintTLS prints it.
func pemFile(t *testing.T, root, rel, cn string) string {
	t.Helper()
	k, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	tpl := &x509.Certificate{SerialNumber: big.NewInt(time.Now().UnixNano()), Subject: pkix.Name{CommonName: cn},
		NotBefore: time.Now().Add(-time.Hour), NotAfter: time.Now().Add(time.Hour)}
	der, err := x509.CreateCertificate(rand.Reader, tpl, tpl, &k.PublicKey, k)
	if err != nil {
		t.Fatal(err)
	}
	p := filepath.Join(root, rel)
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(p, pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der}), 0o644); err != nil {
		t.Fatal(err)
	}
	return FingerprintTLS(p)
}

// ServerFingerprint: 1.5 keeps the certificate in net/ (the split, on by default), the 1.0 and the single-process build in
// /var/lib/remotix/certificates; the install summary must show the fingerprint of whichever exists, the net/ one first.
func TestServerFingerprint(t *testing.T) {
	root := t.TempDir()
	if got := ServerFingerprint(root); got != "" {
		t.Fatalf("no certificate anywhere: want empty, got %q", got)
	}
	old := pemFile(t, root, "var/lib/remotix/certificates/page.pem", "old")
	if old == "" {
		t.Fatal("the fixture certificate has no fingerprint")
	}
	if got := ServerFingerprint(root); got != old {
		t.Fatalf("only the 1.0 place: want %q, got %q", old, got)
	}
	net := pemFile(t, root, "var/lib/remotix/net/certificates/page.pem", "net")
	if net == old {
		t.Fatal("the two fixtures are the same certificate")
	}
	if got := ServerFingerprint(root); got != net {
		t.Fatalf("both places: the net/ one wins, want %q, got %q", net, got)
	}
	// an unreadable or damaged file in net/ does not hide the other
	if err := os.WriteFile(filepath.Join(root, "var/lib/remotix/net/certificates/page.pem"), []byte("not a certificate"), 0o644); err != nil {
		t.Fatal(err)
	}
	if got := ServerFingerprint(root); got != old {
		t.Fatalf("damaged net/ file: want the 1.0 one %q, got %q", old, got)
	}
}
