import collections
import datetime

# The control panel consumes about 2.8W.
#
# When the washer is running, it frequently drops to 7.5W, but this
# never lasts more than 10 seconds. The max over 60 seconds never
# drops below 50W, except right at the beginning when it starts at
# 10–20W and ramps up for ~20 seconds. In that ramp up, it sometime
# briefly drops below 7.5W, but since this happens in the first 20
# seconds, we're still in the window where transitioning back to "off"
# is disallowed.
#
# When the washer finishes, it drops to <1W for about 10 seconds, then
# 0W.
#
# For any transition, to prevent flapping and smooth blips that happen
# just after a transition, we disallow another transition for
# WINDOW_DUR (longer would also be safe).
WINDOW_DUR = datetime.timedelta(seconds=60)
RUNNING_WATTS = 20              # Max over window
OFF_WATTS = 5                   # Instantaneous

class WasherMonitor:
    def __init__(self):
        self.state = "off"
        self.__transition_time = None
        self.__power = collections.deque()

    def update_power(self, time, watts):
        # TODO: Schedule a future state change so we don't depend on
        # polling.

        # Update window.
        self.__power.append((time, watts))
        expire = time - WINDOW_DUR
        while len(self.__power) > 0 and self.__power[0][0] <= expire:
            self.__power.popleft()
        recent_max = max(p[1] for p in self.__power)

        # Update state.
        prevState = self.state
        if self.__transition_time == None or time - self.__transition_time >= WINDOW_DUR:
            if self.state == "off" and recent_max >= RUNNING_WATTS:
                self.state = "on"
            if self.state == "on" and watts < OFF_WATTS:
                self.state = "off"
        if self.state != prevState:
            self.__transition_time = time

        return recent_max
