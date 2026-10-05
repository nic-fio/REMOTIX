#!/bin/bash
# 19-nv-prova-contenitore.sh — il banco NVIDIA provato SUL PORTATILE, in un contenitore podman
# con systemd e SENZA scheda: tutti i passi che non toccano la GPU, dal vero.
#
#   bash banchi/19-nvidia/19-nv-prova-contenitore.sh [debian13|ubuntu2604]
#
# Che cosa ci si aspetta (senza scheda e' giusto cosi'):
#   controlli   ROSSO («nessuna scheda NVIDIA»), ma la fotografia della macchina e' fatta
#   dipendenze  VERDE: XFCE, labwc, attrezzi, Firefox ESR, Chrome, l'utente del banco
#   remotix     l'installatore RIFIUTA (RX-GPU-003: nessuna scheda) ⇒ il .deb col gestore,
#               il server si accende e ascolta (dichiara che non sa codificare)
#   codifica    ROSSO: «nessuno», codice 3
#   19-confronto: si COMPILA (la corsa vuole la scheda)
#   suite       NON GUARDATA (nessun nodo NVIDIA)
#   raccogli    l'archivio torna sul portatile
#   pulisci     i pacchetti e /etc/apt tornano come prima: lo si confronta
# Serve la valigia (`19-nvidia.sh prepara`).  Il contenitore resta acceso alla fine per guardarci
# dentro (`podman exec -it rxnv-prova-<bersaglio> bash`); si toglie con `podman rm -f`.
set -u
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
B=${1:-debian13}
case $B in
debian13) BASE=docker.io/library/debian:13 ;;
ubuntu2604) BASE=docker.io/library/ubuntu:26.04 ;;
*) echo "bersaglio: debian13 o ubuntu2604"; exit 2 ;;
esac
IMM=localhost/remotix-nv-prova-$B
NOME=rxnv-prova-$B
export CONTENITORE=$NOME
D=$QUI/19-nvidia.sh
M=/opt/remotix-nv/albero/banchi/19-nvidia/19-nv-macchina.sh

if ! podman image exists "$IMM"; then
	printf 'FROM %s\nENV DEBIAN_FRONTEND=noninteractive\nRUN apt-get update && apt-get install -y --no-install-recommends systemd systemd-sysv dbus ca-certificates iproute2 && rm -rf /var/lib/apt/lists/*\nSTOPSIGNAL SIGRTMIN+3\nCMD ["/sbin/init"]\n' "$BASE" \
		| podman build -q -t "$IMM" -f - "$QUI" >/dev/null || { echo "immagine non costruita"; exit 1; }
fi
podman rm -f "$NOME" >/dev/null 2>&1
podman run -d --name "$NOME" --systemd=always --cap-add=AUDIT_WRITE,AUDIT_CONTROL "$IMM" >/dev/null || exit 1
for _ in $(seq 1 30); do
	s=$(podman exec "$NOME" systemctl is-system-running 2>/dev/null)
	[ "$s" = running ] || [ "$s" = degraded ] && break
	sleep 1
done
echo "== $NOME: systemd $s"
x() { podman exec -i "$NOME" bash -c "$1"; }

bash "$D" manda || exit 1
x "dpkg-query -W -f='\${db:Status-Abbrev} \${Package}\n' | awk '\$1==\"ii\"{print \$2}' | sort > /root/pacchetti-inizio.txt; tar -C / -cf /root/apt-inizio.tar etc/apt"
for p in controlli dipendenze remotix codifica; do
	echo; echo "######## $p"
	x "bash $M $p"; echo ">> $p: uscita $?"
done
echo; echo "######## 19-confronto: solo la costruzione"
x "ALBERO=/opt/remotix-nv/albero USCITA=/var/lib/remotix-nv/confronto bash /opt/remotix-nv/albero/banchi/19-vulkan/19-confronto.sh costruisci 2>&1 | tail -n 4"
echo ">> costruzione: uscita $?"
echo; echo "######## suite"
x "bash $M suite"; echo ">> suite: uscita $?"
echo; echo "######## il server, visto da dentro"
x "ss -ltnu | grep -E ':7447 ' ; grep -a -E 'NON SA CODIFICARE|pronto' /var/lib/remotix-nv/registro.log | head -4"
bash "$D" raccogli
echo; echo "######## pulisci"
bash "$D" pulisci
echo; echo "######## il confronto col principio"
x "dpkg-query -W -f='\${db:Status-Abbrev} \${Package}\n' | awk '\$1==\"ii\"{print \$2}' | sort > /root/pacchetti-fine.txt; \
	echo \"pacchetti in piu': \$(comm -13 /root/pacchetti-inizio.txt /root/pacchetti-fine.txt | tr '\n' ' ')\"; \
	echo \"pacchetti in meno: \$(comm -23 /root/pacchetti-inizio.txt /root/pacchetti-fine.txt | tr '\n' ' ')\"; \
	mkdir -p /root/a && tar -C /root/a -xf /root/apt-inizio.tar && diff -r /root/a/etc/apt /etc/apt && echo '/etc/apt: uguale a prima'; \
	id rxbanco 2>&1 | head -1; ls /opt/remotix-nv /var/lib/remotix-nv /etc/remotix 2>&1 | head -3"
