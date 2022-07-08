# Wumpy

A Discord API wrapper for Python. Wumpy aims to be easy enough for Wumpus, and
extensible enough for Clyde!

## Community

There is a [development Discord server](https://discord.gg/ZWpjYdKKTF) you can
join. GitHub Discussions is used for support.

## Usage

If you are new to Wumpy consider [reading the documentation](https://wumpy.rtfd.io).

A lot of the functionality of Wumpy is separated into *multiple subpackages*,
for example [`wumpy-gateway`](library/wumpy-gateway/README.md) (imported as
`wumpy.gateway`) is a subpackage that only contains the code for interacting
with the gateway.

If you are building another library, consider using some of these subpackages
instead of re-implementing the same functionality - more times than not it is
only the highest level (the one that the end-user interacts with) that differs.
For Wumpy the highest level of abstraction is
[`wumpy-client`](library/wumpy-client/README.md) which is built on top of all
other subpackages.

## Support

If you have a problem please open a discussion through GitHub. This is the best
place to ask for help as only bug reports or detailed feature requests should
go in the issue tracker.

⭐ Please consider starring the repository, it really helps! ⭐

## Future plans

The highest priority right now is to get full API coverage, while keeping the
standards of quality that Wumpy stands for.

Development is triaged through
[this GitHub project](https://github.com/orgs/wumpyproject/projects/1) if you
get curious about the current state of the project, this brings together all
issues and todos from all subpackage.

## Contributing

The library is only first now starting to get a good structure. Take a look
at [CONTRIBUTING.md](CONTRIBUTING.md) and
[the Wiki](https://github.com/wumpyproject/wumpy/wiki) for developer notes and
different design decision write-ups.

The library is licensed under one of MIT or Apache 2.0 (up to you). Please
see [LICENSE](./LICENSE) for more information.

## Version guarantees

The Wumpy project's official subpackages all follow
[Semantic Versioning 2.0](https://semver.org/):

- Major version bumps hold no guarantees at all.

- Minor version bumps are backwards compatible but not forwards compatible.

- Patch versions are *both* backwards compatible and forwards compatible.

To simplify the above, this is how it will affect you (these are imaginary
example versions):

- You can upgrade from `v1.0.6` to `v1.0.8`, or downgrade to `v1.0.3` without
  any code changes.

- You can upgrade from `v1.5.0` to `v1.6.0` without any code changes, but you
  can't downgrade to `v1.4.0`.

- You cannot upgrade from `v4.0.0` to `v5.0.0` or downgrade to `v3.0.0`. Major
  versions have no guarantee of compatability.

## Public API

The public API is documented in the API reference hosted on Read the docs,
which can be found [here](https://wumpy.rtfd.io/).
