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
    message = ''

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
        rtp_port = self.xml_dicc['rtpaudio']['puerto']
        proxy_port = self.xml_dicc['regproxy']['puerto']
        proxy_ip = self.xml_dicc['regproxy']['ip']
        server_ip = self.xml_dicc['uaserver']['ip']
        server_port = self.xml_dicc['uaserver']['puerto']
        print("----------")
        print(proxy_port + " " + username)
     
        if sys.argv[3] == 'REGISTER':
            expires = sys.argv[4]
            message = 'REGISTER sip:' + username + ':' + server_port + ' SIP/2.0\r\n'
            message += 'Expires: ' + expires
        print(self.message)
        return self.message

cliente = UAClient()
dicc = cliente.config()
prueba = cliente.building_sip()
print(prueba)

proxy_ip = dicc['regproxy']['ip']
proxy_port = int(dicc['regproxy']['puerto'])

if len(sys.argv) != 4:
    sys.exit("Usage: python uaclient.py config metodo opcion")

method = sys.argv[2]
print(method)

#FALTA CAPTURAR ERROR DE NO PUERTO CONECTADO
try:
    if method == 'REGISTER':
        expires = sys.argv[3]
        print(expires)
    elif method =='INVITE':
        invited = sys.argv[3]
    else:
        sys.exit("Método inválido")
except (IndexError, ValueError, NameError):
    sys.exit("Usage: python uaclient.py config metodo opcion")

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((proxy_ip, proxy_port))

    message = 'ay'
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
            EVENT = date + " Sent to " + "CAMBIAR" + ":" + "CAMBIAR" + ": " + method
            EVENT += " sip:" + "CAMBIAR"
            file.write(EVENT)
            print(EVENT)
        # TERMINAR BUCLE

print("Fin.")
