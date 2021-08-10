from easybuild.framework.easyconfig.easyconfig import get_easyblock_class
from easybuild.easyblocks.generic.cmakemake import CMakeMake
from easybuild.framework.easyconfig.constants import EASYCONFIG_CONSTANTS
from distutils.version import LooseVersion
from cc_hooks_common import modify_all_opts, update_opts, PREPEND, APPEND, REPLACE, APPEND_LIST

import os

new_version_mapping = {
        'ALL': {
            'pkg_mapping': {
                ('Perl', '5.22.2'): ('5.22.4',None),
                'JasPer': '1.900.1',
                'QScintilla':'2.10.7',
                'QJson':'0.9.0',
                ('Python','2.7.13','ANY'): ('2.7.14',None),
                ('Python','3.5.2','ANY'): ('3.5.4',None),
                ('SciPy-Stack','ANY'): ('2019a',None),
                ('Java', ('1.7.0_80','1.8.0_121','1.8.0_192')): ('1.8',None),
            },
            'tc_mapping': {
                'ALL':('dummy','dummy'),
            }
        },
        (('gmkl','2018.3'),('iimkl','2018.3'),
         ('gomkl','2018.3.312'),('iomkl','2018.3.312'),
         ('gomklc','2018.3.312.100'),('iomklc','2018.3.312.100')): {
            'pkg_mapping': {
                'arpack-ng': '3.5.0',
                ('AUGUSTUS','3.2.3'):'3.3',
                'CheMPS2': '1.8.9',
                'R':('3.5.2',None),
            },
            'tc_mapping': {
                (('gmkl','2018.3'),('gomkl','2018.3.312'),('gomklc','2018.3.312.100')):('gmkl','2018.3'),
                (('iimkl','2018.3'),('iomkl','2018.3.312'),('iomklc','2018.3.312.100')):('iimkl','2018.3'),
            }
        },
        (('iccifort','2018.3'),('GCC','7.3.0'),
         ('gmkl','2018.3'),('iimkl','2018.3'),
         ('gompi','2018.3.312'),('iompi','2018.3.312'),
         ('gomkl','2018.3.312'),('iomkl','2018.3.312'),
         ('gcccuda','2018.3.100'),('iccifortcuda','2018.3.100'),
         ('gmklc','2018.3.100'),('iimklc','2018.3.100'),
         ('gomklc','2018.3.312.100'),('iomklc','2018.3.312.100'),
         ('gompic','2018.3.312.100'),('iompic','2018.3.312.100')): {
            'pkg_mapping': {
                'BLAST+': '2.7.1',
                ('Boost',('1.54.0','1.60.0','1.65.1','1.66.0'),None): '1.68.0',
                'Bowtie2': '2.3.4.3',
                'CLHEP': '2.4.1.0',
                ('FFTW','ANY',None): '3.3.8',
                'GDAL': ('2.1.3',None),
                ('GEOS',('3.4.3','3.6.1'),None): ('3.6.1',None),
                ('GSL',('2.2.1', '2.3', '2.4')) : '2.5' ,
                ('HDF5',('1.8.18','1.10.1'),None): '1.10.3',
                'HTSlib': '1.9',
                'ITK': '4.13.1',
                ('libxc','3.0.0'): '3.0.0',
                ('libxc','4.2.1'): '4.2.3',
                'MAFFT': '7.397',
                'Mono': '5.16.0.179',
                'muParser': '2.2.6',
                ('netCDF','ANY',None): '4.6.1',
                'NLopt': '2.4.2',
                ('OpenImageIO','1.8.7'): '1.8.15',
                'OSL': '1.9.12',
                'PRANK': '170427',
                ('SAMtools',('1.3.1','1.5','1.8','1.9')): '1.9',
                ('SAMtools',('0.1.17','0.1.20')): '0.1.20',
                ('Trinity','2.4.0'):'2.8.4',
                'UDUNITS': '2.2.26',
            },
            'tc_mapping': {
                (('iccifort','2018.3'),('iimkl','2018.3'),('iompi','2018.3.312'),('iomkl','2018.3.312'),
                ('iccifortcuda','2018.3.100'),('iimklc','2018.3.100'),('iompic','2018.3.312.100'),('iomklc','2018.3.312.100')):('iccifort','2018.3'),
                (('GCC','7.3.0'),('gmkl','2018.3'),('gompi','2018.3.312'),('gomkl','2018.3.312'),
                ('gcccuda','2018.3.100'),('gmklc','2018.3.100'),('gompic','2018.3.312.100'),('gomklc','2018.3.312.100')):('GCC','7.3.0'),
            }
        },
        (('iccifort','2019.3'),('GCC','8.3.0'),
         ('gmkl','2019.3'),('iimkl','2019.3'),
         ('gompi','2019.3.401'),('iompi','2019.3.401'),
         ('gomkl','2019.3.401'),('iomkl','2019.3.401')): {
            'pkg_mapping': {
                ('HDF5','ANY',None): '1.10.5',
                ('netCDF','ANY',None): '4.7.0',
            },
            'tc_mapping': {
                (('iccifort','2019.3'),('iimkl','2019.3'),('iompi','2019.3.401'),('iomkl','2019.3.401')
                ):('iccifort','2019.3'),
                (('GCC','8.3.0'),('gmkl','2019.3'),('gompi','2019.3.401'),('gomkl','2019.3.401')
                ):('GCC','8.3.0'),
            }
        },
        (('gompi','2018.3.312'),('iompi','2018.3.312'),
         ('gomkl','2018.3.312'),('iomkl','2018.3.312'),
         ('gompic','2018.3.312.100'),('iompic','2018.3.312.100'),
         ('gomklc','2018.3.312.100'),('iomklc','2018.3.312.100')): {
            'pkg_mapping': {
                ('Boost','ANY','-mpi'): '1.68.0',
                ('FFTW','ANY','-mpi'): '3.3.8',
                ('HDF5','1.8.18','-mpi'): '1.10.3',
                ('netCDF','ANY','-mpi'): '4.6.1',
                'SCOTCH':'6.0.6',
            },
            'tc_mapping': {
                (('gompi','2018.3.312'),('gomkl','2018.3.312'),('gompic','2018.3.312.100'),('gomklc','2018.3.312.100')):('gompi','2018.3.312'),
                (('iompi','2018.3.312'),('iomkl','2018.3.312'),('iompic','2018.3.312.100'),('iomklc','2018.3.312.100')):('iompi','2018.3.312'),
            }
        },
        (('gomkl','2018.3.312'),('iomkl','2018.3.312'),
         ('gomklc','2018.3.312.100'),('iomklc','2018.3.312.100')): {
            'pkg_mapping': {
                ('ESMF','7.0.1'):'7.1.0r',
                ('Hypre','ANY'):'2.15.1',
                ('PLUMED','2.3.0'):'2.3.7',
                ('PLUMED','2.4.2'):'2.4.3',
                ('PETSc','ANY','ANY'): '3.10.2',
                ('Trilinos','12.10.1','ANY'): ('12.10.1',None),
            },
            'tc_mapping': {
                (('gomkl','2018.3.312'),('gomklc','2018.3.312.100')):('gomkl','2018.3.312'),
                (('iomkl','2018.3.312'),('iomklc','2018.3.312.100')):('iomkl','2018.3.312'),
            }
        },
        (('iomkl','2018.3.312'),('iomklc','2018.3.312.100')): {
            'pkg_mapping': {
                ('PETSc','ANY','ANY'): '3.10.5',
            },
            'tc_mapping': {
                (('iomkl','2018.3.312'),('iomklc','2018.3.312.100')):('iomkl','2018.3.312'),
            }
        },
}
new_version_mapping_app_specific = {
        ('BLASR','blasr-libcpp'):{
            (('iccifort','2018.3'),('GCC','7.3.0')): {
                'pkg_mapping': {
                    'HDF5' : '1.8.20'
                },
                'tc_mapping': {
                    (('iccifort','2018.3')):('iccifort','2018.3'),
                    (('GCC','7.3.0')):('GCC','7.3.0'),
                }
            },
        },
}

