/**
 * Copyright (c) 2021 Alibaba Group.
 *
 *    Licensed under the Apache License, Version 2.0 (the "License"); you may
 *    not use this file except in compliance with the License. You may obtain
 *    a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
 *
 *    THIS CODE IS PROVIDED ON AN *AS IS* BASIS, WITHOUT WARRANTIES OR
 *    CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
 *    LIMITATION ANY IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS
 *    FOR A PARTICULAR PURPOSE, MERCHANTABILITY OR NON-INFRINGEMENT.
 *
 *    See the Apache Version 2.0 License for specific language governing
 *    permissions and limitations under the License.
 *
 * @file    device.thrift
 *
 * @brief   This file defines PMON thrift interfaces
 */

// OK:0, ERROR:1~
typedef i8 ret_code

enum periph_type {
    CHASSIS,
    LINECARD,
    CU,
    FAN,
    PSU,
    NONE
}

enum slot_status {
    EMPTY,
    INIT,
    READY,
    MISMATCH,
    COMFAIL,
    UNKNOWN
}

enum led_type {
    CU,
    FAN,
    PSU,
    UNKNOWN
}

enum fpga_type {
    UP,
    DOWN
}

enum led_color {
    RED,
    GREEN,
    YELLOW,
    ORANGE,
    OFF,
    UNKNOWN
}

enum led_flash_type {
    RED_YELLOW_GREEN,
    NONE
}

enum linecard_type {
    P230C,
    E100C,
    E110C,
    E120C
}

enum reboot_type {
    POWER,
    COLD,
    SOFT,
    ABNORMAL,
    DOG,
    BUTTON,
}

enum power_ctl_type {
    OFF,
    ON
}

struct system_version {
1:  string fpgaup
2:  string fpgadown
3:  string pcb;
4:  string bom;
5:  string devmgr;
6:  string ucd90120;
}

struct psu_info {
1:  i32 abs;
2:  i32 ambient_temp;
3:  i32 primary_temp;
4:  i32 secondary_temp;
5:  i32 vout;
6:  i32 vin;
7:  i32 iout;
8:  i32 iin;
9:  i32 pout;
10: i32 pin;
11: i32 fan;
12: i32 capacity;
}

struct periph_eeprom {
1: string type;
2: string model_name;
3: string pn;
4: string sn;
5: string label;
6: string hw_ver;
7: string sw_ver;
8: string mfg_date;
9: string mac_addr;
}

struct fan_speed {
1: i32 front;
2: i32 behind;
}

struct power_monitor {
1:  i32 vol1;
2:  i32 vol2;
3:  i32 vol3;
4:  i32 vol4;
5:  i32 vol5;
6:  i32 vol6;
7:  i32 vol7;
8:  i32 vol8;
9:  i32 vol9;
10: i32 vol10;
11: i32 vol11;
12: i32 vol12
}

service periph_rpc {
    bool periph_presence(1: periph_type type, 2: i8 id);

    system_version get_system_version();

    string get_periph_version(1: periph_type type, 2: i8 id);

    i32 get_periph_temperature(1: periph_type type, 2: i8 id);

    slot_status get_periph_slot_status(1: periph_type type, 2: i8 id);

    periph_eeprom get_periph_eeprom(1: periph_type type, 2: i8 id);

    ret_code initialize(1: periph_type type, 2: i8 id);

    psu_info get_psu_info(1: i8 id);

    ret_code set_led_flash(1: led_type type, 2: i8 id, 4: led_flash_type flash_type);

    ret_code set_led_color(1: led_type type, 2: i8 id, 3: led_color color);

    reboot_type get_reboot_type();

    ret_code periph_reboot(1: periph_type type, 2: i8 id, 3: reboot_type reboot_type);

    string get_power_control_version(1: i8 slot_id);

    ret_code set_power_control(1: i8 slot_id, 2: power_ctl_type type);

    ret_code recover_linecard_default_config(1: i8 id, 2: linecard_type type);

    ret_code switch_slot_uart(1: i8 id);

    fan_speed get_fan_speed(1: i8 id);

    ret_code set_fan_speed(1: i8 id, 2: i32 speed);

    ret_code sync_time_to_power_control();

    string get_fpga_version(1: fpga_type ftype)

    i32 get_slot_power_monitor_points_number(1: i8 id);

    i32 get_slot_power_monitor_point_log(1: i8 id, 2: i32 total, 3: i32 index);

    power_monitor get_fpga_up_power_monitor();

    power_monitor get_slot_power_monitor(1: i8 id);
}