import socket                                   # Socket Programming
import threading                                # MultiThreading
import sqlite3                                  # SQL DataBase
# from pymongo.mongo_client import MongoClient    # MongoDB DataBase
import bcrypt                                   # Hashing Passwords
from datetime import datetime
import requests                                 # HTTP Requests
from PIL import Image
import io
import random                                   # Generate Random Numbers
import json
import signal
import sys

# RTL-ize Persian Strings
import arabic_reshaper
from bidi.algorithm import get_display

# ArvanCloud Object Storage (S3) Libraries
import boto3
import logging
from botocore.exceptions import ClientError

# Parameters
HOST = 'localhost'
PORT = 12345
MAX_CONNECTIONS = 5
# SQL Database Name
DB_FILE = 'data.db'
# Mongo Database config
MONGODB_PASSWORD = ''
# Neshan API Key
NESHAN_API_KEY = "service.a4cd78ab859e411b8c2d111eb7f0331a"


class ClientThread(threading.Thread):
    def __init__(self, conn, addr):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr

    def run(self):
        #with conn:
        while True:
            # Maximum Size of Recieving Data
            data = self.conn.recv(80000)
            if not data:
                break
            print (data)
            command, subCommand = data.decode('utf-8').split('/')
            if command == 'busUpdate':
                update_buses(subCommand)
            elif command == 'register':
                username, password = subCommand.split(',')
                insert_user(username, password, conn)
            elif command == 'login':
                username, password = subCommand.split(',')
                check_user(username, password, conn)
            elif command == 'distance':
                clientLatitude, clientLongitude = subCommand.split(',')
                busLatitude = round(random.uniform(35.610504, 35.808707), 6)
                busLongitude = round(random.uniform(51.138365, 51.605760), 6)
                response = get_distance_matrix(float(clientLatitude), float(clientLongitude), busLatitude, busLongitude)     
                send_answer(response, conn)
                print("Distance Was Sent to user")
            elif command == 'stationArivalTime':
                response = 'In Developement State!!!'
                send_answer(response, conn)
            elif command == 'ticket':
                unicQR = username + str(random.uniform(1, 1000))
                url = 'https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=' + unicQR
                response = requests.get(url)
                response = response.content
                conn.sendall(response)
                print('Ticket was sent to user')       
            elif command == 'review':
                busID, review = subCommand.split(',')
                response = update_reviews(int(busID), int(review))
                send_answer(response, conn)
                print("Response was Sent to user")        
            elif command == 'driverPic':
                busID = subCommand
                response = get_driver_image(int(busID))
                conn.sendall(response)
                print('Picture was Sent to user')       
            else:
                print ('command not defined!')
        self.conn.close()


def get_driver_image(busID):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Check for bus_id in Table
    c.execute("SELECT driver_pic FROM buses WHERE bus_id = ?", (busID,))
    result = c.fetchone()
    conn.close()
    # Update row if Exist or Insert row if not Exist
    if not result:
        return(f"Error: bus_id {busID} not found.")
    else:
        driverPicPath = result[0]
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        try:
            # S3 resource
            s3_resource = boto3.resource(
                's3',
                endpoint_url='https://s3.ir-thr-at1.arvanstorage.ir',
                aws_access_key_id='a503d236-3243-466a-8ef9-a8a4d804a185',
                aws_secret_access_key='c0ae1b6f0ca5f82c8f653fb4851257d7afe03c9a24bcac958771b56d8f38bc40'
            )
        except Exception as exc:
            logging.error(exc)
        else:
            try:
                bucket_name = 'cloudproject'
                bucket = s3_resource.Bucket(bucket_name)
                # download the image file
                object_name = driverPicPath
                print(object_name)
                download_path = 'driver.jpg'
                bucket.download_file(object_name, download_path)
                with open(download_path, 'rb') as f:
                    image_data = f.read()
                # # show the downloaded image
                # with Image.open(download_path) as img:
                #     img.show()
                return image_data
            except ClientError as e:
                logging.error(e)


def update_reviews(busID, review):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT review_count, review_mark FROM buses WHERE bus_id=?", (busID,))
    result = c.fetchone()
    if result is None:
        conn.close()
        print(f"Error: bus_id {busID} not found.")
        return(f"Error: bus_id {busID} not found.")
    else:
        if result[0] is None:
            review_count = 0
            review_mark = 0
        else:
            review_count = result[0]
            review_mark = result[1]
        new_review_count = review_count + 1
        new_review_mark = (review_mark * review_count + review) / new_review_count
        c.execute("UPDATE buses SET review_count=?, review_mark=? WHERE bus_id=?", (new_review_count, new_review_mark, busID))
        conn.commit()
        conn.close()
        print("Review was Submitted in DataBase")
        return (f"Thanks for your review")


