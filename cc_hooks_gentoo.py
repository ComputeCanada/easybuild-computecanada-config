from easybuild.framework.easyconfig.easyconfig import get_easyblock_class, get_toolchain_hierarchy
from easybuild.easyblocks.generic.cmakemake import CMakeMake
from easybuild.easyblocks.generic.mesonninja import MesonNinja
from easybuild.toolchains.system import SystemToolchain
from easybuild.toolchains.gcccore import GCCcore
from easybuild.framework.easyconfig.constants import EASYCONFIG_CONSTANTS
from distutils.version import LooseVersion
from cc_hooks_common import modify_all_opts, update_opts, PREPEND, APPEND, REPLACE, APPEND_LIST, DROP
from cc_hooks_common import get_matching_keys
from easybuild.tools.toolchain.utilities import search_toolchain
from easybuild.tools.environment import setvar
import os

SYSTEM = [('system', 'system')]
GCCCORE93 = [('GCCcore', '9.3.0')]
GCC93 = [('GCC', '9.3.0')]
ICC2020a = [('iccifort', '2020.1.217')]
COMPILERS_2020a = [ICC2020a[0], GCC93[0]]
cOMPI_2020a = [('iompi', '2020a'),('gompi', '2020a')]

# Dictionary containing version mapping
# Keys can be one of :
# - software name
# - (software name, software version)
# - (software name, 'ANY', version suffix)
# - (software name, software version, version suffix)
#
# The most specific key match will be used
#
# Values can be one of :
# - (new software version, list of compatible toolchains)
# - (new software version, list of compatible toolchains, None)
new_version_mapping_2020a = {
        'Boost': ('1.72.0', COMPILERS_2020a),
        ('Boost','ANY','-mpi'): ('1.72.0', cOMPI_2020a),
        ('CUDA', '11.0.2'): ('11.0', COMPILERS_2020a),
        'CGAL': ('4.14.3', COMPILERS_2020a, None),
        'ETSF_IO': ('1.0.4', [('iompi', '2020a'), ('iccifort', '2020.1.217')]),
        'FFTW': ('3.3.8', COMPILERS_2020a),
        ('FFTW','ANY','-mpi'): ('3.3.8', cOMPI_2020a),
        'Eigen': ('3.3.7', SYSTEM),
        'GDAL': ('3.0.4', GCC93, None),
        'GEOS': ('3.8.1', GCCCORE93, None),
        'GObject-Introspection': ('1.64.0', SYSTEM, None),
        'GSL': ('2.6', COMPILERS_2020a),
        ('GSL', '1.16'): ('1.16', COMPILERS_2020a),
        'JasPer': ('2.0.16', SYSTEM),
        ('Java', '11'): ('13', SYSTEM),
        ('HDF5','ANY',""): ('1.10.6', cOMPI_2020a + COMPILERS_2020a, None),
        ('HDF5','ANY','-mpi'): ('1.10.6', cOMPI_2020a),
        ('imkl','2020.1.217'): ('2020.1.217', SYSTEM),
        ('netCDF','ANY',""): ('4.7.4', cOMPI_2020a + COMPILERS_2020a, None),
        ('netCDF','ANY','-mpi'): ('4.7.4', cOMPI_2020a, None),
        ('netCDF-C++4','ANY', ""): ('4.3.1', cOMPI_2020a + COMPILERS_2020a, None),
        ('netCDF-C++4','ANY','-mpi'): ('4.3.1', cOMPI_2020a, None),
        ('netCDF-Fortran','ANY', ""): ('4.5.2', cOMPI_2020a + COMPILERS_2020a, None),
        ('netCDF-Fortran','ANY','-mpi'): ('4.5.2', cOMPI_2020a, None),
        ('ParaView', '5.8.0'): ('5.8.0', [('gompi', '2020a')], None),
        'PLUMED': ('2.6.1', cOMPI_2020a, None),
        'UDUNITS': ('2.2.26', SYSTEM),
        **dict.fromkeys([('Python', '2.7.%s' % str(x)) for x in range(0,18)], ('2.7', GCCCORE93)),
        **dict.fromkeys([('Python', '3.5.%s' % str(x)) for x in range(0,8)], ('3.7', GCCCORE93)),
        **dict.fromkeys([('Python', '3.6.%s' % str(x)) for x in range(0,10)], ('3.6', GCCCORE93)),
        **dict.fromkeys([('Python', '3.7.%s' % str(x)) for x in range(0,8)], ('3.7', GCCCORE93)),
        **dict.fromkeys([('Python', '3.8.%s' % str(x)) for x in range(0,5)], ('3.8', GCCCORE93)),
        'Qt5': ('5.12.8', GCCCORE93),
        'SCOTCH': ('6.0.9', cOMPI_2020a),
}

