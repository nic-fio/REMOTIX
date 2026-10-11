#!/bin/bash
# restart-servers.sh [product] — restarts the server in the 4 boxes; with «product» it first puts the product back in.
cd /media/REMOTIX/rete11 || exit 2
P=$(sed -n "s/^pass: *//p" ~/SERVER.ssh)
for d in gnome kde xfce lxqt; do
	if [ "${1:-}" = product ]; then
		printf "%s\n" "$P" | sudo -S -p "" bash 11-start.sh product $d >/dev/null 2>&1 && echo "$d: product inside" || echo "$d: ⛔ product did NOT succeed"
	fi
	printf "%s\n" "$P" | sudo -S -p "" bash 11-start.sh server $d 2>&1 | grep -E "OK|NO"
done
