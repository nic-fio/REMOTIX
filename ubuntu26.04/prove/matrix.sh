#!/bin/bash
# matrix.sh - every desktop on a fresh box: Chrome (new session) then Firefox (resumed); output log/base-<de>-<browser>-<tag>.out
cd "$(dirname "$0")"; TAG=${1:-m1}
for de in xfce lxqt gnome kde; do
	./fresh.sh $de > log/fresh-$de-$TAG.out 2>&1
	for b in chrome firefox; do python3 base-check.py --box $de --browser $b > log/base-$de-$b-$TAG.out 2>&1; echo "exit=$?" >> log/base-$de-$b-$TAG.out; done
done
echo done > log/matrix-$TAG.done
