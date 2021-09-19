# Hello world, your first interaction

The same way you once (maybe not too long ago) printed your first "Hello World" it is now time
you have your first interaction with the big world of Discord.

## Creating slash commands

To get started let's first register a simple slash command that will greet the user.

Following the setup from the previous chapter, we'll initialize an `InteractionApp`:

```python
from wumpy import interactions


app = interactions.InteractionApp(...)


...  # This is where the new code will be
```

It is now time to register the command, which can best be done through a decorator.

If no name or no description is passed the function's name and docstring will be used.

Let's create a command called "hello" and add a description. The callback will need to have at
least one argument being the interaction received from Discord:

```python
from wumpy import interactions


app = interactions.InteractionApp(...)


@app.command()
async def hello(interaction: interactions.CommandInteraction) -> None:
    """Greet the bot and say hello."""
    pass
```

## Responding to interactions

You will find that if you try to run this code Discord will display a red "This interaction
failed" which only you can see. This is because we don't yet respond to the interaction.

Replace `pass` with a call to `interaction.respond()`, like this:

```python
from wumpy import interactions


app = interactions.InteractionApp(...)


@app.command()
async def hello(interaction: interactions.CommandInteraction) -> None:
    """Greet the bot and say hello."""
    await interaction.respond('Hello')
```

The command should now be in working order, run the script and call the command!
