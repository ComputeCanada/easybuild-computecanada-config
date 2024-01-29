from easybuild.framework.easyconfig.easyconfig import get_easyblock_class, get_toolchain_hierarchy
from easybuild.easyblocks.generic.cmakemake import CMakeMake
from easybuild.easyblocks.generic.cmakeninja import CMakeNinja
from easybuild.easyblocks.generic.mesonninja import MesonNinja
from easybuild.toolchains.system import SystemToolchain
from easybuild.toolchains.gcccore import GCCcore
from easybuild.framework.easyconfig.constants import EASYCONFIG_CONSTANTS
from distutils.version import LooseVersion
import sys, os
parentdir = os.path.dirname(os.path.dirname(__file__))
if parentdir not in sys.path:
    sys.path.append(parentdir)
from cc_hooks_common import modify_all_opts, update_opts, PREPEND, APPEND, REPLACE, APPEND_LIST, DROP, DROP_FROM_LIST, REPLACE_IN_LIST
from cc_hooks_common import get_matching_keys, get_matching_keys_from_ec
from easybuild.tools.config import build_option
from easybuild.tools.toolchain.utilities import search_toolchain
from easybuild.tools.environment import setvar
from easybuild.tools.run import run_cmd
import uuid
import shutil

# options to change in parse_hook, others are changed in other hooks
PARSE_OPTS = ['multi_deps', 'dependencies', 'builddependencies', 'license_file', 'version', 'name',
              'source_urls', 'sources', 'patches', 'checksums', 'versionsuffix', 'modaltsoftname',
              'skip_license_file_in_module', 'withnvptx', 'skipsteps']

SYSTEM = [('system', 'system')]
GCCCORE123 = [('GCCcore', '12.3.0'), ('GCCcore', '12.3-gentoo')]
GCC123 = [('GCC', '12.3.0')]
ICC2023a = [('intel-compilers', '2023.2.1')]
COMPILERS_2023a = [ICC2023a[0], GCC123[0]]
cOMPI_2023a = [('iompi', '2023a'),('gompi', '2023a')]
cOMKL_2023a = [('iomkl', '2023a'),('gomkl', '2023a')]

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
new_version_mapping_2023a = {
        ('Boost', 'ANY', ''): ('1.82.0', COMPILERS_2023a),
        ('Boost.MPI','ANY', ''): ('1.82.0', cOMPI_2023a),
        ('CUDA', '12.2.2'): ('12.2', COMPILERS_2023a),
        'CGAL': ('5.5.2', SYSTEM),
        'CMake': ('3.26.5', SYSTEM),
        'ETSF_IO': ('1.0.4', [('iompi', '2023a'), ('iccifort', '2020.1.217')]),
        ('FFTW', 'ANY', ""): ('3.3.10', COMPILERS_2023a),
        ('FFTW.MPI', 'ANY', ''): ('3.3.10', cOMPI_2023a),
        'Eigen': ('3.4.0', SYSTEM),
        ('GCCcore', '12.3.0'): ('12.3', SYSTEM, '-gentoo'),
        'GSL': ('2.7', COMPILERS_2023a),
        ('Java', '11'): ('17', SYSTEM),
        ('HDF5','ANY',''): ('1.14.2', COMPILERS_2023a),
        ('HDF5','ANY',''): ('1.14.2', cOMPI_2023a, '-mpi'),
        ('HDF5','ANY','-mpi'): ('1.14.2', cOMPI_2023a, '-mpi'),
        ('imkl','2023.1.0'): ('2023.2.0', SYSTEM),
        ('imkl','2023.2.0'): ('2023.2.0', SYSTEM),
        ('intel-compilers', '2023.1.0'): ('2023.2.1', SYSTEM),
        ('libbeef', '0.1.2'): ('0.1.2', COMPILERS_2023a),
        'libcerf': ('2.4', GCCCORE123),
        ('netCDF','ANY',""): ('4.9.2', COMPILERS_2023a),
        ('netCDF','ANY',""): ('4.9.2', cOMPI_2023a, '-mpi'),
        ('netCDF','ANY','-mpi'): ('4.9.2', cOMPI_2023a, '-mpi'),
        ('netCDF-C++4','ANY', ""): ('4.3.1', COMPILERS_2023a),
        ('netCDF-C++4','ANY', ""): ('4.3.1', cOMPI_2023a, '-mpi'),
        ('netCDF-C++4','ANY','-mpi'): ('4.3.1', cOMPI_2023a, '-mpi'),
        ('netCDF-Fortran','ANY', ""): ('4.6.1', COMPILERS_2023a),
        ('netCDF-Fortran','ANY', ""): ('4.6.1', cOMPI_2023a, '-mpi'),
        ('netCDF-Fortran','ANY','-mpi'): ('4.6.1', cOMPI_2023a, '-mpi'),
        ('ParaView', '5.8.0'): ('5.8.0', [('gompi', '2023a')], None),
        'Perl': ('5.36.1', SYSTEM),
        ('PLUMED', '2.6.0'): ('2.6.2', cOMKL_2023a, None),
        'UDUNITS': ('2.2.28', SYSTEM),
        **dict.fromkeys([('Python', '3.10.%s' % str(x)) for x in range(0,14)], ('3.10', GCCCORE123)),
        **dict.fromkeys([('Python', '3.11.%s' % str(x)) for x in range(0,6)], ('3.11', GCCCORE123)),
        'Qt5': ('5.15.11', GCCCORE123 + SYSTEM),
        'SCOTCH': ('7.0.3', cOMPI_2023a, None),
}

