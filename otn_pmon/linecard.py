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
import otn_pmon.periph as periph
import otn_pmon.db as db
from otn_pmon.thrift_api.ttypes import led_color, power_ctl_type, periph_type
from otn_pmon.thrift_client import thrift_try

@lru_cache()
class Linecard(periph.Periph):
    def __init__(self, id):
        super().__init__(periph_type.LINECARD, id)
        self.boot_timeout_secs = 8 * 60

    def initialize_state(self):
        s_status = self.get_slot_status()
        if not s_status or s_status != slot_status.READY :
            s_status = slot_status.INIT

        data = [
            ("parent", "CHASSIS-1"),
            ("empty", "false"),
            ("removable", "true"),
            ("power-admin-state", "POWER_ENABLED"),
            ("mfg-name", "alibaba"),
            ("oper-status", periph.slot_status_to_oper_status(s_status)),
            ("slot-status", get_slot_status_name(s_status)),
        ]

        # initialize inventory info if linecard`s eeprom can be read by thrift
        inv = self.get_inventory()
        if inv :
            extend = [
                ("linecard-type", inv.type),
                ("part-no", inv.pn),
                ("serial-no", inv.sn),
                ("mfg-date", inv.mfg_date),
                ("hardware-version", inv.hw_ver),
            ]
            data.extend(extend)
            # the host controls the power on|off if the real card type can be read from eeprom
            self.set_power_control(power_ctl_type.ON)

        self.dbs[db.STATE_DB].set(self.table_name, self.name, data)

    def __get_subcomponents(self, card_type):
        if card_type == "E100C" :
            return f"AMPLIFIER-1-{self.id}-1,AMPLIFIER-1-{self.id}-2,ATTENUATOR-1-{self.id}-1,ATTENUATOR-1-{self.id}-3,OSC-1-{self.id}-1,MUX-1-{self.id}-1,OSC-1-{self.id}-1,PORT-1-{self.id}-L1IN,PORT-1-{self.id}-L1OUT"
        elif card_type == "E110C" :
            return f"AMPLIFIER-1-{self.id}-1,AMPLIFIER-1-{self.id}-2,ATTENUATOR-1-{self.id}-1,ATTENUATOR-1-{self.id}-2,ATTENUATOR-1-{self.id}-3,APS-1-{self.id}-1,OSC-1-{self.id}-1,MUX-1-{self.id}-1,PORT-1-{self.id}-L1IN,PORT-1-{self.id}-L1OUT,PORT-1-{self.id}-L2IN,PORT-1-{self.id}-L2OUT"
        elif card_type == "E120C" :
            return f"ATTENUATOR-1-{self.id}-1,ATTENUATOR-1-{self.id}-2,APS-1-{self.id}-1,PORT-1-{self.id}-C1IN,PORT-1-{self.id}-C1OUT,PORT-1-{self.id}-L1IN,PORT-1-{self.id}-L1OUT,PORT-1-{self.id}-L2IN,PORT-1-{self.id}-L2OUT"
        elif card_type == "P230C" :
            return f"PORT-1-{self.id}-C1,PORT-1-{self.id}-C2,PORT-1-{self.id}-C3,PORT-1-{self.id}-C4,PORT-1-{self.id}-L1,PORT-1-{self.id}-L2"
        else :
            return ""

    def set_power_control(self, type) :
        def inner(client):
            return client.set_power_control(self.id, type)
        LOG.log_info(f"set {self.name} power control {type}")
        return thrift_try(inner)

    def get_temperature(self):
        counters_db = self.dbs[db.COUNTERS_DB]
        key = f"{self.name}_Temperature:15_pm_current"
        ok, instant = counters_db.get_field(self.table_name, key, "instant")
        if not ok or not instant :
            return INVALID_TEMPERATURE
        return float(instant)

    def mismatch(self) :
        config_db = self.dbs[db.CONFIG_DB]
        ok, type_c = config_db.get_field(self.table_name, self.name, "linecard-type")
        if not ok or type_c == "NONE" :
            return False

        inv = self.get_inventory()
        if inv :
            # the real card type should be read from driver
            if inv.type.upper() != type_c.upper() :
                return True
        else :
            # the real card type should be read from db
            state_db = self.dbs[db.STATE_DB]
            ok, type_s = state_db.get_field(self.table_name, self.name, "linecard-type")
            if not ok or not type_s :
                return False

            if type_c.upper() != type_s.upper() :
                return True
 
        return False

    def update_pm(self) :
        temp = self.get_temperature()
        super().update_pm("Temperature", temp)

    def update_alarm(self) :
        super().update_alarm()