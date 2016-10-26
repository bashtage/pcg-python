import glob
import os
import shutil
import sys
from os.path import join
import subprocess
import struct

import numpy
from Cython.Build import cythonize
from setuptools import setup, find_packages
from setuptools.extension import Extension
from setuptools.dist import Distribution

try:
    import Cython.Tempita as tempita
except ImportError:
    try:
        import tempita
    except ImportError:
        raise ImportError('tempita required to install, '
                          'use pip install tempita')

FORCE_EMULATION = False
USE_SSE2 = True if not '--no-sse2' in sys.argv else False

mod_dir = './randomstate'
configs = []

rngs = ['RNG_DSFMT', 'RNG_MLFG_1279_861', 'RNG_MRG32K3A', 'RNG_MT19937',
        'RNG_PCG32', 'RNG_PCG64', 'RNG_XORSHIFT128', 'RNG_XOROSHIRO128PLUS',
        'RNG_XORSHIFT1024']

compile_rngs = rngs[:]

extra_defs = [('_CRT_SECURE_NO_WARNINGS','1')] if os.name == 'nt' else []
extra_link_args = ['/LTCG', 'Advapi32.lib', 'Kernel32.lib'] if os.name == 'nt' else []
base_extra_compile_args = [] if os.name == 'nt' else ['-std=c99']
if USE_SSE2:
    if os.name == 'nt':
        base_extra_compile_args += ['/wd4146','/GL']
        if struct.calcsize('P') < 8:
            base_extra_compile_args += ['/arch:SSE2']
    else:
        base_extra_compile_args += ['-msse2']


def write_config(file_name, config):
    flags = config['flags']
    with open(file_name, 'w') as config:
        config.write('# Autogenerated\n\n')
        for key in flags:
            val = flags[key]
            if isinstance(flags[key], str):
                val = '"' + val + '"'
            config.write('DEF ' + key + ' = ' + str(val) + '\n')


base_include_dirs = [mod_dir] + [numpy.get_include()]
if os.name == 'nt' and sys.version_info < (3, 5):
    base_include_dirs += [join(mod_dir, 'src', 'common')]

