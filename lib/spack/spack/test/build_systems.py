# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import glob
import os
import sys

import py.path
import pytest

import llnl.util.filesystem as fs

import spack.build_systems.autotools
import spack.environment
import spack.platforms
import spack.repo
from spack.build_environment import ChildError, get_std_cmake_args, setup_package
from spack.spec import Spec
from spack.util.executable import which

DATA_PATH = os.path.join(spack.paths.test_path, 'data')

pytestmark = pytest.mark.skipif(sys.platform == "win32",
                                reason="does not run on windows")


@pytest.fixture()
def concretize_and_setup():
    def _func(spec_str):
        s = Spec('mpich').concretized()
        setup_package(s.package, False)
        return s
    return _func


@pytest.fixture()
def test_dir(tmpdir):
    def _func(dir_str):
        py.path.local(dir_str).copy(tmpdir)
        return str(tmpdir)
    return _func


@pytest.mark.usefixtures('config', 'mock_packages', 'working_env')
class TestTargets(object):
    @pytest.mark.parametrize(
        'input_dir', glob.iglob(os.path.join(DATA_PATH, 'make', 'affirmative', '*'))
    )
    def test_affirmative_make_check(self, input_dir, test_dir, concretize_and_setup):
        """Tests that Spack correctly detects targets in a Makefile."""
        s = concretize_and_setup('mpich')
        with fs.working_dir(test_dir(input_dir)):
            assert s.package._has_make_target('check')
            s.package._if_make_target_execute('check')

    @pytest.mark.parametrize(
        'input_dir', glob.iglob(os.path.join(DATA_PATH, 'make', 'negative', '*'))
    )
    @pytest.mark.regression('9067')
    def test_negative_make_check(self, input_dir, test_dir, concretize_and_setup):
        """Tests that Spack correctly ignores false positives in a Makefile."""
        s = concretize_and_setup('mpich')
        with fs.working_dir(test_dir(input_dir)):
            assert not s.package._has_make_target('check')
            s.package._if_make_target_execute('check')

    @pytest.mark.skipif(not which('ninja'), reason='ninja is not installed')
    @pytest.mark.parametrize(
        'input_dir', glob.iglob(os.path.join(DATA_PATH, 'ninja', 'affirmative', '*'))
    )
    def test_affirmative_ninja_check(self, input_dir, test_dir, concretize_and_setup):
        """Tests that Spack correctly detects targets in a Ninja build script."""
        s = concretize_and_setup('mpich')
        with fs.working_dir(test_dir(input_dir)):
            assert s.package._has_ninja_target('check')
            s.package._if_ninja_target_execute('check')

    @pytest.mark.skipif(not which('ninja'), reason='ninja is not installed')
    @pytest.mark.parametrize(
        'input_dir', glob.iglob(os.path.join(DATA_PATH, 'ninja', 'negative', '*'))
    )
    def test_negative_ninja_check(self, input_dir, test_dir, concretize_and_setup):
        """Tests that Spack correctly ignores false positives in a Ninja
        build script.
        """
        s = concretize_and_setup('mpich')
        with fs.working_dir(test_dir(input_dir)):
            assert not s.package._has_ninja_target('check')
            s.package._if_ninja_target_execute('check')


