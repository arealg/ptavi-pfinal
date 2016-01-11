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


    dicc = {}
    def handle(self):
        while 1:
            line = self.rfile.read()
            if not line:
                break
            linea = line.decode('utf-8')
            lista = linea.split()
            if lista[0] == 'INVITE' or lista[0] == 'ACK' or lista[0] == 'BYE':
                pass
            else:
                self.wfile.write(b'SIP/2.0 405 Method Not Allowed')
                break

            if (not 'sip' in lista[1].split(':') or
                  not 'SIP/2.0' in lista or not '@' in lista[1]):
                self.wfile.write(b'SIP/2.0 400 Bad Request')
                break

            if 'Content-Type:' in lista:
                info_user = {}
                info_user['puerto'] = lista[11]
                info_user['ip'] = lista[7]
                self.dicc[lista[1].split(':')[1]] = info_user

            if 'INVITE' in lista:
                msn = ('Content-Type: application/sdp' + '\r\n\r\n' + 'v=0' + '\r\n'
                      + 'o=' + list['account']['username'] + ' ' + list['uaserver']['ip'] + '\r\n'
                      + 's=misesion' + '\r\n' + 't=0' + '\r\n' + 'm=audio '
                      + list['rtpaudio']['puerto'] + ' ' + 'RTP' + '\r\n' )
                LINE = ('SIP/2.0 100 Trying'
                      + '\r\n\r\n' + 'SIP/2.0 180 Ring'
                      + '\r\n\r\n' + 'SIP/2.0 200 OK' + '\r\n' + msn
                      + '\r\n\r\n')
                self.wfile.write(bytes(LINE, 'utf-8'))

            elif 'ACK' in lista:
                print(self.dicc)
                login = lista[1].split(':')[1]
                print('\r\n\r\n' + linea + '\r\n\r\n')
                rtp_msn = './mp32rtp -i ' + self.dicc[login]['ip'] + ' -p ' + self.dicc[login]['puerto']
                rtp_msn = rtp_msn + ' < ' + list['audio']['path']
                os.system(rtp_msn)

            elif 'BYE' in lista:
                self.wfile.write(b'SIP/2.0 200 OK'+ b'\r\n\r\n')


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
