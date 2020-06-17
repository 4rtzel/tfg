"""FlameGraph terminal browser.
Provides a terminal interface to display and interact with a FlameGraph.
"""
import curses
from tfg.browser.visualtree import VisualFrameTree, fit_string, calculate_width
from tfg.browser.palette import Palette


class BrowserException(Exception):
    pass


class BrowserContext(object):
    """Common browser variables that can be modified by different windows.

    vft - main VisualFrameTree.
    palette - main Palette.
    ws_filler - whitespace filler.
    current_vf - current VisualFrame
    win_stack - windows stack
    """
    def __init__(self, vft, palette, ws_filler):
        self.vft = vft
        self.palette = palette
        self.ws_filler = ws_filler
        self.current_vf = None
        self.win_stack = []


class BrowserWindow(object):
    """Base class for all windows
    """
    def draw(self):
        raise BrowserException('Not implemented')

    def process_input(self, stdscr):
        """stdscr - window to read inputs from
        """
        raise BrowserException('Not implemented')


class FlameGraphWindow(BrowserWindow):
    """FlameGraph window
    """
    def __init__(self, stdscr, context):
        self._context = context
        self._width = curses.COLS
        self._height = curses.LINES - 1
        # _start_level is the very bottom frame that we're going to display. This
        # value can be changed if the number of levels > then the screen size.
        self._start_level = 0
        self._win = stdscr.subwin(self._height, self._width, 0, 0)

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def draw(self):
        # Create an invisible border for the window with a line at the bottom
        self._win.border(' ', ' ', ' ', curses.ACS_HLINE,
                         ' ', ' ', curses.ACS_HLINE, curses.ACS_HLINE)
        self._gradient = self._context.palette.gradient()
        # Drawing from the bottom to top
        y = self._height - 2
        for vfs in self._context.vft.level_traversal():
            # Skip until the self._start_level
            if vfs[0].y < self._start_level:
                continue
            for vf in vfs:
                if vf.width != 0:
                    self._draw_frame(vf, y)
            y -= 1
            if y < 0:
                break

    def _draw_frame(self, vf, y):
        color = next(self._gradient)

        # We want to draw zoomed frames with a bit ligher colors.
        if vf.zoomed:
            attrs = self._context.palette.lighter
        else:
            attrs = color

        # Highlight the current visual frame.
        if vf == self._context.current_vf:
            attrs |= curses.A_STANDOUT
        try:
            self._win.addstr(y, vf.x, vf.text, attrs)
        except curses.error as cer:
            raise BrowserException('error: {}, x: {}, y: {}, text: {}'.format(
                cer, vf.x, y, vf.text))

    def process_input(self, stdscr):
        char = stdscr.getch()
        # Quit.
        if char == ord('q'):
            self._context.win_stack.pop()
        # Switch combined frames.
        elif char == ord('c'):
            self._context.vft.with_combined_frames = not self._context.vft.with_combined_frames
            self._context.current_vf = self._context.vft.rebuild_tree(self._context.vft.start_vf)
            self._context.vft.link_frames()
        # Go down to the parent.
        elif char == curses.KEY_DOWN:
            if self._context.current_vf.parent_vf is not None:
                self._context.current_vf = self._context.current_vf.parent_vf
            # Go down if the current visual frame is below the window.
            if self._context.current_vf.y < self._start_level:
                self._start_level -= 1
        # Go up to the first visible children.
        elif char == curses.KEY_UP:
            for frame in self._context.current_vf.frames:
                if frame.width > 0:
                    self._context.current_vf = frame
                    break
            # Go up if the current visual frame is above the window.
            if self._context.current_vf.y > self._start_level + self._height - 2:
                self._start_level += 1
        # Go left to the sibling.
        elif char == curses.KEY_LEFT:
            if self._context.current_vf.left_vf is not None:
                self._context.current_vf = self._context.current_vf.left_vf
        # Go right to the sibling.
        elif char == curses.KEY_RIGHT:
            if self._context.current_vf.right_vf:
                self._context.current_vf = self._context.current_vf.right_vf
        # Zoom to the current visual frame.
        elif char in [curses.KEY_ENTER, ord('\n')]:
            if self._context.current_vf.cf is not None:
                self._context.current_vf = self._context.vft.rebuild_tree(self._context.current_vf)
                self._context.vft.link_frames()
            elif self._context.current_vf.combined_frames:
                self._context.win_stack.append(SelectVisualFrameWindow(stdscr, self._context))
        # Reset.
        elif char == ord('r'):
            self._context.current_vf = self._context.vft.rebuild_tree(self._context.vft.head)
            self._context.vft.link_frames()
        # Ignore anything else


