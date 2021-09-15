# Talking to Discord

The next step is to use the application you created, this page will go through authenticating
to Discord so that it isn't repeated on each page.

## Interaction Server

Discord provides two ways for bots to use its API and receive events.

The newest one is through an interaction server. This is a normal HTTP server (like a website)
that Discord makes requests to.

It is the recommended way if you are making a bot that only relies on interactions. This
tutorial will focus on using an interaction server because it is the easiest to use with free
services like [Heroku](https://www.heroku.com/) and [Replit](https://replit.com/).

To use an interaction server there is at minimum two values you need. It is the
**Application ID** and **Public Key** of your application.

They can be found on the first page after visiting the
[Discord Developer Portal](https://discord.com/developers/) and selecting your application:

![General Information page](images/talking-to-discord/general-information.png)

These can now be passed to `InteractionApp` like this:

```python
from wumpy import interactions

app = interactions.InteractionApp(
    887286788362756096,
    '63e4b2010dd4c34aec586f40318de423cc2fc26d81baf6d016fa4d8969b05a0d'
)
```

### Automatically creating commands

If you want Wumpy to automatically sync interaction commands there is a 3rd value necessary.

It is the **Client Secret** and can be found under the OAuth2 tab in the sidebar:

![OAuth2 page overview](images/talking-to-discord/oauth2-page.png)

You can now change the code to pass the secret with `secret=`:

```python
from wumpy import interactions

app = interactions.InteractionApp(
    887286788362756096,
    '63e4b2010dd4c34aec586f40318de423cc2fc26d81baf6d016fa4d8969b05a0d',
    secret='AbCd3fgH1jKlmN0pqrst0vwxyzAbCd3f'  # THIS MUST STAY SECRET
)
```

!!! error
    **The client secret should stay secret!** Never ever push the secret to GitHub or hand it
    out to anyone. Read [Hiding credentials](#hiding-credentials) for more information.

## Gateway

This is the second option, the bot will connect to Discord through a WebSocket and will receive
events like a user.

If you are making a bot that needs to react to messages, reactions, typings, channels being
changed, joins and leaves, presences or similar events you need to use the gateway.

You can also receive interactions through the gateway, **but not at the same time as you have**
**an interaction server**.

You only need one credential when using the gateway and it is the **Bot Token** you'll find
under the Bot tab in the sidebar:

![Bot tab overview](images/talking-to-discord/bot-overview.png)

It can then be passed to `Client` like this:

```python
import wumpy

# THE TOKEN MUST STAY SECRET
bot = wumpy.Client(token='ODg3Mjg2Nzg4MzYyNzU2MDk2.YUB8Nw.AbCD3Fgh1jKLMn0pQRST0VwxYz0')
```

!!! error
    **The bot token must be hidden**, it should never be pushed to GitHub or given to anyone
    else. With it anybody can log in as your bot. [Hiding Credentials](#hiding-credentials) has
    tips for how to hide your bot token.

## Hiding credentials

There are some values required when talking to Discord that have to stay hidden.

This is because if someone else knows this they can talk to Discord as you.

If Wumpus gets ahold of your bot token, it can login as your bot and do anything with it.

### Hidden Python files

One easy way of making sure your credentials stay hidden is with a normal Python file.

Create a file called `config.py` (but you can name it whatever you want) and define a variable
with your client secret or bot token:

=== "Client Secret"

    Your file should look like this:

    ```python
    SECRET = 'AbCd3fgH1jKlmN0pqrst0vwxyzAbCd3f'
    ```

    Now go back to your main file and import this variable like this:

    ```python
    from wumpy import interactions

    from config import SECRET

    app = interactions.InteractionApp(
        887286788362756096,
        '63e4b2010dd4c34aec586f40318de423cc2fc26d81baf6d016fa4d8969b05a0d',
        secret=SECRET
    )
    ```

=== "Bot token"

    Your file should look like this:

    ```python
    TOKEN = 'ODg3Mjg2Nzg4MzYyNzU2MDk2.YUB8Nw.AbCD3Fgh1jKLMn0pQRST0VwxYz0'
    ```

    Now go back to your main file and import this variable:

    ```python
    import wumpy

    from config import TOKEN

    bot = wumpy.Client(token=TOKEN)
    ```

If you use [Git](https://git-scm.com/) the final step is to add `config.py` to your
`.gitignore` file so that it isn't included when you make a commit.

### .env files

Another option is to use `.env` files which will be loaded as what is called enviroment
variables.

This will require `python-dotenv` to be installed so that it can load the file:

```bash
python -m pip install python-dotenv
```

After that has been called create a file called `.env`.

=== "Client Secret"

    It should look like this:

    ```dotenv
    SECRET=AbCd3fgH1jKlmN0pqrst0vwxyzAbCd3f
    ```

    Then import `python-dotenv` and `os` like this:

    ```python
    import os

    from dotenv import load_env
    from wumpy import interactions

    load_env()

    app = interactions.InteractionApp(
        887286788362756096,
        '63e4b2010dd4c34aec586f40318de423cc2fc26d81baf6d016fa4d8969b05a0d',
        secret=os.environ['SECRET']
    )
    ```

=== "Bot token"

    It should look like this:

    ```dotenv
    TOKEN=ODg3Mjg2Nzg4MzYyNzU2MDk2.YUB8Nw.AbCD3Fgh1jKLMn0pQRST0VwxYz0
    ```

    Then import `python-dotenv` and `os` like this:

    ```python
    import os

    import wumpy
    from dotenv import load_env

    load_env()

    bot = wumpy.Client(token=os.environ['TOKEN'])
    ```

### Config files

The last option is to use real configuration files, such as Toml or Yaml.

It is also possible to use JSON for this purpose.

This is mostly used for other purposes than the credentials and can become rather complicated.
For that reason this tutorial won't go into it more than mentioning it.
