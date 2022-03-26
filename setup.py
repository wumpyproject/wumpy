from setuptools import setup

# IMPORTANT: This is only for in-dev installation of the whole Git repository.
#            It has no stability guarantees and if possible, it is recommended
#            to 'cd' into each subpackage and install them with '--pth-file'
#            during development. This setuptools installation is only to allow
#            installation from git+https://github.com/wumpyproject/wumpy


with open('README.md', 'r', encoding='utf-8') as readme:
    long_description = readme.read()


setup(
    name='wumpy',

    # This version is not representative of Wumpy's real version, rather it is
    # set to satisfy and be explicit about versions.
    version='0.1.0a0',

    description='Discord API Wrapper - Easy enough for Wumpus, and fast enough for Clyde!',
    long_description=long_description,

    author='Bluenix',
    author_email='bluenixdev@gmail.com',

    packages=[
        'wumpy.bot', 'wumpy.cache', 'wumpy.gateway', 'wumpy.interactions',
        'wumpy.models', 'wumpy.rest',
    ],

    package_dir={
        'wumpy.bot': 'library/wumpy-bot/wumpy/bot',
        'wumpy.cache': 'library/wumpy-cache/wumpy/cache',
        'wumpy.gateway': 'library/wumpy-gateway/wumpy/gateway',
        'wumpy.interactions': 'library/wumpy-interactions/wumpy/interactions',
        'wumpy.models': 'library/wumpy-models/wumpy/models',
        'wumpy.rest': 'library/wumpy-rest/wumpy/rest',
    },

    # Sadly we have to duplicate these from the pyproject.toml files
    requires=[
        "anyio >= 3.3.4, < 4",
        "httpx[http2] >= 0.22, < 1",
        "discord-typings >= 0.4.0, <1",
        "discord-gateway >=0.3.0, <1",
        "pynacl > 1, < 2",
        "typing_extensions >= 4, <5",
    ],
)
