#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
import os.path
import os
import xml.etree.ElementTree as ET
import os.path
import socket

class UAServer():
    xml_dicc = {}
    message = ''

    def config(self):
    # SACO LA CONFIGURACIÓN DE XML
        tree = ET.parse(sys.argv[1])
        root = tree.getroot()
        for branch in root:
            self.xml_dicc[str(branch.tag)] = branch.attrib
        return self.xml_dicc

    def logfile(self, event=''):
        self.config()
        file_rute = self.xml_dicc['log']['path']
        format_date = '%Y%m%d%H%M%S'
        time = datetime.now()
        date = time.strftime(format_date)
        event = event + '\r\n'
        if os.path.exists(file_rute):
            file = open(file_rute, 'a')
        else:
            file = open(file_rute, 'w')
        file.write(date + " " + event)     


class EchoHandler(socketserver.DatagramRequestHandler, UAServer):
    """
    Echo server class
    """

    def handle(self):
        """
        Defined different responses
        to different requests from client
        """

        for line in self.rfile:
            lines = []
            print("El cliente nos manda " + line.decode('utf-8'))

            if line.decode('utf-8') == '\r\n' or not line:
                continue
            else:
                received_message = line.decode('utf-8')
                lines.append(received_message) 

        prueba = ''.join(lines)
        prueba1 = prueba.replace('\r\n', ' ')
        request = prueba1.split(' ')
        print(request)
        print('______________________')

        if request[2] != 'SIP/2.0\r\n':
            self.wfile.write(b'SIP/2.0 400 Bad Request')
        elif request[0] == 'INVITE':
            RESPONSE = 'SIP/2.0 100 Trying\r\n' + 'SIP/2.0 180 Ringing\r\n'
            RESPONSE += 'SIP/2.0 200 OK\r\n'
            self.wfile.write(bytes(RESPONSE, 'utf-8'))
        elif request[0] == 'BYE':
            self.wfile.write(b'SIP/2.0 200 OK\r\n')
        elif request[0] == 'ACK':
            aEjecutar = 'mp32rtp -i 127.0.0.1 -p 23032 < ' + 'AQUÍ AUDIO'
            print("Vamos a ejecutar: " + aEjecutar)
            #os.system(aEjecutar)
        elif request[0] != ('INVITE' and 'BYE' and 'ACK'):
            self.wfile.write(b'SIP/2.0 405 Method Not Allowed\r\n')
            print("Hemos recibido una petición inválida.")


if __name__ == "__main__":
    """
    Echo server is created
    """
    try:
        config = sys.argv[1]
    except (IndexError, ValueError, NameError):
        sys.exit("Usage: python uaserver.py config")

    server = UAServer()
    dicc = server.config()
    port = int(dicc['uaserver']['puerto'])
    proxy_ip = dicc['regproxy']['ip']
    proxy_port = int(dicc['regproxy']['puerto'])
    username = dicc['account']['username']
    sip_message = "REGISTER sip:" + username + ':' + str(port) + ' SIP/2.0\r\n'
    sip_message += 'Expires: ' + '1'

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((proxy_ip, proxy_port))
        print("Enviando: " + sip_message)
        my_socket.send(bytes(sip_message, 'utf-8') + b'\r\n')

    serv = socketserver.UDPServer(('', port), EchoHandler)
    print("Listening...")
    serv.serve_forever()
