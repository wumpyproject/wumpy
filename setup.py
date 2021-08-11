from setuptools import setup


setup(
    name='wumpy',
    version='0.0.1',
    description='Imagine an efficient and extensible Discord API wrapper',
    packages=['wumpy', 'wumpy.http', 'wumpy.models'],
    install_requires=['aiohttp', 'typing_extensions'],
    extras_require={'all': ['orjson']},
)
