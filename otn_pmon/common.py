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