# Choices with enums

Previously we went through option choices using a rock, paper, scissors game
using the `Literal` annotation or Option keyword arguments. This page will
present an alternate way to use choices using enums.

## Defining the enum

When the documentation refers to a enum it of course means `Enum` from the
`enum` module. Let's define one for our emoji command.

```python
from enum import Enum


class EmojiKind(str, Enum):
    smile = 'Smile'
    frown = 'Frown'
    laugh = 'Laugh'
```

Here we define what you usually refer to as a "string enum". It behaves like an
enum and string at the same time.

Wumpy will use this information to also set the `type` to string.

## Using the enum as an option

Now it is time to add the slash command part, the code will start like this:

```python
from enum import Enum

from wumpy import interactions


app = interactions.InteractionApp(...)


class EmojiKind(str, Enum):
    smile = 'Smile'
    frown = 'Frown'
    laugh = 'Laugh'


@app.command()
async def emoji(
    interaction: interactions.CommandInteraction,
    kind: EmojiKind = interactions.Option(description='The kind of emoji'),
) -> None:
    """Send an ASCII emoji of the specified kind."""
    pass
```

Just like that the user will now get to pick from Smile, Frown or Laugh.

Let's quickly finish the command implementation now!

```python
from enum import Enum

from wumpy import interactions


app = interactions.InteractionApp(...)


class EmojiKind(str, Enum):
    smile = 'Smile'
    frown = 'Frown'
    laugh = 'Laugh'


@app.command()
async def emoji(
    interaction: interactions.CommandInteraction,
    kind: EmojiKind = interactions.Option(description='The kind of emoji'),
) -> None:
    """Send an ASCII emoji of the specified kind."""
    if kind is EmojiKind.smile:
        await interaction.respond(':)')
    elif kind is EmojiKind.frown:
        await interaction.respond(':(')
    elif kind is EmojiKind.laugh:
        await interaction.respond(':D')
```

Actually- this can be done better...

## Improving our command

This is more of general Python advice but important nonetheless.

Instead of going through each kind and comparing it we can use a dictionary.

A dictionary is what's called a "hash map". These allow you to have a key and
value which is exactly what we want.

The big benefit of hash maps are that they're fast, extremely fast! No matter
if you have 1 million elements or just 1 it will take equal amounts of time.

Let's update our command:

```python
from enum import Enum

from wumpy import interactions


app = interactions.InteractionApp(...)


class EmojiKind(str, Enum):
    smile = 'Smile'
    frown = 'Frown'
    laugh = 'Laugh'


# This is our dictionary that we look up emojis in
EMOJI_DICT = {
    EmojiKind.smile: ':)',
    EmojiKind.frown: ':(',
    EmojiKind.laugh: ':D',
}


@app.command()
async def emoji(
    interaction: interactions.CommandInteraction,
    kind: EmojiKind = interactions.Option(description='The kind of emoji'),
) -> None:
    """Send an ASCII emoji of the specified kind."""
    await interaction.respond(EMOJI_DICT[kind])
```

Look how clean our command is now!
