"""
Created on 11 Jul 2017

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)

settings for OPCMonitor

example JSON:
{"model": "R1", "sample-period": 10, "power-saving": false, "spi-bus": 0, "spi-device": 0}
"""

from collections import OrderedDict

from scs_core.data.json import PersistentJSONable

from scs_dfe.particulate.opc_monitor import OPCMonitor

from scs_dfe.particulate.opc_n2.opc_n2 import OPCN2
from scs_dfe.particulate.opc_n3.opc_n3 import OPCN3
from scs_dfe.particulate.opc_r1.opc_r1 import OPCR1

from scs_dfe.particulate.sps_30.sps_30 import SPS30


# --------------------------------------------------------------------------------------------------------------------

class OPCConf(PersistentJSONable):
    """
    classdocs
    """

    __FILENAME = "opc_conf.json"

    @classmethod
    def persistence_location(cls, host):
        return host.conf_dir(), cls.__FILENAME


    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def construct_from_jdict(cls, jdict):
        if not jdict:
            return None

        model = jdict.get('model')
        sample_period = jdict.get('sample-period')
        power_saving = jdict.get('power-saving')

        bus = jdict.get('bus')
        address = jdict.get('address')

        return OPCConf(model, sample_period, power_saving, bus, address)


    @classmethod
    def is_valid_model(cls, model):
        return model in (OPCN2.SOURCE, OPCN3.SOURCE, OPCR1.SOURCE, SPS30.SOURCE)


    # ----------------------------------------------------------------------------------------------------------------

    def __init__(self, model, sample_period, power_saving, bus, address):
        """
        Constructor
        """
        super().__init__()

        self.__model = model
        self.__sample_period = int(sample_period)
        self.__power_saving = bool(power_saving)

        self.__bus = bus
        self.__address = address


    # ----------------------------------------------------------------------------------------------------------------

    def opc_monitor(self, host, load_switch_active_high):
        opc = self.opc(host, load_switch_active_high)

        return OPCMonitor(opc, self)


    def opc(self, host, load_switch_active_high):
        if self.model == OPCN2.SOURCE:
            return OPCN2(load_switch_active_high, self.opc_bus(host), self.opc_address(host))

        elif self.model == OPCN3.SOURCE:
            return OPCN3(load_switch_active_high, self.opc_bus(host), self.opc_address(host))

        elif self.model == OPCR1.SOURCE:
            return OPCR1(load_switch_active_high, self.opc_bus(host), self.opc_address(host))

        elif self.model == SPS30.SOURCE:
            return SPS30(load_switch_active_high, self.opc_bus(host), SPS30.DEFAULT_ADDR)

        raise ValueError('unknown model: %s' % self.model)


    # ----------------------------------------------------------------------------------------------------------------

    def opc_bus(self, host):
        try:
            return int(self.__bus)

        except TypeError:
            return host.opc_spi_bus()


    def opc_address(self, host):
        try:
            return int(self.__address)

        except TypeError:
            return host.opc_spi_device()


    # ----------------------------------------------------------------------------------------------------------------

    @property
    def model(self):
        return self.__model


    @property
    def sample_period(self):
        return self.__sample_period


    @property
    def power_saving(self):
        return self.__power_saving


    @property
    def bus(self):
        return self.__bus


    @property
    def address(self):
        return self.__address


    # ----------------------------------------------------------------------------------------------------------------

    def as_json(self):
        jdict = OrderedDict()

        jdict['model'] = self.__model
        jdict['sample-period'] = self.__sample_period
        jdict['power-saving'] = self.__power_saving

        if self.__bus is not None:
            jdict['bus'] = self.__bus

        if self.__address is not None:
            jdict['address'] = self.__address

        return jdict


    # ----------------------------------------------------------------------------------------------------------------

    def __str__(self, *args, **kwargs):
        return "OPCConf:{model:%s, sample_period:%s, power_saving:%s, bus:%s, address:%s}" %  \
               (self.model, self.sample_period, self.power_saving, self.bus, self.address)
