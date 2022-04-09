import json
import time

import asyncio
import board
import busio
import displayio

from adafruit_neokey.neokey1x4 import NeoKey1x4
from adafruit_pyportal import PyPortal

from display import Display, COLORS
from timer import Timer


print(f'Running {__file__}')


class KeyPressTracker:
    def __init__(self, app, idx: int, long_press: float = 0.5) -> None:
        self.app = app
        self.idx = idx
        self.long_press = long_press
        self.debounce = False

    def append(self, x):
        if not x:
            self.num_press = 0
            self.debounce = False
        else:
            self.app.neokeys.pixels[self.app.key_idxs[self.idx]] = (0, 0, 0)
            self.num_press += 1
            long_press = self.app.sampling_rate * self.num_press > self.long_press
            if long_press:
                self.app.timers[self.idx].reset()
                self.num_press = 0
            elif not self.debounce:  # short press ignore debounce
                self.app.timers[self.idx].toggle()
            self.debounce = True


def rgb_to_hex(rgb):
    hexstr = '%02x%02x%02x' % rgb
    return hex(int(hexstr, 16))


class AppManager:
    with open('config.json') as fo:
        config = json.load(fo)
    def __init__(self, pyportal, neokeys):
        self.pyportal = pyportal
        self.neokeys = neokeys
        self.sampling_rate = 0.01
        self.timers = [Timer(length) for length in self.config['timers']]
        self.key_idxs = list(range(0, 4))
        if self.config['reverse_keys']:
            self.key_idxs = self.key_idxs[::-1]
        self.key_press_history = [KeyPressTracker(self, i, self.config['key_press']['long']) for i in range(4)]
        self.display = Display(self)

    async def monitor_keys(self):
        refresh_counter, refresh_every, start = 0, 64, time.time()
        while True:
            for i, kp_hist in enumerate(self.key_press_history):
                key_idx = self.key_idxs[i]
                kp_hist.append(self.neokeys[key_idx])
            refresh_counter += 1
            if refresh_counter % refresh_every == 0 and refresh_counter > 0:
                self.sampling_rate = (time.time() - start) / refresh_every
                start, refresh_counter = time.time(), 0
            await asyncio.sleep(0)

    async def loop(self):
        oot_counter = 0
        while True:
            for i in range(4):
                state = self.timers[i].state
                self.update_lights(state, self.key_idxs[i])
                self.display.update(state, i)
            self.display.rf.text = f'FR: {self.sampling_rate:0.4f}'
            self.display.display.refresh()
            if any(timer.out_of_time for timer in self.timers) and oot_counter < self.config['sound']['stop_after']:
                self.pyportal.play_file(self.config['sound']['end'])
                oot_counter += 1
            elif all(not timer.out_of_time for timer in self.timers):
                oot_counter = 0
            await asyncio.sleep(0.8)

    def update_lights(self, timer_state, i):
        if timer_state.out_of_time:
            self.neokeys.pixels[i] = COLORS['red']
        elif timer_state.running:
            self.neokeys.pixels[i] = COLORS['orange']
        elif not timer_state.running and timer_state.remaining < timer_state.length:
            self.neokeys.pixels[i] = COLORS['yellow']
        else:
            self.neokeys.pixels[i] = COLORS['green']


async def main():
    pyportal = PyPortal()
    i2c_bus = busio.I2C(board.SCL, board.SDA)
    neokeys = NeoKey1x4(i2c_bus, addr=0x30)
    app = AppManager(pyportal, neokeys)
    app.display.show()
    await asyncio.gather(
        asyncio.create_task(app.monitor_keys()),
        asyncio.create_task(app.loop()),
    )


if __name__ == '__main__':
    asyncio.run(main())
