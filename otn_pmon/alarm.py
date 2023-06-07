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

import time
import otn_pmon.db as db
from otn_pmon.common import *
from otn_pmon.thrift_api.ttypes import periph_type

_alarms = {
    "FAN_FAIL"           : {"severity" : "CRITICAL",    "service_affect" : "false", "text" : "FAN CARD FAIL"},
    "FAN_HIGH"           : {"severity" : "NOT_ALARMED", "service_affect" : "false", "text" : "FAN HIGH SPEED"},
    "FAN_LOW"            : {"severity" : "NOT_ALARMED", "service_affect" : "false", "text" : "FAN LOW SPEED"},
    "CRD_MISS"           : {"severity" : "MAJOR",       "service_affect" : "true",  "text" : "CARD MISSING"},
    "PSU_MISMATCH"       : {"severity" : "CRITICAL",    "service_affect" : "false", "text" : "PSU CARD MISMATCH"},
    "CRD_MISMATCH"       : {"severity" : "CRITICAL",    "service_affect" : "true",  "text" : "SLOT CARD MISMATCH"},
    "CRD_UNKNOWN"        : {"severity" : "CRITICAL",    "service_affect" : "true",  "text" : "SLOT CARD UNKNOWN"},
    "DISK_FULL"          : {"severity" : "MINOR",       "service_affect" : "false", "text" : "DISK SPACE ALERT"},
    "CHASSIS_TEMP_HIALM" : {"severity" : "CRITICAL",    "service_affect" : "false", "text" : "CHASSIS TEMPERATURE HIGH alarm"},
    "CHASSIS_TEMP_LOALM" : {"severity" : "CRITICAL",    "service_affect" : "false", "text" : "CHASSIS TEMPERATURE LOW alarm"},
    "CHASSIS_TEMP_HIWAR" : {"severity" : "MAJOR",       "service_affect" : "false", "text" : "CHASSIS TEMPERATURE HIGH warning"},
    "CHASSIS_TEMP_LOWAR" : {"severity" : "MAJOR",       "service_affect" : "false", "text" : "CHASSIS TEMPERATURE LOW warning"},
    "MEM_USAGE_HIGH"     : {"severity" : "CRITICAL",    "service_affect" : "false", "text" : "MEMORY USAGE ALARM"},
    "CPU_USAGE_HIGH"     : {"severity" : "MAJOR",       "service_affect" : "false", "text" : "CPU USAGE ALARM"},
    "CRD_BOOT_FAIL"      : {"severity" : "CRITICAL",    "service_affect" : "true",  "text" : "CARD BOOT FAIL"},
    "VOLTAGE_INPUT_HIGH" : {"severity" : "CRITICAL",    "service_affect" : "false", "text" : "VOLTAGE INPUT HIGH"},
    "VOLTAGE_INPUT_LOW"  : {"severity" : "CRITICAL",    "service_affect" : "false", "text" : "VOLTAGE INPUT LOW"},
}

def alarm_exist_by_type(type) :
    from otn_pmon.public import get_first_slot_id, get_last_slot_id

    # check host db
    dbc = db.Client(db.HOST_DB, db.STATE_DB).db
    if len(dbc.keys(f"{db.Table.CURRENT_ALARM}*{type}*")) != 0 :
        return True

    # check asic dbs
    start = get_first_slot_id(periph_type.LINECARD)
    end = get_last_slot_id(periph_type.LINECARD)
    for i in range (start, end + 1) :
        dbc = db.Client(i, db.STATE_DB, True).db
        if len(dbc.keys(f"{db.Table.CURRENT_ALARM}*{type}*")) != 0 :
            return True

    return False

