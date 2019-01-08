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
        return self.message

    def writing_log(self):

        self.building_sip()
        proxy_ip = self.xml_dicc['regproxy']['ip']
        proxy_port = self.xml_dicc['regproxy']['puerto']
        event1 = "Sent to " + proxy_ip + ":" + proxy_port + ": " + self.message
        siptolog = event1.replace('\r\n', ' ')

        self.logfile(siptolog)

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
    client.logfile('Starting...')
    log = client.writing_log()
    sip_message = client.building_sip()

    proxy_ip = dicc['regproxy']['ip']
    proxy_port = int(dicc['regproxy']['puerto'])
    password = dicc['account']['passwd']

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((proxy_ip, proxy_port))
        print("Enviamos:" + sip_message)
        my_socket.send(bytes(sip_message, 'utf-8') + b'\r\n\r\n')

        try:
            data = my_socket.recv(1024)
        except ConnectionRefusedError:
            EVENT = 'Error: No server listening at ' + proxy_ip + ' port ' + str(proxy_port)
            client.logfile(EVENT)
            sys.exit('Nada escuchando')

        print('Recibido -- \r\n', data.decode('utf-8'))

        lines = []
        if data.decode('utf-8') != '':
            received = data.decode('utf-8')
            lines.append(received)

            recv = ''.join(lines)
            log_recv = recv.replace('\r\n', ' ')
            recv_event = "Received from " + proxy_ip + ":" + str(proxy_port) + ":" + log_recv
            client.logfile(recv_event)

            request = log_recv.split(' ')

            if '401' in received:
                response = sip_message + '\r\n'
                response += 'Authorization: Digest response="' + password + '"'

                my_socket.send(bytes(response, 'utf-8') + b'\r\n\r\n')
                data = my_socket.recv(proxy_port)
                print(data.decode('utf-8'))
                recv = data.decode('utf-8')

                logmessg_r = "Received from " + proxy_ip + ":" + str(proxy_port) + ": " + recv
                logmessg_s = "Sent to " + proxy_ip + ":" + str(proxy_port) + ": " + response
                sent_event = logmessg_s.replace('\r\n', ' ')
                recv_event = logmessg_r.replace('\r\n', ' ')
                client.logfile(sent_event)
                client.logfile(recv_event)


            elif '100' and '180' in received:
                receiver = request[19][request[19].find('=')+1:]
                print('--------------- PRUEBA CABECERAS')
                print(request)
                print(receiver)
                response = "ACK sip:" + receiver + " SIP/2.0"
                sent_event = "Sent to " + proxy_ip + ":" + str(proxy_port) + ": " + response
                client.logfile(sent_event)
                my_socket.send(bytes(response, 'utf-8') + b'\r\n\r\n')

                audio_rute = dicc['audio']['path']
                ip_server = request[20]
                rtp_servport = request[23]
                print(rtp_servport)
                aEjecutar = 'mp32rtp -i ' + ip_server + ' -p ' + rtp_servport + ' < ' + audio_rute
                print("Vamos a ejecutar: " + aEjecutar)
                os.system(aEjecutar)

    client.logfile('Finishing...') 

print("Fin.")
