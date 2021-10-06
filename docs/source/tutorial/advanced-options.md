# Catifying nicknames

On this page we're gonna go through how to use advanced option types, more
specfically how to take a user object as an option.

## Defining the option

Let's start by taking the usual boilerplate to create a slash command and add
a parameter annotated as `interactions.InteractionUser`:

```python
from wumpy import interactions


app = interactions.InteractionApp(...)


@app.command()
async def catify(
    interaction: interactions.CommandInteraction,
    target: interactions.InteractionUser,
) -> None:
    """Catify a user's name."""
    pass
```

This will tell Wumpy to create an option where the user must specify a user to
send to the command.

By now you should know that there's something missing in this command, let's
add the missin `Option` default.

```python
from wumpy import interactions


app = interactions.InteractionApp(...)


@app.command()
async def catify(
    interaction: interactions.CommandInteraction,
    target: interactions.InteractionUser = interactions.Option(
        description="The user who's name to catify"
    ),
) -> None:
    """Catify a user's name."""
    pass
```

## Finishing the command logic

Like usual with these tutorial let's finish the command to have something fun
to play around with.

All we need to do is append `ᓚᘏᗢ` at the end of the user's name and respond
to the interaction with this.

Usually we respond with a normal response, but let's switch it up this time!

Empheral messages are messages that only the user who invoked the command sees.
In Wumpy they can be used like this:

```python
from wumpy import interactions


app = interactions.InteractionApp(...)


@app.command()
async def catify(
    interaction: interactions.CommandInteraction,
    target: interactions.InteractionUser = interactions.Option(
        description="The user who's name to catify"
    ),
) -> None:
    """Catify a user's name."""
    await interaction.respond(
        f"{target.mention}'s new name will be: {target.name + 'ᓚᘏᗢ'}",
        empheral=True
    )
```
