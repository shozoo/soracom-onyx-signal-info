#!/usr/bin/env python3
# encoding: utf-8
"""
Gets signal information from SORACOM Onyx LTE USB Dongle SC-QGLC4-C1 (Quectel EG25-G)
https://github.com/shozoo/soracom-onyx-signal-info

Usage examples:
$ ./get-onyx-signal-info.py --help   # to show help
$ ./get-onyx-signal-info-py -d /dev/ttyUSB3 -i any --json  # output to the standard output in JSON format
$ ./get-onyx-signal-info-py -d /dev/ttyUSB3 -i rat,band,rsrp,rsrq,sinr --udp-endpoint  # send to the unified endpoint
"""
import argparse
import json
import queue
import serial
import serial.threaded
import socket
import threading
import urllib.request


def main():

    # parse command-line options
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--device', default='/dev/ttyUSB3', help='Name of the AT command port to use. If not specified, /dev/ttyUSB3 is used.')
    parser.add_argument('-i', '--include', default='rat,band,rsrp,sinr', help='Comma-separated list of items to be output. Set \'-i any\' to output all available items.')
    parser.add_argument('--json', action='store_true', help='Output the result to the standard output in JSON format.')
    parser.add_argument('--metadata', action='store_true', help='Put the result to the SORACOM Air metadata service as tag values.')
    parser.add_argument('--udp-endpoint', action='store_true', help='Send the result to the unified endpoint by UDP packet. ')
    args = parser.parse_args()

    # open SORACOM Onyx LTE USB dongle
    with serial.Serial(args.device, timeout=1) as ser:
        with serial.threaded.ReaderThread(ser, EG2xG) as onyx:

            # get full result
            full_result = onyx.query_serving_cell()

            # filter output
            result = dict()
            item_names = args.include.split(',')
            if 'any' in item_names:
                result = full_result
            else:
                result = { k:v for k,v in full_result.items() if k in item_names }
            
            # output JSON if (--json is set) or (neither --metadata nor --udp-endpoint are set)
            if args.json or not (args.metadata or args.udp_endpoint):
                print(json.dumps(result))

            # output to metadata tags
            if args.metadata:
                put_metadata(result)

            # output to unified endpoint in UDP
            if args.udp_endpoint:
                put_udp_endpoint(result)


def put_metadata(obj):
    headers = {
        'Content-type':'application/json'
    }
    tags = list()
    for k, v in obj.items():
        tags.append({'tagName': k, 'tagValue': str(v)})
    body = json.dumps(tags).encode('utf-8')
    req = urllib.request.Request('http://metadata.soracom.io/v1/subscriber/tags',
        data = body,
        headers = headers,
        method='PUT')
    with urllib.request.urlopen(req) as f:
        resp = f.read().decode('utf-8')
        if len(resp) > 0:
            print('PUT signal information into metadata: {}'.format(resp))

def put_udp_endpoint(obj):
    body = json.dumps(obj).encode('utf-8')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(body, ('unified.soracom.io', 23080))

class ATProtocol(serial.threaded.LineReader):

    def __init__(self):
        super(ATProtocol, self).__init__()
        self.responses = queue.Queue()
        self.lock = threading.Lock()

    def handle_line(self, line):
        self.responses.put(line)

    def command(self, command, response='OK', timeout=5):
        with self.lock:
            self.write_line(command)
            lines = []
            while True:
                try:
                    line = self.responses.get(timeout=timeout)
                    if line == response or line == 'ERROR' or line == 'NO CARRIER':
                        return lines
                    else:
                        lines.append(line)
                except:
                    raise RuntimeError('AT command timeout ({!r})'.format(command))

