# encoding: utf-8


r'''Matrix-product representation of POVMs

This module provides the following classes:

* :class:`MPPovm`: A matrix product representation of a multi-site
  POVM.

  For example, for a linear chain of `n` qubits this class can
  represent the POVM of the observable `XX...X` with :math:`2^n`
  elements efficiently. It is also possible to sample from the
  probability distribution of this POVM efficiently.

* :class:`MPPovmList`: A list of MP-POVMs.

  This class can be used e.g. to obtain estimated expectation values
  of the local observable `XX1...1` on two qubits from from samples
  for the global observables `XX...X` and `XXY...Y` (cf. below on
  :ref:`mppovm-lfun-overview`).

* The methods :func:`MPPovm.embed`,
  :func:`MPPovm.block`/:func:`MPPovmList.block`,
  :func:`MPPovm.repeat`/:func:`MPPovmList.repeat` as well as
  :func:`pauli_mpp` and :func:`pauli_mpps` allow for convenient
  construction of MP-POVMs and MP-POVM lists.

.. _mppovm-lfun-overview:

Linear combinations of functions of POVM outcomes
=====

In order to perform the just mentioned estimation of probabilities of
one POVM from samples of another POVM with possibly larger support, we
provide a function which can estimate linear functions of functions of
POVM outcomes: Let :math:`M` a finite index set with real elements
:math:`y \in M \subset \mathbb R` such that :math:`\hat y` are the
positive semidefinite POVM elements which sum to the identity,
:math:`\sum_{y \in M} \hat y = 1`. Given a state :math:`\rho`, the
probability mass function (PMF) of the probability distribution given
by the POVM and the state can be expressed as :math:`p_y =
\operatorname{tr}(\rho \hat y)`, :math:`y \in M` or as :math:`p(x) =
\sum_{y \in M} \delta(x - y) p_y`. Let further :math:`D = (x_1,
\ldots, x_m)`, :math:`x_k \in M` a set of samples from :math:`p(x)`
and let :math:`f \colon M \to \mathbb R` an arbitrary function of the
POVM outcomes. The true value :math:`\langle f \rangle_p = \int f(y)
p(y) \mathrm d y` can then be estimated using the sample average
:math:`\langle f \rangle_D = \frac1m \sum_{k=1}^m f(x_k) p_{x_k}`. In
the same way, a linear combination :math:`f = \sum c_i f_i` of
functions :math:`f_i \colon M \to \mathbb R` of POVM outcomes can be
estimated by :math:`\langle f \rangle_D = \sum_i c_i \langle f_i
\rangle_D`. Such a linear combination of functions of POVM outcomes
can be estimated using :func:`MPPovm.est_lfun()`. More technically,
the relation :math:`\langle \langle f \rangle_D \rangle_{p_m} =
\langle f \rangle_p` shows that :math:`\langle f \rangle_D` is an
unbiased estimator for the true expectation value :math:`\langle f
\rangle_p`; the probability distribution of the dataset :math:`D` is
given by the sampling distribution :math:`p_m(D) = p(x_1) \ldots
p(x_m)`.

Estimates of the POVM probabilities :math:`p_y` can also be expressed
as functions of this kind: Consider the function

.. math::

   \theta_y(x) =
   \begin{cases}
     1, & x = y, \\
     0, & \text{otherwise.}
   \end{cases}

The true value of this function under :math:`p(x)` is :math:`\langle
\theta_y \rangle_p = p_y` and the sample average :math:`\langle
\theta_y \rangle_D` provides an estimator for :math:`p_y`. In order to
estimate probabilities of one POVM from samples for another POVM, such
a function can be used: E.g. to estimate the probability of the
:math:`(+1, +1)` outcome of the POVM `XX1...1`, we can define a
function which is equal to 1 if the outcome of the POVM `XX...X` on
the first two sites is equal to :math:`(+1, +1)` and zero
otherwise. The sample average of this function over samples for the
latter POVM `XX...X` will estimate the desired probability. This
approach is implemented in :func:`MPPovm.est_pmf_from()`. If samples
from more than one POVM are available for estimating a given
probability, a weighted average of estimators can be used as
implemented in :func:`MPPovm.est_pmf_from_mpps()`; the list of
MP-POVMs for which samples are available is passed as an
:class:`MPPovmList` instance. Finally, the function
:func:`MPPovmList.est_lfun_from` allows estimation of a linear
combination of probabilities from different POVMs using samples of a
second list of MP-POVMs. This function also estimates the variance of
the estimate. In order to perform the two estimation procedures, for
each probability, we construct an estimator from a weighted average of
functions of outcomes of different POVMs, as has been explained
above. For more simple settings, :func:`MPPovmList.est_lfun` is also
available.

True values of the functions just mentioned can be obtained from
:func:`MPPovm.lfun`, :func:`MPPovmList.lfun` and
:func:`MPPovmList.lfun_from`. All functions return both the true
expectation value and the variance of the expectation value.

The variance of the (true) expectation value :math:`\langle f
\rangle_p` of a function :math:`f\colon M \to \mathbb R` is given by
:math:`\operatorname{var}_p(f) = \operatorname{cov}_p(f, f)` with
:math:`\operatorname{cov}_p(f, g) = \langle fg \rangle_p - \langle f
\rangle_p \langle g \rangle_p`. The variance of the estimate
:math:`\langle f \rangle_D` is given by
:math:`\operatorname{var}_{p_m}(\langle f \rangle_D) = \frac1m
\operatorname{var}_p(f)` where :math:`p_m(D)` is the sampling
distribution from above. An unbiased estimator for the covariance
:math:`\operatorname{cov}_p(f, g)` is given by :math:`\frac{m}{m-1}
\operatorname{cov}_D(f, g)` where the sample covariance
:math:`\operatorname{cov}_D(f, g)` is defined in terms of sample
averages in the usual way, :math:`\operatorname{cov}_D(f, g) = \langle
fg \rangle_D - \langle f \rangle_D \langle g \rangle_D`. This
estimator is used by :func:`MPPovm.est_lfun`.

.. todo::

   Explain the details of the variance estimation, in particular the
   difference between the variances returned from
   :func:`MPPovmList.lfun` and :func:`MPPovmList.lfun_from`. Check the
   mean square error.

   Add a good references explaining all facts mentioned above and for
   further reading.

   Document the runtime and memory cost of the functions.

Class and function reference
=====

'''


from __future__ import absolute_import, division, print_function

import collections
import itertools as it
import numpy as np

import mpnum.factory as factory
import mpnum.mparray as mp
import mpnum.mpsmpo as mpsmpo
from mpnum._tools import check_pmf


class _MPSCC:

    "Represent a mixed state as convex combination of pure MPS (experimental)"

    def __init__(self, weights, mps, eps=1e-10):
        assert weights.dtype.kind == 'f'
        assert abs(weights.sum() - 1.0) <= eps
        assert all(len(m) == len(mps[0]) for m in mps)
        self.weights = weights
        self.mps = mps

    def __len__(self):
        return len(self.mps[0])

    def to_pmps(self, norm_eps=1e-6, **kwargs):
        from mpnum.special import sumup2
        n = len(self.mps)
        def basempa(ldim, i):
            a = np.zeros([ldim])
            a[i] = 1.0
            return mp.MPArray.from_array(a[None, :], plegs=2)
        pmps = (
            mp.partialdot(mpsmpo.mps_to_pmps(mps), basempa(n, i), start_at=0)
            for i, mps in enumerate(self.mps)
        )
        res = sumup2(pmps, self.weights**0.5, **kwargs)
        n = mp.norm(res)
        # Assumes input MPS were normalized
        assert abs(n - 1.0) <= norm_eps
        res /= n
        return res


