# Why use extensions?

As you follow this tutorial you will eventually feel the need to split your
Discord bot into multiple files to make your code mode readable and easier to
manage. This is exactly what extensions are for.

## What are extensions?

Extensions allow you to define some commands and listeners elsewhere, then load
them onto your main bot or application.

This way you can put some commands having to do with a certain feature in one
specific file reducing the length of your main file.

## Why are extensions loaded using strings?

There's another big benefit to extensions; they are dynamically loaded!

For you as a user this means that you can reload an extension to apply changes
without restarting your bot. If the extensions are imported directly using
`from ... import ...` that complicates things greatly.

## What are the downsides of extensions?

When extensions are reloaded they are also fully executed again so that new
changes can be applied. This means that existing code could be holding outdated
references.

For example, if you define a class inside an extension and have other code
that imports this and uses it with `isinstance(...)` you will get unexpected
behavior when reloading an extension. The code that has the `isinstance(...)`
*could* be holding a reference to the old class (from Python's point of view
that is a different class) and `isinstance(...)` will return False.

This is very uncommon if you structure your code correctly though, but could be
worth noting when designing your bot.
