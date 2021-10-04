# Rock paper scissors!

There are cases where you only allow certain values for an option. On this page
we're gonna implement a rock, paper and scissors game.

## Creating the command

Let's start with the usual boilerplate needed for an application command:

```python
from wumpy import interactions


app = interactions.InteractionApp(...)


@app.command()
async def rps(interaction: interactions.CommandInteraction) -> None:
    """Play rock, paper and scissors against the bot."""
    pass
```

There are now two ways we can add the choices. Either it can be passed to the
Option function (or decorator) or use the `Literal` annotation.

=== "`Literal` annotation"

    Wumpy of course reads annotations and can figure out choices from `Literal`
    annotation.

    This sets the name and value of the choice to the same value, so what is
    used inside the `Literal` is what the user will have to pick from.

    Let's take a look:

    ```python
    from typing import Literal

    from wumpy import interactions


    app = interactions.InteractionApp(...)


    @app.command()
    async def rps(
        interaction: interactions.CommandInteraction,
        choice: Literal['Rock', 'Paper', 'Scissors'] = Option(
            description='The play you want to make.'
        ),
    ) -> None:
        """Play rock, paper and scissors against the bot."""
        pass
    ```

=== "Option function"

    If you prefer not to use the annotation it is also possible to pass the
    `choices` keyword argument to the Option function:

    ```python
    from wumpy import interactions


    app = interactions.InteractionApp(...)


    @app.command()
    async def rps(
        interaction: interactions.CommandInteraction,
        choice: str = Option(
            description='The play you want to make.',
            choices=['Rock', 'Paper', 'Scissors']
        ),
    ) -> None:
        """Play rock, paper and scissors against the bot."""
        pass
    ```

    The same goes for the option decorator:

    ```python
    from wumpy import interactions


    app = interactions.InteractionApp(...)


    @interactions.option(
        'choice',description='The play you want to make.',
        choices=['Rock', 'Paper', 'Scissors']
    )
    @app.command()
    async def rps(
        interaction: interactions.CommandInteraction,
        choice: str,
    ) -> None:
        """Play rock, paper and scissors against the bot."""
        pass
    ```

!!! note
    The documentation tries to keep a low line length to support as many
    screens as possible, that's why the option is spread over multiple lines.

When a user is typing out your command, they will now have to pick from 'Rock',
'Paper' or 'Scissors'.

## Adding an implementation

Now that know how to tell Wumpy to create our command. Let's finish the
implementation!

We need to start by importing the `random` module and choose a random choice
to be the computer's choice:

```python
import random
from typing import Literal

from wumpy import interactions


app = interactions.InteractionApp(...)


@app.command()
async def rps(
    interaction: interactions.CommandInteraction,
    choice: Literal['Rock', 'Paper', 'Scissors'] = Option(
        description='The play you want to make.'
    ),
) -> None:
    """Play rock, paper and scissors against the bot."""
    computer = random.choice(['Rock', 'Paper', 'Scissors'])
```

After this we need to add the main logic that compares the user's pick to the
computer's.

The first step is seing if the computer and user made the same play. This of
course results in a tie:

```python
@app.command()
async def rps(
    interaction: interactions.CommandInteraction,
    choice: Literal['Rock', 'Paper', 'Scissors'] = Option(
        description='The play you want to make.'
    ),
) -> None:
    """Play rock, paper and scissors against the bot."""
    computer = random.choice(['Rock', 'Paper', 'Scissors'])

    if computer == choice:
        return await interaction.respond('Tie! Try again')
```

There are now two cases where the computer wins. That is when the computer
picked "Paper" and the user picked "Rock" or if the computer picked
"Rock" and the user picked "Scissors".

The rest of the cases the user wins.

Let's see how this looks like in code:

```python
@app.command()
async def rps(
    interaction: interactions.CommandInteraction,
    choice: Literal['Rock', 'Paper', 'Scissors'] = Option(
        description='The play you want to make.'
    ),
) -> None:
    """Play rock, paper and scissors against the bot."""
    computer = random.choice(['Rock', 'Paper', 'Scissors'])

    if computer == choice:
        return await interaction.respond('Tie! Try again')

    if (
        (computer == 'Paper' and choice == 'Rock') or
        (computer == 'Rock' and choice == 'Scissors')
    ):
        return await interaction.respond('The computer won!')

    # All other cases the user win
    return await interaction.respond('You won!')
```

## Final result

The final code should look like this:

```python
import random
from typing import Literal

from wumpy import interactions


app = interactions.InteractionApp(...)


@app.command()
async def rps(
    interaction: interactions.CommandInteraction,
    choice: Literal['Rock', 'Paper', 'Scissors'] = Option(
        description='The play you want to make.'
    ),
) -> None:
    """Play rock, paper and scissors against the bot."""
    computer = random.choice(['Rock', 'Paper', 'Scissors'])

    if computer == choice:
        return await interaction.respond('Tie! Try again')

    if (
        (computer == 'Paper' and choice == 'Rock') or
        (computer == 'Rock' and choice == 'Scissors')
    ):
        return await interaction.respond('The computer won!')

    # All other cases the user win
    return await interaction.respond('You won!')
```
