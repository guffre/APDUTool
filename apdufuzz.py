#!/usr/bin/env python2
import smartcard
from smartcard.System import readers
from smartcard.util import toHexString

import re
import sys
import itertools
import struct

def bruteforce_parse(block):
    ret = set()
    if "*" in block:
        ret.add(-1)
        block.replace("*","")
    singles = re.findall("[0-9a-f]{2}", block, re.IGNORECASE)
    ranges = re.findall("([0-9a-f]{2})-([0-9a-f]{2})", block, re.IGNORECASE)
    for val in singles:
        ret.add(int(val,16))
    for lo,hi in ranges:
        ret.update(list(range(int(lo,16), int(hi,16))))
    # Below should only happen for auto-mode on Lc (length command)
    if len(ret) == 0:
        ret.update([None])
    return ret

def command_length(com):
    com_length = len(com)
    if com_length == 0: # Zero bytes, todo
        print("command_length 0?")
    elif com_length < 0xff: # One byte
        return [com_length]
    else: # Three bytes
        bytes = [0]
        bytes.extend(struct.unpack("bb", struct.pack(">h", com_length)))
        return bytes

def traverse_records(connection):
    records = list(range(0,0x10))
    for record in records:
        line = [00, 0xb2, record, 0x0c]
        send_apdu(connection, line, True)

def send_apdu(connection, line, traversal=False):
    #print("transmitting: {}".format(toHexString(line)))
    data, sw1, sw2 = connection.transmit(line)
    if (sw1 == 0x6d and sw2 == 0) or (sw1 == 0x6a and sw2 == 0x82):
        pass
    else:
        print("transmitting: {}".format(toHexString(line)))
        print("Response Bytes: {} {}".format(sw1, sw2))
        print("Response Data: {}".format(toHexString(data)))
        tmp = ""
        for char in data:
            tmp += chr(char) if (char > 31 or char < 128) else '.'
        print("Response Data: {}".format(tmp))
        if not traversal:
            traverse_records(connection)

def reader_select():
    select = -1
    while (select < 0):
        try:
            r = readers()
            print("Please select a reader:")
            for i,reader in enumerate(r):
                print("{}] {}".format(i+1,reader))
            select = int(raw_input("> "))
        except:
            print("Invalid selection.")
    return r[select]

def get_command():
    command = raw_input("Please enter your command:\n> ")
    return command.split()

# ./apdufuzz.py 0 00 a4 04 00 xx a0 00 00 00-08 00,03,11,22,33,44,55,66,77,88,99 00,01,10,11,20,30 00,01,10,11,20,30 *00
if __name__ == '__main__':
    if len(sys.argv) < 2:
        reader = reader_select()
        command = get_command()
    else:
        print(sys.argv)
        reader = readers()[int(sys.argv[1])]
        command = sys.argv[2:]
    connection = reader.createConnection()
    connection.connect()
    
    # Perform bruteforce
    bytes = []
    for block in command:
        bytes.append(bruteforce_parse(block))
    for line in itertools.product(*bytes):
        if line[4] == None:
            tmp = []
            tmp.extend(line[:4])
            command = list(line[5:-1])
            while (-1 in command):
                command.remove(-1)
            tmp.extend(command_length(command))
            tmp.extend(command)
            tmp.append(line[-1])
            line = tmp
        send_apdu(connection, line)
