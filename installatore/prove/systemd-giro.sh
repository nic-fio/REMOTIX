#!/bin/sh
# Il giro del motore DAL VERO in una Fedora 44 con systemd acceso (prove/Contenitore.systemd): le
# azioni che parlano sul D-Bus (systemd1: GetUnitFileState, EnableUnitFiles, DisableUnitFiles,
# Reload) e gpasswd dall'elenco chiuso. (firewalld nel contenitore senza root non parte: vedi
# Contenitore.systemd.)
#   1. piano con un utente → approva → applica: CONFERMATA; da fuori: unità abilitata, utente in
#      «video», e i programmi lanciati annotati nel registro;
#   2. un piano che fallisce a metà (l'utente da mettere in «video» non esiste, e il passo viene
#      DOPO i due file e l'unità abilitata): ANNULLATA, e /etc identica a prima (impronta dei
#      contenuti: l'ora di modifica delle cartelle cambia comunque, aggiungendo e togliendo un file).
# Le prove di interruzione (processo ucciso in ogni punto) stanno in go test: qui si prova che il
# motore parla davvero con systemd e con gpasswd.
set -u
qui=$(cd "$(dirname "$0")/.." && pwd)
"$qui/costruisci.sh" >/dev/null
"$qui/costruisci.sh" go build -trimpath -o uscita/impronta ./prove/impronta
podman image exists remotix-motore-systemd || podman build -q -t remotix-motore-systemd -f "$qui/prove/Contenitore.systemd" "$qui/prove"
podman rm -f rx-motore >/dev/null 2>&1
podman run -d --name rx-motore --systemd=always --cap-add NET_ADMIN,NET_RAW -v "$qui/uscita:/opt/rx:ro,Z" remotix-motore-systemd >/dev/null
for i in $(seq 1 30); do
	s=$(podman exec rx-motore systemctl is-system-running 2>/dev/null)
	[ "$s" = running ] || [ "$s" = degraded ] && break
	sleep 1
done
echo "sistema: $s"
x() { podman exec rx-motore sh -c "$1"; }

echo "== 1. installazione di prova, CONFERMATA attesa"
x 'cd /root && /opt/rx/remotix-install piano --utente provamotore --operazioni /root/op >/dev/null && /opt/rx/remotix-install approva piano-prova.json && /opt/rx/remotix-install applica piano-prova.json --senza-firma --operazioni /root/op | tail -8; echo "applica: uscita $?"'
echo "-- visto da fuori:"
x 'echo "unità: $(systemctl is-enabled remotix-prova-motore.service)"; echo "video: $(getent group video)"; echo "programmi lanciati (registro):"; grep -h "\"COMANDO\"" /root/op/*/registro.jsonl | sed "s/.*dettaglio\":\"//; s/\"}//"; cat /root/op/*/certificato.txt | head -20'

echo "== 2. un passo fallisce a metà (utente inesistente, dopo file e unità): ANNULLATA attesa, /etc com'era"
podman rm -f rx-motore >/dev/null
podman run -d --name rx-motore --systemd=always --cap-add NET_ADMIN,NET_RAW -v "$qui/uscita:/opt/rx:ro,Z" remotix-motore-systemd >/dev/null
for i in $(seq 1 30); do
	s=$(podman exec rx-motore systemctl is-system-running 2>/dev/null)
	[ "$s" = running ] || [ "$s" = degraded ] && break
	sleep 1
done
x 'cd /root && /opt/rx/impronta -contenuti /etc > prima && /opt/rx/remotix-install piano --utente nessuno-si-chiama-cosi --operazioni /root/op >/dev/null && /opt/rx/remotix-install approva piano-prova.json >/dev/null && /opt/rx/remotix-install applica piano-prova.json --senza-firma --operazioni /root/op | tail -14; /opt/rx/impronta -contenuti /etc > dopo; if /opt/rx/impronta -confronta prima dopo; then echo "/etc: identica a prima (contenuti, permessi, proprietari; non le ore delle cartelle)"; else echo "/etc: DIVERSA"; fi; echo "unità: $(systemctl is-enabled remotix-prova-motore.service 2>&1)"'
podman rm -f rx-motore >/dev/null