class MPPovm(mp.MPArray):
    """MPArray representation of multipartite POVM

    There are two different ways to write down a POVM in matrix product form

    1) As a list of matrix product operators, where each entry corresponds to
        a single POVM element

    2) As a matrix proudct array with 3 physical legs:

                [POVM index, column index, row index]

       that is, the first physical leg of the MPArray corresponds to
       the index of the POVM element. This representation is
       especially helpful for computing expectation values with
       MPSs/MPDOs.

    Here, we choose the second.

    .. todo:: This class should provide a function which returns
        expectation values as full array. (Even though computing
        expectation values using the POVM struture brings advantages,
        we usually need the result as full array.) This function
        should also replace small negative probabilities by zero and
        normalize the sum of all probabilities to unity (if the
        deviation is non-zero but small). The same checks should also
        be implemented in localpovm.POVM.

    .. todo:: Right now we use this class for multi-site POVMs with
        elements obtained from every possible combination of the
        elements of single-site POVMs: The POVM index is split across
        all sites. Explore whether and how this concept can also be
        useful in other cases.

    """

    def __init__(self, *args, **kwargs):
        mp.MPArray.__init__(self, *args, **kwargs)
        assert all(plegs == 3 for plegs in self.plegs), \
            "Need 3 physical legs at each site: {!r}".format(self.pdims)
        assert all(pdims[1] == pdims[2] for pdims in self.pdims), \
            "Hilbert space dimension mismatch: {!r}".format(self.pdims)
        # Used to store single outcomes as np.uint8 with 255 = 0xff
        # denoting "no value" (see :func:`MPPovm.sample`,
        # :func:`MPPovm.unpack_samples`).
        assert all(dim <= 255 for dim in self.outdims), \
            "Maximal outcome dimension 255 exceeded: {!r}".format(self.outdims)

    @property
    def outdims(self):
        """Outcome dimensions"""
        # First physical leg dimension
        return tuple(lt.shape[1] for lt in self._lt)

    @property
    def nsoutdims(self):
        """Non-singleton outcome dimensions (dimension larger one)"""
        return tuple(lt.shape[1] for lt in self._lt if lt.shape[1] > 1)

    @property
    def nsoutpos(self):
        """Sites with non-singleton outcome dimension (dimension larger one)"""
        return tuple(k for k, lt in enumerate(self._lt) if lt.shape[1] > 1)

    @property
    def hdims(self):
        """Local Hilbert space dimensions"""
        # Second physical leg dimension (equals third physical leg dimension)
        return tuple(lt.shape[2] for lt in self._lt)

    @property
    def elements(self):
        """Returns an iterator over all POVM elements. The result is the i-th
        POVM element in MPO form.

        It would be nice to call this method `__iter__`, but this
        breaks `mp.dot(mppovm, ...)`. In addition,
        `next(iter(mppovm))` would not be equal to `mppovm[0]`.

        """
        return self.paxis_iter(axes=0)

    @property
    def probability_map(self):
        """Map that takes a raveled MPDO to the POVM probabilities

        You can use :func:`MPPovm.expectations()` or
        :func:`MPPovm.pmf()` as convenient wrappers around this map.

        If `rho` is a matrix product density operator (MPDO), then

        .. code::

            mp.dot(a_povm.probability_map, rho.ravel())

        produces the POVM probabilities as MPA (similar to
        :func:`mpnum.povm.localpovm.POVM.probability_map`).

        """
        # See :func:`.localpovm.POVM.probability_map` for explanation
        # of the transpose.
        return self.transpose((0, 2, 1)).reshape(
            (pdim[0], -1) for pdim in self.pdims)

    @classmethod
    def from_local_povm(cls, lelems, width):
        """Generates a product POVM on `width` sites.

        :param lelems: POVM elements as an iterator over all local elements
            (i.e. an iterator over numpy arrays representing the latter)
        :param int width: Number of sites the POVM lives on
        :returns: :class:`MPPovm` which is a product POVM of the `lelems`

        """
        return cls.from_kron(it.repeat(lelems, width))

    @classmethod
    def eye(cls, local_dims):
        """Construct MP-POVM with no output or measurement

        Corresponds to taking the partial trace of the quantum state
        and a shorter MP-POVM.

        :param local_dims: Iterable of local dimensions

        """
        return cls.from_kron(
            (np.eye(dim).reshape((1, dim, dim)) for dim in local_dims))

    def embed(self, nr_sites, startsite, local_dim):
        """Embed MP-POVM into larger system

        Applying the resulting embedded MP-POVM to a state `rho` gives
        the same result as applying the original MP-POVM `self` on the
        reduced state of sites `range(startsite, startsite +
        len(self))` of `rho`.

        :param nr_sites: Number of sites of the resulting MP-POVM
        :param startsite: Position of the first site of `self` in the
            resulting MP-POVM
        :param local_dim: Local dimension of sites to be added

        :returns: MP-POVM with `self` on sites `range(startsite,
            startsite + len(self))` and :func:`MPPovm.eye()` elsewhere

        """
        n_right = nr_sites - len(self) - startsite
        factors = []
        if startsite > 0:
            factors.append(MPPovm.eye([local_dim] * startsite))
        factors.append(self)
        if n_right > 0:
            factors.append(MPPovm.eye([local_dim] * n_right))
        return mp.outer(factors)

    def block(self, nr_sites):
        """Embed an MP-POVM on local blocks

        The returned :class:`MPPovmList` will contain `self` embedded
        at every possible position on `len(self)` neighbouring sites
        in a chain of length `nr_sites`. The remaining sites are not
        measured (:func:`self.embed()`).

        `self` must a have a uniform local Hilbert space dimension.

        :param nr_sites: Number of sites of the resulting MP-POVMs

        """
        local_dim = self.hdims[0]
        assert all(d == local_dim for d in self.hdims), \
            "Blocking requires uniform local Hilbert space dimension"
        return MPPovmList(
            self.embed(nr_sites, startsite, local_dim)
            for startsite in range(nr_sites - len(self) + 1)
        )

    def repeat(self, nr_sites):
        """Construct a longer MP-POVM by repetition

        The resulting POVM will have length `nr_sites`. If `nr_sites`
        is not an integer multiple of `len(self)`, `self` must
        factorize (have bond dimension one) at the position where it
        will be cut. For example, consider the tensor product MP-POVM
        of Pauli X and Pauli Y. Calling `repeat(nr_sites=5)` will
        construct the tensor product POVM XYXYX:

        >>> import mpnum as mp
        >>> import mpnum.povm as mpp
        >>> x, y = (mpp.MPPovm.from_local_povm(lp(3), 1) for lp in
        ...         (mpp.x_povm, mpp.y_povm))
        >>> xy = mp.outer([x, y])
        >>> xyxyx = mp.outer([x, y, x, y, x])
        >>> mp.norm(xyxyx - xy.repeat(5)) <= 1e-10
        True

        """
        n_repeat, n_last = nr_sites // len(self), nr_sites % len(self)
        if n_last > 0:
            assert self.bdims[n_last - 1] == 1, \
                "Partial repetition requires factorizing MP-POVM"
        return mp.outer([self] * n_repeat
                        + ([MPPovm(self.lt[:n_last])] if n_last > 0 else []))

    def expectations(self, mpa, mode='auto'):
        """Computes the exp. values of the POVM elements with given state

        :param mpa: State given as MPDO, MPS, or PMPS
        :param mode: In which form `mpa` is given. Possible values: 'mpdo',
            'pmps', 'mps', or 'auto'. If 'auto' is passed, we choose between
            'mps' or 'mpdo' depending on the number of physical legs
        :returns: Iterator over the expectation values, the n-th element is
            the expectation value correponding to the reduced state on sites
            [n,...,n + len(self) - 1]

        """
        assert len(self) <= len(mpa)
        if mode == 'auto':
            if all(pleg == 1 for pleg in mpa.plegs):
                mode = 'mps'
            elif all(pleg == 2 for pleg in mpa.plegs):
                mode = 'mpdo'

        pmap = self.probability_map

        if mode == 'mps':
            if len(self) == len(mpa):
                # The transpose in pmap does not matter for the reshape
                pmap = pmap.reshape(self.pdims)
                # Avoid MPS-to-MPO conversion. Depending on the bond
                # dimension, this can save a lot of runtime.
                yield mp.dot(mp.dot(pmap, mpa.conj()), mpa)
                return
            for psi_red in mpsmpo.reductions_mps_as_pmps(mpa, len(self)):
                rho_red = mpsmpo.pmps_to_mpo(psi_red)
                yield mp.dot(pmap, rho_red.ravel())
            return
        elif mode == 'mpdo':
            for rho_red in mpsmpo.reductions_mpo(mpa, len(self)):
                yield mp.dot(pmap, rho_red.ravel())
            return
        elif mode == 'pmps':
            for psi_red in mpsmpo.reductions_pmps(mpa, len(self)):
                rho_red = mpsmpo.pmps_to_mpo(psi_red)
                yield mp.dot(pmap, rho_red.ravel())
            return
        elif mode == 'mpscc':
            # TODO Refactor in order to avoid the "to_array()/weighted
            # sum/from_array()" sequence in this part.
            assert isinstance(mpa, _MPSCC)
            out = [0.0] * (len(mpa.mps[0]) - len(self) + 1)
            for weight, mps in zip(mpa.weights, mpa.mps):
                for pos, pmf in enumerate(self.expectations(mps, 'mps')):
                    out[pos] += weight * pmf.to_array()
            for pmf in out:
                yield mp.MPArray.from_array(pmf, plegs=1)
        else:
            raise ValueError("Could not understand data dype.")

    def pmf(self, state, mode='auto'):
        """Compute the POVM's probability mass function for `state`

        If you want to compute the probabilities for reduced states of
        `state`, you can use :func:`MPPovm.expectations()` instead of
        this function.

        :param mp.MPArray state: A quantum state as MPA. Must have the
            same length as `self`.
        :param mode: `'mps'`, `'mpdo'` or `'pmps'`. See
            :func:`MPPovm.expectations()`.

        :returns: Probabilities as MPArray

        """
        assert len(self) == len(state)
        return next(self.expectations(state, mode))

    def pmf_as_array(self, state, mode='auto', eps=1e-10):
        """Compute the POVM's PMF for `state` as full array

        Parameters: See :func:`MPPovm.pmf`.

        :returns: PMF as shape `self.nsoutdims` ndarray

        The resulting (real or complex) probabilities `pmf` are passed
        through :func:`check_pmf(pmf, eps, eps)
        <mpnum._tools.check_pmf>` before being returned.

        """
        assert len(self) == len(state)
        pmf = mp.prune(next(self.expectations(state, mode)), True).to_array()
        return check_pmf(pmf, eps, eps)

    def match_elems(self, other, exclude_dup=(), eps=1e-10):
        """Find POVM elements in `other` which have information on `self`

        We find all POVM sites in `self` which have only one possible
        outcome. We discard these outputs in `other` and afterwards
        check `other` and `self` for any common POVM elements.

        :param other: Another MPPovm
        :param exclude_duplicates: Sequence which can include `'self'`
            or `'other'` (or both) to assert that there are no
            linearly dependent pairs of elements in `self` or `other`.
        :param eps: Threshould for values which should be treated as zero

        :returns: (`matches`, `prefactors`)

        `matches[i_1, ..., i_k, j_1, ..., j_k]` specifies whether
        outcome `(i_1, ..., i_k)` of `self` has the same POVM element
        as the partial outcome `(j_1, ..., j_k)` of `other`; outcomes
        are specified only on the sites mentioned in `sites` such that
        `k = len(sites)`.

        `prefactors[i_1, ..., i_k, j_1, ..., j_k]` specifies how samples
        from `other` have to be weighted to correspond to samples for
        `self`.

        """
        # FIXME Refactor this method into shorter functions.
        if self.hdims != other.hdims:
            raise ValueError('Incompatible input Hilbert space: {!r} vs {!r}'
                             .format(self.hdims, other.hdims))
        if len(exclude_dup) > 0:
            assert {'self', 'other'}.issuperset(exclude_duplicates)
        # Drop measurement outcomes in `other` if there is only one
        # measurement outcome in `self`
        keep_outdims = (outdim > 1 for outdim in self.outdims)
        tr = mp.MPArray.from_kron([
            np.eye(outdim, dtype=lt.dtype)
            if keep else np.ones((1, outdim), dtype=lt.dtype)
            for keep, lt, outdim in zip(keep_outdims, other.lt, other.outdims)
        ])
        other = MPPovm(mp.dot(tr, other).lt)

        # Compute all inner products between elements from self and other
        inner = mp.dot(self.conj(), other,
                       axes=((1, 2), (1, 2)), astype=mp.MPArray)
        # Compute squared norms of all elements from inner products
        snormsq = mp.dot(self.conj(), self,
                         axes=((1, 2), (1, 2)), astype=mp.MPArray)
        eye3d = mp.MPArray.from_kron(
            # Drop inner products between different elements
            np.fromfunction(lambda i, j, k: (i == j) & (j == k), [outdim] * 3)
            for outdim in self.outdims
        )
        snormsq = mp.dot(eye3d, snormsq, axes=((1, 2), (0, 1)))
        onormsq = mp.dot(other.conj(), other,
                         axes=((1, 2), (1, 2)), astype=mp.MPArray)
        eye3d = mp.MPArray.from_kron(
            # Drop inner products between different elements
            np.fromfunction(lambda i, j, k: (i == j) & (j == k), [outdim] * 3)
            for outdim in other.outdims
        )
        onormsq = mp.dot(eye3d, onormsq, axes=((1, 2), (0, 1)))
        inner = abs(mp.prune(inner, True).to_array_global())**2
        inner = inner.reshape(tuple(d for d in inner.shape if d > 1))
        snormsq = mp.prune(snormsq, True).to_array().real
        onormsq = mp.prune(onormsq, True).to_array().real
        assert (snormsq > 0).all()
        assert (onormsq > 0).all()
        assert inner.shape == snormsq.shape + onormsq.shape
        # Compute the product of the norms of each element from self and other
        normprod = np.outer(snormsq, onormsq).reshape(inner.shape)
        assert ((normprod - inner) / normprod >= -eps).all()
        # Equality in the Cauchy-Schwarz inequality implies that the
        # vectors are linearly dependent
        match = abs(inner/normprod - 1) <= eps

        n_sout = len(self.nsoutdims)
        # The two checks are quite indirect
        if 'self' in exclude_dup:
            assert (match.sum(tuple(range(n_sout))) <= 1).all(), \
                "Pair of linearly dependent POVM elements in `self`"
        if 'other' in exclude_dup:
            assert (match.sum(tuple(range(n_sout, match.ndim))) <= 1).all(), \
                "Pair of linearly dependent POVM elements in `other`"

        # Compute the prefactors by which matching elements differ
        snormsq_shape = snormsq.shape
        snormsq = snormsq.reshape(snormsq_shape + (1,) * onormsq.ndim)
        onormsq = onormsq.reshape((1,) * len(snormsq_shape) + onormsq.shape)
        prefactors = (snormsq / onormsq)**0.5
        assert prefactors.shape == match.shape
        prefactors[~match] = np.nan

        return match, prefactors

    @staticmethod
    def _sample_cond_single(rng, marginal_pmf, n_group, out, eps):
        """Single sample from conditional probab. (call :func:`self.sample`)"""
        n_sites = len(marginal_pmf[-1])
        # Probability of the incomplete output. Empty output has unit probab.
        out_p = 1.0
        # `n_out` sites of the output have been sampled. We will add
        # at most `n_group` sites to the output at a time.
        for n_out in range(0, n_sites, n_group):
            # Select marginal probability distribution on (at most)
            # `n_out + n_group` sites.
            p = marginal_pmf[min(n_sites, n_out + n_group)]
            # Obtain conditional probab. from joint `p` and marginal `out_p`
            p = p.get_phys(tuple(out[:n_out]) + (slice(None),) * (len(p) - n_out))
            p = check_pmf(mp.prune(p).to_array() / out_p, eps, eps)
            # Sample from conditional probab. for next `n_group` sites
            choice = rng.choice(p.size, p=p.flat)
            out[n_out:n_out + n_group] = np.unravel_index(choice, p.shape)
            # Update probability of the partial output
            out_p *= np.prod(p.flat[choice])
        # Verify we have the correct partial output probability
        p = marginal_pmf[-1].get_phys(tuple(out)).to_array()
        assert abs(p - out_p) <= eps

    @classmethod
    def _sample_cond(cls, rng, pmf, n_samples, n_group, out, eps):
        """Sample using conditional probabilities (call :func:`self.sample`)"""
        # marginal_pmf[k] will contain the marginal probability
        # distribution p(i_1, ..., i_k) for outcomes on sites 1, ..., k.
        marginal_pmf = [None] * (len(pmf) + 1)
        marginal_pmf[len(pmf)] = pmf
        for n_sites in reversed(range(len(pmf))):
            # Sum over outcomes on the last site
            p = marginal_pmf[n_sites + 1].sum([()] * (n_sites) + [(0,)])
            if n_sites > 0:  # p will be np.ndarray if no legs are left
                p = mp.prune(p)
            marginal_pmf[n_sites] = p
        assert abs(marginal_pmf[0] - 1.0) <= eps
        for i in range(n_samples):
            cls._sample_cond_single(rng, marginal_pmf, n_group, out[i, :], eps)

    def _sample_direct(self, rng, pmf, n_samples, out, eps):
        """Sample from full pmfilities (call :func:`self.sample`)"""
        pmf = check_pmf(mp.prune(pmf, singletons=True).to_array(), eps, eps)
        choices = rng.choice(pmf.size, n_samples, p=pmf.flat)
        for pos, c in enumerate(np.unravel_index(choices, pmf.shape)):
            out[:, pos] = c

    def sample(self, rng, state, n_samples, method='cond', n_group=1,
               mode='auto', pack=False, eps=1e-10):
        """Random sample from `self` on a quantum state

        :param mp.MPArray state: A quantum state as MPA (see `mode`)
        :param n_samples: Number of samples to create
        :param method: Sampling method (`'cond'` or `'direct'`, see below)
        :param n_group: Number of sites to sample at a time in
            conditional sampling.
        :param mode: Passed to :func:`MPPovm.expectations`
        :param eps: Threshold for small values to be treated as zero.

        Two different sampling methods are available:

        * Direct sampling (`method='direct'`): Compute probabilities
          for all outcomes and sample from the full probability
          distribution. Usually faster than conditional sampling for
          measurements on a small number of sites. Requires memory
          linear in the number of possible outcomes.

        * Conditional sampling (`method='cond'`): Sample outcomes on
          all sites by sampling from conditional outcome probabilities
          on at most `n_group` sites at a time. Requires memory linear
          in the number of outcomes on `n_group` sites. Useful for
          measurements which act on large parts of a system
          (e.g. Pauli X on each spin).

        :returns: ndarray `samples` with shape `(n_samples,
            len(self.nsoutdims))`

        The `i`-th sample is given by `samples[i, :]`. `samples[i, j]`
        is the outcome for the `j`-th non-singleton output dimension
        of `self`.

        """
        assert len(self) == len(state)
        pmf = mp.prune(self.pmf(state, mode), singletons=True)
        pmf_sum = pmf.sum()
        # For large numbers of sites, NaNs appear. Why?
        assert abs(pmf_sum.imag) <= eps
        assert abs(1.0 - pmf_sum.real) <= eps

        # The value 255 means "data missing". The values 0..254 are
        # available for measurement outcomes.
        assert all(dim <= 255 for dim in self.outdims)
        out = np.zeros((n_samples, len(pmf)), dtype=np.uint8)
        out[...] = 0xff
        if method == 'cond':
            self._sample_cond(rng, pmf, n_samples, n_group, out, eps)
        elif method == 'direct':
            self._sample_direct(rng, pmf, n_samples, out, eps)
        else:
            raise ValueError('Unknown method {!r}'.format(method))
        assert (out < np.array(self.nsoutdims)[None, :]).all()
        if pack:
            return self.pack_samples(out)
        return out

    def pack_samples(self, samples):
        """Pack samples into one integer per sample

        Store one sample in a single integer instead of a list of
        integers with length `len(self.nsoutdims)`. Example:

        >>> p = pauli_mpp(nr_sites=2, local_dim=2)
        >>> p.outdims
        (6, 6)
        >>> p.pack_samples(np.array([[0, 1], [1, 0], [1, 2], [5, 5]]))
        array([ 1,  6,  8, 35])

        """
        assert samples.ndim == 2
        assert samples.shape[1] == len(self.nsoutdims)
        return np.ravel_multi_index(samples.T, self.nsoutdims)

    def unpack_samples(self, samples):
        """Unpack samples into several integers per sample

        Inverse of :func:`MPPovm.pack_samples`. Example:

        >>> p = pauli_mpp(nr_sites=2, local_dim=2)
        >>> p.outdims
        (6, 6)
        >>> p.unpack_samples(np.array([0, 6, 7, 12]))
        array([[0, 0],
               [1, 0],
               [1, 1],
               [2, 0]], dtype=uint8)

        """
        assert samples.ndim == 1
        assert all(dim <= 255 for dim in self.outdims)
        return np.array(np.unravel_index(samples, self.nsoutdims)) \
                 .T.astype(np.uint8)

    def est_pmf(self, samples, normalize=True, eps=1e-10):
        """Estimate probability mass function from samples

        :param np.ndarray samples: `(n_samples, len(self.nsoutdims))`
            array of samples
        :param bool normalize: True: Return normalized probability
            estimates (default). False: Return integer outcome counts.
        :returns: Estimated probabilities as ndarray `est_pmf` with
            shape `self.nsoutdims`

        `n_samples * est_pmf[i1, ..., ik]` provides the number of
        occurences of outcome `(i1, ..., ik)` in `samples`.

        """
        n_samples = samples.shape[0]
        counts = np.zeros(self.nsoutdims, int)
        assert samples.shape[1] == counts.ndim
        for out_num in range(counts.size):
            out = np.unravel_index(out_num, counts.shape)
            counts[out] = (samples == np.array(out)[None, :]).all(1).sum()
        assert counts.sum() == n_samples
        if normalize:
            return counts / n_samples
        else:
            return counts

    @staticmethod
    def _matches(n_sites, supp, supp2, supp12, fun_out, fun_out2):
        # supp, supp2 and supp12 must be sorted in ascending order
        supp, supp2 = np.array(supp, int), np.array(supp2, int)
        out = np.zeros(n_sites, int)
        out[supp] = 1
        sel1 = np.flatnonzero(out[supp])
        union_pos1 = np.flatnonzero(out[supp12])
        out[supp2] = 1
        out[supp] = 0
        sel2 = np.flatnonzero(out[supp2])
        union_pos2 = np.flatnonzero(out[supp12])

        n1, n2 = fun_out.shape[0], fun_out2.shape[0]
        if len(supp) + len(supp2) == len(supp12):
            mpos1 = np.repeat(np.arange(n1), n2)
            mpos2 = np.tile(np.arange(n2), n1)
        else:
            out[:] = 0
            out[np.intersect1d(supp, supp2)] = 1
            sel1int = np.flatnonzero(out[supp])
            sel2int = np.flatnonzero(out[supp2])
            red_out = fun_out[:, sel1int].copy()
            red_out2 = fun_out2[:, sel2int].copy()
            mpos1, mpos2 = np.zeros((2, n1 * n2), int)
            n_matches = 0
            for pos, out in enumerate(red_out):
                mpos2_add = np.flatnonzero((red_out2 == out[None, :]).all(1))
                num_add = len(mpos2_add)
                mpos2[n_matches:n_matches + num_add] = mpos2_add
                mpos1[n_matches:n_matches + num_add] = pos
                n_matches += num_add
            mpos1, mpos2 = mpos1[:n_matches], mpos2[:n_matches]
        mout = np.zeros([len(mpos1), len(supp12)], dtype=np.uint8)
        mout[:, union_pos1] = fun_out[:, sel1][mpos1, :]
        mout[:, union_pos2] = fun_out2[:, sel2][mpos2, :]
        return mpos1, mpos2, mout

    def _lfun_direct(self, coeff, funs_list, state, mode, eps):
        """Implementation of :func:`lfun` which avoids computing the entire PMF

        :func:`lfun` below computes the entire PMF as an array which
        is a problem for large systems. Indeed, this in unnecessary if
        the list of functions is simple and small. This function
        provides a more efficient implementation for functions which
        declare that they compare the measurement outcome against a
        certain value on a certain support.

        """
        assert funs_list is not None, "to be implemented"
        funs = collections.OrderedDict()
        for pos, fun in enumerate(funs_list):
            try:
                s_funs = funs[fun.support]
            except KeyError:
                s_funs = funs[fun.support] = [[], []]
            s_funs[0].append(pos)
            s_funs[1].append(fun.outcome)
        for supp, (pos, outcomes) in funs.items():
            funs[supp] = (np.array(pos, int), np.array(outcomes, np.uint8))
        pmf = self.pmf(state, mode)
        n_sites = len(self)
        outdims = np.array(self.nsoutdims, int)
        ept = np.zeros(len(funs_list), float)
        ept[:] = np.nan
        cov = np.zeros([len(funs_list)] * 2, float)
        for supp, (fun_pos, fun_out) in funs.items():
            # Compute expectation value and second moment of each function
            s_pmf = pmf.sum([() if p in supp else (0,) for p in range(n_sites)])
            s_pmf = check_pmf(mp.prune(s_pmf).to_array(), eps, eps)
            assert (s_pmf.shape == outdims[np.array(supp)]).all()
            cov[fun_pos, fun_pos] = ept[fun_pos] = s_pmf[tuple(fun_out.T)]
            for supp2, (fun_pos2, fun_out2) in funs.items():
                if supp2 <= supp:
                    continue
                supp12 = np.union1d(supp, supp2)
                # Compute mixed second moments: For compatible observations,
                # the mixed second moment is the corresponding probability.
                mpos1, mpos2, matches = self._matches(
                    n_sites, supp, supp2, supp12, fun_out, fun_out2)
                mpos1, mpos2 = fun_pos[mpos1], fun_pos2[mpos2]
                s_pmf = pmf.sum([() if p in supp12 else (0,)
                                 for p in range(n_sites)])
                s_pmf = check_pmf(mp.prune(s_pmf).to_array(), eps, eps)
                p = s_pmf[tuple(matches.T)]
                cov[mpos1, mpos2] = p
                cov[mpos2, mpos1] = p
        assert not np.isnan(ept).any()
        cov -= np.outer(ept, ept)
        if coeff is None:
            return ept, cov

        # Expectation value
        est = np.inner(coeff, ept)
        # Variance
        var_est = np.inner(coeff, np.dot(cov, coeff))
        assert var_est >= -eps
        if var_est < 0:
            var_est = 0
        return est, var_est

    def lfun(self, coeff, funs, state, mode='auto', eps=1e-10):
        """Evaluate a linear combination of functions of POVM outcomes

        :param np.ndarray coeff: A length `n_funs` array with the
            coefficients of the linear combination. If `None`, return
            the estimated values of the individual functions and the
            estimated covariance matrix of the estimates.
        :param np.ndarray funs: A length `n_funs` sequence of
            functions. If `None`, the estimated function will be a
            linear function of the POVM probabilities.

        For further information, see also :ref:`mppovm-lfun-overview`.

        The parameters `state` and `mode` are passed to
        :func:`MPPovm.pmf`.

        :returns: `(value, var)`: Expectation value and variance of
            the expectation value

        """
        if hasattr(funs[0], 'support') and hasattr(funs[0], 'outcome'):
            return self._lfun_direct(coeff, funs, state, mode, eps)

        if mode == 'pmf_array':
            pmf = state
        else:
            pmf = mp.prune(self.pmf(state, mode), True).to_array()
            pmf = check_pmf(pmf, eps, eps)
        n_out = np.prod(self.nsoutdims)
        if funs is not None:
            out = np.array(np.unravel_index(range(n_out), self.nsoutdims)) \
                    .T.copy()
            fun_out = np.zeros((len(funs), n_out), float)
            fun_out[:] = np.nan
            for pos, fun in enumerate(funs):
                fun_out[pos, :] = fun(out)
        else:
            fun_out = np.eye(n_out, dtype=float)
        if coeff is not None:
            assert coeff.shape == (fun_out.shape[0],)
        w_fun_out = fun_out * pmf.ravel()[None, :]
        ept = w_fun_out.sum(1)
        # Covariance matrix of the functions
        cov = np.dot(fun_out, w_fun_out.T) - np.outer(ept, ept)
        if coeff is None:
            return ept, cov

        # Expectation value
        est = np.inner(coeff, ept)
        # Variance
        var_est = np.inner(coeff, np.dot(cov, coeff))
        assert var_est >= -eps
        if var_est < 0:
            var_est = 0
        return est, var_est

    def est_lfun(self, coeff, funs, samples, weights=None, eps=1e-10):
        """Estimate a linear combination of functions of POVM outcomes

        This function estimates the function with exact value given by
        :func:`MPPovm.lfun`; see there for description of the
        parameters `coeff` and `funs`.

        :param np.ndarray samples: A shape `(n_samples,
            len(self.nsoutdims))` with samples from `self`
        :param weights: A length `n_samples` array for weighted
            samples. You can submit counts by passing them as
            weights. The number of samples used in average and
            variance estimation is determined by `weights.sum()` if
            `weights` is given.

        :returns: `(est, var)`: Estimated value and estimated variance
            of the estimated value. For details, see
            :ref:`mppovm-lfun-overview`.

        """
        if funs is None:
            # In this special case, we could make the implementation faster.
            n_out = np.prod(self.nsoutdims)
            out = np.array(np.unravel_index(range(n_out), self.nsoutdims)) \
                    .T[:, None, :].copy()
            funs = [lambda s, pos=pos: (s == out[pos]).all(1)
                    for pos in range(n_out)]
        n_funs = len(funs)
        if coeff is not None:
            assert coeff.ndim == 1
            assert coeff.dtype.kind == 'f'
            assert coeff.shape[0] == n_funs
        assert samples.ndim == 2
        n_samples = n_avg_samples = samples.shape[0]
        assert samples.shape[1] == len(self.nsoutdims)
        if weights is not None:
            assert weights.dtype.kind in 'fiu'
            assert weights.shape == (n_samples,)
            assert (weights >= 0).all()
            # Number of samples used for taking averages -- may be
            # different from `n_samples = samples.shape[0]` e.g. if
            # counts have been put into the shape of samples.
            n_avg_samples = weights.sum()
        fun_out = np.zeros((n_funs, n_samples), float)
        fun_out[:] = np.nan
        for pos, fun in enumerate(funs):
            fun_out[pos, :] = fun(samples)
        # Expectation value of each function
        w_fun_out = fun_out if weights is None else fun_out * weights[None, :]
        ept = w_fun_out.sum(1) / n_avg_samples
        # Covariance matrix of the functions
        cov = np.dot(fun_out, w_fun_out.T) / n_avg_samples
        cov -= np.outer(ept, ept)
        # - Has the unbiased estimator larger MSE?
        # - Switch from function covariance to function estimate covariance
        cov *= (n_avg_samples / (n_avg_samples - 1)) / n_avg_samples
        if coeff is None:
            return ept, cov

        # Expectation value / estimate of the linear combination
        est = np.inner(coeff, ept)
        # Estimated variance
        var_est = np.inner(coeff, np.dot(cov, coeff))
        assert var_est >= -eps
        if var_est < 0:
            var_est = 0
        return est, var_est

    def _mppl_lfun_estimator(self, est_coeff, est_funs, other, n_samples,
                            coeff, eps):
        """Compute the estimator used by :func:`MPPovmList.estfun_from()`

        Used by :func:`MPPovmList._lfun_estimator()`.

        `est_coeff[i]` and `est_funs[i]` will specify an estimator in
        the format used by :func:`MPPovm.lfun()` on
        `other.mpps[i]`. This function adds the coefficients and
        functions necessary to estimate the linear function of `self`
        probabilities specified by `coeff`.

        :param est_coeff: Output parameter, tuple of lists
        :param est_funs: Output parameter, tuple of lists
        :param MPPovmList other: An MP-POVM list
        :param n_samples: `n_samples[i]` specifies the number of
            samples available for `other.mpps[i]`. They are used for a
            weighted average if a given `self` probability can be
            estimated from more than one MP-POVMs in
            `other`.
        :param coeff: A linear function of `self` probabilities is
            specified by `coeff`

        :returns: None (output is added to the parameters `est_coeff`
            and `est_fun`)

        """
        assert coeff.shape == self.nsoutdims
        n_nsout = len(self.nsoutdims)
        myout_n_samples = np.zeros(self.nsoutdims, int)
        fun_mpp = []
        fun_myout = []
        fun_coeff = []
        for pos, mpp, n_sam in zip(it.count(), other.mpps, n_samples):
            matches, prefactors = self.match_elems(mpp, eps=eps)
            nsoutdims = tuple(
                sdim for sdim, odim in zip(self.outdims, mpp.outdims) if odim > 1)
            support = tuple(pos for pos, d in enumerate(nsoutdims) if d > 1)
            assert matches.ndim == n_nsout + len(support)
            for outcomes in np.argwhere(matches):
                my_out, out = tuple(outcomes[:n_nsout]), outcomes[n_nsout:]
                # Append a function which matches on the output `out`
                # on sites specified by `support`.
                est_funs[pos].append(
                    lambda s, out=out[None, :], supp=support: (s[:, supp] == out).all(1))
                est_funs[pos][-1].support = support
                est_funs[pos][-1].outcome = out
                # To compute the final coefficient, we need to know
                # how many samples from (possibly many) `mpp`s have
                # contributed to a given probability specified by `my_out`.
                myout_n_samples[my_out] += n_sam
                fun_mpp.append(pos)
                fun_myout.append(my_out)
                # Coefficient:
                # 1. Initial coefficient of probability `my_out`.
                # 2. Weighted average, will be completed below
                # 3. Possibly different POVM element prefactor
                fun_coeff.append(coeff[my_out]                   # 1.
                                 * n_sam                         # 2.
                                 * prefactors[tuple(outcomes)])  # 3.
        for pos, myout, c in zip(fun_mpp, fun_myout, fun_coeff):
            # Complete the weighted average
            est_coeff[pos].append(c / myout_n_samples[myout])

    def _fill_outcome_mpa_holes(self, support, outcome_mpa):
        """Fill holes in an MPA on some of the outcome physical legs

        The dot product of `outcome_mpa` and `self` provides a sum
        over some or all elements of the POVM. The way sites are added
        to `outcome_mpa` implements the selection rule described in
        :func:`self._elemsum_identity()`.

        :param np.ndarray support: List of sites where `outcome_mpa`
            lives
        :param mp.MPArray outcome_mpa: An MPA with physical legs in
            agreement with `self.outdims` with some sites omitted

        :returns: An MPA with physical legs given by `self.outdims`

        """
        outdims = self.outdims
        assert len(support) == len(outcome_mpa)
        assert all(dim[0] == outdims[pos]
                   for pos, dim in zip(support, outcome_mpa.pdims))
        if len(support) == len(self):
            return outcome_mpa  # Nothing to do
        # `self` does not have outcomes on the entire chain. Need
        # to inject sites into `outcome_mpa` accordingly.
        hole_pos, hole_fill = zip(*(
            (pos, map(np.ones, outdims[l + 1:r]))
            for pos, l, r in zip(it.count(), (-1,) + support,
                                 support + (len(self),))
            if r - l > 1
        ))
        return mp.inject(outcome_mpa, hole_pos, None, hole_fill)

    def _elemsum_identity(self, support, given, eps):
        """Check whether a given subset of POVM elements sums to a multiple of
        the identity

        :param np.ndarray support: List of sites on which POVM
            elements are selected by `given`
        :param np.ndarray given: Whether a POVM element with a given
            index should be included (bool array)

        A POVM element specified by the compound index `(i_1, ...,
        i_n)` with `n = len(self)` is included if
        `given[i_(support[0]), ..., i_(support[k])]` is `True`.

        :returns: If the POVM elements sum to a fraction of the
            identity, return the fraction. Otherwise return `None`.

        """
        assert given.any(), "Some elements are required"
        any_missing = not given.all()
        given = self._fill_outcome_mpa_holes(
            support, mp.MPArray.from_array(given, plegs=1))
        elem_sum = mp.dot(given, self)
        eye = factory.eye(len(self), self.hdims)
        sum_norm, eye_norm = mp.norm(elem_sum), mp.norm(eye)
        norm_prod, inner = sum_norm * eye_norm, abs(mp.inner(elem_sum, eye))
        # Cauchy-Schwarz inequality must be satisfied
        assert (norm_prod - inner) / norm_prod >= -eps, "invalid value"
        if (norm_prod - inner) / norm_prod > eps:
            return None
        # Equality in the Cauchy-Schwarz inequality implies linear dependence
        fraction = sum_norm / eye_norm
        if any_missing:
            assert fraction < 1.0 + eps
        else:
            assert abs(fraction - 1.0) <= eps
        return fraction

    def est_pmf_from(self, other, samples, eps=1e-10):
        """Estimate PMF from samples of another MPPovm `other`

        If `other` does not provide information on all elements in
        `self`, we require that the elements in `self` for which
        information is provided sum to a multiple of the identity.

        Example: If we consider the MPPovm
        :func:`MPPovm.from_local_povm(x, n) <MPPovm.from_local_povm>`
        for given local POVMs `x`, it is possible to obtain counts for
        the Pauli X part of :func:`x = pauli_povm()
        <mpnum.povm.localpovm.pauli_povm>` from samples for :func:`x =
        x_povm() <mpnum.povm.localpovm.x_povm>`; this is also true if
        the latter is supported on a larger part of the chain.

        :param MPPovm other: Another MPPovm
        :param np.ndarray samples: `(n_samples, len(other.nsoutdims))`
            array of samples for `other`

        :returns: `(est_pmf, n_samples_used)`. `est_pmf`: Shape
            `self.nsoutdims` ndarray of normalized probability
            estimates; the sum over the available probability
            estimates is equal to the fraction of the identity
            obtained by summing the corresponding POVM
            elements. `n_samples_used`: Number of samples which have
            contributed to the PMF estimate.

        """
        assert len(self) == len(other)
        n_samples = samples.shape[0]
        assert samples.shape[1] == len(other.nsoutdims)
        match, prefactors = self.match_elems(other)
        other_support = tuple(
            pos for pos, (sdim, odim) in enumerate(
                (sdim, odim) for sdim, odim in zip(self.outdims, other.outdims)
                if odim > 1
            ) if sdim > 1
        )
        other_outdims = tuple(dim for dim in (
            other.nsoutdims[pos] for pos in other_support) if dim > 1)
        assert match.shape == self.nsoutdims + other_outdims

        n_nsout = len(self.nsoutdims)
        given = match.any(tuple(range(n_nsout, match.ndim)))
        if not given.any():
            est_pmf = np.zeros(self.nsoutdims, float)
            est_pmf[:] = np.nan
            return est_pmf, 0
        all_prefactor = self._elemsum_identity(self.nsoutpos, given, eps)
        assert all_prefactor is not None, (
            "Given subset of elements does not sum to multiple of identity; "
            "conversion not possible")

        samples = samples[:, other_support]
        n_samples_used = \
            match.reshape((np.prod(self.nsoutdims),) + other_outdims) \
            [(slice(None),) + tuple(samples.T)].any(0).sum()
        est_pmf = np.zeros(self.nsoutdims, float)
        for outcomes in np.argwhere(match):
            my_out, out = tuple(outcomes[:n_nsout]), outcomes[n_nsout:]
            count = (samples == out[None, :]).all(1).sum()
            est_pmf[my_out] += prefactors[tuple(outcomes)] * count / n_samples

        assert abs(est_pmf.sum() - all_prefactor) <= eps
        est_pmf[~given] = np.nan
        return est_pmf, n_samples_used

    def est_pmf_from_mpps(self, other, samples, eps=1e-10):
        """Estimate probability mass function from MPPovmList samples

        :param MPPovmList other: An :class:`MPPovmList` instance
        :param samples: Iterable of samples (e.g. from
            :func:`MPPovmList.samples()`)

        :returns: `(p_est, n_samples_used)`, both are shape
            `self.nsoutdims` ndarrays. `p_est` provides estimated
            probabilities and `n_samples_used` provides the effective
            number of samples used for each probability.

        """
        assert len(other.mpps) == len(samples)
        pmf_ests = np.zeros((len(other.mpps),) + self.nsoutdims, float)
        n_samples = np.zeros(len(other.mpps), int)
        for pos, other_mpp, other_samples in zip(it.count(), other.mpps, samples):
            pmf_ests[pos, ...], n_samples[pos] = self.est_pmf_from(
                other_mpp, other_samples, eps)
        n_out = np.prod(self.nsoutdims)
        pmf_ests = pmf_ests.reshape((len(other.mpps), n_out))
        given = ~np.isnan(pmf_ests)
        n_samples_used = (given * n_samples[:, None]).sum(0)
        # Weighted average over available estimates according to the
        # number of samples underlying each estimate. Probabilities
        # without any estimates produce 0.0 / 0 = nan in `pmf_est`.
        pmf_est = np.nansum(pmf_ests * n_samples[:, None], 0) / n_samples_used
        return (pmf_est.reshape(self.nsoutdims),
                n_samples_used.reshape(self.nsoutdims))


