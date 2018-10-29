"""
Created on 27 Feb 2018

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)

The DFE configuration file must be present to enable sampling operations. In this configuration it has no fields.

example document:
{"pt1000-addr": null}
"""

import os

from collections import OrderedDict

from scs_core.data.json import PersistentJSONable

from scs_core.gas.afe_baseline import AFEBaseline
from scs_core.gas.afe_calib import AFECalib

from scs_dfe.board.mcp9808 import MCP9808

from scs_dfe.gas.afe import AFE


# --------------------------------------------------------------------------------------------------------------------

# noinspection PyUnusedLocal
class DFEConf(PersistentJSONable):
    """
    classdocs
    """

    # ----------------------------------------------------------------------------------------------------------------

    __FILENAME = "dfe_conf.json"

    @classmethod
    def filename(cls, host):
        return os.path.join(host.conf_dir(), cls.__FILENAME)


    # ----------------------------------------------------------------------------------------------------------------

    @staticmethod
    def board_temp_sensor():
        return MCP9808(True)


    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def construct_from_jdict(cls, jdict):
        if not jdict:
            return None

        return DFEConf(None)


    # ----------------------------------------------------------------------------------------------------------------

    def __init__(self, pt1000_addr):
        """
        Constructor
        """
        super().__init__()

        self.__pt1000_addr = pt1000_addr            # int


    # ----------------------------------------------------------------------------------------------------------------

    def afe(self, host):
        # sensors...
        afe_calib = AFECalib.load(host)
        afe_baseline = AFEBaseline.load(host)

        sensors = afe_calib.sensors(afe_baseline)

        return AFE(self, None, sensors)


    @staticmethod
    def pt1000(host):
        return None


    @staticmethod
    def pt1000_adc(gain, rate):
        return None


    # ----------------------------------------------------------------------------------------------------------------

    @property
    def pt1000_addr(self):
        return None


    # ----------------------------------------------------------------------------------------------------------------

    def as_json(self):
        jdict = OrderedDict()

        jdict['pt1000-addr'] = None

        return jdict


    # ----------------------------------------------------------------------------------------------------------------

    def __str__(self, *args, **kwargs):
        return "DFEConf:{pt1000_addr:None}"
