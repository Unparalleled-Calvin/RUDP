运行环境：Windows+Python3
实现功能：
- Go-Back-N
- 选择重传
- 丢包、失序、错误、重复，ack和sack两种模式一共八个测试
- 任意类型文件传输(base64)

使用方式：
``` sh
python TestHarness.py -s Sender.py -r Receiver.py
# 可用-t指定超时时间，不指定则默认为0.5，例如-t 0.05(建议使用小的timeout以减少测试完成时间)
# 可用-f指定文件，不指定则默认为README.md，例如-f Calvin.jpg
```
运行截图：![image-20220108174543271](https://s2.loli.net/2022/01/08/uelHGKqDvQ5X4z1.png)

以下是原README：

In this folder you'll find the sample receiver, code for computing and
validating checksums, as well as example sender code.

Quick! What do I have to write?
===============================
Sender.py is the file in which you will implement your reliable sender.
Sender.py provides all the scaffolding you need to handle the
command line arguments we will use in the grading of your project.

The Receiver
============
Receiver.py is the sample receiver.

BasicSender and Friends
=======================
The BasicSender class in BasicSender.py provides a skeleton upon which to build
your reliable sender. It provides the following methods:

    __init__(self,dest,port,filename,debug=False,sackMode=False): Creates a 
        BasicSender. Specify the destination's hostname, the port at which 
        the receiver is listening, and a filename to transmit. If no filename
        is provided, it will read from STDIN.
    
    receive(self, timeout): Receive a packet. Waits for a packet before
        returning. Optionally you can specify a maximum timeout to wait for a
        packet. Returns the received packet as a string, or None if receive
        times out.
    
    send(self,message): Sends message to the receiver specified when you
        created the sender.
    
    make_packet(self,msg_type,seqno,message): Creates a RUDP packet from
        the specified message type, sequence number, and message. Generates the
        appropriate checksum, and returns the full RUDP packet with
        checksum appended.
    
    split_packet(self,packet): Given a RUDP packet, splits a packet into a
        tuple of the form (msg_type, seqno, data, checksum). For packets
        without a data field, the data element will be the empty string.

In addition, it defines one method which you must implement:

    start(self): Starts the Sender.

We provide two example senders that build upon the BasicSender; you are
welcome to base your design upon these:

UnreliableSender.py: While it provides no reliability, it will read from a file
or STDIN and send to a receiver using our protocol.

InteractiveSender.py: A simple interactive sender. It will send any message you
type to the specified receiver. It then waits for a response before prompting
you for a new message.

Checksums
=========
Checksum.py includes two functions for validating and generating checksums for
your packets:

    validate_checksum(message): Returns true if the message's checksum matches
        the message, and false otherwise. This function assumes the last field
        of the message the checksum.
    
    generate_checksum(message): Returns the checksum string for a message. This
        function assumes the message includes the trailing delimiter. The
        checksum is ONLY valid if you simply append this function's result to
        the message you pass in.

Testing
=======
You are expected to write test cases for your own code to ensure compliance
with the project specifications. To assist you, we've given you a simple test
harness (TestHarness.py). The test harness is designed to intercept all packets
sent between your sender and the receiver. It can modify the stream of packets
and check to ensure the stream meets certain conditions. This is very similar
to the grading script that we will use to evaluate your projects.

We have provided three test cases (BasicTest, DropRandomPackets, and 
SackDropRandomPackets) as examples of how to use the test harness. These test 
cases send this README file using the specified sender implementation to the 
specified receiver implementation, either passing all packets through the 
forwarder unmodified or dropping random packets. They both then verify that 
the file received by the receiver matches the input.

To run a test using this test harness, do the following:

    python TestHarness.py -s YourSender.py -r Receiver.py

where "YourSender.py" is the path to your sender implementation, "Receiver.py"
is the path to the receiver implementation. Inside TestHarness.py, you need to
modify the function "tests_to_run" at the top of the script to include any test
cases you add.

Passing the basic test cases we provide is a necessary but not sufficient
condition for doing well on this project; there are still cases that they do not cover. 


```

```