def modify_list_of_dependencies(ec, param, version_mapping, list_of_deps):
    name = ec["name"]
    version = ec["version"]
    toolchain_name = ec.toolchain.name
    if not list_of_deps or not isinstance(list_of_deps[0], tuple): 
        print("Error, modify_list_of_dependencies did not receive a list of tuples")
        return

    for n, dep in enumerate(list_of_deps):
        if isinstance(dep,list): dep = dep[0]
        dep_name, dep_version, *rest = tuple(dep)
        dep_version_suffix = rest[0] if len(rest) > 0 else ""

        matching_keys = get_matching_keys(ec, version_mapping)
        # search through possible matching keys
        match_found = False
        for key in matching_keys:
            # Skip dependencies on the same name
            if name == key or name == key[0]:
                continue
            new_version, supported_toolchains, *new_version_suffix = version_mapping[key]
            new_version_suffix = new_version_suffix[0] if len(new_version_suffix) == 1 else dep_version_suffix

            # test if one of the supported toolchains is a subtoolchain of the toolchain with which we are building. If so, a match is found, replace the dependency
            for tc_name, tc_version in supported_toolchains:
                try_tc, _ = search_toolchain(tc_name)
                if try_tc == SystemToolchain or try_tc == GCCcore or issubclass(ec.toolchain.__class__, try_tc):
                    match_found = True
                    new_dep = (dep_name, new_version, new_version_suffix, (tc_name, tc_version))
                    print("Matching updated %s found. Replacing %s with %s" % (param, str(dep), str(new_dep)))
                    list_of_deps[n] = new_dep
                    break

            if match_found: break

        if dep_name == 'SciPy-bundle':
            new_dep = ('SciPy-Stack', '2020a')
            print("Replacing %s with %s" % (str(dep), str(new_dep)))
            ec[param][n] = new_dep
        if dep_name == 'Boost.Serial':
            new_dep = ('Boost', dep_version)
            print("Replacing %s with %s" % (str(dep), str(new_dep)))
            ec[param][n] = new_dep
        if dep_name == 'HDF5.Serial':
            new_dep = ('HDF5', dep_version)
            print("Replacing %s with %s" % (str(dep), str(new_dep)))
            ec[param][n] = new_dep


    return list_of_deps

def modify_dependencies(ec, param, version_mapping):
    name = ec["name"]
    version = ec["version"]
    toolchain_name = ec.toolchain.name
    if ec[param] and isinstance(ec[param][0], list) and ec[param][0] and isinstance(ec[param][0][0], tuple):
        for n, deps in enumerate(ec[param]):
            ec[param][n] = modify_list_of_dependencies(ec, param, version_mapping, ec[param][n])
    elif ec[param] and isinstance(ec[param][0], tuple):
        ec[param] = modify_list_of_dependencies(ec, param, version_mapping, ec[param])



compiler_modluafooter = """
prepend_path("MODULEPATH", pathJoin("/cvmfs/soft.computecanada.ca/easybuild/modules/{year}", os.getenv("RSNT_ARCH"), "{sub_path}"))
if isDir(pathJoin(os.getenv("HOME"), ".local/easybuild/modules/{year}", os.getenv("RSNT_ARCH"), "{sub_path}")) then
    prepend_path("MODULEPATH", pathJoin(os.getenv("HOME"), ".local/easybuild/modules/{year}", os.getenv("RSNT_ARCH"), "{sub_path}"))
end

add_property("type_","tools")
"""

mpi_modluafooter = """
assert(loadfile("/cvmfs/soft.computecanada.ca/config/lmod/%s_custom.lua"))("%%(version_major_minor)s")

add_property("type_","mpi")
family("mpi")
"""

