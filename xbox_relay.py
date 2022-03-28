#https://python-evdev.readthedocs.io/en/latest/usage.html
#https://raspberry-valley.azurewebsites.net/Map-Bluetooth-Controller-using-Python/

import os
import sys
import time
from multiprocessing import Process
import atexit
import threading
from evdev import InputDevice, categorize, ecodes, list_devices,util
import json
import serial
import serial.tools.list_ports
import traceback

class xbox_relay:
    BTN_GAS = 9
    BTN_BRAKE = 10
    DELAY_RESTART_NOTIFY=3
    DELAY_RESTART_COLLECT=3
    TIMEOUT_KILL=5
    SERIAL_TIMEOUT=5

    motion_state_lock = threading.Lock()

    motion_state = {
        "motion_state" : {
            "l":0,
            "r":0
        }
    }

    def __init__(self,xbox_name,microcontroller_baud_rate):
        self.xbox_name=xbox_name
        self.microcontroller_baud_rate=microcontroller_baud_rate
        self.serial_port = serial.Serial()
        self.serial_port.baudrate = microcontroller_baud_rate
        self.serial_port.timeout = self.SERIAL_TIMEOUT
        self.serial_port.write_timeout = self.SERIAL_TIMEOUT

    def start(self):
        errcode=0

        try:
            self.process_notify = Process(target=self.notify, name="xbox_relay_notify")
            self.process_notify.start()
            self.process_collect = Process(target=self.collect_events, name="xbox_relay_collect")
            self.process_collect.start()
            self.process_notify.join()
            self.process_collect.join()
        except KeyboardInterrupt as ex:
            errcode=0
        except Exception as ex:
            print_ex(ex)
            errcode=1
        finally:
            self.process_notify.terminate()
            self.process_collect.terminate()
            sys.exit(errcode)

    def notify(self):
        while True:
            serial_error=False

            try:
                if not self.serial_port.is_open:
                    microcontroller_port=self.get_esp32_port()

                    if microcontroller_port is None:
                        time.sleep(self.DELAY_RESTART_NOTIFY)
                        continue

                    self.serial_port.port = microcontroller_port
                    self.serial_port.open()

                if self.serial_port.is_open:
                    self.serial_port.flush()
                    
                    with self.motion_state_lock:
                        motion_state_str=json.dumps(self.motion_state)

                    self.serial_port.write((motion_state_str+"\n").encode())
                    response = json.loads(self.serial_port.readline())
                    print(response)
            except serial.SerialException as ex:
                print_ex(ex)
                serial_error=True
            except Exception as ex:
                print_ex(ex)
                time.sleep(self.DELAY_RESTART_NOTIFY)
            finally:
                if serial_error:
                    self.serial_port.close()
                    time.sleep(self.DELAY_RESTART_NOTIFY)

    def collect_events(self):
        while True:
            try:
                devices = [InputDevice(path) for path in list_devices()]
                device = next((x for x in devices if x.name==self.xbox_name), None)

                if device is None:
                    time.sleep(self.DELAY_RESTART_COLLECT)
                    continue

                capabilities=device.capabilities(verbose=True)
                keys=util.resolve_ecodes_dict(util.find_ecodes_by_regex(r'ABS_(GAS|BRAKE)'))
                list_keys=list(keys)
                key_ev_abs=list_keys[0][0]
                key_abs_gas=next((x for x in list_keys[0][1] if x[0]=="ABS_GAS"), None)
                key_abs_brake=next((x for x in list_keys[0][1] if x[0]=="ABS_BRAKE"), None)
                abs_info_gas=next((x for x in capabilities[key_ev_abs] if x[0]==key_abs_gas), None)
                abs_info_brake=next((x for x in capabilities[key_ev_abs] if x[0]==key_abs_brake), None)
                
                if abs_info_gas is not None and abs_info_brake is not None:
                    gamepad = InputDevice(device.path)
                    abs_gas_max=abs_info_gas[1].max
                    abs_brake_max=abs_info_brake[1].max

                    print("a")
                    for event in gamepad.read_loop():
                        print("b")

                        if event.type == ecodes.EV_ABS:
                            if event.code == self.BTN_GAS:
                                normalized_gas=event.value/abs_gas_max
                                
                                with self.motion_state_lock:
                                    self.motion_state["motion_state"]["r"]=normalized_gas
                            elif event.code == self.BTN_BRAKE:
                                normalized_brake=event.value/abs_brake_max
                                
                                with self.motion_state_lock:
                                    self.motion_state["motion_state"]["l"]=normalized_brake
            except Exception as ex:
                print_ex(ex)
                time.sleep(self.DELAY_RESTART_COLLECT)

    def get_esp32_port(self):
        for port in serial.tools.list_ports.comports():
            try:
                serial_port=serial.Serial(port.device,self.microcontroller_baud_rate)

                if serial_port.is_open:                    
                    input = {
                        "id":""
                    }

                    serial_port.write_timeout=self.SERIAL_TIMEOUT
                    serial_port.write((json.dumps(input)+"\n").encode())
                    serial_port.timeout=self.SERIAL_TIMEOUT
                    response = json.loads(serial_port.readline())

                    if response["id"]=="controller":
                        return port.device

            except Exception as ex:
                print_ex(ex)
            finally:
                if serial_port is not None:
                    serial_port.close()

        return None

def print_ex(ex):
    print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))

def display_usage():
    print("\nUsage: "+os.path.basename(__file__)+" [XBOX Name] [Microcontroller Baud Rate]\n")

if __name__ == "__main__":
    argc=len(sys.argv)

    if argc < 2: 
        display_usage()
        sys.exit(1)

    xbox_name=sys.argv[1]
    microcontroller_baud_rate=sys.argv[2]
    relay=xbox_relay(xbox_name,microcontroller_baud_rate)
    relay.start()