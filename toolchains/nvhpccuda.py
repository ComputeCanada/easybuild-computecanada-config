##
# Copyright 2013-2019 Ghent University
#
# This file is part of EasyBuild,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://www.vscentrum.be),
# Flemish Research Foundation (FWO) (http://www.fwo.be/en)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# https://github.com/easybuilders/easybuild
#
# EasyBuild is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# EasyBuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EasyBuild.  If not, see <http://www.gnu.org/licenses/>.
##
"""
EasyBuild support for a NVHPC + CUDA compiler toolchain.

:author: Maxime Boissonneault (Universite Laval, Calcul Quebec, Compute Canada)
:author: Bart Oldeman (McGill University, Calcul Quebec, Compute Canada)
"""

from easybuild.toolchains.compiler.cuda import Cuda
from easybuild.toolchains.cudacore import CUDAcore
from easybuild.toolchains.gcccorecuda import GCCcoreCUDA
from easybuild.toolchains.nvhpc import NVHPCToolchain


class NVHPCCUDA(NVHPCToolchain, Cuda):
    """Compiler toolchain with NVHPC and CUDA."""
    NAME = 'nvhpccuda'

    COMPILER_MODULE_NAME = NVHPCToolchain.COMPILER_MODULE_NAME + Cuda.COMPILER_CUDA_MODULE_NAME
    SUBTOOLCHAIN = [NVHPCToolchain.NAME, GCCcoreCUDA.NAME, CUDAcore.NAME]
