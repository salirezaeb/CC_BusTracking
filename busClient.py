import socket
import random
from datetime import datetime

HOST = 'localhost'
PORT = 12345

def send_values_to_server(values):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        data = ','.join(str(value) for value in values)
        data = 'busUpdate/' + data
        s.sendall(data.encode('utf-8'))
        print(data + 'was Sent')
        

while True:
    values = []
    busID = input("Bus ID: ")
    values.append(busID)
    Line = input("Line: ")
    values.append(Line)
    busLatitude = round(random.uniform(35.610504, 35.808707), 6)
    values.append(busLatitude)
    busLongitude = round(random.uniform(51.138365, 51.605760), 6)            
    values.append(busLongitude)
    lastModified = datetime.now()            
    values.append(lastModified)
    population = input("Population: ")
    values.append(population)
    latency = input("Latency: ")
    values.append(latency)
    driverName = input("Driver Name: ")
    values.append(driverName)
    driverPic = input("Driver Profile: ")
    values.append(driverPic)
    send_values_to_server(values)
    values = []
    print ('update request was sent to server\n')
