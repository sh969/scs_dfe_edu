"""
Created on 10 Nov 2018

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)

a dummy LED state, to maintain compatibility with the DFE Eng package
"""

from collections import OrderedDict

from scs_core.data.json import JSONable


# --------------------------------------------------------------------------------------------------------------------

class LEDState(JSONable):
    """
    classdocs
    """

    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def construct_from_jdict(cls, _):
        return LEDState(None, None)


    # ----------------------------------------------------------------------------------------------------------------

    # noinspection PyUnusedLocal
    def __init__(self, colour0, colour1):
        """
        Constructor
        """
        pass


    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def is_valid(cls):
        return None


    # ----------------------------------------------------------------------------------------------------------------

    def as_json(self):
        jdict = OrderedDict()

        jdict['colour0'] = None
        jdict['colour1'] = None

        return jdict


    # ----------------------------------------------------------------------------------------------------------------

    @property
    def colour0(self):
        return None


    @property
    def colour1(self):
        return None


    # ----------------------------------------------------------------------------------------------------------------

    def __str__(self, *args, **kwargs):
        return "LEDState:{colour0:None, colour1:None}"
