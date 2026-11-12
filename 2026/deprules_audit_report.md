# Audit of DepRules and Dependency Packages for the 2026 Software Environment

## 1. Executive Summary

This report provides a comprehensive audit of dependency transformations (`DepRule` entries in `2026/cc_hooks.py`) for the new 2026 software environment (`/Users/mboisson/git/easybuild-easyconfigs-installed-avx2/2026`), referenced against historical dependency usage across the 2023 (`/Users/mboisson/git/easybuild-easyconfigs-installed-avx2/2023`) and 2020 environments.

### Key Takeaways
1. **Direct Hook Omissions:** `GSL` and `PLUMED`, which were actively mapped in `2023/cc_hooks.py`, are installed in the 2026 environment but have **no rule** in `dep_transforms_2026`. Additionally, `JasPer` (mapped in 2020) is installed with `GCCcore-15.3.0` but lacks an upgrade rule.
2. **Installed Packages Missing Rules:** Over 20 packages installed in 2026 are frequently depended upon by upstream easyconfigs (e.g., `SciPy-Stack`, `mpi4py`, `SWIG`, `tbb`, `libxc`, `HTSlib`, `protobuf`, `ant`), but have not been added to `dep_transforms_2026`. Upstream easyconfigs declaring older versions or non-GCCcore toolchains for these packages will fail to resolve unless rules are registered.
3. **High-Impact Missing Dependencies Not Yet Installed in 2026:** Several critical software packages that unblock large dependency graphs (such as `VTK`, `ELPA`, `Wannier90`, `ecCodes`, `sparsehash`, and `ParMETIS`) have not yet been built for the 2026 environment. Their latest upstream versions have been verified via web search to guide upcoming builds.

---

## 2. Direct Omissions from Historical Hook Mappings

The following packages were explicitly upgraded in `2023/cc_hooks.py` (or `2020/cc_hooks.py`) and are present in the 2026 software environment, but were not carried forward into `dep_transforms_2026`:

| Package | 2023 Dependents | 2023/2020 Rule in `cc_hooks.py` | 2026 Installed Version & Toolchain | Recommended `DepRule` |
| :--- | :--- | :--- | :--- | :--- |
| **`GSL`** | **66** (54 run, 12 build) | `'GSL': ('2.7', COMPILERS_2023a)` | `2.8` (`GCC-15.3.0`, `intel-compilers-2026.1.0`) | `DepRule(new_version='2.8', match_toolchain=COMPILERS_2026)` |
| **`PLUMED`** | **19** (14 run, 5 build) | `('PLUMED', '2.6.0'): ('2.6.2', cOMKL_2023a)` | `2.10.2` (`gofb-2026`, `gofbc-2026`) | `DepRule(new_version='2.10.2', match_toolchain=[('gofb', '2026'), ('gofbc', '2026')])` |
| **`JasPer`** | **29** (11 run, 18 build) | `'JasPer': ('2.0.16', SYSTEM)` *(2020)* | `4.2.9` (`GCCcore-15.3.0`) | `DepRule(new_version='4.2.9', match_toolchain=GCCCORE153)` |

### Analysis:
* **GSL (GNU Scientific Library):** One of the most common dependencies across scientific computing (bioinformatics, physical simulation, numerical algorithms). In 2026, it is installed with `GCC-15.3.0` and `intel-compilers-2026.1.0`. Adding this rule is critical to prevent recipes depending on `GSL` 2.6 or 2.7 from failing.
* **PLUMED:** Required by molecular dynamics packages including GROMACS, CP2K, LAMMPS, and Amber. In 2026, it is installed under toolchains `gofb-2026` and `gofbc-2026`.
* **JasPer:** In 2026, `JasPer` is built as an explicit module with `GCCcore-15.3.0`. Upstream easyconfigs often use older versions or the `system` toolchain.

---

## 3. High-Frequency Dependencies Installed in 2026 Lacking DepRules

The following software packages are installed in the 2026 environment and were frequently used as dependencies in 2023/2020, but have no entries in `dep_transforms_2026` and are not in `filter-deps`:

### A. Scientific & Numerical Computing

