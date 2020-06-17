"""Call frames stack represenation as a tree.
"""

class CallFrameNode(object):
    """Stack frame node.
    Represent a single stack frame.

    name - original stack frame name.
    frames - children stack frames.
    base_count - original sample count for the this node.
    count - samle count for all children. Useful to calculate the 'weight' of the node.
    """

    def __init__(self, name, frames=None, base_count=0, count=0, parent=None):
        """__init__(self, name: str, frames: list[CallFrameNode], base_count: int, count: int)
        """
        self.name = name
        if frames is None:
            self.frames = []
        else:
            self.frames = frames[:]
        self.base_count = base_count
        self.count = count
        self.parent = parent

    def __repr__(self):
        return 'CallFrameNode(name={}, base_count={}, count={})'.format(
            self.name, self.base_count, self.count)


class CallFrameTree(object):
    """Tree based representation of call frames.
    By default CallFrameTree consist of only one 'all' (head) node.
    add_stack() function should be used to add additional frames to the tree.
    It will create nodes for all frames (if needed) and will calculate sample
    count for each of them.

    Example:
        frames1 = ['main', 'foo', 'bar']
        frames2 = ['main', 'foo', 'panic']

        Calling add_stack():
            add_stack(frames1, 1)
            add_stack(frames2, 1)
        will result in the following tree structure:

        'all' -> 'main' -> 'foo' -> 'bar'
                             |
                             -----> 'panic'
    """
    def __init__(self):
        self._head = CallFrameNode('all')

    def add_stack(self, frames, count):
        """add_stack(self, frames: list[str], count: int)
        Add frames to the tree with sample count.
        """
        self._head.count += count
        self._insert_frame(self._head, frames, count)

    @property
    def head(self):
        """Head node.
        """
        return self._head

    def dump(self):
        """Dump tree to stdout.
        This should produce the same output as any stackcollapse*.pl from
        https://github.com/brendangregg/FlameGraph.
        """
        self._dump(self._head, [])

    def _dump(self, cf, callstack):
        # Only original top call frames have base_count > 0
        if cf.base_count > 0:
            print('{} {}'.format(';'.join(f.name for f in callstack), cf.base_count))
        for child_cf in cf.frames:
            callstack.append(child_cf)
            self._dump(child_cf, callstack)
            callstack.pop()

    def _insert_frame(self, start_frame, frames, count):
        if not frames:
            return
        frame = self._get_or_create_frame(start_frame, frames)
        frame.count += count
        # Save the original base_count
        if len(frames) == 1:
            frame.base_count += count
        self._insert_frame(frame, frames[1:], count)

    def _get_or_create_frame(self, start_frame, frames):
        for frame in start_frame.frames:
            if frame.name == frames[0]:
                return frame
        else:
            start_frame.frames.append(CallFrameNode(frames[0], parent=start_frame))
            return start_frame.frames[-1]
