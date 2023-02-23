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

from otn_pmon.device.ttypes import power_ctl_type, periph_type
from otn_pmon.thrift_client import thrift_try

def get_system_version():
    def inner(client):
        return client.get_system_version()
    return thrift_try(inner)

def get_product_name() :
    name = ""
    def inner(client):
        return client.get_periph_eeprom(periph_type.CHASSIS, 1)
    chassis_eeprom = thrift_try(inner)
    if chassis_eeprom :
        name = chassis_eeprom.model_name
    return name

def set_power_control(slot_id, type) :
    pass

def get_inlet_temp() :
    pass

def get_outlet_temp() :
    pass

def get_reboot_type() :
    pass

def switch_slot_uart(slot_id) :
    def inner(client):
        return client.switch_slot_uart(slot_id)
    return thrift_try(inner)