| Package | 2023 Dep Count | 2026 Installed EasyConfig | Description & Justification | Recommended `DepRule` |
| :--- | :--- | :--- | :--- | :--- |
| **`SciPy-Stack`** | 81 (54 run, 27 build) | `SciPy-Stack-2026b-GCCcore-15.3.0.eb` | While `SciPy-bundle` is transformed, recipes directly requesting `('SciPy-Stack', '2023b')` fail to resolve without an explicit rule for `SciPy-Stack`. | `DepRule(new_version='2026b', new_suffix='', new_toolchain=None)` |
| **`mpi4py`** | 48 (14 run, 34 build) | `mpi4py-4.1.2-gompi-2026.eb`<br>`mpi4py-4.1.2-iompi-2026.eb` | Upstream recipes specify `('mpi4py', '3.1.4')`, `('mpi4py', '4.0.0')`, or `('mpi4py', '4.1.0')`. Needs normalization under `cOMPI_2026`. | `DepRule(new_version='4.1.2', match_toolchain=cOMPI_2026)` |
| **`libxc`** | 23 (20 run, 3 build) | `libxc-7.1.2-GCC-15.3.0.eb` | Core exchange-correlation library for DFT codes (CP2K, Octopus, Quantum ESPRESSO, GPAW, PySCF). | `DepRule(new_version='7.1.2', match_toolchain=GCC153)` |
| **`arpack-ng`** | 16 (12 run, 4 build) | `arpack-ng-3.9.1-gccflexiblas-2026.eb` | Eigensolver library used by SciPy, Octave, Armadillo, and structural solvers. | `DepRule(new_version='3.9.1', match_toolchain=('gccflexiblas', '2026'))` |
| **`PnetCDF`** | 11 (11 run, 0 build) | `PnetCDF-1.15.1-gompi-2026.eb` | Parallel NetCDF library used by climate, weather, and ocean models (WRF, MPAS). | `DepRule(new_version='1.15.1', match_toolchain=[('gompi', '2026')])` |

### B. Core Development & Build Dependencies

| Package | 2023 Dep Count | 2026 Installed EasyConfig | Description & Justification | Recommended `DepRule` |
| :--- | :--- | :--- | :--- | :--- |
| **`SWIG`** | 31 (0 run, 31 build) | `SWIG-4.4.1-GCCcore-15.3.0.eb` | Universal interface generator. Unlike 2020/2017, SWIG is not in 2026 `filter-deps`. | `DepRule(new_version='4.4.1', match_toolchain=GCCCORE153)` |
| **`tbb`** | 28 (14 run, 14 build) | `tbb-2022.3.0-GCCcore-15.3.0.eb` | Intel oneTBB. Required by Bowtie2, OpenCV, OpenImageIO, OSPray, and rendering/vision tools. | `DepRule(new_version='2022.3.0', match_toolchain=GCCCORE153)` |
| **`protobuf`** | 26 (7 run, 19 build) | `protobuf-36.1-GCCcore-15.3.0.eb` | Google Protocol Buffers. Required by TensorFlow, PyTorch, Arrow, ONNX, and gRPC. | `DepRule(new_version='36.1', match_toolchain=GCCCORE153)` |
| **`ant`** | 22 (0 run, 22 build) | `ant-1.10.18.eb` | Java build tool required by Java-based scientific packages. | `DepRule(new_version='1.10.18', match_toolchain=SYSTEM)` |
| **`thrift`** | 18 (0 run, 18 build) | `thrift-0.24.0-GCCcore-15.3.0.eb` | Apache Thrift. Required by Apache Arrow, Parquet, and data serialization pipelines. | `DepRule(new_version='0.24.0', match_toolchain=GCCCORE153)` |
| **`RapidJSON`** | 18 (2 run, 16 build) | `RapidJSON-1.1.0-20250205-GCCcore-15.3.0.eb` | Fast JSON parser required by Apache Arrow and modern C++ tools. | `DepRule(new_version='1.1.0-20250205', match_toolchain=GCCCORE153)` |
| **`Abseil`** | 14 (2 run, 12 build) | `Abseil-20260107.1-GCCcore-15.3.0.eb` | Google Abseil C++ library. Required by Protobuf, TensorFlow, Arrow, and gRPC. | `DepRule(new_version='20260107.1', match_toolchain=GCCCORE153)` |
| **`pytest`** | 17 (1 run, 16 build) | `pytest-9.2.0-GCCcore-15.3.0.eb` | Python test framework commonly listed in build dependencies. | `DepRule(new_version='9.2.0', match_toolchain=GCCCORE153)` |
| **`googletest`** | 9 (1 run, 8 build) | `googletest-1.17.0-GCCcore-15.3.0.eb` | C++ testing framework required in build dependencies of scientific C++ codes. | `DepRule(new_version='1.17.0', match_toolchain=GCCCORE153)` |

