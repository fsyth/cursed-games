import curses

class ColorPair:
    """
    Curses color pair, with id, foreground color,
    and background color, for xterm-256color.
    | Range   | Colors                        |
    | :-----: | :---------------------------- |
    |     -1  | Terminal default              |
    |   0-15  | Standard terminal colours x16 |
    |  16-231 | RGB cube 6x6x6                |
    | 232-255 | Greyscale shades x24          |
    """

    counter = 0

    def __init__(self, fg: int, bg: int):
        ColorPair.counter += 1
        self.id = ColorPair.counter
        self.fg = fg
        self.bg = bg

    def to_curses(self):
        return curses.color_pair(self.id)
