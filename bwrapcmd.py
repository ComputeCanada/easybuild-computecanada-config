import sys, os
from easybuild.framework.easyconfig.easyconfig import process_easyconfig
from easybuild.tools.options import set_up_configuration

if __name__ == "__main__":
    os.environ["EASYBUILD_LOGTOSTDOUT"] = "1"
    os.environ["EASYBUILD_CONFIGFILES"] = os.environ["LOCAL_EASYBUILD_CONFIGFILES"]
    os.environ["EASYBUILD_ROBOT_PATHS"] = os.pathsep.join((os.environ["EASYBUILD_ROBOT_PATHS"],
                                                           os.path.join(os.environ["EBROOTGENTOO"],
                                                                        "easybuild", "easyconfigs")))

    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")

    set_up_configuration(args="")
    parsed_ec = process_easyconfig(sys.argv[1])

    sys.stdout.close()
    full_mod_name = parsed_ec[0]['full_mod_name']
    prefix = os.environ.get("EASYBUILD_PREFIX", "/cvmfs/soft.computecanada.ca/easybuild")
    eis = os.environ.get("EASYBUILD_INSTALLPATH_SOFTWARE", os.path.join(prefix, os.environ["EASYBUILD_SUBDIR_SOFTWARE"]))
    eim = os.path.join(prefix, os.environ["EASYBUILD_SUBDIR_MODULES"])
    spath = os.path.dirname(os.path.join(eis, full_mod_name))
    mpath = os.path.dirname(os.path.join(eim, full_mod_name))
    while not os.path.exists(spath):
        spath = os.path.dirname(spath)
        mpath = os.path.dirname(mpath)

    bwrapdir = sys.argv[2]
    os.makedirs(os.path.join(bwrapdir, spath), exist_ok=True)
    os.makedirs(os.path.join(bwrapdir, mpath), exist_ok=True)
    bwrap_cmd = f"bwrap --dev-bind / / --bind {bwrapdir}{spath} {spath} --bind {bwrapdir}{mpath} {mpath}"
    old_stdout.write(f"{bwrap_cmd}\n")
