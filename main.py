# in case you need to reset:
# 1: esptool.py --port /dev/ttyUSB0 erase_flash
# 2: esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=8m 0 esp8266-20160909-v1.8.4.bin

# otherwise: ampy --port /dev/ttyUSB0 put main.py /main.py
# to see output: screen /dev/ttyUSB0 115200

import network
import time
import machine
import gc
from umqtt.simple import MQTTClient

print("Running program")
# Wifi variables
wifi_ssid = "Nortugget"
wifi_pwd = "palsternacka"

# MQTT variables
mqtt_server = "10.0.0.131"
mqtt_id = "lamp_livingroom"
mqtt_topic = "rgbw/1"

FREQUENCY = 100
SATURATION_MIN = 0
SATURATION_MAX = 200
COLOR_MAX = 1530

RED = 13
GREEN = 12
BLUE = 14
WHITE = 2
SWITCH = 15

lamp_status = 1
lamp_brightness = 0
lamp_red = 0
lamp_green = 0
lamp_blue = 0
lamp_white = 0
lamp_random = 0
lamp_speed = 0

lamp_saturation_white = 0
lamp_saturation_color = 0


# init pwm pins
pin_green = machine.Pin(GREEN)
pin_red = machine.Pin(RED)
pin_blue = machine.Pin(BLUE)
pin_white = machine.Pin(WHITE)
pin_switch = machine.Pin(SWITCH, machine.Pin.OUT)

pwm_green = machine.PWM(pin_green)
pwm_red = machine.PWM(pin_red)
pwm_blue = machine.PWM(pin_blue)
pwm_white = machine.PWM(pin_white)
# max duty is 1024
pwm_green.freq(500)
pwm_green.duty(0)
pwm_red.freq(500)
pwm_red.duty(0)
pwm_blue.freq(500)
pwm_blue.duty(0)
pwm_white.freq(500)
pwm_white.duty(1024)

def rgbw_calc_color(color):
    global lamp_red
    global lamp_green
    global lamp_blue
    if (color >= 0) and (color <= 1*COLOR_MAX/6):
        lamp_red = 1*COLOR_MAX/6
        lamp_green = color
        lamp_blue = 0
    elif (color >= 1*COLOR_MAX/6) and (color <= 2*COLOR_MAX/6):
        lamp_red = 1*COLOR_MAX/6 - (color - 1*COLOR_MAX/6)
        lamp_green = 1*COLOR_MAX/6
        lamp_blue = 0
    elif (color >= 2*COLOR_MAX/6) and (color <= 3*COLOR_MAX/6):
        lamp_red = 0
        lamp_green = 1*COLOR_MAX/6
        lamp_blue = 1*COLOR_MAX/6 - (3*COLOR_MAX/6 - color)
    elif (color >= 3*COLOR_MAX/6) and (color <= 4*COLOR_MAX/6):
        lamp_red = 0
        lamp_green = 1*COLOR_MAX/6 - (color - 3*COLOR_MAX/6)
        lamp_blue = 1*COLOR_MAX/6
    elif (color >= 4*COLOR_MAX/6) and (color <= 5*COLOR_MAX/6):
        lamp_red = 1*COLOR_MAX/6 - (5*COLOR_MAX/6 - color)
        lamp_green = 0
        lamp_blue = 1*COLOR_MAX/6
    elif (color >= 5*COLOR_MAX/6) and (color <= COLOR_MAX):
        lamp_red = 1*COLOR_MAX/6
        lamp_green = 0
        lamp_blue = COLOR_MAX - color
    else:
        print ("Color error")
    # Debug
    print (lamp_red)
    print (lamp_green)
    print (lamp_blue)

def rgbw_calc_saturation(saturation):
    global lamp_saturation_white
    global lamp_saturation_color
    if (saturation >= SATURATION_MIN and saturation <= SATURATION_MAX / 2):
        lamp_saturation_white = SATURATION_MAX / 2
        lamp_saturation_color = saturation
    elif (saturation > SATURATION_MAX / 2 and saturation <= SATURATION_MAX):
        lamp_saturation_color = SATURATION_MAX / 2
        lamp_saturation_white = SATURATION_MIN - saturation

def rgbw_calc_pwm():
    global pwm_white
    global pwm_red
    global pwm_green
    global pwm_blue
    pwm_white.duty(int(1024 * lamp_white * lamp_status * (lamp_brightness/100) * (lamp_saturation_white/100)))
    pwm_red.duty(int(1024 * lamp_red * lamp_status * (lamp_brightness/100) * (lamp_saturation_color/100)))
    pwm_green.duty(int(1024 * lamp_green * lamp_status * (lamp_brightness/100) * (lamp_saturation_color/100)))
    pwm_blue.duty(int(1024 * lamp_blue * lamp_status * (lamp_brightness/100) * (lamp_saturation_color/100)))


def mqtt_parser(msg):
    global lamp_status
    global lamp_brightness
    global lamp_speed

    lamp_status = float(msg.split(':')[0])
    lamp_brightness = float(msg.split(':')[1])
    saturation = float(msg.split(':')[2])
    color = float(msg.split(':')[3])
    lamp_speed = float(msg.split(':')[4])
    # for debugging
    print (lamp_status)
    print (lamp_brightness)
    print (color)
    print (saturation)
    print (lamp_speed)
    rgbw_calc_color(color)
    rgbw_calc_saturation(saturation)
    rgbw_calc_pwm()

# MQTT functions
def mqtt_callback(topic, msg):
    global state
    print((topic, msg))
    mqtt_parser(msg.decode("utf-8"))


def mqtt_connect():
    c = MQTTClient(mqtt_id, mqtt_server)
    # Subscribed messages will be delivered to this callback
    c.set_callback(mqtt_callback)
    c.connect()
    c.subscribe(mqtt_topic)
    print("Connected to %s, subscribed to %s topic" % (mqtt_server, mqtt_topic))

    try:
        while 1:
            #micropython.mem_info()
            c.wait_msg()
    finally:
        c.disconnect()

def wifi_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(wifi_ssid, wifi_pwd)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

wifi_connect()
mqtt_connect()
print("End of program")
