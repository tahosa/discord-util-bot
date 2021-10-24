scoresaber-bot
==============

This is a Discord bot for handling multiple functions within your discord server. Currently, the following tasks are available:

 * [`scoresaber`](app/tasks/scoresaber/README.md): Tracking scoresaber high scores among your friends

Running
-------

The bot is set up to be run using Docker. To start, do the following:

1. [Create your server config file](#Configuring)
2. Enable the modules you wish to use (currently `scoresaber`)
    * (Optional) Create an empty file for the scoresaber database if you are using that task. This is useful if you want the database to be re-used if you need to tear down the container for any reason, e.g. updating
3. Build the container with `docker build . -t discord-util:latest`
    * Eventually it will be pushed to docker hub, but not yet
4. Start the container and mount the server config and other relevant files (this example includes the scoresaber database)
    * `docker run -d --mount type=bind,source=/path/to/scores.db,target=/discord-util/scores.db --mount type=bind,source=/path/to/server.cfg,target=/discord-util/server.cfg discord-util:latest`
    * This command assumes you are using `scores.db` as the database name for scoresaber inside your server config. Update that mount if you are using something else.

Configuring
-----------

Make a copy of `server.cfg.template` called `server.cfg`. The only top-level value to configure is the token your bot will use to authenticate to discord for all the tasks. Everything operates using the same bot, so only one token is necessary. For more information on discord bot users, see [their documentation](https://discord.com/developers/docs/topics/oauth2#bots) See the appropriate docs to see how to configure each task.

#### `bot_token`

The bot token from your Discord app page as a quoted string. This is used to authenticate with Discord and start the bot.

### Task Configuration

[`scoresaber`](app/tasks/scoresaber/README.md#Configuration)

Developing
----------

The recommended use is to set up to use `pyenv` or `virtualenv` (or both) to manage the python dependencies. Currently, the bot has been developed and tested using python 3.8.

```shell
pyenv virtualenv python3 discord-util-bot
pyenv activate discord-util-bot
pip install -r requirements.txt
```

This assumes you have configured pyenv correctly and set up the shim wrappers on your `$PATH`

### Debugging

Run the application with `python3 app/app.py`. If you are using VS Code, a launch configuration has been provided.
