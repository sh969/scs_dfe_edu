"""
Created on 8 Oct 2018

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)
"""


# --------------------------------------------------------------------------------------------------------------------

class IO(object):
    """
    a dummy I/O expander
    """
    HIGH =                  None
    LOW =                   None


    # ----------------------------------------------------------------------------------------------------------------
    # power outputs...

    @property
    def gps_power(self):
        return None

    @gps_power.setter
    def gps_power(self, level):
        pass


    @property
    def opc_power(self):
        return None


    @opc_power.setter
    def opc_power(self, level):
        pass


    @property
    def ndir_power(self):
        return None


    @ndir_power.setter
    def ndir_power(self, level):
        pass


    # ----------------------------------------------------------------------------------------------------------------
    # LED outputs...

    @property
    def led_red(self):
        return None


    @led_red.setter
    def led_red(self, level):
        pass


    @property
    def led_green(self):
        return None


    @led_green.setter
    def led_green(self, level):
        pass


    # ----------------------------------------------------------------------------------------------------------------

    def __str__(self, *args, **kwargs):
        return "IO:{device:None}"