openfoam_modluafooter = """
local wm_compiler = "%s"
local wm_label_size = "32"

-- Nothing below this line should need changing for a different version or compiler
local version = "%%(version)s"
local wm_project = "%%(name)s"
local wm_project_dir = pathJoin(root, wm_project .. "-" .. version)
local wm_thirdparty_dir = pathJoin(root, "ThirdParty-" .. version)
local wm_project_user_dir = pathJoin(os.getenv("HOME"), wm_project, os.getenv("USER") .. "-" .. version)
local wm_options_no_opt = "linux64" .. wm_compiler .. "DPInt" .. wm_label_size
local wm_options = wm_options_no_opt .. "Opt"

local foam_site_dir = pathJoin(root, "site", version, "platforms", wm_options)
local platform_dir = pathJoin(wm_project_dir, "platforms", wm_options)
local foam_usr_dir = pathJoin(wm_project_user_dir, "platforms", wm_options)

setenv("WM_THIRD_PARTY_DIR", wm_thirdparty_dir)
setenv("FOAM_EXT_LIBBIN", pathJoin(wm_thirdparty_dir,"platforms",wm_options_no_opt,"lib"))
setenv("BOOST_ARCH_PATH", "")
setenv("CGAL_ARCH_PATH", "")
setenv("FOAMY_HEX_MESH", "yes")
setenv("FOAM_APP", pathJoin(wm_project_dir, "applications"))
setenv("FOAM_APPBIN", pathJoin(platform_dir, "bin"))
setenv("FOAM_ETC", pathJoin(wm_project_dir, "etc"))
setenv("FOAM_JOB_DIR", pathJoin(root, "jobControl"))
setenv("FOAM_LIBBIN", pathJoin(platform_dir, "lib"))
setenv("FOAM_MPI", "mpi")
setenv("FOAM_RUN", pathJoin(wm_project_user_dir, "run"))
setenv("FOAM_SETTINGS", "")
setenv("FOAM_SIGFPE", "")
setenv("FOAM_SITE_APPBIN", pathJoin(foam_site_dir, "bin"))
setenv("FOAM_SITE_LIBBIN", pathJoin(foam_site_dir, "lib"))
setenv("FOAM_SOLVERS", pathJoin(wm_project_dir, "applications", "solvers"))
setenv("FOAM_SRC", pathJoin(wm_project_dir, "src"))
setenv("FOAM_TUTORIALS", pathJoin(wm_project_dir, "tutorials"))
setenv("FOAM_USER_APPBIN", pathJoin(foam_usr_dir, "bin"))
setenv("FOAM_USER_LIBBIN", pathJoin(foam_usr_dir, "lib"))
setenv("FOAM_UTILITIES", pathJoin(wm_project_dir, "applications" , "utilities"))
prepend_path("LD_LIBRARY_PATH", pathJoin(wm_project_dir,"platforms",wm_options,"lib","dummy"))
prepend_path("LD_LIBRARY_PATH", pathJoin(wm_thirdparty_dir,"platforms",wm_options_no_opt,"lib"))
prepend_path("LD_LIBRARY_PATH", pathJoin(platform_dir,"lib"))
prepend_path("LD_LIBRARY_PATH", pathJoin(foam_site_dir,"lib"))
prepend_path("LD_LIBRARY_PATH", pathJoin(foam_usr_dir,"lib"))
prepend_path("LD_LIBRARY_PATH", pathJoin(wm_thirdparty_dir,"platforms",wm_options_no_opt,"lib","mpi"))
prepend_path("LD_LIBRARY_PATH", pathJoin(platform_dir,"lib","mpi"))
prepend_path("PATH", pathJoin(wm_project_dir, "bin"))
prepend_path("PATH", pathJoin(wm_project_dir, "wmake"))
prepend_path("PATH", pathJoin(platform_dir, "bin"))
prepend_path("PATH", pathJoin(foam_site_dir, "bin"))
prepend_path("PATH", pathJoin(foam_usr_dir, "bin"))
setenv("MPI_BUFFER_SIZE", "20000000")
setenv("WM_ARCH", "linux64")
setenv("WM_ARCH_OPTION", "64")
setenv("WM_CC", "")
setenv("WM_CFLAGS", "")
setenv("WM_COMPILER_LIB_ARCH", "64")
setenv("WM_COMPILER_TYPE", "system")
setenv("WM_COMPILE_OPTION", "Opt")
setenv("WM_CXX", "")
setenv("WM_CXXFLAGS", "")
setenv("WM_DIR", pathJoin(wm_project_dir, "wmake"))
setenv("WM_LABEL_OPTION", "Int" .. wm_label_size)
setenv("WM_LDFLAGS", "")
setenv("WM_LINK_LANGUAGE", "c++")
setenv("WM_OPTIONS", wm_options)
setenv("WM_OSTYPE", "POSIX")
setenv("WM_PRECISION_OPTION", "DP")
setenv("WM_PROJECT", "OpenFOAM")
setenv("WM_PROJECT_DIR", wm_project_dir)
setenv("WM_PROJECT_INST_DIR", root)
setenv("WM_PROJECT_USER_DIR", wm_project_user_dir)

set_alias("app", 'cd $FOAM_APP')
set_alias("foam", 'cd $WM_PROJECT_DIR')
set_alias("foam3rdParty", 'cd $WM_THIRD_PARTY_DIR')
set_alias("foamApps", 'cd $FOAM_APP')
set_alias("foamSite", 'cd $WM_PROJECT_INST_DIR/site')
set_alias("foamSol", 'cd $FOAM_SOLVERS')
set_alias("foamTuts", 'cd $FOAM_TUTORIALS')
set_alias("foamUtils", 'cd $FOAM_UTILITIES')
set_alias("foamfv", 'cd $FOAM_SRC/finiteVolume')
set_alias("foamsrc", 'cd $FOAM_SRC/$WM_PROJECT')
set_alias("lib", 'cd $FOAM_LIBBIN')
set_alias("run", 'cd $FOAM_RUN')
set_alias("sol", 'cd $FOAM_SOLVERS')
set_alias("src", 'cd $FOAM_SRC')
set_alias("tut", 'cd $FOAM_TUTORIALS')
set_alias("util", 'cd $FOAM_UTILITIES')
set_alias("wm32", 'wmSET WM_ARCH_OPTION=32')
set_alias("wm64", 'wmSET WM_ARCH_OPTION=64')
set_alias("wmDP", 'wmSET WM_PRECISION_OPTION=DP')
set_alias("wmSET", '. $WM_PROJECT_DIR/etc/bashrc')
set_alias("wmSP", 'wmSET WM_PRECISION_OPTION=SP')
set_alias("wmSchedOFF", 'unset WM_SCHEDULER')
set_alias("wmSchedON", 'export WM_SCHEDULER=$WM_PROJECT_DIR/wmake/wmakeScheduler')
set_alias("wmUNSET", '. $WM_PROJECT_DIR/etc/config/unset.sh')

local paraview_dir = os.getenv("EBROOTPARAVIEW") or ""
local paraview_ver = "%s"
local paraview_major = "%s"
pushenv("ParaView_DIR", paraview_dir)
pushenv("ParaView_GL","mesa")
pushenv("ParaView_INCLUDE_DIR", pathJoin(paraview_dir, "include", "paraview-" .. paraview_major))
pushenv("ParaView_LIB_DIR", pathJoin(paraview_dir, "lib64"))
setenv("ParaView_MAJOR", paraview_major)
setenv("ParaView_VERSION", paraview_ver)
setenv("PV_PLUGIN_PATH", pathJoin(platform_dir, "lib", "paraview-" .. paraview_major))
"""

