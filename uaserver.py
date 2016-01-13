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
from proxy_registrar import date_time


class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """

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

            if 'Content-Type:' in lista:
                info_user = {}
                info_user['puerto'] = lista[14]
                info_user['ip'] = lista[10]
                self.dicc[lista[1].split(':')[1]] = info_user


            if 'INVITE' in lista:
                date_time(list, linea, 'receive', IP, PUERTO)
                msn = ('Content-Type: application/sdp' + '\r\n\r\n' + 'v=0' + '\r\n'
                      + 'o=' + list['account']['username'] + ' ' + list['uaserver']['ip'] + '\r\n'
                      + 's=misesion' + '\r\n' + 't=0' + '\r\n' + 'm=audio '
                      + list['rtpaudio']['puerto'] + ' ' + 'RTP' + '\r\n' )
                LINE = ('SIP/2.0 100 Trying'
                      + '\r\n\r\n' + 'SIP/2.0 180 Ring'
                      + '\r\n\r\n' + 'SIP/2.0 200 OK' + '\r\n' + msn
                      + '\r\n')
                self.wfile.write(bytes(LINE, 'utf-8'))
                date_time(list, LINE, 'send', IP, PUERTO)


            elif 'ACK' in lista:
                date_time(list, linea, 'receive', IP, PUERTO)
                login = lista[1].split(':')[1]
                listen = 'cvlc rtp://@' + self.dicc[login]['ip'] + ':' + self.dicc[login]['puerto']
                listen = listen + ' 2> /dev/null &'
                os.system(listen)
                rtp_msn = './mp32rtp -i ' + self.dicc[login]['ip'] + ' -p ' + self.dicc[login]['puerto']
                rtp_msn = rtp_msn + ' < ' + list['audio']['path']
                os.system(rtp_msn)

            elif 'BYE' in lista:
                date_time(list, linea, 'receive', IP, PUERTO)
                LINE = 'SIP/2.0 200 OK'+ '\r\n\r\n'
                self.wfile.write(bytes(LINE, 'utf-8'))
                date_time(list, LINE, 'send', IP, PUERTO)

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
