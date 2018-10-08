"""
Created on 4 Jul 2016

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)
"""

import time

from scs_core.data.localized_datetime import LocalizedDatetime
from scs_core.data.datum import Datum

from scs_core.particulate.opc_datum import OPCDatum

from scs_dfe.board.io import IO

from scs_host.bus.spi import SPI
from scs_host.lock.lock import Lock


# TODO: consider locking at the top level, to prevent power on / off by other processes

# --------------------------------------------------------------------------------------------------------------------

class OPCN2(object):
    """
    classdocs
    """
    MIN_SAMPLE_PERIOD =                  5.0       # seconds
    MAX_SAMPLE_PERIOD =                 10.0       # seconds
    DEFAULT_SAMPLE_PERIOD =             10.0       # seconds

    POWER_CYCLE_TIME =                  10.0       # seconds

    # ----------------------------------------------------------------------------------------------------------------

    __BOOT_TIME =                        4.0       # seconds
    __START_TIME =                       5.0       # seconds
    __STOP_TIME =                        2.0       # seconds

    __FLOW_RATE_VERSION =               16

    __FAN_UP_TIME =                     10
    __FAN_DOWN_TIME =                   2

    __PERIOD_CONVERSION =               45360       # should be 12000 (1/12MHz * 1000), but found by experiment

    __CMD_POWER =                       0x03
    __CMD_POWER_ON =                    0x00        # 0x03, 0x00
    __CMD_POWER_OFF =                   0x01        # 0x03, 0x01

    __CMD_CHECK_STATUS =                0xcf
    __CMD_READ_HISTOGRAM =              0x30
    __CMD_GET_FIRMWARE_VERSION =        0x3f

    __SPI_CLOCK =                       488000
    __SPI_MODE =                        1

    __CMD_DELAY =                       0.01
    __TRANSFER_DELAY =                  0.00002

    __LOCK_TIMEOUT =                    6.0


    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def obtain_lock(cls):
        Lock.acquire(cls.__name__, OPCN2.__LOCK_TIMEOUT)


    @classmethod
    def release_lock(cls):
        Lock.release(cls.__name__)


    # ----------------------------------------------------------------------------------------------------------------

    def __init__(self, spi_bus, spi_device):
        """
        Constructor
        """
        self.__io = IO()
        self.__spi = SPI(spi_bus, spi_device, OPCN2.__SPI_MODE, OPCN2.__SPI_CLOCK)


    # ----------------------------------------------------------------------------------------------------------------

    def power_on(self):
        initial_power_state = self.__io.opc_power

        self.__io.opc_power = IO.LOW

        if initial_power_state == IO.HIGH:      # initial_power is None if there is no power control facility
            time.sleep(self.__BOOT_TIME)


    def power_off(self):
        self.__io.opc_power = IO.HIGH


    # ----------------------------------------------------------------------------------------------------------------

    def operations_on(self):
        try:
            self.obtain_lock()
            self.__spi.open()

            # start...
            self.__spi.xfer([OPCN2.__CMD_POWER, OPCN2.__CMD_POWER_ON])
            time.sleep(OPCN2.__START_TIME)

            # clear histogram...
            self.__spi.xfer([OPCN2.__CMD_READ_HISTOGRAM])
            time.sleep(OPCN2.__CMD_DELAY)

            for _ in range(62):
                self.__read_byte()

        finally:
            self.__spi.close()
            self.release_lock()


    def operations_off(self):
        try:
            self.obtain_lock()
            self.__spi.open()

            self.__spi.xfer([OPCN2.__CMD_POWER, OPCN2.__CMD_POWER_OFF])

        finally:
            time.sleep(OPCN2.__CMD_DELAY)

            self.__spi.close()
            self.release_lock()

        time.sleep(OPCN2.__STOP_TIME)


    # ----------------------------------------------------------------------------------------------------------------

    def sample(self):
        try:
            self.obtain_lock()
            self.__spi.open()

            self.__spi.xfer([OPCN2.__CMD_READ_HISTOGRAM])
            time.sleep(OPCN2.__CMD_DELAY)

            # bins...
            bins = [None] * 16

            for i in range(16):
                bins[i] = self.__read_int()

            # bin MToFs...
            bin_1_mtof = self.__read_byte()
            bin_3_mtof = self.__read_byte()
            bin_5_mtof = self.__read_byte()
            bin_7_mtof = self.__read_byte()

            # flow rate...
            self.__spi.read_bytes(4)

            # temperature
            self.__spi.read_bytes(4)

            # period...
            period = self.__read_float()

            # checksum...
            self.__read_int()

            # PMx...
            try:
                pm = self.__read_float()
                pm1 = 0.0 if pm < 0 else pm
            except TypeError:
                pm1 = None

            try:
                pm = self.__read_float()
                pm2p5 = 0.0 if pm < 0 else pm
            except TypeError:
                pm2p5 = None

            try:
                pm = self.__read_float()
                pm10 = 0.0 if pm < 0 else pm
            except TypeError:
                pm10 = None

            now = LocalizedDatetime.now()

            return OPCDatum(now, pm1, pm2p5, pm10, period, bins, bin_1_mtof, bin_3_mtof, bin_5_mtof, bin_7_mtof)

        finally:
            time.sleep(OPCN2.__CMD_DELAY)

            self.__spi.close()
            self.release_lock()


    def firmware(self):
        try:
            self.obtain_lock()
            self.__spi.open()

            self.__spi.xfer([OPCN2.__CMD_GET_FIRMWARE_VERSION])
            time.sleep(OPCN2.__CMD_DELAY)

            read_bytes = []

            for _ in range(60):
                time.sleep(OPCN2.__TRANSFER_DELAY)
                read_bytes.extend(self.__spi.read_bytes(1))

            report = '' . join(chr(b) for b in read_bytes)

            return report.strip('\0\xff')       # \0 - Raspberry Pi, \xff - BeagleBone

        finally:
            time.sleep(OPCN2.__CMD_DELAY)

            self.__spi.close()
            self.release_lock()


    # ----------------------------------------------------------------------------------------------------------------

    def __read_byte(self):
        time.sleep(OPCN2.__TRANSFER_DELAY)
        read_bytes = self.__spi.read_bytes(1)

        return read_bytes[0]


    def __read_int(self):
        read_bytes = []

        for _ in range(2):
            time.sleep(OPCN2.__TRANSFER_DELAY)
            read_bytes.extend(self.__spi.read_bytes(1))

        return Datum.decode_unsigned_int(read_bytes)


    def __read_float(self):
        read_bytes = []

        for _ in range(4):
            time.sleep(OPCN2.__TRANSFER_DELAY)
            read_bytes.extend(self.__spi.read_bytes(1))

        return Datum.decode_float(read_bytes)


    # ----------------------------------------------------------------------------------------------------------------

    def __str__(self, *args, **kwargs):
        return "OPCN2:{io:%s, spi:%s}" % (self.__io, self.__spi)