opts_changes = {
    'Boost.Serial': {
        'name': ('Boost', REPLACE),
        'multi_deps': ({'Python': ['2.7', '3.6', '3.7', '3.8']}, REPLACE),
        'builddependencies': ([[('SciPy-Stack', '2020a'), ('Python', v)] for v in ['2.7', '3.6', '3.7', '3.8'] ], REPLACE),
        'patches': (['Boost-1.65.1_python3.patch'], REPLACE),
        'checksums': ('d86d34cf48fdbc4b9a36ae7706b3f3353f9ad521ff1d5a716cce750ae9f5dd33', APPEND_LIST),
    },
    'Boost': {
        'configopts': ('--without-libraries=python', DROP),
        'prebuildopts': ('[ "$(ls -A %(installdir)s)" ] && mv %(installdir)s/* %(builddir)s/obj ; ', REPLACE),
    },
    'BioPerl': {
        'dependencies': ([('Perl', '5.30.2'), ('XML-LibXML', '2.0205')], REPLACE),
    },
    'BOLT-LMM': {
        'postinstallcmds': (['/cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s '], REPLACE),
    },
    'Clang': {
        'preconfigopts': ("""pushd %(builddir)s/llvm-%(version)s.src/tools/clang; """ +
                 # Use ${EPREFIX} as default sysroot
                 """sed -i -e "s@DEFAULT_SYSROOT \\"\\"@DEFAULT_SYSROOT \\"${EPREFIX}\\"@" CMakeLists.txt ; """ +
                 """pushd lib/Driver/ToolChains ; """ +
                 # Use dynamic linker from ${EPREFIX}
                 """sed -i -e "/LibDir.*Loader/s@return \\"\/\\"@return \\"${EPREFIX%/}/\\"@" Linux.cpp ; """ +
                 # Remove --sysroot call on ld for native toolchain
                 """sed -i -e "$(grep -n -B1 sysroot= Gnu.cpp | sed -ne '{1s/-.*//;1p}'),+1 d" Gnu.cpp ; """ +
                 """popd; popd ; """,
                 PREPEND)
    },
    'cram': {
        'multi_deps': ({'Python': ['2.7', '3.6', '3.7', '3.8']}, REPLACE),
        'modluafooter': ('depends_on("python")', REPLACE),
    },
    ('CUDA', '11.0.2'): {
        'version': ('11.0', REPLACE),
    },
    ('CUDAcore','10.2.89'): {
        'builddependencies': ([('GCCcore', '8.4.0')], REPLACE),
        'postinstallcmds': (['/cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s --add_origin'], REPLACE),
    },
    'CUDAcore': {
        'postinstallcmds': (['/cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s --add_origin'], REPLACE),
    },
    'GCCcore': {
        # build EPREFIX-aware GCCcore
        'preconfigopts': (
                    "if [ -f ../gcc/gcc.c ]; then sed -i 's/--sysroot=%R//' ../gcc/gcc.c; " +
                    "for h in ../gcc/config/*/*linux*.h; do " +
                    r'sed -i -r "/_DYNAMIC_LINKER/s,([\":])(/lib),\1${EPREFIX}\2,g" $h; done; fi; ',
                    PREPEND ),
        'configopts': ("--with-sysroot=$EPREFIX", PREPEND),
        # remove .la files, as they mess up rpath when libtool is used
        'postinstallcmds': (["find %(installdir)s -name '*.la' -delete"], REPLACE),
    },
    'GObject-Introspection': {
        'dependencies': ([], REPLACE),
        'modluafooter': ('depends_on(atleast("python", "3"))', REPLACE),
        'versionsuffix': ('', REPLACE),
    },
    'HDF5.Serial': {
        'name': ('HDF5', REPLACE),
    },
    'iccifort': {
        'skip_license_file_in_module': (True, REPLACE),
        'license_file': ("/cvmfs/soft.computecanada.ca/config/licenses/intel/computecanada.lic", REPLACE),
        #See compilers_and_libraries_2020.1.217/licensing/compiler/en/credist.txt
        'postinstallcmds': (['''
    echo "--sysroot=$EPREFIX" > %(installdir)s/compilers_and_libraries_%(version)s/linux/bin/intel64/icc.cfg
    echo "--sysroot=$EPREFIX" > %(installdir)s/compilers_and_libraries_%(version)s/linux/bin/intel64/icpc.cfg
    /cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s
    /cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s/compilers_and_libraries_%(version)s/linux/compiler/lib --add_origin
    patchelf --set-rpath '$ORIGIN/../lib:$ORIGIN/../compiler/lib/intel64' %(installdir)s/compilers_and_libraries_%(version)s/linux/lib/LLVMgold.so
    installdir=%(installdir)s
    publicdir=${installdir/restricted.computecanada.ca/soft.computecanada.ca}
    rm -rf $publicdir
    for i in $(grep -h "compiler.*\.so" $installdir/compilers_and_libraries_%(version)s/licensing/compiler/en/[cf]redist.txt | cut -c 13-); do
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
'''], REPLACE),
        "modluafooter": ("""
prepend_path("INTEL_LICENSE_FILE", pathJoin("/cvmfs/soft.computecanada.ca/config/licenses/intel", os.getenv("CC_CLUSTER") .. ".lic"))

if isloaded("imkl") then
    always_load("imkl/2020.1.217")
end
""", APPEND),
    },
    'impi': {
        'set_mpi_wrappers_all': (True, REPLACE),
        # Fix mpirun from IntelMPI to explicitly unset I_MPI_PMI_LIBRARY
        # it can only be used with srun.
        'postinstallcmds': ([
                "sed -i 's@\\(#!/bin/sh.*\\)$@\\1\\nunset I_MPI_PMI_LIBRARY@' %(installdir)s/intel64/bin/mpirun",
                "/cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s/intel64/bin --add_path='$ORIGIN/../lib/release'",
                "for dir in release release_mt debug debug_mt; do /cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s/intel64/lib/$dir --add_path='$ORIGIN/../../libfabric/lib'; done",
                "patchelf --set-rpath $EBROOTUCX/lib --force-rpath %(installdir)s/intel64/libfabric/lib/prov/libmlx-fi.so"
            ], REPLACE),
        'modluafooter': (mpi_modluafooter % 'intelmpi', REPLACE),
    },
    'IQ-TREE': {
        'toolchainopts': ({}, REPLACE),
        'configopts': ('-DIQTREE_FLAGS=omp', REPLACE),
        'sanity_check_paths': ({'files': ['bin/iqtree'], 'dirs': []}, REPLACE),
    },
    'iq-tree-mpi': {
        'configopts': ('-DIQTREE_FLAGS=mpi', REPLACE),
        'sanity_check_paths': ({'files': ['bin/iqtree-mpi'], 'dirs': []}, REPLACE),
    },
    'Java': {
        'postinstallcmds': (['/cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s'], REPLACE),
    },
    'OpenBLAS': {
        **dict.fromkeys(['buildopts','installopts','testopts'],
                        ({'sse3': 'DYNAMIC_ARCH=1',
                        'avx': 'TARGET=SANDYBRIDGE',
                        'avx2': 'DYNAMIC_ARCH=1 DYNAMIC_LIST="HASWELL ZEN SKYLAKEX"',
                        'avx512': 'TARGET=SKYLAKEX'}[os.getenv('RSNT_ARCH')] + ' NUM_THREADS=64',
                        PREPEND))
    },
    ("OpenFOAM", "8"): {
        'patches': (['OpenFOAM-8-cleanup-cc.patch'], APPEND_LIST),
        'checksums': ('51ef17739ced32c1cbf239c377bbf4abfa4e4f12eaf19a635c432e071ce58197', APPEND_LIST),
        'modluafooter': (openfoam_modluafooter % ('Gcc', '5.8.0', '5.8'), REPLACE),
    },
    "OpenMPI": {
        # local customizations for OpenMPI
        'configopts': ('--enable-shared --with-verbs ' +
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
                    'ras-tm,spml-ucx,sshmem-ucx,hwloc-external',
                    PREPEND),
        'postinstallcmds': (['rm %(installdir)s/lib/*.la %(installdir)s/lib/*/*.la'], REPLACE),
        'modluafooter': (mpi_modluafooter % 'openmpi', REPLACE),
        'dependencies': (('libfabric', '1.10.1'), APPEND_LIST),
    },
    'Python': {
        'modextrapaths': ({'PYTHONPATH': ['/cvmfs/soft.computecanada.ca/easybuild/python/site-packages']}, REPLACE),
        'allow_prepend_abs_path': (True, REPLACE),
        'prebuildopts': ('sed -i -e "s;/usr;$EBROOTGENTOO;g" setup.py && ', REPLACE),
        'installopts': (' && /cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s --add_path %(installdir)s/lib --any_interpreter', REPLACE),
    },
    'UCX': {
        # local customizations for UCX
        'configopts': ("--with-rdmacm=$EBROOTGENTOO --with-verbs=$EBROOTGENTOO --with-knem=$EBROOTGENTOO ", PREPEND)
    },
}



