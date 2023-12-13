import threading
import socket
import time
from threading import Lock
import select
import sys

host = '127.0.0.1' # local host
port = 3007

# Create socket and listen on specified IP/Port
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host,port))
server.listen()
print('Server running...')

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
        try:
            self.connection.send(bytes(str(message), 'utf-8'))
        except:
            pass

    # Method to recieve messages from client, recieves max 1024 bytes and handles decoding
    def recieve_message(self):
        try:
            return self.connection.recv(1024).decode('utf-8')
        except:
            pass


# keeps track of clients on server, used to send shutdown message
clients = []
# used to check for duplicate names of riders 
rider_names = []
# holds rider of type Client to send/recieve messages waiting for ride
riders = [] 
# holds drivers of type Client to send/recieve messages 
drivers = [] 
# dictionary where key is rider name and value is there ride distance 
requested = {} 
# dictionary to keep track of riders in chatroom, same format as requested
chatroom = {}
# used when a driver returns from a chatroom to resend the current riders data from requested
returning_chatroom = False
# used to prevent race conditions since we are using multithreading
lock = Lock()
# used to break out of loop if a chatroom is accepted on driver side
accept = False
# used to break out of main loop if shutdown command is entered
shutdown = False

# Find riders in the rider list and return the name given the rider object of type client
def find_rider(name):
    for rider in riders:
        if rider.name == name:
            return rider
    return None

# Process after clients input they are a rider, prompts for distance and eta
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
    rider.send_message('Your ride has been requested, a driver will be reaching out soon.')

# Process after clients input they are a driver, listens for new riders requesting rides and prompts to initaite chatroom
def handle_driver(driver):
    global returning_chatroom
    driver.send_message('Hello driver ' + driver.name + '\n')
    # get current list of rider names in requested
    previous_names = list(requested.keys())

    # prompt drivers with requested rides if they are initially joining the platform
    first_time = True

    while True:
        # Check for new requests and compare to previous 
        current_names = list(requested.keys())
        if (current_names != previous_names) or returning_chatroom or first_time:
            
            first_time = False
            returning_chatroom = False
            
            previous_names = current_names[:]

            if not requested:
                driver.send_message('No available rides, we will inform you of any requests\n')
            else:
                driver.send_message('The current pending trips are:\n')
                for key, value in requested.items():
                    driver.send_message(f'{key}: {value}\n')


        '''
        check if driver sent a message, chatGPT helped us with this piece as recieve_message is a blocking method so if we just had recieve_message
        and a new rider joined, the server would have to recieve a response from the driver before showing the new rides which is not a good user experience 
        if there intent is to wait for a ride of their choice but they can not see updates without manual input, ready_to_read listens for messages but allows other
        processes to run, in our case listening for new additions to the requested dictionary and prompting drivers with new rides.
        '''
        ready_to_read, _, _ = select.select([driver.connection], [], [], 1)
        if ready_to_read:
            rider_name = driver.recieve_message()

            # validate input
            if rider_name in requested: 
                # get the rider object of type client to be able to send messages to start chatroom
                selected_rider = find_rider(rider_name)
                driver.send_message('What port number do you wish to have your chatroom on?')
                chatroom_ip = driver.recieve_message()
                # error in development where sometimes these two messages would be concatenated so give a slight pause between sends
                time.sleep(0.1)
                chatroom_port = driver.recieve_message()

                # Give driver a second to set up server after they send the IP and port
                time.sleep(1)   

                # init chatroom by sending rider IP and port number to have them join
                init_chatroom(selected_rider, driver, chatroom_ip, chatroom_port)

                # response from chatroom indicates they accept a ride, break out of this process
                if accept:
                    break
            
            # driver would not like to take any riders
            elif rider_name.lower() == 'no':
                driver.send_message('Sorry we could not find a suitable ride\n')
                break
            else:
                driver.send_message('Rider not found\n')

        # Sleep for a short period to prevent extreme overhead
        time.sleep(1) 

