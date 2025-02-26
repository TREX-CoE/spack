# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class PyMdanalysis(PythonPackage):
    """MDAnalysis is a Python toolkit to analyze molecular dynamics
    trajectories generated by a wide range of popular simulation
    packages including DL_Poly, CHARMM, Amber, NAMD, LAMMPS, and
    Gromacs. (See the lists of supported trajectory formats and
    topology formats.)"""

    homepage = "https://www.mdanalysis.org"
    pypi = "MDAnalysis/MDAnalysis-0.19.2.tar.gz"

    version('1.0.0',  sha256='f45a024aca45e390ff1c45ca90beb2180b78881be377e2a1aa9cd6c109bcfa81')
    version('0.20.1', sha256='d04b71b193b9716d2597ffb9938b93f43487fa535da1bb5c1f2baccf356d7df9')
    version('0.19.2', sha256='c5395bbafa5efca2e1aee4715d26129844140c47cb8301da0293106cb969de7d')
    version('0.19.1', sha256='ff1d694f8598c0833ec340de6a6adb3b5e62b92d0fa94ee6401718ba972db3cc')
    version('0.19.0', sha256='248e3b37fc6150e31c609cc18a3927c32aee37b76d29cbfedf635e7e1aa982cf')
    version('0.18.0', sha256='a08acea1755112411e7db55e3f282e164b47a59e15794b38744cce6c596f252a')
    version('0.17.0', sha256='9bd61760334698cc7b8a57ad26456451e926e9c9e66722594ad8816561348cde')
    version('0.16.2', sha256='407d9a9ff1ab8a5e47973714d06fabff220f8d08a28792dee93e88e70e995b0a')
    version('0.16.1', sha256='3dc8f5d639ab3a0d152cbd7259ae9372ec8a9bac0f8cb7d3b80ce5adc1e3ee57')
    version('0.16.0', sha256='c4824fa1fddd336daa39371436187ebb023366885fb250c2827ed7fce2546bd4')
    version('0.15.0', sha256='9088786048b47339cba1f8a586977bbb3bb04ae1bcd0462b59e45bda37e25533')

    variant('analysis', default=True,
            description='Enable analysis packages: matplotlib, scipy, seaborn')
    variant('amber', default=False,
            description='Support AMBER netcdf format.')

    depends_on('python@2.7:', type=('build', 'run'))

    depends_on('py-setuptools',   type='build')
    depends_on('py-cython@0.16:', type='build')

    depends_on('py-six@1.4.0:',    type=('build', 'run'))
    depends_on('py-networkx@1.0:', type=('build', 'run'))

    depends_on('py-gsd@1.4.0:',         when='@0.17.0:', type=('build', 'run'))
    depends_on('py-mmtf-python@1.0.0:', when='@0.16.0:', type=('build', 'run'))
    depends_on('py-mock',               when='@0.18.0:', type=('build', 'run'))
    depends_on('py-tqdm@4.43.0:',       when='@1.0.0:',  type=('build', 'run'))

    depends_on('py-joblib',       when='@0.16.0:0.20.1', type=('build', 'run'))
    depends_on('py-joblib@0.12:', when='@1.0.0:',        type=('build', 'run'))

    depends_on('py-numpy@1.5.0:',  when='@:0.15.0',       type=('build', 'run'))
    depends_on('py-numpy@1.10.4:', when='@0.16.0:0.19.2', type=('build', 'run'))
    depends_on('py-numpy@1.13.3:', when='@0.20.1:',       type=('build', 'run'))

    depends_on('py-biopython@1.59:', when='@:0.17.0', type=('build', 'run'))
    depends_on('py-biopython@1.71:', when='@0.18.0:', type=('build', 'run'))

    depends_on('py-griddataformats@0.3.2:', when='@:0.16.2', type=('build', 'run'))
    depends_on('py-griddataformats@0.4:',   when='@0.17.0:', type=('build', 'run'))

    depends_on('py-matplotlib',        when='@:0.15.0+analysis',       type=('build', 'run'))
    depends_on('py-matplotlib@1.5.1:', when='@0.16.0:0.16.1+analysis', type=('build', 'run'))
    depends_on('py-matplotlib@1.5.1:', when='@0.16.2:',                type=('build', 'run'))

    depends_on('py-scipy',        when='@:0.16.1+analysis', type=('build', 'run'))
    depends_on('py-scipy',        when='@0.16.2:0.17.0',    type=('build', 'run'))
    depends_on('py-scipy@1.0.0:', when='@0.18.0:',          type=('build', 'run'))

    depends_on('py-scikit-learn', when='@0.16.0:+analysis', type=('build', 'run'))
    depends_on('py-seaborn',      when='+analysis',         type=('build', 'run'))

    depends_on('py-netcdf4@1.0:', when='+amber', type=('build', 'run'))
    depends_on('hdf5',            when='+amber', type=('run'))
