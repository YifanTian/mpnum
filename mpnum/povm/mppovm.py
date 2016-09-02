# encoding: utf-8
from __future__ import absolute_import, division, print_function

import itertools as it
import numpy as np

import mpnum.factory as factory
import mpnum.mparray as mp
import mpnum.mpsmpo as mpsmpo
from mpnum import povm as mpp


class MPPovm(mp.MPArray):
    """MPArray representation of multipartite POVM

    There are two different ways to write down a POVM in matrix product form

    1) As a list of matrix product operators, where each entry corresponds to
        a single POVM element

    2) As a matrix proudct array with 3 physical legs:

                [POVM index, column index, row index]

        that is, the first physical leg of the MPArray corresponds to the index
        of the POVM element. This representation is especially helpful for
        computing expectation values with MPSs/MPDOs.

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

    @property
    def outdims(self):
        """Tuple of outcome dimensions"""
        # First physical leg dimension
        return tuple(lt.shape[1] for lt in self._ltens)

    @property
    def nsoutdims(self):
        """Tuple of non-singleton outcome dimensions (dimension larger one)"""
        return tuple(lt.shape[1] for lt in self._ltens if lt.shape[1] > 1)

    @property
    def hdims(self):
        """Tuple of local Hilbert space dimensions"""
        # Second physical leg dimension (equals third physical leg dimension)
        return tuple(lt.shape[2] for lt in self._ltens)

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
        :func:`MPPovm.probab()` as convenient wrappers around this
        map.

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
        left = MPPovm.eye([local_dim] * startsite)
        n_right = nr_sites - len(self) - startsite
        right = MPPovm.eye([local_dim] * n_right)
        return MPPovm(mp.outer([left, self, right]))

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
        >>> xy = mpp.MPPovm(mp.outer((x, y)))
        >>> xyxyx = mpp.MPPovm(mp.outer((x, y, x, y, x)))
        >>> mp.norm(xyxyx - xy.repeat(5)) <= 1e-10
        True

        """
        n_repeat, n_last = nr_sites // len(self), nr_sites % len(self)
        if n_last > 0:
            assert self.bdims[n_last - 1] == 1, \
                "Partial repetition requires factorizing MP-POVM"
        return MPPovm(mp.outer(
            [self] * n_repeat + ([mp.MPArray(self[:n_last])] if n_last > 0 else [])))

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
        else:
            raise ValueError("Could not understand data dype.")

    def probab(self, state, mode='auto'):
        """Compute probabilities of `state`

        If you want to compute the probabilities for reduced states of
        `state`, you can use :func:`self.expectations()` instead of
        this function.

        :param mp.MPArray state: A quantum state as MPA. Must have the
            same length as `self`.
        :param mode: `'mps'`, `'mpdo'` or `'pmps'`. See
            :func:`self.expectations()`.

        :returns: Probabilities as MPArray

        """
        assert len(self) == len(state)
        return next(self.expectations(state, mode))

    def find_matching_elements(self, other, exclude_dup=(), eps=1e-10):
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
            for keep, lt, outdim in zip(keep_outdims, other, other.outdims)
        ])
        other = MPPovm(mp.dot(tr, other))

        # Compute all inner products between elements from self and other
        inner = mp.dot(self.conj(), other, axes=((1, 2), (1, 2)))
        # Compute squared norms of all elements from inner products
        snormsq = mp.dot(self.conj(), self, axes=((1, 2), (1, 2)))
        eye3d = mp.MPArray.from_kron(
            # Drop inner products between different elements
            np.fromfunction(lambda i, j, k: (i == j) & (j == k), [outdim] * 3)
            for outdim in self.outdims
        )
        snormsq = mp.dot(eye3d, snormsq, axes=((1, 2), (0, 1)))
        onormsq = mp.dot(other.conj(), other, axes=((1, 2), (1, 2)))
        eye3d = mp.MPArray.from_kron(
            # Drop inner products between different elements
            np.fromfunction(lambda i, j, k: (i == j) & (j == k), [outdim] * 3)
            for outdim in other.outdims
        )
        onormsq = mp.dot(eye3d, onormsq, axes=((1, 2), (0, 1)))
        inner = abs(mp.prune(inner, True).to_array_global())**2
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
    def _sample_cond_single(rng, marginal_p, n_group, out, eps):
        """Single sample from conditional probab. (call :func:`self.sample`)"""
        n_sites = len(marginal_p[-1])
        # Probability of the incomplete output. Empty output has unit probab.
        out_p = 1.0
        # `n_out` sites of the output have been sampled. We will add
        # at most `n_group` sites to the output at a time.
        for n_out in range(0, n_sites, n_group):
            # Select marginal probability distribution on (at most)
            # `n_out + n_group` sites.
            p = marginal_p[min(n_sites, n_out + n_group)]
            # Obtain conditional probab. from joint `p` and marginal `out_p`
            p = p[tuple(out[:n_out]) + (slice(None),) * (len(p) - n_out)]
            p = mp.prune(p).to_array() / out_p
            assert (abs(p.imag) <= eps).all()
            p = p.real
            assert (p >= -eps).all()
            p[p < 0] = 0.0
            assert abs(p.sum() - 1.0) <= eps
            # Sample from conditional probab. for next `n_group` sites
            choice = rng.choice(p.size, p=p.flat)
            out[n_out:n_out + n_group] = np.unravel_index(choice, p.shape)
            # Update probability of the partial output
            out_p *= np.prod(p.flat[choice])
        # Verify we have the correct partial output probability
        p = marginal_p[-1][tuple(out)].to_array()
        assert abs(p - out_p) <= eps

    @classmethod
    def _sample_cond(cls, rng, probab, n_samples, n_group, out, eps):
        """Sample using conditional probabilities (call :func:`self.sample`)"""
        # marginal_p[k] will contain the marginal probability
        # distribution p(i_1, ..., i_k) for outcomes on sites 1, ..., k.
        marginal_p = [None] * (len(probab) + 1)
        marginal_p[len(probab)] = probab
        for n_sites in reversed(range(len(probab))):
            # Sum over outcomes on the last site
            p = marginal_p[n_sites + 1].sum([()] * (n_sites) + [(0,)])
            if n_sites > 0:  # p will be np.ndarray if no legs are left
                p = mp.prune(p)
            marginal_p[n_sites] = p
        assert abs(marginal_p[0] - 1.0) <= eps
        for i in range(n_samples):
            cls._sample_cond_single(rng, marginal_p, n_group, out[i, :], eps)

    def _sample_direct(self, rng, probab, n_samples, out, eps):
        """Sample from full probabilities (call :func:`self.sample`)"""
        probab = mp.prune(probab, singletons=True).to_array()
        assert (abs(probab.imag) <= eps).all()
        probab = probab.real
        assert (probab >= -eps).all()
        probab[probab < 0] = 0.0
        assert abs(probab.sum() - 1.0) <= eps
        choices = rng.choice(probab.size, n_samples, p=probab.flat)
        for pos, c in enumerate(np.unravel_index(choices, probab.shape)):
            out[:, pos] = c

    def sample(self, rng, state, n_samples, method='cond', n_group=1,
               mode='auto', eps=1e-10):
        """Sample from `self` on a quantum state

        :param mp.MPArray state: A quantum state as MPA (see `mode`)
        :param n_samples: Number of samples to create
        :param method: Sampling method (`'cond'` or `'direct'`, see below)
        :param n_group: Number of sites to sample at a time in
            conditional sampling.
        :param mode: Passed to :func:`self.expectations`
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
        probab = mp.prune(self.probab(state, mode), singletons=True)
        probab_sum = probab.sum()
        # For large numbers of sites, NaNs appear. Why?
        assert abs(probab_sum.imag) <= eps
        assert abs(1.0 - probab_sum.real) <= eps

        # The value 255 means "data missing". The values 0..254 are
        # available for measurement outcomes.
        assert all(dim <= 255 for dim in self.outdims)
        out = np.zeros((n_samples, len(probab)), dtype=np.uint8)
        out[...] = 0xff
        if method == 'cond':
            self._sample_cond(rng, probab, n_samples, n_group, out, eps)
        elif method == 'direct':
            self._sample_direct(rng, probab, n_samples, out, eps)
        else:
            raise ValueError('Unknown method {!r}'.format(method))
        assert (out < np.array(self.nsoutdims)[None, :]).all()
        return out

    def est_fun(self, coeff, funs, samples, weights=None, eps=1e-10):
        """Estimate a linear combination of functions of the POVM outcomes

        :param np.ndarray coeff: A length `n_funs` array with the
            coefficients of the linear combination
        :param np.ndarray funs: A length `n_funs` sequence of functions
        :param np.ndarray samples: A shape `(n_samples,
            len(self.nsoutdims))` with samples from `self`
        :param weights: A length `n_samples` array for weighted
            samples. You can submit counts by passing them as
            weights. The number of samples used in average and
            variance estimation is determined by `weights.sum()` if
            `weights` is given.

        :returns: `(est, var)`: Estimated value and estimated variance
            of the estimated value

        """
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

    def _estfun_from_estimator(self, est_coeff, est_funs, other, n_samples,
                               coeff, eps):
        """Compute the estimator used by :func:`MPPovmList.estfun_from()`

        Used by :func:`MPPovmList._estfun_from_estimator()`.

        `est_coeff[i]` and `est_funs[i]` will specify an estimator in
        the format used by :func:`MPPovm.est_fun()` on
        `other.mpps[i]`. This functions adds the coefficients and
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
        support = tuple(pos for pos, dim in enumerate(self.outdims) if dim > 1)
        n_nsout = len(self.nsoutdims)
        myout_n_samples = np.zeros(self.nsoutdims, int)
        fun_mpp = []
        fun_myout = []
        fun_coeff = []
        for pos, mpp, n_sam in zip(it.count(), other.mpps, n_samples):
            matches, prefactors = self.find_matching_elements(mpp, eps=eps)
            for outcomes in np.argwhere(matches):
                my_out, out = tuple(outcomes[:n_nsout]), outcomes[n_nsout:]
                # Append a function which matches on the output `out`
                # on sites specified by `support`.
                est_funs[pos].append(
                    lambda s, out=out[None, :]: (s[:, support] == out).all(1))
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

    def _fill_out_holes(self, support, outcome_mpa):
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
        i_n)` with `n = len(self` is included if
        `given[i_(support[0]), ..., i_(support[k])]` is `True`.

        :returns: If the POVM elements sum to a fraction of the
            identity, return the fraction. Otherwise return `None`.

        """
        assert given.any(), "Some elements are required" 
        any_missing = not given.all()
        given = self._fill_out_holes(
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
        all_prefactor = sum_norm / eye_norm
        if any_missing:
            assert all_prefactor < 1.0 + eps
        else:
            assert abs(all_prefactor - 1.0) <= eps
        return all_prefactor

    def counts_from(self, other, samples, eps=1e-10):
        """Obtain counts from samples of another MPPovm `other`

        If `other` does not provide information on all elements in
        `self`, we require that the elements in `self` for which
        information is provided sum to a multiple of the identity.

        Example: If we consider the MPPovm
        :func:`MPPovm.from_local_povm(x, n) <MPPovm.from_local_povm>`
        for given local POVMs `x`, it is possible to obtain counts for
        the Pauli X part of :func:`pauli_povm()
        <mpnum.povm.localpovm.pauli_povm>` from samples for
        :func:`x_povm() <mpnum.povm.localpovm.x_povm>`; this is also
        true if the latter is supported on a larger part of the chain.

        :param MPPovm other: Another MPPovm
        :param np.ndarray samples: `(n_samples, len(other.nsoutdims))`
            array of samples for `other`

        :returns: `(counts, n_samples_used)`. `counts`: Array of
            normalized outcome counts; the sum over the available
            counts is equal to the fraction of the identity given by
            the corresponding POVM elements. `n_samples_used`: Number
            of samples which have contributed to `counts`.

        """
        assert len(self) == len(other)
        n_samples = samples.shape[0]
        assert samples.shape[1] == len(other.nsoutdims)
        match, prefactors = self.find_matching_elements(other)
        support = tuple(pos for pos, dim in enumerate(self.outdims) if dim > 1)
        other_outdims = tuple(other.outdims[i] for i in support)
        assert match.shape == self.nsoutdims + other_outdims

        n_nsout = len(self.nsoutdims)
        given = match.any(tuple(range(n_nsout, match.ndim)))
        if not given.any():
            counts = np.zeros(self.nsoutdims, float)
            counts[:] = np.nan
            return counts, 0
        all_prefactor = self._elemsum_identity(support, given, eps)
        assert all_prefactor is not None, (
            "Given subset of elements does not sum to multiple of identity; "
            "conversion not possible")

        samples = samples[:, support]
        n_samples_used = \
            match.reshape((np.prod(self.nsoutdims),) + other_outdims) \
            [(slice(None),) + tuple(samples.T)].any(0).sum()
        counts = np.zeros(self.nsoutdims, float)
        for outcomes in np.argwhere(match):
            my_out, out = tuple(outcomes[:n_nsout]), outcomes[n_nsout:]
            count = (samples == out[None, :]).all(1).sum()
            counts[my_out] += prefactors[tuple(outcomes)] * count / n_samples

        assert abs(counts.sum() - all_prefactor) <= eps
        counts[~given] = np.nan
        return counts, n_samples_used

    def count_samples(self, samples, weights=None, eps=1e-10):
        """Count number of outcomes in samples

        :param np.ndarray samples: `(n_samples, len(self.nsoutdims))`
            array of samples
        :returns: ndarray `counts` with shape `self.nsoutdims`

        `counts[i1, ..., ik]` provides the number of occurences of
        outcome `(i1, ..., ik)` in `samples`.

        """
        n_samples = samples.shape[0]
        counts = np.zeros(self.nsoutdims, int)
        assert samples.shape[1] == counts.ndim
        for out_num in range(counts.size):
            out = np.unravel_index(out_num, counts.shape)
            counts[out] = (samples == np.array(out)[None, :]).all(1).sum()
        assert counts.sum() == n_samples
        return counts

    def estprob_from_mpplist(self, other, samples, eps=1e-10):
        """Estimate POVM probabilities from MPPovmList samples

        :param MPPovmList other: An :class:`MPPovmList` instance
        :param samples: Iterable of samples (e.g. from
            :func:`MPPovmList.samples()`)

        :returns: `(p_est, n_samples_used)`, both are shape
            `self.nsoutdims` ndarrays. `p_est` provides estimated
            probabilities and `n_samples_used` provides the effective
            number of samples used for each probability.

        """
        counts = np.zeros((len(other.mpps),) + self.nsoutdims, float)
        n_samples = np.zeros(len(other.mpps), int)
        for pos, other_mpp, other_samples in zip(it.count(), other.mpps, samples):
            counts[pos, ...], n_samples[pos] = self.counts_from(
                other_mpp, other_samples, eps)
        n_out = np.prod(self.nsoutdims)
        counts = counts.reshape((len(other.mpps), n_out))
        given = ~np.isnan(counts)
        n_samples_used = (given * n_samples[:, None]).sum(0)
        # Probabilities without any estimates produce 0.0 / 0 = nan.
        p_est = np.nansum(counts * n_samples[:, None], 0) / n_samples_used
        return p_est.reshape(self.nsoutdims), \
            n_samples_used.reshape(self.nsoutdims)


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
        >>> xx = mpp.MPPovm(mp.outer((x, x)))
        >>> xy = mpp.MPPovm(mp.outer((x, y)))
        >>> mppl = mpp.MPPovmList((xx, xy))
        >>> xxe = mpp.MPPovm(mp.outer((x, x, e)))
        >>> xye = mpp.MPPovm(mp.outer((x, y, e)))
        >>> exx = mpp.MPPovm(mp.outer((e, x, x)))
        >>> exy = mpp.MPPovm(mp.outer((e, x, y)))
        >>> expect = (xxe, xye, exx, exy)
        >>> [abs(mp.norm(a - b)) <= 1e-10 
        ...  for a, b in zip(mppl.block(3).mpps, expect)]
        [True, True, True, True]

        """
        return MPPovmList(it.chain(*zip(*(m.block(nr_sites).mpps
                                          for m in self.mpps))))

    def repeat(self, nr_sites):
        """Construct longer MP-POVMs by repeating each MP-POVM

        This function calls :func:`MPPovm.repeat(nr_sites)` for each
        MP-POVM in the list.

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

    def sample(self, rng, state, n_samples, method, n_group=1, mode='auto',
               eps=1e-10):
        """Sample from MPPovms on state

        Parameters: See :func:`MPPovm.sample()`.

        Return value: Iterable of return values from
        :func:`MPPovm.sample()`.

        """
        for mpp in self.mpps:
            yield mpp.sample(rng, state, n_samples, method, n_group, mode, eps)

    def estprob_from(self, other, samples, eps=1e-10):
        """Estimate POVM probabilities from MPPovmList samples

        :param MPPovmList other: A different MPPovmList
        :param samples: Samples from `other`

        :returns: Iterator over `(p_est, n_samples_used)` from
            :func:`MPPovm.estprob_from_mpps()`.

        .. todo:: Add a separate method to estimate from samples for
            `self`. This method should not be used if `other` is equal
            to `self`!

        """
        assert len(self.mpps[0]) == len(other.mpps[0])
        for mpp in self.mpps:
            yield mpp.estprob_from_mpps(other, samples, eps)

    def _estfun_from_estimator(self, other, coeff, n_samples, eps):
        """Compute the estimator used by :func:`self.estfun_from()`

        Parameters: See :func:`self.estfun_from()` for `other` and
        `coeff`.  See :func:`MPPovm._estfun_from_estimator()` for
        `n_samples`.

        :returns: `(est_coeff, `est_funs`): `est_coeff[i]` and
            `est_funs[i]` specify an estimator in the format used by
            :func:`MPPovm.est_fun()` on `other.mpps[i]`.

        This method aggregates the results from
        :func:`MPPovm._estfun_from_estimator()` on each
        `self.mpps[i]`.

        """
        assert len(n_samples) == len(other.mpps)
        assert len(coeff) == len(self.mpps)
        est_coeff = tuple([] for _ in range(len(other.mpps)))
        est_funs = tuple([] for _ in range(len(other.mpps)))
        for c, mpp in zip(coeff, self.mpps):
            mpp._estfun_from_estimator(est_coeff, est_funs, other, n_samples, c,
                                       eps=eps)
        return est_coeff, est_funs

    def estfun_from(self, other, coeff, samples, eps=1e-10):
        """Estimate a linear function from samples for another MPPovmList

        The function to estimate is a linear function of the
        probabilities of `self` and is specified by `coeff`.

        :param MPPovmList other: Another MP-POVM list
        :param coeff: A sequence of shape `self.mpps[i].nsoutdims`
            coefficients which specify the function to estimate
        :param samples: A sequence of samples for `other`

        :returns: `(est, var)`: Estimated value and estimated variance
            of the estimated value

        """
        n_samples = [s.shape[0] for s in samples]
        est_coeff, funs = self._estfun_from_estimator(other, coeff, n_samples,
                                                      eps)
        est, var = zip(*(
            mpp.est_fun(np.array(c, float), f, s, eps=eps)
            for c, f, s, mpp in zip(est_coeff, funs, samples, other.mpps)))
        return sum(est), sum(var)

    def probab(self, state, mode='auto'):
        """Compute probabilities

        :param state: A quantum state as MPA
        :param mode: Passed to :func:`MPPovm.expectations()`

        :returns: Iterator over shape probabilities as MPArrays

        """
        assert len(state) == len(self.mpps[0])
        for mpp in self.mpps:
            yield mpp.probab(state, mode)


def pauli_mpp(nr_sites, local_dim):
    """Pauli POVM tensor product as MP-POVM

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
    >>> proj = pauli[1, 3].to_array_global().reshape((4, 4))
    >>> abs(proj - xyproj / 3**nr_sites).max() <= 1e-10
    True

    The prefactor `1 / 3**nr_sites` arises because X, Y and Z are in a
    single POVM.

    """
    return MPPovm.from_local_povm(mpp.pauli_povm(local_dim), nr_sites)


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
    parts = [MPPovm.from_local_povm(x, 1) for x in mpp.pauli_parts(local_dim)]
    return MPPovmList(MPPovm(mp.outer(factors))
                      for factors in it.product(parts, repeat=nr_sites))
