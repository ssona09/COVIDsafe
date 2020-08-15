import threading
import socket
import json
import sys
import time
import datetime 

#SERVER_IP = '127.0.0.1'
#below is SERVER_IP...
HOST = sys.argv[1]
SERVER_PORT = int(sys.argv[2])
CLIENT_UDP_PORT = int(sys.argv[3]) 

#Create z5258346_contactlog.txt and override with emptiness
#open('z5258346_contactlog.txt', 'w').close()

class Global:
    tempid_valid = False
    my_temp_id = ''
    first_login = True

'''
Take in commands: Download_tempID, Upload_contact_log, logout, Beacon
'''
def commands(Client, username):
    command = input('>')   
    
    #send beacon to central device
    size = len(command.split())   
    if size == 3:
        first_word = command.split()[0]
        if first_word == "Beacon":
            dest_IP = command.split()[1]
            dest_port = int(command.split()[2])
            SendingBeacons(dest_IP, dest_port, username)
            commands(Client, username)
        
    if command == "Download_tempID":
        message = {
            'messageType': command,
            'user': username,
        }
        Client.send(json.dumps(message).encode('utf-8'))
        response = Client.recv(1024)
        response_dict = json.loads(response)
        #print on client terminal 
        print('Temp ID:')
        print(response_dict['tempID'])  
        #allow user to enter command again
        commands(Client, username)
        
    elif command == "Upload_contact_log":
        message = {
            'messageType': 'Upload_contact_log',
            'username' : username
        }
        #open contactlog and read it and print on terminal
        f = open("z5258346_contactlog.txt", "r")
        contents = f.readlines()
        counter = 0
        for line in contents:
            print(line)
            counter = counter + 1
            if counter == 10:
                break
                
        Client.send(json.dumps(message).encode('utf-8'))
        response = Client.recv(1024)        
        commands(Client, username)

        
    elif command == "logout":
        message = {
            'messageType': command,
        }
        #Client.send(json.dumps(message).encode('utf-8'))
        
        
    else:
        print('Error. Invalid command')
        commands(Client, username)
        
def login():
    i = 0
    Client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    Client.connect((HOST, SERVER_PORT))
    while True:
        username = input('>username: ')
        password = input('>password: ')

        message = {
            'messageType': 'login',
            'username': username,
            'password' : password
        }
        Client.send(json.dumps(message).encode('utf-8'))
        response = Client.recv(1024)
        response_dict = json.loads(response)
        if response_dict['messageType'] == 'welcomemessage' :
            print(response_dict['welcome_message'])
        
        if response_dict['welcome_message'] == "Invalid password. Please try again":
            login()
        

        if response_dict['welcome_message'] == "Invalid Password. Your account has been blocked. Please try again later":
            response = Client.recv(1024)
            login()
            

        if response_dict['welcome_message'] == "Welcome to the BlueTrace simulator":
            #client can receive beacons once logged in
            receivingbeacons = ReceivingBeacons(CLIENT_UDP_PORT)
            receivingbeacons.start()
            commands(Client, username)
            
            
                 
'''
UDP Client: Sending beacons in peripheral state
'''
def SendingBeacons(serverName, serverPort, username):
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    #Get Beacon information from TempIDs.txt
    f = open("tempIDs.txt", "r")
    contents = f.readlines()
    lst = []
    for line in contents:
        line_final = line.replace('\n', ' ')
        lst = line_final.split(' ')
        #print(lst)
        if lst[0] == username:
            TempID = lst[1]
            start_time = lst[2] + " " + lst[3] 
            expiry_time = lst[4] + " " + lst[5] 
            break
                            
                                
    message = {
        'TempID': TempID,
        'start_time': start_time,
        'expiry_time': expiry_time,
        'version_number': 1
    }
    
    print(message['TempID'] + " " + message['start_time'] + " " + message['expiry_time'] + " " + "1")

    clientSocket.sendto(json.dumps(message).encode('utf-8'),(serverName, serverPort))
    
    clientSocket.close()



'''
UDP Server: Receiving beacons in central state
'''
class ReceivingBeacons(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
    
    def run(self):
        UDP_Server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        UDP_Server.bind((HOST, self.port))
        while True:
            '''
            #check for beacons older than 3 minutes
            try:
                with open("z5258346_contactlog.txt", "r") as infile:   
                    lines = infile.readlines()
                    
                    with open("z5258346_contactlog.txt", 'w') as outfile:
                        lst = []
                        for pos, line in enumerate(lines):
                            lst = line.split(' ')
                            #print(lst)
                            exp_time = lst[3] + " " + lst[4][:-1]
                            print(exp_time)
                            exp_time = datetime.datetime.strptime(exp_time, "%m/%d/%Y %H:%M:%S")
                            now = datetime.datetime.now()
                            now_minus_3 = now - datetime.timedelta(minutes = 3)
                            if exp_time < now_minus_3:
                                outfile.write(line)
                
                outfile.close()
            except IOError:
                infile = open("z5258346_contactlog.txt", "w").close()
            '''
            data, addr = UDP_Server.recvfrom(1024)
            data_dict = json.loads(data)
            print("received beacon:")
            print(data_dict['TempID'], data_dict['start_time'], data_dict['expiry_time'], data_dict['version_number'])
            
            #Print the current system time
            current_time = datetime.datetime.now()
            current_time = current_time.strftime("%m/%d/%Y %H:%M:%S")
            print(f"Current system time is: {current_time}")
            
            #Check if system time is between data_dict[start_time] and data_dict[expiry_time]
            current_time = datetime.datetime.strptime(current_time, "%m/%d/%Y %H:%M:%S")
            start_time = datetime.datetime.strptime(data_dict['start_time'], "%m/%d/%Y %H:%M:%S")
            expiry_time = datetime.datetime.strptime(data_dict['expiry_time'], "%m/%d/%Y %H:%M:%S")
            if current_time < expiry_time and current_time > start_time:
                #Beacon is valid
                print("The Beacon is valid.")
                filename = 'z5258346_contactlog.txt'
                local_log = open(filename,'a+')
                local_log.write(data_dict['TempID'] + " " + data_dict['start_time'] + " " + data_dict['expiry_time'] + '\n')
                local_log.close()
            else:
                print("The Beacon is invalid.")
            
                            
login()
                
