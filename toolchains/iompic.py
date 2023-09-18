##
# Copyright 2013-2023 Ghent University
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
EasyBuild support for iompic compiler toolchain (includes Intel compilers (icc, ifort), OpenMPI and CUDA).

Authors:

* Stijn De Weirdt (Ghent University)
* Kenneth Hoste (Ghent University)
* Bart Oldeman (Digital Research Alliance of Canada)
"""

from easybuild.toolchains.iompi import Iompi
from easybuild.toolchains.iccifortcuda import IccIfortCUDA
from easybuild.toolchains.intelcompilerscuda import IntelCompilersCUDA


class Iompic(Iompi, IccIfortCUDA, IntelCompilersCUDA):
    """Compiler toolchain with Intel compilers (icc/ifort), OpenMPI and CUDA."""
    # compiler-only subtoolchain can't be determine statically
    # since depends on toolchain version (see below),
    # so register both here as possible alternatives (which is taken into account elsewhere)
    NAME = 'iompic'
    SUBTOOLCHAIN = [(IccIfortCUDA.NAME, IntelCompilersCUDA.NAME)]

    def __init__(self, *args, **kwargs):
        """Constructor for Iompic toolchain class."""

        super(Iompic, self).__init__(*args, **kwargs)
        if self.oneapi_gen:
            self.SUBTOOLCHAIN = IntelCompilersCUDA.NAME
            self.COMPILER_MODULE_NAME = IntelCompilersCUDA.COMPILER_MODULE_NAME
        else:
            self.SUBTOOLCHAIN = IccIfortCUDA.NAME
            self.COMPILER_MODULE_NAME = IccIfortCUDA.COMPILER_MODULE_NAME
