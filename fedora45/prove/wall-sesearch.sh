#!/bin/sh
# wall-sesearch.sh BOX [LOGDIR] - what the LOADED policy of the VM BOX says about remotix_net_t: `sesearch -A` (allow) and `sesearch -T` (type
# transitions) for the domain, plus a few targeted questions.  setools is on the build VM (`costruzione`, must be on, ssh 2355), not on the others:
# the compiled policy is copied from BOX to it (a file in ~/pol, nothing installed).  Run ON THE DEV SERVER; output in LOGDIR/policy-facts.txt.
BOX=${1:?usage: wall-sesearch.sh BOX [LOGDIR]}; LOGDIR=${2:-log-selinux}; mkdir -p "$LOGDIR"
R=/media/REMOTIX-FEDORA/vm-radeon
case $BOX in gnome) P=2351;; kde) P=2352;; xfce) P=2353;; lxqt) P=2354;; esac
SSHO="-o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
ssh $SSHO -i $R/$BOX/vmkey -p $P root@127.0.0.1 'cat /etc/selinux/targeted/policy/policy.*' |
  ssh $SSHO -i $R/costruzione/vmkey -p 2355 prova@127.0.0.1 "mkdir -p pol && cat > pol/policy.$BOX"
ssh $SSHO -i $R/costruzione/vmkey -p 2355 prova@127.0.0.1 "cd pol; P=policy.$BOX
echo '### policy of $BOX, loaded: '\$(ls -l \$P | awk '{print \$5}')' bytes'
echo '### sesearch -A -s remotix_net_t'; sesearch -A -s remotix_net_t \$P
echo; echo '### sesearch -T -s remotix_net_t (type transitions)'; sesearch -T -s remotix_net_t \$P
echo; echo '### the questions'
echo '[IP sockets: create/bind/connect/name_bind on anything but the inherited ones]'; sesearch -A -s remotix_net_t -c tcp_socket -c udp_socket -c rawip_socket -c packet_socket -p create -p bind -p name_bind -p name_connect -p connect \$P
echo '[shadow_t]'; sesearch -A -s remotix_net_t -t shadow_t \$P | grep -v ' domain '
echo '[execute_no_trans]'; sesearch -A -s remotix_net_t -p execute_no_trans \$P | grep -v ' domain '
echo '[capabilities]'; sesearch -A -s remotix_net_t -c capability -c capability2 \$P
echo '[ptrace]'; sesearch -A -s remotix_net_t -p ptrace \$P
 echo; echo '### sesearch -A -s remotix_t -c process (the root side)'; sesearch -A -s remotix_t -c process \$P
 echo; echo '### sigkill / signal / signull from remotix_t, UNFILTERED (rules given through attributes such as domain show here)'; sesearch -A -s remotix_t -c process -p sigkill \$P; sesearch -A -s remotix_t -c process -p signal \$P; sesearch -A -s remotix_t -c process -p signull \$P" >"$LOGDIR/policy-facts.txt" 2>&1
wc -l "$LOGDIR/policy-facts.txt"
