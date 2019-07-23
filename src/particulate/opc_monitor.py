"""
Created on 9 Jul 2017

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)
"""

import sys
import time

from collections import OrderedDict
from multiprocessing import Manager

from scs_core.sync.interval_timer import IntervalTimer
from scs_core.sync.synchronised_process import SynchronisedProcess

from scs_dfe.particulate.opc import OPC

from scs_host.lock.lock_timeout import LockTimeout


# TODO: should be able to start and stop the OPC on very long sampling intervals

# --------------------------------------------------------------------------------------------------------------------

class OPCMonitor(SynchronisedProcess):
    """
    classdocs
    """
    __MAX_PERMITTED_ZERO_READINGS =      3

    __FATAL_ERROR =                     -1


    # ----------------------------------------------------------------------------------------------------------------

    def __init__(self, opc: OPC, conf):
        """
        Constructor
        """
        manager = Manager()

        SynchronisedProcess.__init__(self, manager.list())

        self.__opc = opc
        self.__conf = conf

        self.__first_reading = True
        self.__datum_class = self.__opc.datum_class()


    # ----------------------------------------------------------------------------------------------------------------
    # SynchronisedProcess implementation...

    def start(self):
        try:
            self.__opc.power_on()
            self.__opc.operations_on()

            self.__first_reading = True

            super().start()

        except KeyboardInterrupt:
            pass


    def stop(self):
        try:
            super().stop()

            self.__opc.operations_off()
            self.__opc.power_off()

        except (KeyboardInterrupt, LockTimeout, OSError):
            pass


    def run(self):
        try:
            # clean...
            self.__opc.clean()

            # sample...
            timer = IntervalTimer(self.__conf.sample_period)

            zero_count = 0

            while timer.true():
                try:
                    if not self.__opc.data_ready():
                        print("OPCMonitor.run: data not ready.", file=sys.stderr)
                        self.__empty()
                        continue

                    datum = self.__opc.sample()

                    if datum.is_zero():
                        zero_count += 1

                        if zero_count > self.__MAX_PERMITTED_ZERO_READINGS:
                            raise ValueError("zero reading")

                    else:
                        zero_count = 0

                    if not self.__first_reading:
                        with self._lock:
                            datum.as_list(self._value)

                except LockTimeout as ex:
                    print("OPCMonitor.run: %s" % ex, file=sys.stderr)
                    self.__empty()

                except ValueError as ex:
                    print("OPCMonitor.run: %s" % ex, file=sys.stderr)
                    self.__empty()
                    self.__power_cycle()

                except OSError as ex:
                    print("OPCMonitor.run: %s" % ex, file=sys.stderr)
                    self.__error(self.__FATAL_ERROR)
                    break

                if self.__first_reading:
                    self.__first_reading = False

        except KeyboardInterrupt:
            pass


    # ----------------------------------------------------------------------------------------------------------------
    # SynchronisedProcess special operations...

    def __error(self, code):
        with self._lock:
            del self._value[:]
            self._value.append(code)


    def __empty(self):
        with self._lock:
            del self._value[:]


    def __power_cycle(self):
        print("OPCMonitor: power cycle", file=sys.stderr)
        sys.stderr.flush()

        try:
            # off...
            self.__opc.operations_off()
            self.__opc.power_off()

            time.sleep(self.__opc.power_cycle_time())

            # on...
            self.__opc.power_on()
            self.__opc.operations_on()

            self.__first_reading = True

        except KeyboardInterrupt:
            pass


    # ----------------------------------------------------------------------------------------------------------------
    # data retrieval for client process...

    def firmware(self):
        return self.__opc.firmware()


    def sample(self):
        with self._lock:
            value = self._value

        if len(value) == 1 and value[0] == self.__FATAL_ERROR:
            raise StopIteration()

        return None if value is None else self.__datum_class.construct_from_jdict(OrderedDict(value))


    # ----------------------------------------------------------------------------------------------------------------

    def __str__(self, *args, **kwargs):
        return "OPCMonitor:{value:%s, opc:%s, conf:%s, first_reading:%s}" % \
               (self._value, self.__opc, self.__conf, self.__first_reading)