@pytest.mark.usefixtures('config', 'mock_packages')
class TestAutotoolsPackage(object):

    def test_with_or_without(self):
        s = Spec('a').concretized()
        options = s.package.with_or_without('foo')

        # Ensure that values that are not representing a feature
        # are not used by with_or_without
        assert '--without-none' not in options
        assert '--with-bar' in options
        assert '--without-baz' in options
        assert '--no-fee' in options

        def activate(value):
            return 'something'

        options = s.package.with_or_without('foo', activation_value=activate)
        assert '--without-none' not in options
        assert '--with-bar=something' in options
        assert '--without-baz' in options
        assert '--no-fee' in options

        options = s.package.enable_or_disable('foo')
        assert '--disable-none' not in options
        assert '--enable-bar' in options
        assert '--disable-baz' in options
        assert '--disable-fee' in options

        options = s.package.with_or_without('bvv')
        assert '--with-bvv' in options

        options = s.package.with_or_without('lorem-ipsum', variant='lorem_ipsum')
        assert '--without-lorem-ipsum' in options

    def test_none_is_allowed(self):
        s = Spec('a foo=none').concretized()
        options = s.package.with_or_without('foo')

        # Ensure that values that are not representing a feature
        # are not used by with_or_without
        assert '--with-none' not in options
        assert '--without-bar' in options
        assert '--without-baz' in options
        assert '--no-fee' in options

    def test_libtool_archive_files_are_deleted_by_default(
            self, mutable_database
    ):
        # Install a package that creates a mock libtool archive
        s = Spec('libtool-deletion').concretized()
        s.package.do_install(explicit=True)

        # Assert the libtool archive is not there and we have
        # a log of removed files
        assert not os.path.exists(s.package.libtool_archive_file)
        search_directory = os.path.join(s.prefix, '.spack')
        libtool_deletion_log = fs.find(
            search_directory, 'removed_la_files.txt', recursive=True
        )
        assert libtool_deletion_log

    def test_libtool_archive_files_might_be_installed_on_demand(
            self, mutable_database, monkeypatch
    ):
        # Install a package that creates a mock libtool archive,
        # patch its package to preserve the installation
        s = Spec('libtool-deletion').concretized()
        monkeypatch.setattr(s.package, 'install_libtool_archives', True)
        s.package.do_install(explicit=True)

        # Assert libtool archives are installed
        assert os.path.exists(s.package.libtool_archive_file)

    def test_autotools_gnuconfig_replacement(self, mutable_database):
        """
        Tests whether only broken config.sub and config.guess are replaced with
        files from working alternatives from the gnuconfig package.
        """
        s = Spec('autotools-config-replacement +patch_config_files +gnuconfig')
        s.concretize()
        s.package.do_install()

        with open(os.path.join(s.prefix.broken, 'config.sub')) as f:
            assert "gnuconfig version of config.sub" in f.read()

        with open(os.path.join(s.prefix.broken, 'config.guess')) as f:
            assert "gnuconfig version of config.guess" in f.read()

        with open(os.path.join(s.prefix.working, 'config.sub')) as f:
            assert "gnuconfig version of config.sub" not in f.read()

        with open(os.path.join(s.prefix.working, 'config.guess')) as f:
            assert "gnuconfig version of config.guess" not in f.read()

    def test_autotools_gnuconfig_replacement_disabled(self, mutable_database):
        """
        Tests whether disabling patch_config_files
        """
        s = Spec('autotools-config-replacement ~patch_config_files +gnuconfig')
        s.concretize()
        s.package.do_install()

        with open(os.path.join(s.prefix.broken, 'config.sub')) as f:
            assert "gnuconfig version of config.sub" not in f.read()

        with open(os.path.join(s.prefix.broken, 'config.guess')) as f:
            assert "gnuconfig version of config.guess" not in f.read()

        with open(os.path.join(s.prefix.working, 'config.sub')) as f:
            assert "gnuconfig version of config.sub" not in f.read()

        with open(os.path.join(s.prefix.working, 'config.guess')) as f:
            assert "gnuconfig version of config.guess" not in f.read()

    @pytest.mark.disable_clean_stage_check
    def test_autotools_gnuconfig_replacement_no_gnuconfig(self, mutable_database):
        """
        Tests whether a useful error message is shown when patch_config_files is
        enabled, but gnuconfig is not listed as a direct build dependency.
        """
        s = Spec('autotools-config-replacement +patch_config_files ~gnuconfig')
        s.concretize()

        msg = "Cannot patch config files: missing dependencies: gnuconfig"
        with pytest.raises(ChildError, match=msg):
            s.package.do_install()

    @pytest.mark.disable_clean_stage_check
    def test_broken_external_gnuconfig(self, mutable_database, tmpdir):
        """
        Tests whether we get a useful error message when gnuconfig is marked
        external, but the install prefix is misconfigured and no config.guess
        and config.sub substitute files are found in the provided prefix.
        """
        env_dir = str(tmpdir.ensure('env', dir=True))
        gnuconfig_dir = str(tmpdir.ensure('gnuconfig', dir=True))  # empty dir
        with open(os.path.join(env_dir, 'spack.yaml'), 'w') as f:
            f.write("""\
spack:
  specs:
  - 'autotools-config-replacement +patch_config_files +gnuconfig'
  packages:
    gnuconfig:
      buildable: false
      externals:
      - spec: gnuconfig@1.0.0
        prefix: {0}
""".format(gnuconfig_dir))

        msg = ("Spack could not find `config.guess`.*misconfigured as an "
               "external package")
        with spack.environment.Environment(env_dir) as e:
            e.concretize()
            with pytest.raises(ChildError, match=msg):
                e.install_all()


