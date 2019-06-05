#!/bin/bash

# Update the code from Github if possible
wget -q --spider http://google.com
if [ $? -eq 0 ]; then
    echo "Online"
    cd /home/pi/
    rm -r -f scs_dfe_edu
    git clone https://github.com/sh969/scs_dfe_edu.git # && sleep 30 ; kill $!
    FILE=/home/pi/scs_dfe_edu/README.md
    if [ -f "$FILE" ]; then
        echo "$FILE exists"
        rm -r -f /home/pi/SCS/scs_dfe_edu
        cp -r -f /home/pi/scs_dfe_edu /home/pi/SCS/
        cp -f /home/pi/SCS/scs_dfe_edu/start_up.sh /home/pi/
        cd /home/pi/
        chmod 755 start_up.sh
    else 
        echo "$FILE does not exist"
    fi
else
    echo "Offline"
fi

echo "Changing hostname"
# find imei of gsm module
FILE=/home/pi/log/imei.txt
if ! [ -f "$FILE" ]; then
    echo "IMEI" > $FILE
fi
imei=$(cat $FILE)

# find git version number
cd /home/pi/SCS/scs_dfe_edu/tests/open-seneca/
version=$(git rev-list --count develop)

# change hostname
echo "os-"$imei"-"$version > hostname
sudo mv -f hostname /etc
# change hosts
head -n -1 /etc/hosts > temp
echo -e "127.0.0.1\t"$(cat /etc/hostname) >> temp
sudo mv -f temp /etc/hosts

# start script
echo "Starting script"
bash -c "export PYTHONPATH=/home/pi/SCS/scs_dev/src:/home/pi/SCS/scs_osio/src:/$"
python3 ./sampler_gsm.py $version
