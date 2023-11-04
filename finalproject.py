# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 16:25:02 2023

@author: georg
"""
import socket


Chatbox_Client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
Port = 1234
Host = socket.gethostname()
Star_Rating=3
Distance =input("How far away is your destination?")
Chatbox_Client.connect((Host,Port))
Chatbox_Client.send(bytes(Distance,'utf-8'))
while True:
   #Takes input from client
   print("If you would like to cancel the ride, text the word cancel.")
   text=input("input text")
   #Sends client input
   Chatbox_Client.send(bytes(text,'utf-8'))
   print(Chatbox_Client.recv(50))
   #Breaks out of while look if text is bye
   if text=="cancel":
        break
Chatbox_Client.close()
