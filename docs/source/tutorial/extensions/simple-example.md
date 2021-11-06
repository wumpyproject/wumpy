# Simple extension example

For most code you can easily change `InteractionApp` or `GatewayBot` to
`Extension` and it will work as expected.

Here's the code-block from [the Hello World](#hello-world.md) changed to be an
extension:

```python
from wumpy import Extension, interactions


ext = Extension()


@ext.command()
async def hello(interaction: interactions.CommandInteraction) -> None:
    """Greet the bot and say hello."""
    await interaction.respond('Hello')
```

Inside of your main file you can now load this extension like this:

```python
from wumpy import interactions


app = interactions.InteractionApp(...)


# Load the extension, which is inside `hello_world.py`. Then after the ':' we
# tell Wumpy that the actual extension variable is called `ext`.
app.load_extension('hello_world:ext')
```
