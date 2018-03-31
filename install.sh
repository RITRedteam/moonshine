#!/bin/bash
# Install shine for SSH

rm -frv shine/__pycache__/
rm -frv /usr/lib/python3/dist-packages/moonshine
/bin/cp -rvf shine /usr/lib/python3/dist-packages/moonshine
/bin/cp -vf moonshine.py /usr/bin/moonshine
mkdir -p /etc/moonshine
/bin/cp -vf moonshine.yml /etc/moonshine/moonshine.yml
chmod 755 /usr/bin/moonshine
grep "/usr/bin/moonshine" /etc/ssh/sshd_config 2>/dev/null >/dev/null;
if [ "$?" != "0" ]; then
    echo "Adding moonshine to sshd config"
    echo "Match User shine" >> /etc/ssh/sshd_config
    echo -e "\tForceCommand /usr/bin/moonshine" >> /etc/ssh/sshd_config
    service ssh restart
fi