for rng in rngs:
    if rng not in compile_rngs:
        continue

    file_name = rng.lower().replace('rng_', '')
    flags = {'RS_RNG_MOD_NAME': file_name}
    sources = [join(mod_dir, file_name + '.pyx'),
               join(mod_dir, 'src', 'common', 'entropy.c'),
               join(mod_dir, 'distributions.c'),
               join(mod_dir, 'aligned_malloc.c')]
    include_dirs = base_include_dirs[:]
    extra_compile_args = base_extra_compile_args[:]

    if rng == 'RNG_PCG32':
        sources += [join(mod_dir, 'src', 'pcg', 'pcg32.c')]
        sources += [join(mod_dir, 'interface/pcg-32', 'pcg-32-shim.c')]

        defs = [('RS_PCG32', '1')]

        include_dirs += [join(mod_dir, 'src', 'pcg')]

    elif rng == 'RNG_PCG64':
        sources += [join(mod_dir, 'src', 'pcg64-compat', p) for p in ('pcg64.c',)]
        sources += [join(mod_dir, 'interface/pcg-64', 'pcg-64-shim.c')]

        defs = [('RS_PCG64', '1')]
        flags['RS_PCG128_EMULATED'] = 0
        if sys.maxsize < 2 ** 32 or os.name == 'nt' or FORCE_EMULATION:
            # Force emulated mode here
            defs += [('PCG_FORCE_EMULATED_128BIT_MATH', '1')]
            flags['RS_PCG128_EMULATED'] = 1
        else:
            # TODO: This isn't really right - should test for this and only
            # TODO: use this path if the compiler defines this. For now, an assumption.
            defs += [('__SIZEOF_INT128__', '16')]

        include_dirs += [join(mod_dir, 'src', 'pcg')]

    elif rng == 'RNG_MT19937':
        sources += [join(mod_dir, 'src', 'random-kit', p) for p in ('random-kit.c',)]
        sources += [join(mod_dir, 'interface', 'random-kit', 'random-kit-shim.c')]

        defs = [('RS_RANDOMKIT', '1')]

        include_dirs += [join(mod_dir, 'src', 'random-kit')]

    elif rng == 'RNG_XORSHIFT128':
        sources += [join(mod_dir, 'src', 'xorshift128', 'xorshift128.c')]
        sources += [join(mod_dir, 'interface', 'xorshift128', 'xorshift128-shim.c')]

        defs = [('RS_XORSHIFT128', '1')]

        include_dirs += [join(mod_dir, 'src', 'xorshift128')]
    elif rng == 'RNG_XORSHIFT1024':
        sources += [join(mod_dir, 'src', 'xorshift1024', 'xorshift1024.c')]
        sources += [join(mod_dir, 'interface', 'xorshift1024', 'xorshift1024-shim.c')]

        defs = [('RS_XORSHIFT1024', '1')]

        include_dirs += [join(mod_dir, 'src', 'xorshift1024')]
    elif rng == 'RNG_XOROSHIRO128PLUS':
        sources += [join(mod_dir, 'src', 'xoroshiro128plus', 'xoroshiro128plus.c')]
        sources += [join(mod_dir, 'interface', 'xoroshiro128plus', 'xoroshiro128plus-shim.c')]

        defs = [('RS_XOROSHIRO128PLUS', '1')]

        include_dirs += [join(mod_dir, 'src', 'xoroshiro128plus')]
    elif rng == 'RNG_MRG32K3A':
        sources += [join(mod_dir, 'src', 'mrg32k3a', 'mrg32k3a.c')]
        sources += [join(mod_dir, 'interface', 'mrg32k3a', 'mrg32k3a-shim.c')]

        defs = [('RS_MRG32K3A', '1')]

        include_dirs += [join(mod_dir, 'src', 'mrg32k3a')]

    elif rng == 'RNG_MLFG_1279_861':
        sources += [join(mod_dir, 'src', 'mlfg-1279-861', 'mlfg-1279-861.c')]
        sources += [join(mod_dir, 'interface', 'mlfg-1279-861', 'mlfg-1279-861-shim.c')]

        defs = [('RS_MLFG_1279_861', '1')]

        include_dirs += [join(mod_dir, 'src', 'mlfg_1279_861')]

    elif rng == 'RNG_DSFMT':
        sources += [join(mod_dir, 'src', 'dSFMT', 'dSFMT.c')]
        sources += [join(mod_dir, 'src', 'dSFMT', 'dSFMT-jump.c')]
        sources += [join(mod_dir, 'interface', 'dSFMT', 'dSFMT-shim.c')]
        # TODO: HAVE_SSE2 should only be for platforms that have SSE2
        # TODO: But how to reliably detect?
        defs = [('RS_DSFMT', '1'), ('DSFMT_MEXP', '19937')]
        if USE_SSE2:
            defs += [('HAVE_SSE2', '1')]

        include_dirs += [join(mod_dir, 'src', 'dSFMT')]

    config = {'file_name': file_name,
              'sources': sources,
              'include_dirs': include_dirs,
              'defs': defs,
              'flags': dict([(k, v) for k, v in flags.items()]),
              'compile_args': extra_compile_args
              }

    configs.append(config)


class BinaryDistribution(Distribution):
    def is_pure(self):
        return False


try:
    subprocess.call(['pandoc', '--from=markdown', '--to=rst', '--output=README.rst', 'README.md'])
except:
    pass
# Generate files and extensions
extensions = [Extension('randomstate.entropy',
                        sources=[join(mod_dir, 'entropy.pyx'),
                                 join(mod_dir, 'src', 'common', 'entropy.c')],
                        include_dirs=base_include_dirs,
                        define_macros=extra_defs,
                        extra_compile_args=base_extra_compile_args,
                        extra_link_args=extra_link_args)]

