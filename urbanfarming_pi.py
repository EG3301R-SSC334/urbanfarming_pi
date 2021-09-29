#!/usr/bin/env python3

import time
import requests
import json
import serial
from apscheduler.schedulers.background import BackgroundScheduler
from struct import *


url = 'https://urban-farming-demo.herokuapp.com/systems/'
headers = {'content-type': 'application/json'}

f = open('id.json')
id = json.load(f)
data = {}
resched_flag = 1

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
        line = ser.readline().rstrip().decode()
        data['EC'] = unpack('<f', bytes.fromhex(line[0:8]))[0]
        data['pH'] = unpack('<f', bytes.fromhex(line[8:16]))[0]
        data['temp'] = unpack('<f', bytes.fromhex(line[16:24]))[0]
        data['humidity'] = unpack('<f', bytes.fromhex(line[24:32]))[0]
        print("reading data")

def mainPumpOn():
    print("spraying")

def mainPumpOff():
    print("not spraying")

def pPump():
    print("peristaltic")

def lightOn():
    print("light on")

def lightOff():
    print("light off")

def background_schedule():
    global scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(mainPumpOn, 'interval', seconds=10, id="pumpon") #minutes=17)
    scheduler.add_job(mainPumpOff, 'interval', seconds=10, id="pumpoff") #minutes=17)
    scheduler.add_job(lightOn, 'cron', minute='*/1', id="lighton") #hour=9)
    scheduler.add_job(lightOff, 'cron', minute='*/2', id="lightoff") #hour=18)
    scheduler.add_job(post, 'cron', minute='*/10')
    scheduler.start()

def controlSystem():
    global data, scheduler, resched_flag
    if resched_flag:
        print("rescheduling")
        scheduler.reschedule_job("pumpon", trigger='interval', seconds=20)
        resched_flag = 0

if __name__ == '__main__':
    # firstPost("testsystem", 1, "testplant", {"humidity": "80", "temp": "25", "pH":"6.5", "EC":"1.6"})
    ser = serial.Serial('/dev/ttyACM0', 9600)
    ser.flush()
    background_schedule()

    while True:
        readData()
        controlSystem()
