"""
Created on 16 Nov 2018

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)
"""

from collections import OrderedDict

from scs_core.data.json import JSONable


# --------------------------------------------------------------------------------------------------------------------

class OPCStatus(JSONable):
    """
    classdocs
    """

    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def construct(cls, chars):
        if len(chars) != 6:
            raise ValueError(chars)

        fan_on = chars[0]
        laser_dac_on = chars[1]
        fan_dac_value = chars[2]
        laser_dac_value = chars[3]
        laser_switch = chars[4]
        gain_toggle = chars[5]

        return OPCStatus(fan_on, laser_dac_on, fan_dac_value, laser_dac_value, laser_switch, gain_toggle)


    # ----------------------------------------------------------------------------------------------------------------

    def __init__(self, fan_on, laser_dac_on, fan_dac_value, laser_dac_value, laser_switch, gain_toggle):
        """
        Constructor
        """
        self.__fan_on = int(fan_on)
        self.__laser_dac_on = int(laser_dac_on)
        self.__fan_dac_value = int(fan_dac_value)
        self.__laser_dac_value = int(laser_dac_value)
        self.__laser_switch = int(laser_switch)
        self.__gain_toggle = int(gain_toggle)


    # ----------------------------------------------------------------------------------------------------------------

    def fan_is_on(self):
        return self.fan_on & 0x01


    def laser_is_on(self):
        return self.laser_switch & 0x01


    # ----------------------------------------------------------------------------------------------------------------

    def as_json(self):
        jdict = OrderedDict()

        jdict['fan-on'] = self.fan_on
        jdict['laser-dac-on'] = self.laser_dac_on
        jdict['fan-dac-value'] = self.fan_dac_value
        jdict['laser-dac-value'] = self.laser_dac_value
        jdict['laser-switch'] = self.laser_switch
        jdict['gain-toggle'] = self.gain_toggle

        return jdict


    # ----------------------------------------------------------------------------------------------------------------

    @property
    def fan_on(self):
        return self.__fan_on


    @property
    def laser_dac_on(self):
        return self.__laser_dac_on


    @property
    def fan_dac_value(self):
        return self.__fan_dac_value


    @property
    def laser_dac_value(self):
        return self.__laser_dac_value


    @property
    def laser_switch(self):
        return self.__laser_switch


    @property
    def gain_toggle(self):
        return self.__gain_toggle


    # ----------------------------------------------------------------------------------------------------------------

    def __str__(self, *args, **kwargs):
        return "OPCStatus:{fan_on:0x%02x, laser_dac_on:0x%02x, fan_dac_value:0x%02x, laser_dac_value:0x%02x, " \
               "laser_switch:0x%02x, gain_toggle:0x%02x}" % \
               (self.fan_on, self.laser_dac_on, self.fan_dac_value, self.laser_dac_value,
                self.laser_switch, self.gain_toggle)
