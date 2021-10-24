import logging
import config
import discord

from tasks.scoresaber import scoresaber

_LOG = logging.getLogger('discord-util')
_LOG.setLevel(logging.INFO)

_HANDLER = logging.StreamHandler()
_HANDLER.addFilter(logging.Filter(name = 'discord-util'))
_HANDLER.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.getLogger().addHandler(_HANDLER)

cfg = config.Config('server.cfg')

intents = discord.Intents.default()
intents.members = True

client = discord.Client(
    chunk_guilds_at_startup = True,
    intents = intents
)

def start():
    if cfg['tasks.scoresaber.enabled']:
        sb = scoresaber.Scoresaber(client, cfg)
        sb.run()

@client.event
async def on_ready():
    _LOG.info(f'We have logged in as {client.user.name}')
    start()


client.run(cfg['bot_token'])
