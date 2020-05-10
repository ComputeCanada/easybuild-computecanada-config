from easybuild.framework.easyconfig.easyconfig import get_easyblock_class
from easybuild.easyblocks.generic.cmakemake import CMakeMake
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
        'ALL_GENTOO': {
            'pkg_mapping': {
                'JasPer': '2.0.16',
                ('Python','2.7.14','ANY'): ('2.7.17',None),
                ('Python','3.5.4','ANY'): ('3.7.5',None),
                ('Python','3.7.0','ANY'): ('3.7.5',None),
                ('Python','3.7.4','ANY'): ('3.7.5',None),
                ('Eigen','ANY'): ('3.3.7',None),
                ('CMake','3.15.3'): ('3.12.2',None), # to be ignored by filter-deps
            },
            'tc_mapping': {
                'ALL':('system','system'),
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
        (('iccifort','2020.0.166'),('GCC','9.2.0'),
         ('gmkl','2020.0'),('iimkl','2020.0'),
         ('gompi','2020.0.403'),('iompi','2020.0.403'),
         ('gomkl','2020.0.403'),('iomkl','2020.0.403')): {
            'pkg_mapping': {
                'BLAST+': '2.10.0',
                ('Boost',('1.54.0','1.60.0','1.65.1','1.66.0','1.68.0'),None): '1.72.0',
                'Bowtie2': '2.3.5.1',
                'BUFRLIB': '11.3.0',
                ('CGAL','4.9'): '4.14.2',
                'CLHEP': '2.4.1.3',
                'ecCodes': '2.16.0',
                ('FFTW','ANY',None): '3.3.8',
                'GDAL': ('3.0.4',None),
                ('GEOS',('3.4.3','3.6.1'),None): ('3.8.0',None),
                ('GSL',('2.2.1', '2.3', '2.4', '2.5')) : '2.6' ,
                ('HDF5','ANY',None): '1.10.6',
                'HTSlib': '1.10.2',
                'ITK': '5.0.1',
                ('libxc','3.0.0'): '3.0.0',
                ('libxc',('4.2.1', '4.2.3')): '4.3.4',
                'MAFFT': '7.450',
                'Mono': '6.8.0.105',
                'muParser': '2.2.6',
                ('netCDF','ANY',None): '4.7.3',
                ('netCDF-C++4','ANY',None):'4.3.1',
                ('netCDF-Fortran','ANY',None):'4.5.2',
                'NLopt': '2.6.1',
                ('OpenImageIO',('1.8.7','1.8.15')): '2.1.10',
                'OSL': '1.10.9',
                'PRANK': '170427',
                ('SAMtools',('1.3.1','1.5','1.8','1.9','1.10')): '1.10',
                ('SAMtools',('0.1.17','0.1.20')): '0.1.20',
                ('Trinity','2.4.0','2.8.4'):'2.9.1',
                'UDUNITS': '2.2.26',
            },
            'tc_mapping': {
                (('iccifort','2020.0.166'),('iimkl','2020.0'),('iompi','2020.0.312'),('iomkl','2020.0.312')): ('iccifort','2020.0.166'),
                (('GCC','9.2.0'),('gmkl','2020.0'),('gompi','2020.0.312'),('gomkl','2020.0.312')): ('GCC', '9.2.0')
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
        (('gompi','2020.0.403'),('iompi','2020.0.403'),
         ('gomkl','2020.0.403'),('iomkl','2020.0.403')): {
            'pkg_mapping': {
                ('Boost','ANY','-mpi'): '1.72.0',
                ('FFTW','ANY','-mpi'): '3.3.8',
                ('HDF5','1.8.18','-mpi'): '1.10.6',
                ('HDF5','1.10.3','-mpi'): '1.10.6',
                ('netCDF','ANY','-mpi'): '4.7.3',
                ('netCDF-C++4','ANY','-mpi'):'4.3.1',
                ('netCDF-Fortran','ANY','-mpi'):'4.5.2',
                'SCOTCH':'6.0.9',
            },
            'tc_mapping': {
                (('gompi','2020.0.403'),('gomkl','2020.0.403')):('gompi','2020.0.403'),
                (('iompi','2020.0.403'),('iomkl','2020.0.403')):('iompi','2020.0.403'),
            }
        },
        (('gomkl','2018.3.312'),('iomkl','2018.3.312'),
         ('gomklc','2018.3.312.100'),('iomklc','2018.3.312.100')): {
            'pkg_mapping': {
                ('ESMF','7.0.1'):'7.1.0r',
                ('Hypre','ANY'):'2.15.1',
                ('PLUMED','2.3.0'):'2.3.7',
                ('PLUMED','2.4.2'):'2.4.3',
                ('PETSc','ANY','ANY'): '3.10.5',
                ('Trilinos','12.10.1','ANY'): ('12.10.1',None),
            },
            'tc_mapping': {
                (('gomkl','2018.3.312'),('gomklc','2018.3.312.100')):('gomkl','2018.3.312'),
                (('iomkl','2018.3.312'),('iomklc','2018.3.312.100')):('iomkl','2018.3.312'),
            }
        },
        (('gomkl','2020.0.403'),('iomkl','2020.0.403')): {
            'pkg_mapping': {
                ('ESMF',('7.0.1','7.1.0r')):'8.0.0',
                ('Hypre','ANY'):'2.18.2',
                ('PLUMED',('2.3.0','2.3.7')):'2.3.8',
                ('PLUMED',('2.4.2','2.4.3')):'2.4.7',
                ('PETSc','ANY','ANY'): '3.12.4',
                ('Trilinos','12.10.1','ANY'): ('12.10.1',None),
            },
            'tc_mapping': {
                (('gomkl','2020.0.403')):('gomkl','2020.0.403'),
                (('iomkl','2020.0.403')):('iomkl','2020.0.403'),
            }
        }
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
        ('intel','gimkl','iomkl','gomkl'):{
            'ALL': {
                'pkg_mapping': {
                    ('imkl','2020.1.217'): '2020.1.217',
                },
                'tc_mapping': {
                    (('iimpi','2020a')):('system','system'),
                }
            },
        },
        ('foss'):{
            'ALL': {
                'pkg_mapping': {
                    ('FFTW','3.3.8'): '3.3.8',
                },
                'tc_mapping': {
                    (('system','system')):('GCC','9.3.0'),
                }
            },
        },
}
preconfigopts_changes = {
        # build EPREFIX-aware GCCcore
        'GCCcore': ("", "if [ -f ../gcc/gcc.c ]; then sed -i 's/--sysroot=%R//' ../gcc/gcc.c; " +
                   "for h in ../gcc/config/*/*linux*.h; do " +
                    r'sed -i -r "/_DYNAMIC_LINKER/s,([\":])(/lib),\1${EPREFIX}\2,g" $h; done; fi; ')
}

configopts_changes = {
        # build EPREFIX-aware GCCcore
        'GCCcore': ("", "--with-sysroot=$EPREFIX"),
        # local customizations for OpenMPI
        'OpenMPI': ("", '--enable-shared --with-verbs ' +
                    '--with-hwloc=external '  + # hwloc support
                    '--without-usnic ' + # No usnic-via-libfabric
                    # rpath is already done by ld wrapper
                    '--disable-wrapper-runpath --disable-wrapper-rpath ' +
                    '--with-munge ' + #enable Munge in PMIx
                    '--with-slurm --with-pmi=$EBROOTGENTOO ' +
                    '--enable-mpi-cxx ' +
                    '--with-hcoll ' +
                    '--disable-show-load-errors-by-default ' +
                    '--enable-mpi1-compatibility ' +
                    # enumerate all mca's that should be compiled as plugins
                    # (only those that link to system-specific
                    # libraries (lustre, fabric, and scheduler)
                    '--enable-mca-dso=common-ucx,common-verbs,event-external,' +
                    'atomic-ucx,btl-openib,btl-uct,' +
                    'coll-hcoll,ess-tm,fs-lustre,mtl-ofi,mtl-psm,mtl-psm2,osc-ucx,' +
                    'plm-tm,pmix-s1,pmix-s2,pml-ucx,pnet-opa,psec-munge,' +
                    'ras-tm,spml-ucx,sshmem-ucx,hwloc-external')
}

configopts_changes_based_on_easyblock_class_and_name = {
        'ANY': {
            CMakeMake: (' -DZLIB_ROOT=$NIXUSER_PROFILE ' +
                   ' -DOPENGL_INCLUDE_DIR=$NIXUSER_PROFILE/include -DOPENGL_gl_LIBRARY=$NIXUSER_PROFILE/lib/libGL.so ' +
                   ' -DOPENGL_glu_LIBRARY=$NIXUSER_PROFILE/lib/libGLU.so ' +
                   ' -DJPEG_INCLUDE_DIR=$NIXUSER_PROFILE/include -DJPEG_LIBRARY=$NIXUSER_PROFILE/lib/libjpeg.so ' +
                   ' -DPNG_PNG_INCLUDE_DIR=$NIXUSER_PROFILE/include -DPNG_LIBRARY=$NIXUSER_PROFILE/lib/libpng.so ' +
                   ' -DPYTHON_EXECUTABLE=$EBROOTPYTHON/bin/python ' +
                   ' -DCURL_LIBRARY=$NIXUSER_PROFILE/lib/libcurl.so -DCURL_INCLUDE_DIR=$NIXUSER_PROFILE/include ' +
                   ' -DCMAKE_SYSTEM_PREFIX_PATH=$NIXUSER_PROFILE ' +
                   ' -DCMAKE_SKIP_INSTALL_RPATH=ON ',
                   ' -DCMAKE_SKIP_INSTALL_RPATH=ON ')
        },
        # this version is a fake CMakeMake, it falls back to ./configure
        ('ROOT','5.34.36'): {},
        ('mariadb', '10.4.11'): {
            CMakeMake: ' '
        },

}
buildopts_changes = {
	'OpenBLAS': {'sse3': 'DYNAMIC_ARCH=1',
                    'avx': 'TARGET=SANDYBRIDGE',
                    'avx2': 'DYNAMIC_ARCH=1 DYNAMIC_LIST="HASWELL ZEN SKYLAKEX"',
                    'avx512': 'TARGET=SKYLAKEX'}[os.getenv('RSNT_ARCH')] + ' NUM_THREADS=64'
}

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

def modify_dependencies(ec,param):
    for tc in new_version_mapping:
        deps_mapping = new_version_mapping[tc]
        if tc == 'ALL' or tc == 'ALL_GENTOO':
            if ((tc == 'ALL_GENTOO' and "EBROOTGENTOO" in os.environ) or
                 tc == 'ALL' and "EBROOTGENTOO" not in os.environ):
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

def prepend_configopts(ec,changes,key="configopts"):
    print("Changing configopts from: %s" % ec[key])
    if isinstance(ec[key], str):
        configopts = [ec[key]]
    elif isinstance(ec[key], list):
        configopts = ec[key]
    else:
        return
    for i in range(len(configopts)):
        if not changes in configopts[i]:
            configopts[i] = changes + configopts[i]
        if 'NIXUSER_PROFILE' not in os.environ:
            optlist = [opt for opt in configopts[i].split() if '$NIXUSER_PROFILE' not in opt and
                       '$EBROOTNIXPKGS' not in opt and '$EBROOTPYTHON' not in opt]
            configopts[i] = ' '.join(optlist)
            print(configopts[i])

    if isinstance(ec[key], str):
        ec[key] = configopts[0]
    print("New configopts: %s" % ec[key])

def modify_configopts(ec):
    if ec['name'] in preconfigopts_changes.keys():
        print("Changing preconfigopts from: %s" % ec['preconfigopts'])
        prepend_configopts(ec,preconfigopts_changes[ec['name']]['EBROOTGENTOO' in os.environ],'preconfigopts')

    if ec['name'] in configopts_changes.keys():
        print("Changing configopts from: %s" % ec['configopts'])
        prepend_configopts(ec,configopts_changes[ec['name']]['EBROOTGENTOO' in os.environ])

    c = get_easyblock_class(ec.easyblock, name=ec.name)
    name_to_be_checked = 'ANY'
    if (ec['name'],ec['version']) in configopts_changes_based_on_easyblock_class_and_name.keys():
        name_to_be_checked = (ec['name'],ec['version'])

    for easyblock_class in configopts_changes_based_on_easyblock_class_and_name[name_to_be_checked].keys():
        if c == easyblock_class or issubclass(c,easyblock_class):
            print("Class type %s is subclass of %s:" % (str(c),str(easyblock_class)))
            changes = configopts_changes_based_on_easyblock_class_and_name[name_to_be_checked][easyblock_class]
            prepend_configopts(ec,changes['EBROOTGENTOO' in os.environ])

    if ec['name'] in configopts_changes.keys():
        print("Changing configopts for %s" % ec['name'])
        prepend_configopts(ec,configopts_changes[ec['name']]['EBROOTGENTOO' in os.environ])

    if ec['name'] in buildopts_changes:
        print("Changing buildopts for %s" % ec['name'])
        prepend_configopts(ec,buildopts_changes[ec['name']],'buildopts')

compiler_modluafooter = """
prepend_path("MODULEPATH", pathJoin("/cvmfs/soft.computecanada.ca/easybuild/modules/%s", os.getenv("RSNT_ARCH"), "Compiler/%s"))
if isDir(pathJoin(os.getenv("HOME"), ".local/easybuild/modules/%s", os.getenv("RSNT_ARCH"), "Compiler/%s")) then
    prepend_path("MODULEPATH", pathJoin(os.getenv("HOME"), ".local/easybuild/modules/%s", os.getenv("RSNT_ARCH"), "Compiler/%s"))
end

add_property("type_","tools")
"""

intel_modluafooter = """
prepend_path("INTEL_LICENSE_FILE", pathJoin("/cvmfs/soft.computecanada.ca/config/licenses/intel", os.getenv("CC_CLUSTER") .. ".lic"))

if isloaded("imkl") then
    always_load("imkl/2020.1.217")
end
"""

mpi_modluafooter = """
assert(loadfile("/cvmfs/soft.computecanada.ca/config/lmod/%s_custom.lua"))("%%(version_major_minor)s")

add_property("type_","mpi")
family("mpi")
"""

#See compilers_and_libraries_2020.0.166/licensing/compiler/en/credist.txt
intel_postinstallcmds = '''
    echo "--sysroot=$EPREFIX" > %(installdir)s/compilers_and_libraries_%(version)s/linux/bin/intel64/icc.cfg
    echo "--sysroot=$EPREFIX" > %(installdir)s/compilers_and_libraries_%(version)s/linux/bin/intel64/icpc.cfg
    /cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s
    /cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s/compilers_and_libraries_%(version)s/linux/compiler/lib --add_origin
    patchelf --set-rpath '$ORIGIN/../lib:$ORIGIN/../compiler/lib/intel64' %(installdir)s/compilers_and_libraries_%(version)s/linux/lib/LLVMgold.so
    installdir=%(installdir)s
    publicdir=${installdir/restricted.computecanada.ca/soft.computecanada.ca}
    for i in $(grep "compiler.*\.so" $installdir/compilers_and_libraries_%(version)s/licensing/compiler/en/credist.txt | cut -c 13-); do
       if [ -f $installdir/$i ]; then
         mkdir -p $(dirname $publicdir/$i)
         cp -p $installdir/$i $publicdir/$i
       fi
     done
     cd $installdir
     for i in compilers_and_libraries_%(version)s/linux/compiler/lib/*; do
       if [ -L $i ]; then
         cp -a $i $publicdir/$i
       fi
     done
     ln -s compilers_and_libraries_%(version)s/linux/compiler/lib $publicdir/lib
'''

def parse_hook(ec, *args, **kwargs):
    """Example parse hook to inject a patch file for a fictive software package named 'Example'."""
    modify_dependencies(ec,'dependencies')
    modify_dependencies(ec,'builddependencies')
    if 'EBROOTGENTOO' not in os.environ:
        return
    moduleclass = ec.get('moduleclass','')
    if moduleclass == 'compiler':
        year = os.environ['EBVERSIONGENTOO']
        name = ec['name'].lower()
        if name == 'iccifort':
            name = 'intel'
        comp = name + ec['version'][:ec['version'].find('.')]
        ec['modluafooter'] = compiler_modluafooter%(year,comp,year,comp,year,comp)
        if name != 'gcccore':
            ec['modluafooter'] += 'family("compiler")\n'
            if name == 'intel':
                # set via intel_modluafooter
                ec['skip_license_file_in_module'] = True
                ec['modluafooter'] = intel_modluafooter + ec['modluafooter']
                ec['modaltsoftname'] = name
                ec['license_file'] = "/cvmfs/soft.computecanada.ca/config/licenses/intel/computecanada.lic"
                ec['postinstallcmds'] = [intel_postinstallcmds]
    elif moduleclass == 'mpi':
        name = ec['name'].lower()
        if name == 'impi':
            name = intelmpi
        ec['modluafooter'] = mpi_modluafooter%name
        if name == 'openmpi':
            ec['postinstallcmds'] = ['rm %(installdir)s/lib/*.la %(installdir)s/lib/*/*.la']
            ec['dependencies'].append(('libfabric', '1.10.1'))
    if moduleclass == 'toolchain' or ec['name'] == 'GCCcore':
        ec['hidden'] = True

def pre_configure_hook(self, *args, **kwargs):
    "Modify configopts (here is more efficient than parse_hook since only called once)"
    modify_configopts(self.cfg)
