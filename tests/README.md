# Testing an API Wrapper..

It is quite hard to test an API wrapper. The actual interaction with Discord is
extremely hard to replicate and will never be enough, hence it will never be
correctly tested.

That said, there are still things to test other than the interaction with
Discord. Namely setting up commands, adding listeners and loading extensions.

## Running the test suite

Firstly, install [pytest](https://docs.pytest.org/en/latest/) and
[coverage.py](https://coverage.readthedocs.io/en/latest).

Then run the test suit with:

```bash
coverage run --branch -m pytest tests/
```

You can then run the following to generate a coverage report:

```bash
coverage.html
```
