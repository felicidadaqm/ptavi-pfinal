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
from datetime import datetime, timedelta

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

    def sendtoproxy(self, ip='', port='', message=''):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((ip, port))
            my_socket.send(bytes(message, 'utf-8') + b'\r\n')
            print("Enviando: " + message)

            data = my_socket.recv(port)
            recv = data.decode('utf-8')
            recv1 = recv.replace('\r\n', ' ')
            return recv1

    def registerserver(self, adicc=''):
        self.config()
        proxy_ip = self.xml_dicc['regproxy']['ip']
        proxy_port = int(self.xml_dicc['regproxy']['puerto'])
        username = self.xml_dicc['account']['username']
        sip_message = "REGISTER sip:" + username + ':' + str(port) + ' SIP/2.0\r\n'
        sip_message += 'Expires: ' + '30\r\n'
        message = sip_message + adicc

        self.logfile("Starting...")

        recv = self.sendtoproxy(proxy_ip, proxy_port, message)   

        sent_event = "Sent to " + proxy_ip + ":" + str(proxy_port) + ": " + message.replace('\r\n', ' ')
        recv_event = "Received from " + proxy_ip + ":" + str(proxy_port) + ": " + recv

        self.logfile(sent_event)
        self.logfile(recv_event)

        if '401' in recv:
            password = self.xml_dicc['account']['passwd']
            response = sip_message + 'Authorization: Digest response="' + password + '"'
            logmessg = "Sent to " + proxy_ip + ":" + str(proxy_port) + ": " + response
            sent_event = logmessg.replace('\r\n', ' ')
            self.logfile(sent_event)
            data = self.sendtoproxy(proxy_ip, proxy_port, response)

            recv_event = "Received from " + proxy_ip + ":" + str(proxy_port) + ": " + data
            self.logfile(recv_event)


class EchoHandler(socketserver.DatagramRequestHandler, UAServer):
    """
    Echo server class
    """
    rtp_info = {}

    def handle(self):
        """
        Defined different responses
        to different requests from client
        """
        lines = []
        proxy_ip = self.xml_dicc['regproxy']['ip']
        proxy_port = self.xml_dicc['regproxy']['puerto']

        for line in self.rfile:
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
        print("-----------------------")
        
        recv_event = "Received from " + proxy_ip + ":" + proxy_port + ": " + prueba1
        self.logfile(recv_event)

        if request[0] == 'INVITE' and request[2] == 'SIP/2.0':
            print('----------------')
            invited = request[6][request[6].find('=')+1:] 
            SDP = "SIP/2.0 200 OK\r\n" + 'INVITE sip:' + invited + ' SIP/2.0\r\n'
            SDP += 'Content-Type: application/sdp\r\n\r\n'
            SDP += 'v=0\r\n' + 'o=' + self.xml_dicc['account']['username']
            SDP += ' ' + '127.0.0.1\r\n' + 't=0\r\n'
            SDP += 'm=audio ' + self.xml_dicc['rtpaudio']['puerto']
            self.wfile.write(b'SIP/2.0 100 Trying\r\n')
            self.wfile.write(b'SIP/2.0 180 Ringing\r\n')
            self.wfile.write(bytes(SDP, 'utf-8'))
            self.rtp_info[request[7]] = request[11]

            self.logfile("Sent to " + proxy_ip + ":" + proxy_port + ": SIP/2.0 100 Trying")
            self.logfile("Sent to " + proxy_ip + ":" + proxy_port + ": SIP/2.0 180 Ringing")
            self.logfile("Sent to " + proxy_ip + ":" + proxy_port + ": " + SDP.replace('\r\n', ' '))
        elif request[0] == 'BYE':
            self.wfile.write(b'SIP/2.0 200 OK\r\n')
            self.logfile("Sent to " + proxy_ip + ":" + proxy_port + ": SIP/2.0 200 OK")
        elif request[0] == 'ACK':
            audio_rute = self.xml_dicc['audio']['path']
            ip = self.client_address[0]
            port = self.rtp_info[ip]
            aEjecutar = 'mp32rtp -i ' + ip + '-p ' + port + ' < ' + audio_rute
            print("Vamos a ejecutar: " + aEjecutar)
            #os.system(aEjecutar)
        elif request[0] != ('INVITE' and 'BYE' and 'ACK' and 'REGISTER'):
            self.wfile.write(b'SIP/2.0 405 Method Not Allowed\r\n')
            self.logfile("Sent to " + proxy_ip + ":" + proxy_port + ": SIP/2.0 405 Method Not Allowed")
            print("Hemos recibido una petición inválida.")
        elif request[2] != 'SIP/2.0':
            self.wfile.write(b'SIP/2.0 400 Bad Request\r\n')
            self.logfile("Sent to " + proxy_ip + ":" + proxy_port + ": SIP/2.0 400 Bad Request")


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

    server.registerserver()
    serv = socketserver.UDPServer(('', port), EchoHandler)
    print("Listening...")

    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        server.logfile("Finishing...")
        print("uaserver terminado")



