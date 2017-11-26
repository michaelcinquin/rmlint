#!/usr/bin/env python3
# encoding: utf-8
from nose.plugins.attrib import attr
from nose import with_setup
from tests.utils import *


BLACKLIST = [ ]

@attr('slow')
@with_setup(usual_setup_func, usual_teardown_func)
def test_collision_resistance():
    # test for at least 20 bits of collision resistancel
    # this should detect gross errors in checksum encoding...

    numfiles = 1024*1024
    for i in range(numfiles):
        create_file(i, str(i), write_binary=True)

    for algo in CKSUM_TYPES:
        if algo not in BLACKLIST:
            *_, footer = run_rmlint('-a {}'.format(algo))
            assert footer['duplicates'] == 0, 'Unexpected hash collision for hash type {}'.format(algo)
