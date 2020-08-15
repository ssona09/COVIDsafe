import threading
import socket
import json
import sys
from random import randint
import time
import os 
import datetime
import secrets

#HOST = '127.0.0.1'
SERVER_PORT = int(sys.argv[1])
BLOCK_DURATION = int(sys.argv[2])

#Create TempIDs.txt and override with emptiness
open('tempIDs.txt', 'w').close()

class Global:
    invalid_attempt = 0

#Multithreaded TCP server code modified from:
#https://www.tutorialspoint.com/python3/python_multithreading.htm
class myThread (threading.Thread):
    def __init__(self, conn,addr,HOST,SERVER_PORT):
      threading.Thread.__init__(self)
      self.conn = conn
      self.addr = addr
      self.HOST = HOST
      self.SERVER_PORT = SERVER_PORT


    def run(self):
        while True:
            data = self.conn.recv(1024)
            
            if data:
                data_dict = json.loads(data)
                if data_dict['messageType'] == 'login':
                    #if verify success, server shall response the tempid to client
                    f = open("credentials.txt", "r")
                    contents = f.readlines()
                    lst = []
                    verify_success = False
                    for line in contents:
                        line_final = line.replace('\n',' ')
                        lst = line_final.split(' ')
                        if lst[0] == data_dict['username'] and lst[1] == data_dict['password']:
                            verify_success = True
                            break
                            

                    if verify_success == False:
                        Global.invalid_attempt = Global.invalid_attempt + 1
                        if Global.invalid_attempt == 3:
                            Global.invalid_attempt = 0
                            #block login attempts for BLOCK_DURATION
                            message = {
                                'messageType':'welcomemessage',
                                'welcome_message':"Invalid Password. Your account has been blocked. Please try again later"
                            }
                            self.conn.send(json.dumps(message).encode('utf-8'))
                            
                            time.sleep(BLOCK_DURATION)
                            self.conn.send(json.dumps(message).encode('utf-8'))
                            
                            
                        
                        else:    
                            message = {
                                'messageType':'welcomemessage',
                                'welcome_message':"Invalid password. Please try again"
                            }
                            self.conn.send(json.dumps(message).encode('utf-8'))
                            

                    else:
                        
                        message = {
                            'messageType':'welcomemessage',
                            'welcome_message':"Welcome to the BlueTrace simulator"
                        }
                        self.conn.send(json.dumps(message).encode('utf-8'))
                        Global.invalid_attempt = 0                   
                    
                elif data_dict['messageType'] == 'Upload_contact_log':
                    username = data_dict['username']
                    print(f"received contact log from {username}")
                    #print contact log on server terminal
                    f = open("z5258346_contactlog.txt", "r")
                    contents = f.readlines()
                    counter = 0
                    for line in contents:
                        print(line)
                        counter = counter + 1
                        if counter == 10:
                            break
                            
                    #contact log checking
                    print("Contact log checking")
                    f = open("z5258346_contactlog.txt", "r")
                    contents = f.readlines()
                    lst = []
                    verify_success = False
                    for line in contents:
                        line_final = line.replace('\n',' ')
                        lst = line_final.split(' ')
                        print(username + " " + lst[1] + " " + lst[2] + " " + lst[3] + " " + lst[4])
                        
                    message = {
                        'messageType' : 'done'
                    }
                    self.conn.send(json.dumps(message).encode('utf-8'))
                    
                elif data_dict['messageType'] == 'Download_tempID':
                    tempID = secrets.randbits(160)
                    username = data_dict['user']
                    #store username and start and expire time in tempIDs.txt
                    #expire time is 15 mins after current time
                    #borrowed code for calculating time difference from time strings
                    #https://www.programiz.com/python-programming/datetime/strptime
                    start_time = datetime.datetime.now()
                    expire_time = start_time + datetime.timedelta(minutes = 15)
                    start = start_time.strftime("%m/%d/%Y %H:%M:%S")
                    expire = expire_time.strftime("%m/%d/%Y %H:%M:%S")
                    
                    filename = 'tempIDs.txt'
                    TempID = open(filename,'a')
                    TempID.write(username + " " + str(tempID) + " " + start + " " + expire + '\n')
                    TempID.close()
                    
                    message = {
                        'messageType':'tempid',
                        'tempID':tempID
                    }
                    self.conn.send(json.dumps(message).encode('utf-8'))
                    print(tempID)
                    
                elif data_dict['messageType'] == 'logout':
                    #logout/ end server program
                    serverServices()

def serverServices():
    Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #get IP from OS
    host_name = socket.gethostname() 
    host_ip = socket.gethostbyname(host_name)
    HOST = str(host_ip)
    
    Server.bind((HOST, SERVER_PORT))
    print(f"connected to {HOST} ")
    Server.listen()

    while True:
        conn, addr  = Server.accept()
        thread1 = myThread(conn,addr,HOST,SERVER_PORT)
        thread1.start()

    
serverServices()

                    
                
