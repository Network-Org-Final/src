import threading
import socket
import time
from threading import Lock
host = '127.0.0.1' # local host
port = 1239

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host,port))
server.listen()

class Client:
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        self.name = None
    
    def set_name(self, name):
        self.name = name

    def send_message(self, message):
        self.connection.send(bytes(str(message), 'utf-8'))

    def recieve_message(self):
        return self.connection.recv(1024).decode('utf-8')

global riders, drivers, requested

riders = [] # holds riders waiting for a ride
riders_lock = Lock()
drivers = [] # holds drivers waiting to take a ride
drivers_lock = Lock()
requested = {} # dictionary that holds requested riders and they're requested ride distance
requested_lock = Lock()

def get_riders():
    with riders_lock:
        for rider in riders:
            print(rider)

def find_rider(name):
    with riders_lock:
        for rider in riders:
            if rider.name == name:
                return rider
    print('Rider not found')

def remove_rider(name):
    with riders_lock:
        for rider in riders:
            if rider.name == name:
                riders.remove(rider)

def send_message_to_driver(message):
    for driver in drivers:
        print(driver.name)
        print(driver.connection)
        driver.send_message(message)
        
def find_driver(name):
    with drivers_lock:
        for driver in drivers:
            if driver.name == name:
                return driver
    print('driver not found')

def remove_driver(name):
    with drivers_lock:
        for driver in drivers:
            if driver.name == name:
                drivers.remove(driver)
# TODO:
# def connect_clients(driver, rider):
    # Get IP of driver & rider

    # Exchange IP & Port to each
    
    # Run client code to connect

    # If they accept a ride recieve word back and remove rider/driver from list

def handle_rider(rider):
    # Prompt rider for their destination(length)
    rider.send_message('What is the distance in miles for your trip? (In miles)')
    distance = rider.recieve_message()

    # Prompt rider for how long this should take
    rider.send_message('How long do you think this will take (HH:MM)')
    eta = rider.recieve_message()

    requested[rider.name] = distance + ' miles and ' + eta + ' minutes'

def handle_driver(driver):
    previous_keys = []  # Set to keep track of the previous keys in the dictionary
    driver.send_message('Hello driver ' + driver.name + '\n')

    while True:
        current_keys = list(requested.keys())
        if current_keys != previous_keys:
            if requested:
                driver.send_message('The current pending trips are: \n')
                for key, value in requested.items():
                    driver.send_message(f'{key}: {value}\n')
                
                driver.send_message('To take one of these rides, simply enter the rider name and you will be placed in a chat room.')
                rider_name = driver.recieve_message()

                if rider_name in requested:
                    
            previous_keys = current_keys[:]

        time.sleep(1)  # Sleep for a short period to prevent constant CPU usage
        
    # Recieve requests from riders
    # Get to choose if they want to take a drive of the distance
    # If yes run connect_clients()

# def send_to_drivers(requested):
    # Iterates over requested dictionary
    # sends a formatted message with the current requests allowing drivers to choose

def main(client_obj):
    while True:
        client_obj.send_message('What is your name')
        client_obj.name = client_obj.recieve_message()

        client_obj.send_message('Are you a driver or a rider?')
        client_role = client_obj.recieve_message()

        if client_role.lower() == 'driver':
            print('Client is choosing to be a driver')
            with drivers_lock:
                drivers.append(client_obj)
                print('driver added')
            break

        elif client_role.lower() == 'rider':
            print('Client is choosing to be a rider')
            with riders_lock:
                riders.append(client_obj)
                print('rider added')
            break


        else:
            print('Invalid choice')
            client_obj.send_message('Invalid choice please enter driver or rider')

    if client_role.lower() == 'driver':
        handle_driver(client_obj)

    if client_role.lower() == 'rider':
        handle_rider(client_obj)

# client connects to server

# server sends messages asking client if they're a driver/rider, then their name

# server 

while True:
    print('Server running...')
    client, address = server.accept()

    client_obj = Client(client, address)
    print('Connection established with ', client_obj.address)

    thread = threading.Thread(target = main, args = (client_obj,))
    thread.start()

    shutdown = input('shutdown server y/n')
    if shutdown == 'y':
        # This needs some fixing 
        server.close()
        break
 
