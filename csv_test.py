from austin_laundry.washer import WasherMonitor
from austin_laundry.dryer import DryerMonitor
import csv
import sys
import datetime

mon = WasherMonitor()
#mon = DryerMonitor()
for rec in csv.reader(sys.stdin):
    if rec[1] == "unavailable":
        continue
    time = datetime.datetime.strptime(rec[0], "%Y-%m-%d %H:%M:%S.%f")
    m = mon.update_power(time, float(rec[1]))
    print("%s %10s %10s %s" % (rec[0], rec[1], m, mon.state))
