#!/usr/bin/env python3

import time
import requests
import json
import serial

url = 'https://urban-farming-demo.herokuapp.com/systems/'
headers = {'content-type': 'application/json'}

f = open('id.json')
id = json.load(f)

def firstPost(systemName, ownerID, plantType, data):
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

    print("POST: " + str(resp))

    id = resp.json()['_id']
    with open('id.json', 'w') as f:
        json.dump(id, f)

def post(data):
    unixtime = time.time()
    updateData = json.dumps({
        'humidity': {'value': data['humidity'], 'time': unixtime},
        'temperature': {'value': data['temp'], 'time': unixtime},
        'pH': {'value': data['pH'], 'time': unixtime},
        'EC': {'value': data['EC'], 'time': unixtime}
    })

    requests.put(url + id, data=updateData, headers=headers)

post({'humidity': '85', 'temp': 28, 'pH': 6.5, 'EC': 1.7})

if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    ser.flush()

    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            print(line)