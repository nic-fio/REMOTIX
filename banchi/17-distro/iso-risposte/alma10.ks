# REMOTIX phase 17 — AlmaLinux 10 from the boot ISO, kickstart, "Server with GUI".
# SELinux and firewalld stay as default. The only additions of the bench are marked with [banco].
# Placeholders filled in by 17-vm.sh: @UTENTE@ @HASH@ @CHIAVE@ @NOME@
lang it_IT.UTF-8
keyboard --xlayouts=it
timezone Europe/Rome --utc
network --bootproto=dhcp --device=link --activate --hostname=@NOME@
url --url=https://repo.almalinux.org/almalinux/10/BaseOS/x86_64/os/
repo --name=AppStream --baseurl=https://repo.almalinux.org/almalinux/10/AppStream/x86_64/os/

zerombr
clearpart --all --initlabel --disklabel=gpt
# The default proposal: LVM with xfs
autopart
bootloader

rootpw --lock
user --name=@UTENTE@ --groups=wheel --password=@HASH@ --iscrypted
# [banco] the bench key
sshkey --username=@UTENTE@ "@CHIAVE@"

%packages
@^graphical-server-environment
%end

%post
# [banco] passwordless sudo
echo '@UTENTE@ ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/90-banco
chmod 440 /etc/sudoers.d/90-banco
%end

reboot
