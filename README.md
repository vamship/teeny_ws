# teeny_ws
A tiny web server module for Micropython applications running on
microcontrollers such as the ESP32 and ESP8266. Supports fixed responses,
chunked responses and web socket communication.

# Usage
Basic usage instructions for your module:

```python
# Example usage will depend on what you add to your module
# For function-based modules:
# from teeny_ws import some_function
# result = some_function(param)

# For class-based modules:
from teeny_ws import HttpServer
server = HttpServer()
# Add your specific usage examples here
```

Check out the [API Documentation](/docs/index.html) for more details.

# Installation

For boards that are connected to the internet, you can install this module using
[mip](https://docs.micropython.org/en/latest/reference/packages.html) via
the MicroPython REPL or a script. See `mip` documentation for details.

Alternatively (preferred) for boards that are not connected to the internet,
you use `mip` via
[mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) by
following the steps below.

##  Prerequisites

The prerequisites described in this document include python packages that can be
installed using `pip`. However, using `uv` to install these packages is
preferred, and is described below.

### uv
> NOTE: This is an optional step that can be skipped if you prefer to use `pip`
> directly to install the required packages.

See the [uv documentation](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)
for installation instructions. On macOS, you can use Homebrew:
```bash
brew install uv
```

### mpremote
Mpremote is a tool for interacting with MicroPython boards. It can be installed
using uv as follows:
```bash
uv tool install mpremote
```
> NOTE: Ensure that the uv tool install path (`~/.local/bin`) is in your system
> PATH, or use `uv tool run mpremote` to run the tool.


## Installation Steps

The preferred way to install this module is to use `mip` via `mpremote`. Before
running the command below:
1. Ensure that your MicroPython board is connected to your computer.
1. Make note of the serial port your board is connected to (ex: `/dev/ttyUSB0`)
1. In most cases, `mpremote` will automatically detect the correct port. If
   not, or if you have multiple boards connected, you can first connect to the
   board by running the following command.
   ```bash
   # You might not need to do this unless you have multiple boards connected.
   mpremote connect <your-port>
   ```
1. Install the module using the following command:
   ```bash
   mpremote mip install github:vamship/teeny_ws
   ```
1. You can now use the module in your MicroPython scripts by importing it:
   ```python
   # Import will depend on what you've added to your module
   # See usage examples above for specific import patterns
   ```

# Development
This section describes the process to make changes to the module and build the
output.

## Prerequisites
In order to develop this module, you will need the following tools.

### mpy-cross
This is the MicroPython cross compiler that compiles Python source files
(`.py`) into bytecode files (`.mpy`). You can install `mpy-cross` using `uv` as
follows:

```bash
uv tool install mpy-cross
```

### make
Make is used to automate the build process and can be installed on macOS by
installing Xcode command line tools:
Homebrew:
```bash
xcode-select --install
```

## Building

First clone the repository:
```bash
git clone https://github.com/vamship/teeny_ws.git
```

Build the module using the `make` command:
```bash
make clean build
```

This will create a `build` directory containing the compiled `.mpy` files. These
files must be included in the source control repository so that it can be
installed using `mip`.

> NOTE: If new files are added to the source code, you will need to update the
> `package.json` file to specify which files should be included when the module
> is installed using `mip`. See
> [mip documentation](https://docs.micropython.org/en/latest/reference/packages.html#writing-publishing-packages)
> for more information.