# Sends rider the chatroom information provided by driver for rider to join
def init_chatroom(rider, driver, ip, port):
    global drivers, riders, chatroom, returning_chatroom, accept, clients
    if rider == None:
        driver.send_message('Unexpected error finding your rider, do not worry you are being returned to the main lobby to find another ride.')
        return
    try:
        # send information to rider, slight pause between messages so messages are handled correctly and not concatenated
        rider.send_message('Chatroom information:')
        time.sleep(.1)
        rider.send_message(ip)  
        time.sleep(.1)
        rider.send_message(port)
    except Exception as e:
        driver.send_message('Unexpected network error, returning you to main lobby.')
        return 

    # set chatroom to have rider inside, remove requested so drivers cannot attempt to take a ride that is currently in a chatroom(in negotiation)
    chatroom[rider.name] = requested[rider.name]
    print(f'value added to chatroom for {rider.name}')
    del requested[rider.name]

    # await response from driver on the result of the chatroom
    chatroom_result = driver.recieve_message()

    if chatroom_result == 'accept':
        print(f'{driver.name} is giving {rider.name} a ride')

        # Close connections
        rider.connection.close()
        driver.connection.close()

        # Remove from the lists
        with lock:
            riders.remove(rider)
            rider_names.remove(rider.name)
            drivers.remove(driver)
            clients.remove(driver)
            clients.remove(rider)

        # Safely delete from chatroom
        if rider.name in chatroom:
            del chatroom[rider.name]
            print(f'Removed {rider.name} from chatroom')
        else:
            print(f'Warning: {rider.name} not found in chatroom for deletion')

        # to break out of loop for drivers in handle_driver
        accept = True

    # clients where not able to come to a accepted price, return rider back to requested dictionary and set driver returning_chatroom to true so they are prompted with current rides
    elif chatroom_result == 'decline':
        requested[rider.name] = chatroom[rider.name]
        if rider.name in chatroom:
            del chatroom[rider.name]
            print(f'Removed {rider.name} from chatroom after decline')
        else:
            print(f'Warning: {rider.name} not found in chatroom for deletion after decline')
        returning_chatroom = True

# Thread awaiting input from server side to send messages to clients so they close connection and end the server
def kill_server():
    global shutdown
    while True:
        shutdown = input('shutdown server y/n\n')
        if shutdown == 'y':
            print('Server shutting down')
            shutdown = True
            for client in clients:
                client.send_message("Server shutdown")
            # close servers
            server.close()
            time.sleep(.2)
            # end process
            sys.exit(0)

# main initial process that is ran, prompts client for rider/driver
def main(client_obj):
    while True:
        
        client_obj.send_message('Are you a driver or a rider?')
        client_role = client_obj.recieve_message()

        if client_role.lower() == 'driver':
            with lock:
                client_obj.send_message('What is your name')
                client_obj.name = client_obj.recieve_message()
                drivers.append(client_obj)
            break

        elif client_role.lower() == 'rider':
            while True:
                client_obj.send_message('What is your name')
                client_obj.name = client_obj.recieve_message()
                # riders will eventually be placed into a requested queue and the name is the key, cannot be duplicate
                if client_obj.name in rider_names:
                    client_obj.send_message('Sorry name is in use please select another.')
                else:
                    with lock:
                        riders.append(client_obj)
                        rider_names.append(client_obj.name)
                    break
            # break out of main loop
            break

        else:
            client_obj.send_message('Invalid choice please enter driver or rider')

    if client_role.lower() == 'driver':
        handle_driver(client_obj)

    if client_role.lower() == 'rider':
        handle_rider(client_obj)

# kill thread 
shutdown_thread = threading.Thread(target = kill_server)
shutdown_thread.start()

# main listening loop
while not shutdown:
    try:
        client, address = server.accept()
        client_obj = Client(client, address)
        clients.append(client_obj)
        thread = threading.Thread(target = main, args = (client_obj,))
        thread.daemon = True
        thread.start()
    except:
        pass

    
