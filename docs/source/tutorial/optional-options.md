# Optional options

On the last page you learned about options, but not all options are created equally.

Let's make the `name` parameter optional, and when it is missing fall back to the same
behaviour as when you first created the command.

## Making options optional

Let's look back on the "personal" subcommand before figuring out what you want to change.

```python
from wumpy import interactions

app = interactions.InteractionApp(...)

hello = app.group(name='hello', description='Greeting commands')

@hello.subcommand()
async def personal(
    interaction: interactions.CommandInteraction,
    name: str = interactions.Option(description='Name to greet')
) -> None:
    """Make a personal greeting"""
    await interaction.respond(f'Hello {name}')
```

!!! note
    Some commands are not shown because the bot is becoming rather big. You do not need to
    remove them from your bot, just compare the differences.

To make an option optional, you have to give it a default. The default is the value that Wumpy
will give you when the option is not passed.

=== "Parameter default"

    When using parameter defaults just pass the value as a positional argument:

    ```python
    @hello.subcommand()
    async def personal(
        interaction: interactions.CommandInteraction,
        name: str = interactions.Option(None, description='Name to greet')
    ) -> None:
        """Make a personal greeting"""
        pass
    ```

=== "Decorator"

    When using decorators the parameter default is not occupied so that can be used:

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

    Alternatively, you can use decorators for that as well:

    ```python
    @interactions.option('name', description='Name to greet', default=None)
    @hello.subcommand()
    async def personal(
        interaction: interactions.CommandInteraction,
        name: str
    ) -> None:
        """Make a personal greeting"""
        pass
    ```

The last thing you should do is update the annotations, because `None` is not a string.

This is easily done by importing `Optional` from `typing` and changing `str` to `Optional[str]`
like this:

=== "Parameter default"

    ```python
    from typing import Optional

    from wumpy import interactions

    app = interactions.InteractionApp(...)

    hello = app.group(name='hello', description='Greeting commands')

    @hello.subcommand()
    async def personal(
        interaction: interactions.CommandInteraction,
        name: Optional[str] = interactions.Option(None, description='Name to greet')
    ) -> None:
        """Make a personal greeting"""
        await interaction.respond(f'Hello {name}')
    ```

=== "Decorator"

    When using decorators the parameter default is not occupied so that can be used:

    ```python
    from typing import Optional

    from wumpy import interactions

    app = interactions.InteractionApp(...)

    hello = app.group(name='hello', description='Greeting commands')

    @interactions.option('name', description='Name to greet')
    @hello.subcommand()
    async def personal(
        interaction: interactions.CommandInteraction,
        name: Optional[str] = None
    ) -> None:
        """Make a personal greeting"""
        await interaction.respond(f'Hello {name}')
    ```

!!! note "Pro tip"
    Wumpy understands `Optional[...]` as having `None` the default. You can remove the default
    and Wumpy will add it automatically.

## Updating our command

Now that the option is optional, and the user may not pass a name we need to handle this case.

Let's add an if-statement that will just respond with "Hello" if no name was passed:

```python
@hello.subcommand()
async def personal(
    interaction: interactions.CommandInteraction,
    name: Optional[str] = interactions.Option(None, description='Name to greet')
) -> None:
    """Make a personal greeting"""
    if name is None:
        await interaction.respond('Hello')
    else:
        await interaction.respond(f'Hello {name}')
```

And we're done, that's all! The user can now use the subcommand with, or without, a name.
