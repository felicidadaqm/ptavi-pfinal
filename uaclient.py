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
import threading
import time

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

    def wlogsent(self, ip='', port='', extra=''):
        sent_event = "Sent to " + ip + ":" + port + ": " + extra
        self.logfile(sent_event)

    def wlogrecv(self, ip='', port='', extra=''):
        recv_event = "Received from " + ip + ":" + port + ": " + extra
        self.logfile(recv_event)

    def building_sip(self, username='', rtp_port='', my_ip='', my_port=''):
        self.config()
        method = sys.argv[2]
        option = sys.argv[3]

        if method == 'REGISTER':
            self.message = method + ' sip:' + username + ':' + my_port
            self.message += ' SIP/2.0\r\n' + 'Expires: ' + option
        elif method == 'INVITE':
            self.message = method + ' sip:' + option + ' SIP/2.0\r\n'
            self.message += 'Content-Type: application/sdp\r\n' + '\r\n'
            self.message += 'v=0\r\n' + 'o=' + username + ' ' + my_ip + '\r\n'
            self.message += 's=misesion\r\n' + 't=0\r\n' + 'm=audio '
            self.message += rtp_port + ' RTP\r\n'
        elif method == 'BYE':
            self.message = method + ' sip:' + option + ' SIP/2.0\r\n'
        else:
            self.message = method + ' sip:' + option + ' SIP/2.0\r\n'
            print("Petición inválida")
        return self.message


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

    proxy_ip = dicc['regproxy']['ip']
    proxy_port = dicc['regproxy']['puerto']
    password = dicc['account']['passwd']
    rtp_port = dicc['rtpaudio']['puerto']
    my_ip = dicc['uaserver']['ip']
    username = dicc['account']['username']
    my_port = dicc['uaserver']['puerto']
    audio_rute = dicc['audio']['path']

    if my_ip == '':
        my_ip = '127.0.0.1'

    sip_message = client.building_sip(username, rtp_port, my_ip, my_port)

    def cvlc(self, ip='', port=''):
        listen = 'cvlc rtp://@' + ip + ':' + str(port) + ' 2> /dev/null'
        os.system(listen)

    def mp32rtp(self, ip='', port='', audio_rute=''):
        aEjecutar = 'mp32rtp -i ' + ip + ' -p ' + str(port)
        aEjecutar += ' < ' + audio_rute
        os.system(aEjecutar)

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((proxy_ip, int(proxy_port)))
        print("Enviamos:" + sip_message)
        my_socket.send(bytes(sip_message, 'utf-8') + b'\r\n\r\n')
        client.wlogsent(proxy_ip, proxy_port, sip_message.replace('\r\n', ' '))

        try:
            data = my_socket.recv(1024)
        except ConnectionRefusedError:
            EVENT = 'Error: No server listening at ' + proxy_ip
            EVENT += ' port ' + proxy_port
            client.logfile(EVENT)
            sys.exit('Nada escuchando')

        print('Recibido -- \r\n', data.decode('utf-8'))

        lines = []
        if data.decode('utf-8') != '':
            received = data.decode('utf-8')
            lines.append(received)

            recv = ''.join(lines)
            log_recv = recv.replace('\r\n', ' ')
            client.wlogrecv(proxy_ip, proxy_port, log_recv)

            request = log_recv.split(' ')

            if '401' in received:
                response = sip_message + '\r\n'
                response += 'Authorization: Digest response="' + password + '"'

                my_socket.send(bytes(response, 'utf-8') + b'\r\n\r\n')
                data = my_socket.recv(int(proxy_port))
                print(data.decode('utf-8'))
                recv = data.decode('utf-8')

                client.wlogsent(proxy_ip, proxy_port,
                                response.replace('\r\n', ' '))
                client.wlogrecv(proxy_ip, proxy_port,
                                recv.replace('\r\n', ' '))

            elif '100' and '180' in received:
                receiver = request[20][request[20].find('=')+1:]
                print('--------------- PRUEBA CABECERAS')
                print(request)
                print(receiver)
                response = "ACK sip:" + receiver + " SIP/2.0"
                client.wlogsent(proxy_ip, proxy_port, response)
                my_socket.send(bytes(response, 'utf-8') + b'\r\n\r\n')

                audio_rute = dicc['audio']['path']
                ip_server = request[21]
                rtp_servport = request[24]
                print(rtp_servport)
                client.wlogsent(ip_server, rtp_servport, "Enviando audio")
                client.wlogrecv(ip_server, rtp_servport, "Recibiendo audio")

                #_thread.start_new_thread(mp32rtp, (ip_server, rtp_servport, audio_rute))
                #_thread.start_new_thread(cvlc, (my_ip, rtp_port))
                cvlc_thread = threading.Thread(target=cvlc, args=(my_ip, rtp_port))
                mp32rtp_thread = threading.Thread(target=mp32rtp, args=(ip_server, rtp_servport, audio_rute))

                cvlc_thread.start()
                print('1')
                time.sleep(1)
                mp32rtp_thread.start()

                time.sleep(15)
                os.system('killall mp32rtp')
                os.system('killall vlc')
                sys.exit("Acabando servidor...")

    client.logfile('Finishing...')
    my_socket.close()

print("Fin.")
