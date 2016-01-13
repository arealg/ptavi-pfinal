#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
import xml.etree.ElementTree as ET
import hashlib
import time
import os




if len(sys.argv) != 4:
    sys.exit('Usage: python3 uaclient.py config method option')


tree = ET.parse(sys.argv[1])
root = tree.getroot()
list = {}
for child in root:
    list[child.tag] = child.attrib

port_serv = list['uaserver']['puerto']
METODO = sys.argv[2]
IP = list['regproxy']['ip']
PORT = int(list['regproxy']['puerto'])

def date_time(linea, opcion, IP, PORT):
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

date_time('Starting...', '', IP, PORT)

try:
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP, PORT))


    if METODO == 'REGISTER':
        LOGIN = list['account']['username']
        EXPIRES = sys.argv[3]
        LINE = METODO + ' ' + 'sip:' + LOGIN + ':' + port_serv + ' ' + 'SIP/2.0' + '\r\n'
        LINE = LINE + 'Expires: ' + EXPIRES
        date_time(LINE, 'send', IP, PORT)
        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n\r\n')
        data = my_socket.recv(1024)
        date_time(data.decode('utf-8'), 'receive', IP, PORT)


    elif METODO == 'INVITE':
        LOGIN = sys.argv[3]
        msn = ('Content-Type: application/sdp' + '\r\n\r\n' + 'v=0' + '\r\n'
              + 'o=' + list['account']['username'] + ' ' + list['uaserver']['ip'] + '\r\n'
              + 's=misesion' + '\r\n' + 't=0' + '\r\n' + 'm=audio '
              + list['rtpaudio']['puerto'] + ' ' + 'RTP' + '\r\n' )

        LINE = METODO + ' ' + 'sip:' + LOGIN + ' SIP/2.0' + '\r\n' + msn
        date_time(LINE, 'send', IP, PORT)
        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
        data = my_socket.recv(1024)
        date_time(data.decode('utf-8'), 'receive', IP, PORT)

    elif METODO == 'BYE':
        LOGIN = sys.argv[3]
        LINE = 'BYE' + ' ' + 'sip:' + LOGIN + ' ' + 'SIP/2.0' + '\r\n'
        date_time(LINE, 'send', IP, PORT)
        my_socket.send(bytes(LINE,'utf-8'))
        data = my_socket.recv(1024)
        date_time(data.decode('utf-8'), 'receive', IP, PORT)

    response_msg = data.decode('utf-8')


    if '401 Unauthorized' in response_msg:
        date_time(response_msg, 'receive', IP, PORT)
        nonce = bytes(response_msg.split()[5].split('=')[1].strip('"'),'utf-8')
        passwd = bytes(list['account']['passwd'],'utf-8')
        m = hashlib.md5()
        m.update(passwd + nonce)
        response = m.hexdigest()
        LINE = LINE +  '\r\n' + 'Authorization: Digest response=' + '"' + response + '"'
        date_time(LINE, 'send', IP, PORT)
        my_socket.send(bytes(LINE,'utf-8'))
        data = my_socket.recv(1024)
        print(data.decode('utf-8'))


    elif ('100 Trying' in response_msg and '180 Ring' in response_msg
        and '200 OK' in response_msg):
        ip = response_msg.split(' ')[8].split('\r\n')[0]
        puerto = response_msg.split(' ')[9]
        date_time(response_msg, 'receive', IP, PORT)
        LINE = 'ACK' + ' ' + 'sip:' + LOGIN + ' ' + 'SIP/2.0' + '\r\n'
        my_socket.send(bytes(LINE,'utf-8'))
        print('Enviando RTP')
        rtp_msn = './mp32rtp -i ' +ip + ' -p ' + puerto
        rtp_msn = rtp_msn + ' < ' + list['audio']['path']
        os.system(rtp_msn)
        date_time(LINE, 'send', IP, PORT)
        data = my_socket.recv(1024)


    my_socket.close()

except ConnectionRefusedError:
    linea = ' Error: No server listening at'
    date_time(linea, '', IP, PORT)
    sys.exit('No server listening')

my_socket.close()
