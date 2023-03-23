#!/usr/bin/env python3
# Allison Creely, 2018, LGPLv3 License
# Rock 64 GPIO Library for Python

import R64.GPIO as GPIO
from time import sleep
from adafruit_seesaw.seesaw import Seesaw
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient

import logging
import time
import json
import argparse
import busio

print(GPIO)
from board import SCL, SDA

print("Testing R64.GPIO Module...")

# Test Variables
print("")
print("Module Variables:")
print("Name           Value")
print("----           -----")
print("GPIO.ROCK      " + str(GPIO.ROCK))
print("GPIO.BOARD     " + str(GPIO.BOARD))
print("GPIO.BCM       " + str(GPIO.BCM))
print("GPIO.OUT       " + str(GPIO.OUT))
print("GPIO.IN        " + str(GPIO.IN))
print("GPIO.HIGH      " + str(GPIO.HIGH))
print("GPIO.LOW       " + str(GPIO.LOW))
print("GPIO.PUD_UP    " + str(GPIO.PUD_UP))
print("GPIO.PUD_DOWN  " + str(GPIO.PUD_DOWN))
print("GPIO.VERSION   " + str(GPIO.VERSION))
print("GPIO.RPI_INFO  " + str(GPIO.RPI_INFO))

print(GPIO)

# Set Variables
var_gpio_out = 16
var_gpio_in = 18

# GPIO Setup
GPIO.setwarnings(True)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(var_gpio_out, GPIO.OUT, initial=GPIO.HIGH)       # Set up GPIO as an output, with an initial state of HIGH
GPIO.setup(var_gpio_in, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Set up GPIO as an input, pullup enabled

# Test Output
print("")
print("Testing GPIO Input/Output:")

var_gpio_state = GPIO.input(var_gpio_out)                   # Return state of GPIO
print("Output State : " + str(var_gpio_state))              # Print results
sleep(1)
GPIO.output(var_gpio_out, GPIO.LOW)                         # Set GPIO to LOW

# Test Input
var_gpio_state = GPIO.input(var_gpio_in)                    # Return state of GPIO
print("Input State  : " + str(var_gpio_state))              # Print results
sleep(0.5)

# Test interrupt
print("")
print("Waiting 3 seconds for interrupt...")
var_interrupt = GPIO.wait_for_edge(var_gpio_in, GPIO.FALLING, timeout=3000)
if var_interrupt is None:
    print("Timeout!")
else:
    print("Detected!")

# Test PWM Output
p=GPIO.PWM(var_gpio_out, 60)                                # Create PWM object/instance

print("")
print("Testing PWM Output - DutyCycle - High Precision:")
print("60Hz at 50% duty cycle for 1 second")
p.start(50)
sleep(1)
print("60Hz at 25% duty cycle for 1 second")
p.ChangeDutyCycle(25)
sleep(1)
print("60Hz at 10% duty cycle for 1 second")
p.ChangeDutyCycle(10)
sleep(1)
print("60Hz at  1% duty cycle for 1 second")
p.ChangeDutyCycle(1)
sleep(1)
p.stop()

print("")
print("Testing PWM Output - DutyCycle - Low Precision:")
print("60Hz at 50% duty cycle for 1 second")
p.start(50, pwm_precision=GPIO.LOW)
sleep(1)
print("60Hz at 25% duty cycle for 1 second")
p.ChangeDutyCycle(25)
sleep(1)
print("60Hz at 10% duty cycle for 1 second")
p.ChangeDutyCycle(10)
sleep(1)
print("60Hz at  1% duty cycle for 1 second")
p.ChangeDutyCycle(1)
sleep(1)
p.stop()

print("")
print("Testing PWM Output - Frequency - Low Precision:")
print("60Hz at 50% duty cycle for 1 second")
p.start(50, pwm_precision=GPIO.LOW)
sleep(1)
print("30Hz at 50% duty cycle for 1 second")
p.ChangeFrequency(30)
sleep(1)
print("20Hz at 50% duty cycle for 1 second")
p.ChangeFrequency(20)
sleep(1)
print("10Hz at 50% duty cycle for 1 second")
p.ChangeFrequency(10)
sleep(1)
p.stop()

# Shadow JSON schema:
#
# {
#   "state": {
#       "desired":{
#           "moisture":<INT VALUE>,
#           "temp":<INT VALUE>            
#       }
#   }
# }

# Function called when a shadow is updated
def customShadowCallback_Update(payload, responseStatus, token):

    # Display status and data from update request
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")

    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print("moisture: " + str(payloadDict["state"]["reported"]["moisture"]))
        print("temperature: " + str(payloadDict["state"]["reported"]["temp"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")

    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")

# Function called when a shadow is deleted
def customShadowCallback_Delete(payload, responseStatus, token):

    # Display status and data from delete request
    if responseStatus == "timeout":
        print("Delete request " + token + " time out!")

    if responseStatus == "accepted":
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Delete request with token: " + token + " accepted!")
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")

    if responseStatus == "rejected":
        print("Delete request " + token + " rejected!")


# Read in command-line parameters
def parseArgs():

    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your device data endpoint")
    parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
    parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
    parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
    parser.add_argument("-p", "--port", action="store", dest="port", type=int, help="Port number override")
    parser.add_argument("-n", "--thingName", action="store", dest="thingName", default="Bot", help="Targeted thing name")
    parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicShadowUpdater", help="Targeted client id")

    args = parser.parse_args()
    return args


# Configure logging
# AWSIoTMQTTShadowClient writes data to the log
def configureLogging():

    logger = logging.getLogger("AWSIoTPythonSDK.core")
    logger.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)


# Parse command line arguments
args = parseArgs()

if not args.certificatePath or not args.privateKeyPath:
    parser.error("Missing credentials for authentication.")
    exit(2)

# If no --port argument is passed, default to 8883
if not args.port: 
    args.port = 8883


# Init AWSIoTMQTTShadowClient
myAWSIoTMQTTShadowClient = None
myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(args.clientId)
myAWSIoTMQTTShadowClient.configureEndpoint(args.host, args.port)
myAWSIoTMQTTShadowClient.configureCredentials(args.rootCAPath, args.privateKeyPath, args.certificatePath)

# AWSIoTMQTTShadowClient connection configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10) # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5) # 5 sec

# Initialize Raspberry Pi's I2C interface
i2c_bus = busio.I2C(SCL, SDA)

# Intialize SeeSaw, Adafruit's Circuit Python library
ss = Seesaw(i2c_bus, addr=0x36)

# Connect to AWS IoT
myAWSIoTMQTTShadowClient.connect()

# Create a device shadow handler, use this to update and delete shadow document
deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(args.thingName, True)

# Delete current shadow JSON doc
deviceShadowHandler.shadowDelete(customShadowCallback_Delete, 5)

# Read data from moisture sensor and update shadow
while True:

    # read moisture level through capacitive touch pad
    moistureLevel = ss.moisture_read()

    # read temperature from the temperature sensor
    temp = ss.get_temp()

    # Display moisture and temp readings
    print("Moisture Level: {}".format(moistureLevel))
    print("Temperature: {}".format(temp))

    # Create message payload
    payload = {"state":{"reported":{"moisture":str(moistureLevel),"temp":str(temp)}}}

    # Update shadow
    deviceShadowHandler.shadowUpdate(json.dumps(payload), customShadowCallback_Update, 5)
    time.sleep(1)

GPIO.cleanup([var_gpio_in, var_gpio_out])                   # Perform cleanup on specified GPIOs

print("")
print("Test Complete")

