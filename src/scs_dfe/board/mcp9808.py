"""
Created on 6 Aug 2016

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)
"""

import time

from scs_dfe.board.board_datum import BoardDatum

from scs_host.bus.i2c import I2C


# --------------------------------------------------------------------------------------------------------------------

class MCP9808(object):
    """
    Microchip Technology MCP9808 temperature sensor
    """

    __ADDR =                0x1f

    __REG_CONFIG =          0x01        # ---- 0001
    __REG_ALERT_UPPER =     0x02        # ---- 0010
    __REG_ALERT_LOWER =     0x03        # ---- 0011
    __REG_CRITICAL_TEMP =   0x04        # ---- 0100
    __REG_TEMP =            0x05        # ---- 0101
    __REG_MFR_ID =          0x06        # ---- 0110
    __REG_DEV_ID =          0x07        # ---- 0111
    __REG_RESOLUTION =      0x08        # ---- 1000

    __CONV_SHUT =           0x0100      # ---- ---1 ---- ----
    __CONV_CONT =           0x0000      # ---- ---0 ---- ----

    __TCONV_0p0625 =        0.250


    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def null_datum(cls):
        return BoardDatum(None)


    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def __write_config(cls, config):
        try:
            I2C.start_tx(cls.__ADDR)
            I2C.write(cls.__REG_CONFIG, config >> 8, config & 0xff)
        finally:
            I2C.end_tx()


    @classmethod
    def __read_temp(cls):
        try:
            I2C.start_tx(cls.__ADDR)
            msb, lsb = I2C.read_cmd(cls.__REG_TEMP, 2)
        finally:
            I2C.end_tx()

        # render voltage...
        unsigned_c = float(msb & 0x1f) * 16 + float(lsb) / 16
        sign = msb & 0x10

        temp = 256 - unsigned_c if sign else unsigned_c

        return temp


    # ----------------------------------------------------------------------------------------------------------------

    def __init__(self, running):
        """
        initialise with conversion status
        """
        self.__running = None

        # write config...
        self.running = running


    # ----------------------------------------------------------------------------------------------------------------

    def sample(self):
        """
        returned value is centigrade
        """
        if not self.__running:
            raise ValueError("MCP9808:sense: conversion not running.")

        return BoardDatum(MCP9808.__read_temp())


    # ----------------------------------------------------------------------------------------------------------------

    @property
    def running(self):
        return self.__running


    @running.setter
    def running(self, running):
        """
        sleeps for 250 mS if conversion is being switched on
        """
        config = MCP9808.__CONV_CONT if running else MCP9808.__CONV_SHUT
        MCP9808.__write_config(config)

        if running and not self.__running:
            time.sleep(MCP9808.__TCONV_0p0625)

        self.__running = running


    # ----------------------------------------------------------------------------------------------------------------

    def __str__(self, *args, **kwargs):
        return "MCP9808:{running:%s}" % self.running
