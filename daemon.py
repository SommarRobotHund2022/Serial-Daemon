#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# autopep8 -i

import serial
import serial.tools.list_ports
import queue
import threading
import time
import sys
import zmq

context = zmq.Context()
pub_sock = context.socket(zmq.PUB)
pub_sock.bind("tcp://127.0.0.1:2271")

rep_sock = context.socket(zmq.REP)
rep_sock.bind("tcp://127.0.0.1:2272")

BAUDRATE = 115200
TIMEOUT = 1


DEBUG_MODE = ('--debug' in sys.argv) | False
DO_ECHO = ('--echo' in sys.argv) | False

TOKENS = ['k', 'c', 'm', 'M', 'u', 'b', 'h', 'j', 'd', 'p', 'g', 'a', 's', 'r']

def timestamp():
    return '[' + time.ctime(time.time()) + ']'

def log(*s, t='I'):
    print(f'{timestamp()} [{t}]', *s)

def log_d(*s, t='I'):
    if DEBUG_MODE:
        print(f'{timestamp()} [DEBUG] [{t}]', *s)




class OpenCatSerialConnection:
    def __init__(self, port='/dev/ttyUSB0', max_read_buffer=0, encoding='utf-8', baud=BAUDRATE):
        self.__timeout = TIMEOUT
        self.__serial_to_port = None
        self.__baud = baud
        try:
            self.serial_to_port = serial.Serial(port, self.__baud, timeout=TIMEOUT)
        except:
            raise Exception("No port found!")

            
        self.__encoding         = encoding
        self.write_queue        = queue.Queue(max_read_buffer)
        self.read_queue         = queue.Queue(max_read_buffer)
        self.read_queue_raw     = queue.Queue(max_read_buffer)
        self.__aq               = queue.LifoQueue(max_read_buffer)

        self.__stop_bkw_event   = threading.Event()        
        self.__wire_lock        = threading.Lock()
        self.stats              = { 'ack_success': 0, 'ack_failed': 0, 'r_cycles': 0, 'w_cycles': 0}

        self.__bkw_w            = threading.Thread(target=self.__wq_worker, daemon=True)
        self.__bkw_r            = threading.Thread(target=self.__rq_worker, daemon=True)
        self.__bkw_stats        = threading.Thread(target=self.__stat_worker, args=(60,), daemon=True)

        # bkw stand for 'burger king worker' not 'background worker'
        self.__bkw_w.start()
        self.__bkw_r.start()
        self.__bkw_stats.start()

    # __init__


    def __del__(self):
        try:
            self.__stop_bkw_event.set()
            self.__bkw_w.join()
            self.__bkw_r.join()
            self.__bkw_stats.join()
        except Exception as e:
            print(e)
        finally:
            log_d('BKW killed')
        
        log_d('serial closed')
    # __del__


    def __wq_worker(self):
        while not self.__stop_bkw_event.is_set():
            time.sleep(0.01)
            
            self.stats['w_cycles'] += 1
            
            if self.write_queue.empty():
                continue
                
            task = self.write_queue.get()
            
            self.__wire_lock.acquire()
            try:
                self.serial_to_port.write(task.encode(self.__encoding))
                
            finally:
                self.__wire_lock.release()
            
            if task[0] in TOKENS:
                    self.__aq.put(task[0])
                    
            log_d('SEND TASK: ', task)
    # __wq_worker

    def __rq_worker(self):
        while not self.__stop_bkw_event.is_set():
            time.sleep(0.01)

            self.stats['r_cycles'] += 1

            self.__wire_lock.acquire()
            res = ""
            try:
                res = self.serial_to_port.readline().decode(self.__encoding).rstrip()
            finally:
                self.__wire_lock.release()

            if res == '':
                continue
            if DO_ECHO:
                pass
            log_d(f'Got {res}')

            self.read_queue_raw.put(res)
            if len(res) == 1 and res in TOKENS:
                if self.__aq.empty():
                    self.stats['ack_failed'] += 1
                    log_d(f'ACK failure! got {res} but none was expected!')
                    continue

                ack = self.__aq.get()
                if res == ack:
                    self.stats['ack_success'] += 1
                    log(f'ACK success on command {ack}')
                else:
                    self.stats['ack_failed'] += 1
                    log(f'ACK failure! got {res}, expected {ack}', t='W')
            else:    
                self.read_queue.put(res)
    # __rq_worker

    def __stat_worker(self, delay = 10):
        while True:
            log('Statistics:')
            for k in self.stats:
                print(f'    {k}: {self.stats[k]}')
            time.sleep(delay)


    def queue_task(self, task):
        self.write_queue.put(task)
    # queue_task        


    def read(self):
       pass
    # read


def pub_read_queue(conn: OpenCatSerialConnection):
    while True:
        if not conn.read_queue.empty():
            pub_sock.send_string(conn.read_queue.get())
#pub_read_queue

def recv_write_queue(conn: OpenCatSerialConnection):
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
        sc = OpenCatSerialConnection()
        t1 = threading.Thread(target=pub_read_queue, args=(sc,), daemon=True)
        t2 = threading.Thread(target=recv_write_queue, args=(sc,), daemon=True)
        t1.start()
        t2.start()
        while True:
            x = input('')
            sc.queue_task(x)
    except KeyboardInterrupt:
        del sc
        print('\n\nstop')
