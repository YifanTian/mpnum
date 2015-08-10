#!/usr/bin/env python
# encoding: utf-8
# FIXME Is there a better metric to compare two arrays/scalars than
#       assert_(array)_almost_equal? Something that takes magnitude into
#       account?

from __future__ import absolute_import, division, print_function

import numpy as np
import pytest as pt
from numpy.testing import assert_almost_equal

import mpnum.linalg

import mpnum.factory as factory
import mpnum.mparray as mp
from mpnum import _tools

from mparray_test import mpo_to_global, MP_TEST_PARAMETERS


@pt.mark.parametrize('nr_sites, local_dim, bond_dim', MP_TEST_PARAMETERS)
def test_mineig(nr_sites, local_dim, bond_dim):
    # With startvec_bonddim = 2 * bonddim and this seed, mineig() gets
    # stuck in a local minimum. If that happens again, increasing the
    # bond dimension of the start vector should solve the problem.
    #   np.random.seed(46)
    mpo = factory.random_mpa(nr_sites, (local_dim, local_dim), bond_dim)
    # make mpa Herimitan in place, without increasing bond dimension:
    for lten in mpo:
        lten += lten.swapaxes(1, 2).conj()
    mpo.normalize()
    mpo /= mp.norm(mpo)
    op = mpo_to_global(mpo).reshape((local_dim**nr_sites,) * 2)
    eigvals, eigvec = np.linalg.eig(op)
    assert (np.abs(eigvals.imag) < 1e-10).all(), str(eigvals.imag)
    mineig_pos = eigvals.argmin()
    mineig = eigvals[mineig_pos]
    mineig_eigvec = eigvec[:, mineig_pos]
    mineig2, mineig_eigvec2 = mpnum.linalg.mineig(mpo, startvec_bonddim=3 * bond_dim)
    mineig_eigvec2 = mineig_eigvec2.to_array().flatten()
    overlap = np.inner(mineig_eigvec.conj(), mineig_eigvec2)
    assert_almost_equal(mineig, mineig2)
    assert_almost_equal(1, abs(overlap))
