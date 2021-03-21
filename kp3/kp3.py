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
# kp3.py
#

#-- Import --#
# Standard Library
import sys

from json    import load
from os      import getcwd
from os.path import abspath, dirname, isdir, join
from re      import sub
from shlex   import join as shell_join
from signal  import SIGINT, SIGTERM, signal
from typing  import Optional
from urllib  import request

# Local Library
from util import error, msg, msg2

# Third-Party Library
try:
    from docker        import from_env
    from docker.errors import ImageNotFound
    from docker.types  import Mount
except ImportError:
    error("python-docker is not installed")

try:
    from pyalpm        import Package
    from pycman.config import init_with_config
except ImportError:
    error("pyalpm is not installed")


#-- Define --#
TRANSTABLE = str.maketrans({
    '(': None,
    ')': None,
    "'": None
})

ROOT       = getcwd()
SCRIPTROOT = abspath(dirname(__file__))

# Docker
CLIENT     = from_env()

# Pyalpm
HANDLE     = init_with_config(join(SCRIPTROOT, "pacman.conf"))
LOCALDB    = HANDLE.get_localdb()
SYNCDBS    = HANDLE.get_syncdbs()


#-- Class --#
class Kp3(object):
    aur_pkgs = {}

    def __init__(self, path = join(ROOT, "PKGBUILD")) -> None:
        self.path = path
        self.check_depends()

        msg("Check image")

        try:
            CLIENT.images.get("archlinux:latest")
        except ImageNotFound:
            msg("Pull image")
            CLIENT.images.pull("archlinux:latest")

        msg("Create container")

        self.container = CLIENT.containers.create(
            "archlinux:latest",
            environment = {"TERM":    "xterm-256color"},
            mounts      = [Mount("/home/kp3/build", ROOT, type="bind")],
            tty         = True
        )

        self.api = self.container.client.api


    def __enter__(self):
        self.start()
        return self


    def __exit__(self, exit_type, *args) -> None:
        if not exit_type:
            self.close()


    def start(self) -> None:
        msg("Start kp3")

        # Connect signal
        signal(SIGTERM, self.sig_kill)
        signal(SIGINT,  self.sig_kill)

        # Start container
        self.container.start()

        # Setup mirror
        msg("Setup mirror")
        self.run_quit(["bash", "-c", "echo 'Server = http://mirrors.cat.net/archlinux/$repo/os/$arch' > /etc/pacman.d/mirrorlist"])

        # Install base-devel, git
        msg("Install base-devel, git")
        self.run(["pacman", "-Syyu", "--noconfirm", "--needed", "base-devel", "git"])

        # Create user
        msg("Create user")
        self.run_quit(["useradd", "-m", "-s", "/bin/bash", "kp3"])
        self.run_quit(["usermod", "-U", "-g", "kp3", "kp3"])
        self.run_quit(["groupadd", "sudo"])
        self.run_quit(["usermod", "-aG", "sudo", "kp3"])
        self.run_quit(["chmod", "700", "-R", "/home/kp3"])
        self.run_quit(["chown", "kp3:kp3", "-R", "/home/kp3"])
        self.run_quit(["bash", "-c", "echo 'kp3 ALL=NOPASSWD: ALL' >> /etc/sudoers"])


    def close(self) -> None:
        msg("Close kp3")
        self.container.remove(force=True)


    def build(self) -> None:
        self.build_aur_pkgs()

        msg("Build packages")
        self.run(
            ["makepkg", "--clean", "--cleanbuild", "--ignorearch", "--force", "--syncdeps", "--noconfirm"],
            user    = "kp3",
            workdir = "/home/kp3/build"
        )


    # Signal
    def sig_kill(self, *args) -> None:
        error("\nKill kp3")
        self.container.remove(force=True)
        sys.exit(1)


    # AUR Util
    def get_pkg(self, pkgname: str) -> Optional[Package]:
        for db in SYNCDBS:
            pkg = db.get_pkg(pkgname)

            if pkg:
                return pkg
            
            for pkg in db.search(pkgname):
                if pkgname in [sub(r"=.*$", "", provide) for provide in pkg.provides]:
                    return pkg

        return None


    def check_aur_depends(self, pkgname: str) -> None:
        url = f"https://aur.archlinux.org/rpc/?v=5&type=info&arg[]={pkgname}"

        with request.urlopen(url) as response:
            info = load(response)["results"]

        if len(info) == 0:
            error(f"{pkgname} is not found")
            sys.exit(1)

        self.aur_pkgs[pkgname] = f"https://aur.archlinux.org/{pkgname}.git/"

        depends = []

        if "Depends" in info:
            depends += info["Depends"]

        if "MakeDepends" in info:
            depends += info["MakeDepends"]

        if len(depends) == 0:
            return

        depends = [pkgname for pkgname in depends if not self.get_pkg(pkgname)]

        if len(depends) != 0:
            for pkg in depends:
                self.check_aur_depends(pkg)


    def check_depends(self) -> None:
        with open(self.path) as f:
            lines = [line.strip() for line in f.readlines()]

        in_brackets = False
        data        = ""
        depends     = []

        for line in lines:
            if "depends" in line or "makedepends" in line:
                in_brackets = True
                data = line
            elif in_brackets:
                data += " " + line

            if in_brackets and ')' in line:
                in_brackets = False
                depends += [sub(r">.*$", "", line) for line in data.split("=", 1)[1].translate(TRANSTABLE).split()]

        depends = [pkgname for pkgname in depends if not self.get_pkg(pkgname)]

        if len(depends) == 0:
            return

        for pkg in depends:
            print(pkg)
            self.check_aur_depends(pkg)


    # Docker Util
    def check_return_code(self, cmd: list, exit_code: int)-> None:
        if exit_code != 0:
            error("Command Failed")
            msg2(f"Command: {shell_join(cmd)}")
            msg2(f"Return Code: {exit_code}")
            self.container.remove(force=True)
            sys.exit(1)


    def run(self, cmd: list, **kwargs) -> None:
        response = self.api.exec_create(
            self.container.id,
            cmd,
            tty = True,
            **kwargs
        )

        output = self.api.exec_start(
            response["Id"],
            tty    = True,
            stream = True
        )

        for line in output:
            print(line.decode(), end="")

        self.check_return_code(
            cmd,
            self.api.exec_inspect(response["Id"])["ExitCode"]
        )


    def run_quit(self, cmd: list) -> None:
        exit_code, _= self.container.exec_run(cmd)
        self.check_return_code(cmd, exit_code)


    # Build Util
    def build_aur_pkgs(self) -> None:
        if len(self.aur_pkgs) == 0:
            return

        msg("Build aur packages")

        for pkgname, url in self.aur_pkgs.items():
            self.run(
                ["git", "clone", url],
                user    = "kp3",
                workdir = "/home/kp3"
            )

            self.run(
                ["makepkg", "--clean", "--cleanbuild", "--force", "--ignorearch", "--install", "--noconfirm", "--syncdeps"],
                user    = "kp3",
                workdir = "/home/kp3/" + pkgname
            )
