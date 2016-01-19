randomstate's documentation
===========================
This package contains a drop-in replacements for the NumPy RandomState object
that change the core random number generator.

What's New or Different
=======================
* ``random_uintegers`` produces either 32-bit or 64-bit unsigned integers.
  These are at the core of most PRNGs and so they are directly exposed.
* ``randomstate.entropy.random_entropy`` provides access to the system
  source of randomness that is used in cryptographic applications (e.g.,
  ``/dev/urandom`` on Unix).
* The normal generator supports a 256-step ziggurat method which is 2-6 times
  faster than NumPy's ``standard_normal``.  This generator can be accessed using

.. code-block:: python

  from randomstate import standard_normal
  standard_normal(100000, method='zig')


Supported Generators
====================
The main innovation is the inclusion of a number of alternative pseudo random number
generators, 'in addition' to the standard PRNG in NumPy.  The included PRNGs are:

* MT19937 - The standard NumPy generator.  Produces identical results to NumPy
  using the same seed/state. See `NumPy's documentation`_.
* dSFMT - A SSE2 enables version of the MT19937 generator.  Theoretically the
  same, but with a different state and so it is not possible to produce an
  sequence identical to MT19937. See the `dSFMT authors' page`_.
* XorShit128+ and XorShift1024* - Vast fast generators based on the XSadd
  generator. These generators can be rapidly 'jumped' and so can be used in
  parallel applications. See the documentation for
  :meth:`randomstate.prng.xorshift1024.jump` for details. More information
  about these PRNGs is available at the `xorshift authors' page`_.
* PCG-32 and PCG-64 - Fast generators that support many parallel streams and
  can be advanced by an arbitrary amount. See the documentation for
  :meth:`randomstate.prng.pcg64.advance`.  PCG-32 only as a period of
  :math:`2^{64}` while PCG-64 has a period of :math:`2^{128}`. See the
  `PCG author's page`_ for more details about this class of PRNG.
* Multiplicative Lagged Fibonacci Generator MLFG(1279, 861, \*) - A directly
  implemented multiplicative lagged Fibonacci generator with a very large
  period and good performance. Future plans include multiple stream support.
  See the `wiki page on Fibonacci generators`_.
* MRG32K3A - a classic and popular generator by L'Ecuyer. Future plans
  include multiple stream support. See the `MRG32K3A author's page`_. Lower
  performance than more modern generators.

.. _`NumPy's documentation`: http://docs.scipy.org/doc/numpy/reference/routines.random.html
.. _`dSFMT authors' page`: http://www.math.sci.hiroshima-u.ac.jp/~m-mat/MT/SFMT/
.. _`xorshift authors' page`:  http://xorshift.di.unimi.it/
.. _`PCG author's page`: http://www.pcg-random.org/
.. _`wiki page on Fibonacci generators`: https://en.wikipedia.org/wiki/Lagged_Fibonacci_generator
.. _`MRG32K3A author's page`: http://simul.iro.umontreal.ca/


RandomState Pseudo Random Number Generator Documentation:

.. toctree::
   :maxdepth: 2

   MT19937 <mt19937>
   dSFMT <dsfmt>
   XorShift128+ <xorshift128>
   XorShift1024* <xorshift1024>
   PCG-32 <pcg32>
   PCG-64 <pcg64>
   MLFG <mlfg>
   MRG32K3A <mrg32k3a>
   Reading System Entropy <entropy>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
