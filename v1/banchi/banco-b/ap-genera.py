# I testi e le immagini di prova, tutti scritti da qui: cosi' i due lati
# confrontano gli stessi byte e non due idee di quel che dovevano essere.
import struct, sys, zlib

quale = sys.argv[1]

if quale == "lungo":
    riga = "REMOTIX prova di appunti lunghi, riga %05d.\n"
    testo = "".join(riga % i for i in range(2000))
    open("/tmp/ap-lungo.txt", "w", encoding="utf-8").write(testo)
    print(len(testo.encode("utf-8")))

elif quale == "strano":
    # Accenti, simboli, e due caratteri FUORI dal piano base: in UTF-16 sono
    # coppie surrogate, ed e' li' che un conto sbagliato taglia a meta'.
    testo = "perche' però: àèìòù €10 — «virgolette» 😀🎧 fine"
    open("/tmp/ap-strano.txt", "w", encoding="utf-8").write(testo)
    print(len(testo.encode("utf-8")))

elif quale == "righe":
    open("/tmp/ap-righe.txt", "w", encoding="utf-8").write("prima\nseconda\nterza\n")
    print("3")

elif quale == "html":
    open("/tmp/ap-html.txt", "w", encoding="utf-8").write(
        "<b>grassetto</b> e <i>corsivo</i>")
    print("ok")

elif quale == "grande":
    larg, alt = 320, 200
    righe = b"".join(
        b"\x00" + bytes([(x * 7) % 256, (y * 11) % 256, ((x + y) * 3) % 256, 255][k]
                        for x in range(larg) for k in range(4))
        for y in range(alt))
    def pezzo(tipo, dati):
        return (struct.pack(">I", len(dati)) + tipo + dati
                + struct.pack(">I", zlib.crc32(tipo + dati)))
    png = (b"\x89PNG\r\n\x1a\n"
           + pezzo(b"IHDR", struct.pack(">IIBBBBB", larg, alt, 8, 6, 0, 0, 0))
           + pezzo(b"IDAT", zlib.compress(righe))
           + pezzo(b"IEND", b""))
    open("/tmp/ap-grande.png", "wb").write(png)
    print("%d %d" % (larg, alt))
