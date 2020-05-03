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
        self.state = "off"      # "on", "done", "off"
        self.__pstate = "off"   # "on", "off"
        self.__transition_time = None
        self.__power = WindowedStep(WINDOW_DUR)

    def update(self, time, watts=None):
        self.__power.update(time, watts)

        # Update power state.
        pstate, next_time = self.__power.process(self.__compute_pstate)
        if pstate != self.__pstate:
            # Apply hysteresis.
            if self.__transition_time == None or time - self.__transition_time >= WINDOW_DUR:
                self.__pstate = pstate
                self.__transition_time = time
            else:
                end_t = self.__transition_time + WINDOW_DUR
                if next_time == None:
                    next_time = end_t
                else:
                    next_time = min(next_time, end_t)

        # Use power state to transition overall state.
        if self.state == "on" and self.__pstate == "off":
            # Washer finished; clothes are ready.
            self.state = "done"
        elif self.state == "done" and self.__pstate == "off":
            # Clothes remain ready.
            pass
        else:
            self.state = self.__pstate

        return next_time

    def __compute_pstate(self, power):
        # TODO: The reads of __pstate here are wrong in a sense
        # because they read the current power state, but as we
        # simulate forward that could change. Really this should be a
        # derived signal.
        if self.__pstate == "off" and power.max() >= ON_MIN_WATTS:
            return "on"
        if self.__pstate == "on" and power.current() < OFF_MAX_WATTS:
            return "off"
        # No change.
        return self.__pstate

    def door_opened(self):
        if self.state == "done":
            self.state = "off"
