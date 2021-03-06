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
        """ Gets configuration from xml file """
        tree = ET.parse(sys.argv[1])
        root = tree.getroot()
        for branch in root:
            self.xml_dicc[str(branch.tag)] = branch.attrib
        return self.xml_dicc

    def json2registered(self, file_rute='', dicc={}):
        """
        Checks if there's a json file,
        if not, it creates it
        """
        with open(file_rute, 'w') as json_file:
            json.dump(dicc, json_file)

    def restablishusers(self):
        file_rute = self.xml_dicc['database']['path']
        if os.path.exists(file_rute):
            with open(file_rute) as json_file:
                users = json.load(json_file)
                self.client_dicc = users

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

    def wlogsent(self, ip='', port='', extra=''):
        sent_event = "Sent to " + ip + ":" + port + ": " + extra
        self.logfile(sent_event)

    def wlogrecv(self, ip='', port='', extra=''):
        recv_event = "Received from " + ip + ":" + port + ": " + extra
        self.logfile(recv_event)

    def resend(self, ip='', port='', message=''):
        """
        Checks the messages we get from an ua,
        and sees possible connection errors
        """
        recv_mssg = ''
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((ip, port))
        my_socket.send(bytes(message, 'utf-8') + b'\r\n')

        try:
            data = my_socket.recv(1024)
            lines = []
            if data.decode('utf-8') == '\r\n' and data.decode('utf-8') == '':
                pass
            else:
                received_message = data.decode('utf-8')
                lines.append(received_message)
            recv_mssg = ''.join(lines)
        except ConnectionRefusedError:
            self.logfile('Error: No server listening at ' + ip +
                         ' port ' + str(port))
            print("ATENCIÓN!!! No hay ningún servidor escuchando")
            self.wfile.write(bytes("SIP/2.0 503 Service Unavailable\r\n\r\n",
                                   'utf-8'))
        return recv_mssg

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
        try:
            for user in user_list:
                del self.client_dicc[username]
        except KeyError:
            print("No se puede borrar, usuario no encontrado")

    def aditionalheader(self, message='', eol=''):
        """ Ads an aditional proxy """
        ip = self.xml_dicc['server']['ip']
        port = self.xml_dicc['server']['puerto']
        proxy_header = eol + "Via: SIP/2.0/UDP " + ip + ":"
        proxy_header += port + ";rport;branch=PASAMOSPORPOROXY\r\n"
        final_messg = message + proxy_header
        return final_messg

    def checkip(self, ip=''):
        validez = ''
        ipieces = ip.split('.')
        biggest_num = 0

        if len(ipieces) != 4:
            validez = 'no valida'
        else:
            for number in ipieces:
                if int(number) > biggest_num:
                    biggest_num = int(number)

            if biggest_num < 0 or biggest_num > 255:
                validez = 'no valida'
            else:
                validez = 'valida'
        return validez

    def checkport(self, port=''):
        validez = ''

        if '.' in str(port):
            validez = 'no valido'
        else:
            validez = 'valido'
        return validez

    def checkregistered(self, username=''):
        registered = ''
        if username in self.client_dicc:
            registered = 'ok'
        else:
            registered = 'no'

        return registered

    def checkifparticipant(self, username='', partlist=[]):
        participant = ''
        print(partlist)
        if username in partlist:
            participant = 'yes'
        else:
            participant = 'no'

        return participant

    def addparticipant(self, username='', partlist=[]):
        if username not in partlist:
            partlist.append(username)


