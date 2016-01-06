#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
import os
import xml.etree.ElementTree as ET


class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """

    def handle(self):
        while 1:
            line = self.rfile.read()
            if not line:
                break
            linea = line.decode('utf-8')
            lista = linea.split()
            recpt_port = list[2]['puerto']
            recpt_ip = list[1]['ip']
            if lista[0] == 'INVITE' or lista[0] == 'ACK' or lista[0] == 'BYE':
                pass
            else:
                self.wfile.write(b'SIP/2.0 405 Method Not Allowed')
                break

            if (not 'sip' in lista[1].split(':') or
                  not 'SIP/2.0' in lista or not '@' in lista[1]):
                self.wfile.write(b'SIP/2.0 400 Bad Request')
                break

            if 'INVITE' in lista:
                msn = ('Content-Type: application/sdp' + '\r\n\r\n' + 'v=0' + '\r\n'
                      + 'o=' + list[0]['username'] + ' ' + list[1]['ip'] + '\r\n'
                      + 's=misesion' + '\r\n' + 't=0' + '\r\n' + 'm=audio '
                      + list[2]['puerto'] + ' ' + 'RTP' + '\r\n' )
                self.wfile.write(b'SIP/2.0 100 Trying'
                + b'\r\n\r\n'+ b'SIP/2.0 180 Ring'
                + b'\r\n\r\n' + bytes('SIP/2.0 200 OK' + '\r\n' + msn ,'utf-8')
                + b'\r\n\r\n')

            elif 'ACK' in lista:
                print('\r\n\r\n' + linea + '\r\n\r\n')
                aEjecutar = './mp32rtp -i ' + recpt_ip + ' -p ' + recpt_port
                aEjecutar = aEjecutar + ' < ' + list[5]['path']
                print('Vamos a ejecutar', aEjecutar)
                os.system(aEjecutar)

            elif 'BYE' in lista:
                self.wfile.write(b'SIP/2.0 200 OK'+ b'\r\n\r\n')


if __name__ == "__main__":

    if len(sys.argv) != 2:
        sys.exit('Usage: python3 uaserver.py config')
    else:
        print('Listening...')

    tree = ET.parse(sys.argv[1])
    root = tree.getroot()
    list = []
    for child in root:
        list.append(child.attrib)

    serv = socketserver.UDPServer(('', int(list[1]['puerto'])), EchoHandler)
    serv.serve_forever()