def modify_list_of_dependencies(ec, param, version_mapping, list_of_deps):
    name = ec["name"]
    version = ec["version"]
    toolchain_name = ec.toolchain.name
    new_dep = None
    if not list_of_deps or not isinstance(list_of_deps[0], tuple): 
        print("Error, modify_list_of_dependencies did not receive a list of tuples")
        return

    for n, dep in enumerate(list_of_deps):
        if isinstance(dep,list): dep = dep[0]
        dep_name, dep_version, *rest = tuple(dep)
        dep_version_suffix = rest[0] if len(rest) > 0 else ""

        matching_keys = get_matching_keys(dep_name, dep_version, dep_version_suffix, version_mapping)
        # search through possible matching keys
        match_found = False
        for key in matching_keys:
            # Skip dependencies on the same name
            if name == key or name == key[0]:
                continue
            new_version, supported_toolchains, *new_version_suffix = version_mapping[key]
            new_version_suffix = new_version_suffix[0] if len(new_version_suffix) == 1 else dep_version_suffix

            # test if one of the supported toolchains is a subtoolchain of the toolchain with which we are building. If so, a match is found, replace the dependency
            supported_versions = [tc[1] for tc in supported_toolchains]
            for tc_name, tc_version in supported_toolchains:
                try_tc, _ = search_toolchain(tc_name)
                # for whatever reason, issubclass and class comparison does not work. It is the same class name, but not the same class, so comparing strings
                str_mro = [str(x) for x in ec.toolchain.__class__.__mro__]
                if try_tc == SystemToolchain or str(try_tc) in str_mro and ec.toolchain.version in supported_versions:
                    match_found = True
                    new_dep = (dep_name, new_version, new_version_suffix, (tc_name, tc_version))
                    if str(new_dep) != str(dep):
                        print("%s: Matching updated %s found. Replacing %s with %s" % (ec.filename(), param, str(dep), str(new_dep)))
                    list_of_deps[n] = new_dep
                    break

            if match_found: break

        if dep_name == 'SciPy-bundle':
            new_dep = ('SciPy-Stack', '2023b')
        elif dep_name == 'Boost.Serial':
            new_dep = ('Boost', dep_version)
        elif dep_name == 'HDF5.Serial':
            new_dep = ('HDF5', dep_version)
        elif dep_name == 'netCDF.Serial':
            new_dep = ('netCDF', dep_version)
        elif dep_name == 'libfabric' and new_dep is not None and new_dep[0] == 'libfabric':
            dep = new_dep
            new_dep = dep[:2]
        else:
            new_dep = None
        if new_dep is not None and str(new_dep) != str(dep):
            ec[param][n] = new_dep
            print("%s: Replacing %s with %s" % (ec.filename(), str(dep), str(new_dep)))


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
local arch = "x86-64-v3"
if os.getenv("RSNT_ARCH") == "avx512" then
	arch = "x86-64-v4"
end
prepend_path("MODULEPATH", pathJoin("/cvmfs/soft.computecanada.ca/easybuild/modules/{year}", arch, "{sub_path}"))
if isDir(pathJoin(os.getenv("HOME"), ".local/easybuild/modules/{year}", arch, "{sub_path}")) then
    prepend_path("MODULEPATH", pathJoin(os.getenv("HOME"), ".local/easybuild/modules/{year}", arch, "{sub_path}"))
end

add_property("type_","tools")
"""

mpi_modluafooter = """
assert(loadfile("/cvmfs/soft.computecanada.ca/config/lmod/%s_custom.lua"))("%%(version_major_minor)s")

add_property("type_","mpi")
family("mpi")
"""

intelmpi2021_dict = {
    'accept_eula': (True, REPLACE),
    'set_mpi_wrappers_all': (True, REPLACE),
    # Fix mpirun from IntelMPI to explicitly unset I_MPI_PMI_LIBRARY
    # it can only be used with srun.
    'postinstallcmds': ([
        "sed -i 's@\\(#!/bin/sh.*\\)$@\\1\\nunset I_MPI_PMI_LIBRARY@' %(installdir)s/mpi/%(version)s/bin/mpirun",
        "/cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s/mpi/%(version)s/bin",
        "for i in %(installdir)s/mpi/%(version)s/bin/I*; do patchelf --set-rpath '$ORIGIN/../lib/release' --force-rpath $i; done",
        "patchelf --set-rpath '$ORIGIN/../lib/release:$ORIGIN/../libfabric/lib' --force-rpath %(installdir)s/mpi/%(version)s/bin/impi_info",
        "for dir in release debug; do /cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s/mpi/%(version)s/lib/$dir --add_path='$ORIGIN/../../libfabric/lib'; done",
        "patchelf --set-rpath $EBROOTUCX/lib --force-rpath %(installdir)s/mpi/%(version)s/libfabric/lib/prov/libmlx-fi.so"
    ], REPLACE),
    'modluafooter': (mpi_modluafooter % 'intelmpi', REPLACE),
}

opts_changes = {
    'ALPSCore': {
        'dependencies': ([('Boost', '1.72.0'), ('HDF5', '1.8.22'), ('Eigen', '3.3.7', '', True) ], REPLACE)
    },
    'Apptainer': {
        'modluafooter': ('assert(loadfile("/cvmfs/soft.computecanada.ca/config/lmod/apptainer_custom.lua"))()', REPLACE),
    },
    'Bazel': {
        # Bazel really needs to use Java 11, not 13
        'dependencies': ([('Java', '11', '', True)], REPLACE)
    },
    'Boost.Serial': {
        'name': ('Boost', REPLACE),
        'multi_deps': ({'Python': ['2.7', '3.6', '3.7', '3.8']}, REPLACE),
        'builddependencies': ([[('SciPy-Stack', '2023a'), ('Python', v)] for v in ['2.7', '3.6', '3.7', '3.8'] ], REPLACE),
        'patches': (['Boost-1.65.1_python3.patch'], REPLACE),
        'checksums': ('d86d34cf48fdbc4b9a36ae7706b3f3353f9ad521ff1d5a716cce750ae9f5dd33', APPEND_LIST),
    },
    'Boost': {
        'configopts': ('--without-libraries=python', DROP),
        'prebuildopts': ('[ "$(ls -A %(installdir)s)" ] && mv %(installdir)s/* %(builddir)s/obj ; ', REPLACE),
    },
    'Boost.MPI': {
        'modaltsoftname': ('boost-mpi', REPLACE),
        'configopts': ('--without-libraries=python', DROP),
        'prebuildopts': ('[ "$(ls -A %(installdir)s)" ] && mv %(installdir)s/* %(builddir)s/obj ; ', REPLACE),
    },
    'BOLT-LMM': {
        'postinstallcmds': (['/cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s '], REPLACE),
    },
    'Brunsli' : {
        'buildopts': (" BROTLI_DIR=$EBROOTGENTOO BROTLI_INCLUDE=$EBROOTGENTOO/include", APPEND),
    },
    'Clang': {
        'preconfigopts': ("""pushd %(builddir)s/llvm-%(version)s.src/tools/clang || pushd %(builddir)s/llvm-project-%(version)s.src/clang; """ +
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
    'CMake': {
        'patches': (['cmake-3.14.0_rc3-prefix-dirs.patch'], REPLACE),
        'checksums': (['4c2daf971ea0edd9c2b200e96fca011eb858513252124a7c4daa974cd091c6bc'], APPEND_LIST),
        'preconfigopts': ('sed -i ' +
                          '-e "s|@GENTOO_PORTAGE_GCCLIBDIR@|$EBROOTGENTOO/$(gcc -dumpmachine)/lib/|g" ' +
                          '-e "/@GENTOO_HOST@/d" ' +
                          '-e "s|@GENTOO_PORTAGE_EPREFIX@|${EPREFIX}/|g" ' +
                          'Modules/Platform/{UnixPaths,Darwin}.cmake && ',
                          PREPEND)
    },
    'cram': {
        'multi_deps': ({'Python': ['2.7', '3.6', '3.7', '3.8']}, REPLACE),
        'modluafooter': ('depends_on("python")', REPLACE),
    },
    ('CUDA', '11.8.0'): {
        'version': ('11.8', REPLACE),
    },
    ('CUDA', '12.2.2'): {
        'version': ('12.2', REPLACE),
    },
    'CUDAcore': {
        'postinstallcmds': (['for dir in %(installdir)s/{bin,nvvm}; do /cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path $dir; done',
                             'for dir in %(installdir)s/{c,e,g,nsight,t}*; do /cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path $dir --add_origin; done'],
                            APPEND_LIST),
        'modluafooter': ('''
if cuda_driver_library_available("%(version_major_minor)s") == "compat" then
        depends_on("cudacompat/.%(version_major_minor)s")
end
''', REPLACE)
    },
    'cuDNN': {
        'postinstallcmds': (['/cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s --add_path $EBROOTCUDACORE/lib64 --add_origin'], APPEND_LIST),
    },
    'DB': {
        'configopts': ('--enable-cxx --enable-stl --enable-dbm', APPEND),
    },
    'FFmpeg': {
        'configopts': (' --enable-libvidstab', APPEND),
    },
    'FFTW.MPI': {
        'modaltsoftname': ('fftw-mpi', REPLACE),
    },
    'FreeSurfer': {
        'postinstallcmds': ([
            'upx -d %(installdir)s/bin/*; true',
            '/cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s '], APPEND_LIST),
    },
    ('GCC', '12.3.0'): {
        'version': ('12.3', REPLACE),
    },
    'GObject-Introspection': {
        'multi_deps': ({'Python': ['3.6', '3.7', '3.8']}, REPLACE),
        'builddependencies': ([[('Python', v)] for v in ['2.7', '3.6', '3.7', '3.8'] ], REPLACE),
        'modextrapaths': ({'PYTHONPATH': ['lib/gobject-introspection']}, REPLACE),
        'dependencies': ([], REPLACE),
        'modluafooter': ('depends_on(atleast("python", "3"))', REPLACE),
        'versionsuffix': ('', REPLACE),
    },
    'HDF': {
        'configopts': (' --with-szlib=$EBROOTGENTOO CFLAGS="$CFLAGS -I$EBROOTGENTOO/include/tirpc"', APPEND),
    },
    'HDF5.Serial': {
        'name': ('HDF5', REPLACE),
    },
    'iccifort': {
        'skip_license_file_in_module': (True, REPLACE),
        'license_file': ("/cvmfs/restricted.computecanada.ca/config/licenses/intel/2020/build-node.lic", REPLACE),
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
     for i in $(cd $installdir && find compilers_and_libraries_%(version)s/linux/tbb); do
       if [ -f $installdir/$i ]; then
         mkdir -p $(dirname $publicdir/$i)
         cp -p $installdir/$i $publicdir/$i
       elif [ -L $installdir/$i ]; then
         mkdir -p $(dirname $publicdir/$i)
         cp -a $installdir/$i $publicdir/$i
       fi
     done
     cd $installdir
     for i in $(find . -type l); do
       if [ -f $publicdir/$i ]; then
         cp -a $i $publicdir/$i
       fi
     done
     ln -s compilers_and_libraries_%(version)s/linux/compiler/lib $publicdir/lib
'''], REPLACE),
        "modluafooter": ("""
