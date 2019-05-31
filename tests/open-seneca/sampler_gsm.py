#!/usr/bin/env python3

"""
Created on 7 Mar 2019

@author: Sebastian Horstmann (sh969@cam.ac.uk)
"""

# ads1115 (taken from scs_dfe_edu/tests/gas/ads1115_test.py)
import time

from scs_dfe.gas.ads1115 import ADS1115

from scs_host.bus.i2c import I2C
from scs_host.sys.host import Host

# OPC R1 (taken from scs_dfe_eng/tests/particulate/opc_r1_test.py)
import sys

from scs_core.data.json import JSONify
import json
import csv
import os

from scs_dfe.particulate.opc_r1.opc_r1 import OPCR1

# Pi Hat related imports
import serial
import datetime
import pynmea2
from at_commands import *

# --------------------------------------------------------------------------------------------------------------------

ser = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=5)

time.sleep(5)
APN = 'TM'
URL = 'www.ppp.one/gps.php'

print("gps off")
GPSoff(APN, URL, ser)
print("gprs_on")
[imei, cnum] = GPRSstartup(APN, URL, ser)
print("gps_on")
GPSstartup(APN, URL, ser)

dataframe = {
		"datetime" : None,
		"lat" : None,
		"lon" : None,
		"alt" : None,
		"vel" : None,
		"hhop" : None,
	}
gprs = {
        "imei": imei,
        "cnum": cnum,
        "version": os.path.basename(__file__)
    }


# --------------------------------------------------------------------------------------------------------------------

ADS1115.init()

gain = ADS1115.GAIN_2p048       # GAIN_1p024
rate = ADS1115.RATE_8

no2_we_channel = ADS1115.MUX_A0_GND         # on wrk ADC
no2_ae_channel = ADS1115.MUX_A0_GND         # on aux ADC

h2s_we_channel = ADS1115.MUX_A2_GND         # on wrk ADC
co_we_channel = ADS1115.MUX_A3_GND          # on wrk ADC

gnd_wrk_channel = ADS1115.MUX_A1_GND        # on wrk ADC
gnd_aux_channel = ADS1115.MUX_A1_GND        # on aux ADC


# --------------------------------------------------------------------------------------------------------------------

def read_conversion(device, channel):
    device.start_conversion(channel, gain)
    time.sleep(wrk.tconv)

    return device.read_conversion()


# --------------------------------------------------------------------------------------------------------------------

try:
    I2C.open(Host.I2C_SENSORS)
    opc = OPCR1(Host.opc_spi_bus(), Host.opc_spi_device())
    opc.power_on()
    time.sleep(1)
    opc.operations_on()
    time.sleep(1)
    checkpoint = time.time()
    counter = 0
    filename = '/home/pi/log/'+str(int(checkpoint))+'.csv'

    while 1:    		
        # opc r1
        datum = opc.sample()
        # print(JSONify.dumps(datum))
        datum_dict = json.loads(JSONify.dumps(datum))
        
        datum_dict["counter"] = counter
        keys_to_round = ['pm1', 'pm2.5' 'pm10', 'vel', 'tmp', 'hmd']
        for item in keys_to_round:
            datum_dict[item] = round(datum_dict[item], 2)


        # ads1115
        wrk = ADS1115(ADS1115.ADDR_WRK, rate)
        # print(",", wrk)

        aux = ADS1115(ADS1115.ADDR_AUX, rate)
        # print(",", aux)

        no2_we_v = read_conversion(wrk, no2_we_channel)
        # printf("%0.6f" % no2_we_v)
        datum_dict["no2_we_v"] = round(no2_we_v, 6)

        no2_ae_v = read_conversion(aux, no2_ae_channel)
        # print("%0.6f" % no2_ae_v)
        datum_dict["no2_ae_v"] = round(no2_ae_v, 6)
    
        h2s_we_v = read_conversion(wrk, h2s_we_channel)
        # print("%0.6f" % h2s_we_v)
        datum_dict["h2s_we_v"] = round(h2s_we_v, 6)
    
        co_we_v = read_conversion(wrk, co_we_channel)
        # print("%0.6f" % co_we_v)
        datum_dict["co_we_v"] = round(co_we_v, 6)
    
        gnd_wrk_v = read_conversion(wrk, gnd_wrk_channel)
        # print("%0.6f" % gnd_wrk_v)        
        datum_dict["gnd_wrk_v"] = round(gnd_wrk_v, 6)
    
        gnd_aux_v = read_conversion(aux, gnd_aux_channel)
        # print("%0.6f" % gnd_aux_v)
        datum_dict["gnd_aux_v"] = round(gnd_aux_v, 6)

        # datum_dict["el_chem"] = {"no2_we_v":no2_we_v, "no2_ae_v":no2_ae_v, "h2s_we_v":h2s_we_v, "co_we_v":co_we_v, "gnd_wrk_channel":gnd_wrk_channel, "gnd_aux_channel":gnd_aux_channel}
    	
        # Reformat SHT readings
        datum_dict["hmd"] = datum_dict["sht"]["hmd"]
        datum_dict["tmp"] = datum_dict["sht"]["tmp"]
        del datum_dict["sht"]

        # timing
        now = time.time()
        datum_dict["interval"] = round(now - checkpoint, 3)
        # print("interval: %0.3f" % round(now - checkpoint, 3))

        # print(datum_dict["pm1"])
 
        checkpoint = now

        # --------------------------------------------------------------------------------------------------------------------

        # Start GNSS data received via UART
        txrx_force(APN, URL, ser, 'AT+CGNSTST=1\r\n', 'OK', 5)
        # Get one dataframe (see above) from GNSS string
        dataframe = readGPS(APN, URL, ser, dataframe)          
        # Stop GNSS data received via UART so you can send data via GPRS    
        txrx_force(APN, URL, ser, 'AT+CGNSTST=0\r\n', 'OK', 5)

        dataframe.update(datum_dict)
        dataframe.update(gprs)
        print(dataframe)
        
        # logging to the SD card
        header = []
        data = []
        log_file = open(filename, 'a', newline='')
        csvwriter = csv.writer(log_file)
        for item in dataframe:
            if counter == 0:
                header.append(item)
            data.append(dataframe[item])
        if counter == 0: csvwriter.writerow(header)
        csvwriter.writerow(data)
        log_file.close()

        # Prep send
        txrx_force(APN, URL, ser, 'AT+HTTPDATA='+ str(len(json.dumps(dataframe)))+',10000\r\n', 'DOWNLOAD', 5)
        # Load data
        txrx_force(APN, URL, ser, json.dumps(dataframe) + '\r\n', 'OK', 5)    
        # Post the data
        #txrx_force(APN, URL, ser, 'AT+HTTPACTION=1\r\n', 'OK', 5) # for Charles' server
        txrx_force(APN, URL, ser, 'AT+HTTPACTION=1\r\n', '+HTTPACTION: 1,200,1', 5) # for Pete's server

        # --------------------------------------------------------------------------------------------------------------------

        # Finishing off
        counter+=1
        time.sleep(3)

    sys.stdout.flush()

except KeyboardInterrupt:
    print("KeyboardInterrupt", file=sys.stderr)
		
finally:
    opc.operations_off()
    opc.power_off()
    I2C.close()