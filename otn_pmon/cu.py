##
#   Copyright (c) 2021 Alibaba Group and Accelink Technologies
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#   THIS CODE IS PROVIDED ON AN *AS IS* BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
#   LIMITATION ANY IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS
#   FOR A PARTICULAR PURPOSE, MERCHANTABILITY OR NON-INFRINGEMENT.
#
#   See the Apache Version 2.0 License for specific language governing
#   permissions and limitations under the License.
##

import psutil
from otn_pmon.base import Alarm, slot_status
import otn_pmon.periph as periph
import otn_pmon.utils as utils
from functools import lru_cache
from otn_pmon.device.ttypes import led_color, periph_type
from swsscommon import swsscommon

@lru_cache()
class Cu(periph.Periph):
    CPU_MEMORY_USAGE_THRESH = 80
    CPU_MEMORY_CLEAR_THRESH = 60

    def __init__(self, id):
        super().__init__(periph_type.CU, id)
    
    def initialize_state(self):
        Alarm.clearAll(self.name)
        eeprom = self.get_periph_eeprom()
        data = [
            ("part-no", eeprom.pn),
            ("serial-no", eeprom.sn),
            ("mfg-date", eeprom.mfg_date),
            ("hardware-version", eeprom.hw_ver),
            ("software-version", eeprom.sw_ver),
            ("parent", "CHASSIS-1"),
            ("empty", "false"),
            ("removable", "false"),
            ("mfg-name", "alibaba"),
            ("oper-status", utils.slot_status_to_oper_status(slot_status.INIT)),
        ]

        self.dbs[swsscommon.STATE_DB].set(self.table_name, self.name, data)

    def __get_memory(self) :
        memory = {}
        tmp = psutil.virtual_memory()
        memory["utilized"] = tmp.used
        memory["available"] = tmp.available
        memory["percent"] = tmp.percent
        return memory

    def __get_cpu_percent(self) :
        percent = psutil.cpu_percent(interval = 1)
        return int(percent)

    def update_pm(self) :
        temp = self.get_temperature()
        super().update_pm("Temperature", temp)

        memory = self.__get_memory()
        super().update_pm("MemoryUtilized", memory["utilized"])
        super().update_pm("MemoryAvailable", memory["available"])

        percent = self.__get_cpu_percent()
        super().update_pm("CpuUtilization", percent)

    def update_alarm(self) :
        memory_hi = Alarm(self.name, "MEM_USAGE_HIGH")
        memory = self.__get_memory()
        if memory["percent"] > Cu.CPU_MEMORY_USAGE_THRESH :
            memory_hi.create()
        elif memory["percent"] < Cu.CPU_MEMORY_CLEAR_THRESH :
            memory_hi.clear()

        cpu_hi = Alarm(self.name, "CPU_USAGE_HIGH")
        cpu_percent = self.__get_cpu_percent()
        if cpu_percent > Cu.CPU_MEMORY_USAGE_THRESH :
            cpu_hi.create()
        elif cpu_percent < Cu.CPU_MEMORY_CLEAR_THRESH :
            cpu_hi.clear() 