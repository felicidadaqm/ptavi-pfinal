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

    def passwdfile(self):
        self.config()
        file_rute = self.xml_dicc['log']['path']
        if os.path.exists(file_rute):
            file = open(file_rute, 'a')
        else:
            file = open(file_rute, 'w')

class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """

    def handle(self):
        for line in self.rfile:
            print("El cliente nos manda " + line.decode('utf-8'))


if __name__ == "__main__":
    print("prueba")

    try:
        config = sys.argv[1]
    except IndexError:
        sys.exit("Usage: python3 server.py IP port audio_file")

    prox = Proxy()
    dicc = prox.config()
    print(dicc)

    proxy_ip = dicc['server']['ip']
    proxy_port = int(dicc['server']['puerto'])

    serv = socketserver.UDPServer((proxy_ip, proxy_port), EchoHandler)
    print("Listening...")
    serv.serve_forever()











