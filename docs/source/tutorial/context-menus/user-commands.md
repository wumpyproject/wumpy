# User commands

Previously we have went through slash commands, also called chat input commands. There are more
commands than this, and on this page we will deep dive into user commands.

## Creating a user command

All you need to create a user command is to pass in a different application command type:

```python
from wumpy import interactions

app = interactions.InteractionApp(...)

@app.command(interactions.CommandType.user)
async def wave(
    interaction: interactions.CommandInteraction,
    user: interactions.InteractionUser
) -> None:
    """Wave hello to someone!"""
    pass
```

User commands cannot take options, all they receive are the user they were invoked on.

Let's respond to the interaction:

```python
from wumpy import interactions

app = interactions.InteractionApp(...)

@app.command(interactions.CommandType.user)
async def wave(
    interaction: interactions.CommandInteraction,
    user: interactions.InteractionUser
) -> None:
    """Wave hello to someone!"""
    await interaction.respond(f'{interaction.user} waves to {user} 👋')
```

It's *that* easy and not much more to it. That's why the documentation won't
