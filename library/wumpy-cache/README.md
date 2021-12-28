# Wumpy-cache

Simple memory cache for the gateway.

The default implementation in `wumpy-cache` is rather simple dictionaries, but
it can be overriden by other implementations as long as they follow the typing
`Cache` Protocol.

This means that you can use alternate implementations of data structures for
more efficient retrieval for your use-case or offload caching to something like
Redis or even store it in Postgres.
