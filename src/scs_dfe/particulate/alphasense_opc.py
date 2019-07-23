"""
Created on 2 May 2019

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)
"""

from abc import ABC

from scs_core.particulate.opc_datum import OPCDatum

from scs_dfe.particulate.opc import OPC

from scs_host.bus.spi import SPI


# TODO: fix lock_name()
# TODO: fix bus and address

# --------------------------------------------------------------------------------------------------------------------

class AlphasenseOPC(OPC, ABC):
    """
    classdocs
    """

    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def uses_spi(cls):
        return True


    @classmethod
    def datum_class(cls):
        return OPCDatum


    # ----------------------------------------------------------------------------------------------------------------

    def __init__(self, load_switch_active_high, spi_bus, spi_device, spi_mode, spi_clock):
        """
        Constructor
        """
        super().__init__(load_switch_active_high)

        self._spi = SPI(spi_bus, spi_device, spi_mode, spi_clock)


    # ----------------------------------------------------------------------------------------------------------------

    def clean(self):
        pass


    @property
    def cleaning_interval(self):
        return None


    @cleaning_interval.setter
    def cleaning_interval(self, interval):
        pass


    # ----------------------------------------------------------------------------------------------------------------

    def data_ready(self):
        return True


    # ----------------------------------------------------------------------------------------------------------------

    @property
    def bus(self):
        return self._spi.bus


    @property
    def address(self):
        return self._spi.device


    # ----------------------------------------------------------------------------------------------------------------

    @property
    def lock_name(self):
        return self.__class__.__name__


    # ----------------------------------------------------------------------------------------------------------------

    def __str__(self, *args, **kwargs):
        return self.__class__.__name__ + ":{load_switch_active_high:%s, io:%s, spi:%s}" % \
               (self.load_switch_active_high, self.io, self._spi)