# modules with both -mpi and no-mpi varieties
mpi_modaltsoftname = ['fftw', 'hdf5', 'netcdf-c++4', 'netcdf-c++', 'netcdf-fortran', 'netcdf', 'iq-tree', 'boost', 'vtk', 'libgridxc', 'etsf_io']
modaltsoftnames = {
    "iccifort": "intel",
    "impi": "intelmpi",
}
def set_modaltsoftname(ec):
    if ec['name'] in modaltsoftnames:
        ec['modaltsoftname'] = modaltsoftnames[ec['name']]

    # add -mpi to module name for various modules with both -mpi and no-mpi varieties
    toolchain = ec.get('toolchain')
    toolchain_class, _ = search_toolchain(toolchain['name'])
    if (ec['name'].lower() in mpi_modaltsoftname and
        (toolchain_class(version=toolchain['version']).mpi_family() or (ec['toolchainopts'] and ec['toolchainopts'].get('usempi')))
       ):
        ec['modaltsoftname'] = ec['name'].lower() + '-mpi'
        ec['versionsuffix'] = '-mpi'


def disable_use_mpi_for_non_mpi_toolchains(ec):
    toolchain = ec.get('toolchain')
    toolchain_class, _ = search_toolchain(toolchain['name'])
    if ec['toolchainopts'] and ec['toolchainopts'].get('usempi') and not toolchain_class(version=toolchain['version']).mpi_family():
        print("usempi option found, but using a non-MPI toolchain. Disabling it")
        del ec['toolchainopts']['usempi']
        print("New toolchainopts:%s" % str(ec['toolchainopts']))


