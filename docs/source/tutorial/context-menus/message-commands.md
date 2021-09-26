# Message commands

There are more context menus than user commands. You can also create message commands, let's
make one to reverse a message's content.

## Creating message commands

Creating message commands is very similar to how user commands are made, just change the enum
value like this:

```python
from wumpy import interactions

app = interactions.InteractionApp(...)

@app.command(interactions.CommandType.message)
async def reverse(
    interaction: interactions.CommandInteraction,
    message: interactions.InteractionMessage
) -> None:
    """Reverse a message's content."""
    pass
```

The command will always be given the interaction generated and message the command was invoked
with but nothing else.

Like with user commands you cannot use options with message commands.

Now that we understand message commands, let's finish the implementation:

```python
from wumpy import interactions

app = interactions.InteractionApp(...)

@app.command(interactions.CommandType.message)
async def reverse(
    interaction: interactions.CommandInteraction,
    message: interactions.InteractionMessage
) -> None:
    """Reverse a message's content."""
    await interaction.respond(message.content[::-1])
```

!!! info
    The reversal implementation is a neat indexing trick, by passing a "step" with -1 we create
    a string with all characters reversed.

Like with user commands it's *that* easy so the documentation won't explore it more than this.
