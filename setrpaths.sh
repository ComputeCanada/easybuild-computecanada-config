#!/usr/bin/env python

import getopt
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from elftools.common.exceptions import ELFError
from elftools.elf.dynamic import DynamicSection
from elftools.elf.elffile import ELFFile

REX_OS_INTERPRETER = "/lib64/ld-linux-x86-64.so.2.*"
REX_LINUX_INTERPRETER = ".*ld-linux-x86-64.so.2"
REX_LSB_INTERPRETER = ".*ld-lsb-x86-64.so.3"

def print_usage():
    print("Usage: $0 --path <path to search> [--add_origin] [--add_path=<path>] [--any_interpreter]")

def patch_rpath(filename, arg_add_origin, arg_any_interpreter, arg_add_path,
                interpreter, force_rpath):

    set_interp = False
    has_needed = False
    interp_name = ""
    with open(filename, "rb") as f:
        try:
            elf = ELFFile(f)
            if elf.header['e_type'] not in {'ET_DYN', 'ET_EXEC'}:
                return
            for seg in elf.iter_segments('PT_INTERP'):
                interp_name = seg.get_interp_name()
            # check if shared libraries have NEEDED entries, if not
            # we whould not manipulate RPATH
            if not interp_name and (arg_add_origin or arg_add_path):
                for section in elf.iter_sections():
                    if isinstance(section, DynamicSection):
                        for tag in section.iter_tags():
                            if tag.entry.d_tag == 'DT_NEEDED':
                                has_needed = True
                                break
        except ELFError:
            return

    if interp_name:
        if (re.match(REX_OS_INTERPRETER, interp_name) or
            (arg_any_interpreter and (re.match(REX_LINUX_INTERPRETER, interp_name) or
                                      re.match(REX_LSB_INTERPRETER, interp_name)))):
            subprocess.run(["patchelf", "--set-interpreter", interpreter, filename])
            set_interp = True

    if (arg_add_origin or arg_add_path) and (set_interp or has_needed):
        rpath = subprocess.check_output(["patchelf", "--print-rpath", filename])
        rpath_old = rpath

        if arg_add_origin and not rpath.startswith(b"$ORIGIN"):
            if rpath.strip():
                rpath = b'$ORIGIN:' + rpath
            else:
                rpath = b'$ORIGIN'

        if arg_add_path:
            if rpath:
                rpath = arg_add_path + b":" + rpath
            else:
                rpath = arg_add_path

        if rpath != rpath_old:
            if force_rpath:
                subprocess.run(["patchelf", "--force-rpath", "--set-rpath", rpath, filename])
            else:
                subprocess.run(["patchelf", "--set-rpath", rpath, filename])


def patch_zip(filename, arg_add_origin, arg_any_interpreter, arg_add_path,
              interpreter, force_rpath):
    fullname = os.path.realpath(filename)
    oldcwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)

        # Extract all and patch every binary file, and update the archive
        subprocess.run(["unzip", "-q", fullname])    
        for root, dirs, files in os.walk(os.getcwd()):
            root = Path(root)
            for name in files:
                fname = root / name
                oldperm = os.stat(fname).st_mode
                os.chmod(fname, oldperm | stat.S_IWUSR)
                patch_rpath(fname, arg_add_origin, arg_any_interpreter, arg_add_path,
                            interpreter, force_rpath)
                os.chmod(fname, oldperm)

        subprocess.run(["zip", "-rq", fullname, "."])
        os.chdir(oldcwd)
        print(oldcwd)


def main():
    optlist, _ = getopt.gnu_getopt(sys.argv, 'p:', ["path=", "add_origin" , "add_path=",
                                                    "any_interpreter"])
    arg_add_origin = False
    arg_add_path = ""
    arg_any_interpreter = False
    arg_path = ""

    for opt, value in optlist:
        if opt in ('-p', '--path'):
            arg_path = value
        elif opt == '--add_origin':
            arg_add_origin = True
        elif opt == '--any_interpreter':
            arg_any_interpreter = True
        elif opt == '--add_path':
            arg_add_path = value
        else:
            print(f"Unknown parameter {opt}")
            print_usage()
            return 1

    if not arg_path:
        print_usage()
        return 1

    # Avoid failing to set rpaths when a symlink is provided
    if stat.S_ISLNK(os.stat(arg_path).st_mode):
        print(f"error: {arg_path} is a symlink. Please provide a path not a symlink.")
        return 1

    if "NIXUSER_PROFILE" in os.environ:
        prefix = Path(os.environ["NIXUSER_PROFILE"])
        interpreter = prefix / "lib" / "ld-linux-x86-64.so.2"
        force_rpath = False
    elif "EPREFIX" in os.environ:
        prefix = Path(os.environ["EPREFIX"])
        year = int(os.environ["EBVERSIONGENTOO"])
        if year >= 2023:
            interpreter = prefix / "lib64" / "ld-linux-x86-64.so.2"
        else:
            interpreter = prefix / "lib" / "ld-linux-x86-64.so.2"
        force_rpath = True
    else:
        print("Neither nixpkgs nor gentoo modules are loaded. Aborting")
        sys.exit(1)

    for root, dirs, files in os.walk(arg_path):
        root = Path(root)
        for name in files:
            f = root / name
            if name[-4:] in {".whl", ".jar"}:
                patch_zip(f, arg_add_origin, arg_any_interpreter, arg_add_path,
                          interpreter, force_rpath)
            else:
                patch_rpath(f, arg_add_origin, arg_any_interpreter, arg_add_path,
                            interpreter, force_rpath)
    return 0

if __name__ == "__main__":
    sys.exit(main())
