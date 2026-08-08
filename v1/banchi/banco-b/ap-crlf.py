# Il testo che il client ha ricevuto deve avere i `\r\n`: senza, quel che si
# incolla in un programma di Windows compare tutto su una riga sola.
import sys
d = open(sys.argv[1], "rb").read()
print("CRLF %d LF %d" % (d.count(b"\r\n"), d.count(b"\n") - d.count(b"\r\n")))
