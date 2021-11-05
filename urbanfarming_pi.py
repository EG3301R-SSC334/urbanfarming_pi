#!/usr/bin/env python3

from os import X_OK
import time
import requests
import json
import serial
import logging
from PID import PID
from apscheduler.schedulers.background import BackgroundScheduler
from struct import *

logging.basicConfig(filename='plantstation.log', level=logging.DEBUG)
url = 'https://urban-farming-demo.herokuapp.com/systems/'
headers = {'content-type': 'application/json'}

with open('id.json', 'r') as f:
    id = json.load(f)
data = {}
data['EC'] = 1.8
data['pH'] = 6.5
data['temp'] = 25.0
data['humidity'] = 98.2
data['time'] = time.time()
resched_flag = 1
pump_flag = 0

def firstPost(systemName, ownerID, plantType):
    global id
    systemData = json.dumps({
        'systemName': systemName,
        'ownerID': ownerID,
        'plantType': plantType,
        'humidity': {'value': data['humidity'], 'time': data['time']},
        'temperature': {'value': data['temp'], 'time': data['time']},
        'pH': {'value': data['pH'], 'time': data['time']},
        'EC': {'value': data['EC'], 'time': data['time']}
    })

    resp = requests.post(url + "sensordata/", data=systemData, headers=headers)

    id = resp.json()['_id']
    with open('id.json', 'w') as f:
        json.dump(id, f)

def post():
    logging.info("Posting data to server")
    updateData = json.dumps({
        'humidity': {'value': data['humidity'], 'time': data['time']},
        'temperature': {'value': data['temp'], 'time': data['time']},
        'pH': {'value': data['pH'], 'time': data['time']},
        'EC': {'value': data['EC'], 'time': data['time']}
    })

    requests.put(url + "sensordata/" + id, data=updateData, headers=headers)

def readData():
    if ser.in_waiting > 0:
        line = ser.readline().rstrip().decode()
        data['EC'] = unpack('<f', bytes.fromhex(line[0:8]))[0]
        # data['pH'] = unpack('<f', bytes.fromhex(line[8:16]))[0]
        # data['temp'] = unpack('<f', bytes.fromhex(line[16:24]))[0]
        # data['humidity'] = unpack('<f', bytes.fromhex(line[24:32]))[0]
        data['time'] = time.time()
        logging.info("Sensor data received")
        logging.info("EC: " + str(data['EC']))
        pid_out = pid.update(data['EC'], data['time'])
        logging.info("PID Output: " + str(pid_out))
        if pid_out < -5:
            val = int(pid_out*200)
            controlEC(1, val)
        elif pid_out > 5:
            val = int(pid_out*200)
            controlEC(0, val)
        else: 
            logging.info("PID within range, no solution added")

### mainpump(1), onduration(6), offduration(6)
### peristaltic pump(1), pumpselect(1), duration(6)
### light(1), on/off(1)

def lightOn():
    logging.info("Light on")
    ser.write(b"30\n")

def lightOff():
    logging.info("Light off")
    ser.write(b"31\n")

def background_schedule():
    global scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(lightOn, 'cron', hour=9, id="lighton")
    scheduler.add_job(lightOff, 'cron', hour=18, id="lightoff")
    scheduler.add_job(post, 'cron', minute='*/10')
    scheduler.add_job(changeLightHours, 'cron', minute=30)
    scheduler.start()

def changeLightHours():
    global scheduler
    resp = requests.get(url + id)
    on = resp.json()["lighting"][0]
    off = resp.json()["lighting"][1]
    logging.info("Changing light hours to " + str(on) + " and " + str(off))
    scheduler.reschedule_job("lighton", trigger='cron', hour=on)
    scheduler.reschedule_job("lightoff", trigger='cron', hour=off)

def changePumpInterval(on, off):
    logging.info("Changing pump interval")
    logging.info("On: " + str(on))
    logging.info("Off: " + str(off))
    onstr = ("0" * (6 - len(str(on)))) + str(on)
    offstr = ("0" * (6 - len(str(off)))) + str(off)
    data = "1" + onstr + offstr + "\n"
    ser.write(bytes(data, 'UTF-8'))

def controlEC(pump, duration):
    logging.info("Pump Duration: " + str(duration))
    durationstr = ("0" * (6 - len(str(duration)))) + str(duration)
    data = "2" + str(pump) + durationstr + "\n"
    ser.write(bytes(data, 'UTF-8'))

if __name__ == '__main__':
    # firstPost("testsystem", 1, "testplant", {"humidity": "80", "temp": "25", "pH":"6.5", "EC":"1.6"})
    ser = serial.Serial('/dev/ttyACM0', 9600)
    ser.flush()
    background_schedule()
    pid = PID(1, 0, 2, 1.8)

    while True:
        readData()
