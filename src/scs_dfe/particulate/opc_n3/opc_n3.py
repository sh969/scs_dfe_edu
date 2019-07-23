"""
Created on 15 Nov 2018

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)

Firmware report:
OPC-N3 Iss1.1 FirmwareVer=1.17a...........................BS
"""

import time

from scs_core.climate.sht_datum import SHTDatum

from scs_core.data.datum import Decode
from scs_core.data.localized_datetime import LocalizedDatetime
from scs_core.data.modbus_crc import ModbusCRC

from scs_core.particulate.opc_datum import OPCDatum

from scs_dfe.climate.sht31 import SHT31

from scs_dfe.particulate.alphasense_opc import AlphasenseOPC
from scs_dfe.particulate.opc_n3.opc_status import OPCStatus


# TODO: increase power-off time on power cycle

# --------------------------------------------------------------------------------------------------------------------

class OPCN3(AlphasenseOPC):
    """
    classdocs
    """
    SOURCE =                            'N3'

    MIN_SAMPLE_PERIOD =                  5.0        # seconds
    MAX_SAMPLE_PERIOD =                 10.0        # seconds
    DEFAULT_SAMPLE_PERIOD =             10.0        # seconds

    # ----------------------------------------------------------------------------------------------------------------

    __BOOT_TIME =                       8.0         # seconds
    __POWER_CYCLE_TIME =               10.0         # seconds

    __LASER_START_TIME =                1.0         # seconds
    __FAN_START_TIME =                  5.0         # seconds

    __FAN_STOP_TIME =                   2.0         # seconds

    __CMD_POWER =                       0x03
    __CMD_LASER_ON =                    0x07
    __CMD_LASER_OFF =                   0x06
    __CMD_FAN_ON =                      0x03
    __CMD_FAN_OFF =                     0x02

    __CMD_READ_HISTOGRAM =              0x30

    __CMD_GET_FIRMWARE =                0x3f
    __CMD_GET_VERSION =                 0x12
    __CMD_GET_SERIAL =                  0x10
    __CMD_GET_STATUS =                  0x13

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

            # laser...
            for _ in range(2):
                self.__cmd_power(self.__CMD_LASER_ON)

            # fan...
            for _ in range(2):
                self.__cmd_power(self.__CMD_FAN_ON)

            time.sleep(self.__FAN_START_TIME)

        finally:
            self.release_lock()


    def operations_off(self):
        try:
            self.obtain_lock()

            # laser...
            for _ in range(2):
                self.__cmd_power(self.__CMD_LASER_OFF)

            # fan...
            for _ in range(2):
                self.__cmd_power(self.__CMD_FAN_OFF)

            time.sleep(self.__FAN_STOP_TIME)

        finally:
            self.release_lock()


    def reset(self):
        try:
            self.obtain_lock()
            self._spi.open()

            # command...
            self.__cmd(self.__CMD_RESET)

            time.sleep(self.__DELAY_TRANSFER)

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
            chars = self.__read_bytes(86)

            # checksum...
            required = Decode.unsigned_int(chars[84:86], '<')
            actual = ModbusCRC.compute(chars[:84])

            if required != actual:
                raise ValueError("bad checksum: required: 0x%04x actual: 0x%04x" % (required, actual))

            # time...
            rec = LocalizedDatetime.now()

            # bins...
            bins = [Decode.unsigned_int(chars[i:i + 2], '<') for i in range(0, 48, 2)]

            # bin MToFs...
            bin_1_mtof = chars[48]
            bin_3_mtof = chars[49]
            bin_5_mtof = chars[50]
            bin_7_mtof = chars[51]

            # period...
            raw_period = Decode.unsigned_int(chars[52:54], '<')
            period = round(float(raw_period) / 100.0, 3)

            # temperature & humidity
            raw_temp = Decode.unsigned_int(chars[56:58], '<')
            raw_humid = Decode.unsigned_int(chars[58:60], '<')

            sht = SHTDatum(SHT31.humid(raw_humid), SHT31.temp(raw_temp))

            # PMx...
            try:
                pm1 = Decode.float(chars[60:64], '<')
            except TypeError:
                pm1 = None

            try:
                pm2p5 = Decode.float(chars[64:68], '<')
            except TypeError:
                pm2p5 = None

            try:
                pm10 = Decode.float(chars[68:72], '<')
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


    def status(self):
        try:
            self.obtain_lock()
            self._spi.open()

            # command...
            self.__cmd(self.__CMD_GET_STATUS)
            chars = self.__read_bytes(6)

            # report...
            status = OPCStatus.construct(chars)

            return status

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
