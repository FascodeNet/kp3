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
# util.py
#

# Standard Library
from sys import stderr


ALL_OFF = "\033[0m"
BOLD    = "\033[1m"
BLUE    = f"{BOLD}\033[34m"
GREEN   = f"{BOLD}\033[32m"
RED     = f"{BOLD}\033[31m"
YELLOW  = f"{BOLD}\033[33m"


def msg(message: str) -> None:
    print(f"{GREEN}==>{ALL_OFF}{BOLD} {message}{ALL_OFF}")


def msg2(message: str) -> None:
    print(f"{BLUE}  ->{ALL_OFF}{BOLD} {message}{ALL_OFF}")


def error(message: str) -> None:
    print(f"{RED}==> ERROR:{ALL_OFF}{BOLD} {message}{ALL_OFF}", file=stderr)


def warn(message: str) -> None:
    print(f"{YELLOW}==> WARNING:{ALL_OFF}{BOLD} {message}{ALL_OFF}")
