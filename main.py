#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import radiopaedia.commands
from spiderpig import run_spiderpig


if __name__ == '__main__':
    run_spiderpig(
        command_packages=[radiopaedia.commands]
    )
