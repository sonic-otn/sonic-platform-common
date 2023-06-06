import time
from functools import lru_cache
from swsscommon import swsscommon
import otn_pmon.db as db

@lru_cache()
class Pm :
    """PM class"""
    PM_TYPE_15 = "15"
    PM_TYPE_24 = "24"
    def __init__(self, table, base_key, name, type) : 
        self.table = table
        self.base_key = base_key
        self.name = name # PM name
        self.type = type # PM type 15|24
        self.dbs = db.get_dbs(base_key, [swsscommon.COUNTERS_DB, swsscommon.HISTORY_DB])

        self.starttime = 0 
        self.interval = self.__get_interval()
        self.instant = 0 # current value
        self.avg = 0
        self.min = 0
        self.max = 0
        self.min_time = 0
        self.max_time = 0
        self.sum = 0    # sampling sum
        self.count = 0  # sampling total count

    def __get_interval(self) :
        ns_unit = 1000000000
        interval = 0
        if self.type == Pm.PM_TYPE_15 :
            interval = 15 * 60 * ns_unit
        else :
            interval = 24 * 60 * 60 * ns_unit
        return interval

    def __get_latest_sampling_timestamp(self, time) :
        delta = self.__get_interval()
        # pmon中不需要考虑时区么？
        return int(time / delta) * delta

    def __need_reset(self, time) :
        new_timestamp = self.__get_latest_sampling_timestamp(time)
        if self.starttime != 0 and self.starttime != new_timestamp :
            return True
        return False

    def __reset(self) :
        # generate history pm then do reset
        self.__save(swsscommon.HISTORY_DB)
 
        self.starttime = 0
        self.instant = 0 # current value
        self.avg = 0.0
        self.min = 0.0
        self.max = 0.0
        self.min_time = 0
        self.max_time = 0
        self.sum = 0
        self.count = 0 # accumulate times

    def __get_key(self, type = swsscommon.COUNTERS_DB) :
        if type == swsscommon.HISTORY_DB :
            suffix = "15_pm_history"
            if self.type != Pm.PM_TYPE_15 :
                suffix = "24_pm_history"

            return  f"{self.base_key}_{self.name}:{suffix}_{self.starttime}"

        suffix = "15_pm_current"
        if self.type != Pm.PM_TYPE_15 :
            suffix = "24_pm_current"
        return  f"{self.base_key}_{self.name}:{suffix}"

    def __save(self, type = swsscommon.COUNTERS_DB) :
        if self.starttime == 0 :
            return

        validity = "incomplete"
        if type == swsscommon.HISTORY_DB :
            validity = "complete"

        data = [
            ("starttime", f"{self.starttime}"),
            ("instant", f"{self.instant}"),
            ("avg", f"{self.avg}"),
            ("min", f"{self.min}"),
            ("max", f"{self.max}"),
            ("interval", f"{self.interval}"),
            ("min-time", f"{self.min_time}"),
            ("max-time", f"{self.max_time}"),
            ("validity", validity),
        ]

        key = self.__get_key(type)
        if type not in self.dbs :
            print(f"save pm {key} to db failed as the type {type} is invalid")
            return
        # print(f"set {self.table} {key}")
        self.dbs[type].set(self.table, key, data)

    def update(self, value) :
        cur_time = int(time.time() * 1000000000) # ns

        if self.__need_reset(cur_time) :
            print(f"{self.name} {self.type} PM reset")
            self.__reset()

        self.starttime = self.__get_latest_sampling_timestamp(cur_time)
        self.instant = value
        if value < self.min or self.min_time == 0 :
            self.min = value
            self.min_time = cur_time
        if value > self.max or self.max_time == 0 :
            self.max = value
            self.max_time = cur_time

        self.sum += value
        self.count += 1
        self.avg = round(self.sum / self.count, 1)
        
        # save current pm to counters db
        self.__save()

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
}

def _moveCurAlarmToHisAlarm(dbs, id) :
    # get current alarm info
    ok, info = dbs[swsscommon.STATE_DB].get_entry(db.Table.CURRENT_ALARM, id)
    if not ok or not info :
        #alarm not exist
        return
    # delete current alarm
    dbs[swsscommon.STATE_DB].delete_entry(db.Table.CURRENT_ALARM, id)
    info_dict = dict(info)
    time_created = info_dict.get('time-created','NA')
    his_key = id + "_" + f"{time_created}"
    cur_time = int(time.time() * 1000000000)
    time_cleared = (('time-cleared', f"{cur_time}"),)
    his_alm_info = info + time_cleared
    # create histroy alarm
    dbs[swsscommon.HISTORY_DB].set(db.Table.HISTORY_ALARM, his_key, his_alm_info)
    dbs[swsscommon.HISTORY_DB].expire(db.Table.HISTORY_ALARM, his_key)
    # print(f"alarm {id} is moved to history db")

class Alarm(object):
    def __init__(self, resource, type_id) :
        self.dbs = db.get_dbs(resource, [swsscommon.STATE_DB, swsscommon.HISTORY_DB])
        self.__init_alarm(resource, type_id)

    def __init_alarm(self, resource, type_id) :
        if not _alarms[type_id] :
            print(f"pmom has no alarm {type_id} for {resource}")
            return
        self.id = f"{resource}"+"#"+f"{type_id}"
        self.resource = resource
        self.type_id = type_id
        self.serverity = _alarms[type_id]["severity"]
        self.service_affect = _alarms[type_id]["service_affect"]
        self.text = _alarms[type_id]["text"]

    @staticmethod
    def clearAll(resource) :
        dbs = db.get_dbs(resource, [swsscommon.STATE_DB, swsscommon.HISTORY_DB])
        if not dbs :
            return
        keys = dbs[swsscommon.STATE_DB].get_keys(db.Table.CURRENT_ALARM)
        for k in keys :
            if resource not in k :
                continue
            _moveCurAlarmToHisAlarm(dbs, k)

    def create(self):
        #time_created = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        time_created = int(time.time() * 1000000000)#ms
        alarm_data = [
            ("time-created",   f"{time_created}"),
            ("id",             f"{self.id}"),
            ("resource",       f"{self.resource}"),
            ("text",           f"{self.text}"),
            ("type-id",        f"{self.type_id}"),
            ("severity",       f"{self.serverity}"),
            ("service-affect", f"{self.service_affect}"),
        ]

        if not self.dbs[swsscommon.STATE_DB].exists(db.Table.CURRENT_ALARM, self.id) :
            self.dbs[swsscommon.STATE_DB].set(db.Table.CURRENT_ALARM, self.id, alarm_data)
    
    def createAndClear(self, pattern = None) :
        if pattern :
            self.clearByPattern(pattern)
        self.create()

    def clearByPattern(self, pattern) :
        keys = self.dbs[swsscommon.STATE_DB].get_keys(db.Table.CURRENT_ALARM)
        for k in keys :
            if self.resource not in k :
                # alarms do not belong to the resource
                continue
            if self.id == k :
                # the alarm itself already exists
                continue
            type_id = k.split("#")[1]
            if pattern in type_id :
                _moveCurAlarmToHisAlarm(self.dbs, k)

    def clear(self) :
        _moveCurAlarmToHisAlarm(self.dbs, self.id)