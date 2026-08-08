# Confronta due testi, tollerando la differenza di fine riga: e' esattamente
# quel che il protocollo cambia per strada, e non e' un errore.
import sys

a = open(sys.argv[1], encoding="utf-8", errors="replace").read()
b = open(sys.argv[2], encoding="utf-8", errors="replace").read()
a_n = a.replace("\r\n", "\n").rstrip("\n\x00")
b_n = b.replace("\r\n", "\n").rstrip("\n\x00")
if a_n == b_n:
    print("UGUALI %d" % len(b.encode("utf-8")))
else:
    # Dove divergono, che e' la sola cosa utile quando non tornano.
    n = min(len(a_n), len(b_n))
    dove = next((i for i in range(n) if a_n[i] != b_n[i]), n)
    print("DIVERSI %d %d %d %r %r"
          % (len(a_n), len(b_n), dove, a_n[dove:dove + 12], b_n[dove:dove + 12]))
