# Contributing

Thank you for your interest in contributing to this project.

## Setting up tools

Since this project uses Cython's Pure Python Mode this means several Python
tools can be utilized to help with development other than Cython itself.
Because of the strongly statically typed nature of Cython code with Pure
Python annotations, static type checkers are encouraged to be used.
There are plans to setup a CI/CD that run PyRight or MyPy on the project to
ensure it passes.

This project uses [flake8](https://github.com/PyCQA/flake8) for linting
as a laid-back linter, mainly it enforces line length. Preferrably lines
should be between 79 and 95 characters long, but flake8 will not complain
until it reaches 105 characters.

Imports should be ordered according to the rules of
[isort](https://github.com/PyCQA/isort).
