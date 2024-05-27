import socket
import random
import os
import requests
from PIL import Image
import io


HOST = 'localhost'
PORT = 12345 #پورت سرور
MAX_TRIES = 5  # حداکثر تعداد تلاش‌ها


def register(tcpConn, values):
    data = ','.join(str(value) for value in values)
    data = 'register/' + data
    print(data)
    tcpConn.sendall(data.encode('utf-8'))
    print('register request was sent to server\n')
    response = tcpConn.recv(1024)  # دریافت پاسخ سرور
    print(response.decode('utf-8'))  # چاپ پاسخ سرور
    

def login(tcpConn, values):
    data = ','.join(str(value) for value in values)
    data = 'login/' + data
    print(data)
    tcpConn.sendall(data.encode('utf-8'))
    print('login request was sent to server\n')
    response = tcpConn.recv(1024)  # دریافت پاسخ سرور
    if response.decode('utf-8')=='OK':
        logined(username, tcpConn)
    else:
        print(response.decode('utf-8'))  # چاپ پاسخ سرور 
        

def logined(username, tcpConn):
    while True:
        os.system('cls')
        print('Hello ' + username)
        select = input('1. Nearest Station\n2. Station Time\n3. Buy Ticket\n4. Review\n5. Driver Profile\n6. Exit\n')
        if select == '1':
            latitude = round(random.uniform(35.610504, 35.808707), 6)
            longitude = round(random.uniform(51.138365, 51.605760), 6)
            location = str(latitude) + ',' + str(longitude)
            request = 'distance/' + location
            response = send_request_to_server(request, tcpConn)
            print(response)
            input()
        elif select == '2':
            stationNumber = input('Station Number: ')
            request = 'stationTime/' + stationNumber
            response = send_request_to_server(request, tcpConn)
            print(response)
            input()
        elif select == '3':
            request = 'ticket/'
            response = send_request_to_server(request, tcpConn)
            print('Your QR Ticket: ')
            image = Image.open(io.BytesIO(response))
            image = image.convert("RGBA")
            image.show()
        elif select == '4':
            busID = input('BUS ID: ')
            review = input('Review (1 to 5): ')
            request = 'review/' + busID + ',' + review 
            response = send_request_to_server(request, tcpConn)
            print(response.decode('utf-8'))
            input()
        elif select == '5':
            busID = input('BUS ID: ')
            request = 'driverPic/' + busID 
            response = send_request_to_server(request, tcpConn)
            img = Image.open(io.BytesIO(response))
            # Display the image
            img.show()
        elif select == '6':
            os.system('cls')
            break
        else:
            print('not defined')

 

def send_request_to_server(request, tcpConn):
    tcpConn.settimeout(10)  # تنظیم زمان انتظار برای دریافت پاسخ به 10 ثانیه
    try:
        tcpConn.sendall(request.encode('utf-8'))
        print('request was sent to server\n')
        response = tcpConn.recv(80000)  # دریافت پاسخ سرور
        return response
    except socket.timeout:
        print('Error: Connection timed out')
        return None
    

tries = 0  # شمارنده‌ی تعداد تلاش‌ها
os.system('cls')
while tries < MAX_TRIES:
    print('Trying to Connect to Server...')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((HOST, PORT))
        print ('Connected\n') 
        print('Welcome to CBUSMA')
        while True:
            select = input('1. Login\n2. Register\n3. Exit\n')
            if select == '1':
                values = []
                username = input("username: ")
                values.append(username)
                password = input("password: ")
                values.append(password)
                login(s, values)
            elif select == '2':
                values = []
                username = input("username: ")
                values.append(username)
                password = input("password: ")
                values.append(password)
                register(s, values)
            elif select == '3':
                break
            else:
                print('not defined')
    except socket.error:
        print("Unable to connect to server")
    finally:
        s.close()
        if select=='3':
            break
        else:
            tries += 1  # افزایش شمارنده‌ی تعداد تلاش‌ها
    
    if tries == MAX_TRIES:
        print("Could not connect to server after 5 attempts.")