class EchoHandler(socketserver.DatagramRequestHandler, Proxy):
    """
    Echo server class
    """
    client_info = {}
    conver_participants = []

    def handle(self):
        lines = []
        backsend = ''
        final_messg = ''
        registered = ''
        sender_address = ''
        participant = ''
        conver_participants = []

        if not self.client_dicc:
            self.restablishusers()

        for line in self.rfile:
            if line.decode('utf-8') == '\r\n' or not line:
                continue
            else:
                received_message = line.decode('utf-8')
                lines.append(received_message)

        message = ''.join(lines)
        logextra = message.replace('\r\n', ' ')
        request = logextra.split(' ')
        print("El cliente nos manda: " + message)

        IP = self.client_address[0]
        recv_port = str(self.client_address[1])
        validez_ip = self.checkip(IP)

        if request[0] == 'REGISTER' and validez_ip == 'valida':
            address = request[1][request[1].find(':')+1:request[1].rfind(':')]
            port = request[1][request[1].rfind(':')+1:]
            validez_port = self.checkport(port)
            self.client_info[IP] = port

            if validez_port == 'no valido':
                print('Valor de puerto no válido')
                response = '400 Bad Request\r\n\r\n'
                self.wfile.write(bytes(response, 'utf-8'))
                self.logfile('Error: Port value is not valid')

            if 'Authorization:' in request and validez_port == 'valido':
                response = "SIP/2.0 200 OK\r\n"
                self.wfile.write(bytes(response, 'utf-8'))
                passwd = request[7][request[7].find('"')+1:
                                    request[7].rfind('"')]
                now = datetime.now()
                reg_time = now.timestamp()
                expires = float(request[4]) + reg_time
                passwd_comprobation = self.checkpasswd(passwd, address)

                if request[4] == '0' and passwd_comprobation == 'coincide':
                    print("Recibida petición de borrado" + '\r\n')
                    del self.client_dicc[address]
                elif passwd_comprobation == 'coincide':
                    print("Usuario correcto, registramos" + '\r\n')
                    self.client_dicc[address] = [IP, port, reg_time, expires]
                else:
                    print("Contraseña incorrecta, no se puede registrar" +
                          '\r\n')
                    response = '400 Bad Request\r\n\r\n'
                    self.wfile.write(bytes(response, 'utf-8'))
                    self.wlogsent(IP, port, response.replace('\r\n', ' '))

            elif 'Authorization:' not in request and validez_port == 'valido':
                nonce = random.randint(0, 999999999999999999999)
                response = 'SIP/2.0 401 Unathorized\r\n\r\n'
                response += 'WWW Authenticate: Digest nonce="' + str(nonce)
                response += '"' + '\r\n\r\n'
                self.wfile.write(bytes(response, 'utf-8'))

            self.wlogrecv(IP, recv_port, logextra)
            self.wlogsent(IP, port, response.replace('\r\n', ' '))

        elif request[0] != 'REGISTER' and validez_ip == 'valida':
            # ENVIO A LA DIRECCIÓN QUE ESTÁ EN LA INVITACIÓN
            port = str(self.client_address[1])
            inv_address = request[1][request[1].find(':')+1:]
            self.addparticipant(inv_address, self.conver_participants)
            self.wlogrecv(IP, port, logextra)

            print('----------AÑADIMOS CABECERA Y REENVIAMOS---------')

            if request[0] == 'INVITE':
                princip = self.aditionalheader(lines[0], '')
                final_messg = princip + lines[1] + '\r\n' + ''.join(lines[2:])
                sender_address = request[6][request[6].find("=")+1:]
                self.addparticipant(sender_address, self.conver_participants)
                registered = self.checkregistered(sender_address)
                self.client_info[inv_address] = sender_address
            elif request[0] == 'BYE':
                for_check = self.client_info[inv_address]
                participant = self.checkifparticipant(for_check,
                                                      self.conver_participants)
                final_messg = self.aditionalheader(message)
                self.conver_participants = []
            else:
                final_messg = self.aditionalheader(message)

            comprobations = ''
            if registered == 'ok' or registered == '':
                if participant == 'yes' or participant == '':
                    comprobations = 'correcto'
                else:
                    comprobations = 'incorrecto'
            else:
                comprobations = 'incorrecto'

            if comprobations == 'correcto' or request[0] == 'ACK':
                try:
                    print("Todo correcto, reenviamos:\r\n" + final_messg)
                    invited_ip = self.client_dicc[inv_address][0]
                    invited_port = self.client_dicc[inv_address][1]
                    backsend = self.resend('', int(invited_port), final_messg)
                    self.wlogrecv(IP, port, logextra)
                    self.wlogsent(invited_ip, str(invited_port),
                                  final_messg.replace('\r\n', ' '))

                except KeyError:
                    self.wfile.write(b'SIP/2.0 404 User Not Found\r\n\r\n')
                    self.wlogsent(IP, str(port), 'SIP/2.0 404 User Not Found')
                    print('Enviamos 404 user not found')

                print("Los participantes de esta conversación son: " +
                      ' '.join(self.conver_participants) + '\r\n')

            elif comprobations == 'incorrecto':
                response = 'SIP/2.0 401 Unathorized\r\n\r\n'
                self.wfile.write(bytes(response, 'utf-8'))
                self.wlogrecv(IP, port, logextra)
                self.wlogsent(IP, port, response.replace('\r\n', ' '))
                print("Usuario no autorizado intenta enviar bye o invite" +
                      '\r\n')

            # SI LA RESPUESTA A RESEND TIENE ALGO, LA ENVIO DE VUELTA
            if backsend != '':
                if '200' in backsend:
                    spliting_mssg = backsend.split('\r\n')
                    final_mssg = self.aditionalheader('\r\n'.join(
                                                      spliting_mssg[:7]),
                                                      '\r\n')
                    final_mssg += '\r\n'.join(spliting_mssg[8:])
                    print(final_mssg)
                else:
                    final_mssg = self.aditionalheader(backsend)
                    print(final_mssg)
                self.wlogrecv(IP, port, backsend.replace('\r\n', ' '))
                self.wlogsent(invited_ip, invited_port,
                              final_mssg.replace('\r\n', ' '))
                self.wfile.write(bytes(final_mssg, 'utf-8'))

        elif validez_ip == 'no valida':
            print("Valor de IP no válida")
            response = 'SIP/2.0 400 Bad Request\r\n\r\n'
            self.wfile.write(bytes(response, 'utf-8'))
            self.logfile('Error: Not a valid IP')

        registerfile = self.xml_dicc['database']['path']
        self.json2registered(registerfile, self.client_dicc)
        self.timeout()
        print('----------- USUARIOS REGISTRADOS EN ESTE MOMENT0 -----------')
        print(self.client_dicc)
        print('\r\n')

if __name__ == "__main__":
    print("------------ MAIN DEL PROXY -------------")

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
    print("Server " + proxy_name + " listening at port " +
          str(proxy_port) + "...")

    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        prox.logfile("Finishing...")
        print("Proxy_registrar terminado")
