DEF RS_RNG_NAME = 'mrg32k3a'
DEF RS_RNG_JUMPABLE = 1

cdef extern from "distributions.h":

    cdef struct s_mrg32k3a_state:
        int64_t s10
        int64_t s11
        int64_t s12
        int64_t s20
        int64_t s21
        int64_t s22

    ctypedef s_mrg32k3a_state mrg32k3a_state

    cdef struct s_aug_state:
        mrg32k3a_state *rng
        binomial_t *binomial

        int has_gauss, shift_zig_random_int, has_uint32
        double gauss
        uint32_t uinteger
        uint64_t zig_random_int

    ctypedef s_aug_state aug_state

    cdef void set_seed(aug_state* state, uint64_t seed)

ctypedef mrg32k3a_state rng_t

ctypedef uint64_t rng_state_t

cdef object _get_state(aug_state state):
    return (state.rng.s10, state.rng.s11, state.rng.s12,
            state.rng.s20, state.rng.s21, state.rng.s22)

cdef object _set_state(aug_state *state, object state_info):
    state.rng.s10 = state_info[0]
    state.rng.s11 = state_info[1]
    state.rng.s12 = state_info[2]
    state.rng.s20 = state_info[3]
    state.rng.s21 = state_info[4]
    state.rng.s22 = state_info[5]

cdef object matrix_power_127(x, m):
    n = x.shape[0]
    # Start at power 1
    out = x.copy()
    current_pow = x.copy()
    for i in range(7):
        current_pow = np.mod(current_pow.dot(current_pow), m)
        out = np.mod(out.dot(current_pow), m)
    return out

m1 = np.int64(4294967087)
a12 = np.int64(1403580)
a13n = np.int64(810728)
A1 = np.array([[0, 1, 0], [0, 0, 1], [-a13n, a12, 0]], dtype=np.int64)
A1p = np.mod(A1, m1).astype(np.uint64)
A1_127 = matrix_power_127(A1p, m1)

a21 = np.int64(527612)
a23n = np.int64(1370589)
A2 = np.array([[0, 1, 0], [0, 0, 1], [-a23n, 0, a21]], dtype=np.int64)
m2 = np.int64(4294944443)
A2p = np.mod(A2, m2).astype(np.uint64)
A2_127 = matrix_power_127(A2p, m2)

cdef void jump_state(aug_state* state):
    # vectors s1 and s2
    s1 = np.array([state.rng.s10,state.rng.s11,state.rng.s12], dtype=np.uint64)
    s2 = np.array([state.rng.s20,state.rng.s21,state.rng.s22], dtype=np.uint64)

    # Advance the state
    s1 = np.mod(A1_127.dot(s1), m1)
    s2 = np.mod(A1_127.dot(s2), m2)

    # Restore state
    state.rng.s10 = s1[0]
    state.rng.s11 = s1[1]
    state.rng.s12 = s1[2]

    state.rng.s20 = s2[0]
    state.rng.s21 = s2[1]
    state.rng.s22 = s2[2]

DEF CLASS_DOCSTRING = """
RandomState(seed=None)

Container for L\'Ecuyer MRG32K3A pseudo random number generator.

MRG32K3A is a 32-bit implementation of L'Ecuyer's combined multiple
recursive generator ([1]_, [2]_). MRG32K3A has a period of 2**191 and
supports multiple streams (NOT IMPLEMENTED YET).

``mrg32k3a.RandomState`` exposes a number of methods for generating random
numbers drawn from a variety of probability distributions. In addition to the
distribution-specific arguments, each method takes a keyword argument
`size` that defaults to ``None``. If `size` is ``None``, then a single
value is generated and returned. If `size` is an integer, then a 1-D
array filled with generated values is returned. If `size` is a tuple,
then an array with that shape is filled and returned.

**No Compatibility Guarantee**

``mrg32k3a.RandomState`` does not make a guarantee that a fixed seed and a
fixed series of calls to ``mrg32k3a.RandomState`` methods using the same
parameters will always produce the same results. This is different from
``numpy.random.RandomState`` guarantee. This is done to simplify improving
random number generators.  To ensure identical results, you must use the
same release version.

Parameters
----------
seed : {None, int}, optional
    Random seed initializing the pseudo-random number generator.
    Can be an integer in [0, 2**64] or ``None`` (the default).
    If `seed` is ``None``, then ``mrg32k3a.RandomState`` will try to read data
    from ``/dev/urandom`` (or the Windows analogue) if available or seed from
    the clock otherwise.

Notes
-----
The state of the MRG32KA PRNG is represented by 6 64-bit integers.

This implementation is integer based and produces integers in the interval
:math:`[0, 2^{32}-209+1]`.  These are treated as if they 32-bit random integers.

**Parallel Features**

``mrg32k3a.RandomState`` can be used in parallel applications by
calling the method ``jump`` which advances the
the state as-if :math:`2^{127}` random numbers have been generated [3]_. This
allow the original sequence to be split so that distinct segments can be used
on each worker process. All generators should be initialized with the same
seed to ensure that the segments come from the same sequence.

>>> import randomstate.prng.mrg32k3a as rnd
>>> rs = [rnd.RandomState(12345) for _ in range(10)]
# Advance rs[i] by i jumps
>>> for i in range(10):
        rs[i].jump(i)


References
----------
.. [1] "Software developed by the Canada Research Chair in Stochastic
       Simulation and Optimization", http://simul.iro.umontreal.ca/
.. [2] Pierre L'Ecuyer, (1999) "Good Parameters and Implementations for
       Combined Multiple Recursive Random Number Generators.", Operations
       Research 47(1):159-164
.. [3] L'ecuyer, Pierre, Richard Simard, E. Jack Chen, and W. David Kelton.
       "An object-oriented random-number package with many long streams
       and substreams." Operations research 50, no. 6, pp. 1073-1075, 2002.
"""
