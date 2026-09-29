# REMOTIX fase 17 — AlmaLinux 10 dall'ISO boot, kickstart, «Server with GUI».
# SELinux e firewalld restano come di serie. Le sole aggiunte del banco sono segnate con [banco].
# Segnaposti riempiti da 17-vm.sh: @UTENTE@ @HASH@ @CHIAVE@ @NOME@
lang it_IT.UTF-8
keyboard --xlayouts=it
timezone Europe/Rome --utc
network --bootproto=dhcp --device=link --activate --hostname=@NOME@
url --url=https://repo.almalinux.org/almalinux/10/BaseOS/x86_64/os/
repo --name=AppStream --baseurl=https://repo.almalinux.org/almalinux/10/AppStream/x86_64/os/

zerombr
clearpart --all --initlabel --disklabel=gpt
# La proposta di serie: LVM con xfs
autopart
bootloader

rootpw --lock
user --name=@UTENTE@ --groups=wheel --password=@HASH@ --iscrypted
# [banco] la chiave del banco
sshkey --username=@UTENTE@ "@CHIAVE@"

%packages
@^graphical-server-environment
%end

%post
# [banco] sudo senza parola
echo '@UTENTE@ ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/90-banco
chmod 440 /etc/sudoers.d/90-banco
%end

reboot