opts_changes = {
    'Java': {
        'modluafooter': ('setenv("JAVA_TOOL_OPTIONS", "-Xmx2g")', REPLACE),
    },
    'Nextflow': {
        'postinstallcmds': (['sed -i -e "s/cli=(\$(/cli=(\$(export NFX_OPTS=\$JAVA_TOOL_OPTIONS; unset JAVA_TOOL_OPTIONS; /g" %(installdir)s/bin/nextflow'], APPEND_LIST),
    },
    'OpenBLAS': {
        'buildopts': ({'sse3': 'DYNAMIC_ARCH=1',
                       'avx': 'TARGET=SANDYBRIDGE',
                       'avx2': 'DYNAMIC_ARCH=1 DYNAMIC_LIST="HASWELL ZEN SKYLAKEX"',
                       'avx512': 'TARGET=SKYLAKEX'}[os.getenv('RSNT_ARCH')] + ' NUM_THREADS=64',
                       PREPEND),
        'installopts': ({'sse3': 'DYNAMIC_ARCH=1',
                       'avx': 'TARGET=SANDYBRIDGE',
                       'avx2': 'DYNAMIC_ARCH=1 DYNAMIC_LIST="HASWELL ZEN SKYLAKEX"',
                       'avx512': 'TARGET=SKYLAKEX'}[os.getenv('RSNT_ARCH')] + ' NUM_THREADS=64',
                       PREPEND),
        'testopts': ({'sse3': 'DYNAMIC_ARCH=1',
                       'avx': 'TARGET=SANDYBRIDGE',
                       'avx2': 'DYNAMIC_ARCH=1 DYNAMIC_LIST="HASWELL ZEN SKYLAKEX"',
                       'avx512': 'TARGET=SKYLAKEX'}[os.getenv('RSNT_ARCH')] + ' NUM_THREADS=64',
                       PREPEND),
    },
    'ROOT': {
        # Cling needs to know about different sysroot
        'configopts': ("-DDEFAULT_SYSROOT=/cvmfs/soft.computecanada.ca/nix/var/nix/profiles/glibc-2.24", PREPEND),
    },
}

