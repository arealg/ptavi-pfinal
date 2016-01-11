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
import hashlib


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

    def date_time(self, linea, opcion, IP, PORT):
        fichero = list['log']['path']
        outfile = open(fichero, 'a')
        fecha = time.strftime('%Y%m%d%H%M%S' , time.gmtime())
        linea = linea.replace('\r\n\r\n', ' ')
        linea = linea.replace('\r\n', ' ')
        if opcion == 'send':
            linea = 'Send to ' + IP + ':' + str(PORT) + ': ' + linea
        elif opcion == 'receive':
            linea = 'Received from ' + IP + ':' + str(PORT) + ': ' + linea
        fecha = fecha + ' ' + linea + '\n'
        outfile.write(fecha)
        outfile.close()

    def msn2clientserver (self, lista, linea, ip, puerto):
        user = lista[1].split(':')[1]

        if user in self.dicc:
            PORT = int(self.dicc[user]['puerto'])
            IP = self.dicc[user]['address']
            self.date_time(linea, 'receive', IP, PORT)
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((IP, PORT))
            self.date_time(linea, 'send', IP, PORT)
            my_socket.send(bytes(linea, 'utf-8') + b'\r\n')
            data = my_socket.recv(1024)
            return data
            my_socket.close()
        else:
            LINE = ("SIP/2.0 404 Not Found (User not found)" + '\r\n')
            self.date_time(LINE, 'send', ip, puerto)
            self.wfile.write(bytes(LINE,'utf-8'))


    dicc_passwd = {}
    def open_passwd(self):
        with open('passwd.json', 'r') as fich:
            fichero = json.loads(fich.read())
            self.dicc_passwd = fichero

    def response_equal(self, login):
        self.open_passwd()
        passwd = bytes(self.dicc_passwd[login]['passwd'], 'utf-8')
        nonce = bytes(self.dicc_passwd[login]['nonce'], 'utf-8')
        m = hashlib.md5()
        m.update(passwd + nonce)
        resp_proxy = m.hexdigest()
        return resp_proxy

    def not_login (self, login, expires, ip, puerto):
        if expires == '0' and not login in self.dicc:
            LINE = ("SIP/2.0 404 Not Found (User not found)" + '\r\n')
            self.date_time(LINE, 'send', ip, puerto)
            self.wfile.write(bytes(LINE,'utf-8'))
            return True

    def error(self, ip, PUERTO, puerto):
        try:
            puerto = int(puerto)
            ip = ip.split('.')
            for i in ip:
                int(i)
        except:
            LINE = ("SIP/2.0 400 Bad Request" + '\r\n')
            self.date_time(LINE, 'send', ip, PUERTO)
            self.wfile.write(bytes(LINE,'utf-8'))
            return True


    def handle(self):
        """
        Se identifica al cliente y se registra en un diccionario.
        """
        self.json2registered()
        ip = self.client_address[0]
        PUERTO = self.client_address[1]
        # print("{} {}".format(IP, PUERTO))
        while 1:
            line = self.rfile.read()
            if not line:
                break
            linea = line.decode('utf-8')
            lista = linea.split()
            self.date_time('Starting...', '', ip, PUERTO)
            if 'REGISTER' in lista:
                print(lista)
                login = lista[1].split(':')[1]
                puerto = lista[1].split(':')[2]
                expires = lista[4]
                self.date_time(linea, 'receive', ip, PUERTO)
                self.tiempo_exp()
                if not self.not_login(login, expires, ip, PUERTO) and not self.error(ip, PUERTO, puerto):
                    if len(lista) >= 6 and lista[5].split(':')[0] == 'Authorization':
                        response = lista[5].split(':')[1].split('=')[1]
                        resp_proxy= self.response_equal(login)
                        if resp_proxy == response:
                            self.wfile.write(b"SIP/2.0 200 OK" + b'\r\n\r\n')
                        else:
                            LINE = ("SIP/2.0 401 Unauthorized" + '\r\n')
                            self.date_time(LINE, 'send', IP, PUERTO)
                            self.wfile.write(bytes(LINE,'utf-8'))

                        if expires == '0':
                            if resp_proxy == response :
                                del self.dicc[login]
                    else:
                        nonce = str(random.randint(0,10**20))
                        self.open_passwd()
                        if login in self.dicc_passwd:
                            self.dicc_passwd[login]['nonce'] = nonce
                        with open('passwd.json', 'w') as file:
                            json.dump(self.dicc_passwd, file, sort_keys=True, indent=4)
                        LINE = ("SIP/2.0 401 Unauthorized" + '\r\n'
                               + 'WWWW Authenticate:'+ ' '+  'nonce=' + nonce  + '\r\n')
                        self.date_time(LINE, 'send', ip, PUERTO)
                        self.wfile.write(bytes(LINE,'utf-8'))
                        tiempo = time.time() + float(expires)
                        self.registrar_cliente(ip, login, tiempo, puerto)
                self.register2json()

            if 'INVITE' in lista:
                print(lista)
                login = lista[1].split(':')[1]
                if login in self.dicc:
                    data = self.msn2clientserver(lista, linea, ip, PUERTO)
                    if data != None:
                        self.wfile.write(data)
                else:
                    LINE = ("SIP/2.0 404 Not Found (User not found)" + '\r\n')
                    self.date_time(LINE, 'send', ip, puerto)
                    self.wfile.write(bytes(LINE,'utf-8'))

            elif 'ACK' in lista:
                self.msn2clientserver(lista, linea, ip, PUERTO)
            elif 'BYE' in lista:
                data = self.msn2clientserver(lista,linea, ip, PUERTO)
                self.wfile.write(data)


if __name__ == "__main__":

    tree = ET.parse(sys.argv[1])
    root = tree.getroot()
    list = {}
    for child in root:
        list[child.tag] = child.attrib
    puerto = list['server']['puerto']

    if len(sys.argv) != 2:
        sys.exit('Usage: python3 proxy_registrar.py config')
    else:
        print('Server MiServidorBigBang listening at port ' + puerto)

    serv = socketserver.UDPServer(('', int(puerto)), SIPRegisterHandler)
    serv.serve_forever()
