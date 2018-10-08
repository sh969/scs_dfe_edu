"""
Created on 22 Jul 2016

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)
"""

import struct
import time

from scs_host.bus.i2c import I2C
from scs_host.lock.lock import Lock


# TODO: create an abstract gain constant list

# --------------------------------------------------------------------------------------------------------------------

class ADS1115(object):
    """
    Texas Instruments ADS1115 ADC
    """
    ADDR_AUX =          0x48
    ADDR_WRK =          0x49

    MUX_A0_A1 =         0x0000      # -000 ---- ---- ----
    MUX_A0_A3 =         0x1000      # -001 ---- ---- ----
    MUX_A1_A3 =         0x2000      # -010 ---- ---- ----
    MUX_A2_A3 =         0x3000      # -011 ---- ---- ----

    MUX_A0_GND =        0x4000      # -100 ---- ---- ----
    MUX_A1_GND =        0x5000      # -101 ---- ---- ----
    MUX_A2_GND =        0x6000      # -110 ---- ---- ----
    MUX_A3_GND =        0x7000      # -111 ---- ---- ----

    GAIN_6p144 =        0x0000      # ---- 000- ---- ----                  1 bit = 0.1875000 mV     0.2
    GAIN_4p096 =        0x0200      # ---- 001- ---- ----    (default)     1 bit = 0.1250000 mV     0.1
    GAIN_2p048 =        0x0400      # ---- 010- ---- ----                  1 bit = 0.0625000 mV     0.05
    GAIN_1p024 =        0x0600      # ---- 011- ---- ----                  1 bit = 0.0312500 mV     0.025
    GAIN_0p512 =        0x0800      # ---- 100- ---- ----                  1 bit = 0.0156250 mV     0.0125
    GAIN_0p256 =        0x0a00      # ---- 101- ---- ----                  1 bit = 0.0078125 mV     0.00625

    RATE_8 =            0x0000      # ---- ---- 000- ----
    RATE_16 =           0x0020      # ---- ---- 001- ----
    RATE_32 =           0x0040      # ---- ---- 010- ----
    RATE_64 =           0x0060      # ---- ---- 011- ----
    RATE_128 =          0x0080      # ---- ---- 100- ----    (default)
    RATE_250 =          0x00a0      # ---- ---- 101- ----
    RATE_475 =          0x00c0      # ---- ---- 110- ----
    RATE_860 =          0x00e0      # ---- ---- 111- ----


    # ----------------------------------------------------------------------------------------------------------------

    __REG_CONV =        0x00
    __REG_CONFIG =      0x01
    __REG_LO_THRESH =   0x02
    __REG_HI_THRESH =   0x03

    __OS_START =        0x8000      # 1--- ---- ---- ----

    __MODE_CONT =       0x0000      # ---- ---0 ---- ----
    __MODE_SINGLE =     0x0100      # ---- ---1 ---- ----    (default)

    __COMP_TRAD =       0x0000      # ---- ---- ---0 ----    (default)
    __COMP_WINDOW =     0x0010      # ---- ---- ---1 ----

    __COMP_POL_LOW =    0x0000      # ---- ---- ---- 0---    (default)
    __COMP_POL_HIGH =   0x0008      # ---- ---- ---- 1---

    __COMP_LATCH_OFF =  0x0000      # ---- ---- ---- -0--    (default)
    __COMP_LATCH_ON =   0x0004      # ---- ---- ---- -1--

    __COMP_QUEUE_1 =    0x0000      # ---- ---- ---- --00
    __COMP_QUEUE_2 =    0x0001      # ---- ---- ---- --01
    __COMP_QUEUE_4 =    0x0002      # ---- ---- ---- --10
    __COMP_QUEUE_0 =    0x0003      # ---- ---- ---- --11    (default)


    __GAIN =            None
    __FULL_SCALE =      None
    __TCONV =           None


    # ----------------------------------------------------------------------------------------------------------------

    __LOCK_TIMEOUT =    10.0


    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def init(cls):
        cls.__GAIN = (
                        ADS1115.GAIN_0p256,        # 0
                        ADS1115.GAIN_0p512,        # 1
                        ADS1115.GAIN_1p024,        # 2
                        ADS1115.GAIN_2p048,        # 3
                        ADS1115.GAIN_4p096,        # 4
                        ADS1115.GAIN_6p144         # 5
                    )

        cls.__FULL_SCALE = {
                        ADS1115.GAIN_0p256:  0.256,
                        ADS1115.GAIN_0p512:  0.512,
                        ADS1115.GAIN_1p024:  1.024,
                        ADS1115.GAIN_2p048:  2.048,
                        ADS1115.GAIN_4p096:  4.096,
                        ADS1115.GAIN_6p144:  6.144
                    }

        cls.__TCONV = {
                        ADS1115.RATE_8:     0.145,
                        ADS1115.RATE_16:    0.082,
                        ADS1115.RATE_32:    0.051,
                        ADS1115.RATE_64:    0.036,
                        ADS1115.RATE_128:   0.028,
                        ADS1115.RATE_250:   0.024,
                        ADS1115.RATE_475:   0.022,
                        ADS1115.RATE_860:   0.021
                    }


    @classmethod
    def gain(cls, index):
        return cls.__GAIN[index]


    # ----------------------------------------------------------------------------------------------------------------

    def __init__(self, addr, rate):
        """
        initialise ADC with given gain and rate
        """
        # fields...
        self.__addr = addr
        self.__rate = rate
        self.__gain = None

        self.__config = ADS1115.__MODE_SINGLE | self.__rate | ADS1115.__COMP_QUEUE_0

        # write config...
        try:
            self.obtain_lock()
            self.__write_config(self.__config)

        finally:
            self.release_lock()


    # ----------------------------------------------------------------------------------------------------------------

    def start_conversion(self, mux, gain):
        """
        start single-shot conversion
        wait for conv_time before reading
        """
        self.__gain = gain

        start = ADS1115.__OS_START | mux | gain | self.__config

        self.obtain_lock()
        self.__write_config(start)


    def read_conversion(self):
        """
        read most recent conversion
        returned value is voltage
        """
        try:
            config = self.__read_config()

            if not (config & ADS1115.__OS_START):
                raise ValueError("ADS1115:read_conversion: conversion not ready.")

            v = self.__read_conv()

        finally:
            self.release_lock()

        return v


    def convert(self, mux, gain):
        """
        start single-shot conversion, waits for ready, then reads
        warning: creates a high level of I2C traffic
        returned value is voltage
        """
        try:
            self.start_conversion(mux, gain)

            while True:
                time.sleep(ADS1115.__TCONV[ADS1115.RATE_860])
                config = self.__read_config()

                if config & ADS1115.__OS_START:
                    break

        finally:
            self.release_lock()

        v = self.__read_conv()

        return v


    # ----------------------------------------------------------------------------------------------------------------

    def __read_config(self):
        try:
            I2C.start_tx(self.__addr)
            msb, lsb = I2C.read_cmd(ADS1115.__REG_CONFIG, 2)

        finally:
            I2C.end_tx()

        config = (msb << 8) | lsb
        return config


    def __write_config(self, config):
        try:
            I2C.start_tx(self.__addr)
            I2C.write(ADS1115.__REG_CONFIG, config >> 8, config & 0xff)

        finally:
            I2C.end_tx()


    def __read_conv(self):
        try:
            I2C.start_tx(self.__addr)
            msb, lsb = I2C.read_cmd(ADS1115.__REG_CONV, 2)

        finally:
            I2C.end_tx()

        # render voltage...
        unsigned = (msb << 8) | lsb

        # print("unsigned: 0x%04x" % unsigned)

        signed = struct.unpack('h', struct.pack('H', unsigned))

        v = (signed[0] / 32767.5) * ADS1115.__FULL_SCALE[self.__gain]

        return v


    # ----------------------------------------------------------------------------------------------------------------

    def obtain_lock(self):
        Lock.acquire(self.__lock_name, ADS1115.__LOCK_TIMEOUT)


    def release_lock(self):
        Lock.release(self.__lock_name)


    @property
    def __lock_name(self):
        return self.__class__.__name__ + "-" + ("0x%02x" % self.__addr)


    # ----------------------------------------------------------------------------------------------------------------

    @property
    def addr(self):
        return self.__addr


    @property
    def rate(self):
        return self.__rate


    @property
    def tconv(self):
        return ADS1115.__TCONV[self.__rate]


    # ----------------------------------------------------------------------------------------------------------------

    def __str__(self, *args, **kwargs):
        return "ADS1115:{addr:0x%0.2x, rate:0x%0.4x, config:0x%0.4x}" % (self.addr, self.rate, self.__config)
