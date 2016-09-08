#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import radiopaedia.commands
import fma.commands
from spiderpig import run_spiderpig


if __name__ == '__main__':
    run_spiderpig(
        namespaced_command_packages={
            'radiopaedia': radiopaedia.commands,
            'fma': fma.commands,
        }
    )
