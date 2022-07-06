#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# autopep8 -i

import threading
import sys
import zmq
from OpenCatSerial import *


INTERACTIVE = ('--interactive' in sys.argv or '-i' in sys.argv) | False
NO_NETWORK = ('--no-net' in sys.argv) | False
PORT = ''
if '--port' in sys.argv:
    i = sys.argv.index('--port') + 1
    try:
        PORT = sys.argv[i]
    except:
        PORT = '/dev/ttyS0'
else:
    PORT = '/dev/ttyS0'

if not NO_NETWORK:
    context = zmq.Context()
    pub_sock = context.socket(zmq.PUB)
    pub_sock.bind("tcp://127.0.0.1:2271")

    rep_sock = context.socket(zmq.REP)
    rep_sock.bind("tcp://127.0.0.1:2272")



def pub_read_queue(conn):
    while True:
        if not conn.read_queue.empty():
            print("sending")
            pub_sock.send_string(conn.read_queue.get())
#pub_read_queue

def recv_write_queue(conn):
    while True:
        try:
            conn.queue_task(rep_sock.recv().decode('utf-8'))
            print('command recv')
        except:
            rep_sock.send_string('failure')
        finally:
            rep_sock.send_string('success')
#pub_read_queue

if __name__ == '__main__':
    try:
        print('start')
        
        sc = None
        try:
            sc = OpenCatSerialConnection(PORT, max_read_buffer=16)
            print("Found port:", PORT)
        except:
            print('Not OpenCat found on', PORT)
            exit(1)
            
        if not NO_NETWORK:
            t1 = threading.Thread(target=pub_read_queue, args=(sc,), daemon=True)
            t2 = threading.Thread(target=recv_write_queue, args=(sc,), daemon=True)
            t1.start()
            t2.start()

        while True:
            if INTERACTIVE:
                x = input('')
                sc.queue_task(x)
    
    except KeyboardInterrupt:
        del sc
        print('\n\nstop')
