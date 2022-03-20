//https://techtutorialsx.com/2021/01/04/esp32-soft-ap-and-station-modes/

#include "ArduinoJson.h"

const int PIN_LEFT_MOTOR_PWM = 25;
const int PIN_RIGHT_MOTOR_PWM = 26;

const int PIN_LEFT_MOTOR_A = 14;
const int PIN_LEFT_MOTOR_B = 12;
const int PIN_RIGHT_MOTOR_A = 33;
const int PIN_RIGHT_MOTOR_B = 32;

const int PWM_CHANNEL_MOTOR_LEFT = 0; 
const int PWM_CHANNEL_MOTOR_RIGHT = 1; 

const int PWM_FREQUENCY = 5000; 
const int PWM_RESOLUTION = 8;

const double MIN_GAS=1e-2;

unsigned long SERIAL_TIMEOUT=500;

void set_left_motor_stationary() {
    digitalWrite(PIN_LEFT_MOTOR_A, 0);
    digitalWrite(PIN_LEFT_MOTOR_B, 0);
}

void set_left_motor_clockwise() {
    digitalWrite(PIN_LEFT_MOTOR_A, 0);
    digitalWrite(PIN_LEFT_MOTOR_B, 1);
}

void set_left_motor_counter_clockwise() {
    digitalWrite(PIN_LEFT_MOTOR_A, 1);
    digitalWrite(PIN_LEFT_MOTOR_B, 0);
}

void set_right_motor_stationary() {
    digitalWrite(PIN_RIGHT_MOTOR_A, 0);
    digitalWrite(PIN_RIGHT_MOTOR_B, 0);
}

void set_right_motor_clockwise() {
    digitalWrite(PIN_RIGHT_MOTOR_A, 0);
    digitalWrite(PIN_RIGHT_MOTOR_B, 1);
}

void set_right_motor_counter_clockwise() {
    digitalWrite(PIN_RIGHT_MOTOR_A, 1);
    digitalWrite(PIN_RIGHT_MOTOR_B, 0);
}

int get_sign_dbl(double x) {
  if (x > 0) 
    return 1;
  if (x < 0) 
    return -1;
  
  return 0;  
}
 
void setup() {
  Serial.begin(9600);
  Serial.setTimeout(SERIAL_TIMEOUT);

  pinMode(PIN_LEFT_MOTOR_A, OUTPUT);
  pinMode(PIN_LEFT_MOTOR_B, OUTPUT);
  pinMode(PIN_RIGHT_MOTOR_A, OUTPUT);
  pinMode(PIN_RIGHT_MOTOR_B, OUTPUT);

  set_left_motor_stationary();
  set_right_motor_stationary();

  ledcSetup(PWM_CHANNEL_MOTOR_LEFT, PWM_FREQUENCY, PWM_RESOLUTION);  
  ledcSetup(PWM_CHANNEL_MOTOR_RIGHT, PWM_FREQUENCY, PWM_RESOLUTION);  
  
  ledcAttachPin(PIN_LEFT_MOTOR_PWM, PWM_CHANNEL_MOTOR_LEFT);
  ledcAttachPin(PIN_RIGHT_MOTOR_PWM, PWM_CHANNEL_MOTOR_RIGHT);
  delay(500);
}

void loop() {
      if(Serial.available()>0) {
      String input=Serial.readStringUntil('\n');
      StaticJsonDocument<128> json_command;
      DeserializationError error = deserializeJson(json_command,input);

      if(error) {
        set_left_motor_stationary();
        set_right_motor_stationary();
        ledcWrite(PWM_CHANNEL_MOTOR_LEFT, 0);
        ledcWrite(PWM_CHANNEL_MOTOR_RIGHT, 0);
        
        StaticJsonDocument<128> response_json;
        response_json["error"]="1";
        String output;
        serializeJson(response_json, output);  
        Serial.print(output+"\n");
      }
      else if(json_command.containsKey("id")) {
        StaticJsonDocument<128> response_json;
        response_json["id"]="controller";
        String output;
        serializeJson(response_json, output);  
        Serial.print(output+"\n");        
      }
      else if(json_command.containsKey("motion_state")) {
        String motion_state_string=json_command["motion_state"].as<String>();
        StaticJsonDocument<128> motion_state_json;
        DeserializationError error = deserializeJson(motion_state_json,motion_state_string);
        double l=motion_state_json["l"].as<double>();
        double r=motion_state_json["r"].as<double>();
        double abs_l=abs(l);
        double abs_r=abs(r);

        set_left_motor_stationary();
        set_right_motor_stationary();

        if(abs_l<MIN_GAS&&abs_r<MIN_GAS){
          set_left_motor_stationary();
          set_right_motor_stationary();
        }
        else if(abs_l<MIN_GAS||abs_r<MIN_GAS) {
          double max_gas=max(abs_l,abs_r);

          if(max_gas==abs_l) {
            int direction=get_sign_dbl(l);
            abs_r=abs_l;

            if(direction>0) {
              set_left_motor_clockwise();
              set_right_motor_counter_clockwise();
            }
            else {
              set_left_motor_counter_clockwise();
              set_right_motor_clockwise();
            }
          }
          else {
            int direction=get_sign_dbl(r);
            abs_l=abs_r;

            if(direction>0) {
              set_left_motor_counter_clockwise();
              set_right_motor_clockwise();
            }
            else {
              set_left_motor_clockwise();
              set_right_motor_counter_clockwise();
            }
          }
        }
        else {
          if(l>0) {
            set_left_motor_counter_clockwise();            
          }
          else {
            set_left_motor_clockwise();
          }

          if(r>0) {
            set_right_motor_counter_clockwise();            
          }
          else {
            set_right_motor_clockwise();
          }
        }

        ledcWrite(PWM_CHANNEL_MOTOR_LEFT, abs_l*255);
        ledcWrite(PWM_CHANNEL_MOTOR_RIGHT, abs_r*255);

        StaticJsonDocument<128> response_json;
        response_json["error"]="0";
        response_json["abs_l"]=abs_l;
        response_json["abs_r"]=abs_r;
        String output;
        serializeJson(response_json, output);  
        Serial.print(output+"\n");  
      }
      }
      
  delay(1);
}