#!/usr/bin/env python3
# Standard Library
from subprocess import run, PIPE
from os.path import abspath, join, dirname, isdir
from urllib import request
from json import loads
import sys
import tarfile
from io import BytesIO

# Local Library
from msg import msg2,  error, msg

# Third-Party Library
import pycman

ROOT = abspath(dirname(__file__))

HANDLE = pycman.config.init_with_config(join(ROOT, "pacman.conf"))

def get_pkg(pkgname):
    for db in HANDLE.get_syncdbs():
        pkg = db.get_pkg(pkgname)

        if pkg: return pkg

    return None

def check_depends():
    msg("Check Package")

    output = run(["bash", join(ROOT, "get_depends.sh")], stdout=PIPE, text=True)
    pkgs = [pkg for pkg in output.stdout.strip().split() if not get_pkg(pkg)]

    if len(pkgs) == 0: return

    urls = []

    for pkg in pkgs:
        msg2(f"Check {pkg}...")
        url = f"https://aur.archlinux.org/cgit/aur.git/?h={pkg}"

        try:
            with request.urlopen(url):
                urls.append(f"https://aur.archlinux.org/{pkg}.git/")
        except:
            error(f"{pkg} not found")
            sys.exit(1)
    
    return urls