class EG2xG(ATProtocol):

    def __init__(self):
        super(EG2xG, self).__init__()

    def query_serving_cell(self):
        resp = lookup_line(self.command('AT+QENG=\"servingcell\"'), '+QENG:').split(',')
        info = {}
        info['state'] = resp[(i:=1)].strip('\"')
        info['rat'] = resp[(i:=i+1)].strip('\"')
        if info['rat'] == 'GSM':
            info['mcc'] = resp[(i:=i+1)]
            info['mnc'] = resp[(i:=i+1)]
            info['lac'] = resp[(i:=i+1)]
            info['cellid'] = resp[(i:=i+1)]
            info['bsic'] = str2int(resp[(i:=i+1)])
            info['arfcn'] = str2int(resp[(i:=i+1)])
            info['band'] = str2int(resp[(i:=i+1)], -1)
            info['rxlev'] = str2int(resp[(i:=i+1)],-1)
            info['txp'] = str2int(resp[(i:=i+1)])
            info['rla'] = str2int(resp[(i:=i+1)])
            info['drx'] = str2int(resp[(i:=i+1)])
            info['c1'] = str2int(resp[(i:=i+1)])
            info['c2'] = str2int(resp[(i:=i+1)])
            info['gprs'] = str2int(resp[(i:=i+1)],-1)
            info['tch'] = str2int(resp[(i:=i+1)])
            info['ts'] = str2int(resp[(i:=i+1)])
            info['ta'] = str2int(resp[(i:=i+1)])
            info['maio'] = str2int(resp[(i:=i+1)])
            info['hsn'] = str2int(resp[(i:=i+1)])
            info['rxlevsub'] = str2int(resp[(i:=i+1)],-1)
            info['rxlevfull'] = str2int(resp[(i:=i+1)],-1)
            info['rxqualsub'] = str2int(resp[(i:=i+1)],-1)
            info['rxqualfull'] = str2int(resp[(i:=i+1)],-1)
            info['voicecodec'] = resp[(i:=i+1)].strip('\"')
        elif info['rat'] == 'WCDMA':
            info['mcc'] = resp[(i:=i+1)]
            info['mnc'] = resp[(i:=i+1)]
            info['lac'] = resp[(i:=i+1)]
            info['cellid'] = resp[(i:=i+1)]
            info['uarfcn'] = str2int(resp[(i:=i+1)])
            info['psc'] = str2int(resp[(i:=i+1)])
            info['rac'] = str2int(resp[(i:=i+1)],-1)
            info['rscp'] = str2int(resp[(i:=i+1)])
            info['ecio'] = str2int(resp[(i:=i+1)])
            info['phych'] = str2int(resp[(i:=i+1)],-1)
            info['sf'] = str2int(resp[(i:=i+1)],8)
            info['slot'] = str2int(resp[(i:=i+1)],-1)
            info['speech_code'] = resp[(i:=i+1)]
            info['commod'] = str2int(resp[(i:=i+1)],-1)
        elif info['rat'] == 'LTE':
            info['duplex'] = resp[(i:=i+1)].strip('\"')
            info['mcc'] = resp[(i:=i+1)]
            info['mnc'] = resp[(i:=i+1)]
            info['cellid'] = resp[(i:=i+1)]
            info['pcid'] = str2int(resp[(i:=i+1)])
            info['earfcn'] = str2int(resp[(i:=i+1)])
            info['band'] = str2int(resp[(i:=i+1)])
            info['ul_bandwidth'] = str2int(resp[(i:=i+1)])
            info['dl_bandwidth'] = str2int(resp[(i:=i+1)])
            info['tac'] = resp[(i:=i+1)]
            info['rsrp'] = str2int(resp[(i:=i+1)])
            info['rsrq'] = str2int(resp[(i:=i+1)])
            info['rssi'] = str2int(resp[(i:=i+1)])
            info['sinr'] = str2int(resp[(i:=i+1)])
            info['rxlev'] = str2int(resp[(i:=i+1)])
        return info

def lookup_line(list, prefix):
    for l in list:
        if l.startswith(prefix):
            return l
    raise RuntimeError('cannot find string starts with {} in {!r}'.format(prefix, list))

def str2int(str, nan=0):
    if str == "-":
        return nan
    try:
        return int(str)
    except:
        return nan

if __name__ == '__main__':
    main()
