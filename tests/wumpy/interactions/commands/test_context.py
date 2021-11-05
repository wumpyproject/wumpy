import pytest

from wumpy.interactions import (
    CommandInteraction, CommandRegistrar, CommandType
)


@pytest.mark.parametrize('commandtype', [CommandType.message, CommandType.user])
class TestContextCommand:
    def test_no_annotation(self, commandtype: CommandType):
        registrar = CommandRegistrar()

        # For context menu commands there is only one possible annotation so
        # we get enough information from the command type.
        @registrar.command(commandtype)
        async def test(interaction, argument):
            ...

        assert registrar.commands['test'] == test

    def test_non_async(self, commandtype: CommandType):
        registrar = CommandRegistrar()

        with pytest.raises(TypeError):
            @registrar.command(commandtype)  # type: ignore
            def non_async(interaction, argument):
                ...

    def test_wrong_args(self, commandtype: CommandType):
        registrar = CommandRegistrar()

        with pytest.raises(TypeError):
            @registrar.command(commandtype)  # type: ignore
            async def no_args():
                ...

        with pytest.raises(TypeError):
            @registrar.command(commandtype)  # type: ignore
            async def too_many_args(interaction, argument, too_much):
                ...

    def test_bad_annotation(self, commandtype: CommandType):
        registrar = CommandRegistrar()

        with pytest.raises(TypeError):
            @registrar.command(commandtype)  # type: ignore
            async def int_arg(interaction: CommandInteraction, argument: int):
                ...

        with pytest.raises(TypeError):
            @registrar.command(commandtype)  # type: ignore
            async def str_arg(interaction: CommandInteraction, argument: str):
                ...

    def test_bad_interaction_annotation(self, commandtype: CommandType):
        registrar = CommandRegistrar()

        with pytest.raises(TypeError):
            @registrar.command(commandtype)  # type: ignore
            async def bad_annotation(interaction: str, argument):
                ...

    def test_argument_name(self, commandtype: CommandType):
        # The command should work no matter the names of the arguments
        registrar = CommandRegistrar()

        @registrar.command(commandtype)
        async def weird_arg_name(ctx: CommandInteraction, target):
            ...

    def test_kwarg(self, commandtype: CommandType):
        registrar = CommandRegistrar()

        with pytest.raises(TypeError):
            @registrar.command(commandtype)
            async def kwargs(*, interaction: CommandInteraction, argument):
                ...
