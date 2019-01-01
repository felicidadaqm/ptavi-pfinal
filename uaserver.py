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


class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """

    def handle(self):
        """
        Defined different responses
        to different requests from client
        """

        for line in self.rfile:
            print("El cliente nos manda " + line.decode('utf-8'))

            if line.decode('utf-8') == '\r\n' or not line:
                continue
            else:
                request = line.decode('utf-8').split(" ")

            if request[2] != 'SIP/2.0\r\n':
                self.wfile.write(b'SIP/2.0 400 Bad Request')
            elif request[0] == 'INVITE':
                RESPONSE = 'SIP/2.0 100 Trying ' + 'SIP/2.0 180 Ringing '
                RESPONSE += 'SIP/2.0 200 OK'
                self.wfile.write(bytes(RESPONSE, 'utf-8'))
            elif request[0] == 'BYE':
                self.wfile.write(b'SIP/2.0 200 OK')
            elif request[0] == 'ACK':
                aEjecutar = 'mp32rtp -i 127.0.0.1 -p 23032 < ' + 'AQUÍ AUDIO'
                print("Vamos a ejecutar: " + aEjecutar)
                #os.system(aEjecutar)
            elif request[0] != ('INVITE' and 'BYE' and 'ACK'):
                self.wfile.write(b'SIP/2.0 405 Method Not Allowed')
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

    serv = socketserver.UDPServer(('', port), EchoHandler)
    print("Listening...")
    serv.serve_forever()