def set_modluafooter(ec):
    matching_keys = get_matching_keys(ec, opts_changes)
    for key in matching_keys:
        if 'modluafooter' in opts_changes[key]:
            update_opts(ec, opts_changes[key]['modluafooter'][0], 'modluafooter', opts_changes[key]['modluafooter'][1])

    moduleclass = ec.get('moduleclass','')
    year = os.environ['EBVERSIONGENTOO']
    name = ec['name'].lower()
    if moduleclass == 'compiler' and not name == 'gcccore' and not name == 'llvm':
        if name == 'iccifort':
            name = 'intel'
        comp = os.path.join('Compiler', name + ec['version'][:ec['version'].find('.')])
        ec['modluafooter'] = (compiler_modluafooter.format(year=year,sub_path=comp) + 'family("compiler")\n')
    if ec['name'] == 'CUDAcore':
        comp = os.path.join('CUDA', 'cuda' + '.'.join(ec['version'].split('.')[:2]))
        ec['modluafooter'] = compiler_modluafooter.format(year=year, sub_path=comp)


def add_dependencies(ec, keyword):
    matching_keys = get_matching_keys(ec, opts_changes)
    for key in matching_keys:
        if keyword in opts_changes[key]:
            update_opts(ec, opts_changes[key][keyword][0], keyword, opts_changes[key][keyword][1])

