import threading
import socket
import time
from threading import Lock

host = '127.0.0.1' # local host
port = 3005

# Create socket and listen on specified IP/Port
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host,port))
server.listen()

class Client:
    # Contructor to create client variable
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        self.name = None
    
    # Method to set the name of a client 
    def set_name(self, name):
        self.name = name

    # Method to send message, handles encoding utf-8
    def send_message(self, message):
        self.connection.send(bytes(str(message), 'utf-8'))

    # Method to recieve messages from client, recieves max 1024 bytes and handles decoding
    def recieve_message(self):
        return self.connection.recv(1024).decode('utf-8')

global riders, drivers, requested

riders = [] # holds riders waiting for a ride
riders_lock = Lock()
drivers = [] # holds drivers waiting to take a ride
drivers_lock = Lock()
requested = {} # dictionary that holds requested riders and they're requested ride distance
requested_lock = Lock()
# dictionary to keep track of riders in chat, same format as requested
chatroom = {}
# used when a driver returns from a chatroom to resend the current riders
returning_chatroom = False

def find_rider(name):
    for rider in riders:
        if rider.name == name:
            return rider
    return None

def handle_rider(rider):
    '''
    Method that is called when a client chooses to be a rider, asks for the distance and eta of the ride and 
    stores this in the requested dictionary. The rider then waits to be placed in a chatroom with a driver who 
    is interested in the trip.
    '''

    # Prompt rider for their destination(length)
    rider.send_message('What is the distance in miles for your trip? (In miles)')
    distance = rider.recieve_message()

    # Prompt rider for how long this should take
    rider.send_message('How long do you think this will take in minutes')
    eta = rider.recieve_message()

    requested[rider.name] = distance + ' miles and ' + eta + ' minutes'

def handle_driver(driver):
    global returning_chatroom
    '''
    Method called when a client chooses to be a driver, greets them with there name, then iterates
    over the requested dictionary letting the client know the current rides being requested from riders.
    Method then waits for input to initiate a chatroom with a driver/client pair.
    '''
    previous_names = []  # Set to keep track of the previous keys in the dictionary
    driver.send_message('Hello driver ' + driver.name + '\n')

    if len(requested) == 0:
        driver.send_message('No avaliable rides, we will inform you of any requests')

    while True:
        # set to the key in requested dictionary
        current_names = list(requested.keys()) 
        # check if there are changes(new rider added to dictionary or rider leaves)


        if (current_names != previous_names) or returning_chatroom: 
            returning_chatroom = False
            # check if requested is not empty
            if requested: 
                # set previous_names to current
                previous_names = current_names[:]

                driver.send_message('The current pending trips are: \n') 
                # iterate over requested dictionary 
                if len(requested) == 0:
                    driver.send_message('No avaliable rides, waiting for riders...')
                else:
                    for key, value in requested.items(): 
                        driver.send_message(f'{key}: {value}\n')

                while True:
                    driver.send_message('To take one of these rides, simply enter the rider name and you will be placed in a chat room, if you dont want to take a ride enter no.')    

                    # check if a new recent addition to riders dicitonary, break loop and prompt again   
                    if list(requested.keys()) != previous_names:
                        break
                    
                    rider_name = driver.recieve_message() 
                    if rider_name in requested: 
                        selected_rider = find_rider(rider_name)
                        driver.send_message('What port number do you wish to have your chatroom on?')
                        chatroom_port = driver.recieve_message()

                        # Give rider_server a second to initiate
                        time.sleep(1)   
                        init_chatroom(selected_rider, driver, chatroom_port)
                        break
                    elif rider_name.lower() == 'no':
                        driver.send_message('Sorry we could not find a suitable ride\n')
                        break
                    else:
                        print('input: ' + rider_name)
                        driver.send_message('Rider not found\n')
                
                if driver not in drivers:
                    break

        # Sleep for a short period to prevent extreme overload
        time.sleep(1)  

def init_chatroom(rider, driver, port):
    global drivers, riders, chatroom, returning_chatroom
    if rider == None:
        driver.send_message('Unexpected error finding your rider, do not worry you are being returned to the main lobby to find another ride.')
        return

    rider.send_message('Chatroom information:')
    time.sleep(.1)
    rider.send_message('127.0.0.1')  # Host address
    time.sleep(.1)
    rider.send_message(port)
    
    chatroom[rider.name] = requested[rider.name]
    del requested[rider.name]

    chatroom_result = driver.recieve_message()

    if chatroom_result == 'accept':
        print(f'{driver.name} is giving {rider.name} a ride')

        # Close connections
        rider.connection.close()
        driver.connection.close()

        # Remove from the lists
        with riders_lock:
            riders.remove(rider)
        with drivers_lock:
            drivers.remove(driver)

        del chatroom[rider.name]

    elif chatroom_result == 'decline':
        requested[rider.name] = chatroom[rider.name]
        del chatroom[rider.name]
        returning_chatroom = True


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
            break

        elif client_role.lower() == 'rider':
            print('Client is choosing to be a rider')
            with riders_lock:
                riders.append(client_obj)
            break


        else:
            print('Invalid choice')
            client_obj.send_message('Invalid choice please enter driver or rider')

    if client_role.lower() == 'driver':
        handle_driver(client_obj)

    if client_role.lower() == 'rider':
        handle_rider(client_obj)

while True:
    print('Server running...')
    client, address = server.accept()

    client_obj = Client(client, address)

    thread = threading.Thread(target = main, args = (client_obj,))
    thread.start()

    shutdown = input('shutdown server y/n')
    if shutdown == 'y':
        # This needs some fixing 
        server.close()
        break
  
