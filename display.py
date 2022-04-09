import board
import displayio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from adafruit_progressbar.verticalprogressbar import (
    VerticalProgressBar,
    VerticalFillDirection
)


COLORS = {
    'yellow': (122, 122, 6),
    'green': (36, 200, 36),
    'blue': (0, 0, 255),
    'red': (200, 24, 15),
    'purple': (122, 0, 122),
    'cyan': (0, 122, 122),
    'orange': (253, 164, 119),
    'off': (0, 0, 0),
    'white': (82, 82, 82)
}

def seconds_to_string(x: int) -> str:
    h = x // 3600
    m = ( x - (h * 3600) ) // 60
    s = x - (h * 3600 + m * 60)
    return f'{h:02d}:{m:02d}:{s:02d}'


class Display:
    title_font = bitmap_font.load_font("fonts/OrangeKid-Regular-50.bdf", displayio.Bitmap)
    font = bitmap_font.load_font("fonts/OrangeKid-Regular-32.bdf", displayio.Bitmap)
    colors = {
        'green': (169, 206, 128),
        'purple': (161, 120, 222),
        'blue': (81, 183, 231),
        'yellow': (251, 221, 4),
        'orange': (253, 164, 119),
        'red': (252, 118, 121),
    }
    dark_colors = {
        'green': 0x96c95b,
        'purple': (181, 140, 242),
        'blue': 0x3ba1d1,
        'yellow': 0xc4ad00,
        'orange': (253, 184, 139),
        'red': 0xe35456,
    }
    bg_color = 0x9E6E57
    def __init__(self, app) -> None:
        self.timers = app.timers
        self.display = board.DISPLAY
        self.main_screen = displayio.Group()
        self.init_background()
        self.init_header()

        horizontal_spacing = self.display.width // len(self.timers)
        self.pbars = []
        self.texts = []
        for i, timer in enumerate(self.timers):
            timer_state = timer.state
            x = horizontal_spacing * i
            g = displayio.Group(x=x, y=0)
            x_center = horizontal_spacing // 2
            pbar_width = 32
            pbar_height = 192
            pbar_offset = (x_center - pbar_width // 2, 72)
            pbar = VerticalProgressBar(
                pbar_offset,
                (pbar_width, pbar_height),
                min_value=0,
                bar_color=self.colors['green'],
                outline_color=self.dark_colors['green'],
                border_thickness=4,
                max_value=timer.length,
                value=timer_state.remaining,
                direction=VerticalFillDirection.BOTTOM_TO_TOP,
            )
            
            g.append(pbar)
            self.pbars.append(pbar)
            text_group = self.setup_text(
                seconds_to_string(timer_state.remaining),
                x_center - 48, pbar_offset[1] + pbar_height + 24
            )
            g.append(text_group)
            self.texts.append(text_group)
            self.main_screen.append(g)

    def init_background(self):
        palette = displayio.Palette(1)
        palette[0] = self.bg_color
        bg_bitmap = displayio.Bitmap(self.display.width, self.display.height, len(palette))
        bg_tile = displayio.TileGrid(bg_bitmap, pixel_shader=palette)
        self.main_screen.append(bg_tile)

    def init_header(self):
        group = displayio.Group(x=0, y=0)
        palette = displayio.Palette(1)
        palette[0] = 0xDAAE46
        header_bitmap = displayio.Bitmap(self.display.width, 64, 1)
        header_tile = displayio.TileGrid(header_bitmap, pixel_shader=palette)
        group.append(header_tile)
        text = self.setup_text('tiny timer', self.display.width // 2 - 64, 24, font=self.title_font)
        group.append(text)
        self.rf = self.setup_text('FR: ', 10, 24, self.font)
        group.append(self.rf)
        self.main_screen.append(group)

    def setup_text(self, text: str, xpos, ypos, font = None, scale = None):
        if font is None:
            font = self.font
        fg = Label(font, text=text, color=0xFFFFFF)
        fg.x = xpos
        fg.y = ypos
        return fg

    def show(self):
        self.display.show(self.main_screen)

    def update(self, timer_state, i):
        pbar = self.pbars[i]
        pbar.value = timer_state.remaining
        self.texts[i].text = seconds_to_string(timer_state.remaining)
        if timer_state.out_of_time:
            pbar.bar_color = self.colors['red']
            pbar.border_color = self.dark_colors['red']
        elif timer_state.running:
            pbar.bar_color = self.colors['green']
            pbar.border_color = self.dark_colors['green']
        elif not timer_state.running and timer_state.remaining < timer_state.length:
            pbar.bar_color = self.colors['yellow']
            pbar.border_color = self.dark_colors['yellow']
        else:
            pbar.bar_color = self.colors['green']
            pbar.border_color = self.dark_colors['green']