class StatusWindow(BrowserWindow):
    """Status window.
    Simply displays the full name of the current visual frame
    """
    def __init__(self, stdscr, context):
        self._context = context
        self._width = curses.COLS
        self._height = 1
        self._win = stdscr.subwin(self._height, self._width, curses.LINES - 1, 0)

    def draw(self):
        if self._context.current_vf.cf is not None:
            cf = self._context.current_vf.cf
            parent = cf.parent or cf
            self_time_total = int(cf.base_count * 100 / self._context.vft._call_tree.head.count)
            combined_time_total = int(cf.count * 100 / self._context.vft._call_tree.head.count)
            self_time_parent = int(cf.base_count * 100 / parent.count)
            combined_time_parent = int(cf.count * 100 / parent.count)
            name = fit_string(
                "%s self=%s%% aggregate=%s%% self/parent=%s%% aggregate/parent=%s%%" %
                (self._context.current_vf.cf.name, self_time_total, self_time_parent, combined_time_total,
                 combined_time_parent),
                self._width - 1, ' ')
        else:
            name = self._context.current_vf.text
        self._win.addstr(0, 0, name)

    def process_input(self, stdscr):
        # Focus can't be on the status window, so we just quit.
        self._context.win_stack.pop()


class SelectVisualFrameWindow(BrowserWindow):
    """Select visual frame window.
    Allow to choose a visual frame to zoom in from combined frames.
    """
    def __init__(self, stdscr, context):
        self._context = context
        self._vf = self._context.current_vf
        self._BORDER_SIZE = 2
        # Height should be enough to fit all combined frames but not more than the screen size.
        self._height = min(len(self._vf.combined_frames) + self._BORDER_SIZE, curses.LINES)
        # We want to put a numbers before each frame, so we need to calculate the size of
        # the biggest number.
        self._NUMBER_SIZE = len(str(self._height))
        # Full prefix size = number size + dot size + space size:
        # ' 42. '
        # |   | |
        # |   |  \
        # |    \   ->space size
        #  \     -> dot size
        #    -> number size
        self._PREFIX_SIZE = self._NUMBER_SIZE + 2
        # Width should be enough to fit the longest frame name but not more than the screen size.
        self._width = min(max(len(f.cf.name) for f in self._vf.combined_frames)
                          + self._BORDER_SIZE + self._PREFIX_SIZE,
                          curses.COLS)
        x = (curses.COLS - self._width) // 2
        y = (curses.LINES - self._height) // 2
        self._win = stdscr.subwin(self._height, self._width, y, x)
        # If there is too many frames we will only display part of them [from, to)
        self._from = 0
        self._to = self._height - self._BORDER_SIZE
        # Current selected frame
        self._current = 0

    def draw(self):
        self._win.box(0, 0)
        x = self._BORDER_SIZE // 2
        y = self._BORDER_SIZE // 2
        for vf in self._vf.combined_frames[self._from:self._to]:
            number_string = '{:>{width}}.'.format(y + self._from, width=self._NUMBER_SIZE)
            name = '{} {}'.format(number_string, vf.cf.name)
            self._win.addstr(y, x, fit_string(name, self._width - self._BORDER_SIZE, ' '))

            # Redraw part of the string with color to show the impact percentage
            width = calculate_width(vf.count, self._vf.count,
                                    self._width - self._PREFIX_SIZE - self._BORDER_SIZE)
            color_name = fit_string(vf.cf.name, width, self._context.ws_filler)
            self._win.addstr(y, self._PREFIX_SIZE + 1, color_name, self._context.palette.normal)

            # Highlight a number for the current line
            if self._current == y + self._from - 1:
                self._win.addstr(y, 1, fit_string(number_string, self._NUMBER_SIZE, ' '),
                                 curses.A_STANDOUT)
            y += 1

    def process_input(self, stdscr):
        char = stdscr.getch()
        # Quit.
        if char == ord('q'):
            self._context.win_stack.pop()
        # Go down.
        elif char == curses.KEY_DOWN:
            if self._current < len(self._vf.combined_frames) - 1:
                self._current += 1
            if self._current >= self._to:
                self._from += 1
                self._to += 1
        # Go up.
        elif char == curses.KEY_UP:
            if self._current > 0:
                self._current -= 1
            if self._current < self._from:
                self._from -= 1
                self._to -= 1
        # Select a frame and quit.
        elif char in [curses.KEY_ENTER, ord('\n')]:
            self._context.current_vf = self._context.vft.rebuild_tree(self._vf.combined_frames[self._current])
            self._context.vft.link_frames()
            self._context.win_stack.pop()


class TerminalBrowser(object):
    """Terminal browser power by ncurses library.
    """
    def __init__(self, call_tree, ws_filler, palette_type):
        self._call_tree = call_tree
        self._ws_filler = ws_filler
        self._palette_type = palette_type
        self._fg_win = None
        self._select_vf_win = None
        self._context = None

    def display(self):
        # This wrapper will initialize all curses stuff before calling self._display() and
        # it will also properly deinit them when we'll return from self._display() or raise
        # an exception.
        curses.wrapper(self._display)

    def _display(self, stdscr):
        palette = Palette(self._palette_type)
        self._context = BrowserContext(None, palette, self._ws_filler)
        vf_win = FlameGraphWindow(stdscr, self._context)
        vft = VisualFrameTree(self._call_tree, 0, 0, vf_win.width, vf_win.height - 1, self._ws_filler)
        self._context.vft = vft
        self._context.current_vf = self._context.vft.head
        self._context.win_stack.append(StatusWindow(stdscr, self._context))
        self._context.win_stack.append(vf_win)

        while self._context.win_stack:
            stdscr.clear()
            # Draw all windows but process input only on the last one
            for win in self._context.win_stack:
                win.draw()
            self._context.win_stack[-1].process_input(stdscr)
