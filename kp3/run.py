#!/usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# mk-linux419
# Twitter: @fascoder_4
# Email  : mk419@fascode.net
#
# (c) 2019-2021 Fascode Network.
#
# run.py
#

# Standard Library
import sys
from os import getcwd, path

# Local Library
from util import msg, msg2,  error
from kp3 import Kp3

if __name__ == "__main__":
    ROOT = getcwd()
    msg("Check PKGBUILD...")

    if not path.isfile(path.join(ROOT, "PKGBUILD")):
        error("PKGBUILD not found")
        sys.exit(1)

    with Kp3() as builder:
        builder.build()
