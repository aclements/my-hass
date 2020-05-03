import unittest
import csv
import sys
import datetime

from austin_laundry.washer import WasherMonitor
from austin_laundry.dryer import DryerMonitor

class TestWasher(unittest.TestCase):
    def test_1(self):
        with open("washer-1.csv") as f:
            got = states(f, WasherMonitor())
        want = [(ptime("2020-03-28 22:00:25.785103"), "off"),
                (ptime("2020-03-28 22:34:54.777509"), "on"),
                (ptime("2020-03-28 23:54:50.758941"), "done")]
        self.assertEqual(got, want)

    def test_2(self):
        with open("washer-2.csv") as f:
            got = states(f, WasherMonitor())
        want = [(ptime("2020-03-29 19:30:25.479715"), "off"),
                # This one takes a little while to get over the "on"
                # threshold.
                (ptime("2020-03-29 19:46:04.478596"), "on"),
                (ptime("2020-03-29 20:47:50.478907"), "done"),
                # Then a second load.
                (ptime("2020-03-29 20:59:26.477060"), "on"),
                (ptime("2020-03-29 21:58:06.451661"), "done")]
        self.assertEqual(got, want)

DWIN = datetime.timedelta(seconds=15)
class TestDryer(unittest.TestCase):
    def test_1(self):
        with open("dryer-1.csv") as f:
            got = states(f, DryerMonitor())
        want = [(ptime("2020-03-28 23:30:29.314665"), "off"),
                # It takes a window to respond.
                (ptime("2020-03-28 23:59:33.313988") + DWIN, "on"),
                # When the power drops, we respond immediately.
                (ptime("2020-03-29 00:51:23.309325"), "done"),
                # There are a bunch of wrinkle-protect cycles that we
                # ignore. It takes a window to respond to the door
                # open event.
                (ptime("2020-03-29 01:53:39.418616") + DWIN, "off"),
        ]
        self.assertEqual(got, want)

    def test_2(self):
        with open("dryer-2.csv") as f:
            got = states(f, DryerMonitor())
        want = [(ptime("2020-03-29 20:30:29.149019"), "off"),
                (ptime("2020-03-29 20:50:00.141341") + DWIN, "on"),
                # We briefly opened the door during the cycle.
                (ptime("2020-03-29 20:58:14.146706"), "done"),
                (ptime("2020-03-29 20:58:19.148173") + DWIN, "on"),
                # Now done for real.
                (ptime("2020-03-29 21:33:15.143626"), "done"),
                # Now we unload and start another cycle.
                (ptime("2020-03-29 23:32:40.127907") + DWIN, "off"),
                (ptime("2020-03-29 23:34:06.126349") + DWIN, "on"),
                (ptime("2020-03-30 00:18:00.102895"), "done"),
                (ptime("2020-03-30 01:47:26.092223") + DWIN, "off"),
        ]
        self.assertEqual(got, want)

    def test_3(self):
        with open("dryer-3.csv") as f:
            got = states(f, DryerMonitor())
        want = [(ptime("2020-04-15 16:45:25.180127"), "off"),
                (ptime("2020-04-15 17:02:45.183073") + DWIN, "on"),
                # We pressed "pause", so power briefly dropped into
                # the "done" zone, then opened the door, then started
                # it again.
                (ptime("2020-04-15 17:12:52.180421"), "done"),
                (ptime("2020-04-15 17:12:54.181579") + DWIN, "off"),
                (ptime("2020-04-15 17:13:39.182232") + DWIN, "on"),
                # Done for real.
                (ptime("2020-04-15 17:48:09.178732"), "done"),
                (ptime("2020-04-15 18:06:39.168630") + DWIN, "off")]
        self.assertEqual(got, want)

def ptime(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")

def states(csv_file, monitor, debug=False):
    # Parse CSV.
    recs = []
    for rec in csv.reader(csv_file):
        if rec[1] == "unavailable":
            continue
        recs.append((ptime(rec[0]), float(rec[1])))

    transitions = []
    prev = None
    update_time = None
    recs.reverse()
    while recs or update_time != None:
        # Is rec or update_time next?
        if update_time == None or recs[-1][0] < update_time:
            time, watts = recs.pop()
        else:
            time, watts = update_time, None

        update_time = monitor.update(time, watts)

        if monitor.state != prev:
            transitions.append((time, monitor.state))
            prev = monitor.state

        if debug:
            print("%s %10s %s" % (time, watts, monitor.state))
    return transitions

if __name__ == '__main__':
    unittest.main()
