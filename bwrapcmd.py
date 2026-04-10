import sys, os
from easybuild.framework.easyconfig.easyconfig import process_easyconfig
from easybuild.tools.options import set_up_configuration
from easybuild.tools.filetools import mkdir

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
    bwrap_modules = [p['full_mod_name'] for p in parsed_ec]

    prefix = os.environ.get("EASYBUILD_PREFIX", "/cvmfs/soft.computecanada.ca/easybuild")
    installpath_software = os.environ.get("EASYBUILD_INSTALLPATH_SOFTWARE",
                                          os.path.join(prefix, os.environ["EASYBUILD_SUBDIR_SOFTWARE"]))
    bwrap_installpath = sys.argv[2]
    bwrap_cmd = ['bwrap', '--dev-bind', '/', '/']

    for mod in bwrap_modules:
        spath = os.path.join(os.path.realpath(installpath_software), mod)
        bwrap_spath = os.path.join(bwrap_installpath, os.environ["EASYBUILD_SUBDIR_SOFTWARE"], mod)
        if os.path.exists(spath):
            bwrap_cmd.extend(['--bind', bwrap_spath, spath])
        else:
            bwrap_workdir = os.path.join(bwrap_installpath, 'workdir', mod)
            while not os.path.exists(spath):
                spath = os.path.dirname(spath)
                bwrap_spath = os.path.dirname(bwrap_spath)
                bwrap_workdir = os.path.dirname(bwrap_workdir)
            mkdir(bwrap_workdir, parents=True)
            bwrap_cmd.extend(['--overlay-src', spath, '--overlay', bwrap_spath, bwrap_workdir, spath])
        mkdir(bwrap_spath, parents=True)

    sys.stdout.close()
    old_stdout.write(f'{" ".join(bwrap_cmd)}\n')
