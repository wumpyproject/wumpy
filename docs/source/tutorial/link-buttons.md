# Rick-rolls

Now that we've fully explored the possibilities with application commands
there's a second part of the interactions API to take a look at!

Discord calls these message components.

## Creating buttons

In Wumpy it is very simple to create one-off buttons, all you need to do is
instance the `Button` class.

Start with a bare slash command:

```python
from wumpy import interactions


app = interactions.InteractionApp(...)


@app.command()
async def link(interaction: interactions.CommandInteraction) -> None:
    """Respond with an unknown link."""
    pass
```

Now it is time to create the button. For link buttons there's not as many
fields necessary, only `url` and `label` itself. Like this:

```python
Button(label='Click me!', url='https://youtu.be/dQw4w9WgXcQ')
```

This instance needs to be given to `interaction.respond` inside of two lists.

Wumpy automatically converts it into the types that Discord expects, which is a
list of ActionRows. Action rows are special components that contain other
components.

Your code should look like this:

```python
from wumpy import interactions


app = interactions.InteractionApp(...)


@app.command()
async def link(interaction: interactions.CommandInteraction) -> None:
    """Respond with an unknown link."""
    await interaction.respond(
        components=[[
            Button(label='Click me!', url='https://youtu.be/dQw4w9WgXcQ')
        ]]
    )
```
