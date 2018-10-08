"""
Created on 19 Jun 2018

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)

Based-on code
https://gist.github.com/asciiphil/6167905

References
https://www.nxp.com/docs/en/data-sheet/MPL115A2.pdf
https://www.nxp.com/docs/en/application-note/AN3785.pdf
https://community.nxp.com/thread/73878
"""

from scs_host.bus.i2c import I2C


# --------------------------------------------------------------------------------------------------------------------

class MPL115A2Reg:
    """
    NXP MPL115A2 digital barometer - I2C control
    """

    __I2C_ADDR =            0x60

    __CMD_START_CONV =      0x12


    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def convert(cls):
        try:
            I2C.start_tx(MPL115A2Reg.__I2C_ADDR)
            I2C.write(cls.__CMD_START_CONV, 0x00)

        finally:
            I2C.end_tx()


    # ----------------------------------------------------------------------------------------------------------------

    def __init__(self, reg_addr, total, sign, fractional, zero_padding):
        self.__reg_addr = reg_addr

        self.__total = total
        self.__sign = sign
        self.__fractional = fractional

        self.__zero_padding = zero_padding


    # ----------------------------------------------------------------------------------------------------------------

    def read(self):
        # read...
        raw_value = self.__read_raw()

        # convert...
        if self.__sign and (raw_value & 0x8000):        # TODO: do it like STMicro code
            raw_value = raw_value ^ 0xffff * -1

        return (raw_value >> (16 - self.__total)) / float(2 ** (self.__fractional + self.__zero_padding))


    # ----------------------------------------------------------------------------------------------------------------

    def __read_raw(self):
        try:
            I2C.start_tx(self.__I2C_ADDR)
            values = I2C.read_cmd(self.__reg_addr, 2)

            return values[0] << 8 | values[1]

        finally:
            I2C.end_tx()


    # ----------------------------------------------------------------------------------------------------------------

    def __str__(self, *args, **kwargs):
        return "MPL115A2Reg:{reg_addr:0x%2x, total:%s, sign:%s, fractional:%s, zero_padding:%s}" % \
               (self.__reg_addr, self.__total, self.__sign, self.__fractional, self.__zero_padding)
