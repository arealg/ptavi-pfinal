#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
import xml.etree.ElementTree as ET
import hashlib
import datetime



if len(sys.argv) != 4:
    sys.exit('Usage: python3 uaclient.py config method option')

tree = ET.parse(sys.argv[1])
root = tree.getroot()

list = []

for child in root:
    list.append(child.attrib)

port_serv = list[1]['puerto']
METODO = sys.argv[2]
IP = list[3]['ip']
PORT = int(list[3]['puerto'])

# def date_time (x):
#     fecha = '%s%s%s%s%s%s'%(x.year,x.month,x.day,x.hour,x.minute,x.second)

try:
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP, PORT))

    if METODO == 'REGISTER':
        LOGIN = list[0]['username']
        LINE = METODO + ' ' + 'sip:' + LOGIN + ':' + port_serv + ' ' + 'SIP/2.0' + '\r\n'
        EXPIRES = sys.argv[3]
        LINE = LINE + 'Expires: ' + EXPIRES
        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n\r\n')
        data = my_socket.recv(1024)


    elif METODO == 'INVITE':
        LOGIN = sys.argv[3]
        msn = ('Content-Type: application/sdp' + '\r\n\r\n' + 'v=0' + '\r\n'
              + 'o=' + list[0]['username'] + ' ' + list[1]['ip'] + '\r\n'
              + 's=misesion' + '\r\n' + 't=0' + '\r\n' + 'm=audio '
              + list[2]['puerto'] + ' ' + 'RTP' + '\r\n' )
        LINE = METODO + ' ' + 'sip:' + LOGIN + ':' + ' SIP/2.0' + '\r\n' + msn
        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
        data = my_socket.recv(1024)


    print(data.decode('utf-8'))
    response_msg = data.decode('utf-8')

    if '401 Unauthorized' in response_msg:
        nonce = bytes(response_msg.split()[5].split('=')[1],'utf-8')
        passwd = bytes(list[0]['passwd'],'utf-8')
        m = hashlib.md5()
        m.update(passwd + nonce)
        response = m.hexdigest()
        LINE = LINE +  '\r\n' + 'Authorization:' + 'response=' + response
        my_socket.send(bytes(LINE,'utf-8'))
        data = my_socket.recv(1024)
        print(data.decode('utf-8'))


    elif ('100 Trying' in response_msg and '180 Ring' in response_msg
        and '200 OK' in response_msg):
        my_socket.send(bytes('ACK' + ' ' + 'sip:' + LOGIN + ' '
                       + 'SIP/2.0', 'utf-8')
                       + b'\r\n')
        data = my_socket.recv(1024)
        print(data.decode('utf-8'))

except ConnectionRefusedError:
    x = datetime.datetime.now()
    print('Not connect at server_port')
    outfile = open('log.txt', 'w')
    fecha = '%s%s%s%s%s%s'%(x.year,x.month,x.day,x.hour,x.minute,x.second)
    outfile.write(fecha)
    outfile.close()

my_socket.close()
