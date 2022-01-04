import sys
import getopt
import math
import time

import Checksum
import BasicSender

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False, sackMode=False):
        super(Sender, self).__init__(dest, port, filename, debug)
        if sackMode:
            raise NotImplementedError #remove this line when you implement SACK
        self.payload = 1024 #正文长度不超过1024
        self.winlen = 5
        self.base = 0 #窗口为[base, base+5)
        self.seqno = 0 #下一个要发的seqno
        self.timeout = 0.5 #超时为0.5
        self.packets = []
        self.timers = []
    
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
            file_content[i*self.payload:(i+1)*self.payload if (i+1)*self.payload<file_length else file_length]
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
        self.timers = [0 for i in range(len(packets))]
        self.length = len(packets)

    #Main sending loop.
    def start(self):
        self.gen_all_packets() #生成所有要发送的包
        ack = 0
        while ack != self.length:
            while self.seqno < self.base + self.winlen and self.seqno < self.length: #一次性将seqno到窗口末端的包全部发完
                self.timers[self.seqno] = time.time()
                self.send(self.packets[self.seqno])
                if self.debug:
                    print("Sender.py: send seqno={} timer={}".format(self.seqno, self.timers[self.seqno]))
                self.seqno += 1
            for seqno in range(self.base, self.seqno): #轮询检查超时情况
                now = time.time()
                try:
                    if now - self.timers[seqno] >= self.timeout:
                        self.handle_timeout(seqno)
                        break
                except IndexError:
                    break
            message = self.receive(self.timeout)
            if message:
                message = message.decode()
                msg_type, ack, data, checksum = self.split_packet(message)
                if self.debug:
                    print("Sender.py: received {}|{}|{}|{}".format(msg_type, ack, data[:5], checksum))
                ack = int(ack)
                if msg_type == "ack":
                    if not Checksum.validate_checksum(message):
                        pass
                    else: # ack合法
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
        if ack == self.base + 1:
            self.base += 1
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
        print("-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost")
        print("-d | --debug Print debug messages")
        print("-h | --help Print this usage message")
        print("-k | --sack Enable selective acknowledgement mode")

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "f:p:a:dk", ["file=", "port=", "address=", "debug=", "sack="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
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
        elif o in ("-k", "--sack="):
            sackMode = True

    s = Sender(dest, port, filename, debug, sackMode)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()