def drop_dependencies(ec, param):
    # dictionary in format <name>:<version under which to drop>
    to_drop = {
            'CMake': 'ALL',
            'ICU': 'ALL',
            'libxslt': 'ALL',
            'libzip': 'ALL',
            'Meson': 'ALL',
            'Ninja': 'ALL',
            'PyQt5': 'ALL',
            'SQLite': 'ALL',
            'pybind11': 'ALL',
    }
    # iterate over a copy
    for dep in ec[param][:]:
        if isinstance(dep, list):
            dep_copy = dep[:]
            for d in dep_copy:
                name, version = d[0], d[1]
                if name in to_drop:
                    if to_drop[name] == 'ALL' or LooseVersion(version) < LooseVersion(to_drop[name]):
                        print("Dropped %s, %s from %s" % (name, version, param))
                        dep.remove(d)

        else:
            dep_list = list(dep)
            if dep_list[0] == ec.name:
                continue
            if dep_list[0] in to_drop:
                if to_drop[dep_list[0]] == 'ALL' or LooseVersion(dep_list[1]) < LooseVersion(to_drop[dep_list[0]]):
                    print("Dropped %s, %s from %s" % (dep_list[0],dep_list[1],param))
                    ec[param].remove(dep)


def parse_hook(ec, *args, **kwargs):
    """Example parse hook to inject a patch file for a fictive software package named 'Example'."""
    disable_use_mpi_for_non_mpi_toolchains(ec)
    set_modaltsoftname(ec)
    modify_all_opts(ec, opts_changes, opts_to_skip=[], opts_to_change=['multi_deps', 'dependencies', 'builddependencies', 'license_file', 'version', 'name', 'patches', 'checksums', 'versionsuffix'])
    modify_dependencies(ec, 'dependencies', new_version_mapping_2020a)
    modify_dependencies(ec, 'builddependencies', new_version_mapping_2020a)
    drop_dependencies(ec, 'dependencies')
    drop_dependencies(ec, 'builddependencies')
    set_modluafooter(ec)

    # always disable multi_deps_load_default when multi_deps is used
    if ec.get('multi_deps', None): 
        ec['multi_deps_load_default'] = False

    # hide toolchains
    if ec.get('moduleclass','') == 'toolchain' or ec['name'] == 'GCCcore' or ec['name'] == 'CUDAcore':
        ec['hidden'] = True

    # special parse hook for Python
    if ec['name'].lower() == 'python':
        python_parsehook(ec)


