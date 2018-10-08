"""
Created on 5 Jul 2016

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)

https://github.com/raspberrypi/weather-station/blob/master/SHT31.py
"""

import time

from scs_core.climate.sht_datum import SHTDatum

from scs_host.bus.i2c import I2C


# --------------------------------------------------------------------------------------------------------------------

class SHT31(object):
    """
    Sensirion SHT3x-DIS temperature and humidity
    """
    __CMD_RESET =                   0x30a2
    __CMD_CLEAR =                   0x3041

    __CMD_READ_SINGLE_HIGH =        0x2c06
    __CMD_READ_SINGLE_LOW =         0x2c10

    __CMD_READ_STATUS =             0xf32d


    # ----------------------------------------------------------------------------------------------------------------

    @staticmethod
    def humid(raw_humid):
        humid = float(raw_humid) / 65535.0

        return 100.0 * humid


    @staticmethod
    def temp(raw_temp):
        temp = float(raw_temp) / 65535.0

        return -45.0 + (175.0 * temp)


    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def null_datum(cls):
        return SHTDatum(None, None)


    # ----------------------------------------------------------------------------------------------------------------

    def __init__(self, addr):
        """
        Constructor
        """
        self.__addr = addr

        self.__raw_temperature = None
        self.__raw_humidity = None


    # ----------------------------------------------------------------------------------------------------------------

    def reset(self):
        try:
            I2C.start_tx(self.__addr)
            I2C.write16(SHT31.__CMD_RESET)
            time.sleep(0.001)

            I2C.write16(SHT31.__CMD_CLEAR)
            time.sleep(0.001)

        finally:
            I2C.end_tx()


    def sample(self):
        if self.__addr == 0:
            return None

        try:
            I2C.start_tx(self.__addr)
            temp_msb, temp_lsb, _, humid_msb, humid_lsb, _ = I2C.read_cmd16(SHT31.__CMD_READ_SINGLE_HIGH, 6)

            raw_humid = (humid_msb << 8) | humid_lsb
            raw_temp = (temp_msb << 8) | temp_lsb

            return SHTDatum(SHT31.humid(raw_humid), SHT31.temp(raw_temp))

        finally:
            I2C.end_tx()


    # ----------------------------------------------------------------------------------------------------------------

    @property
    def status(self):
        try:
            I2C.start_tx(self.__addr)
            status_msb, status_lsb, _ = I2C.read_cmd16(SHT31.__CMD_READ_STATUS, 3)

            return (status_msb << 8) | status_lsb

        finally:
            I2C.end_tx()


    @property
    def addr(self):
        return self.__addr


    # ----------------------------------------------------------------------------------------------------------------

    def __str__(self, *args, **kwargs):
        return "SHT31:{addr:0x%02x}" % self.addr
