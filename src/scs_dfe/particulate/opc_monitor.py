"""
Created on 9 Jul 2017

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)
"""

import sys
import time

from collections import OrderedDict
from multiprocessing import Manager

from scs_core.particulate.opc_datum import OPCDatum

from scs_core.sync.interval_timer import IntervalTimer
from scs_core.sync.synchronised_process import SynchronisedProcess

from scs_dfe.particulate.opc_n2 import OPCN2

from scs_host.lock.lock_timeout import LockTimeout


# TODO: should be able to start and stop the OPC on very long sampling intervals

# --------------------------------------------------------------------------------------------------------------------

class OPCMonitor(SynchronisedProcess):
    """
    classdocs
    """

    # ----------------------------------------------------------------------------------------------------------------

    def __init__(self, opc, conf):
        """
        Constructor
        """
        manager = Manager()

        SynchronisedProcess.__init__(self, manager.list())

        self.__opc = opc
        self.__conf = conf


    # ----------------------------------------------------------------------------------------------------------------
    # SynchronisedProcess implementation...

    def start(self):
        try:
            self.__opc.power_on()
            self.__opc.operations_on()

            super().start()

        except KeyboardInterrupt:
            pass


    def stop(self):
        try:
            super().stop()

            self.__opc.operations_off()
            self.__opc.power_off()

        except KeyboardInterrupt:
            pass

        except LockTimeout:             # because __power_cycle() may be running!
            pass


    def run(self):
        self.__opc.sample()     # reset counts

        try:
            timer = IntervalTimer(self.__conf.sample_period)

            while timer.true():
                sample = self.__opc.sample()

                # report...
                with self._lock:
                    sample.as_list(self._value)

                # monitor...
                if sample.is_zero():
                    self.__power_cycle()

        except KeyboardInterrupt:
            pass


    # ----------------------------------------------------------------------------------------------------------------
    # SynchronisedProcess special operations...

    def __power_cycle(self):
        print("OPCMonitor: POWER CYCLE", file=sys.stderr)
        sys.stderr.flush()

        try:
            # off...
            self.__opc.operations_off()
            self.__opc.power_off()

            time.sleep(OPCN2.POWER_CYCLE_TIME)

            # on...
            self.__opc.power_on()
            self.__opc.operations_on()

        except KeyboardInterrupt:
            pass


    # ----------------------------------------------------------------------------------------------------------------
    # data retrieval for client process...

    def firmware(self):
        return self.__opc.firmware()


    def sample(self):
        with self._lock:
            value = self._value

        return OPCDatum.construct_from_jdict(OrderedDict(value))


    # ----------------------------------------------------------------------------------------------------------------

    def __str__(self, *args, **kwargs):
        return "OPCMonitor:{value:%s, opc:%s, conf:%s}" % (self._value, self.__opc, self.__conf)