@pytest.mark.usefixtures('config', 'mock_packages')
class TestCMakePackage(object):
    def test_cmake_std_args(self):
        # Call the function on a CMakePackage instance
        s = Spec('cmake-client').concretized()
        assert s.package.std_cmake_args == get_std_cmake_args(s.package)

        # Call it on another kind of package
        s = Spec('mpich').concretized()
        assert get_std_cmake_args(s.package)

    def test_cmake_bad_generator(self):
        s = Spec('cmake-client').concretized()
        s.package.generator = 'Yellow Sticky Notes'
        with pytest.raises(spack.package_base.InstallError):
            get_std_cmake_args(s.package)

    def test_cmake_secondary_generator(config, mock_packages):
        s = Spec('cmake-client').concretized()
        s.package.generator = 'CodeBlocks - Unix Makefiles'
        assert get_std_cmake_args(s.package)

    def test_define(self):
        s = Spec('cmake-client').concretized()

        define = s.package.define
        for cls in (list, tuple):
            assert define('MULTI', cls(['right', 'up'])) == '-DMULTI:STRING=right;up'

        file_list = fs.FileList(['/foo', '/bar'])
        assert define('MULTI', file_list) == '-DMULTI:STRING=/foo;/bar'

        assert define('ENABLE_TRUTH', False) == '-DENABLE_TRUTH:BOOL=OFF'
        assert define('ENABLE_TRUTH', True) == '-DENABLE_TRUTH:BOOL=ON'

        assert define('SINGLE', 'red') == '-DSINGLE:STRING=red'

    def test_define_from_variant(self):
        s = Spec('cmake-client multi=up,right ~truthy single=red').concretized()

        arg = s.package.define_from_variant('MULTI')
        assert arg == '-DMULTI:STRING=right;up'

        arg = s.package.define_from_variant('ENABLE_TRUTH', 'truthy')
        assert arg == '-DENABLE_TRUTH:BOOL=OFF'

        arg = s.package.define_from_variant('SINGLE')
        assert arg == '-DSINGLE:STRING=red'

        with pytest.raises(KeyError, match="not a variant"):
            s.package.define_from_variant('NONEXISTENT')


@pytest.mark.usefixtures('config', 'mock_packages')
class TestDownloadMixins(object):
    """Test GnuMirrorPackage, SourceforgePackage, SourcewarePackage and XorgPackage."""
    @pytest.mark.parametrize('spec_str,expected_url', [
        # GnuMirrorPackage
        ('mirror-gnu', 'https://ftpmirror.gnu.org/make/make-4.2.1.tar.gz'),
        # SourceforgePackage
        ('mirror-sourceforge',
         'https://prdownloads.sourceforge.net/tcl/tcl8.6.5-src.tar.gz'),
        # SourcewarePackage
        ('mirror-sourceware', 'https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz'),
        # XorgPackage
        ('mirror-xorg',
         'https://www.x.org/archive/individual/util/util-macros-1.19.1.tar.bz2')
    ])
    def test_attributes_defined(self, spec_str, expected_url):
        s = Spec(spec_str).concretized()
        assert s.package.urls[0] == expected_url

    @pytest.mark.parametrize('spec_str,error_fmt', [
        # GnuMirrorPackage
        ('mirror-gnu-broken', r'{0} must define a `gnu_mirror_path` attribute'),
        # SourceforgePackage
        ('mirror-sourceforge-broken',
         r'{0} must define a `sourceforge_mirror_path` attribute'),
        # SourcewarePackage
        ('mirror-sourceware-broken',
         r'{0} must define a `sourceware_mirror_path` attribute'),
        # XorgPackage
        ('mirror-xorg-broken', r'{0} must define a `xorg_mirror_path` attribute'),
    ])
    def test_attributes_missing(self, spec_str, error_fmt):
        s = Spec(spec_str).concretized()
        error_msg = error_fmt.format(type(s.package).__name__)
        with pytest.raises(AttributeError, match=error_msg):
            s.package.urls


