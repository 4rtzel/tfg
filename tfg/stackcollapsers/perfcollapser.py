"""Perf stack collapser. Used to collapse stacks produced by 'perf script' tool.
Perf script output example:

    init     1 [002] 4042688.470566:     454356 cycles:
        5028bd intel_idle (/usr/lib/debug/lib/modules/2.6.32-696.23.1.el6.x86_64/vmlinux)
        64a99e cpuidle_idle_call (/usr/lib/debug/lib/modules/2.6.32-696.23.1.el6.x86_64/vmlinux)
        209fc9 cpu_idle (/usr/lib/debug/lib/modules/2.6.32-696.23.1.el6.x86_64/vmlinux)
        74c25b start_secondary (/usr/lib/debug/lib/modules/2.6.32-696.23.1.el6.x86_64/vmlinux)

    ...

Read more here: https://github.com/brendangregg/FlameGraph/blob/master/stackcollapse-perf.pl
"""

from itertools import takewhile
from tfg.stackcollapsers.stackcollapser import StackCollapser, StackCollapserException, trim_offset

class PerfCollapser(StackCollapser):
    def __init__(self, input_file):
        """__init__(self, input_file: file)
        """
        super(PerfCollapser, self).__init__(input_file)

    def parse(self):
        """parse(self) -> list[(list[str], int)]
        """
        result = []
        stack = []
        comm = ''
        for i, line in enumerate([x.strip() for x in self._input_file], 1):
            if not line:
                if comm: # If line is empty and we have a comm name
                    stack.append(comm)
                    result.append((stack[::-1], 1))
                    stack = []
                    comm = ''
                continue

            fields = line.split()
            if len(fields) > 3:
                comm = extract_comm(fields)
                if not comm:
                    raise StackCollapserException('Failed to parse line {}'.format(i))
            else:
                try:
                    stack.append(trim_offset(extract_stack_name(fields)))
                except IndexError:
                    raise StackCollapserException('Failed to parse line {}'.format(i))
        return result

def extract_comm(fields):
    """_extract_comm(self, fields: list[str]) -> str
    Extract a command name (commonly used as 'comm') from fields

    Examples:
        ['Web', '123', 'cycles:'] -> Web
        ['Google', 'Chrome', '321', 'cycles:'] -> Google_Chrome
    """
    return '_'.join(takewhile(lambda x: not x.isdigit(), fields))

def extract_stack_name(fields):
    """_extract_stack_name(self, fields: list[str]) -> str
    Extract a stack name from the fields

    Examples:
        ffffffff818244f2 [unknown] ([kernel.kallsyms]) -> [kernel.kallsyms]
        1094d __GI___libc_recvmsg (/lib/x86_64-linux-gnu/libpthread-2.23.so) -> __GI__libc_recvmsg

    """
    if fields[1] == '[unknown]':
        return to_module_name(fields[2][1:-1])
    return fields[1]

def to_module_name(field):
    """_to_module_name(self, field: str) -> str
    Convert module name to match syntax used in https://github.com/brendangregg/FlameGraph

    Examples:
        [unknown] -> [unknown]'
        /usr/bin/firefox -> [firefox]
    """
    if field != '[unknown]':
        field = '[{}]'.format(field.split('/')[-1])
    return field
