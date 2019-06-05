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
        echo "$FILE exist"
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

echo "Starting script"

# FILE=/home/pi/log/imei.txt
# if [ -f "$FILE" ]; then
#     echo "$FILE exist"
# else
#     echo "IMEI" > $FILE
# imei=$(cat $FILE)
# echo $imei

cd /home/pi/SCS/scs_dfe_edu/tests/open-seneca/
# version=$(git rev-list --count develop)
# echo "os-"$imei"-"$version > hostname
# sudo mv -f hostname /etc

bash -c "export PYTHONPATH=/home/pi/SCS/scs_dev/src:/home/pi/SCS/scs_osio/src:/$"

python3 ./sampler_gsm.py $version