prepend_path("INTEL_LICENSE_FILE", pathJoin("/cvmfs/restricted.computecanada.ca/config/licenses/intel/2020", os.getenv("CC_CLUSTER") .. ".lic"))

if isloaded("imkl") then
    always_load("imkl/2020.1.217")
end
""", APPEND),
    },
    'impi': intelmpi2021_dict,
    'intel-compilers': {
        'accept_eula': (True, REPLACE),
        #See compiler/2021.2.0/licensing/credist.txt
        'postinstallcmds': (['''
    for compname in icc icpc ifort; do
       echo "--sysroot=$EPREFIX" > %(installdir)s/compiler/%(version)s/linux/bin/intel64/$compname.cfg
    done
    for compname in icx icpx ifx; do
       echo "--sysroot=$EPREFIX" > %(installdir)s/compiler/%(version)s/linux/bin/$compname.cfg
       echo "-L$EBROOTGCCCORE/lib64" >> %(installdir)s/compiler/%(version)s/linux/bin/$compname.cfg
       echo "-Wl,-dynamic-linker=$EPREFIX/lib64/ld-linux-x86-64.so.2" >> %(installdir)s/compiler/%(version)s/linux/bin/$compname.cfg
    done
    echo "#!$EPREFIX/bin/sh" > %(installdir)s/compiler/%(version)s/linux/bin/intel64/dpcpp
    echo "exec %(installdir)s/compiler/%(version)s/linux/bin/dpcpp --sysroot=$EPREFIX -Wl,-dynamic-linker=$EPREFIX/lib64/ld-linux-x86-64.so.2 -L$EBROOTGCCCORE/lib64 \${1+\\"\$@\\"}" >> %(installdir)s/compiler/%(version)s/linux/bin/intel64/dpcpp
    chmod +x %(installdir)s/compiler/%(version)s/linux/bin/intel64/dpcpp
    /cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s
    /cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s/compiler/%(version)s/linux/compiler/lib --add_origin
    for i in %(installdir)s/compiler/%(version)s/linux/lib/*.so; do
       patchelf --set-rpath '$ORIGIN/../lib:$ORIGIN/../compiler/lib/intel64' $i
    done
    patchelf --set-rpath '$ORIGIN:$ORIGIN/../../../../../tbb/%(version)s/lib/intel64/gcc4.8' %(installdir)s/compiler/%(version)s/linux/lib/x64/libintelocl.so
    installdir=%(installdir)s
    publicdir=${installdir/restricted.computecanada.ca/soft.computecanada.ca}
    rm -rf $publicdir
    for i in $(grep -h "compiler.*" $installdir/compiler/%(version)s/licensing/[cf]redist.txt | cut -c 13-); do
       if [ -f $installdir/$i ]; then
         mkdir -p $(dirname $publicdir/$i)
         cp -p $installdir/$i $publicdir/$i
       fi
    done
    for i in $(cd $installdir && find tbb); do
       if [ -f $installdir/$i ]; then
         mkdir -p $(dirname $publicdir/$i)
         cp -p $installdir/$i $publicdir/$i
       fi
    done
    cd $installdir
    for i in $(find . -type l); do
       if [ -f $publicdir/$i ]; then
         cp -a $i $publicdir/$i
       fi
    done
    for i in tbb/%(version)s/lib/intel64/gcc4.8/*; do
       if [ -L $i ]; then
         cp -a $i $publicdir/$i
       fi
    done
    ln -s %(version)s $publicdir/compiler/latest
'''], REPLACE),
        "modluafooter": ("""
