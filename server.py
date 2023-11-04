import threading
import socket

host = '127.0.0.1' # local host
port = 59000

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
        self.connection.send(message.encode('utf-8'))

    def recieve_message(self):
        return self.connection.recv(1024).decode('utf-8')

riders = [] # holds riders waiting for a ride
drivers = [] # holds drivers waiting to take a ride
requested = {} # dictionary that holds requested riders and they're requested ride distance

def get_riders():
    for rider in riders:
        print(rider)

def find_rider(name):
    for rider in riders:
        if rider.name == name:
            return rider
    print('Rider not found')

def remove_rider(name):
    for rider in riders:
        if rider.name == name:
            riders.remove(rider)
def get_drivers():
    for driver in drivers:
        print(driver)
        
def find_driver(name):
    for driver in drivers:
        if driver.name == name:
            return driver
    print('driver not found')

def remove_driver(name):
    for driver in drivers:
        if driver.name == name:
            drivers.remove(driver)
# TODO:
def connect_clients(driver, rider):
    # Get IP of driver & rider

    # Exchange IP & Port to each
    
    # Run client code to connect

    # If they accept a ride recieve word back and remove rider/driver from list

def handle_rider(rider):
    # Prompt rider for their destination(length)
    # Prompt rider for how long this should take
    # Send message to all drivers, maybe push this to a requested array so drivers who join after can see this 
    # Wait 30 seconds or something if no response send message
    # If a driver wants to take it run connect_clients() for them to enter a chatroom and negotiatie

def handle_driver(driver):
    # Recieve requests from riders
    # Get to choose if they want to take a drive of the distance
    # If yes run connect_clients()

def send_to_drivers(requested):
    # Iterates over requested dictionary
    # sends a formatted message with the current requests allowing drivers to choose

def main():
    while True:
        print('Server running...')
        client, address = server.accept()

        client_obj = Client(client_socket, address)
        print('Connection established with ', client_obj.address)
        
        while True:
            client_obj.send('Are you a driver or a rider?'.encode('utf-8'))
            client_role = client_obj.recieve_message()

            if client_role.lower() == 'driver':
                print('Client is choosing to be a driver')
                drivers.append(client_obj)
                break

            elif client_role.lower() == 'rider':
                print('Client is choosing to be a rider')
                riders.append(client_obj)
                break

            else:
                print('Invalid choice')
                client_obj.send_message('Invalid choice please enter driver or rider')

        if client_role.lower() == 'driver':
            thread = threading.Thread(target = handle_driver, args=(client_obj,))
            thread.start()

        if client_role.lower() == 'rider':
            thread = threading.Thread(target = handle_rider, args=(client_obj,))
            thread.start()

    # client connects to server

    # server sends messages asking client if they're a driver/rider, then their name

    # server 
