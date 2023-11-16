import socket
import threading

def send_messages():
    while True:
        response = input()
        server.send(bytes(response, 'utf-8'))

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
Port = 12342
Host = socket.gethostname()
server.connect((Host, Port))

# Start a separate thread for sending messages
thread = threading.Thread(target=send_messages)
thread.start()

while True:
    # Continuously listen for messages from the server
    try:
        msg = server.recv(1024)
        if not msg:
            print("Disconnected from server")
            break
        message = msg.decode('utf-8')
        print(message)
    except ConnectionResetError:
        print("Connection was lost with the server.")
        break

server.close()
