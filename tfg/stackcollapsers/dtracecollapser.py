"""DTrace stack collapser. Used to collapse stacks produced by DTrace tool.
DTrace output example:

    libc.so.7`memcmp+0x16
    tcsh`0x4485a3
    tcsh`0x40d7dc
    tcsh`0x405126
    tcsh`0x40395f
    ld-elf.so.1`0xc0067b000
       42

    ...

Read more here: https://github.com/brendangregg/FlameGraph/blob/master/stackcollapse.pl
"""

from tfg.stackcollapsers.stackcollapser import StackCollapser, StackCollapserException, trim_offset


class DtraceCollapser(StackCollapser):
    def __init__(self, input_file):
        """__init__(self, input_file: file)
        """
        super(DtraceCollapser, self).__init__(input_file)

    def parse(self):
        """parse(self) -> list[(list[str], int)]
        """
        result = []
        stack = []
        for i, line in enumerate([x.strip() for x in self._input_file], 1):
            if not line:
                continue
            try:
                count = int(line)
                if not stack:
                    raise StackCollapserException('Found a number at line {} but the stack is empty'.format(i))
                result.append((stack[::-1], count))
                stack = []
            except ValueError:
                stack.append(trim_offset(line))

        return result
