import pytest

from wumpy.interactions import ApplicationCommandOption, Option, option
from wumpy.interactions.commands.option import OptionClass
from wumpy.interactions.commands.registrar import CommandRegistrar


def test_option_func():
    original = OptionClass(
        'default', name='name', description='description',
        required=True, choices=['A', 'B', 'C'],
        type=ApplicationCommandOption.string
    )

    default = Option(
        'default', name='name', description='description',
        required=True, choices=['A', 'B', 'C'],
        type=ApplicationCommandOption.string
    )

    # These two should be identical

    assert original.name == default.name
    assert original.description == default.description
    assert original.required == default.required
    assert original.default == default.default
    assert original.choices == default.choices
    assert original.type == default.type


def test_option_func_min_max():
    original = OptionClass(
        'default', name='name', description='description',
        min=500, max=1000,
        type=ApplicationCommandOption.integer
    )

    default = Option(
        'default', name='name', description='description',
        min=500, max=1000,
        type=ApplicationCommandOption.integer
    )

    # These two should be identical

    assert original.name == default.name
    assert original.description == default.description
    assert original.default == default.default
    assert original.min == default.min
    assert original.max == default.max
    assert original.type == default.type


def test_option_deco():
    registrar = CommandRegistrar()

    @option(
        'other', name='else', type=str,
        choices={'Answer A': 'A', 'Answer B': 'B', 'Answer C': 'C'}
    )
    @option('arg', description='The only argument', type=int, min=0, max=10)
    @registrar.command()
    # The first argument will always be the interaction
    async def command(_, arg, other):
        ...

    assert command.options['arg'].description == 'The only argument'
    assert command.options['arg'].type == ApplicationCommandOption.integer
    assert command.options['arg'].min == 0
    assert command.options['arg'].max == 10

    # It should've been renamed now from 'other'
    assert command.options['else'].name == 'else'
    assert command.options['else'].type == ApplicationCommandOption.string
    assert command.options['else'].choices == {
        'Answer A': 'A', 'Answer B': 'B', 'Answer C': 'C'
    }


def test_option_deco_no_command():
    with pytest.raises(TypeError):
        @option('arg', choices=['A', 'B', 'C'])  # type: ignore
        async def not_command(arg):
            ...


def test_option_deco_no_param():
    registrar = CommandRegistrar()

    with pytest.raises(ValueError):
        @option('bad', description="Doesn't exist")
        @registrar.command()
        async def command(param):
            ...
