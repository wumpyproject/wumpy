# Creating the bot

The first step of all Discord tutorials is to create the bot account, this is how you
authenticate and talk to the Discord API.

## Creating an application

Discord's API consist of applications. These applications are used for games, "Log in with
Discord", and of course - bots!

Start by navigating to the [Discord Developer Portal](https://discord.com/developers/). The
page should look like this:

![Overview of the Discord Developer Portal](developer-portal.png)

Now click the "New Application" button at the top right. This will prompt you for a name for
your application, like this:

![Prompt asking for a name](name-prompt.png)

Wumpus decided to call its bot "Wumpbot", but you are free to name yours as you wish.

Now click "Create", you should see the following page:

![General information about the application](general-information.png)

This step is completely optional, but you can now add a description and picture to your
application if you want to.

## Adding a bot to the mix

It is now time to add a bot to the application, click the "Bot" tab in the sidebar. It should
look like this:

![Overview of empty Bot tab](build-a-bot.png)

Click "Add Bot" in the top right and then "Yes, do it!" in the following dialog box to confirm.

![Confirmation box](bot-confirmation.png)

There is now a bot attached to your application and you should see the following page:

![Overview of Bot tab with information](bot-overview.png)

## Inviting the bot to your server

The very last part of creating a Discord bot is inviting it to your server.

In the left sidebar go to "OAuth2" and pick "bot" as well as "application.commands" in the
OAuth2 URL Generator at the bottom of the page.

![Overview of OAuth2 tab](oauth2-tab.png)

Now copy the link generated and open it in your browser, it should look like this:

![OAuth2 flow page](bot-invite-flow.png)

Select the server you want to add the bot to and click "Authorize". The bot will then appear
in your server with the power of technology.

![Bot appearing in the Discord server](bot-joined.png)
