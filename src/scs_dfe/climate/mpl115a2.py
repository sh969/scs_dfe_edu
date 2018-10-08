"""
Created on 19 Jun 2018

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)

Based-on code
https://gist.github.com/asciiphil/6167905
https://github.com/hackscribble/microbit-MPL115A1-barometer/blob/master/microbit-MPL115A1-barometer.py
https://gist.github.com/cubapp/23dd4e91814a995b8ff06f406679abcf

References
https://www.nxp.com/docs/en/data-sheet/MPL115A2.pdf
https://www.nxp.com/docs/en/application-note/AN3785.pdf
https://community.nxp.com/thread/73878
"""

import time

from scs_core.climate.mpl115a2_datum import MPL115A2Datum

from scs_dfe.climate.mpl115a2_reg import MPL115A2Reg

from scs_host.lock.lock import Lock


# --------------------------------------------------------------------------------------------------------------------

class MPL115A2(object):
    """
    NXP MPL115A2 digital barometer - orchestration
    """

    # ----------------------------------------------------------------------------------------------------------------

    __CONVERSION_TIME = 0.005                                   # seconds

    __LOCK_TIMEOUT =    1.0

    # sampling...
    __REG_P_ADC =       MPL115A2Reg(0x00, 10, 0, 0, 0)
    __REG_T_ADC =       MPL115A2Reg(0x02, 10, 0, 0, 0)

    # calibration...
    __REG_A0 =          MPL115A2Reg(0x04, 16, 1, 3, 0)
    __REG_B1 =          MPL115A2Reg(0x06, 16, 1, 13, 0)
    __REG_B2 =          MPL115A2Reg(0x08, 16, 1, 14, 0)
    __REG_C12 =         MPL115A2Reg(0x0a, 14, 1, 13, 9)


    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def construct(cls, calib):
        c25 = None if calib is None else calib.c25

        return MPL115A2(c25)


    # ----------------------------------------------------------------------------------------------------------------

    def __init__(self, c25):
        """
        Constructor
        """
        self.__c25 = c25

        self.__a0 = None
        self.__b1 = None
        self.__b2 = None
        self.__c12 = None


    # ----------------------------------------------------------------------------------------------------------------

    def init(self):
        try:
            self.obtain_lock()

            self.__a0 = self.__REG_A0.read()
            self.__b1 = self.__REG_B1.read()
            self.__b2 = self.__REG_B2.read()
            self.__c12 = self.__REG_C12.read()

        finally:
            self.release_lock()


    def sample(self, altitude=None):
        try:
            self.obtain_lock()

            MPL115A2Reg.convert()
            time.sleep(self.__CONVERSION_TIME)

            # read...
            p_adc = self.__REG_P_ADC.read()
            t_adc = self.__REG_T_ADC.read()

            # interpret...
            p_comp = self.__a0 + (self.__b1 + self.__c12 * t_adc) * p_adc + self.__b2 * t_adc

            return MPL115A2Datum.construct(self.__c25, p_comp, t_adc, altitude)

        finally:
            self.release_lock()


    # ----------------------------------------------------------------------------------------------------------------

    def obtain_lock(self):
        Lock.acquire(self.__class__.__name__, self.__LOCK_TIMEOUT)


    def release_lock(self):
        Lock.release(self.__class__.__name__)


    # ----------------------------------------------------------------------------------------------------------------

    def __str__(self, *args, **kwargs):
        return "MPL115A2:{c25:%s, a0:%s, b1:%s, b2:%s, c12:%s}" % \
               (self.__c25, self.__a0, self.__b1, self.__b2, self.__c12)
