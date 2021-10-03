from setuptools import setup

setup(
    name='wumpy',
    version='0.0.1',
    description='Imagine an efficient and extensible Discord API wrapper',
    packages=['wumpy', 'wumpy.models', 'wumpy.rest', 'wumpy.interactions', 'wumpy.interactions.commands', 'wumpy.interactions.components'],
    install_requires=['aiohttp', 'anyio', 'typing_extensions', 'pynacl'],
    extras_require={'all': ['orjson']},
)
