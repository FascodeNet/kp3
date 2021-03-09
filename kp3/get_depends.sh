#!/usr/bin/bash
source PKGBUILD
echo "${makedepends[@]} ${depends[@]}" | sed "s@ @\n@g" | grep -v "^$"
