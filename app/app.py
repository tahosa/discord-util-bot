import os
import logging
import config
import discord
from discord.ext.commands import Bot

import tasks
from bot_config import BotConfig

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


cfg = BotConfig.model_validate(config.Config('server.cfg').as_dict())

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = Bot('!', intents = intents)

async def start():
    if cfg.tasks.uwu.enabled:
        await bot.add_cog(tasks.uwu.Uwu())

    if cfg.tasks.scoresaber.enabled:
        sb = tasks.scoresaber.Scoresaber(bot, cfg.tasks.scoresaber)
        sb.run()
        await bot.add_cog(sb)

    if cfg.tasks.mtg.enabled:
        mtg = tasks.mtg.Mtg(bot, cfg.tasks.mtg)
        await bot.add_cog(mtg)

@bot.event
async def on_ready():
    if bot.user is not None:
        _LOG.info(f'We have logged in as {bot.user.name}')
        await start()
    else:
        _LOG.fatal(f'Unable to log in!')


bot.run(cfg.bot_token)