def map_dependency_version(dep, new_dep, tc_mapping, mytc):
    if isinstance(dep,tuple): dep = list(dep)
    # ensure that it has a length of 4
    for _ in range(len(dep),4):
        dep.append(None)

    # figure out what is the right toolchain to put there
    new_tc = None
    if 'ALL' in tc_mapping: new_tc = tc_mapping['ALL']
    for tcs in tc_mapping.keys():
        if not isinstance(tcs,tuple): continue
        if mytc == tcs or mytc in tcs:
            new_tc = tc_mapping[tcs]

    if isinstance(new_dep, str): dep[1] = new_dep
    if isinstance(new_dep, tuple):
        dep[1] = new_dep[0]
        dep[2] = new_dep[1]
        if len(new_dep) == 3:
            new_tc = new_dep[2]

    dep[3] = new_tc
    return dep

def package_match(ref, test):
    #print("Testing %s against %s" % (str(test),str(ref)))
    if isinstance(ref,str): ref = (ref, "ANY", "ANY")
    if isinstance(test,list) and isinstance(test[0],tuple): return False  # does not change anything for multi_deps
    ref_name = ref[0]
    ref_version = ref[1]
    ref_version_suffix = "ANY"
    if len(ref) >= 3:
        ref_version_suffix = ref[2]

    test_name = test[0]
    test_version = test[1]
    test_version_suffix = None
    if len(test) >= 3:
        test_version_suffix = test[2]

    # test name
    if ref_name != test_name: return False
    #print("Name matches")

    # test version
    if ref_version != "ANY":
        if isinstance(ref_version, str) and test_version != ref_version:
            return False
        if isinstance(ref_version, tuple) and not test_version in ref_version:
            return False
    #print("Version matches")

    # if we get to this point, the versions match, test version_suffixes
    if ref_version_suffix != "ANY":
        # undefined version_suffix required and version_suffix provided
        if not ref_version_suffix and test_version_suffix:
            return False
        if isinstance(ref_version_suffix, str) and test_version_suffix != ref_version_suffix:
            return False
        if isinstance(ref_version_suffix, tuple) and not test_version_suffix in ref_version_suffix:
            return False
    #print("Version suffix matches")

    return True


