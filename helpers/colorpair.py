import curses

class ColorPair:
    """Curses color pair, with id, foreground color, and background color, for xterm-256color."""
    counter = 0

    def __init__(self, fg: int, bg: int):
        ColorPair.counter += 1
        self.id = ColorPair.counter
        self.fg = fg
        self.bg = bg

    def to_curses(self):
        return curses.color_pair(self.id)
