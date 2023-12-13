import socket
import threading
import random
import time
import sys

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

# main server connection
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
Port = 3007
Host = '127.0.0.1'
server.connect((Host, Port))

# This will control the thread to send messages to main server, turned off when clients join chatroom
main_server_connection = True
# This will control if the clients come to an agreement on a price and closes the connection with main server
agreed = False
# This will handle state if the client is a driver
driver = False
# Handles sending messages, only will become false when a chatroom agreement
running = True

# send messages to main server or chatroom, thread running to be able to freely send responses as messages come in
def send_messages():
    global main_server_connection, server, chatroom_server, running, agreed
    while running:
        try:
            if not driver:
                response = input()
                if main_server_connection:
                    # Send to the main server
                    if server:
                        server.send(bytes(response, 'utf-8'))
                    # Send to the chatroom server
                elif chatroom_server:
                    chatroom_server.send(bytes(response, 'utf-8'))
                '''
                Because of how we handle sending messages through a separate thread, when a chatroom starts the driver is required to input twice 
                the first input here on line 37 then the thread understands that the driver is in fact a driver(line 36) the program then reaches 
                the inputs inside negotiate(). Since input is a blocking method there was no way around this, to fix that we added a wait time
                so the client can recieve aknowledgement from the main server that a chatroom is being created and the state is fixed. This was especially
                needed when we where testing on multiple devices going over the internet as opposed to local host
                '''
                time.sleep(1)
        except Exception as e:
            break
# create chatroom server used by drivers
def create_chatroom(chat_port, chat_ip):
    global main_server_connection, driver
    host = chat_ip
    chatroom_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    chatroom_server.bind((host,int(chat_port)))

    # allow 10 seconds until server times out
    chatroom_server.settimeout(10)

    # allow a single connection at a time
    chatroom_server.listen(1) 

    print(f'Chatroom created on port {chat_port}')
    main_server_connection = False
    driver = True

    while True:
        try:
            client, address = chatroom_server.accept()
            client_obj = Client(client, address)
            # only want one client
            print('Rider joined chatroom waiting for message...')
            break
        except socket.timeout:
            print('Error with client joining, returning to main lobby')
            main_server_connection = True
            driver = False
            return

    negotiate(chatroom_server, client_obj)

# join chatroom server used by riders given ip and port from driver
def join_chatroom(IP, PORT):
    global main_server_connection, chatroom_server
    chatroom_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    chatroom_server.connect((IP, PORT))
    print(f"Joined chatroom")
    main_server_connection = False
    return chatroom_server

# leave chatroom server used by clients, either allows clients to return to main server or if they agreed on a price close connections
def leave_chatroom(chatroom_server):
    global main_server_connection, agreed, driver, running

    if agreed:
        chatroom_server.close()
        server.send(bytes(str('accept'), 'utf-8'))
        running = False
        server.close()
    else:
        chatroom_server.close()
        chatroom_server = None
        print("Left the chatroom.")
        driver = False
        main_server_connection = True
        server.send(bytes(str('decline'), 'utf-8'))

# cycles through open ports to find to create chatroom
def get_open_port():
    # runs through random number 1024 - 65535 and checks if the port is in use
    not_valid = True
    while not_valid:
        random_port = random.randint(1024, 65535)
        # use the port number to check if the connection is possible or returns the error that the socket is in use
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            not_valid = s.connect_ex(('localhost', random_port)) == 0
    
    return str(random_port)

