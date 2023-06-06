import json
from platform import platform
from otn_pmon.device.ttypes import periph_type, slot_status
from sonic_py_common.device_info import get_path_to_platform_dir

def get_periph_spec() :
    platform_path = get_path_to_platform_dir()
    spec_path = f"{platform_path}/dev_spec.json"
    with open(spec_path, 'r', encoding='utf8') as fp:
        return json.load(fp) 

def get_periph_number(type) :
    spec = get_periph_spec()
    type_name = periph_type._VALUES_TO_NAMES[type]
    if type_name :
        return spec["number"][type_name]
    return 0

def get_expected_pn(type) :
    spec = get_periph_spec()
    type_name = periph_type._VALUES_TO_NAMES[type]
    if type_name :
        return spec["expected-pn"][type_name]
    return None

def get_first_slot_id(type) :
    linecard_num = get_periph_number(periph_type.LINECARD)
    psu_num = get_periph_number(periph_type.PSU)
    if type == periph_type.LINECARD or type == periph_type.CU or type == periph_type.CHASSIS :
        return 1
    elif type == periph_type.PSU :
        # the fan is behind the linecard
        return 1 + linecard_num
    elif type == periph_type.FAN :
        # the fan is behind the psu
        return 1 + linecard_num + psu_num
    else :
        return 0

def get_last_slot_id(type) :
    start = get_first_slot_id(type)
    if start == 0 :
        return 0
    
    number = get_periph_number(type)
    return start + number - 1

def get_chassis_power_capacity() :
    pc = 0
    chassis_pn = get_expected_pn(periph_type.CHASSIS)
    if chassis_pn and len(chassis_pn) >= 4 :
        power_type = chassis_pn[3]
        if power_type == "0" :
            pc = 550
        elif power_type == "1" :
            pc = 800
        elif power_type == "2" :
            pc = 1300
    return pc

def slot_status_to_oper_status(status) :
    oper_status = None
    if status == slot_status.READY :
        oper_status = "ACTIVE"
    elif status == slot_status.INIT or status == slot_status.COMFAIL :
        oper_status = "INACTIVE"
    elif status == slot_status.UNKNOWN or status == slot_status.MISMATCH :
        oper_status = "DISABLED"
    
    return oper_status
    



        