### C. Domain Libraries (Bioinformatics, Astronomy, Visualization, CUDA)

| Package | 2023 Dep Count | 2026 Installed EasyConfig | Description & Justification | Recommended `DepRule` |
| :--- | :--- | :--- | :--- | :--- |
| **`HTSlib`** | 25 (19 run, 6 build) | `HTSlib-1.24-GCCcore-15.3.0.eb` | Universal HTS file format library (SAM/BAM/CRAM/VCF) required by SAMtools, BCFtools, and aligners. | `DepRule(new_version='1.24', match_toolchain=GCCCORE153)` |
| **`SAMtools`** | 11 (8 run, 3 build) | `SAMtools-1.24-GCCcore-15.3.0.eb` | Commonly required as a dependency by higher-level bioinformatics pipelines. | `DepRule(new_version='1.24', match_toolchain=GCCCORE153)` |
| **`cuDNN`** | 18 (8 run, 10 build) | `cuDNN-9.26.0-CUDAcore-13.3.1.eb` | Deep learning primitives library for NVIDIA GPUs (PyTorch, TensorFlow, JAX). | `DepRule(new_version='9.26.0', match_toolchain=[('CUDAcore', '13.3.1')])` |
| **`XDRfile`** | 14 (14 run, 0 build) | `XDRfile-1.1.4-GCCcore-15.3.0.eb` | Trajectory reader used by molecular dynamics tools (e.g., MDAnalysis). | `DepRule(new_version='1.1.4', match_toolchain=GCCCORE153)` |
| **`CFITSIO`** | 12 (9 run, 3 build) | `CFITSIO-4.7.0-GCCcore-15.3.0.eb` | FITS file I/O library used in astrophysics (Astropy, HEALPix) and geospatial software (GDAL). | `DepRule(new_version='4.7.0', match_toolchain=GCCCORE153)` |
| **`GLFW`** | 12 (9 run, 3 build) | `GLFW-3.5.1-GCCcore-15.3.0.eb` | Window creation and OpenGL input handling library. | `DepRule(new_version='3.5.1', match_toolchain=GCCCORE153)` |
| **`gnuplot`** | 10 (10 run, 0 build) | `gnuplot-6.0.3-GCCcore-15.3.0.eb` | Graphing utility used by benchmarking and simulation post-processing packages. | `DepRule(new_version='6.0.3', match_toolchain=GCCCORE153)` |
| **`libaec`** | 10 (10 run, 0 build) | `libaec-1.1.7-GCCcore-15.3.0.eb` | Lossless compression library serving as an open Szip replacement in HDF5 and NetCDF. | `DepRule(new_version='1.1.7', match_toolchain=GCCCORE153)` |

---

## 4. Frequent Dependencies Not Yet Installed in 2026

The following software packages appeared frequently as dependencies in 2023 and 2020 but **have not yet been installed** in `/Users/mboisson/git/easybuild-easyconfigs-installed-avx2/2026`. Their latest upstream release versions were obtained via online search:

