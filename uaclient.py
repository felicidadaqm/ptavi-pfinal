#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
from datetime import datetime, timedelta
import os.path
import xml.etree.ElementTree as ET

class UAClient:
    xml_dicc = {}

    def config(self):
    # SACO LA CONFIGURACIÓN DE XML
        tree = ET.parse('ua1.xml')
        root = tree.getroot()
        for branch in root:
            self.xml_dicc[str(branch.tag)] = branch.attrib
        print(self.xml_dicc)
        return self.xml_dicc

    def building_sip(self):
    # SACO LO QUE NECESITO, FALTA MONTAR SIP
        self.config()

        username = str(self.xml_dicc['account']['username'])
        server_rtp = self.xml_dicc['rtpaudio']['puerto']
        proxy_port = self.xml_dicc['regproxy']['puerto']
        proxy_ip = self.xml_dicc['regproxy']['ip']
        print("----------")
        print(proxy_port + " " + username)


cliente = UAClient()
prueba = cliente.building_sip()

if len(sys.argv) != 3:
    sys.exit("Usage: client.py metodo receptor@IPreceptor:puertoSIP")


# CAMBIAR ESTO, DATOS EN XML
try:
    method = sys.argv[1]
    receiver = sys.argv[2][0:sys.argv[2].find('@')]
    IP = sys.argv[2][sys.argv[2].find('@')+1:sys.argv[2].find(':')]
    port = int(sys.argv[2][sys.argv[2].rfind(':')+1::])
except (IndexError, ValueError, NameError):
    sys.exit("Usage: python3 client.py method receiver@IP:SIPport")

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP, port))


    message = method + " sip:" + receiver + "@" + IP + " SIP/2.0"
    print("Enviando: " + message)
    my_socket.send(bytes(message, 'utf-8') + b'\r\n')
    data = my_socket.recv(1024)
    format_date = '%Y%m%d%H%M%S'
    time = datetime.now()
    date = time.strftime(format_date)
    print(date)

    print('Recibido -- ', data.decode('utf-8'))
    print("Terminando socket...")

    if data.decode('utf-8') != '':
        received = data.decode('utf-8')
        print(received)
        if 'Trying' in received and 'Ringing' in received and 'OK' in received:
            message2 = 'ACK' + " sip:" + receiver + "@" + IP + " SIP/2.0"
            print("Enviando " + message2)
            my_socket.send(bytes(message2, 'utf-8') + b'\r\n')

    if os.path.exists('log.txt'):
        file = open('log.txt', 'w')
        
        EVENT = date + " Starting..." + "\r\n"
        file.write(EVENT)
        print(EVENT)
        if message != '\r\n':
            EVENT = date + " Sent to " + str(IP) + ":" + str(port) + ": " + method
            EVENT += " sip:" + receiver
            file.write(EVENT)
            print(EVENT)
        # TERMINAR BUCLE

print("Fin.")
