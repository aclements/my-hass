import collections

class WindowedStep:
    """A time-windowed view of a step-wise continuous signal."""
    def __init__(self, duration):
        self.__dur = duration
        self.__q = collections.deque()

    def update(self, time, value=None):
        """Update window to end at time, optionally updating value.

        This moves the window forward to end at time. If value is not
        None, it additionally records a change in the signal at time.
        """
        # Shift the window forward.
        start = time - self.__dur
        last = None
        while len(self.__q) > 0 and self.__q[0][0] <= start:
            last = self.__q.popleft()
        if last != None:
            # The queue represents a continuous signal, so the last
            # entry we popped actually covers from its time up to the
            # next entry. Put it back with an updated time.
            self.__q.appendleft((start, last[1]))

        # Update the signal.
        if value != None:
            self.__q.append((time, value))

    def min(self):
        return min(x[1] for x in self.__q)

    def max(self):
        return max(x[1] for x in self.__q)
    