if isloaded("imkl") then
    always_load("imkl/%(version_major_minor)s")
end
""", APPEND),
    },
    'ispc': {
        'sources': (['ispc-v%(version)s-linux-oneapi.tar.gz'], REPLACE),
        'postinstallcmds': (['/cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s'], REPLACE),
    },
    'itac': {
        'postinstallcmds': (['chmod -R u+w %(installdir)s && /cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s'], REPLACE),
    },
    'InterProScan': {
        'sanity_check_commands': (['%(installdir)s/bin/prosite/pfsearchV3 -h'], APPEND_LIST),
    },
    'IQ-TREE': {
        'toolchainopts': ({}, REPLACE),
        'configopts': ('-DIQTREE_FLAGS=omp -DUSE_LSD2=ON -DTERRAPHAST_ARCH_NATIVE=OFF', REPLACE),
        'sanity_check_paths': ({'files': ['bin/iqtree2'], 'dirs': []}, REPLACE),
    },
    'iq-tree-mpi': {
        'configopts': ('-DIQTREE_FLAGS=mpi -DUSE_LSD2=ON -DTERRAPHAST_ARCH_NATIVE=OFF', REPLACE),
        'sanity_check_paths': ({'files': ['bin/iqtree2-mpi'], 'dirs': []}, REPLACE),
    },
    'Java': {
        'postinstallcmds': (['/cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s'], REPLACE),
        'modluafooter': ('setenv("JAVA_TOOL_OPTIONS", "-Xmx2g")', REPLACE),
    },
    ('libfabric', '1.18.0'): {
        'builddependencies': ([('opa-psm2', '12.0.1'), ('GDRCopy', '2.3.1'), ('CUDAcore', '12.2.2')], REPLACE),
        'configopts': ('--enable-cuda-dlopen --enable-gdrcopy-dlopen ', PREPEND),
        'patches': (['libfabric-1.18.0_eliminate-cudart-use.patch'], APPEND_LIST),
        'checksums': ('71e2e1bbbbcebae20d1ffc3255598949e06fb1bc1d3e5c040244df3f69db00fa', APPEND_LIST),
    },
    'libgeotiff': {
        'configopts': (' --with-libtiff=$EBROOTGENTOO --with-zlib=$EBROOTGENTOO --with-jpeg=$EBROOTGENTOO', APPEND),
    },
    'libxsmm': {
        'skipsteps': ([], REPLACE),
        'preconfigopts': ('#', REPLACE),
        'installopts': ({'sse3': ' SSE=3', 'avx': ' AVX=1', 'avx2': ' AVX=2', 'avx512': ' AVX=3'}
                        [os.getenv('RSNT_ARCH')], APPEND),
    },
    'LLDB': {
        'dependencies': ([], REPLACE),
    },
    ('MATLAB', '2020a'): {
        'modluafooter': ("""require("SitePackage")
local found = find_and_define_license_file("MLM_LICENSE_FILE","matlab")
if (not found) then
        local error_message = [[
        We did not find a suitable license for Matlab. If you have access to one, you can create the file $HOME/.licenses/matlab.lic with the license information. If you think you should have access to one as    part of your institution, please write to support@computecanada.ca so that we can configure it.

        Nous n'avons pas trouve de licence utilisable pour Matlab. Si vous avez acces a une licence de Matlab, vous pouvez creer le fichier $HOME/.licenses/matlab.lic avec l'information de la licence. Si vous    pensez que vous devriez automatiquement avoir acces a une licence via votre institution, veuillez ecrire a support@calculcanada.ca pour que nous puissions la configurer.
        ]]
        LmodError(error_message)
end
setenv("MATLAB_LOG_DIR","/tmp")""", REPLACE),
        'dependencies': ([('Java', '13')], REPLACE),
        'postinstallcmds': ([
        'chmod -R u+w %(installdir)s ',
        # install the python engines with both python 2.7, 3.6, 3.7
        'module load python/2.7 && pushd %(installdir)s/extern/engines/python && python setup.py install --prefix=%(installdir)s/extern/engines/python && popd ',
        'module load python/3.6 && pushd %(installdir)s/extern/engines/python && python setup.py install --prefix=%(installdir)s/extern/engines/python && popd ',
        'module load python/3.7 && pushd %(installdir)s/extern/engines/python && python setup.py install --prefix=%(installdir)s/extern/engines/python && popd ',
        "find %(installdir)s/sys/os/glnxa64 -name 'libstdc++.so*' -exec mv {} {}.bak \;",
        "find %(installdir)s/sys/os/glnxa64 -name 'libgcc_s.so*' -exec mv {} {}.bak \;",
        "find %(installdir)s/sys/os/glnxa64 -name 'libgfortran.so*' -exec mv {} {}.bak \;",
        "find %(installdir)s/sys/os/glnxa64 -name 'libquadmath.so*' -exec mv {} {}.bak \;",
        '/cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s --add_origin',
        '/cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s/extern/engines/python --add_path %(installdir)s/bin/glnxa64 --add_origin --any_interpreter '
], REPLACE),
        'modextrapaths': ({'EBPYTHONPREFIXES': ['extern/engines/python']}, REPLACE),
    },
    'mpi4py': {
        'builddependencies': ([[('Python', v), ('Cython', '0.29.36')] for v in ['3.10', '3.11'] ], REPLACE),
        'dependencies': ([], REPLACE),
        'multi_deps': ({'Python': ['3.10', '3.11'] }, REPLACE),
    },
    'Nextflow': {
        'postinstallcmds': (['sed -i -e "s/cli=(\$(/cli=(\$(export NFX_OPTS=\$JAVA_TOOL_OPTIONS; unset JAVA_TOOL_OPTIONS; /g" %(installdir)s/bin/nextflow'], APPEND_LIST),
    },
    'NextGenMap': {
        'preconfigopts': (" sed -i '/include_directories(.*zlib/d' ../NextGenMap-%(version)s/CMakeLists.txt && ", APPEND),
    },
    'nodejs': {
        'postinstallcmds': (["export PATH=%(installdir)s/bin:$PATH; %(installdir)s/bin/npm install --global yarn"], APPEND_LIST),
    },
    ('NCCL', '2.18.3'): {
        'checksums': (['6477d83c9edbb34a0ebce6d751a1b32962bc6415d75d04972b676c6894ceaef9'], REPLACE),
    },
    'NVHPC': {
        'postinstallcmds': (['''
        installdir=%(installdir)s/Linux_x86_64/%(version)s
        /cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path $installdir
        sed -i "s@\(set LDSO=.*\);@\\1 --sysroot=$EPREFIX;@" $installdir/compilers/bin/localrc
        echo "set DEFLIBDIR=$EBROOTGENTOO/lib64;" >> $installdir/compilers/bin/localrc
        echo "set DEFSTDOBJDIR=$EBROOTGENTOO/lib64;" >> $installdir/compilers/bin/localrc
        echo "set NORPATH=YES;" >> $installdir/compilers/bin/localrc
        publicdir=${installdir/restricted.computecanada.ca/soft.computecanada.ca}
        rm -rf $publicdir
        mkdir -p $publicdir
        cp -a $installdir/REDIST/* $publicdir
        for i in $(find $publicdir); do
            if [[ $(readlink $i) == ../../../* ]]; then
                rm $i
                cp -p ${i/soft.computecanada.ca/restricted.computecanada.ca} $i
            fi
        done
        '''], REPLACE),
    },
    ("OpenFOAM", "11"): {
        'modluafooter': ("""if convertToCanonical(LmodVersion()) >= convertToCanonical("8.6") then
        source_sh("bash", root .. "/OpenFOAM-{version}/etc/bashrc")
