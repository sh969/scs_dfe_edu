"""
Created on 23 Jan 2019

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)

Firmware report:
OPC-R1 FirmwareVer=2.10...................................BS
"""

import time

from scs_core.climate.sht_datum import SHTDatum

from scs_core.data.datum import Decode
from scs_core.data.localized_datetime import LocalizedDatetime
from scs_core.data.modbus_crc import ModbusCRC

from scs_core.particulate.opc_datum import OPCDatum

from scs_dfe.climate.sht31 import SHT31

from scs_dfe.particulate.alphasense_opc import AlphasenseOPC


# --------------------------------------------------------------------------------------------------------------------

class OPCR1(AlphasenseOPC):
    """
    classdocs
    """
    SOURCE =                            'R1'

    MIN_SAMPLE_PERIOD =                  5.0        # seconds
    MAX_SAMPLE_PERIOD =                 10.0        # seconds
    DEFAULT_SAMPLE_PERIOD =             10.0        # seconds


    # ----------------------------------------------------------------------------------------------------------------

    __BOOT_TIME =                       8.0         # seconds
    __POWER_CYCLE_TIME =               10.0         # seconds

    __FAN_START_TIME =                  3.0         # seconds
    __FAN_STOP_TIME =                   3.0         # seconds

    __CMD_POWER =                       0x03
    __CMD_PERIPHERALS_ON =              0x07
    __CMD_PERIPHERALS_OFF =             0x00

    __CMD_READ_HISTOGRAM =              0x30

    __CMD_GET_FIRMWARE =                0x3f
    __CMD_GET_VERSION =                 0x12
    __CMD_GET_SERIAL =                  0x10

    __CMD_RESET =                       0x06

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

            # peripherals...
            for _ in range(2):
                self.__cmd_power(self.__CMD_PERIPHERALS_ON)

            time.sleep(self.__FAN_START_TIME)

        finally:
            self.release_lock()


    def operations_off(self):
        try:
            self.obtain_lock()

            # peripherals...
            for _ in range(2):
                self.__cmd_power(self.__CMD_PERIPHERALS_OFF)

            time.sleep(self.__FAN_STOP_TIME)

        finally:
            self.release_lock()


    def reset(self):
        try:
            self.obtain_lock()
            self._spi.open()

            # command...
            self.__cmd(self.__CMD_RESET)

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
            chars = self.__read_bytes(64)

            # checksum...
            required = Decode.unsigned_int(chars[62:64], '<')
            actual = ModbusCRC.compute(chars[:62])

            if required != actual:
                raise ValueError("bad checksum: required: 0x%04x actual: 0x%04x" % (required, actual))

            # time...
            rec = LocalizedDatetime.now()

            # bins...
            bins = [Decode.unsigned_int(chars[i:i + 2], '<') for i in range(0, 32, 2)]

            # bin MToFs...
            bin_1_mtof = chars[32]
            bin_3_mtof = chars[33]
            bin_5_mtof = chars[34]
            bin_7_mtof = chars[35]

            # temperature & humidity
            raw_temp = Decode.unsigned_int(chars[40:42], '<')
            raw_humid = Decode.unsigned_int(chars[42:44], '<')

            sht = SHTDatum(SHT31.humid(raw_humid), SHT31.temp(raw_temp))

            # period...
            period = Decode.float(chars[44:48], '<')

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
                            bin_1_mtof, bin_3_mtof, bin_5_mtof, bin_7_mtof, sht)

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


    def version(self):
        try:
            self.obtain_lock()
            self._spi.open()

            # command...
            self.__cmd(self.__CMD_GET_VERSION)

            # report...
            major = int(self.__read_byte())
            minor = int(self.__read_byte())

            return major, minor

        finally:
            self._spi.close()
            self.release_lock()


    def serial_no(self):
        try:
            self.obtain_lock()
            self._spi.open()

            # command...
            self.__cmd(self.__CMD_GET_SERIAL)
            chars = self.__read_bytes(60)

            # report...
            report = ''.join(chr(byte) for byte in chars)
            pieces = report.split(' ')

            if len(pieces) < 2:
                return None, None

            return pieces[0], pieces[1]             # type, number

        finally:
            self._spi.close()
            self.release_lock()


    # ----------------------------------------------------------------------------------------------------------------

    def __cmd_power(self, cmd):
        try:
            self._spi.open()

            self._spi.xfer([self.__CMD_POWER, cmd])
            time.sleep(self.__DELAY_CMD)

        finally:
            self._spi.close()


    def __cmd(self, cmd):
        self._spi.xfer([cmd])
        time.sleep(self.__DELAY_CMD)

        self._spi.xfer([cmd])


    def __read_bytes(self, count):
        return [self.__read_byte() for _ in range(count)]


    def __read_byte(self):
        chars = self._spi.read_bytes(1)
        time.sleep(self.__DELAY_TRANSFER)

        return chars[0]
