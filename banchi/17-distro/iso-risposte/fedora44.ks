# REMOTIX fase 17 — Fedora 44 Workstation dall'ISO Everything netinst, kickstart.
# L'ambiente e' quello della Workstation (@^workstation-product-environment); SELinux e
# firewalld restano come di serie. Le sole aggiunte del banco sono segnate con [banco].
# Segnaposti riempiti da 17-vm.sh: @UTENTE@ @HASH@ @CHIAVE@ @NOME@
lang it_IT.UTF-8
keyboard --xlayouts=it
timezone Europe/Rome --utc
network --bootproto=dhcp --device=link --activate --hostname=@NOME@
url --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=fedora-44&arch=x86_64
repo --name=updates --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-f44&arch=x86_64

zerombr
clearpart --all --initlabel --disklabel=gpt
# La proposta di serie della Workstation: btrfs
autopart --type=btrfs
bootloader

rootpw --lock
user --name=@UTENTE@ --groups=wheel --password=@HASH@ --iscrypted
# [banco] la chiave del banco
sshkey --username=@UTENTE@ "@CHIAVE@"
# [banco] sshd: sulla Workstation c'e' ma e' spento di serie
services --enabled=sshd

%packages
@^workstation-product-environment
%end

%post
# [banco] sudo senza parola
echo '@UTENTE@ ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/90-banco
chmod 440 /etc/sudoers.d/90-banco
%end

reboot
