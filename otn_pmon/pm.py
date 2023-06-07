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
from functools import lru_cache
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
        self.dbs = db.get_dbs(base_key, [db.COUNTERS_DB, db.HISTORY_DB])

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
        # timezone ???
        return int(time / delta) * delta

    def __need_reset(self, time) :
        new_timestamp = self.__get_latest_sampling_timestamp(time)
        if self.starttime != 0 and self.starttime != new_timestamp :
            return True
        return False

    def __reset(self) :
        # generate history pm then do reset
        self.__save(db.HISTORY_DB)
 
        self.starttime = 0
        self.instant = 0 # current value
        self.avg = 0.0
        self.min = 0.0
        self.max = 0.0
        self.min_time = 0
        self.max_time = 0
        self.sum = 0
        self.count = 0 # accumulate times

    def __get_key(self, type = db.COUNTERS_DB) :
        if type == db.HISTORY_DB :
            suffix = "15_pm_history"
            if self.type != Pm.PM_TYPE_15 :
                suffix = "24_pm_history"

            return  f"{self.base_key}_{self.name}:{suffix}_{self.starttime}"

        suffix = "15_pm_current"
        if self.type != Pm.PM_TYPE_15 :
            suffix = "24_pm_current"
        return  f"{self.base_key}_{self.name}:{suffix}"

    def __save(self, type = db.COUNTERS_DB) :
        if self.starttime == 0 :
            return

        validity = "incomplete"
        if type == db.HISTORY_DB :
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
            # print(f"{self.name} {self.type} PM reset")
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