def get_distance_matrix(clientLatitude, clientLongitude, busLatitude, busLongitude):
    response = requests.get(f"https://api.neshan.org/v1/distance-matrix?type=car&origins={clientLatitude},{clientLongitude}&destinations={busLatitude},{busLongitude}",
                       headers={"Api-Key": NESHAN_API_KEY})
    if response.status_code == 200:
        for i, row in enumerate(response.json()['rows']):
            origin = response.json()['origin_addresses'][i]
            for j, element in enumerate(row['elements']):
                destination = response.json()['destination_addresses'][j]
                duration = element['duration']['text']
                distance = element['distance']['text']
                print(f"From {origin} to {destination}:")
                print(f"Duration: {convert(duration)}")
                print(f"Distance: {convert(distance)}")
                response = convert(distance) + ',' + convert(duration)
        return response
    else:
        print(response.status_code)
        return("Error in request to Neshan!")


def send_answer(message, socketConn):
    socketConn.sendall(message.encode('utf-8'))


def create_database():
    conn = sqlite3.connect(DB_FILE)
    #Table for Buses Data
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS buses 
                 (bus_id INTEGER PRIMARY KEY, line INTEGER, latitude REAL, longitude REAL, 
                 last_modified TEXT, populate INTEGER, latency INTEGER, review_mark REAL,
                 review_count INTEGER, driver_name TEXT, driver_pic TEXT)''')
    conn.commit()
    #Table for Users Data
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT NOT NULL, password TEXT NOT NULL,
                 profile_pic TEXT, ticket_count INTEGER)''')
    conn.commit()
    conn.close()


# def creat_mongo_database():
#     url = "mongodb+srv://hamidreza:{MONGODB_PASSWORD}@cluster0.ziwgtn7.mongodb.net/?retryWrites=true&w=majority"
#     # Create a new client and connect to the server
#     client = MongoClient(url)
#     # Send a ping to confirm a successful connection
#     try:
#         client.admin.command('ping')
#         print("Pinged your deployment. You successfully connected to MongoDB!")
#     except Exception as e:
#         print(e)


def update_buses(subCommand):
    bus_id, line, latitude, longitude, lastModified, populate, latency ,driver_name, driver_pic = subCommand.split(',')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Check for bus_id in Table
    c.execute("SELECT bus_id FROM buses WHERE bus_id = ?", (bus_id,))
    result = c.fetchone()
    # Update row if Exist or Insert row if not Exist
    if not result:
        c.execute("INSERT INTO buses (bus_id, line, latitude, longitude, last_modified, populate, latency, driver_name, driver_pic) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                  (int(bus_id), int(line), float(latitude), float(longitude), lastModified,
                   int(populate), int(latency), driver_name, driver_pic))
    else:
        update_query = "UPDATE buses SET line = ?, latitude = ?, longitude = ?, last_modified = ?, populate = ?, latency = ?"
        update_values = (int(line), float(latitude), float(longitude), lastModified, int(populate), int(latency))
        if driver_name != '':
            update_query += ", driver_name = ?"
            update_values += (driver_name,)
        if driver_pic != '':
            update_query += ", driver_pic = ?"
            update_values += (driver_pic,)
        update_query += " WHERE bus_id = ?"
        update_values += (int(bus_id),)
        c.execute(update_query, update_values)
    conn.commit()
    conn.close()
    print(f'Bus {bus_id} data updated in database')


def check_user(username, password, socketConn):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=?', (username,))
    user = c.fetchone()
    if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
        send_answer('OK', socketConn)
    else:
        send_answer('Invalid credentials', socketConn)
    conn.close()


def insert_user(username, password, socketConn):
    # ایجاد هش شده از رمز عبور
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    existing_user = c.fetchone()
    if existing_user:
        send_answer("Error: Username already exists.", socketConn)
    else:
        # افزودن کاربر جدید به دیتابیس
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        send_answer("User added successfully.", socketConn)
    conn.close()


# RTL-ize Persian Srings 
def convert(text):
    reshaped_text = arabic_reshaper.reshape(text)
    converted = get_display(reshaped_text)
    return converted


# conn = sqlite3.connect(DB_FILE)
# c = conn.cursor()
# # حذف جدول
# c.execute('DROP TABLE IF EXISTS buses')
# # ذخیره تغییرات و بستن اتصال
# conn.commit()
# conn.close()


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(MAX_CONNECTIONS)
    print("Server started and listening for connections on port: " + str(PORT))
    create_database()
    while True:
        conn, addr = s.accept()
        print(f"New client connected: {addr} at {datetime.now()}")
        # Create a New Thread for New Client
        client_thread = ClientThread(conn, addr)
        client_thread.start()

