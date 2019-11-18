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
EasyBuild support for a system+CUDAcore compiler toolchain.

:author: Kenneth Hoste (Ghent University)
:author: Bart Oldeman (McGill University, Calcul Quebec, Compute Canada)
"""

from easybuild.toolchains.compiler.cuda import Cuda
from easybuild.toolchains.compiler.gcc import Gcc
from easybuild.toolchains.gcccore import GCCcore
try:
    from easybuild.tools.toolchain import SYSTEM_TOOLCHAIN_NAME
except ImportError:
    from easybuild.tools.toolchain import DUMMY_TOOLCHAIN_NAME as SYSTEM_TOOLCHAIN_NAME


class CUDAcore(Cuda):
    """Compiler toolchain with system compiler and CUDAcore."""
    NAME = 'CUDAcore'

    COMPILER_MODULE_NAME = []
    COMPILER_CUDA_MODULE_NAME = ['CUDAcore']
    COMPILER_FAMILY = GCCcore.NAME
    COMPILER_GENERIC_OPTION = Gcc.COMPILER_GENERIC_OPTION

    COMPILER_UNIQUE_OPTION_MAP = {'defaultprec': []}
    COMPILER_CC = Gcc.COMPILER_CC
    COMPILER_CXX = Gcc.COMPILER_CXX
    COMPILER_F77 = Gcc.COMPILER_F77
    COMPILER_F90 = Gcc.COMPILER_F90
    COMPILER_FC = Gcc.COMPILER_FC

    SUBTOOLCHAIN = SYSTEM_TOOLCHAIN_NAME
    OPTIONAL = True

