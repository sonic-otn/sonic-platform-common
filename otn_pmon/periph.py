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

from sonic_py_common import logger
from otn_pmon.device.ttypes import periph_type
from otn_pmon.thrift_client import thrift_try
from swsscommon import swsscommon
from otn_pmon.base import Pm, Alarm, slot_status
import otn_pmon.db as db
import otn_pmon.utils as utils

class Periph(object):
    def __init__(self, type, id):
        self.type = type
        self.id = id
        self.name = self.__get_name()
        self.table_name = periph_type._VALUES_TO_NAMES[type]
        self.dbs = db.get_dbs(self.name, [swsscommon.CONFIG_DB, swsscommon.STATE_DB, swsscommon.COUNTERS_DB])
        self.state_initialized = False

        self.log = logger.Logger(self.table_name, logger.Logger.LOG_FACILITY_DAEMON, (logger.Logger.LOG_OPTION_NDELAY | logger.Logger.LOG_OPTION_PID))
        self.log.set_min_log_priority_info()

    def __get_name(self) :
        type_string = periph_type._VALUES_TO_NAMES[self.type]
        if self.type == periph_type.FAN or self.type == periph_type.PSU or self.type == periph_type.LINECARD :
            name = f"{type_string}-1-{self.id}"
        else :
            name = f"{type_string}-{self.id}"
        return name

    def synchronize(self) :
        try:
            if self.get_presence() :
                # self.initialize()
                self.synchronize_presence()
                print("{} synchronize_presence done".format(self.name))
            else :
                self.synchronize_not_presence()
                print("{} synchronize_not_presence done".format(self.name))
        except Exception as e :
            self.log.log_warning(f"Failed to synchronize {self.name} as error : {e}")

    def synchronize_presence(self) :
        if not self.state_initialized :
            print("{} initialize_state doing".format(self.name))
            self.initialize_state()
            self.state_initialized = True
        else :
            print("{} update_state doing".format(self.name))
            self.update_state()

    def synchronize_not_presence(self):
        self.state_initialized = False
        self.dbs[swsscommon.STATE_DB].delete_entry(self.table_name, self.name)
        Alarm.clearAll(self.name)
 
        data = [
            ("empty", "true"),
            ("slot-status", "Empty"),
        ]
        self.dbs[swsscommon.STATE_DB].set(self.table_name, self.name, data)

        card_miss = Alarm(self.name, "CARD_MISS")
        card_miss.create()

    def update_state(self) :
        state_db = self.dbs[swsscommon.STATE_DB]
        if self.removable() :
            while True :
                # the slot-status is still INIT until the initialization completed.
                rss = self.get_slot_status()
                if rss != slot_status.INIT :
                    print(f"real-slot-status {slot_status._VALUES_TO_NAMES[rss]}")
                    oper_status = utils.slot_status_to_oper_status(rss)
                    state_db.set_field(self.table_name, self.name, "oper-status", oper_status)
                    # initializing completed with slot-status changed
                    break
        else :
            oper_status = utils.slot_status_to_oper_status(slot_status.READY)
            state_db.set_field(self.table_name, self.name, "oper-status", oper_status)

    def update_pm(self, pm_name, value):
        pm15 = Pm(self.table_name, self.name, pm_name, "15")
        pm24 = Pm(self.table_name, self.name, pm_name, "24")
        pm15.update(value)
        pm24.update(value)

    def update_alarm(self):
        pass
    
    def removable(self) :
        if self.type in (periph_type.LINECARD, periph_type.FAN, periph_type.PSU) :
            return True
        return False

    def initialize(self):
        def inner(client):
            return client.initialize(self.type, self.id)
        return thrift_try(inner)
      
    def get_presence(self):
        def inner(client):
            return client.periph_presence(self.type, self.id)
        return thrift_try(inner)

    def get_version(self):
        def inner(client):
            return client.get_periph_version(self.type, self.id)
        return thrift_try(inner)

    def get_temperature(self):
        def inner(client):
            return client.get_periph_temperature(self.type, self.id)
        return thrift_try(inner) / 100

    def get_slot_status(self):
        state_db = self.dbs[swsscommon.STATE_DB]
        ok, status = state_db.get_field(self.table_name, self.name, "slot-status")
        if ok and status in slot_status._NAMES_TO_VALUES :
            return slot_status._NAMES_TO_VALUES[status.upper()]

        return None

    def get_periph_eeprom(self):
        def inner(client):
            return client.get_periph_eeprom(self.type, self.id)
        return thrift_try(inner)

    def set_led_color(self, type, id, color):
        def inner(client):
            return client.set_led_color(type, id, color)
        return thrift_try(inner)