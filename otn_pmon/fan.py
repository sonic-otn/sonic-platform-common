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

from otn_pmon.base import Alarm, slot_status
import otn_pmon.periph as periph
import otn_pmon.utils as utils
from functools import lru_cache
from otn_pmon.device.ttypes import led_color, periph_type
from otn_pmon.thrift_client import thrift_try
from swsscommon import swsscommon

@lru_cache()
class Fan(periph.Periph) :
    SPEED_MAX = 31000
    SPEED_MIN = 6000

    def __init__(self, id):
        super().__init__(periph_type.FAN, id)

    def initialize_state(self):
        Alarm.clearAll(self.name)
        eeprom = self.get_periph_eeprom()
        data = [
            ('part-no', eeprom.pn),
            ('serial-no', eeprom.sn),
            ('mfg-date', eeprom.mfg_date),
            ('hardware-version', eeprom.hw_ver),
            ("parent", "CHASSIS-1"),
            ("empty", "false"),
            ('removable', "true"),
            ("mfg-name", "alibaba"),
            ("oper-status", utils.slot_status_to_oper_status(slot_status.INIT)),
            ("slot-status", slot_status._VALUES_TO_NAMES[slot_status.INIT]),
        ]

        self.dbs[swsscommon.STATE_DB].set(self.table_name, self.name, data)

    def __get_speed(self):
        def inner(client):
            return client.get_fan_speed(self.id)
        return thrift_try(inner)

    def update_pm(self):
        temp = self.get_temperature()
        super().update_pm("Temperature", temp)

        speed = self.__get_speed()
        super().update_pm("Speed", speed.front)
        super().update_pm("Speed_2", speed.behind)

        pass

    def update_alarm(self):
        speed_high = Alarm(self.name, "FAN_HIGH")
        speed_low = Alarm(self.name, "FAN_LOW")
        fan_fail = Alarm(self.name, "FAN_FAIL")

        speed = self.__get_speed()
        max_speed = speed.front if speed.front >= speed.behind else speed.behind
        min_speed = speed.front if speed.front <= speed.behind else speed.behind

        if max_speed > Fan.SPEED_MAX :
            speed_high.createAndClear("FAN")
        elif max_speed == 0 or min_speed == 0 :
            fan_fail.createAndClear("FAN")
        elif min_speed < Fan.SPEED_MIN :
            speed_low.createAndClear("FAN")
        else :
            Alarm.clearAll(self.name)