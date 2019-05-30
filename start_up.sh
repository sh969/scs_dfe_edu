#!/bin/bash

# Update the code from Github if possible
wget -q --spider http://google.com

if [ $? -eq 0 ]; then
    echo "Online"
    cd /home/pi/
    rm -r scs_dfe_edu
    git clone https://github.com/sh969/scs_dfe_edu.git && sleep 30 ; kill $!
    FILE=/home/pi/scs_dfe_edu/README.md
    if [ -f "$FILE" ]; then
        echo "$FILE exist"
        cd /home/pi/SCS
        rm -r scs_dfe_edu
        mv -r /home/pi/scs_dfe_edu /home/pi/SCS/
    else 
        echo "$FILE does not exist"
    fi
else
    echo "Offline"
fi

echo "Starting script"
cd /home/pi/SCS/scs_dfe_edu/tests/open-seneca/

bash -c "export PYTHONPATH=/home/pi/SCS/scs_dev/src:/home/pi/SCS/scs_osio/src:/$

python3 ./sampler_gsm.py
