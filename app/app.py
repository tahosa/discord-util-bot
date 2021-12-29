import os
import logging
import config
import discord
from discord.ext.commands import Bot
import nest_asyncio

import tasks

nest_asyncio.apply()

_LOG = logging.getLogger('discord-util')

_HANDLER = logging.StreamHandler()
_HANDLER.addFilter(logging.Filter(name = 'discord-util'))
_HANDLER.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(_HANDLER)

try:
    env_level = os.getenv('LOG_LEVEL', logging.INFO)
    log_level = int(env_level)
    _LOG.setLevel(log_level)
except ValueError:
    _LOG.setLevel(logging.INFO)
    _LOG.error(f'Could not parse log level "{env_level}" from env. Log level must be an int. Defaulting to INFO')


cfg = config.Config('server.cfg')

intents = discord.Intents.default()
intents.members = True

bot = Bot('!', intents = intents)

def start():
    if cfg['tasks.uwu.enabled']:
        bot.add_cog(tasks.uwu.Uwu())

    if cfg['tasks.scoresaber.enabled']:
        sb = tasks.scoresaber.Scoresaber(bot, cfg)
        sb.run()
        bot.add_cog(sb)

    if cfg['tasks.mtg.enabled']:
        mtg = tasks.mtg.Mtg(bot, cfg)
        bot.add_cog(mtg)

@bot.event
async def on_ready():
    _LOG.info(f'We have logged in as {bot.user.name}')
    start()


bot.run(cfg['bot_token'])
