from collections import namedtuple
import json
from datetime import datetime
from pprint import pprint
import pickle
from argparse import ArgumentParser

def getCurrentBytes(iface):
    dp = namedtuple("Datapoint", ["rx","tx","timestamp"])
    try:
        with open("/sys/class/net/" + iface + "/statistics/rx_bytes", 'r') as f:
            dp.rx = int(f.readline().strip())

        with open("/sys/class/net/" + iface + "/statistics/tx_bytes", 'r') as f:
            dp.tx = int(f.readline().strip())

        dp.timestamp = datetime.now()

        return dp

    except:
        print("Interface not found")
        return None

def getUptime():
    with open('/proc/uptime', 'r') as f:
        return float(f.readline().split()[0])

def size_formater(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

if __name__ == '__main__':
    parser = ArgumentParser(description="This icinga/nagios plugin monitores the accumulated traffic of a specified interface.")
    parser.add_argument('iface', metavar='INTERFACE')
    parser.add_argument('-w', '--warning', type=int, required=True, help="traffic in bytes")
    parser.add_argument('-c', '--critical', type=int, required=True, help="traffic in bytes")
    args = parser.parse_args()

    bytes = getCurrentBytes("wlan0")

    data = {
                "rx": 0,
                "tx": 0,
                "last_rx": bytes.rx,
                "last_tx": bytes.tx,
                "time": bytes.timestamp,
                "uptime": getUptime()
            }

    try:
        with open('app.cache', 'rb') as handle:
            cache = pickle.load(handle)
    except:
            print("Could not open cache")
            cache = data

    if data['uptime'] < cache['uptime']:
        #reboot detected
        rx = data['last_rx'] + cache['rx']
        tx = data['last_tx'] + cache['tx']
    else:
        rx = cache['rx'] + (data['last_rx'] - cache['rx'])
        tx = cache['tx'] + (data['last_tx'] - cache['tx'])

    data['rx'] = rx
    data['tx'] = tx

    if (rx + tx) > args.critical:
        print("TRAFFIC WARNING: Traffic exeded limit - " + size_formater(rx+tx))
    elif (rx + tx) > args.warning:
        print("TRAFFIC WARNING: Traffic is near to exeded the limit - " + size_formater(rx+tx))
    else:
        print("TRAFFIC OK: Traffic is below the limit - " + size_formater(rx+tx))

    try:
        with open('app.cache', 'wb+') as handle:
            pickle.dump(data, handle)
    except:
        print("Error creating cache")
