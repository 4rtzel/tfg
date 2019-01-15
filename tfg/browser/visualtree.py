"""Call frames stack representation as a visual tree.
Visual tree is a tree where each node contains an enough information to draw it on screen.
"""
from itertools import tee
from functools import partial


def pairwise(iterable):
    """Return an iterator to a pair
    s[] -> (s[0], s[1]), (s[2], s[3]), (s[4], s[5]), ...
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def fit_string(text, width, ws_filler):
    """fit_string(text: str, width: int, ws_filler: str)
    Fit a 'text' string inside [0, width) range. Use ws_filler as a white space filler.
    """
    if len(text) < width:
        return ''.join([text[:width], ws_filler * (width - len(text))])
    return text[:width]


def calculate_width(count, parent_count, parent_width):
    """calculate_width(count: int, parent_count: int, parent_width: int)
    Calculate string width based on parent width and sample count.
    """
    return int(count * parent_width // parent_count) if parent_count != 0 else 0


class VisualFrameNode(object):
    """Visual stack frame node.
    Store all necessary information to draw a stack frame node.

    Sometimes the number of samples for a stack frame can be so small that the calculated
    visual frame width is equal to 0. In that case, we will collect all those 'small' frames
    and create a single 'combined frame'. The user later, could select this frame and choose
    which 'small' frame he would like to examine.

    x - x coordinate on screen.
    y - y coordinate on screem.
    count - sample count (see CallFrameNode).
    width - width of the frame.
    text - text to display (always len(text) == width). To get the full text use 'cf'.
        Note: all those neighbor visual frames are used to easily navigate around a flame graph.
    parent_vf - parent VisualFrameNode.
    left_vf - left VisualFrameNode.
    right_vf - right VisualFrameNode.
    frames - child frames
    cf - original CallFrameNode. Equal to None in case of combined frames.
    zoomed - True if we're zooming in this frame.
    combined_frames - A list of combined frames. [CallFrameNode].
    """

    def __init__(self, x, y, count, width, text, pvf=None, lvf=None, rvf=None, cf=None):
        self.x = x
        self.y = y
        self.count = count
        self.width = width
        self.text = text
        self.parent_vf = pvf
        self.left_vf = lvf
        self.right_vf = rvf
        self.frames = []
        self.cf = cf
        self.zoomed = False
        self.combined_frames = []


class VisualFrameTree(object):
    def __init__(self, call_tree, x, y, width, height, ws_filler=' ', with_combined_frames=True):
        """__init__(self, call_tree: CallFrameTree, x: int, y: int, width: int, height: int,
                    ws_filler:str, with_combined_frames: bool)
        (x, y) - top left corner of the area to draw on.
        (width, height) - size of the area to draw on.
        """
        self._call_tree = call_tree
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._ws_filler = ws_filler
        self._start_vf = None
        self._with_combined_frames = with_combined_frames
        self.rebuild_tree()
        self.link_frames()

    def rebuild_tree(self, start_vf=None):
        """Rebuild the whole tree. Use start_vf as a zoomed frame.
        """
        text = fit_string(self._call_tree.head.name, self._width, self._ws_filler)
        self._head = VisualFrameNode(self._x, 0, self._call_tree.head.count, self._width, text)
        self._head.cf = self._call_tree.head
        self._head.zoomed = True
        start_vf = self._create_start_vf(start_vf, self._width)
        self._create_vf_children(start_vf, start_vf.cf)
        return start_vf

    def link_frames(self):
        """Link left and right frames.
        """
        for lvf, rvf in pairwise(self.bfs_traversal()):
            lvf.left_vf = rvf
            rvf.right_vf = lvf

    def dfs_traversal(self):
        """Return depth-first search traversal iterator.
        """
        def dfs_iterator(vf):
            yield vf
            for child_vf in vf.frames:
                for vf_yield in dfs_iterator(child_vf):
                    yield vf_yield
        return partial(dfs_iterator, self._head)()

    def bfs_traversal(self):
        """Return breadth-first search traversal iterator.
        """
        def bfs_iterator(vf):
            queue = [vf]
            while queue:
                vf = queue.pop(0)
                yield vf
                queue.extend(vf.frames)
        return partial(bfs_iterator, self._head)()

    def level_traversal(self):
        """Return level traversal iterator.
        """
        def level_iterator(vf):
            bfs = self.bfs_traversal()
            vfs = [next(bfs)]
            for vf in bfs:
                if vfs[0].y == vf.y:
                    vfs.append(vf)
                else:
                    yield vfs
                    vfs = [vf]
            if vfs:
                yield vfs
        return partial(level_iterator, self._head)()

    @property
    def with_combined_frames(self):
        return self._with_combined_frames

    @with_combined_frames.setter
    def with_combined_frames(self, value):
        self._with_combined_frames = value

    @property
    def head(self):
        return self._head

    @property
    def start_vf(self):
        return self._start_vf

    def _create_start_vf(self, start_vf, width):
        """Create start visual frame.
        """
        if start_vf is not None and start_vf != self._head:
            start_vf_parents = []
            start_vf_parent = start_vf
            while start_vf_parent is not None:
                start_vf_parents.append(start_vf_parent)
                start_vf_parent = start_vf_parent.parent_vf

            self._start_vf = self._head
            for parent in start_vf_parents[:-1][::-1]:
                text = fit_string(parent.cf.name, width, self._ws_filler)
                vf = VisualFrameNode(self._x, parent.y, parent.count, width, text, self._start_vf)
                vf.cf = parent.cf
                self._start_vf.frames.append(vf)
                self._start_vf = self._start_vf.frames[-1]
                self._start_vf.zoomed = True
        else:
            self._start_vf = self._head
        return self._start_vf

    def _create_vf_children(self, vf, cf):
        """Create children for 'vf' from 'cf.frames'.
        """
        if not cf.frames:
            return

        x = vf.x + vf.width
        # All calculated widths
        vf_widths = [calculate_width(c.count, vf.count, vf.width) for c in cf.frames]
        # If at least one children has width == 0
        has_zero_vf = min(vf_widths) == 0
        vf_total_width = sum(vf_widths)
        has_combined = self._with_combined_frames and has_zero_vf

        combined_vfs = []
        for child_cf in sorted(cf.frames, key=lambda c: c.name, reverse=True):
            child_vf = self._create_vf(x,
                                       vf.y + 1,
                                       vf,
                                       child_cf,
                                       has_combined and vf_total_width == vf.width)
            x -= child_vf.width
            # We will combine all vfs with width == 0 in one vf
            if child_vf.width > 0:
                self._create_vf_children(child_vf, child_cf)
                vf.frames.append(child_vf)
            else:
                combined_vfs.append(child_vf)

        # Push combined frame to 'vf'
        if has_combined:
            combined_vfs_total_count = sum(c.count for c in combined_vfs)
            vf_child = VisualFrameNode(x - 1, vf.y + 1, combined_vfs_total_count, 1, '+', vf)
            vf_child.combined_frames = combined_vfs
            vf.frames.append(vf_child)

    def _create_vf(self, x, y, parent_vf, cf, has_combined):
        """Create a visual frame.
        """
        width = parent_vf.width
        if has_combined:
            width -= 1
        width = calculate_width(cf.count, parent_vf.count, width)
        text = fit_string(cf.name, width, self._ws_filler)
        return VisualFrameNode(x - width, y, cf.count, width, text, parent_vf, cf=cf)