end""".format(version="11"), REPLACE),
        'patches': (['OpenFOAM-11-cleanup-cc.patch'], APPEND_LIST),
        'checksums': ('56a98703a1022d5e75f7b1f7cd4592bc79ba93c1dd53d3e52316726797430c33', APPEND_LIST),
    },
    ("OpenFOAM", "v2306"): {
        'modluafooter': ("""if convertToCanonical(LmodVersion()) >= convertToCanonical("8.6") then
        source_sh("bash", root .. "/OpenFOAM-{version}/etc/bashrc")
end""".format(version="v2306"), REPLACE),
        'prebuildopts': ('MPFR_ARCH_PATH=$EBROOTGENTOO ', APPEND),
    },
    "OpenMPI": {
        # local customizations for OpenMPI
        'builddependencies': ([('opa-psm2', '12.0.1')], REPLACE),
        'configopts': ('--enable-shared --with-verbs ' +
                    '--with-hwloc=external '  + # hwloc support
                    '--with-libevent=external ' + # libevent from Gentoo
                    '--without-usnic ' + # No usnic-via-libfabric
                    # rpath is already done by ld wrapper
                    '--disable-wrapper-runpath --disable-wrapper-rpath ' +
                    '--with-munge ' + #enable Munge in PMIx
                    '--with-slurm --with-pmi=/opt/software/slurm ' +
                    '--enable-mpi-cxx ' +
                    '--disable-show-load-errors-by-default ' +
                    '--enable-mpi1-compatibility ' +
                    # enumerate all mca's that should be compiled as plugins
                    # (only those that link to system-specific
                    # libraries (lustre, fabric, and scheduler)
                    '--enable-mca-dso=common-ofi,common-ucx,common-verbs,event-external,' +
                    'atomic-ucx,btl-ofi,btl-openib,btl-uct,' +
                    'coll-ucc,ess-tm,fs-lustre,mtl-ofi,mtl-psm,mtl-psm2,osc-ucx,' +
                    'plm-tm,pmix-ext3x,pmix-s1,pmix-s2,pml-ucx,pnet-opa,psec-munge,' +
                    'ras-tm,scoll-ucc,spml-ucx,sshmem-ucx,hwloc-external ',
                    PREPEND),
        'postinstallcmds': (['rm %(installdir)s/lib/*.la %(installdir)s/lib/*/*.la',
                             'for i in %(installdir)s/lib/openmpi/mca_pmix_s[12].so; '
                             'do patchelf --set-rpath '
                             '$(patchelf --print-rpath $i):/opt/software/slurm/lib:/opt/software/slurm/lib64:/opt/slurm/lib64 $i;'
                             'done'], REPLACE),
        'modluafooter': (mpi_modluafooter % 'openmpi', REPLACE),
    },
    "PMIx": {
        # local customizations for PMIx
        'configopts': ('--with-munge ' + #enable Munge in PMIx
                    '--disable-show-load-errors-by-default ' +
                    # enumerate all mca's that should be compiled as plugins
                    '--enable-mca-dso=psec-munge',
                    PREPEND),
        'postinstallcmds': (['rm %(installdir)s/lib/*.la %(installdir)s/lib/*/*.la'],
                            REPLACE),
    },
    'Python': {
        'modextrapaths': ({'PYTHONPATH': ['/cvmfs/soft.computecanada.ca/easybuild/python/site-packages']}, REPLACE),
        'ebpythonprefixes': (False, REPLACE),  # disable upstream's version of sitecustomize.py for ebpythonprefixes
        'allow_prepend_abs_path': (True, REPLACE),
        'installopts': (' && /cvmfs/soft.computecanada.ca/easybuild/bin/setrpaths.sh --path %(installdir)s --add_path %(installdir)s/lib --any_interpreter', APPEND),
        'builddependencies': (('Rust', '1.52.1'), DROP_FROM_LIST),
        # replace pip 21.1.1 with pip 20.0.2
        'exts_list': ([(('pip', '21.1.1', { 'checksums': ['51ad01ddcd8de923533b01a870e7b987c2eb4d83b50b89e1bf102723ff9fed8b'],}),
                       ('pip', '20.0.2', {'checksums': ['7db0c8ea4c7ea51c8049640e8e6e7fde949de672bfa4949920675563a5a6967f'],})),
                       (('virtualenv', '20.4.6', {'checksums': ['72cf267afc04bf9c86ec932329b7e94db6a0331ae9847576daaa7ca3c86b29a4']}),
                        ('virtualenv', '20.0.18', {'checksums': ['ac53ade75ca189bc97b6c1d9ec0f1a50efe33cbf178ae09452dcd9fd309013c1']}))
                       ], REPLACE_IN_LIST),
    },
    'Qt5': {
        'modaltsoftname': ('qt', REPLACE),
    },
    'ROOT': {
        # Cling needs to know about different sysroot
        'configopts': ("-DDEFAULT_SYSROOT=$EPREFIX", PREPEND),
    },
    'Rust': {
        'prebuildopts': ("sed -i 's/\\(ninja.*=.*\\)false/\\1true/' config.toml && export EASYBUILD_SYSROOT=$EPREFIX && ", PREPEND),
    },
    ('SCOTCH', '6.1.2', '-no-thread'): {
        'modaltsoftname': ('scotch-no-thread', REPLACE),
    },
    ('SCOTCH', '7.0.3', '-no-thread'): {
        'modaltsoftname': ('scotch-no-thread', REPLACE),
    },
    'Togl': {
            'patches': ('Togl-2.0_configure.patch', DROP_FROM_LIST),
            'checksums': ('da97f36b60cd107444cd92453809135b14dc1e8775146b3ba0731da8002e6f9f', DROP_FROM_LIST),
    },
    'tbb': {
        'postinstallcmds': (['chmod -R u-w %(installdir)s/cmake || chmod -R u-w %(installdir)s/lib64/cmake'], REPLACE),
    },
    'UCX': {
        # local customizations for UCX
        'configopts': ("--with-rdmacm=$EBROOTGENTOO --with-verbs=$EBROOTGENTOO --with-knem=$EBROOTGENTOO " +
                       {'sse3': '--without-avx --without-sse41 --without-sse42 '}.get(os.getenv('RSNT_ARCH'), ''),
                       PREPEND)
    },
    'Valgrind': {
        # tell correct location of debuginfo files
        'configopts': (' && sed -i "s@/usr/lib/debug@$EPREFIX/usr/lib/debug@g" coregrind/m_debuginfo/readelf.c', APPEND),
        'modaltsoftname': ('valgrind-mpi', REPLACE),
        'versionsuffix': ('-mpi', REPLACE),
    },
    ('Wannier90', '2.0.1.1', '-abinit'): {
        'modaltsoftname': ('wannier90-abinit', REPLACE),
    },
}



# modules with both -mpi and no-mpi varieties
mpi_modaltsoftname = ['hdf5', 'netcdf-c++4', 'netcdf-c++', 'netcdf-fortran', 'netcdf', 'iq-tree', 'vtk', 'libgridxc', 'etsf_io', 'valgrind']
modaltsoftnames = {
    "iccifort": "intel",
    "intel-compilers": "intel",
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
    matching_keys = get_matching_keys_from_ec(ec, opts_changes)
    for key in matching_keys:
        for opt in ('modluafooter', 'allow_prepend_abs_path', 'modextrapaths', 'ebpythonprefixes'):
            if opt in opts_changes[key]:
                update_opts(ec, opts_changes[key][opt][0], opt, opts_changes[key][opt][1])

    moduleclass = ec.get('moduleclass','')
    year = os.environ['EBVERSIONGENTOO']
    name = ec['name'].lower()
    if moduleclass == 'compiler' and not name in ('gcccore', 'llvm', 'clang', 'fpc', 'dpc++', 'ispc'):
        if name in ['iccifort', 'intel-compilers']:
            name = 'intel'
        comp = os.path.join('Compiler', name + ec['version'][:ec['version'].find('.')])
        ec['modluafooter'] += (compiler_modluafooter.format(year=year,sub_path=comp) + 'family("compiler")\n')
    if ec['name'] == 'CUDAcore':
        comp = os.path.join('CUDA', 'gcccore', 'cuda' + '.'.join(ec['version'].split('.')[:2]))
        ec['modluafooter'] += compiler_modluafooter.format(year=year, sub_path=comp)


def add_dependencies(ec, keyword):
    matching_keys = get_matching_keys_from_ec(ec, opts_changes)
    for key in matching_keys:
        if keyword in opts_changes[key]:
            update_opts(ec, opts_changes[key][keyword][0], keyword, opts_changes[key][keyword][1])

def drop_dependencies(ec, param):
    # dictionary in format <name>:<version under which to drop>
    to_drop = {
            'CMake': '3.18.4',
            'ICU': 'ALL',
            'libxslt': 'ALL',
            'libzip': 'ALL',
            'Meson': 'ALL',
            'Ninja': 'ALL',
            'PyQt5': 'ALL',
            'SQLite': '3.42.0',
            'pybind11': 'ALL',
            'git': 'ALL',
            'CUDA': 'ALL',
    }
    # iterate over a copy
    for dep in ec[param][:]:
        if isinstance(dep, list):
            dep_copy = dep[:]
            for d in dep_copy:
                name, version = d[0], d[1]
                if name in to_drop and name != 'CUDA':
                    if to_drop[name] == 'ALL' or LooseVersion(version) < LooseVersion(to_drop[name]):
                        print("%s: Dropped %s, %s from %s" % (ec.filename(), name, version, param))
                        dep.remove(d)

        else:
            dep_list = list(dep)
            if dep_list[0] == ec.name:
                continue
            if dep_list[0] in to_drop:
                if to_drop[dep_list[0]] == 'ALL' or LooseVersion(dep_list[1]) < LooseVersion(to_drop[dep_list[0]]):
                    # special case: drop CUDA dep for easyconfigs with CUDA versionsuffix (we use toolchains instead)
                    if dep_list[0] == 'CUDA' and not ec['toolchain']['name'].endswith('cuda'):
                        continue
                    print("%s: Dropped %s, %s from %s" % (ec.filename(), dep_list[0],dep_list[1],param))
                    ec[param].remove(dep)


def is_filtered_ec(ec):
    filter_spec = ec.parse_filter_deps()
    software_spec = {'name': ec.name, 'version': ec.version}
    return ec.dep_is_filtered(software_spec, filter_spec)

def parse_hook(ec, *args, **kwargs):
    """Example parse hook to inject a patch file for a fictive software package named 'Example'."""
    if is_filtered_ec(ec):
        print("ERROR, software %s/%s is filtered. Please contact a RSNT software admin before installing" % (ec.name, ec.version))
        exit(1)

    disable_use_mpi_for_non_mpi_toolchains(ec)

    # automatic --try-toolchain for common cases:
    if ec['toolchain'] == {'name': 'GCCcore', 'version': '12.3.0'}:
        if ec['versionsuffix'] == '-CUDA-%(cudaver)s':
            ec['toolchain'] = {'name': 'gcccorecuda', 'version': '2023a'}
            ec['versionsuffix'] = ''
        else:
            ec['toolchain'] = {'name': 'GCCcore', 'version': '12.3-gentoo'}
    elif ec['toolchain'] == {'name': 'intel-compilers', 'version': '2023.1.0'}:
        ec['toolchain']['version'] = '2023.2.1'

    # Use ifx by default as Fortran compiler for Intel toolchains.
    # Adapt optarch if oneapi compilers are used.
    toolchain, _ = search_toolchain(ec['toolchain']['name'])
    if toolchain.COMPILER_FAMILY == 'Intel':
        if ec['toolchainopts'] is None:
            ec['toolchainopts'] = {}
        tcopts = ec['toolchainopts']
        if tcopts.get('optarch', True) == True:
            optarch = '-' + build_option('optarch')['Intel']
            optarch_new = optarch.replace('core-avx2', 'x86-64-v3').replace('skylake-avx512', 'x86-64-v4')
            if (tcopts.get('oneapi') or (tcopts.get('oneapi_c_cxx', True) and tcopts.get('oneapi_fortran'))):
                tcopts['optarch'] = optarch_new
            elif tcopts.get('oneapi_c_cxx', True):
                # use new optarch flags for C/C++ only (default)
                for key in 'extra_cflags', 'extra_cxxflags':
                    tcopts[key] = optarch_new + ' ' + tcopts.get(key, '')
                for key in 'extra_fflags', 'extra_fcflags', 'extra_f90flags':
                    tcopts[key] = optarch + ' ' + tcopts.get(key, '')
                tcopts['optarch'] = ''

    modify_dependencies(ec, 'dependencies', new_version_mapping_2023a)
    modify_dependencies(ec, 'builddependencies', new_version_mapping_2023a)
    drop_dependencies(ec, 'dependencies')
    drop_dependencies(ec, 'builddependencies')
    set_modaltsoftname(ec)
    modify_all_opts(ec, opts_changes, opts_to_change=PARSE_OPTS)

    # always disable multi_deps_load_default when multi_deps is used
    multi_deps = ec.get('multi_deps', None)
    if multi_deps:
        ec['multi_deps_load_default'] = False

        if 'Python' in multi_deps:
            # ensure PythonPackage that build with multi_deps have a corresponding modluafooter
            # don't overwrite the existing one if there is one in the recipe
            if ec.get('easyblock', None) in ['PythonPackage', 'PythonBundle']:
                # get lowest and highest supported versions
                versions = sorted([LooseVersion(x) for x in multi_deps['Python']])
                lowest = str(versions[0])
                highest = str(versions[-1])

                # we need to get the next subversion higher than highest for Lmod syntax
                highest_major, highest_minor = str(highest).split('.')[:2]
                highest_plus = '.'.join([highest_major, str(int(highest_minor)+1)])

                footer_str = """if convertToCanonical(LmodVersion()) >= convertToCanonical("8.2.9") then
        depends_on(between("python",'{lowest}<','<{highest_plus}'))