def replace_dependencies(ec, tc, param, deps_mapping):
    mytc = (ec.toolchain.name, ec.toolchain.version)
    #print("mytc: %s, tc: %s" % (str(mytc), str(tc)))
    if tc == 'ALL' or mytc == tc or mytc in tc:
        #print("toolchain match")
        for n, dep in enumerate(ec[param]):
            dep = list(dep)
            if dep[0] == ec.name:
                print("Dependency has the same name as the easyconfig, not replacing.")
                continue
            for new_dep in deps_mapping['pkg_mapping']:
                new_dep_version = deps_mapping['pkg_mapping'][new_dep]
                if package_match(new_dep, dep):
                    print("Dependency %s matches %s" % (str(dep),(new_dep)))
                    dep = map_dependency_version(dep,new_dep_version,deps_mapping['tc_mapping'],mytc)
                    print("New dependency: %s" % str(dep))
                    dep = tuple(dep)
                    ec[param][n] = dep


def modify_dependencies(ec,param, new_version_mapping, new_version_mapping_app_specific):
    for tc in new_version_mapping:
        deps_mapping = new_version_mapping[tc]
        if tc == 'ALL':
            replace_dependencies(ec,'ALL',param,deps_mapping)
        else:
            replace_dependencies(ec,tc,param,deps_mapping)

    for names in new_version_mapping_app_specific:
        mapping = new_version_mapping_app_specific[names]
        if ec['name'] in names:
            print("Specific dependency mappings exist for %s, applying them" % ec['name'])
            for tc in mapping:
                deps_mapping = mapping[tc]
                replace_dependencies(ec,tc,param,deps_mapping)


def parse_hook(ec, *args, **kwargs):
    """Example parse hook to inject a patch file for a fictive software package named 'Example'."""
    modify_dependencies(ec,'dependencies', new_version_mapping, new_version_mapping_app_specific)
    modify_dependencies(ec,'builddependencies', new_version_mapping, new_version_mapping_app_specific)

    modify_all_opts(ec, opts_changes, opts_to_skip=[], opts_to_change=['modluafooter', 'postinstallcmds'])

    # always disable multi_deps_load_default when multi_deps is used
    if ec.get('multi_deps', None): 
        ec['multi_deps_load_default'] = False


def pre_configure_hook(self, *args, **kwargs):
    "Modify configopts (here is more efficient than parse_hook since only called once)"
    orig_enable_templating = self.cfg.enable_templating
    self.cfg.enable_templating = False

    modify_all_opts(self.cfg, opts_changes)
    ec = self.cfg
    # additional changes for CMakeMake EasyBlocks
    CMakeMake_configopts_changes = (' -DZLIB_ROOT=$NIXUSER_PROFILE ' + 
        ' -DOPENGL_INCLUDE_DIR=$NIXUSER_PROFILE/include -DOPENGL_gl_LIBRARY=$NIXUSER_PROFILE/lib/libGL.so ' +
        ' -DOPENGL_glu_LIBRARY=$NIXUSER_PROFILE/lib/libGLU.so ' +
        ' -DJPEG_INCLUDE_DIR=$NIXUSER_PROFILE/include -DJPEG_LIBRARY=$NIXUSER_PROFILE/lib/libjpeg.so ' +
        ' -DPNG_PNG_INCLUDE_DIR=$NIXUSER_PROFILE/include -DPNG_LIBRARY=$NIXUSER_PROFILE/lib/libpng.so ' +
        ' -DPYTHON_EXECUTABLE=$EBROOTPYTHON/bin/python ' +
        ' -DCURL_LIBRARY=$NIXUSER_PROFILE/lib/libcurl.so -DCURL_INCLUDE_DIR=$NIXUSER_PROFILE/include ' +
        ' -DCMAKE_SYSTEM_PREFIX_PATH=$NIXUSER_PROFILE ' +
        ' -DCMAKE_SKIP_INSTALL_RPATH=ON ')

    if ec.easyblock is None or isinstance(ec.easyblock, str):
        c = get_easyblock_class(ec.easyblock, name=ec.name)
    elif isinstance(ec.easyblock, type):
        c = ec.easyblock
    if c == CMakeMake or issubclass(c,CMakeMake):
        # skip for those
        if (ec['name'],ec['version']) in [('ROOT','5.34.36'), ('mariadb', '10.4.11')]:
            pass
        else:
            update_opts(ec, CMakeMake_configopts_changes, 'configopts', PREPEND)

    self.cfg.enable_templating = orig_enable_templating