for config in configs:
    config_file_name = mod_dir + '/' + config['file_name'] + '-config.pxi'
    # Rewrite core_rng to replace generic #include "config.pxi"
    with open(join(mod_dir, 'randomstate.pyx'), 'r') as original:
        with open(join(mod_dir, config['file_name'] + '.pyx'), 'w') as mod:
            for line in original:
                if line.strip() == 'include "config.pxi"':
                    line = 'include "' + config_file_name + '"\n'
                mod.write(line)
    shutil.copystat(join(mod_dir, 'randomstate.pyx'), join(mod_dir, config['file_name'] + '.pyx'))
    # Write specific config file
    write_config(config_file_name, config)
    shutil.copystat(join(mod_dir, 'randomstate.pyx'), config_file_name)

    ext = Extension('randomstate.prng.' + config['file_name'] + '.' + config['file_name'],
                    sources=config['sources'],
                    include_dirs=config['include_dirs'],
                    define_macros=config['defs'] + extra_defs,
                    extra_compile_args=config['compile_args'],
                    extra_link_args=extra_link_args)
    extensions.append(ext)

# Do not run cythonize if clean
if 'clean' in sys.argv:
    def cythonize(e, *args, **kwargs):
        return e
else:
    files = glob.glob('./randomstate/*.in')
    for templated_file in files:
        output_file_name = os.path.splitext(templated_file)[0]
        with open(templated_file, 'r') as source_file:
            template = tempita.Template(source_file.read())
        with open(output_file_name, 'w') as output_file:
            output_file.write(template.substitute())

ext_modules = cythonize(extensions)

classifiers = ['Development Status :: 5 - Production/Stable',
               'Environment :: Console',
               'Intended Audience :: End Users/Desktop',
               'Intended Audience :: Financial and Insurance Industry',
               'Intended Audience :: Information Technology',
               'Intended Audience :: Science/Research',
               'License :: OSI Approved',
               'Operating System :: MacOS :: MacOS X',
               'Operating System :: Microsoft :: Windows',
               'Operating System :: POSIX :: Linux',
               'Operating System :: Unix',
               'Programming Language :: C',
               'Programming Language :: Cython',
               'Programming Language :: Python :: 2.6',
               'Programming Language :: Python :: 2.7',
               'Programming Language :: Python :: 3.3',
               'Programming Language :: Python :: 3.4',
               'Programming Language :: Python :: 3.5',
               'Topic :: Adaptive Technologies',
               'Topic :: Artistic Software',
               'Topic :: Office/Business :: Financial',
               'Topic :: Scientific/Engineering',
               'Topic :: Security :: Cryptography']

setup(name='randomstate',
      version='1.11.4',
      classifiers=classifiers,
      packages=find_packages(),
      package_dir={'randomstate': './randomstate'},
      package_data={'': ['*.c', '*.h', '*.pxi', '*.pyx', '*.pxd'],
                    'randomstate.tests.data': ['*.csv']},
      include_package_data=True,
      license='NSCA',
      author='Kevin Sheppard',
      author_email='kevin.k.sheppard@gmail.com',
      distclass=BinaryDistribution,
      description='Next-gen RandomState supporting multiple PRNGs',
      url='https://github.com/bashtage/ng-numpy-randomstate',
      long_description=open('README.rst').read(),
      ext_modules=ext_modules,
      keywords=['pseudo random numbers', 'PRNG', 'RNG', 'RandomState', 'random', 'random numbers',
                'parallel random numbers', 'PCG', 'XorShift', 'dSFMT', 'MT19937'],
      zip_safe=False)

# Clean up generated files
# exts = ('.pyx', '-config.pxi', '.c'),
# for config in configs:
#    for ext in exts:
#        file_path = join(mod_dir, config['file_name'] + ext)
#        if os.path.exists(file_path):
#            os.unlink(file_path)