end""".format(lowest=lowest, highest_plus=highest_plus)
                modluafooter = ec.get('modluafooter', "")
                # don't add anything, it is already there
                if 'depends_on("python")' in modluafooter:
                    print("WARNING, this is a multi_deps module. modluafooter should not contain depends_on('python')): %s" % modluafooter)
                elif footer_str in modluafooter:
                    pass
                elif 'depends_on(between(' in ec.get('modluafooter', None):
                    print("Error, incorrect modluafooter for specified versions of python: %s" % ec.get('modluafooter', None))
                    print("Should be absent or should contain:%s" % footer_str)
                    exit(1)
                else:
                    print("%s: Adding to modluafooter: %s" % (ec.filename(), footer_str))
                    ec['modluafooter'] += "\n" + footer_str + "\n"

            # add sanity_checks if there are not already there
            sanity_check_paths = ec.get('sanity_check_paths', {})
            if ec.name not in ['Boost']:
                if not 'dirs' in sanity_check_paths:
                    sanity_check_paths['dirs'] = []
                if not 'files' in sanity_check_paths:
                    sanity_check_paths['files'] = []

                site_packages_path = 'lib/python%(pyshortver)s/site-packages'
                if not site_packages_path in sanity_check_paths['dirs']:
                    sanity_check_paths['dirs'] += [site_packages_path]
                    print("%s: Adding %s to sanity_check_paths['dir']" % (ec.filename(), site_packages_path))
                    print(str(ec.get('sanity_check_paths', None)))

                # for non-generic EasyBlock, the EasyBlock might modify the sanity_check_paths, so we consider
                # our changes as an enhancement
                if not ec.get('easyblock', None):
                    ec['enhance_sanity_check'] = True


    # hide toolchains
    if ec.get('moduleclass','') == 'toolchain' or ec['name'] == 'GCCcore' or ec['name'] == 'CUDAcore':
        ec['hidden'] = True

def python_fetchhook(ec):
    # don't do anything for "default" version
    if ec['version'] == "default":
        return
    # keep only specific extensions
    python_extensions_to_keep = ['setuptools', 'pip', 'wheel', 'virtualenv', 'appdirs', 'distlib', 'filelock',
                                 'six', 'setuptools_scm']
    ver = LooseVersion(ec['version'])
    # python 3.10, 3.11
    if ver >= LooseVersion('3.10') and ver <= LooseVersion('3.12'):
        python_extensions_to_keep += ['tomli', "flit-core", "flit_core", "packaging", "pyparsing", "platformdirs", "hatchling", "pathspec", "pluggy", "hatch_vcs", "typing_extensions", "editables", "trove-classifiers"]

    new_ext_list = [ext for ext in ec['exts_list'] if ext[0] in python_extensions_to_keep]
    ec['exts_list'] = new_ext_list


def pre_configure_hook(self, *args, **kwargs):
    "Modify configopts (here is more efficient than parse_hook since only called once)"
    orig_enable_templating = self.cfg.enable_templating
    self.cfg.enable_templating = False

    modify_all_opts(self.cfg, opts_changes, opts_to_skip=PARSE_OPTS + ['exts_list',
                                                                       'postinstallcmds',
                                                                       'modluafooter',
                                                                       'ebpythonprefixes',
                                                                       'allow_prepend_abs_path',
                                                                       'modextrapaths'])

    # additional changes for CMakeMake EasyBlocks
    ec = self.cfg
    if ec.easyblock is None or isinstance(ec.easyblock, str):
        c = get_easyblock_class(ec.easyblock, name=ec.name)
    elif isinstance(ec.easyblock, type):
        c = ec.easyblock
    if c == CMakeMake or issubclass(c,CMakeMake):
        # ensure CMake is in the build dependencies or dependencies
        if 'CMake' not in str(self.cfg['dependencies']) + str(self.cfg['builddependencies']):
            print("Error, for CMakeMake recipes, you should have a dependency on CMake")
            exit(1)
        # skip for those
        if (ec['name'],ec['version']) in [('ROOT','5.34.36'), ('mariadb', '10.4.11')]:
            pass
        else:
            update_opts(ec, ' -DCMAKE_SKIP_INSTALL_RPATH=ON ', 'configopts', PREPEND)
        # disable XHOST
        update_opts(ec, ' -DENABLE_XHOST=OFF ', 'configopts', PREPEND)
        # use verbose makefile to get the command lines that are executed
        update_opts(ec, ' -DCMAKE_VERBOSE_MAKEFILE:BOOL=ON ', 'configopts', PREPEND)

    # additional changes for MesonNinja EasyBlocks
    if (c == MesonNinja or issubclass(c,MesonNinja)) and c != CMakeNinja:
        update_opts(ec, False, 'fail_on_missing_ninja_meson_dep', REPLACE)

    self.cfg.enable_templating = orig_enable_templating

def pre_fetch_hook(self, *args, **kwargs):
    "Modify extension list (here is more efficient than parse_hook since only called once)"
    orig_enable_templating = self.cfg.enable_templating
    self.cfg.enable_templating = False
    modify_all_opts(self.cfg, opts_changes, opts_to_change=['exts_list'])
    # special extensions hook for Python
    if self.cfg['name'].lower() == 'python':
        python_fetchhook(self.cfg)
    self.cfg.enable_templating = orig_enable_templating

def pre_postproc_hook(self, *args, **kwargs):
    "Modify postinstallcmds (here is more efficient than parse_hook since only called once)"
    orig_enable_templating = self.cfg.enable_templating
    self.cfg.enable_templating = False
    modify_all_opts(self.cfg, opts_changes, opts_to_change=['postinstallcmds'])
    self.cfg.enable_templating = orig_enable_templating

def pre_module_hook(self, *args, **kwargs):
    "Modify module footer (here is more efficient than parse_hook since only called once)"
    orig_enable_templating = self.cfg.enable_templating
    self.cfg.enable_templating = False
    set_modluafooter(self.cfg)
    # special extensions hook for Python with --module-only
    if self.cfg['name'].lower() == 'python':
        python_fetchhook(self.cfg)
    self.cfg.enable_templating = orig_enable_templating

def post_module_hook(self, *args, **kwargs):
    "Modify GCCcore toolchain to system toolchain for ebfiles_repo only"
    # So we get name-version.eb there, but the toolchain inside does not change
    toolchain = self.cfg.get('toolchain')
    if toolchain and toolchain['name'] == 'GCCcore':
        self.cfg['toolchain'] = EASYCONFIG_CONSTANTS['SYSTEM'][0]

def pre_prepare_hook(self, *args, **kwargs):
    packages_in_gentoo = ["EBROOTLIBXML2", "EBROOTLIBJPEGMINTURBO", "EBROOTLIBPNG", "EBROOTLIBTIFF",
                          "EBROOTLIBGLU", "EBROOTMESA", "EBROOTFLTK", "EBROOTTCL", "EBROOTTK", "EBROOTBZIP2",
                          "EBROOTZSTD", "EBROOTFREETYPE", "EBROOTGLIB", "EBROOTLIBXMLPLUSPLUS",
                          "EBROOTSQLITE3", "EBROOTPKGMINCONFIG", "EBROOTMESON", "EBROOTGPERFTOOLS"]
    ebrootgentoo = os.environ["EBROOTGENTOO"]
    for package in packages_in_gentoo:
        setvar(package, ebrootgentoo)

    # this should only be set if external EB PMIx is used in Open MPI
    if self.cfg['name'] == 'OpenMPI' and "PMIx" in {dep["name"] for dep in self.cfg['dependencies']}:
        setvar("EBROOTLIBEVENT", ebrootgentoo)

    # this can not be set in general because it causes issues with Python. It however avoids having to patch
    # OpenFOAM locally to find readline in gentoo
    if self.cfg['name'] == 'OpenFOAM':
        setvar("EBROOTLIBREADLINE", ebrootgentoo)

    setvar("EBVERSIONTCL", "8.6")
    setvar("EBVERSIONTK", "8.6")
    setvar("EBVERSIONMESON", "1.1.1")
    setvar("EBVERSIONGPERFTOOLS", "2.9.1")

def post_prepare_hook(self, *args, **kwargs):
    # we need to define variables such as EBROOTHDF5SERIAL even though we don't use this naming scheme
    serial_to_no_qualifier = ["HDF5", "BOOST", "NETCDF"]
    for pkg in serial_to_no_qualifier:
        to_check = "EBROOT" + pkg
        to_set = "EBROOT" + pkg + "SERIAL"
        if to_check in os.environ:
            setvar(to_set, os.environ[to_check])

def end_hook():
    user = os.getenv("USER")
    # only do this if we are "ebuser"
    if True: #user != "ebuser":
        return

    arch = os.getenv("RSNT_ARCH")

    modulepath = '/cvmfs/soft.computecanada.ca/custom/modules'
    index_dir = '/cvmfs/soft.computecanada.ca/custom/mii/data'
    mii = "/cvmfs/soft.computecanada.ca/easybuild/software/2020/Core/mii/1.1.1/bin/mii"
    final_index_file = os.path.join(index_dir, arch)
    exclude_modnames = ",".join(("gentoo","nixpkgs"))

    unique_filename = arch + "_" + str(uuid.uuid4())
    index_file = os.path.join(index_dir,unique_filename)
    cmd = "MII_INDEX_FILE=%s %s build -m %s -n %s" % (index_file, mii, modulepath, exclude_modnames)
    print("Generating the Mii index with cmd:%s" % cmd )
    (out, _) = run_cmd(cmd, log_all=True, simple=False, log_output=True)

    # create a new symlink
    new_symlink_path = os.path.join(index_dir, arch + str(uuid.uuid4()))
    os.symlink(index_file, new_symlink_path)

    # if the path exists and is a link, remove the target of the link
    current_target = None
    if os.path.islink(final_index_file):
        # get the path of the current index
        current_target = os.readlink(final_index_file)

    # rename the new symlink, overwriting the old symlink or file
    shutil.move(new_symlink_path, final_index_file)

    if current_target:
        # remove the old target
        os.remove(current_target)