def alarm_exist_by_severity(severity) :
    from otn_pmon.public import get_first_slot_id, get_last_slot_id

    def exist_in(db_type, multi_db = False) :
        dbc = db.Client(db_type, db.STATE_DB, multi_db)
        keys = dbc.get_keys(db.Table.CURRENT_ALARM)
        for k in keys :
            ok, val = dbc.get_field(db.Table.CURRENT_ALARM, k, "severity")
            if not ok or not val :
                continue
            if val == severity :
                return True
        return False

    # check host db
    if exist_in(db.HOST_DB) :
        return True

    # check asic dbs
    start = get_first_slot_id(periph_type.LINECARD)
    end = get_last_slot_id(periph_type.LINECARD)
    for i in range (start, end + 1) :
        if exist_in(i, True) :
            return True

    return False

def _moveCurAlarmToHisAlarm(dbs, id) :
    # get current alarm info
    ok, info = dbs[db.STATE_DB].get_entry(db.Table.CURRENT_ALARM, id)
    if not ok or not info :
        #alarm not exist
        return
    # delete current alarm
    dbs[db.STATE_DB].delete_entry(db.Table.CURRENT_ALARM, id)
    info_dict = dict(info)
    time_created = info_dict.get('time-created','NA')
    his_key = id + "_" + f"{time_created}"
    cur_time = int(time.time() * 1000000000)
    time_cleared = (('time-cleared', f"{cur_time}"),)
    his_alm_info = info + time_cleared
    # create histroy alarm
    dbs[db.HISTORY_DB].set(db.Table.HISTORY_ALARM, his_key, his_alm_info)
    dbs[db.HISTORY_DB].expire(db.Table.HISTORY_ALARM, his_key)
    print(f"alarm {id} cleared")

class Alarm(object):
    def __init__(self, resource, type_id, serverity = None, sa = None, text = None) :
        self.dbs = db.get_dbs(resource, [db.STATE_DB, db.HISTORY_DB])
        self.id = f"{resource}"+"#"+f"{type_id}"
        self.resource = resource
        self.type_id = type_id
        self.serverity = serverity
        self.service_affect = sa
        self.text = text
        self.__init_alarm(resource, type_id)

    def __init_alarm(self, resource, type_id) :
        if type_id not in _alarms :
            # print(f"pmom has no alarm {type_id} for {resource}")
            return
        self.serverity = _alarms[type_id]["severity"]
        self.service_affect = _alarms[type_id]["service_affect"]
        self.text = _alarms[type_id]["text"]

    @staticmethod
    def clearBy(resource, pattern = None) :
        dbs = db.get_dbs(resource, [db.STATE_DB, db.HISTORY_DB])
        if not dbs :
            return
        keys = dbs[db.STATE_DB].get_keys(db.Table.CURRENT_ALARM)
        for k in keys :
            if resource not in k :
                continue
            if pattern and pattern not in k :
                continue

            _moveCurAlarmToHisAlarm(dbs, k)

    def create(self):
        # time_created = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        time_created = int(time.time() * 1000000000) # ms
        alarm_data = [
            ("time-created",   f"{time_created}"),
            ("id",             f"{self.id}"),
            ("resource",       f"{self.resource}"),
            ("text",           f"{self.text}"),
            ("type-id",        f"{self.type_id}"),
            ("severity",       f"{self.serverity}"),
            ("service-affect", f"{self.service_affect}"),
        ]

        if not self.dbs[db.STATE_DB].exists(db.Table.CURRENT_ALARM, self.id) :
            self.dbs[db.STATE_DB].set(db.Table.CURRENT_ALARM, self.id, alarm_data)
            LOG.log_warning(f"alarm {self.id} created")

    def createAndClearOthers(self, pattern = None) :
        keys = self.dbs[db.STATE_DB].get_keys(db.Table.CURRENT_ALARM)
        for k in keys :
            # alarm does not belong to the resource
            if self.resource not in k :
                continue
            # the alarm already existed
            if self.id == k :
                continue
            # clear as the k has the pattern
            if pattern and pattern not in k :
                continue

            _moveCurAlarmToHisAlarm(self.dbs, k)

        self.create()

    def clear(self) :
        _moveCurAlarmToHisAlarm(self.dbs, self.id)