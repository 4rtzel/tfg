"""Basic classes and functions for all stack collapsers.
"""

import re


def trim_offset(name):
    """_trim_offset(name: str) -> str
    Remove address offset from name.

    Example:
        some_function+0x42beef -> some_function
    """
    return re.sub(r'\+0x[0-9a-fA-F]+$', '', name)


class StackCollapserException(Exception):
    """Basis stack collapser exception. Used when parse error occured.
    """
    pass


class StackCollapser(object):
    """Basic class for all stack collapsers.

    All derived classes should implement a parse(self) -> list[(list[str], int)] function.
    StackCollapser can parse already collapsed stack (see parse()). It's useful when you
    already have a file with collapsed stack from previous runs of stackcollapser.
    """
    def __init__(self, input_file):
        """__init__(self, input_file: file)
        """
        self._input_file = input_file

    def parse(self):
        """parse(self) -> list[(list[str], int)]
        Parse self._input_file. Assume that self._input_file contains already collapsed stack.

        Example input:
            kernel`0xffffffff8074d27e;kernel`_sx_xlock 1
            kernel`0xffffffff8074d27e;kernel`_sx_xlock_hard 5
            kernel`0xffffffff8074d27e;kernel`fork_exit;if_cxgbe.ko`t4_eth_rx 1

        Example output:
            [
                (['kernel`0xffffffff8074d27e', 'kernel`_sx_xlock'], 1),
                (['kernel`0xffffffff8074d27e', 'kernel`_sx_xlock_hard], 5),
                (['kernel`0xffffffff8074d27e', 'kernel`fork_exit', 'if_cxgbe.ko`t4_eth_rx'], 1)
            ]
        """
        result = list()
        for i, line in enumerate([x.strip() for x in self._input_file], 1):
            if not line:
                continue
            # There should be only 2 entries. Example:
            # kernel`0xffffffff8074d27e;kernel`_sx_xlock 1
            try:
                frames, value = line.split()
                frames = [trim_offset(n) for n in frames.split(';')]
            except ValueError:
                raise StackCollapserException('Unable to parse line {}'.format(i))
            result.append((frames, int(value)))
        return result