class MPPovmList:

    """A list of :class:`Matrix Product POVMs <MPPovm>`

    This class allows you to

    - Conveniently obtain samples and estimated or exact probabilities
      for a list of :class:`MPPovms <MPPovm>`
    - Estimate probabilities from samples for a different MPPovmList
    - Estimate linear functions of probabilities of an MPPovmList from
      samples for a different MPPovmList

    .. automethod:: __init__

    """

    def __init__(self, mppseq):
        """Construct a MPPovmList

        :param mppseq: An iterable of :class:`MPPovm` objects

        All MPPovms must have the same number of sites.

        """
        self.mpps = tuple(mppseq)
        assert all(len(mpp) == len(self.mpps[0]) for mpp in self.mpps)
        self.mpps = tuple(mpp if isinstance(mpp, MPPovm) else MPPovm(mpp)
                          for mpp in self.mpps)

    def block(self, nr_sites):
        """Embed MP-POVMs on local blocks

        This function calls :func:`MPPovm.block(nr_sites)` for each
        MP-POVM in the list. Embedded MP-POVMs at the same position
        appear consecutively in the returned list:

        >>> import mpnum as mp
        >>> import mpnum.povm as mpp
        >>> ldim = 3
        >>> x, y = (mpp.MPPovm.from_local_povm(lp(ldim), 1) for lp in
        ...         (mpp.x_povm, mpp.y_povm))
        >>> e = mpp.MPPovm.eye([ldim])
        >>> xx = mp.outer([x, x])
        >>> xy = mp.outer([x, y])
        >>> mppl = mpp.MPPovmList((xx, xy))
        >>> xxe = mp.outer([x, x, e])
        >>> xye = mp.outer([x, y, e])
        >>> exx = mp.outer([e, x, x])
        >>> exy = mp.outer([e, x, y])
        >>> expect = (xxe, xye, exx, exy)
        >>> [abs(mp.norm(a - b)) <= 1e-10
        ...  for a, b in zip(mppl.block(3).mpps, expect)]
        [True, True, True, True]

        """
        return MPPovmList(it.chain(*zip(*(m.block(nr_sites).mpps
                                          for m in self.mpps))))

    def repeat(self, nr_sites):
        """Construct longer MP-POVMs by repeating each MP-POVM

        This function calls :func:`MPPovm.repeat(nr_sites)
        <MPPovm.repeat>` for each MP-POVM in the list.

        For example, :func:`pauli_mpps()` for `local_dim > 3`
        (i.e. without Z) and two sites returns POVMs for the four
        tensor product observables XX, XY, YX and YY:

        >>> import mpnum as mp
        >>> import mpnum.povm as mpp
        >>> block_sites = 2
        >>> ldim = 3
        >>> x, y = (mpp.MPPovm.from_local_povm(lp(ldim), 1) for lp in
        ...         (mpp.x_povm, mpp.y_povm))
        >>> pauli = mpp.pauli_mpps(block_sites, ldim)
        >>> expect = (
        ...     mp.outer((x, x)),
        ...     mp.outer((x, y)),
        ...     mp.outer((y, x)),
        ...     mp.outer((y, y)),
        ... )
        >>> [abs(mp.norm(a - b)) <= 1e-10 for a, b in zip(pauli.mpps, expect)]
        [True, True, True, True]

        Calling `repeat(5)` then returns the following
        :class:`MPPovmList`:

        >>> expect = (
        ...     mp.outer((x, x, x, x, x)),
        ...     mp.outer((x, y, x, y, x)),
        ...     mp.outer((y, x, y, x, y)),
        ...     mp.outer((y, y, y, y, y)),
        ... )
        >>> [abs(mp.norm(a - b)) <= 1e-10 for a, b in zip(pauli.repeat(5).mpps, expect)]
        [True, True, True, True]

        """
        return MPPovmList(m.repeat(nr_sites) for m in self.mpps)

    def pmf(self, state, mode='auto'):
        """Compute the probability mass functions of all MP-POVMs

        :param state: A quantum state as MPA
        :param mode: Passed to :func:`MPPovm.expectations()`

        :returns: Iterator over probabilities as MPArrays

        """
        assert len(state) == len(self.mpps[0])
        for mpp in self.mpps:
            yield mpp.pmf(state, mode)

    def pmf_as_array(self, state, mode='auto', eps=1e-10):
        """Compute the PMF of all MP-POVMs as full arrays

        Parameters: See :func:`MPPovmList.pmf`. Sanity checks: See
        :func:`MPPovm.pmf_as_array`.

        :returns: Iterator over probabilities as ndarrays

        """
        assert len(state) == len(self.mpps[0])
        for mpp in self.mpps:
            yield mpp.pmf_as_array(state, mode, eps)

    def sample(self, rng, state, n_samples, method, n_group=1, mode='auto',
               pack=False, eps=1e-10):
        """Random sample from all MP-POVMs on a quantum state

        Parameters: See :func:`MPPovm.sample()`.

        Return value: Iterable of return values from
        :func:`MPPovm.sample()`.

        """
        for mpp in self.mpps:
            yield mpp.sample(rng, state, n_samples, method, n_group, mode, pack,
                             eps)

    def pack_samples(self, samples):
        """Pack samples into one integer per sample

        :returns: Iterator over output from :func:`MPPovm.pack_samples`

        """
        assert len(samples) == len(self.mpps)
        for s, mpp in zip(samples, self.mpps):
            yield mpp.pack_samples(s)

    def unpack_samples(self, samples):
        """Unpack samples into several integers per sample

        :returns: Iterator over output from :func:`MPPovm.unpack_samples`

        """
        assert len(samples) == len(self.mpps)
        for s, mpp in zip(samples, self.mpps):
            yield mpp.unpack_samples(s)

    def est_pmf(self, samples, normalized=True, eps=1e-10):
        """Estimate PMF from samples

        Returns an iterator over results from :func:`MPPovm.est_pmf()`
        (see there).

        """
        assert len(samples) == len(self.mpps)
        for mpp, sam in zip(self.mpps, samples):
            yield mpp.est_pmf(sam, normalized, eps)

    def est_pmf_from(self, other, samples, eps=1e-10):
        """Estimate PMF from samples of another MPPovmList

        :param MPPovmList other: A different MPPovmList
        :param samples: Samples from `other`

        :returns: Iterator over `(p_est, n_samples_used)` from
            :func:`MPPovm.est_pmf_from_mpps()`.

        """
        assert len(self.mpps[0]) == len(other.mpps[0])
        for mpp in self.mpps:
            yield mpp.est_pmf_from_mpps(other, samples, eps)

    def lfun(self, coeff, funs, state, mode='auto', eps=1e-10):
        """Evaluate a linear combination of functions of POVM outcomes

        `coeff[i]` and `funs[i]` are passed to :func:`MPPovm.lfun` on
        `self.mpps[i]`. `funs = None` is treated as `[None] *
        len(self.mpps)`. `state` and `mode` are passed to
        :func:`MPPovm.pmf`.

        :returns: `(value, var)`: Expectation value and variance of
            the expectation value

        """
        if funs is None:
            funs = (None,) * len(self.mpps)
        assert len(self.mpps) == len(coeff)
        assert len(self.mpps) == len(funs)
        est, var = zip(*(
            mpp.lfun(c, f, state, mode, eps)
            for mpp, c, f in zip(self.mpps, coeff, funs)))
        return sum(est), sum(var)

    def est_lfun(self, coeff, funs, samples, weights=None, eps=1e-10):
        """Estimate a linear combination of functions of POVM outcomes

        :param coeff: Iterable of coefficient lists
        :param funs: Iterable of function lists
        :param samples: Iterable of samples
        :param weights: Iterable of weight lists or `None`

        The `i`-th item from these parameters is passed to
        :func:`MPPovm.est_lfun` on `self.mpps[i].est_lfun`.

        :returns: (`est`, `var`): Estimated value `est` and estimated
            variance `var` of the estimate `est`

        """
        if funs is None:
            funs = (None,) * len(self.mpps)
        assert len(self.mpps) == len(coeff)
        assert len(self.mpps) == len(funs)
        assert len(self.mpps) == len(samples)
        est, var = zip(*(
            mpp.est_lfun(c, f, sam)
            for mpp, c, f, sam in zip(self.mpps, coeff, funs, samples)))
        return sum(est), sum(var)

    def _lfun_estimator(self, other, coeff, n_samples, eps):
        """Compute the estimator used by :func:`MPPovmList.est_lfun_from()`

        Parameters: See :func:`MPPovmList.est_lfun_from()` for `other`
        and `coeff`.  See :func:`MPPovm._mppl_lfun_estimator()` for
        `n_samples`.

        :returns: `(est_coeff, `est_funs`): `est_coeff[i]` and
            `est_funs[i]` specify an estimator in the format used by
            :func:`MPPovm.est_lfun()` on `other.mpps[i]`.

        This method aggregates the results from
        :func:`MPPovm._mppl_lfun_estimator()` on each `self.mpps[i]`.

        """
        assert len(n_samples) == len(other.mpps)
        assert len(coeff) == len(self.mpps)
        est_coeff = tuple([] for _ in range(len(other.mpps)))
        est_funs = tuple([] for _ in range(len(other.mpps)))
        for c, mpp in zip(coeff, self.mpps):
            mpp._mppl_lfun_estimator(est_coeff, est_funs, other, n_samples, c,
                                    eps=eps)
        return est_coeff, est_funs

    def lfun_from(self, other, coeff, state, mode='auto', other_weights=None,
                  eps=1e-10):
        """Evaluate a linear combination of POVM probabilities

        This function computes the same expectation value as
        :func:`MPPovmList.lfun` if supplied with `funs = None`, but it
        computes the variance for a different estimation procedure: It
        uses weighted averages of POVM probabilities from `other` to
        obtain the necessary POVM probabilities for `self` (the same
        is done in :func:`MPPovmList.est_lfun_from`).

        The parameter `coeff` is explained in
        :func:`MPPovmList.est_lfun_from`. `state` and `mode` are
        passed to :func:`MPPovm.pmf`.

        You can supply the array `other_weights` to determine the
        weighted average used when a probability in a POVM in `self`
        can be estimated from probabilities in multiple different
        POVMs in `other`.

        :returns: `(value, var)`: Expectation value and variance of
            the expectation value

        """
        if other_weights is None:
            other_weights = np.ones(len(other.mpps))
        coeff, funs = self._lfun_estimator(other, coeff, other_weights, eps)
        if mode == 'pmf_array_list':
            mode = 'pmf_array'
            state = iter(state)
        else:
            state = it.repeat(state)
        est, var = zip(*(
            mpp.lfun(np.array(c, float), f, next(state), mode, eps)
            for mpp, c, f in zip(other.mpps, coeff, funs)))
        return sum(est), sum(var)

    def est_lfun_from(self, other, coeff, samples, eps=1e-10):
        """Estimate a linear function from samples for another MPPovmList

        The function to estimate is a linear function of the
        probabilities of `self` and it is specified by `coeff`. Its
        true expectation value and variance are returned by
        :func:`MPPovmList.lfun_from`. First, an estimator is
        constructed using :func:`MPPovmList._lfun_estimator` and this
        estimator is passed to :func:`MPPovm.est_lfun` to obtain the
        estimate. See :ref:`mppovm-lfun-overview` for more details.

        :param MPPovmList other: Another MP-POVM list
        :param coeff: A sequence of shape `self.mpps[i].nsoutdims`
            coefficients which specify the function to estimate
        :param samples: A sequence of samples for `other`

        :returns: `(est, var)`: Estimated value and estimated variance
            of the estimated value

        """
        n_samples = [s.shape[0] for s in samples]
        est_coeff, funs = self._lfun_estimator(other, coeff, n_samples, eps)
        est, var = zip(*(
            mpp.est_lfun(np.array(c, float), f, s, eps=eps)
            for c, f, s, mpp in zip(est_coeff, funs, samples, other.mpps)))
        return sum(est), sum(var)


