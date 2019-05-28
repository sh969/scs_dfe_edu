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

from scs_dfe.particulate.opc_r1.opc_r1 import OPCR1

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
    print("Counter,wrk,aux,no2_we_v,no2_ae_v,h2s_we_v,co_we_v,gnd_wrk_v,gnd_aux_v")
    counter = 0

    while 1:
        counter+=1
        print(counter)

        # ads1115
        wrk = ADS1115(ADS1115.ADDR_WRK, rate)
        # print(",", wrk)

        aux = ADS1115(ADS1115.ADDR_AUX, rate)
        # print(",", aux)
    
        electrochemicals = []

        no2_we_v = read_conversion(wrk, no2_we_channel)
        # printf("%0.6f" % no2_we_v)
        electrochemicals.append(str(no2_we_v))
    
        no2_ae_v = read_conversion(aux, no2_ae_channel)
        # print("%0.6f" % no2_ae_v)
        electrochemicals.append(str(no2_ae_v))
    
        h2s_we_v = read_conversion(wrk, h2s_we_channel)
        # print("%0.6f" % h2s_we_v)
        electrochemicals.append(str(h2s_we_channel))
    
        co_we_v = read_conversion(wrk, co_we_channel)
        # print("%0.6f" % co_we_v)
        electrochemicals.append(str(co_we_v))
    
        gnd_wrk_v = read_conversion(wrk, gnd_wrk_channel)
        # print("%0.6f" % gnd_wrk_v)
        electrochemicals.append(str(gnd_wrk_v))
    
        gnd_aux_v = read_conversion(aux, gnd_aux_channel)
        # print("%0.6f" % gnd_aux_v)
        electrochemicals.append(str(gnd_aux_v))

        print(electrochemicals)
    		
        # opc r1
        datum = opc.sample()
        # print(JSONify.dumps(datum))
        datum_dict = json.loads(JSONify.dumps(datum))
        print(datum_dict["pm1"])
    		
        # timing
        now = time.time()
        print("interval: %0.3f" % round(now - checkpoint, 3))
        checkpoint = now
        time.sleep(5)

    sys.stdout.flush()

except KeyboardInterrupt:
    print("KeyboardInterrupt", file=sys.stderr)
		
finally:
    opc.operations_off()
    opc.power_off()
    I2C.close()