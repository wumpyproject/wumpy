# Subcommands

In Wumpy you can register subcommands similarly to how you registered commands.

All we have to do is first create a command and give it a name, then we can assign it to a
variable and use that to register subcommands.

Let's create a "hello" command, and add a "random" subcommand to it:

```python
from wumpy import interactions

app = interactions.InteractionApp(...)

hello = app.group(name='hello', description='Greeting commands')

@hello.subcommand()
async def random(interaction: interactions.CommandInteraction) -> None:
    """Greet with a random response."""
    pass
```

!!! note
    Note the fact that `hello()` is no longer used as a decorator on a function,
    you cannot invoke a command that has subcommands directly. This is a limitation imposed
    by Discord and not the library.

Now let's make it work, for that we need to use the `choice` from the `random` module:

```python
from random import choice

from wumpy import interactions

app = interactions.InteractionApp(...)

hello = app.group(name='hello', description='Greeting commands')

@hello.subcommand()
async def random(interaction: interactions.CommandInteraction) -> None:
    """Greet with a random response."""
    await interaction.respond(choice(['Hello', 'Nice to see you']))
```

The bot will now respond with a random greeting each time you call it!

You can define multiple subcommands on a command, here Wumpus added a "formal" subcommand:

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
```