def test_cmake_define_from_variant_conditional(config, mock_packages):
    """Test that define_from_variant returns empty string when a condition on a variant
    is not met. When this is the case, the variant is not set in the spec."""
    s = Spec('cmake-conditional-variants-test').concretized()
    assert 'example' not in s.variants
    assert s.package.define_from_variant('EXAMPLE', 'example') == ''


def test_autotools_args_from_conditional_variant(config, mock_packages):
    """Test that _activate_or_not returns an empty string when a condition on a variant
    is not met. When this is the case, the variant is not set in the spec."""
    s = Spec('autotools-conditional-variants-test').concretized()
    assert 'example' not in s.variants
    assert len(s.package._activate_or_not('example', 'enable', 'disable')) == 0


def test_autoreconf_search_path_args_multiple(config, mock_packages, tmpdir):
    """autoreconf should receive the right -I flags with search paths for m4 files
    for build deps."""
    spec = Spec('dttop').concretized()
    aclocal_fst = str(tmpdir.mkdir("fst").mkdir("share").mkdir("aclocal"))
    aclocal_snd = str(tmpdir.mkdir("snd").mkdir("share").mkdir("aclocal"))
    build_dep_one, build_dep_two = spec.dependencies(deptype='build')
    build_dep_one.prefix = str(tmpdir.join("fst"))
    build_dep_two.prefix = str(tmpdir.join("snd"))
    assert spack.build_systems.autotools._autoreconf_search_path_args(spec) == [
        '-I', aclocal_fst, '-I', aclocal_snd
    ]


def test_autoreconf_search_path_args_skip_automake(config, mock_packages, tmpdir):
    """automake's aclocal dir should not be added as -I flag as it is a default
    3rd party dir search path, and if it's a system version it usually includes
    m4 files shadowing spack deps."""
    spec = Spec('dttop').concretized()
    tmpdir.mkdir("fst").mkdir("share").mkdir("aclocal")
    aclocal_snd = str(tmpdir.mkdir("snd").mkdir("share").mkdir("aclocal"))
    build_dep_one, build_dep_two = spec.dependencies(deptype='build')
    build_dep_one.name = 'automake'
    build_dep_one.prefix = str(tmpdir.join("fst"))
    build_dep_two.prefix = str(tmpdir.join("snd"))
    assert spack.build_systems.autotools._autoreconf_search_path_args(spec) == [
        '-I', aclocal_snd
    ]


def test_autoreconf_search_path_args_external_order(config, mock_packages, tmpdir):
    """When a build dep is external, its -I flag should occur last"""
    spec = Spec('dttop').concretized()
    aclocal_fst = str(tmpdir.mkdir("fst").mkdir("share").mkdir("aclocal"))
    aclocal_snd = str(tmpdir.mkdir("snd").mkdir("share").mkdir("aclocal"))
    build_dep_one, build_dep_two = spec.dependencies(deptype='build')
    build_dep_one.external_path = str(tmpdir.join("fst"))
    build_dep_two.prefix = str(tmpdir.join("snd"))
    assert spack.build_systems.autotools._autoreconf_search_path_args(spec) == [
        '-I', aclocal_snd, '-I', aclocal_fst
    ]


def test_autoreconf_search_path_skip_nonexisting(config, mock_packages, tmpdir):
    """Skip -I flags for non-existing directories"""
    spec = Spec('dttop').concretized()
    build_dep_one, build_dep_two = spec.dependencies(deptype='build')
    build_dep_one.prefix = str(tmpdir.join("fst"))
    build_dep_two.prefix = str(tmpdir.join("snd"))
    assert spack.build_systems.autotools._autoreconf_search_path_args(spec) == []


def test_autoreconf_search_path_dont_repeat(config, mock_packages, tmpdir):
    """Do not add the same -I flag twice to keep things readable for humans"""
    spec = Spec('dttop').concretized()
    aclocal = str(tmpdir.mkdir("prefix").mkdir("share").mkdir("aclocal"))
    build_dep_one, build_dep_two = spec.dependencies(deptype='build')
    build_dep_one.external_path = str(tmpdir.join("prefix"))
    build_dep_two.external_path = str(tmpdir.join("prefix"))
    assert spack.build_systems.autotools._autoreconf_search_path_args(spec) == [
        '-I', aclocal
    ]