# negotiate price between driver and rider
def negotiate(server, client):
    global agreed, driver_input, thread
    current_price = 0.0
    # variable to ensure driver gets input on price as well, rider cannot just accept a initial price of 0
    turns = False

    while True:
        client.send_message(f'The current price is {current_price}\n1. Enter a new price\n2. Agree on this price\n3. Leave chatroom and find new ride\n')
        response = client.recieve_message()
        match response:
            case '1':
                while True:
                    client.send_message('Enter your intended price:')
                    response = client.recieve_message()
                    try:
                        if float(response) > 0:
                            client.send_message('Price request sent, waiting for response from driver...\n')
                            current_price = float(response)
                            break
                        else:
                            client.send_message('Price must be positive !') 
                    except ValueError:
                        client.send_message('Invalid input please enter a number.')
            case '2':
                if turns:
                    client.send_message('Price agreed, your driver will be on his way shortly!')
                    agreed = True
                    print('Rider agrees! set your destination for the rider.')
                    leave_chatroom(server)
                    break
                else:
                    client.send_message('Cannot agree yet, driver must give input on price')
            case '3':
                client.send_message('Sorry you could not come to an agreement, returning to main lobby to find new driver.')
                print('Rider is no longer interested returning you to main lobby.')
                leave_chatroom(server)
                break
            case _:
                client.send_message('Invalid input')

        print(f'The client has chosen a price of {current_price}\n1. Enter a new price\n2. Agree on this price\n3. Close connection and find new rider\n')
        
        driver_response = input()

        match driver_response:
                case '1':
                    while True:
                        response = input('Enter your intended price:')
                        try:
                            if float(response) > 0:
                                current_price = float(response)
                                print('Price request sent, waiting for response from rider...\n')
                                turns = True
                                break
                            else:
                                print('Price must be positive')
                        except ValueError:
                            print('Invalid input please enter a number.')
                case '2':
                    client.send_message(f'Price of {current_price} agreed, your driver will be on his way shortly!')
                    agreed = True
                    print('Set your destination for the rider.')
                    leave_chatroom(server)
                    break
                case '3':
                    print('Sorry you could not come to an agreement, returning to main lobby to find new rider.')
                    client.send_message('Driver is no longer interested returning you to main lobby.')
                    thread = threading.Thread(target = send_messages)
                    leave_chatroom(server)
                    break

# Start a separate thread for sending messages
thread = threading.Thread(target=send_messages)
# daemon threads end when the main process ends without waiting for actual thread to finish 
thread.daemon = True
thread.start()

# main loop running 
while True:
    try:
        # Chatroom negotiation occured and clients came to an agreement, leave main server
        if agreed: 
            break 
        # If there is not a current chatroom, listen for main server messages
        if main_server_connection:
            msg = server.recv(1024)
            if not msg:
                print("Disconnected from server")
                break
            message = msg.decode('utf-8')
            # check for chatroom prompts from main server
            match message:
                # prompt for driver 
                case "What port number do you wish to have your chatroom on?":
                    driver = True
                    chatroom_ip = '127.0.0.1'
                    chatroom_port = get_open_port()
                    server.send(bytes(chatroom_ip, 'utf-8'))
                    time.sleep(.1)
                    server.send(bytes(chatroom_port, 'utf-8'))
                    create_chatroom(chatroom_port, chatroom_ip)
                # prompt for rider
                case "Chatroom information:":
                    chatroom_ip = server.recv(1024).decode('utf-8')
                    chatroom_port = int(server.recv(1024).decode('utf-8'))
                    print('Joining chatroom...')
                    chatroom_server = join_chatroom(chatroom_ip, chatroom_port)
                case "Server shutdown":
                    print('Main server shutting down, goodbye...')
                    break
                case _:
                    # if no relating messages to chatroom, print out message on client side
                    print(message)
        if not main_server_connection and not driver:
            msg = chatroom_server.recv(1024)
            message = msg.decode('utf-8')
            print(message)
            
            # Specific messages from servers to handle specific actions 
            if message == 'Sorry you could not come to an agreement, returning to main lobby to find new driver.' or message == 'Driver is no longer interested returning you to main lobby.':
                print('closing...')
                chatroom_server.close()
                main_server_connection = True
            elif 'your driver will be on his way shortly!' in message:
                server.close()
                chatroom_server.close()
                break


    except ConnectionResetError:
        print("Connection was lost with the server.")
        break

# close connection and end process
server.close()
sys.exit(0)


if chatroom_server:
    chatroom_server.close()
# Thread will still run and await input so we just terminate program.
