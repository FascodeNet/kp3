#!/usr/bin/env python3
# Standard Library
import sys
from os import getcwd
from shlex import join
from shutil import get_terminal_size
from signal import SIGINT, SIGTERM, signal

# Local Library
from msg import msg, msg2,  error

# Third-Party Library
import docker
from docker.types import Mount

ROOT = getcwd()

CLIENT = docker.from_env()

class Builder:
    def __init__(self):
        msg("Create container")

        width, height = get_terminal_size()

        self.container = CLIENT.containers.create(
            "archlinux:latest",
            environment = {
                "TERM": "xterm-256color",
                "COLUMNS": width,
                "LINES": height
            },
            mounts = [Mount("/home/kp3/build", ROOT, type="bind")],
            tty = True
        )

        self.api = self.container.client.api

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exit_type, *args):
        if not exit_type: self.close()

    def start(self):
        msg("Start kp3...")

        # Connect signal
        signal(SIGTERM, self.sig_kill)
        signal(SIGINT, self.sig_kill)

        # Start container
        self.container.start()

        # Setup mirror
        msg2("Setup mirror")
        self.run_quit(["bash", "-c",  "echo 'Server = http://mirrors.cat.net/archlinux/$repo/os/$arch' > /etc/pacman.d/mirrorlist"])

        # Install base-devel, git
        msg2("Install base-devel")
        self.run(["pacman", "-Syyu", "--noconfirm", "--needed", "base-devel", "git"])

        # Create user
        msg2("Create user")
        self.run_quit(["useradd", "-m", "-s", "/bin/bash", "kp3"])
        self.run_quit(["usermod", "-U", "-g", "kp3", "kp3"])
        self.run_quit(["groupadd", "sudo"])
        self.run_quit(["usermod", "-aG", "sudo", "kp3"])
        self.run_quit(["chmod", "700", "-R", "/home/kp3"])
        self.run_quit(["chown", "kp3:kp3", "-R", "/home/kp3"])
        self.run_quit(["bash", "-c",  "echo 'kp3 ALL=NOPASSWD: ALL' >> /etc/sudoers"])

    def close(self):
        msg("Close kp3...")
        self.container.remove(force=True)

    def build(self, aur_pkgs):
        if len(aur_pkgs) != 0:
            msg("Build AUR packages")

            for pkg in aur_pkgs:
                pkgname = pkg.replace("https://aur.archlinux.org/", "").replace(".git", "")

                self.run(
                    ["git", "clone", pkg],
                    user = "kp3",
                    workdir = "/home/kp3"
                )

                self.run(
                    ["makepkg", "--syncdeps", "--install", "--noconfirm"],
                    user = "kp3",
                    workdir = "/home/kp3/" + pkgname
                )

        msg("Start build...")
        self.run(
            ["makepkg", "--clean", "--cleanbuild", "--ignorearch", "--force", "--syncdeps", "--noconfirm"],
            user = "kp3",
            workdir = "/home/kp3/build"
        )

    def sig_kill(self, *args):
        error("\nKill kp3...")
        self.container.remove(force=True)
        sys.exit(1)

    def check(self, cmd, exit_code):
        if exit_code != 0:
            error("Command Failed")
            msg2(f"Command: {join(cmd)}")
            msg2(f"Return Code: {exit_code}")
            self.container.remove(force=True)
            sys.exit(1)

    def run(self, cmd, **kwargs):
        response = self.api.exec_create(
            self.container.id,
            cmd,
            tty = True,
            **kwargs
        )

        output = self.api.exec_start(
            response ['Id'],
            tty=True,
            stream=True
        )

        for line in output: print(line.decode(), end="")

        self.check(
            cmd,
            self.api.exec_inspect(response["Id"])["ExitCode"]
        )

    def run_quit(self, cmd):
        exit_code, _= self.container.exec_run(cmd)
        self.check(cmd, exit_code)
