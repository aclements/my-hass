import datetime
from .signal import WindowedStep

# Idle consumption is ~1.5W.
#
# When the control panel is on, it's ~5W.
#
# When the door is open, it's ~11.7W.
#
# When started, it consumes ~1200–1700W for a second.
#
# When running, it consumes ~200–250W, plus a few second spike up to
# ~700W every 5 minutes.
#
# When in wrinkle protect, it's mostly idle (~1.5W), except every 5
# minutes when it spikes up to ~1500–2000W for a second, stays at
# ~200W for a few seconds, and goes idle again. To smooth this out, we
# apply windowing.
#
# When transitioning between off and a high-wattage state (either when
# finishing a load, or when starting or finishing a wrinkle protect),
# it can transiently appear to be in the door-open range. Hence, we
# require the whole window to be within the door-open range.

OFF_MAX_WATTS = 8                           # Instantaneous
WINDOW_DUR = datetime.timedelta(seconds=10)
DOOR_MAX_WATTS = 15                         # Windowed
ON_MIN_WATTS = 150                          # Windowed

class DryerMonitor:
    def __init__(self):
        self.state = "off"      # "on", "off", or "ready"
        self.__pstate = "off"   # "on", "off", or "door"
        self.__power = WindowedStep(WINDOW_DUR)

    def update_power(self, time, watts):
        # TODO: Schedule a future state change so we don't depend on
        # polling. Maybe this should be part of WindowedStep? The
        # simplest thing would be to query it for "when is the time of
        # next change assuming there are no more updates?" and if I
        # want to get fancy I could pass in the computation and ask
        # "when will the value of this computation change if there are
        # no more updates?"

        self.__power.update(time, watts)

        # Compute power state.
        pstate = self.__pstate
        if watts < OFF_MAX_WATTS:
            # It never has a transient drop this low, so we can
            # immediately consider it off.
            pstate = "off"
        elif self.__power.min() >= ON_MIN_WATTS:
            # This means it will take WINDOW_DUR to respond to the
            # dryer coming on, but that's the only way to filter out
            # wrinkle protect.
            pstate = "on"
        elif self.__power.min() > OFF_MAX_WATTS and self.__power.max() < DOOR_MAX_WATTS:
            # We require the whole window to be in the door-open range
            # to filter out transitions between off and high-wattage
            # states.
            pstate = "door"
        self.__pstate = pstate

        # Use power state to transition dryer state.
        if self.state == "on" and pstate == "off":
            # Dryer finished; clothes are ready.
            self.state = "done"
        elif self.state == "done" and pstate == "off":
            # Clothes remain ready.
            pass
        elif pstate == "door":
            # Dryer is being loaded or unloaded.
            self.state = "off"
        else:
            self.state = pstate
