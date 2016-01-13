#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
import os
import time
import xml.etree.ElementTree as ET



class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
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

    dicc = {}
    def handle(self):
        IP = self.client_address[0]
        PUERTO = self.client_address[1]
        while 1:
            line = self.rfile.read()
            if not line:
                break
            linea = line.decode('utf-8')
            lista = linea.split()
            print(lista)

            if 'Content-Type:' in lista:
                info_user = {}
                info_user['puerto'] = lista[14]
                info_user['ip'] = lista[10]
                self.dicc[lista[1].split(':')[1]] = info_user
                print(self.dicc)


            if 'INVITE' in lista:
                self.date_time(linea, 'receive', IP, PUERTO)
                msn = ('Content-Type: application/sdp' + '\r\n\r\n' + 'v=0' + '\r\n'
                      + 'o=' + list['account']['username'] + ' ' + list['uaserver']['ip'] + '\r\n'
                      + 's=misesion' + '\r\n' + 't=0' + '\r\n' + 'm=audio '
                      + list['rtpaudio']['puerto'] + ' ' + 'RTP' + '\r\n' )
                LINE = ('SIP/2.0 100 Trying'
                      + '\r\n\r\n' + 'SIP/2.0 180 Ring'
                      + '\r\n\r\n' + 'SIP/2.0 200 OK' + '\r\n' + msn
                      + '\r\n')
                self.wfile.write(bytes(LINE, 'utf-8'))
                self.date_time(LINE, 'send', IP, PUERTO)


            elif 'ACK' in lista:
                self.date_time(linea, 'receive', IP, PUERTO)
                login = lista[1].split(':')[1]
                rtp_msn = './mp32rtp -i ' + self.dicc[login]['ip'] + ' -p ' + self.dicc[login]['puerto']
                rtp_msn = rtp_msn + ' < ' + list['audio']['path']
                os.system(rtp_msn)

            elif 'BYE' in lista:
                self.date_time(linea, 'receive', IP, PUERTO)
                LINE = 'SIP/2.0 200 OK'+ '\r\n\r\n'
                self.wfile.write(bytes(LINE, 'utf-8'))
                self.date_time(LINE, 'send', IP, PUERTO)

if __name__ == "__main__":

    if len(sys.argv) != 2:
        sys.exit('Usage: python3 uaserver.py config')
    else:
        print('Listening...')

    tree = ET.parse(sys.argv[1])
    root = tree.getroot()
    list = {}
    for child in root:
        list[child.tag] = child.attrib

    serv = socketserver.UDPServer(('', int(list['uaserver']['puerto'])), EchoHandler)
    serv.serve_forever()
