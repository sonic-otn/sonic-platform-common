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
class Chassis(periph.Periph):
    TEMP_HIGH_ALARM_THRESH = 55.0
    TEMP_HIGH_WARN_THRESH  = 50.0
    TEMP_LOW_WARN_THRESH   = 15.0
    TEMP_LOW_ALARM_THRESH  = 10.0
    DISK_USAGE_THRESH = 90.0

    def __init__(self, id):
        super().__init__(periph_type.CHASSIS, id)
    
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

    def update_pm(self) :
        temp = self.get_temperature()
        super().update_pm("Temperature", temp)

    def __get_disk_usage(self) :
        return psutil.disk_usage("/").percent

    def update_alarm(self) :
        disk_full = Alarm(self.name, "DISK_FULL")
        disk_usage = self.__get_disk_usage()
        if disk_usage >= Chassis.DISK_USAGE_THRESH :
            disk_full.create()
        else :
            disk_full.clear()

        temp_hi_alm = Alarm(self.name, "CHASSIS_TEMP_HIALM")
        temp_hi_wrn = Alarm(self.name, "CHASSIS_TEMP_HIWAR")
        temp_lo_alm = Alarm(self.name, "CHASSIS_TEMP_LOALM")
        temp_lo_wrn = Alarm(self.name, "CHASSIS_TEMP_LOWAR")
        temp = self.get_temperature()
        if temp > Chassis.TEMP_HIGH_ALARM_THRESH :
            temp_hi_alm.createAndClear("CHASSIS_TEMP")
        elif Chassis.TEMP_HIGH_WARN_THRESH <= temp <= Chassis.TEMP_HIGH_ALARM_THRESH :
            temp_hi_wrn.createAndClear("CHASSIS_TEMP")
        elif Chassis.TEMP_LOW_ALARM_THRESH <= temp <= Chassis.TEMP_LOW_WARN_THRESH :
            temp_lo_wrn.createAndClear("CHASSIS_TEMP")
        elif temp < Chassis.TEMP_LOW_ALARM_THRESH :
            temp_lo_alm.createAndClear("CHASSIS_TEMP")
        else :
            Alarm.clearAll(self.name)
