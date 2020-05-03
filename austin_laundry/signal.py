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

    def process(self, cb):
        """Process this signal using cb(sig).

        This applies cb to this signal and returns a pair of its
        result and the earliest time at which the result of cb will
        change if there are no more updates to the signal.

        cb must be pure, since this will call it with several
        hypothetical signals.
        """

        # Get the current value.
        now = self.__q[len(self.__q)-1][0]
        val = cb(wsView(self.__q, now))

        # Step forward in time, simulating the situation where there
        # are no more updates.
        q2 = self.__q.copy()
        q2.popleft()
        while len(q2) > 0:
            then = q2[0][0] + self.__dur
            if cb(wsView(q2, then)) != val:
                # The processed value changed at this point.
                return val, then
            q2.popleft()

        # cb will never change until there are further updates.
        return val, None

class wsView:
    def __init__(self, q, now):
        self.__q = q
        self.__now = now

    def time(self):
        return self.__now

    def current(self):
        return self.__q[len(self.__q)-1][1]

    def min(self):
        return min(x[1] for x in self.__q)

    def max(self):
        return max(x[1] for x in self.__q)
