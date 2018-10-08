"""
Created on 11 Jul 2017

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)

settings for OPCMonitor

example JSON:
{"model": "N2", "sample-period": 10, "power-saving": false}
"""

import os

from collections import OrderedDict

from scs_core.data.json import PersistentJSONable

from scs_dfe.particulate.opc_monitor import OPCMonitor
from scs_dfe.particulate.opc_n2 import OPCN2


# --------------------------------------------------------------------------------------------------------------------

class OPCConf(PersistentJSONable):
    """
    classdocs
    """

    __FILENAME = "opc_conf.json"

    @classmethod
    def filename(cls, host):
        return os.path.join(host.conf_dir(), cls.__FILENAME)


    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def construct_from_jdict(cls, jdict):
        if not jdict:
            return None

        model = jdict.get('model')
        sample_period = jdict.get('sample-period')
        power_saving = jdict.get('power-saving')

        return OPCConf(model, sample_period, power_saving)


    # ----------------------------------------------------------------------------------------------------------------

    def __init__(self, model, sample_period, power_saving):
        """
        Constructor
        """
        super().__init__()

        self.__model = model
        self.__sample_period = int(sample_period)
        self.__power_saving = bool(power_saving)


    # ----------------------------------------------------------------------------------------------------------------

    def opc_monitor(self, host):
        opc = self.opc(host)

        return OPCMonitor(opc, self)


    def opc(self, host):
        if self.model == 'N2':
            return OPCN2(host.opc_spi_bus(), host.opc_spi_device())

        else:
            raise ValueError('unknown model: %s' % self.model)


    # ----------------------------------------------------------------------------------------------------------------

    def has_monitor(self):
        return self.model is not None


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


    # ----------------------------------------------------------------------------------------------------------------

    def as_json(self):
        jdict = OrderedDict()

        jdict['model'] = self.__model
        jdict['sample-period'] = self.__sample_period
        jdict['power-saving'] = self.__power_saving

        return jdict


    # ----------------------------------------------------------------------------------------------------------------

    def __str__(self, *args, **kwargs):
        return "OPCConf:{model:%s, sample_period:%s, power_saving:%s}" %  \
               (self.model, self.sample_period, self.power_saving)
