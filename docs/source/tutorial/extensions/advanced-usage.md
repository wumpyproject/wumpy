# More advanced extensions usages

There are times when you want to run some code upon loading. This is fully
supported in Wumpy's extension system.

## Partial example

Most of the time you just want to some code when loading but still load
commands and listeners. This can be accomplished as follows:

```python
from wumpy import Extension


ext = Extension()


...  # Here is some code that adds commands and listeners


def load(target, data):
    print('Loading extension...')

    # Let the extension take over
    return ext.load(target, data)
```

## Underlying extension API

The underlying extension API is very ambiguous and only consists of two
callables.

The first callable should take two positional arguments - the target that
the items (like commands and listeners) should be added to and a dictionary of
values passed.

The second argument allows passing values into an extension as it is loaded,
which can be useful for configuration.

At last the first callable should return another callable which only takes one
argument - the target from before. The point of this callable is to undo what
the first callable did (unload).

## Full usage

A fully managed extension loading where you set some attribute can look like
this as an example:

```python
def unloader(target):
    del target.loaded

def load(target, data):
    target.loaded = data.get('value', True)
    # Return the unloader that Wumpy will call when this extension is
    # unloaded for cleanup.
    return unloader
```
