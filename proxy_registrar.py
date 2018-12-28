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

    def json2registered(self, file_rute=''):
        """
        Checks if there's a json file,
        if not, it creates it
        """
        if os.path.exists(file_rute):
            with open(file_rute, 'w') as json_file:
                json.dump(self.client_dicc, json_file)
        else:
            with open(file_rute, 'w') as json_file:
                json.dump(self.client_dicc, json_file)

    def passwdfile(self, password=''):
        self.config()
        file_rute = self.xml_dicc['database']['passwdpath']
        if os.path.exists(file_rute):
            file = open(file_rute, 'a')
        else:
            file = open(file_rute, 'w')


    def logfile(self, event=''):
        self.config()
        file_rute = self.xml_dicc['log']['path']
        event = event + '\r\n'
        if os.path.exists(file_rute):
            file = open(file_rute, 'a')
        else:
            file = open(file_rute, 'w')
        file.write(event)


class EchoHandler(socketserver.DatagramRequestHandler, Proxy):
    """
    Echo server class
    """
    def handle(self):

        lines = []

        format_date = '%Y%m%d%H%M%S'
        time = datetime.now()
        date = time.strftime(format_date)

        self.logfile(date + " Starting...")

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
        print(prueba)
        print('______________________')

        if request[0] == 'REGISTER' and request[2] == 'SIP/2.0':
            address = request[1][request[1].find(':')+1:request[1].rfind(':')]
            IP = self.client_address[0]
            port = request[1][request[1].rfind(':')+1:]

            user_data = address + " " + IP + " " + str(port)
            if 'Authorization:' in request:
                #FALTA COMPROBACIÓN CONTRASEÑA Y GUARDAR EN DICCIONARIO
                response = "200 OK\r\n"
                sent_event = date + ' Sent to ' + IP + ':' + str(port) + ': ' + response
                self.wfile.write(bytes(response, 'utf-8'))
                passwd = request[7][request[7].find('"')+1:request[7].rfind('"')]
                self.user = address
                self.client_port = port
                self.passwd = self.passwdfile(passwd)
                print("meh")
            elif not 'Authorization:' in request:
                nonce = random.randint(0, 999999999999999999999)
                response = 'SIP/2.0 401 Unathorized\r\n'
                response += 'WWW Authenticate: Digest nonce="' + str(nonce) + '"' + '\r\n'
                response1line = response.replace('\r\n', ' ')
                self.wfile.write(bytes(response, 'utf-8'))
                sent_event = date + ' Sent to ' + IP + ':' + str(port) + ': ' + response1line

        if request[0] == 'INVITE' or request[0] == 'BYE' or request[0] == 'ACK':
            # FALTA BUSCAR EN DICCIONARIO PARA REENVIAR EL MENSAJE
            IP = self.client_address[0]
            port = str(self.client_address[1])


        recv_event = date + ' Received from ' + IP + ':' + port + ': ' + prueba1
        passwdfile = self.xml_dicc['database']['passwdpath']
        registerfile = self.xml_dicc['database']['path']
                  
        self.logfile(recv_event)
        self.logfile(sent_event)
        self.json2registered(passwdfile)
        print(self.client_dicc)

if __name__ == "__main__":
    print("-----------------------------------")

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











