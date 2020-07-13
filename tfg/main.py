#!/usr/bin/env python
"""Terminal flame graph.
Parse dtrace, perf, etc. output and display it as a flame graph inside your terminal emulator.
Use arrow keys to navigate around the flame graph. Use 'Enter' key to 'zoom in' to a call frame.

Python 2 and 3 compatible.
"""

import argparse
from tfg.calltree.calltree import CallFrameTree
from tfg.stackcollapsers.stackcollapser import StackCollapser
from tfg.stackcollapsers.dtracecollapser import DtraceCollapser
from tfg.stackcollapsers.perfcollapser import PerfCollapser
from tfg.stackcollapsers.pyspycollapser import PySpyCollapser
from tfg.browser.terminal import TerminalBrowser
from tfg.browser.palette import PALETTES


COLLAPSERS = {
    'none': StackCollapser,
    'dtrace': DtraceCollapser,
    'perf': PerfCollapser,
    'pyspy': PySpyCollapser,
}


def process_args(args):
    with open(args.file, 'r') as input_file:
        call_tree = CallFrameTree()
        collapser = COLLAPSERS[args.file_type](input_file)
        stacks = collapser.parse()
        for stack in stacks:
            call_tree.add_stack(stack[0], stack[1])
        if args.dump:
            call_tree.dump()
            return

        browser = TerminalBrowser(call_tree, args.ws_filler, PALETTES[args.palette])
        browser.display()

def main():
    parser = argparse.ArgumentParser(description='Command line flame graph browser')
    parser.add_argument('-t',
                        '--type',
                        type=str,
                        dest='file_type',
                        default='none',
                        choices=COLLAPSERS.keys(),
                        help='Input file type')
    parser.add_argument('--ws-filler',
                        type=str,
                        dest='ws_filler',
                        default=' ',
                        help="""Due to a bug (https://bugs.kde.org/show_bug.cgi?id=384620)
                                some versions of ncurses won't highlight the whitespace properly.
                                With this whitespace filler option you can specify any other
                                filler to use (e.g. -)""")
    parser.add_argument('-d', '--dump',
                        dest='dump',
                        action='store_true',
                        help='Dump collapsed stacks and quit')
    parser.add_argument('-p',
                        '--palette',
                        dest='palette',
                        default='hot',
                        choices=PALETTES.keys(),
                        help='Color palette')
    parser.add_argument('file', help='Input file to parse')

    process_args(parser.parse_args())
