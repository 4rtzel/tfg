# Terminal flame graph (tfg)
Command line tool to parse **DTrace** and **perf** output and display it as a flame graph inside your terminal emulator.

## Motivation
Sometimes you may want to visualize a stack trace with [FlameGraph](https://github.com/brendangregg/FlameGraph) of your 
application running on a server, so you will need to copy a stack traces from your server to your local machine, 
create a .svg file and open it in the browser.
This process can get tedious if you're doing that a lot or if you just want to take a quick look of stack traces.

This tool is trying to solve that by letting you view the stack traces inside your terminal emulator.

## Getting Started
This project is trying to be as simple and self-contained as possible, so the only real dependency here (besides Python interpreter)
is [libncurses](https://www.gnu.org/software/ncurses/) which should probably be installed on every system.

Also, this project is Python 2/3 compatible.

To start, simple ```git clone https://github.com/4rtzel/tfg``` and you're good to go.

## Usage
* run **DTrace** or **perf** tool to collect stack traces

  **DTrace:**
  ```bash
  dtrace -n 'profile-197 {@[ustack(100)]=count()' > on.stacks
  ```
  **perf:**
  ```bash
  perf record -g -a -- sleep 1
  perf script > on.stacks
  ```
* run **tfg.py** and specify an input file type
  ```bash
  tfg.py -t perf on.stacks
  ```
* use the following keybindings to navigate

  ```→```, ```←```, ```↑```, ```↓``` - navigation
  
  ```c``` - on/off combined frames
  
  ```Enter``` - zoom to a selected frame
  
  ```r``` - reset
  
  ```q``` - quit


Here is an example of running **tfg** with **perf**:
[![asciicast](https://asciinema.org/a/UpqUa5iZCFzmoFEGjjqYjPI3X.svg)](https://asciinema.org/a/UpqUa5iZCFzmoFEGjjqYjPI3X)

## TODO
* Tests
* Search option and highlight
* Diff view
