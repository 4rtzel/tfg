"""Palette for terminal browser.

Note: if you're sure that yor terminal emulator supports 256 colors but
flame graph colors seem to be off, you could try set $TERM to "xterm-256color".
"""

import curses
from itertools import cycle, chain


class Palette(object):
    """Palette for terminal browser.
    Provides gradient generator to infinitely cycle around available colors.
    In additional to that, provides lighter and darker colors (compared to
    gradient colors).
    Supports terminal emulator with [8, 256] colors.
    """
    HOT = 0
    IO = 1
    WAKEUP = 2
    CHAIN = 3

    def __init__(self, palette):
        self._pairs = None
        self._lighter = 0
        self._normal = 0
        self._darker = 0
        if curses.COLORS == 256:
            self._init_256(palette)
        elif curses.COLORS >= 8:
            self._init_8(palette)
        else:
            raise RuntimeError('Terminal only supports {} colors but at least 8 is required.'
                               .format(curses.COLOR_PAIRS))

    def _init_256(self, palette):
        """Initialize palette for 256-colors terminals
        """
        if palette == Palette.HOT:
            self._init_pairs([226, 220, 214, 208, 202], 228, 214, 130)
        elif palette == Palette.IO:
            self._init_pairs([45, 39, 33, 27, 21], 86, 33, 21)
        else:
            raise RuntimeError('Unknown color palette {}'.format(palette))

    def _init_8(self, palette):
        """Initialize palette for 8-colors terminals
        """
        if palette == Palette.HOT:
            self._init_pairs([curses.COLOR_RED, curses.COLOR_YELLOW],
                             curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_BLUE)
        elif palette == Palette.IO:
            self._init_pairs([curses.COLOR_BLUE, curses.COLOR_CYAN],
                             curses.COLOR_GREEN, curses.COLOR_BLUE, curses.COLOR_MAGENTA)
        else:
            raise RuntimeError('Unknown color palette {}'.format(palette))

    def gradient(self):
        """Infinitely colors generator
        """
        for i in cycle(chain(self._pairs, self._pairs[1:-1][::-1])):
            yield curses.color_pair(i)

    @property
    def lighter(self):
        return curses.color_pair(self._lighter)

    @property
    def normal(self):
        return curses.color_pair(self._normal)

    @property
    def darker(self):
        return curses.color_pair(self._darker)

    def _init_pairs(self, gradient_list, light_color, normal_color, dark_color):
        self._pairs = []
        for i, color in enumerate(gradient_list):
            curses.init_pair(i + 1, curses.COLOR_BLACK, color)
            self._pairs.append(i + 1)
        self._lighter = len(self._pairs) + 1
        self._normal = self._lighter + 1
        self._darker = self._normal + 1
        curses.init_pair(self._lighter, curses.COLOR_BLACK, light_color)
        curses.init_pair(self._normal, curses.COLOR_BLACK, normal_color)
        curses.init_pair(self._darker, curses.COLOR_BLACK, dark_color)


PALETTES = {
    'hot': Palette.HOT,
    'io': Palette.IO,
    'wakeup': Palette.WAKEUP,
    'chain': Palette.CHAIN,
}
