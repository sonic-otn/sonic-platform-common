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

from functools import lru_cache
from otn_pmon.common import *
from otn_pmon.alarm import Alarm
import otn_pmon.periph as periph
import otn_pmon.chassis as chassis
import otn_pmon.db as db
from otn_pmon.thrift_api.ttypes import error_code, led_color, periph_type
from otn_pmon.thrift_client import thrift_try

@lru_cache()
class Psu(periph.Periph):
    def __init__(self, id):
        super().__init__(periph_type.PSU, id)
        self.boot_timeout_secs = 10

    def __get_psu_info(self):
        def inner(client):
            return client.get_psu_info(self.id)

        result = thrift_try(inner)
        if result.ret != error_code.OK :
            return None

        return result.info

    def __psu_vin_high(self) :
        def inner(client):
            return client.psu_vin_high(self.id)
        return thrift_try(inner)

    def __psu_vin_low(self) :
        def inner(client):
            return client.psu_vin_low(self.id)
        return thrift_try(inner)

    def __expected_psu(self, pn) :
        expected_pn = periph.get_periph_expected_pn(self.type)
        if pn in expected_pn :
            return True
        return False

    def initialize_state(self):
        inv = self.get_inventory()
        if not inv :
            return

        psu_info = self.__get_psu_info()
        if not psu_info :
            return

        s_status = self.get_slot_status()
        if not s_status or s_status == slot_status.EMPTY :
            s_status = slot_status.INIT

        data = [
            ('part-no', inv.pn),
            ('serial-no', inv.sn),
            ('mfg-date', inv.mfg_date),
            ('hardware-version', inv.hw_ver),
            ("parent", "CHASSIS-1"),
            ("empty", "false"),
            ('removable', "true"),
            ("mfg-name", "alibaba"),
            ("oper-status", periph.slot_status_to_oper_status(s_status)),
            ("slot-status", get_slot_status_name(s_status)),
            ("capacity",   str(psu_info.capacity)),
        ]

        self.dbs[db.STATE_DB].set(self.table_name, self.name, data)

    def update_pm(self):
        temp = self.get_temperature()
        super().update_pm("Temperature", temp)

        psu_info = self.__get_psu_info()
        if not psu_info :
            return

        super().update_pm("InputCurrent",  psu_info.iin)
        super().update_pm("InputVoltage",  psu_info.vin)
        super().update_pm("InputPower",    psu_info.pin)
        super().update_pm("OutputCurrent", psu_info.iout)
        super().update_pm("OutputPower",   psu_info.pout)
        super().update_pm("OutputVoltage", psu_info.vout)

        super().update_pm("AmbientTemperature", psu_info.ambient_temp)
        super().update_pm("PrimaryTemperature", psu_info.primary_temp)
        super().update_pm("SecondaryTemperature", psu_info.secondary_temp)
        super().update_pm("FanSpeed", psu_info.fan)

    def mismatch(self) :
        psu_info = self.__get_psu_info()
        if not psu_info :
            return False

        cpc = chassis.get_chassis_power_capacity()
        if cpc != psu_info.capacity :
            return True

        return False

    def unknown(self) :
        inv = self.get_inventory()
        # check unknown as the pn is expected or not
        if inv and inv.pn and not self.__expected_psu(inv.pn) :
            return True
 
        return False

    def __proc_vin_alarm(self) :
        vin_h = Alarm(self.name, "VOLTAGE_INPUT_HIGH")
        if self.__psu_vin_high() :
            vin_h.create()
        else :
            vin_h.clear()

        vin_l = Alarm(self.name, "VOLTAGE_INPUT_LOW")
        if self.__psu_vin_low() :
            vin_l.create()
        else :
            vin_l.clear()

    def update_alarm(self):
        cur_status = self.get_slot_status()
        if cur_status == slot_status.UNKNOWN :
            alarm = Alarm(self.name, "CRD_UNKNOWN")
            alarm.createAndClearOthers()
        elif cur_status == slot_status.MISMATCH :
            alarm = Alarm(self.name, "PSU_MISMATCH")
            alarm.createAndClearOthers()
        elif cur_status == slot_status.READY :
            Alarm.clearBy(self.name, "CRD_UNKNOWN")
            Alarm.clearBy(self.name, "PSU_MISMATCH")
            self.__proc_vin_alarm()