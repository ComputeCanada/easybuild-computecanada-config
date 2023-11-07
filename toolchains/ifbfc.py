##
# Copyright 2012-2023 Ghent University
#
# This file is part of EasyBuild,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://www.vscentrum.be),
# Flemish Research Foundation (FWO) (http://www.fwo.be/en)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# http://github.com/hpcugent/easybuild
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
EasyBuild support for ifbfc compiler toolchain (includes Intel compilers,
FlexiBLAS, FFTW (serial), and CUDA).

:author: Stijn De Weirdt (Ghent University)
:author: Kenneth Hoste (Ghent University)
:author: Bart Oldeman (McGill University, Calcul Quebec, Compute Canada)
:author: Maxime Boissonneault (Universite Laval, Calcul Quebec, Calcul Canada)
"""

from easybuild.toolchains.ifbc import Ifbc
from easybuild.toolchains.ifbf import Ifbf


class Ifbfc(Ifbc, Ifbf):
    """
    Compiler toolchain with Intel compilers, FlexiBLAS, FFTW (serial) and CUDA
    """
    NAME = 'ifbfc'
    SUBTOOLCHAIN = [Ifbc.NAME, Ifbf.NAME]
    OPTIONAL = True
