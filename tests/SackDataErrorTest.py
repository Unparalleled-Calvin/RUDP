import random

from tests.BasicTest import BasicTest

class SackDataErrorTest(BasicTest):
    def __init__(self, forwarder, input_file):
        super(SackDataErrorTest, self).__init__(forwarder, input_file, sackMode = True)
    def handle_packet(self):
        for p in self.forwarder.in_queue:
            if random.choice([True, False]): # 更改数据使得数据出错
                p.data = "Unparalleled Calvin!"
            self.forwarder.out_queue.append(p)
        # empty out the in_queue
        self.forwarder.in_queue = []
