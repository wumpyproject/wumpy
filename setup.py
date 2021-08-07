import os

from setuptools import setup

ext_modules = None
if 'SKIP_CYTHON' not in os.environ:
    try:
        from Cython.Build import cythonize
    except ImportError:
        pass
    else:
        # Cython was installed, so we can attempt to cythonize and compile the code.
        ext_modules = cythonize([
                'wumpy/models/base.py',
            ],
            language_level=3
        )


setup(
    name='wumpy',
    version='0.0.1',
    description='Imagine an efficient and extensible Discord API wrapper',
    packages=['wumpy'],
    ext_modules=ext_modules,
    extras_require={'all': ['Cython']},
)
