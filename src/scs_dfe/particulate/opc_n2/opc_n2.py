"""
Created on 4 Jul 2016

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)

Firmware report:
OPC-N2 FirmwareVer=OPC-018.1..............................BD
"""

import time

from scs_core.data.localized_datetime import LocalizedDatetime
from scs_core.data.datum import Decode

from scs_core.particulate.opc_datum import OPCDatum

from scs_dfe.particulate.alphasense_opc import AlphasenseOPC


# --------------------------------------------------------------------------------------------------------------------

class OPCN2(AlphasenseOPC):
    """
    classdocs
    """
    SOURCE =                            'N2'

    MIN_SAMPLE_PERIOD =                  5.0        # seconds
    MAX_SAMPLE_PERIOD =                 10.0        # seconds
    DEFAULT_SAMPLE_PERIOD =             10.0        # seconds

    # ----------------------------------------------------------------------------------------------------------------

    __BOOT_TIME =                        5.0        # seconds
    __START_TIME =                       5.0        # seconds
    __STOP_TIME =                        2.0        # seconds
    __POWER_CYCLE_TIME =                10.0        # seconds

    __FAN_UP_TIME =                     10
    __FAN_DOWN_TIME =                   2

    __CMD_POWER =                       0x03
    __CMD_POWER_ON =                    0x00        # 0x03, 0x00
    __CMD_POWER_OFF =                   0x01        # 0x03, 0x01

    __CMD_CHECK_STATUS =                0xcf
    __CMD_READ_HISTOGRAM =              0x30
    __CMD_GET_FIRMWARE =                0x3f

    __SPI_CLOCK =                       488000
    __SPI_MODE =                        1

    __DELAY_CMD =                       0.010
    __DELAY_TRANSFER =                  0.001

    __LOCK_TIMEOUT =                    6.0


    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def lock_timeout(cls):
        return cls.__LOCK_TIMEOUT


    @classmethod
    def boot_time(cls):
        return cls.__BOOT_TIME


    @classmethod
    def power_cycle_time(cls):
        return cls.__POWER_CYCLE_TIME


    # ----------------------------------------------------------------------------------------------------------------

    def __init__(self, load_switch_active_high, spi_bus, spi_device):
        """
        Constructor
        """
        super().__init__(load_switch_active_high, spi_bus, spi_device, self.__SPI_MODE, self.__SPI_CLOCK)


    # ----------------------------------------------------------------------------------------------------------------

    def operations_on(self):
        try:
            self.obtain_lock()
            self._spi.open()

            # start...
            self.__cmd_power(self.__CMD_POWER_ON)

            time.sleep(self.__START_TIME)

        finally:
            self._spi.close()
            self.release_lock()


    def operations_off(self):
        try:
            self.obtain_lock()
            self._spi.open()

            self.__cmd_power(self.__CMD_POWER_OFF)

            time.sleep(self.__STOP_TIME)

        finally:
            self._spi.close()
            self.release_lock()


    # ----------------------------------------------------------------------------------------------------------------

    def sample(self):
        try:
            self.obtain_lock()
            self._spi.open()

            # command...
            self.__cmd(self.__CMD_READ_HISTOGRAM)
            chars = self.__read_bytes(62)

            # time...
            rec = LocalizedDatetime.now()

            # bins...
            bins = [Decode.unsigned_int(chars[i:i + 2], '<') for i in range(0, 32, 2)]

            # bin MToFs...
            bin_1_mtof = chars[32]
            bin_3_mtof = chars[33]
            bin_5_mtof = chars[34]
            bin_7_mtof = chars[35]

            # period...
            period = Decode.float(chars[44:48], '<')

            # checksum...
            required = Decode.unsigned_int(chars[48:50], '<')
            actual = sum(bins) % 65536

            if required != actual:
                raise ValueError("bad checksum: required: 0x%04x actual: 0x%04x" % (required, actual))

            # PMx...
            try:
                pm1 = Decode.float(chars[50:54], '<')
            except TypeError:
                pm1 = None

            try:
                pm2p5 = Decode.float(chars[54:58], '<')
            except TypeError:
                pm2p5 = None

            try:
                pm10 = Decode.float(chars[58:62], '<')
            except TypeError:
                pm10 = None

            return OPCDatum(self.SOURCE, rec, pm1, pm2p5, pm10, period, bins,
                            bin_1_mtof, bin_3_mtof, bin_5_mtof, bin_7_mtof)

        finally:
            self._spi.close()
            self.release_lock()


    # ----------------------------------------------------------------------------------------------------------------

    def firmware(self):
        try:
            self.obtain_lock()
            self._spi.open()

            # command...
            self.__cmd(self.__CMD_GET_FIRMWARE)
            chars = self.__read_bytes(60)

            # report...
            report = ''.join(chr(byte) for byte in chars)

            return report.strip('\0\xff')       # \0 - Raspberry Pi, \xff - BeagleBone

        finally:
            self._spi.close()
            self.release_lock()


    # ----------------------------------------------------------------------------------------------------------------

    def __cmd_power(self, cmd):
        self._spi.xfer([self.__CMD_POWER, cmd])
        time.sleep(self.__DELAY_CMD)


    def __cmd(self, cmd):
        self._spi.xfer([cmd])
        time.sleep(self.__DELAY_CMD)


    def __read_bytes(self, count):
        return [self.__read_byte() for _ in range(count)]


    def __read_byte(self):
        read_bytes = self._spi.read_bytes(1)
        time.sleep(self.__DELAY_TRANSFER)

        return read_bytes[0]
