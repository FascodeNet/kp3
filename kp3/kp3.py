#!/usr/bin/env python3
# Standard Library
import sys
from os import getcwd, path

# Local Library
from msg import msg, msg2,  error
from depends import check_depends
from builder import Builder

if __name__ == "__main__":
    ROOT = getcwd()
    msg("Check PKGBUILD...")

    if not path.isfile(path.join(ROOT, "PKGBUILD")):
        error("PKGBUILD not found")
        sys.exit(1)

    aur_pkgs = check_depends()

    with Builder() as builder:
        builder.build(aur_pkgs)
