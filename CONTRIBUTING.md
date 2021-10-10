# Contributing

Thank you for your interest in contributing to this project.

## Setting up tools

Static type checkers are encouraged to be used. There are plans to set up a
CI that run PyRight or MyPy on the project to ensure it passes type checking.

This project uses [flake8](https://github.com/PyCQA/flake8) for linting as a
laid-back linter, mainly it enforces line length. Preferably lines should be
between 79 and 95 characters long, but flake8 will not complain until a line
reaches 105 characters which is the hard limit.

Imports should be ordered according to the rules of
[isort](https://github.com/PyCQA/isort).

### Building the documentation

Because of how [Read the Docs](readthedocs.org) builds our documentation from
the root of our project that means that files and folders have to be configured
from that origin.

This means that building and serving the documentation needs to be done from
*the root of the project* as well with the following commands:

```bash
# Locally serve the documentation
mkdocs serve --config-file docs/mkdocs.yml

# For building use the equivalent:
mkdocs build --config-file docs/mkdocs.yml
```

## Making commits

Once you have made your changes it is time to commit it to Git. These commits
should be imperative and clearly explain what was changed. The commit body
can be used to explain why it was changed.

If you are unsure what this means,
[read this blog post](https://chris.beams.io/posts/git-commit/). The blog post
can be summarized to having your commit messages fit into this sentence:

> If applied, this commit will ...
