#!/cvmfs/soft.computecanada.ca/easybuild/software/2020/avx2/Core/python/3.8.10/bin/python
import os
import site
import sys
import shutil
import uuid
import argparse

AVAILABLE_ARCHITECTURES = ["avx2", "avx512", "avx", "sse3"]
AVAILABLE_CPU_VENDORS = ["intel", "amd"]
DEFAULT_INDEX_DIR = "/cvmfs/soft.computecanada.ca/custom/mii/data"

def generate_mii_index(arch="avx2", cpu_vendor="amd", index_dir=DEFAULT_INDEX_DIR):
    modulepath = '/cvmfs/soft.computecanada.ca/custom/modules'
    mii = "/cvmfs/soft.computecanada.ca/easybuild/software/2020/Core/mii/1.1.1/bin/mii"
    prefix = arch + "_" + cpu_vendor
    final_index_file = os.path.join(index_dir, prefix)
    exclude_modnames = ",".join(("gentoo","nixpkgs"))

    os.environ["RSNT_ARCH"] = arch
    os.environ["RSNT_CPU_VENDOR_ID"] = cpu_vendor

    unique_filename = prefix + "_" + str(uuid.uuid4())
    index_file = os.path.join(index_dir,unique_filename)
    cmd = "MII_INDEX_FILE=%s %s build -m %s -n %s" % (index_file, mii, modulepath, exclude_modnames)
    print("Generating the Mii index with cmd:%s" % cmd )
    os.system(cmd)
#    (out, _) = run_cmd(cmd, log_all=True, simple=False, log_output=True)

    # create a new symlink
    new_symlink_path = os.path.join(index_dir, prefix + "_" +  str(uuid.uuid4()))
    os.symlink(index_file, new_symlink_path)

    # if the path exists and is a link, remove the target of the link
    current_target = None
    if os.path.islink(final_index_file):
        # get the path of the current index
        current_target = os.readlink(final_index_file)

    # rename the new symlink, overwriting the old symlink or file
    shutil.move(new_symlink_path, final_index_file)

    if current_target and os.path.isfile(current_target):
        # remove the old target
        os.remove(current_target)

def create_argparser():
    """
    Returns an arguments parser for `generate_mii_index.py` command.
    Note : sys.argv is not parsed yet, must call `.parse_args()`.
    """

    class HelpFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
        """ Dummy class for RawDescription and ArgumentDefault formatter """

    description = "Generate Mii indexes for different combinations of architectures and CPU vendor"

    epilog = "Examples:\n"
    epilog += "    generate_mii_index.py --arch avx2,avx512 --cpu_vendor amd"

    parser = argparse.ArgumentParser(prog="generate_mii_index.py",
                                     formatter_class=HelpFormatter,
                                     description=description,
                                     epilog=epilog)

    cpu_vendor_group = parser.add_argument_group('cpu_vendor')
    parser.add_mutually_exclusive_group()._group_actions.extend([
        cpu_vendor_group.add_argument("--cpu_vendor", choices=AVAILABLE_CPU_VENDORS, nargs='+', default=AVAILABLE_CPU_VENDORS, help="Specify the which cpu vendor to build the inex for."),
        cpu_vendor_group.add_argument("--all_cpu_vendors", action='store_true', help="Build for all CPU vendors"),
        cpu_vendor_group.add_argument("--all-cpu-vendors", action='store_true', dest="all_cpu_vendors"),
    ])

    arch_group = parser.add_argument_group('architecture')
    parser.add_mutually_exclusive_group()._group_actions.extend([
        arch_group.add_argument("-a", "--arch", choices=AVAILABLE_ARCHITECTURES, nargs='+', default=AVAILABLE_ARCHITECTURES, help=f"Specify which CPU architecture to build the index for"),
        arch_group.add_argument("--all_archs", action='store_true', help=f"Build for all CPU architectures"),
        arch_group.add_argument("--all-archs", action='store_true', dest="all_archs")
    ])

    parser.add_argument("--index_dir", default=DEFAULT_INDEX_DIR, help="Specify the directory in which to write indexes.")


    return parser


def main():
    args = create_argparser().parse_args()
    for arch in args.arch:
        for cpu_vendor in args.cpu_vendor:
            generate_mii_index(arch, cpu_vendor, args.index_dir)

if __name__ == "__main__":
    main()