def python_parsehook(ec):
    # keep only specific extensions
    python_extensions_to_keep = ['setuptools', 'pip', 'wheel', 'virtualenv', 'appdirs', 'distlib', 'filelock',
                                 'six']
    ver = LooseVersion(ec['version'])
    if ver < LooseVersion('3.8'):
        python_extensions_to_keep += ['importlib_metadata', 'importlib_resources', 'zipp']
    if ver < LooseVersion('3.0'): # 2.7
        python_extensions_to_keep += ['contextlib2', 'pathlib2', 'configparser', 'scandir',
                                      'singledispatch', 'typing']
    else: # 3.6, 3.7
        python_extensions_to_keep += ['more-itertools']

    new_ext_list = [ext for ext in ec['exts_list'] if ext[0] in python_extensions_to_keep]
    ec['exts_list'] = new_ext_list


def pre_configure_hook(self, *args, **kwargs):
    "Modify configopts (here is more efficient than parse_hook since only called once)"
    orig_enable_templating = self.cfg.enable_templating
    self.cfg.enable_templating = False

    modify_all_opts(self.cfg, opts_changes)

    # additional changes for CMakeMake EasyBlocks
    ec = self.cfg
    if ec.easyblock is None or isinstance(ec.easyblock, str):
        c = get_easyblock_class(ec.easyblock, name=ec.name)
    elif isinstance(ec.easyblock, type):
        c = ec.easyblock
    if c == CMakeMake or issubclass(c,CMakeMake):
        # skip for those
        if (ec['name'],ec['version']) in [('ROOT','5.34.36'), ('mariadb', '10.4.11')]:
            pass
        else:
            update_opts(ec, ' -DCMAKE_SKIP_INSTALL_RPATH=ON ', 'configopts', PREPEND)

    # additional changes for MesonNinja EasyBlocks
    if c == MesonNinja or issubclass(c,MesonNinja):
        update_opts(ec, False, 'fail_on_missing_ninja_meson_dep', REPLACE)

    self.cfg.enable_templating = orig_enable_templating

def post_module_hook(self, *args, **kwargs):
    "Modify GCCcore toolchain to system toolchain for ebfiles_repo only"
    # So we get name-version.eb there, but the toolchain inside does not change
    toolchain = self.cfg.get('toolchain')
    if toolchain and toolchain['name'] == 'GCCcore':
        self.cfg['toolchain'] = EASYCONFIG_CONSTANTS['SYSTEM'][0]

def pre_prepare_hook(self, *args, **kwargs):
    setvar("EBROOTLIBXML2", os.environ["EBROOTGENTOO"])

