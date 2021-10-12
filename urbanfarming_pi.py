#!/usr/bin/env python3

import time
import requests
import json
import serial
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
    unixtime = time.time()
    systemData = json.dumps({
        'systemName': systemName,
        'ownerID': ownerID,
        'plantType': plantType,
        'humidity': {'value': data['humidity'], 'time': unixtime},
        'temperature': {'value': data['temp'], 'time': unixtime},
        'pH': {'value': data['pH'], 'time': unixtime},
        'EC': {'value': data['EC'], 'time': unixtime}
    })

    resp = requests.post(url, data=systemData, headers=headers)

    id = resp.json()['_id']
    with open('id.json', 'w') as f:
        json.dump(id, f)

def post():
    unixtime = time.time()
    updateData = json.dumps({
        'humidity': {'value': data['humidity'], 'time': unixtime},
        'temperature': {'value': data['temp'], 'time': unixtime},
        'pH': {'value': data['pH'], 'time': unixtime},
        'EC': {'value': data['EC'], 'time': unixtime}
    })

    requests.put(url + id, data=updateData, headers=headers)

def readData():
    if ser.in_waiting > 0:
        # line = ser.readline().rstrip()
        # print(line)
        line = ser.readline().rstrip().decode()
        data['EC'] = unpack('<f', bytes.fromhex(line[0:8]))[0]
        data['pH'] = unpack('<f', bytes.fromhex(line[8:16]))[0]
        data['temp'] = unpack('<f', bytes.fromhex(line[16:24]))[0]
        data['humidity'] = unpack('<f', bytes.fromhex(line[24:32]))[0]
        print("received sensor data")

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
    scheduler.add_job(lightOn, 'cron', second=0, id="lighton") #hour=9)
    scheduler.add_job(lightOff, 'cron', second=30, id="lightoff") #hour=18)
    scheduler.add_job(post, 'cron', minute='*/10')
    scheduler.start()

# need to get data from server?
def changeLightHours(on, off):
    global scheduler
    print("changing light hours")
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

def controlSystem():
    global data
    # test humidity
    # if data['humidity'] < 13262:
    #   changePumpInterval(123123,1241241)
    # else if data['humidity'] > 12353:
    #   changePumpInterval(123123,1241241)
    #
    # test ec
    # if data['EC'] < 123123:
    #   asdasd
    # else if data['EC'] > 23412:
    #   asdad

if __name__ == '__main__':
    # firstPost("testsystem", 1, "testplant", {"humidity": "80", "temp": "25", "pH":"6.5", "EC":"1.6"})
    ser = serial.Serial('/dev/ttyACM0', 9600)
    ser.flush()
    background_schedule()

    while True:
        readData()
        controlSystem()
