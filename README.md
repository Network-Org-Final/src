# Ridelink
A hybrid peer to peer rideshare system that utilizes TCP socket connection and multithreading. Clients connect to a main server to choose roles(rider or driver). 
Once inside the main server, riders declare the distance and eta of their rides and this information is sent to the server and distributed to drivers
where drivers can engage interest in riders rides where the main server then exchanges the IP and port # to the driver/rider pair. Once this exchange occurs
another TCP connection is made this time between two clients with the idea of peer-to-peer where clients negotiate prices on the rides, if they come to 
an agreement both clients leave the chatroom and main server, if they do not come to an agreement they simply return to the main server.

# To run
1. Clone the repository
2. Run the server.py
3. Run client.py

Currently the project is set up to run locally on port 3007, to run this over the net there are a few setup changes 
1. on server.py change line 8 (host) to your server IP by running ipconfig on windows or ifconfig on macos
2. on client.py change line 29 (host) to your server IP this HAS to be the same IP as you changed to in step 1 on server.py
    a. Optional: change the port numbers on line 26 on client.py and line 7 if you reach an error that address in use but port 3007 should not be in use
3. on cient.py change line 230 to your specific client machine IP by runnning ipconfig on windows or ifconfig on macos, this ip is used for the chatroom and is exchanged through 
    the main server.

Demo: https://www.youtube.com/watch?v=LgZREpFJqrk&t=8s
