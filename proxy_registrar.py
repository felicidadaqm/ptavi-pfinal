#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socketserver
import sys
from datetime import datetime, timedelta
import os.path
import os
import xml.etree.ElementTree as ET

class Proxy:
    client_dicc = {}
    xml_dicc = {}
    
    def config(self):
    # SACO LA CONFIGURACIÓN DE XML
        tree = ET.parse('pr.xml')
        root = tree.getroot()
        for branch in root:
            self.xml_dicc[str(branch.tag)] = branch.attrib
        print(self.xml_dicc)
        return self.xml_dicc

    def registeredfile(self):
    # CREO ARCHIVOS DE CLIENTES REGISTRADOS
        self.config()
        file_rute = self.xml_dicc['database']['path']
        if os.path.exists(file_rute):
            file = open(file_rute, 'a')
        else:
            file = open(file_rute, 'w')

    def passwdfile(self):
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
        format_date = '%Y%m%d%H%M%S'
        time = datetime.now()
        date = time.strftime(format_date)

        self.logfile(date + " Starting...")

        for line in self.rfile:
            print("El cliente nos manda " + line.decode('utf-8'))
            if line.decode('utf-8') == '\r\n' or not line:
                continue
            else:
                request = line.decode('utf-8').split(" ")
                received_message = line.decode('utf-8')

            if request[0] == 'REGISTER' and request [2] == 'SIP/2.0\r\n':
                self.registeredfile()
                address = request[1][request[1].find(':')+1:request[1].rfind(':')]
                IP = self.client_address[0]
                port = self.client_address[1]

                event = date + ' Received from ' + IP + ':' + str(port) + ' ' + received_message
                self.logfile(event)

                user_data = address + " " + IP + " " + str(port)
                print(user_data)

            elif request[0] == 'Expires:':
                print('meh')


if __name__ == "__main__":
    print("prueba")

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











