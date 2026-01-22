import sys, os
from pathlib import Path
from easybuild.framework.easyconfig.easyconfig import process_easyconfig
from easybuild.tools.options import set_up_configuration

if __name__ == "__main__":
    os.environ["EASYBUILD_LOGTOSTDOUT"] = "1"
    os.environ["EASYBUILD_CONFIGFILES"] = os.environ["LOCAL_EASYBUILD_CONFIGFILES"]
    os.environ["EASYBUILD_ROBOT_PATHS"] = os.pathsep.join((os.environ["EASYBUILD_ROBOT_PATHS"],
                                                           str(Path(os.environ["EBROOTGENTOO"]) /
                                                               "easybuild" / "easyconfigs")))

    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")

    set_up_configuration(args="")
    parsed_ec = process_easyconfig(sys.argv[1])

    sys.stdout.close()
    full_mod_name = parsed_ec[0]['full_mod_name']
    prefix = Path(os.environ.get("EASYBUILD_PREFIX", "/cvmfs/soft.computecanada.ca/easybuild"))
    eis = Path(os.environ.get("EASYBUILD_INSTALLPATH_SOFTWARE", prefix / os.environ["EASYBUILD_SUBDIR_SOFTWARE"]))
    eim = prefix / os.environ["EASYBUILD_SUBDIR_MODULES"]
    spath = eis / full_mod_name
    mpath = eim / full_mod_name
    for i, p in enumerate(spath.parents):
        if p.exists():
            spath = p
            mpath = mpath.parents[i]
            break

    bwrapdir = Path(sys.argv[2])
    (bwrapdir / spath.relative_to('/')).mkdir(parents=True, exist_ok=True)
    (bwrapdir / mpath.relative_to('/')).mkdir(parents=True, exist_ok=True)
    bwrap_cmd = f"bwrap --dev-bind / / --bind {bwrapdir}{spath} {spath} --bind {bwrapdir}{mpath} {mpath}"
    old_stdout.write(f"{bwrap_cmd}\n")