| Package | Historical Dep Count (2023 + 2020) | Typical Dependents | Latest Upstream Version | Upstream Status & Target Details |
| :--- | :--- | :--- | :--- | :--- |
| **`VTK`** | **33** (11 in '23, 22 in '20) | ParaView, ITK, FreeCAD, deal.II, OpenFOAM | **9.6.0** | Maintained on Kitware GitLab/GitHub. Major release featuring Wayland support, ONNX inference, and WASM upgrades. |
| **`sparsehash`** | **24** (6 in '23, 18 in '20) | Trinity, Ray, Kallisto, genome assemblers | **2.0.4** | Google SparseHash repository; 2.0.4 is the stable release (also available as header-only `sparsehash-c11`). |
| **`occt`** *(Open CASCADE)* | **15** (3 in '23, 12 in '20) | FreeCAD, Gmsh, Netgen | **8.0.1** | Major version update transitioning to C++17 baseline, revised module architecture, and modernized CMake configuration. |
| **`BamTools`** | **13** (5 in '23, 8 in '20) | FreeBayes, bam2fastx | **v2.5.3** | C++ API & command-line toolkit for BAM manipulation on GitHub (`pezmaster31/bamtools`). |
| **`ELPA`** | **12** (7 in '23, 5 in '20) | CP2K, Quantum ESPRESSO, ABINIT, VASP | **2026.02.001** | High-performance dense eigenvalue solver maintained by MPCDF; standard in high-end HPC DFT codes. |
| **`Wannier90`** | **16** (7 in '23, 9 in '20) | Quantum ESPRESSO, ABINIT, VASP | **v4.0.3** | Maximally localized Wannier functions library; v4.x is a major new series hosted at `wannier-developers/wannier90`. |
| **`ParMETIS`** | **11** (5 in '23, 6 in '20) | PETSc, SuiteSparse, MFEM, Trilinos | **4.0.3** | Universal MPI graph and mesh partitioning library from KarypisLab. |
| **`ArrayFire`** | **11** (4 in '23, 7 in '20) | GPU/heterogeneous computing tensor pipelines | **v3.10.1** | GPU tensor library with oneAPI, OpenCL, and CUDA 13.x compatibility (`arrayfire/arrayfire`). |
| **`libctl`** | **11** (3 in '23, 8 in '20) | Meep, MPB | **v4.7.1** | Guile-based control language library maintained by `NanoComp/libctl`. |
| **`ITK`** | **10** (5 in '23, 5 in '20) | ANTs, biomedical imaging codes | **5.4.7** | Insight Toolkit for segmentation and registration; features 5D NRRD and 32-bit TIFF support. |
| **`CLHEP`** | **10** (5 in '23, 5 in '20) | Geant4 | **2.4.7.2** | High Energy Physics foundation classes hosted on CERN GitLab (`CLHEP_2_4_7_2`). |
| **`ecCodes`** | **10** (2 in '23, 8 in '20) | CDO, Metview, Magics | **2.50.0** | ECMWF's official GRIB/BUFR decoding and encoding library (`ecmwf/eccodes`). |
| **`YAXT`** | **10** (2 in '23, 8 in '20) | CDO, DWD ICON | **0.12.2.1** | Yet Another eXchange Tool for parallel grid data exchange on DKRZ GitLab (`dkrz-sw/yaxt`). |
| **`wxWidgets`** | **10** (1 in '23, 9 in '20) | Erlang, FileZilla, Audacity | **3.2.12** *(stable)* | Cross-platform C++ GUI framework with Wayland integration and Linux desktop improvements. |
| **`beagle-lib`** | **8** (4 in '23, 4 in '20) | BEAST, MrBayes, PhyML | **v4.0.1** | Parallel likelihood computation for phylogenetic trees (`beagle-dev/beagle-lib`). |
| **`kim-api`** | **8** (4 in '23, 4 in '20) | LAMMPS, ASE | **v2.4.2** | OpenKIM application programming interface on GitHub (`openkim/kim-api`). |
| **`JsonCpp`** | **8** (3 in '23, 5 in '20) | CMake, QGIS | **1.9.8** | C++ library for interacting with JSON (`open-source-parsers/jsoncpp`). |
| **`SUNDIALS`** | **8** (2 in '23, 6 in '20) | Cantera, deal.II, MFEM, AMReX | **v7.9.0** | Suite of nonlinear and differential/algebraic equation solvers from LLNL (`llnl/sundials`). |
| **`Jellyfish`** | **8** (2 in '23, 6 in '20) | Salmon, Trinity | **2.3.1** | Ultra-fast k-mer counting tool (`gmarcais/Jellyfish`). |
| **`Libint`** | **7** (2 in '23, 5 in '20) | CP2K, Molpro, PySCF, Psi4 | **2.9.0** *(or 2.14.x)* | Molecular integrals evaluator over Gaussian basis sets (`evaleev/libint`). |
| **`MUMPS`** | **6** (2 in '23, 4 in '20) | PETSc, Ipopt, SCIP | **5.9.1** | Multifrontal massively parallel direct sparse solver from `mumps-solver.org`. |
| **`jemalloc`** | **7** (3 in '23, 4 in '20) | High-performance multi-threaded memory allocators | **v5.4.0** | General-purpose scalable concurrent allocator (`jemalloc/jemalloc`). |
| **`KaHIP`** | **6** (4 in '23, 2 in '20) | Distributed partitioning algorithms | **v3.25** | Karlsruhe High Quality Partitioning (`KaHIP/KaHIP`). |

