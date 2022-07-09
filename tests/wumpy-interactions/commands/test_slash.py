import pytest
from wumpy.interactions import (
    CommandInteraction, CommandRegistrar, Option, command_payload
)
from wumpy.models import ApplicationCommandOption


class TestSlashcommandInit:
    def test_doc(self):
        registrar = CommandRegistrar()

        @registrar.command()
        async def command(interaction):
            """Fitting description to this command."""
            ...

        assert command.description == 'Fitting description to this command.'

    def test_doc_not_override(self):
        registrar = CommandRegistrar()

        @registrar.command(description='Not overriden')
        async def command(interaction):
            """Overriden by docstring."""
            ...

        assert command.description == 'Not overriden'

    def test_multiline_doc(self):
        registrar = CommandRegistrar()

        @registrar.command()
        async def command(interaction):
            """This is the only part that should appear.

            This is just extra for the developers that can't be used in Discord
            because multiline descriptions don't make sense in the UI.
            """
            ...

        assert command.description == 'This is the only part that should appear.'

    def test_option_default(self):
        registrar = CommandRegistrar()

        @registrar.command()
        async def command(
            interaction,
            option: str = Option(
                None, description='Some option you can pass',
                required=False, choices=['X', 'Y', 'Z']
            ),
        ) -> None:
            """Command with an option containing choices."""
            ...

        assert command.options['option'].default is None
        assert command.options['option'].description == 'Some option you can pass'
        assert command.options['option'].required is False
        assert command.options['option'].choices == {'X': 'X', 'Y': 'Y', 'Z': 'Z'}

    def test_param_annotation(self):
        registrar = CommandRegistrar()

        @registrar.command()
        async def command(interaction: CommandInteraction, param: int, other: str):
            """Multi-parameter command."""
            ...

        assert command.options['param'].type == ApplicationCommandOption.integer
        assert command.options['other'].type == ApplicationCommandOption.string

    def test_wrong_interaction_annotation(self):
        registrar = CommandRegistrar()

        with pytest.raises(TypeError):
            @registrar.command()
            async def command(interaction: int):
                """Wrong interaction annotation."""
                ...


class TestCommandNesting:
    # These tests are quite heavy but they test some example command setup and
    # then the output of them when registering them for Discord.

    def test_subcommnad(self):
        registrar = CommandRegistrar()

        parent = registrar.group(name='parent', description='Family tree of commands')

        @parent.command()
        async def child(interaction, years: int = Option(description='How old the child is')):
            """Child subcommand of parent command."""
            ...

        @parent.command
        async def adult(
            interaction,
            kids: bool = Option(description='Whether the adults have kids of their own')
        ):
            """Adult subcommand of parent command."""
            ...

        assert command_payload(parent) == {
            'name': 'parent',
            'type': 1,
            'description': 'Family tree of commands',
            'options': [
                {
                    'name': 'child',
                    'type': 1,
                    'description': 'Child subcommand of parent command.',
                    'options': [{
                        'name': 'years',
                        'type': 4,
                        'description': 'How old the child is',
                        'required': True,
                    }],
                },
                {
                    'name': 'adult',
                    'type': 1,
                    'description': 'Adult subcommand of parent command.',
                    'options': [{
                        'name': 'kids',
                        'type': 5,
                        'description': 'Whether the adults have kids of their own',
                        'required': True,
                    }],
                },
            ],
        }

    def test_subcommandgroup(self):
        registrar = CommandRegistrar()

        parent = registrar.group(name='parent', description='Family tree of commands')

        pets = parent.group(name='pets', description='Group of pet subcommands')

        @pets.command()
        async def dog(
            interaction,
            puppy: bool = Option(description='Whether the dog is a puppy')
        ):
            """Woof woof subcommand."""
            ...

        @pets.command
        async def cat(
            interaction,
            claws: bool = Option(description='Whether the cat has claws')
        ):
            """Meow meow subcommand."""
            ...

        assert command_payload(parent) == {
            'name': 'parent',
            'type': 1,
            'description': 'Family tree of commands',
            'options': [
                {
                    'name': 'pets',
                    'type': 2,
                    'description': 'Group of pet subcommands',
                    'options': [
                        {
                            'name': 'dog',
                            'type': 1,
                            'description': 'Woof woof subcommand.',
                            'options': [{
                                'name': 'puppy',
                                'type': 5,
                                'description': 'Whether the dog is a puppy',
                                'required': True,
                            }],
                        },
                        {
                            'name': 'cat',
                            'type': 1,
                            'description': 'Meow meow subcommand.',
                            'options': [{
                                'name': 'claws',
                                'type': 5,
                                'description': 'Whether the cat has claws',
                                'required': True,
                            }],
                        },
                    ],
                },
            ],
        }
