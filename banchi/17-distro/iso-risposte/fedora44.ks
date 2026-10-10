# REMOTIX phase 17 — Fedora 44 Workstation from the Everything netinst ISO, kickstart.
# The environment is the Workstation's (@^workstation-product-environment); SELinux and
# firewalld stay as default. The only additions of the bench are marked with [bench].
# Placeholders filled in by 17-vm.sh: @ACCOUNT@ @HASH@ @KEY@ @LABEL_NAME@
lang it_IT.UTF-8
keyboard --xlayouts=it
timezone Europe/Rome --utc
network --bootproto=dhcp --device=link --activate --hostname=@LABEL_NAME@
url --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=fedora-44&arch=x86_64
repo --name=updates --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-f44&arch=x86_64

zerombr
clearpart --all --initlabel --disklabel=gpt
# The Workstation's default proposal: btrfs
autopart --type=btrfs
bootloader

rootpw --lock
user --name=@ACCOUNT@ --groups=wheel --password=@HASH@ --iscrypted
# [bench] the bench key
sshkey --username=@ACCOUNT@ "@KEY@"
# [bench] sshd: on the Workstation it is there but off by default
services --enabled=sshd

%packages
@^workstation-product-environment
%end

%post
# [bench] passwordless sudo
echo '@ACCOUNT@ ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/90-banco
chmod 440 /etc/sudoers.d/90-banco
%end

reboot
