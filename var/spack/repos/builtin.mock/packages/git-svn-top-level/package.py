# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class GitSvnTopLevel(Package):
    """Mock package that uses git for fetching."""
    homepage = "http://www.git-fetch-example.com"

    # can't have two VCS fetchers.
    git = 'https://example.com/some/git/repo'
    svn = 'https://example.com/some/svn/repo'

    version('2.0')
