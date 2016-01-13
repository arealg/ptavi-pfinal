#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Clase (y programa princIPal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
import json
import time
import xml.etree.ElementTree as ET
import random
import socket
import hashlib

def date_time(list, linea, opcion, IP, PORT):
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

    def cabecera_prox(self, linea, metodo):
        line = 'Via: SIP/2.0/UDP real.com;branch=z9hG4bK776asdhds'
        if metodo == 'send':
            linea = linea.split('\r\n')
            linea.insert(1, line)
            linea = '\r\n'.join(linea)
            return linea
        if metodo == 'recive':
            linea = linea.decode('utf-8')
            linea = linea.split('\r\n')
            if linea[0] == 'SIP/2.0 200 OK':
                linea.insert(1, line)
            else:
                linea.insert(5, line)
            linea = '\r\n'.join(linea)
            return linea

    dicc_bye = {}
    def msn2clientserver (self, lista, linea, IP, puerto):
        try:
            user = lista[1].split(':')[1]
            if user in self.dicc:
                PORT = int(self.dicc[user]['puerto'])
                IP = self.dicc[user]['address']
                date_time(list, linea, 'receive', IP, puerto)
                linea = self.cabecera_prox(linea, 'send')
                my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                my_socket.connect((IP, PORT))
                date_time(list, linea, 'send', IP, PORT)
                my_socket.send(bytes(linea, 'utf-8') + b'\r\n')
                data = my_socket.recv(1024)
                linea = self.cabecera_prox(data, 'recive')
                data = bytes(linea, 'utf-8')
                return data
                my_socket.close()
            else:
                LINE = ("SIP/2.0 404 Not Found (User not found)" + '\r\n')
                date_time(list, LINE, 'send', IP, puerto)
                self.wfile.write(bytes(LINE,'utf-8'))
        except ConnectionRefusedError:
            LINE = ("SIP/2.0 603 Decline" + '\r\n')
            date_time(list, LINE, 'send', IP, puerto)
            self.wfile.write(bytes(LINE,'utf-8'))
        except:
            pass

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


    def error(self, IP, PUERTO, lista, metodo):
        error = False
        try:
            if ('sip' in lista[1].split(':') and
                   'SIP/2.0' in lista and '@' in lista[1]):
                if metodo == 'REGISTER':
                    puerto = int(lista[1].split(':')[2])
                elif metodo == 'INVITE':
                    ip = lista[7]
                    for i in ip.split('.'):
                        int(i)
                elif metodo == 'BYE':
                    login = lista[1].split(':')[1]
                    if login in self.dicc_bye:
                        for i in self.dicc_bye:
                            if login == self.dicc_bye[i]:
                                log_borrar = i
                        del self.dicc_bye[login]
                        del self.dicc_bye[log_borrar]
                    else:
                        raise KeyError
            else:
                raise TypeError

        except KeyError:
            LINE = ("SIP/2.0 404 Not Found (User not found)" + '\r\n')

        except TypeError:
            LINE = ("SIP/2.0 400 Bad Request" + '\r\n')
            error = True
        except:
            LINE = ("SIP/2.0 400 Bad Request" + '\r\n')
            error = True
        if error :
            date_time(list, LINE, 'send', IP, PUERTO)
            self.wfile.write(bytes(LINE,'utf-8'))
            return error

    def handle(self):
        """
        Se identifica al cliente y se registra en un diccionario.
        """
        self.json2registered()
        IP = self.client_address[0]
        PUERTO = self.client_address[1]
        while 1:
            line = self.rfile.read()
            if not line:
                break
            linea = line.decode('utf-8')
            lista = linea.split()
            if (lista[0] == 'INVITE' or lista[0] == 'ACK' or
                lista[0] == 'BYE' or lista[0] == 'REGISTER'):
                pass
            else:
                LINE = 'SIP/2.0 405 Method Not Allowed'+'\r\n\r\n'
                self.wfile.write(bytes(LINE, 'utf-8'))
                date_time(list, LINE, 'send', IP, PUERTO)
            self.tiempo_exp()
            if 'REGISTER' in lista:
                if (not self.error(IP ,PUERTO, lista,'REGISTER')):
                    login = lista[1].split(':')[1]
                    puerto = lista[1].split(':')[2]
                    expires = lista[4]
                    date_time(list, linea, 'receive', IP, PUERTO)
                    if (len(lista) >= 7 and
                       lista[5].split(':')[0] == 'Authorization'):
                        response = lista[7].split('=')[1].strip('"')
                        resp_proxy= self.response_equal(login)
                        if resp_proxy == response:
                            self.wfile.write(b"SIP/2.0 200 OK" + b'\r\n\r\n')
                        else:
                            LINE = ("SIP/2.0 401 Unauthorized" + '\r\n')
                            date_time(list, LINE, 'send', IP, PUERTO)
                            self.wfile.write(bytes(LINE,'utf-8'))

                    else:
                        nonce = str(random.randint(0,10**20))
                        self.open_passwd()
                        if login in self.dicc_passwd:
                            self.dicc_passwd[login]['nonce'] = nonce
                        else:
                            LINE = ("SIP/2.0 404 Not Found (User not found)" )
                            LINE = LINE + '\r\n'
                            date_time(list, LINE, 'send', IP, PUERTO)
                            self.wfile.write(bytes(LINE,'utf-8'))
                        with open('passwd.json', 'w') as file:
                            json.dump(self.dicc_passwd, file, sort_keys=True,
                                      indent=4)
                        LINE = "SIP/2.0 401 Unauthorized" + '\r\n'
                        LINE = LINE + 'WWW-Authenticate: Digest '+  'nonce='
                        LINE = LINE + '"' + nonce + '"' + '\r\n\r\n'
                        date_time(list, LINE, 'send', IP, PUERTO)
                        self.wfile.write(bytes(LINE,'utf-8'))
                        tiempo = time.time() + float(expires)
                        self.registrar_cliente(IP, login, tiempo, puerto)
                self.register2json()

            elif 'INVITE' in lista:
                self.error(IP ,PUERTO, lista,'INVITE')
                login = lista[1].split(':')[1]
                origen = lista[6].split('=')[1]
                self.dicc_bye[login] = origen
                self.dicc_bye[origen] = login
                if login in self.dicc:
                    data = self.msn2clientserver(lista, linea, IP, PUERTO)
                    if data != None:
                        self.wfile.write(data)
                else:
                    LINE = ("SIP/2.0 404 Not Found (User not found)" + '\r\n')
                    date_time(list, LINE, 'send', IP, PUERTO)
                    self.wfile.write(bytes(LINE,'utf-8'))

            elif 'ACK' in lista:
                self.error(IP ,PUERTO, lista,'')
                self.msn2clientserver(lista, linea, IP, PUERTO)

            elif 'BYE' in lista:
                self.error(IP ,PUERTO, lista,'BYE')
                data = self.msn2clientserver(lista,linea, IP, PUERTO)
                if data != None:
                    self.wfile.write(data)


if __name__ == "__main__":

    tree = ET.parse(sys.argv[1])
    root = tree.getroot()
    list = {}
    for child in root:
        list[child.tag] = child.attrib
    puerto = list['server']['puerto']
    ip = list['server']['ip']
    date_time(list, 'Starting...', '', ip, puerto)

    if len(sys.argv) != 2:
        sys.exit('Usage: python3 proxy_registrar.py config')
    else:
        print('Server MiServidorBigBang listening at port ' + puerto)

    serv = socketserver.UDPServer(('', int(puerto)), SIPRegisterHandler)
    serv.serve_forever()
