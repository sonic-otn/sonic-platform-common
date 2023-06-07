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

from swsscommon import swsscommon

EXPIRE_7_DAYS = 7 * 24 * 60 * 60 #unit s
EXPIRE_1_DAYS = 1 * 24 * 60 * 60 #unit s
HOST_DB = 0
CONFIG_DB   = swsscommon.CONFIG_DB
STATE_DB    = swsscommon.STATE_DB
COUNTERS_DB = swsscommon.COUNTERS_DB
HISTORY_DB  = swsscommon.HISTORY_DB

def get_dbs(periph_name, db_types) :
    if not isinstance(db_types, list) or len(db_types) == 0 :
        return None
    slot_id = HOST_DB
    multi_db = False
    elmts = periph_name.split("-")
    if len(elmts) > 2 and int(elmts[2]) <= 4 :
        slot_id = int(elmts[2])
        multi_db = True
    dbs = {}
    for t in db_types :
        dbs[t] = Client(slot_id, t, multi_db)
    return dbs

class Table() :
    CHASSIS = "CHASSIS"
    FAN = "FAN"
    LINECARD = "LINECARD"
    PSU = "PSU"
    CU = "CU"
    CURRENT_ALARM = "CURALARM"
    HISTORY_ALARM = "HISALARM"

class Client():
    def __init__(self, slot_id, db_index, multi_db = False) :
        if multi_db == True :
            redis_sock = f"/var/run/redis{slot_id-1}/redis.sock"
        else:
            redis_sock = f"/var/run/redis/redis.sock"
        self.db = swsscommon.DBConnector(db_index, redis_sock, 0)

    def exists(self, tname, kname) :
        t = swsscommon.Table(self.db, tname)
        if not t :
            return False
        ok, _ = t.get(kname)
        return ok

    def get_entry(self, tname, kname) :
        t = swsscommon.Table(self.db, tname)
        if not t :
            return
        return t.get(kname)

    def get_keys(self, tname) :
        t = swsscommon.Table(self.db, tname)
        if not t :
            print(f"{tname} is not exist")
            return
        return t.getKeys()

    def get_field(self, tname, kname, fname) :
        t = swsscommon.Table(self.db, tname)
        if not t :
            return
        return t.hget(kname, fname)

    def set(self, tname, kname, data) :
        t = swsscommon.Table(self.db, tname)
        if not t :
            return
        return t.set(kname, swsscommon.FieldValuePairs(data))

    def set_field(self, tname, kname, fname, fval) :
        data = [(fname, fval)]
        t = swsscommon.Table(self.db, tname)
        if not t :
            return
        return t.set(kname, swsscommon.FieldValuePairs(data))
    
    def expire(self, tname, kname, seconds = EXPIRE_7_DAYS) :
        t = swsscommon.Table(self.db, tname)
        if not t :
            return
        return t.expire(kname, seconds)

    def delete_entry(self, tname, kname) :
        t = swsscommon.Table(self.db, tname)
        if not t :
            return
        return t.delete(kname)

    def pub_sub(self) :
        pubsub = swsscommon.PubSub(self.db)
        if not pubsub :
            return
        return pubsub
