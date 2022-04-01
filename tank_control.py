#https://python-evdev.readthedocs.io/en/latest/usage.html
#https://raspberry-valley.azurewebsites.net/Map-Bluetooth-Controller-using-Python/

import os
import sys
import time
from multiprocessing import Process
import threading
from evdev import InputDevice, categorize, ecodes, list_devices,util
import json
import traceback
import RPi.GPIO as GPIO
import numpy as np

class tank_controller:
    PIN_LEFT_MOTOR_PWM = 33
    PIN_RIGHT_MOTOR_PWM = 31

    PIN_LEFT_MOTOR_A = 37
    PIN_LEFT_MOTOR_B = 35
    PIN_RIGHT_MOTOR_A = 38
    PIN_RIGHT_MOTOR_B = 36

    PWM_CHANNEL_MOTOR_LEFT = 0 
    PWM_CHANNEL_MOTOR_RIGHT = 1 

    PWM_FREQUENCY = 5000 
    PWM_RESOLUTION = 8

    MIN_GAS=5e-2

    BTN_GAS = 9
    BTN_BRAKE = 10

    DELAY_RESTART_CONTROL_LOOP=3
    DELAY_RESTART_EVENT_LOOP=3
    DELAY_CONTROL_LOOP=0.05

    control_loop_alive=True
    event_loop_alive=True

    control_loop_alive_lock = threading.Lock()
    event_loop_alive_lock = threading.Lock()
    motion_state_lock = threading.Lock()

    motion_state = {
        "left":0,
        "right":0
    }

    def __init__(self,xbox_name):
        self.xbox_name=xbox_name

    def start(self):
        errcode=0

        try:
            GPIO.setmode(GPIO.BOARD)
        
            GPIO.setup(self.PIN_LEFT_MOTOR_A, GPIO.OUT)
            GPIO.setup(self.PIN_LEFT_MOTOR_B, GPIO.OUT)
            GPIO.setup(self.PIN_RIGHT_MOTOR_A, GPIO.OUT)
            GPIO.setup(self.PIN_RIGHT_MOTOR_B, GPIO.OUT)
            GPIO.setup(self.PIN_LEFT_MOTOR_PWM, GPIO.OUT)
            GPIO.setup(self.PIN_RIGHT_MOTOR_PWM, GPIO.OUT)

            self.set_left_motor_stationary()
            self.set_right_motor_stationary()

            self.pwm_left=GPIO.PWM(self.PIN_LEFT_MOTOR_PWM, self.PWM_FREQUENCY)
            self.pwm_left.start(0)
            self.pwm_right=GPIO.PWM(self.PIN_RIGHT_MOTOR_PWM, self.PWM_FREQUENCY)
            self.pwm_right.start(0)

            self.process_event_loop = threading.Thread(target=self.event_loop)
            self.process_event_loop.start()
            self.process_control_loop = threading.Thread(target=self.control_loop)
            self.process_control_loop.start()
            self.process_control_loop.join()
            self.process_event_loop.join()
        except KeyboardInterrupt as ex:
            errcode=1
        except Exception as ex:
            print_ex(ex)
            errcode=1
        finally:
            with self.control_loop_alive_lock:
                self.control_loop_alive=False

            with self.event_loop_alive_lock:            
                self.event_loop_alive=False
            
            GPIO.cleanup()
            sys.exit(errcode)

    def control_loop(self):
        def control_loop_alive():
            with self.control_loop_alive_lock:
                return self.control_loop_alive

        while control_loop_alive():
            try:
                left=0
                right=0

                with self.motion_state_lock:
                    print(self.motion_state)
                    left=self.motion_state["left"]
                    right=self.motion_state["right"]
                
                abs_left=abs(left)
                abs_right=abs(right)

                self.set_left_motor_stationary()
                self.set_right_motor_stationary()

                if abs_left<self.MIN_GAS and abs_right<self.MIN_GAS: 
                    self.set_left_motor_stationary()
                    self.set_right_motor_stationary()
                elif abs_left<self.MIN_GAS or abs_right<self.MIN_GAS: 
                    max_gas=max(abs_left,abs_right)

                    if max_gas==abs_left:
                        direction=np.sign(left)
                        abs_right=abs_left

                        if direction>0: 
                            self.set_left_motor_clockwise()
                            self.set_right_motor_counter_clockwise()
                        else:
                            self.set_left_motor_counter_clockwise()
                            self.set_right_motor_clockwise()
                    else:
                        direction=np.sign(right)
                        abs_left=abs_right

                        if direction>0:
                            self.set_left_motor_counter_clockwise()
                            self.set_right_motor_clockwise()
                        
                        else: 
                            self.set_left_motor_clockwise()
                            self.set_right_motor_counter_clockwise()
                else:
                    if(left>0):
                        self.set_left_motor_counter_clockwise()
                    else:
                        self.set_left_motor_clockwise()
                    
                    if(right>0):
                        self.set_right_motor_counter_clockwise()                      
                    else:
                        self.set_right_motor_clockwise()
          
                self.pwm_left.ChangeDutyCycle(abs_left)
                self.pwm_right.ChangeDutyCycle(abs_right)
                # print("abs_right "+str(abs_right))
                # print("abs_left "+str(abs_left))
                time.sleep(self.DELAY_CONTROL_LOOP)
            except Exception as ex:
                print_ex(ex)
                time.sleep(self.DELAY_RESTART_CONTROL_LOOP)

    def event_loop(self):
        def event_loop_alive():
            with self.event_loop_alive_lock:
                return self.event_loop_alive

        while event_loop_alive():
            gamepad=None

            try:
                devices = [InputDevice(path) for path in list_devices()]
                device = next((x for x in devices if x.name==self.xbox_name), None)

                if device is None:
                    time.sleep(self.DELAY_RESTART_EVENT_LOOP)
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

                    while event_loop_alive():
                        event = gamepad.read_one()

                        if event is not None and event.type == ecodes.EV_ABS:
                            if event.code == self.BTN_GAS:
                                normalized_gas=event.value/abs_gas_max
                                
                                with self.motion_state_lock:
                                    self.motion_state["right"]=normalized_gas
                            elif event.code == self.BTN_BRAKE:
                                normalized_brake=event.value/abs_brake_max
                                
                                with self.motion_state_lock:
                                    self.motion_state["left"]=normalized_brake
            except Exception as ex:
                print_ex(ex)
            finally:
                if gamepad is not None:
                    gamepad.close()

                if event_loop_alive():
                    time.sleep(self.DELAY_RESTART_EVENT_LOOP)

    def set_left_motor_stationary(self):
        GPIO.output(self.PIN_LEFT_MOTOR_A, GPIO.LOW)
        GPIO.output(self.PIN_LEFT_MOTOR_B, GPIO.LOW)

    def set_left_motor_clockwise(self): 
        GPIO.output(self.PIN_LEFT_MOTOR_A, GPIO.LOW)
        GPIO.output(self.PIN_LEFT_MOTOR_B, GPIO.HIGH)

    def set_left_motor_counter_clockwise(self): 
        GPIO.output(self.PIN_LEFT_MOTOR_A, GPIO.HIGH)
        GPIO.output(self.PIN_LEFT_MOTOR_B, GPIO.LOW)

    def set_right_motor_stationary(self): 
        GPIO.output(self.PIN_RIGHT_MOTOR_A, GPIO.LOW)
        GPIO.output(self.PIN_RIGHT_MOTOR_B, GPIO.LOW)

    def set_right_motor_clockwise(self):
        GPIO.output(self.PIN_RIGHT_MOTOR_A, GPIO.LOW)
        GPIO.output(self.PIN_RIGHT_MOTOR_B, GPIO.HIGH)

    def set_right_motor_counter_clockwise(self):
        GPIO.output(self.PIN_RIGHT_MOTOR_A, GPIO.HIGH)
        GPIO.output(self.PIN_RIGHT_MOTOR_B, GPIO.LOW)


def print_ex(ex):
    print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))

def display_usage():
    print("\nUsage: "+os.path.basename(__file__)+" [XBOX Name]\n")

if __name__ == "__main__":
    argc=len(sys.argv)

    if argc < 2: 
        display_usage()
        sys.exit(1)

    controller_name=sys.argv[1]
    print(controller_name)
    controller=tank_controller(controller_name)
    controller.start()