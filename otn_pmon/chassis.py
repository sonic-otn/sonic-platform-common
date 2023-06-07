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
from otn_pmon.common import *
from otn_pmon.alarm import Alarm
import otn_pmon.periph as periph
import otn_pmon.db as db
from functools import lru_cache
from otn_pmon.thrift_api.ttypes import led_color, periph_type

def get_chassis_power_capacity() :
    pc = 0
    chassis_pn = periph.get_periph_expected_pn(periph_type.CHASSIS)
    if chassis_pn and len(chassis_pn) >= 4 :
        power_type = chassis_pn[3]
        if power_type == "0" :
            pc = 550
        elif power_type == "1" :
            pc = 800
        elif power_type == "2" :
            pc = 1300
    return pc


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
        inv = self.get_inventory()
        if not inv :
            return

        data = [
            ("part-no", inv.pn),
            ("serial-no", inv.sn),
            ("mfg-date", inv.mfg_date),
            ("hardware-version", inv.hw_ver),
            ("software-version", inv.sw_ver),
            ("parent", "CHASSIS-1"),
            ("empty", "false"),
            ("removable", "false"),
            ("mfg-name", "alibaba"),
            ("oper-status", periph.slot_status_to_oper_status(slot_status.INIT)),
        ]

        self.dbs[db.STATE_DB].set(self.table_name, self.name, data)

    def get_temperature(self):
        from otn_pmon.public import get_inlet_temp
        return get_inlet_temp()

    def update_pm(self) :
        temp = self.get_temperature()
        super().update_pm("Temperature", temp)

    def __get_disk_usage(self) :
        return psutil.disk_usage("/").percent

    def update_alarm(self) :
        alarm = Alarm(self.name, "DISK_FULL")
        disk_usage = self.__get_disk_usage()
        if disk_usage >= Chassis.DISK_USAGE_THRESH :
            alarm.create()
        else :
            alarm.clear()

        alarm = None
        temp = self.get_temperature()
        if temp > Chassis.TEMP_HIGH_ALARM_THRESH :
            alarm = Alarm(self.name, "CHASSIS_TEMP_HIALM")
        elif Chassis.TEMP_HIGH_WARN_THRESH <= temp <= Chassis.TEMP_HIGH_ALARM_THRESH :
            alarm = Alarm(self.name, "CHASSIS_TEMP_HIWAR")
        elif Chassis.TEMP_LOW_ALARM_THRESH <= temp <= Chassis.TEMP_LOW_WARN_THRESH :
            alarm = Alarm(self.name, "CHASSIS_TEMP_LOWAR")
        elif temp < Chassis.TEMP_LOW_ALARM_THRESH :
            alarm = Alarm(self.name, "CHASSIS_TEMP_LOALM")

        if alarm :
            alarm.createAndClearOthers("CHASSIS_TEMP")
        else :
            Alarm.clearBy(self.name, "CHASSIS_TEMP")
