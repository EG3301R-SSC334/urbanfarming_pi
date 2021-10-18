#!/usr/bin/env python3

from os import X_OK
import time
import requests
import json
import serial
from PID import PID
from apscheduler.schedulers.background import BackgroundScheduler
from struct import *


url = 'https://urban-farming-demo.herokuapp.com/systems/'
headers = {'content-type': 'application/json'}

with open('id.json', 'r') as f:
    id = json.load(f)
data = {}
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
        data['pH'] = unpack('<f', bytes.fromhex(line[8:16]))[0]
        data['temp'] = unpack('<f', bytes.fromhex(line[16:24]))[0]
        data['humidity'] = unpack('<f', bytes.fromhex(line[24:32]))[0]
        data['time'] = time.time()
        print("received sensor data")
        print("EC: " + data['EC'])
        pid_out = pid.update(data['EC'], data['time'])
        print(pid_out)
        if pid_out>0:
            val = int(pid_out*10)
            controlEC(1, val)
        else:
            val = int(pid*10)
            controlEC(2, val)

### mainpump(1), onduration(6), offduration(6)
### peristaltic pump(1), pumpselect(1), duration(6)
### light(1), on/off(1)

def lightOn():
    print("light on")
    ser.write(b"31\n")

def lightOff():
    print("light off")
    ser.write(b"30\n")

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
    print("changing light hours to " + str(on) + " and " + str(off))
    scheduler.reschedule_job("lighton", trigger='cron', hour=on)
    scheduler.reschedule_job("lightoff", trigger='cron', hour=off)

def changePumpInterval(on, off):
    print("changing pump interval")
    onstr = ("0" * (6 - len(str(on)))) + str(on)
    offstr = ("0" * (6 - len(str(off)))) + str(off)
    data = "1" + onstr + offstr + "\n"
    ser.write(bytes(data, 'UTF-8'))

def controlEC(pump, duration):
    print("altering ec")
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