---

## 5. Recommended Code Additions to `2026/cc_hooks.py`

Below are the recommended updates to add to `dep_transforms_2026` in `2026/cc_hooks.py`:

```python
    # -------------------------------------------------------------------------
    # Missing scientific & computational libraries
    # -------------------------------------------------------------------------
    'GSL': DepRule(new_version='2.8', match_toolchain=COMPILERS_2026),
    'PLUMED': DepRule(new_version='2.10.2', match_toolchain=[('gofb', '2026'), ('gofbc', '2026')]),
    'SciPy-Stack': DepRule(new_version='2026b', new_suffix='', new_toolchain=None),
    'mpi4py': DepRule(new_version='4.1.2', match_toolchain=cOMPI_2026),
    'libxc': DepRule(new_version='7.1.2', match_toolchain=GCC153),
    'arpack-ng': DepRule(new_version='3.9.1', match_toolchain=('gccflexiblas', '2026')),
    'PnetCDF': DepRule(new_version='1.15.1', match_toolchain=[('gompi', '2026')]),

    # -------------------------------------------------------------------------
    # Missing common build & core development dependencies
    # -------------------------------------------------------------------------
    'JasPer': DepRule(new_version='4.2.9', match_toolchain=GCCCORE153),
    'SWIG': DepRule(new_version='4.4.1', match_toolchain=GCCCORE153),
    'tbb': DepRule(new_version='2022.3.0', match_toolchain=GCCCORE153),
    'protobuf': DepRule(new_version='36.1', match_toolchain=GCCCORE153),
    'thrift': DepRule(new_version='0.24.0', match_toolchain=GCCCORE153),
    'RapidJSON': DepRule(new_version='1.1.0-20250205', match_toolchain=GCCCORE153),
    'Abseil': DepRule(new_version='20260107.1', match_toolchain=GCCCORE153),
    'ant': DepRule(new_version='1.10.18', match_toolchain=SYSTEM),
    'pytest': DepRule(new_version='9.2.0', match_toolchain=GCCCORE153),
    'googletest': DepRule(new_version='1.17.0', match_toolchain=GCCCORE153),

    # -------------------------------------------------------------------------
    # Missing domain libraries (Bioinformatics, Astronomy, Visualization, CUDA)
    # -------------------------------------------------------------------------
    'HTSlib': DepRule(new_version='1.24', match_toolchain=GCCCORE153),
    'SAMtools': DepRule(new_version='1.24', match_toolchain=GCCCORE153),
    'cuDNN': DepRule(new_version='9.26.0', match_toolchain=[('CUDAcore', '13.3.1')]),
    'XDRfile': DepRule(new_version='1.1.4', match_toolchain=GCCCORE153),
    'CFITSIO': DepRule(new_version='4.7.0', match_toolchain=GCCCORE153),
    'GLFW': DepRule(new_version='3.5.1', match_toolchain=GCCCORE153),
    'gnuplot': DepRule(new_version='6.0.3', match_toolchain=GCCCORE153),
    'libaec': DepRule(new_version='1.1.7', match_toolchain=GCCCORE153),
```
