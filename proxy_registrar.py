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
        tree = ET.parse(sys.argv[1])
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
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((ip, port))
        my_socket.send(bytes(message, 'utf-8') + b'\r\n')   
            
        data = my_socket.recv(1024)
        lines = []
        if data.decode('utf-8') == '\r\n' and data.decode('utf-8') != '':
            pass
        else:
            received_message = data.decode('utf-8')
            lines.append(received_message)

        prueba = ''.join(lines)
        print('........................ ' + prueba)
        return prueba

    def checkpasswd(self, passwd='', user=''):
        self.config()
        comprobation = ''
        passwd_rute = self.xml_dicc['database']['passwdpath']
        if os.path.exists(passwd_rute):
            with open(passwd_rute) as passwd_file:
                data = json.load(passwd_file)
                self.passwords_dicc = data
        if passwd == self.passwords_dicc[user][0]:
            comprobation = 'coincide'
        else:
            comprobation = 'no coincide'
        return comprobation

    def timeout(self):
        """
        Searchs for expired users
        """
        user_list = []      
        for username in self.client_dicc:
            expiration = self.client_dicc[username][3]
            actual_time = datetime.now()
            actual_secs = actual_time.timestamp()
            if actual_secs >= expiration:
                user_list.append(username)
        for user in user_list:
            del self.client_dicc[username]

class EchoHandler(socketserver.DatagramRequestHandler, Proxy):
    """
    Echo server class
    """
    def handle(self):
        lines = []
        backsend = ''

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

        IP = self.client_address[0]

        if request[0] == 'REGISTER':
            address = request[1][request[1].find(':')+1:request[1].rfind(':')]
            port = request[1][request[1].rfind(':')+1:]
            recv_event = 'Received from ' + IP + ':' + port + ': ' + prueba1

            if 'Authorization:' in request:
                response = "SIP/2.0 200 OK\r\n"
                sent_event = 'Sent to ' + IP + ':' + str(port) + ': SIP/2.0 200 OK'
                self.wfile.write(bytes(response, 'utf-8'))
                passwd = request[7][request[7].find('"')+1:request[7].rfind('"')]
                now = datetime.now()
                reg_time = now.timestamp()
                expires = float(request[4]) + reg_time

                if expires == '0' and self.checkpasswd(passwd, address) == 'coincide':
                    print("\n" + "Recibida petición de borrado")
                    del self.client_dicc[address]
                elif self.checkpasswd(passwd, address) == 'coincide':
                    print("Usuario correcto, registramos")
                    self.client_dicc[address] = [IP, port, reg_time, expires]
                else:
                    print("Contraseña incorrecta, no se puede registrar")
                    #FALTA VER QUE ERROR SE PONE AQUÍ

            elif not 'Authorization:' in request:
                nonce = random.randint(0, 999999999999999999999)
                response = 'SIP/2.0 401 Unathorized\r\n'
                response += 'WWW Authenticate: Digest nonce="' + str(nonce) + '"' + '\r\n'
                response1line = response.replace('\r\n', ' ')
                print(response1line)
                self.wfile.write(bytes(response, 'utf-8'))
                sent_event = 'Sent to ' + IP + ':' + str(port) + ': ' + response1line

            self.logfile(recv_event)
            self.logfile(sent_event)

        else:
            # ENVIO A LA DIRECCIÓN QUE ESTÁ EN LA INVITACIÓN
            port = str(self.client_address[1])
            address = request[1][request[1].find(':')+1:]
            try:
                invited_ip = self.client_dicc[address][0]
                invited_port = self.client_dicc[address][1]
                sent_event = 'Sent to ' + invited_ip + ':' + str(invited_port) + ': ' + prueba1
                backsend = self.resend('', int(invited_port), prueba)
            except KeyError:
                self.wfile.write(b'SIP/2.0 404 User Not Found\r\n')
                sent_event = 'Sent to ' + IP + ':' + port + ': SIP/2.0 404 User Not Found'
                print('Enviamos 404 user not found')

            recv_event = 'Received from ' + IP + ':' + port + ': ' + prueba1
            self.logfile(recv_event)
            self.logfile(sent_event)

            # SI LA RESPUESTA A RESEND TIENE ALGO, LA ENVIO DE VUELTA
            if backsend != '':
                recv_event = 'Received from ' + IP + ':' + port + ': ' + backsend.replace('\r\n', ' ')
                sent_event = 'Sent to ' + IP + ':' + port + ': ' + backsend.replace('\r\n', ' ')
                self.logfile(recv_event)
                self.logfile(sent_event)
                self.wfile.write(bytes(backsend, 'utf-8'))

        registerfile = self.xml_dicc['database']['path']     
        self.json2registered(registerfile, self.client_dicc)
        self.timeout()
        print(self.client_dicc)

if __name__ == "__main__":
    print("-----------------------------------1")

    try:
        config = sys.argv[1]
    except IndexError:
        sys.exit("Usage: python3 proxy_registrar config")

    prox = Proxy()
    dicc = prox.config()

    proxy_ip = dicc['server']['ip']
    proxy_port = int(dicc['server']['puerto'])
    proxy_name = dicc['server']['name']

    prox.logfile("Starting...")
    serv = socketserver.UDPServer((proxy_ip, proxy_port), EchoHandler)
    print("Server " + proxy_name + " listening at port " + str(proxy_port) + " . . .")

    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        prox.logfile("Finishing...")
        print("Proxy_registrar terminado")
