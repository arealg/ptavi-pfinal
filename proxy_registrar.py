#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
import json
import time
import xml.etree.ElementTree as ET
import random
import socket




class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """
    SIP Register Handler
    """
    dicc = {}

    def register2json(self):
        """
        Se registra al cliente en un fichero json.
        """
        with open('registered.json', 'w') as file:
            json.dump(self.dicc, file, sort_keys=True, indent=4)

    def registrar_cliente(self, IP, login, tiempo, puerto):
        """
        Se añade al cliente con un Address y Expires en un diccionario.
        """
        lista_info = {}
        lista_info['address'] = IP
        lista_info['expires'] = (time.strftime('%Y-%m-%d %H:%M:%S +0100',
                                 time.localtime(tiempo)))
        lista_info['puerto'] = puerto
        self.dicc[login] = lista_info

    def tiempo_exp(self):
        lista_user = []
        for login in self.dicc:
            exp = time.strptime(self.dicc[login]['expires'],
                                '%Y-%m-%d %H:%M:%S +0100')
            if time.time() >= time.mktime(exp):
                lista_user.append(login)
        for login in lista_user:
                del self.dicc[login]

    def json2registered(self):
        """
        Se mira si hay un fichero registered.json.
        """
        try:
            with open('registered.json', 'r') as fich:
                fichero = json.loads(fich.read())
                self.dicc = fichero
        except:
            pass

    def msn_invite (self,lista,linea):
        user = lista[1].split(':')[1]
        if user in self.dicc:
            PORT = int(self.dicc[user]['puerto'])
            IP = self.dicc[user]['address']
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((IP, PORT))
        my_socket.send(bytes(linea, 'utf-8') + b'\r\n')
        data = my_socket.recv(1024)
        print(data.decode('utf-8'))
        self.wfile.write(data)

    def msn_ack (self, lista, linea):
        user = lista[1].split(':')[1]
        if user in self.dicc:
            PORT = int(self.dicc[user]['puerto'])
            IP = self.dicc[user]['address']
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((IP, PORT))
        my_socket.send(bytes(linea, 'utf-8') + b'\r\n')

    def handle(self):
        """
        Se identifica al cliente y se registra en un diccionario.
        """
        self.json2registered()
        IP = self.client_address[0]
        PUERTO = self.client_address[1]
        # print("{} {}".format(IP, PUERTO))
        while 1:
            line = self.rfile.read()
            if not line:
                break
            linea = line.decode('utf-8')
            lista = linea.split()
            if 'REGISTER' in lista:
                if len(lista) >= 6:
                    self.wfile.write(b"SIP/2.0 200 OK" + b'\r\n\r\n')
                else:
                    puerto = lista[1].split(':')[2]
                    expires = lista[4]
                    login = lista[1].split(':')[1]
                    self.tiempo_exp()
                    if expires == '0':
                        if login in self.dicc:
                            del self.dicc[login]
                            self.wfile.write(b"SIP/2.0 200 OK" + b'\r\n\r\n')
                        else:
                            self.wfile.write(b"SIP/2.0 200 OK" + b'\r\n\r\n')
                    else:
                        nonce = str(random.randint(0,10**20))
                        self.wfile.write(b"SIP/2.0 401 Unauthorized" + b'\r\n'
                        + bytes('WWWW Authenticate:'+ ' '+  'nonce=' + nonce , 'utf-8') + b'\r\n')
                        tiempo = time.time() + float(expires)
                        self.registrar_cliente(IP, login, tiempo, puerto)
                self.register2json()
            if 'INVITE' in lista:
                self.msn_invite(lista,linea)
            elif 'ACK' in lista:
                self.msn_ack(lista,linea)


if __name__ == "__main__":

    tree = ET.parse(sys.argv[1])
    root = tree.getroot()

    list = []

    for child in root:
        list.append(child.attrib)

    puerto = list[0]['puerto']

    if len(sys.argv) != 2:
        sys.exit('Usage: python3 proxy_registrar.py config')
    else:
        print('Server MiServidorBigBang listening at port ' + puerto)

    serv = socketserver.UDPServer(('', int(puerto)), SIPRegisterHandler)
    serv.serve_forever()
