/**
 * Copyright (c) 2021 Alibaba Group and Accelink Technologies
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
 **/


typedef i8 ret_code  // OK:0, ERROR:1~
enum error_code {
    OK,
    ERROR
}

enum periph_type {
    CHASSIS,
    LINECARD,
    CU,
    FAN,
    PSU,
    UNKNOWN
}

enum led_type {
    CU,
    FAN,
    PSU,
    UNKNOWN
}

enum led_state {
    OFF,
    ON
}

enum led_color {
    RED,
    GREEN,
    YELLOW,
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
1:  string fpga;            # eg: "1:v1.0;2:v1.1;3:v1.3"
2:  string pcb;
3:  string bom;
4:  string devmgr;
5:  string ucd90120;
6: optional string reserve 
}

struct ret_temp {
1:  ret_code ret;
2:  i32 temperature;
}

struct psu_info {
1:  i32 abs;                         # absorbed power
2:  i32 ambient_temp;                # ambient temperature sensors
3:  i32 primary_temp;                # primary temperature sensors
4:  i32 secondary_temp;              # secondary temperature sensors
5:  i32 vout;                        # voltage output
6:  i32 vin;                         # voltage input
7:  i32 iout;                        # current output
8:  i32 iin;                         # current input
9:  i32 pout;                        # power output
10: i32 pin;                         # power input
11: i32 fan;                         # fan speed
12: i32 capacity;                    # power capacity
13: optional string reserve          # reserve field
}

struct ret_psu_info {
1:  ret_code ret;
2:  psu_info info;
}

struct inventory {
1: optional string type;
2: string model_name;
3: string pn;
4: string sn;
5: string label;
6: string hw_ver;
7: string sw_ver;
8: string mfg_date;
9: string mac_addr;
10: optional string reserve 
}

struct ret_inventory {
1:  ret_code ret;
2:  inventory inv;
}

struct fan_speed {
1: i32 front;
2: i32 behind;
}

struct ret_fan_speed {
1:  ret_code ret;
2:  fan_speed speed;
}

struct fan_speed_spec {
1: i32 max;
2: i32 min;
}

service periph_rpc {
    // common APIs
    system_version get_system_version();

    bool periph_presence(1: periph_type type, 2: i8 id);

    string get_periph_version(1: periph_type type, 2: i8 id);

    ret_temp get_periph_temperature(1: periph_type type, 2: i8 id);

    ret_inventory get_inventory(1: periph_type type, 2: i8 id);

    ret_psu_info get_psu_info(1: i8 id);

    bool psu_vin_high(1: i8 id);

    bool psu_vin_low(1: i8 id);

    ret_code set_led_state(1: led_type type, 2: i8 id, 3: led_state state);

    ret_code set_led_color(1: led_type type, 2: i8 id, 3: led_color color);

    reboot_type get_reboot_type();

    ret_code periph_reboot(1: periph_type ptype, 2: i8 id, 3: reboot_type rtype);

    string get_power_control_version(1: i8 slot_id);

    ret_code set_power_control(1: i8 slot_id, 2: power_ctl_type type);

    ret_code recover_linecard_default_config(1: i8 id, 2: linecard_type type);

    ret_code switch_slot_uart(1: i8 id);

    ret_fan_speed get_fan_speed(1: i8 id);

    fan_speed_spec get_fan_speed_spec(1: i8 id);

    ret_code set_fan_speed_rate(1: i8 id, 2: i32 speed_rate);

    string get_fpga_version(1: i8 id);
}


