import collections
import datetime
from .signal import WindowedStep

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
OFF_MAX_WATTS = 5               # Instantaneous
WINDOW_DUR = datetime.timedelta(seconds=60)
ON_MIN_WATTS = 20               # Max over windowed

class WasherMonitor:
    def __init__(self):
        self.state = "off"      # "on", "off"
        self.__transition_time = None
        self.__power = WindowedStep(WINDOW_DUR)

    def update_power(self, time, watts):
        # TODO: Schedule a future state change so we don't depend on
        # polling.

        self.__power.update(time, watts)

        # Update state.
        state = self.state
        if self.__transition_time == None or time - self.__transition_time >= WINDOW_DUR:
            if state == "off" and self.__power.max() >= ON_MIN_WATTS:
                state = "on"
            if state == "on" and watts < OFF_MAX_WATTS:
                state = "off"
        if state != self.state:
            self.state = state
            self.__transition_time = time
