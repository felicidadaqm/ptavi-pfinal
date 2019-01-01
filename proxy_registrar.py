#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socketserver
import sys
from datetime import datetime, timedelta
import os.path
import os
import xml.etree.ElementTree as ET
import json
import random
import socket

class Proxy:
    client_dicc = {}
    xml_dicc = {}
    passwords_dicc = {}
    
    def config(self):
    # SACO LA CONFIGURACIÓN DE XML
        tree = ET.parse('pr.xml')
        root = tree.getroot()
        for branch in root:
            self.xml_dicc[str(branch.tag)] = branch.attrib
        return self.xml_dicc

    def json2registered(self, file_rute='', dicc=''):
        """
        Checks if there's a json file,
        if not, it creates it
        """
        if os.path.exists(file_rute):
            with open(file_rute, 'w') as json_file:
                json.dump(dicc, json_file)
        else:
            with open(file_rute, 'w') as json_file:
                json.dump(dicc, json_file)


    def logfile(self, event=''):
        self.config()
        format_date = '%Y%m%d%H%M%S'
        time = datetime.now()
        date = time.strftime(format_date)
        file_rute = self.xml_dicc['log']['path']
        event = event + '\r\n'
        if os.path.exists(file_rute):
            file = open(file_rute, 'a')
        else:
            file = open(file_rute, 'w')
        file.write(date + " " + event)

    def resend(self, ip='', port='', message=''):
        #APAÑAR, NO REENVIA
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((ip, port))
            my_socket.send(bytes(message, 'utf-8') + b'\r\n')
            event = ' Sent to ' + ip + ':' + str(port) + ': ' + message
            self.logfile(event)
            


class EchoHandler(socketserver.DatagramRequestHandler, Proxy):
    """
    Echo server class
    """
    def handle(self):

        lines = []
        self.logfile(" Starting...")

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
        print('______________________')

        if request[0] == 'REGISTER':
            address = request[1][request[1].find(':')+1:request[1].rfind(':')]
            IP = self.client_address[0]
            port = request[1][request[1].rfind(':')+1:]

            user_data = address + " " + IP + " " + str(port)
            if 'Authorization:' in request:
                #FALTA COMPROBACIÓN CONTRASEÑA
                response = "200 OK\r\n"
                sent_event = ' Sent to ' + IP + ':' + str(port) + ': ' + response
                self.wfile.write(bytes(response, 'utf-8'))
                passwd = request[7][request[7].find('"')+1:request[7].rfind('"')]
                now = datetime.now()
                reg_time = now.timestamp()
                expires = request[4]
                self.client_dicc[address] = [IP, port, reg_time, expires]
                self.passwords_dicc[address] = [passwd]
                self.resend('', int('6001'), prueba1)

            elif not 'Authorization:' in request:
                nonce = random.randint(0, 999999999999999999999)
                response = 'SIP/2.0 401 Unathorized\r\n'
                response += 'WWW Authenticate: Digest nonce="' + str(nonce) + '"' + '\r\n'
                response1line = response.replace('\r\n', ' ')
                self.wfile.write(bytes(response, 'utf-8'))
                sent_event = ' Sent to ' + IP + ':' + str(port) + ': ' + response1line
                self.resend('', int('6001'), response1line)

        if request[0] == 'INVITE' or request[0] == 'BYE' or request[0] == 'ACK':
            # FALTA REENVIAR EL MENSAJE
            IP = self.client_address[0]
            port = str(self.client_address[1])
            address = request[1][request[1].find(':')+1:]
            invited_ip = self.client_dicc[address][0]
            invited_port = self.client_dicc[address][1]
            sent_event = ' Sent to ' + invited_ip + ':' + str(invited_port) + ': ' + prueba
            print(invited_ip, str(invited_port))


        recv_event = ' Received from ' + IP + ':' + port + ': ' + prueba1
        passwdfile = self.xml_dicc['database']['passwdpath']
        registerfile = self.xml_dicc['database']['path']
                  
        self.logfile(recv_event)
        self.logfile(sent_event)
        self.json2registered(registerfile, self.client_dicc)
        self.json2registered(passwdfile, self.passwords_dicc)
        print(self.client_dicc)

if __name__ == "__main__":
    print("------------------------------------")

    try:
        config = sys.argv[1]
    except IndexError:
        sys.exit("Usage: python3 proxy_registrar config")

    prox = Proxy()
    dicc = prox.config()

    proxy_ip = dicc['server']['ip']
    proxy_port = int(dicc['server']['puerto'])
    proxy_name = dicc['server']['name']

    serv = socketserver.UDPServer((proxy_ip, proxy_port), EchoHandler)
    print("Server " + proxy_name + " listening at port " + str(proxy_port) + " . . .")
    serv.serve_forever()











