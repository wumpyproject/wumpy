# Hello world, your first interaction

The same way you once (maybe not too long ago) printed your first "Hello World" it is now time
you have your first interaction with the big world of Discord.

## Creating slash commands

To get started let's first register a simple slash command, it will respond with a random
greeting and an emoji.

Following the setup from the previous chapter, we'll initialize an `InteractionApp`:

```python
import random

from wumpy import interactions


app = interactions.InteractionApp(...)  # Replace with your credentials


...  # This is where the new code will be


if __name__ = '__main__':
    import uvicorn
    uvicorn.run(app)
```

It is now time to register the command, which can best be done through a decorator.

If no name or no description is passed the function's name and doc-string will be used.

Let's create a command called "hello" and add a description. The callback will need to have at
least one argument being the interaction received from Discord:

```python
@app.command()
async def hello(interaction: interactions.CommandInteraction) -> None:
    """Greet the bot and say hello."""
    pass
```

## Responding to interactions

You will find that if you try to run this code Discord will display a red "This interaction
failed" which only you can see. This is because we don't yet respond to the interaction.

We can hold with the "random greeting" part of our command, and just have the bot respond with
"Hello" for a start.

Replace `pass` with a call to `interaction.respond()`, like this:

```python
@app.command()
async def hello(interaction: interactions.CommandInteraction) -> None:
    """Greet the bot and say hello."""
    await interaction.respond('Hello')
```

The command should now be in working order, run the script and call the command!

Back to the original idea, but first we'll need a list that `random` can pick from. Take the
time to type out some greetings, here's a few examples:

```python
['Hello', 'Hi', 'Nice to see you']
```

Once you have that we can pass it to `random.choice()`, it will return one item of this list.
In turn pass this to `interaction.respond()`.

```python
@app.command()
async def hello(interaction: interactions.CommandInteraction) -> None:
    """Greet the bot and say hello."""
    await interaction.respond(random.choice(['Hello', 'Hi', 'Nice to see you']))
```

## Final result

The final code now looks like this:

```python
import random

from wumpy import interactions


app = interactions.InteractionApp(...)  # Replace with your credentials


@app.command()
async def hello(interaction: interactions.CommandInteraction) -> None:
    """Greet the bot and say hello."""
    await interaction.respond(random.choice(['Hello', 'Hi', 'Nice to see you']))


if __name__ = '__main__':
    import uvicorn
    uvicorn.run(app)
```
