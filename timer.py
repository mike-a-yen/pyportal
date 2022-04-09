from collections import namedtuple
import time


timer_state = namedtuple('timer_state', ['remaining', 'running', 'out_of_time', 'length'])


class TimeError(Exception):
    pass


class Timer:
    def __init__(self, length: int) -> None:
        """
        length: time in seconds.
        """
        self.length = length
        self.working_length = length
        self.start_time = None
        self.running = False

    def start(self) -> None:
        if self.start_time is not None:
            raise TimeError('Timer is running. Use .stop() to stop it.')
        self.start_time = time.time()
        self.running = True

    def pause(self) -> None:
        if self.start_time is None:
            raise TimeError('Timer is not running. Use .start() to start it.')
        elapsed_time = time.time() - self.start_time
        self.working_length -= elapsed_time
        self.start_time = None
        self.running = False

    def toggle(self) -> None:
        if self.out_of_time:
            return
        if self.running:
            self.pause()
        else:
            self.start()

    def reset(self) -> None:
        self.start_time = None
        self.working_length = self.length
        self.running = False

    @property
    def state(self):
        if self.start_time is None:
            remaining = self.working_length
        else:
            elapsed_time = time.time() - self.start_time
            remaining = max(self.working_length - elapsed_time, 0)
        assert remaining >= 0
        return timer_state(remaining, self.running, remaining <= 0, self.length)

    @property
    def out_of_time(self) -> bool:
        if self.start_time is None:
            remaining = self.working_length
        else:
            elapsed_time = time.time() - self.start_time
            remaining = max(self.working_length - elapsed_time, 0)
        return remaining <= 0