# First Tutorial and User Guide

The purpose of this tutorial is to a first introductory to Wumpy and its features.

After reading you should be equipped with knowledge to make bots on your own.

## Setup and Installation

Start by installing Wumpy from the repository with the following command:

```bash
python -m pip install git+https://github.com/Bluenix2/wumpy
```

!!! note
    Wumpy does not yet have a stable release

And that's it! You should now be able to import wumpy and interact with your favourite API.

Most, if not all, of your bots should start with code similar to this:

```python
import os
import random

from wumpy import interactions


app = interactions.InteractionApp(int(os.environ['CLIENT_ID']), os.environ['PUBLIC_KEY'])


if __name__ = '__main__':
    import uvicorn
    uvicorn.run(app)
```

This will initialize an interaction app with values from your enviroment variables, this is the
recommended way as it makes it trivial for someone else to run your bot.

To make loading these enviroment variables easier you can install
[python-dotenv](https://pypi.org/project/python-dotenv/) and create a `.env` file like this:

```text
CLIENT_ID=12345678901112134
PUBLIC_KEY=a8b96f50a8aba153fc5f82f69076551c816b9558d4e5ee790d3fc9eb9fba9d8b
```

Now add the following code before you initialize the app and you should be good to go:

```python
from dotenv import load_dotenv

load_dotenv()
```

## Helpful tools

Discord Interactions require you to use HTTPS, which can be very tricky to set up locally to
test. [Ngrok](https://ngrok.com/) makes this easy.

Download the tool and run `ngrok http` making sure it tunnels the same port as you run uvicorn
with. Sometimes `ngrok http -host-header=rewrite localhost:8000` may be necessary to use.

Now that Ngrok is tunneling traffic to you, login to Discord and copy the URL into the
"Interactions Endpoint URL" field.
