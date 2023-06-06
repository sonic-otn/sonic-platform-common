from functools import lru_cache
from swsscommon import swsscommon
import otn_pmon.utils as utils
import otn_pmon.periph as periph
from otn_pmon.base import Alarm
from otn_pmon.device.ttypes import led_color, led_type, periph_type, slot_status
from otn_pmon.thrift_client import thrift_try

@lru_cache()
class Linecard(periph.Periph):
    def __init__(self, id):
        super().__init__(periph_type.LINECARD, id)

    def initialize_state(self):
        Alarm.clearAll(self.name)
        eeprom = self.get_periph_eeprom()
        data = [
            ("part-no", eeprom.pn),
            ("serial-no", eeprom.sn),
            ("mfg-date", eeprom.mfg_date),
            ("hardware-version", eeprom.hw_ver),
            ("parent", "CHASSIS-1"),
            ("empty", "false"),
            ("removable", "true"),
            ("power-admin-state", "POWER_ENABLED"),
            ("mfg-name", "alibaba"),
            ("oper-status", utils.slot_status_to_oper_status(slot_status.INIT)),
            ("slot-status", slot_status._VALUES_TO_NAMES[slot_status.INIT]),
            ("subcomponents", self.__get_subcomponents(eeprom.type)),
        ]

        self.dbs[swsscommon.STATE_DB].set(self.table_name, self.name, data)

    def __get_subcomponents(self, card_type):
        if card_type == "E100C" :
            return f"AMPLIFIER-1-{self.id}-1,AMPLIFIER-1-{self.id}-2,ATTENUATOR-1-{self.id}-1,ATTENUATOR-1-{self.id}-3,OSC-1-{self.id}-1,MUX-1-{self.id}-1,OSC-1-{self.id}-1,PORT-1-{self.id}-L1IN,PORT-1-{self.id}-L1OUT"
        elif card_type == "E110C" :
            return f"AMPLIFIER-1-{self.id}-1,AMPLIFIER-1-{self.id}-2,ATTENUATOR-1-{self.id}-1,ATTENUATOR-1-{self.id}-2,ATTENUATOR-1-{self.id}-3,APS-1-{self.id}-1,OSC-1-{self.id}-1,MUX-1-{self.id}-1,PORT-1-{self.id}-L1IN,PORT-1-{self.id}-L1OUT,PORT-1-{self.id}-L2IN,PORT-1-{self.id}-L2OUT"
        elif card_type == "E120C" :
            return f"ATTENUATOR-1-{self.id}-1,ATTENUATOR-1-{self.id}-2,APS-1-{self.id}-1,PORT-1-{self.id}-C1IN,PORT-1-{self.id}-C1OUT,PORT-1-{self.id}-L1IN,PORT-1-{self.id}-L1OUT,PORT-1-{self.id}-L2IN,PORT-1-{self.id}-L2OUT"
        elif card_type == "P230C" :
            return f"PORT-1-{self.id}-C1,PORT-1-{self.id}-C2,PORT-1-{self.id}-C3,PORT-1-{self.id}-C4,PORT-1-{self.id}-L1,PORT-1-{self.id}-L2"
        else :
            return ""

    def __type_mismatch(self) :
        config_db = self.dbs[swsscommon.CONFIG_DB]
        _, type_c = config_db.get_field(self.table_name, self.name, "linecard-type")
        if type_c == "NONE" :
            return False

        eeprom = self.get_periph_eeprom()
        type_r = eeprom.type
        if type_c != type_r :
            return True
 
        return False

    def __type_unknown(self) :
        eeprom = self.get_periph_eeprom()
        type_r = eeprom.type
        if type_r not in ["P230C", "E100C", "E110C", "E120C"] :
            return True
 
        return False

    def update_pm(self) :
        temp = self.get_temperature()
        super().update_pm("Temperature", temp)

    def update_alarm(self) :
        s_rel_status = None
        state_db = self.dbs[swsscommon.STATE_DB]
        if self.__type_unknown() :
            alarm = Alarm(self.name, "CRD_UNKNOWN")
            alarm.createAndClear("CRD")
            s_rel_status = slot_status.UNKNOWN
        elif self.__type_mismatch() :
            alarm = Alarm(self.name, "CRD_MISMATCH")
            alarm.createAndClear("CRD")
            s_rel_status = slot_status.MISMATCH

        if s_rel_status :
            s_db_status = slot_status._VALUES_TO_NAMES[s_rel_status]
            state_db.set_field(self.table_name, self.name, "oper-status", utils.slot_status_to_oper_status(s_rel_status))
            state_db.set_field(self.table_name, self.name, "slot-status", s_db_status)