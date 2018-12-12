#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
from datetime import datetime, timedelta
import os.path
import os
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
        self.config()

        username = str(self.xml_dicc['account']['username'])
        rtp_port = self.xml_dicc['rtpaudio']['puerto']
        my_ip = self.xml_dicc['uaserver']['ip']
        my_port = self.xml_dicc['uaserver']['puerto']
     
        method = sys.argv[2]
        option = sys.argv[3]
        
        if method == 'REGISTER':
            self.message = method + ' sip:' + username + ':' + my_port + ' SIP/2.0\r\n'
            self.message += 'Expires: ' + option
        elif method == 'INVITE':
            self.message = method + ' sip:' + option + ' SIP/2.0\r\n'
            self.message += 'Content-Type: application/sdp\r\n' + '\r\n'
            self.message += 'v=0\r\n' + 'o=' + username + ' ' + my_ip + '\r\n'
            self.message += 's=misesion\r\n' + 't=0\r\n' + 'm=audio ' + rtp_port + ' RTP\r\n'
        elif method == 'BYE':
            self.message = method + ' sip:' + option + ' SIP/2.0\r\n'
        else:
            self.message = method + ' sip:' + option + ' SIP/2.0\r\n'
            print("Petición inválida")
        print(self.message)
        return self.message

    def writing_log(self):
        self.building_sip()

        format_date = '%Y%m%d%H%M%S'
        time = datetime.now()
        date = time.strftime(format_date)

        file_rute = self.xml_dicc['log']['path']

        username = str(self.xml_dicc['account']['username'])
        rtp_port = self.xml_dicc['rtpaudio']['puerto']
        proxy_ip = self.xml_dicc['regproxy']['ip']
        proxy_port = self.xml_dicc['regproxy']['puerto']
        my_port = self.xml_dicc['uaserver']['puerto']

        if os.path.exists(file_rute):
            file = open(file_rute, 'a')
        else:
            file = open(file_rute, 'w')

        EVENT = date + " Starting..." + "\r"
        file.write(EVENT)
        print(EVENT)
        if sip_message != '\r\n':
            if method == 'REGISTER':
                EVENT = date + " Sent to " + proxy_ip + ":" + proxy_port + ": " + method
                EVENT += " sip:" + username + ":" + my_port + " SIP/2.0\r"
                file.write(EVENT)
                print(EVENT)
            elif method == 'INVITE':
                EVENT = date + " Sent to " + proxy_ip + ":" + proxy_port + ":" + method
                EVENT += " " + option + " SIP/2.0\r"
                file.write(EVENT)
            elif method == 'BYE':
                EVENT = date + " Sent to" + proxy_ip + ":" + proxy_port + ":" + method + "\r"
                file.write(EVENT)
        # TERMINAR BUCLE CON LO RECIBIDO

if __name__ == "__main__":
    try:
        method = sys.argv[2]
        option = sys.argv[3]
    except (IndexError, ValueError, NameError):
        sys.exit("Usage: python uaclient.py config metodo opcion")

    if len(sys.argv) != 4:
        sys.exit("Usage: python uaclient.py config metodo opcion")

    client = UAClient()
    dicc = client.config()
    sip_message = client.building_sip()
    log = client.writing_log()

    proxy_ip = dicc['regproxy']['ip']
    proxy_port = int(dicc['regproxy']['puerto'])

#FALTA CAPTURAR ERROR DE NO PUERTO CONECTADO

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((proxy_ip, proxy_port))

        print("Enviando: " + sip_message)
        my_socket.send(bytes(sip_message, 'utf-8') + b'\r\n')
        data = my_socket.recv(1024)

        print('Recibido -- ', data.decode('utf-8'))
        print("Terminando socket...")

    if data.decode('utf-8') != '':
        received = data.decode('utf-8')
        print(received)

print("Fin.")