def pauli_mpp(nr_sites, local_dim):
    r"""Pauli POVM tensor product as MP-POVM

    The resulting MP-POVM will contain all tensor products of the
    elements of the local Pauli POVM from :func:`mpp.pauli_povm()`.

    :param int nr_sites: Number of sites of the returned MP-POVM
    :param int local_dim: Local dimension
    :rtype: MPPovm

    For example, for two qubits the `(1, 3)` measurement outcome is
    `minus X` on the first and `minus Y` on the second qubit:

    >>> nr_sites = 2
    >>> local_dim = 2
    >>> pauli = pauli_mpp(nr_sites, local_dim)
    >>> xy = np.kron([1, -1], [1, -1j]) / 2
    >>> xyproj = np.outer(xy, xy.conj())
    >>> proj = pauli.get_phys([1, 3], astype=mp.MPArray) \
    ...             .to_array_global().reshape((4, 4))
    >>> abs(proj - xyproj / 3**nr_sites).max() <= 1e-10
    True

    The prefactor `1 / 3**nr_sites` arises because X, Y and Z are in a
    single POVM.

    """
    from mpnum.povm import pauli_povm
    return MPPovm.from_local_povm(pauli_povm(local_dim), nr_sites)


def pauli_mpps(nr_sites, local_dim):
    """Pauli POVM tensor product as MP-POVM list

    The returned :class:`MPPovmList` contains all tensor products of
    the single-site X, Y (and Z if `local_dim == 2`) POVMs:

    >>> import mpnum as mp
    >>> import mpnum.povm as mpp
    >>> block_sites = 2
    >>> ldim = 3
    >>> x, y = (mpp.MPPovm.from_local_povm(lp(ldim), 1) for lp in
    ...         (mpp.x_povm, mpp.y_povm))
    >>> pauli = mpp.pauli_mpps(block_sites, ldim)
    >>> expect = (
    ...     mp.outer((x, x)),
    ...     mp.outer((x, y)),
    ...     mp.outer((y, x)),
    ...     mp.outer((y, y)),
    ... )
    >>> [abs(mp.norm(a - b)) <= 1e-10 for a, b in zip(pauli.mpps, expect)]
    [True, True, True, True]

    :param int nr_sites: Number of sites of the returned MP-POVMs
    :param int local_dim: Local dimension
    :rtype: MPPovmList

    """
    from mpnum.povm import pauli_parts
    parts = [MPPovm.from_local_povm(x, 1) for x in pauli_parts(local_dim)]
    return MPPovmList(mp.outer(factors)
                      for factors in it.product(parts, repeat=nr_sites))
