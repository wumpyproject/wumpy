# McDonald's order slash command

On this page we're gonna go into how you can have multiple options for a
command and cover more of the types supported.

## Scoping out the command

First let's figure out what we want to do. The plan is to create a `/order`
command that will allow you to order a burger.

The options the comand will take is an integer being the amount of hamburgers
as well as a bool whether the order includes fries.

## Creating the command

Let's start like we always do:

```python
from wumpy import interactions


app = interactions.InteractionApp(...)


@app.command()
async def order(interaction: interactions.CommandInteraction) -> None:
    """Order a McDonald's burger menu."""
    pass
```

Now we add the first option, the amount of burgers:

```python
from wumpy import interactions


app = interactions.InteractionApp(...)


@app.command()
async def order(
    interaction: interactions.CommandInteraction,
    amount: int = interactions.Option(description='The amount of burgers'),
) -> None:
    """Order a McDonald's burger menu."""
    pass
```

We want to give this a default value though, if it isn't passed then of course
you only want one burger.

Let's see how this looks together with a response:

```python
from wumpy import interactions


app = interactions.InteractionApp(...)


@app.command()
async def order(
    interaction: interactions.CommandInteraction,
    amount: int = interactions.Option(1, description='The amount of burgers'),
) -> None:
    """Order a McDonald's burger menu."""
    await interaction.respond(f"Here's your order: {amount}x 🍔")
```

## Adding fries to the mix

Now our command can take an optional `amount` argument, let's add the bool
that we scoped out earlier.

The interaction option will look like this:

```python
from wumpy import interactions


app = interactions.InteractionApp(...)


@app.command()
async def order(
    interaction: interactions.CommandInteraction,
    amount: int = interactions.Option(1, description='The amount of burgers'),
    fries: bool = interactions.Option(
        False, description='Whether you want fries included.'
    ),
) -> None:
    """Order a McDonald's burger menu."""
    await interaction.respond(f"Here's your order: {amount}x 🍔")
```

The very last part is updating our code to handle this. Like this:

```python
from wumpy import interactions


app = interactions.InteractionApp(...)


@app.command()
async def order(
    interaction: interactions.CommandInteraction,
    amount: int = interactions.Option(1, description='The amount of burgers'),
    fries: bool = interactions.Option(
        False, description='Whether you want fries included.'
    ),
) -> None:
    """Order a McDonald's burger menu."""
    extra = ''
    if fries:
        extra += ' + 🍟'

    await interaction.respond(f"Here's your order: {amount}x 🍔" + extra)
```
