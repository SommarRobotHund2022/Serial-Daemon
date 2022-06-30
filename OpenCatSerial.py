import serial
import queue
import threading
import time
import sys
from logging import *

DO_ECHO = ('--echo' in sys.argv or '-e' in sys.argv)            | False

BAUDRATE = 115200
TIMEOUT = 1

TOKENS = ['k', 'c', 'm', 'M', 'u', 'b', 'h', 'j', 'd', 'p', 'g', 'a', 's', 'r']


class OpenCatSerialConnection:
    def __init__(self, port, max_read_buffer=0, encoding='utf-8', baud=BAUDRATE,timeout=TIMEOUT):
        
        self.__serial_port = serial.Serial(port, baud, timeout=timeout)
            
        self.__encoding         = encoding
        self.write_queue        = queue.Queue()
        self.read_queue         = queue.LifoQueue()
        self.read_queue_raw     = queue.LifoQueue()
        self.__aq               = queue.LifoQueue()

        self.__stop_bkw_event   = threading.Event()        
        self.__wire_lock        = threading.Lock()
        self.stats              = { 'ack_success': 0, 'ack_failed': 0, 'r_cycles': 0, 'w_cycles': 0}

        self.__bkw_w            = threading.Thread(target=self.__wq_worker, daemon=True)
        self.__bkw_r            = threading.Thread(target=self.__rq_worker, daemon=True)
        self.__bkw_stats        = threading.Thread(target=self.__stat_worker, args=(5,), daemon=True)

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
            
            self.stats['w_cycles'] += 1
            
            if self.write_queue.empty():
                continue
                
            task = self.write_queue.get()
            
            #self.__wire_lock.acquire()
            try:
                self.__serial_port.write(task.encode(self.__encoding))
                
            finally:
                pass
                #self.__wire_lock.release()
            
            if task[0] in TOKENS:
                    self.__aq.put(task[0])
                    
            log_d('SEND TASK: ', task)
    # __wq_worker

    def __rq_worker(self):
        while not self.__stop_bkw_event.is_set():

            self.stats['r_cycles'] += 1

            #self.__wire_lock.acquire()
            res = ""
            try:
                res = self.__serial_port.readline().decode(self.__encoding).rstrip()
            except:
                log_d('Weåird')
            finally:
                pass
                #self.__wire_lock.release()

            if res == '':
                continue
            if DO_ECHO:
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
            log(f'Queue size: {self.read_queue.qsize()}')
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