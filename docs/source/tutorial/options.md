# Command options

It is now time to explore options you can pass to commands, let's personalize our "hello"
command so that you can use the bot to greet someone.

## Simplest options

Let's add another subcommand to our "hello" command:

```python
from random import choice

from wumpy import interactions

app = interactions.InteractionApp(...)

hello = app.group(name='hello', description='Greeting commands')

@hello.subcommand()
async def random(interaction: interactions.CommandInteraction) -> None:
    """Greet with a random response."""
    await interaction.respond(choice(['Hello', 'Nice to see you']))

@hello.subcommand()
async def formal(interaction: interactions.CommandInteraction) -> None:
    """Make a formal greeting."""
    await interaction.respond('Good evening sir')

@hello.subcommand()
async def personal(interaction: interactions.CommandInteraction) -> None:
    """Make a personal greeting"""
    pass
```

Your code should look like this, let's focus on the `personal` command a bit more.

To add an option just add a parameter like this:

```python
@hello.subcommand()
async def personal(interaction: interactions.CommandInteraction, name: str) -> None:
    """Make a personal greeting"""
    pass
```

Wumpy will read the arguments and create options from that

This is missing some data Discord needs though and won't work. Discord needs at least a name
type and description, but a description is missing.s

=== "Parameter default"

    There are two ways to add this data, one of them is through adding a default to the
    parameter like this:

    ```python
    @hello.subcommand()
    async def personal(
        interaction: interactions.CommandInteraction,
        name: str = interactions.Option(description='Name to greet')
    ) -> None:
        """Make a personal greeting"""
        pass
    ```

=== "Decorator"

    There are two ways to add this data, one of them is through decorators. This has the
    benefit of leaving the function head free from clutter.

    ```python
    @interactions.option('name', description='Name to greet')
    @hello.subcommand()
    async def personal(
        interaction: interactions.CommandInteraction,
        name: str = None
    ) -> None:
        """Make a personal greeting"""
        pass
    ```

!!! info
    The function head got a little long, so it was split into multiple lines.

Let's finalize the command now, we can use the name to format a string.

The result should look like this:

=== "Parameter default"

    ```python
    @hello.subcommand()
    async def personal(
        interaction: interactions.CommandInteraction,
        name: str = interactions.Option(description='Name to greet')
    ) -> None:
        """Make a personal greeting"""
        await interaction.respond(f'Hello {name}')
    ```

=== "Decorator"

    ```python
    @interactions.option('name', description='Name to greet')
    @hello.subcommand()
    async def personal(interaction: interactions.CommandInteraction, name: str) -> None:
        """Make a personal greeting"""
        await interaction.respond(f'Hello {name}')
    ```

The documentation prefers parameter defaults and all code moving forward will be written in
that style, know that you can still use decorators if you want to.
