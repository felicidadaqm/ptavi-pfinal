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
import threading
import time


class UAServer():
    xml_dicc = {}
    message = ''

    def config(self):
        """ Gets configuration from a xml file """
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


class EchoHandler(socketserver.DatagramRequestHandler, UAServer):
    """
    Echo server class
    """
    rtp_info = {}

    def cvlc(self, ip='', port=''):
        listen = 'cvlc rtp://@' + ip + ':' + str(port) + ' 2> /dev/null'
        os.system(listen)

    def mp32rtp(self, ip='', port='', audio_rute=''):
        aEjecutar = 'mp32rtp -i ' + ip + ' -p ' + str(port)
        aEjecutar += ' < ' + audio_rute
        os.system(aEjecutar)

    def handle(self):
        """
        Defined different responses
        to different requests from client
        """
        lines = []
        proxy_ip = self.xml_dicc['regproxy']['ip']
        proxy_port = self.xml_dicc['regproxy']['puerto']
        my_rtp = self.xml_dicc['rtpaudio']['puerto']
        audio_rute = self.xml_dicc['audio']['path']

        for line in self.rfile:
            if line.decode('utf-8') == '\r\n' or not line:
                continue
            else:
                received_message = line.decode('utf-8')
                lines.append(received_message)

        message = ''.join(lines)
        message1line = message.replace('\r\n', ' ')
        request = message1line.split(' ')

        print("Recibimos:\r\n" + message)

        sender_ip = self.client_address[0]
        sender_port = str(self.client_address[1])
        self.wlogrecv(sender_ip, sender_port, message1line)

        if request[0] == 'INVITE' and request[2] == 'SIP/2.0':
            print('----------------')
            invited = request[9][request[9].find('=')+1:]
            print(invited)

            ip = self.client_address[0]
            port = request[14]

            if threading.Thread(target=self.mp32rtp,
                                args=(ip, port,
                                      audio_rute)).is_alive():
                response = 'SIP/2.0 480 Temporarily Unavailable\r\n\r\n'
                print("El servidor está temporalmente ocupado")
                self.wfile.write(bytes(response, 'utf-8'))
                self.wlogsent(proxy_ip, proxy_port,
                              response.replace('\r\n', ' '))
            else:
                SDP = "SIP/2.0 200 OK\r\n\r\n" + 'INVITE sip:'
                SDP += invited + ' SIP/2.0\r\n'
                SDP += 'Content-Type: application/sdp\r\n\r\n'
                SDP += 'v=0\r\n' + 'o=' + self.xml_dicc['account']['username']
                SDP += ' ' + '127.0.0.1\r\n' + 't=0\r\n'
                SDP += 'm=audio ' + my_rtp
                self.wfile.write(b'SIP/2.0 100 Trying\r\n\r\n')
                self.wfile.write(b'SIP/2.0 180 Ringing\r\n\r\n')
                self.wfile.write(bytes(SDP, 'utf-8'))
                self.rtp_info[request[10]] = request[14]

                self.wlogsent(proxy_ip, proxy_port, "SIP/2.0 100 Trying")
                self.wlogsent(proxy_ip, proxy_port, "SIP/2.0 180 Ringing")
                self.wlogsent(proxy_ip, proxy_port, SDP.replace('\r\n', ' '))

        elif request[0] == 'BYE':
            self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
            self.wlogsent(proxy_ip, proxy_port, "SIP/2.0 200 OK")
            os.system('killall vlc')
            os.system('killall mp32rtp')

            print("SI")

        elif request[0] == 'ACK':
            ip = self.client_address[0]
            port = self.rtp_info[ip]

            print('------- RECIBIENDO Y ENVIANDO AUDIO -------')
            print('------- ESPERE POR FAVOR -------')
            cvlc_thread = threading.Thread(target=self.cvlc, args=(ip, port))
            mp32rtp_thread = threading.Thread(target=self.mp32rtp,
                                              args=(ip, port, audio_rute))

            mp32rtp_thread.start()
            time.sleep(1)
            cvlc_thread.start()

            self.wlogsent(ip, my_rtp, "Enviando audio")
            self.wlogrecv(ip, port, "Recibiendo audio")
        elif request[0] != ('INVITE' and 'BYE' and 'ACK' and 'REGISTER'):
            self.wfile.write(b'SIP/2.0 405 Method Not Allowed\r\n\r\n')
            self.wlogsent(proxy_ip, proxy_port,
                          "SIP/2.0 405 Method Not Allowed")
            print("Hemos recibido una petición inválida.")
        elif request[2] != 'SIP/2.0':
            self.wfile.write(b'SIP/2.0 400 Bad Request\r\n\r\n')
            self.wlogsent(proxy_ip, proxy_port, "SIP/2.0 400 Bad Request")


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
    server.logfile("Starting...")

    serv = socketserver.UDPServer(('', port), EchoHandler)
    print("Listening...")

    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        server.logfile("Finishing...")
        print("uaserver terminado")
