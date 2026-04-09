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
    bwrap_modules = [p['full_mod_name'] for p in parsed_ec]

    bwrap_installpath = sys.argv[2]
    tar_cmd = ['tar', 'cvf']

    mod = bwrap_modules[0].split('/')
    mod = mod[-2:] + mod[1:-2] + mod[:1]
    tarball = os.path.join('/shared_tmp', f"{'_'.join(mod)}_{os.environ['YEAR']}_{os.environ['USER']}.tar")
    tar_cmd.extend([tarball] + [os.path.join(bwrap_installpath, d) for d in ['modules', 'software']])

    sys.stdout.close()
    old_stdout.write(f'{" ".join(tar_cmd)}\n')
