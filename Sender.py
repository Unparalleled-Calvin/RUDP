import sys
import getopt
import math
import time
import base64

import Checksum
import BasicSender

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False, sackMode=False, timeout=0.5):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.sackMode = sackMode
        self.payload = 1024 #正文长度不超过1024
        self.winlen = 5
        self.base = 0 #窗口为[base, base+5)
        self.seqno = 0 #下一个要发的seqno
        self.timeout = timeout
        self.packets = [] #存储所有要发的包
    
    #重写send，发送字节类型
    def send(self, message, address=None):
        if address is None:
            address = (self.dest,self.dport)
        self.sock.sendto(message, address)

    #重写make_packet，返回字节类型
    def make_packet(self,msg_type,seqno,msg):
        body = "{}|{}|".format(msg_type,seqno).encode() + msg + "|".encode()
        checksum = Checksum.generate_checksum(body).encode()
        packet = body + checksum
        # print(packet)
        return packet
    
    #读入文件内容，构建所有要发送的包存入self.packets，初始化计时器列表
    def gen_all_packets(self):
        file_content = self.infile.read()
        file_length = len(file_content)
        self.infile.close()
        fragments = [
            base64.encodebytes(file_content[i*self.payload:(i+1)*self.payload if (i+1)*self.payload<file_length else file_length])
                for i in range(math.ceil(file_length/self.payload))
        ]
        if len(fragments) == 1:
            fragments.append("".encode())
        packets = []
        for seqno in range(len(fragments)):
            if seqno == 0:
                packets.append(self.make_packet("start",seqno,fragments[seqno]))
            elif seqno < len(fragments)-1:
                packets.append(self.make_packet("data",seqno,fragments[seqno]))
            else:
                packets.append(self.make_packet("end",seqno,fragments[seqno]))
        self.packets = packets
        self.length = len(packets)

    #Main sending loop.
    def start(self):
        self.gen_all_packets() #生成所有要发送的包
        ack = 0
        acks = [0 for i in range(self.length)]
        timers = [0 for i in range(self.length)]
        while ack != self.length:
            while self.seqno < self.base + self.winlen and self.seqno < self.length: #一次性将seqno到窗口末端的无ack的包全部发完
                if (self.sackMode and acks[self.seqno] == 0) or not self.sackMode:
                    timers[self.seqno] = time.time()
                    self.send(self.packets[self.seqno])
                    if self.debug:
                        print("Sender.py: send seqno={} timer={}".format(self.seqno, timers[self.seqno]))
                self.seqno += 1
            for seqno in range(self.base, self.seqno): #轮询检查超时情况
                now = time.time()
                try:
                    if (self.sackMode and acks[seqno] == 0) or not self.sackMode: #sackMode下仅对已发送未收到ack的包进行超时检查
                        if now - timers[seqno] >= self.timeout:
                            self.handle_timeout(seqno)
                            break
                except IndexError:
                    break
            message = self.receive(self.timeout) #防止ack丢包
            if message != None:
                message = message.decode()
                msg_type, ack_data, data, checksum = self.split_packet(message)
                if not Checksum.validate_checksum(message):
                    continue
                if self.debug:
                    print("Sender.py: received {}|{}|{}|{}".format(msg_type, ack, data[:5], checksum))
                if msg_type == "ack":
                    ack = int(ack_data)
                elif msg_type == "sack":
                    ack_data = ack_data.split(";")
                    ack = int(ack_data[0])
                    acks[ack-1] = 1
                    try:
                        sacks = [int(i) for i in ack_data[1].split(",")]
                        for sack in sacks:
                            acks[sack] = 1
                    except ValueError: #没有sack，int解析""失败
                        pass 
                if ack >= self.base: #ack在窗口内
                    self.handle_new_ack(ack)
                else: #ack不在窗口内
                    self.handle_dup_ack()
                    
        
    def handle_timeout(self, seqno):
        if self.debug:
            print("seqno={} timeout!".format(seqno))
        self.seqno = seqno #seqno处超时，那下次就从seqno处开始发

    def handle_new_ack(self, ack):
        if self.debug:
            print("Sender.py: received ack={} when base={} ".format(ack, self.base), end="")
        self.base = ack
        if self.debug:
            print("now base={}".format(self.base))

    def handle_dup_ack(self, ack):
        pass

    def log(self, msg):
        if self.debug:
            print(msg)


'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print("RUDP Sender")
        print("-f FILE | --file=FILE The file to transfer; if empty reads from STDIN")
        print("-p PORT | --port=PORT The destination port, defaults to 33122")
        print("-a ADDRESS | --address ADDRESS The receiver address or hostname, defaults to localhost")
        print("-t TIMEOUT| --timeout TIMEOUT The maximum time for waitting")
        print("-d | --debug Print debug messages")
        print("-h | --help Print this usage message")
        print("-k | --sack Enable selective acknowledgement mode")

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "f:p:a:t:dk", ["file=", "port=", "address=", "timeout=", "debug=", "sack="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    timeout = 0.5
    debug = False
    sackMode = False

    for o,a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True
        elif o in ("-t", "--timeout="):
            timeout = float(a)
        elif o in ("-k", "--sack="):
            sackMode = True

    s = Sender(dest, port, filename, debug, sackMode, timeout)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
