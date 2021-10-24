import logging
import config
import discord
from discord.ext import tasks as discordTasks

import tasks

from .database import Database
from .updater import ScoreUpdater
from .message_handler import MessageHandler

_LOG = logging.getLogger('discord-util').getChild("scoresaber")

class Scoresaber(tasks.Task):
    database: Database
    updater: ScoreUpdater
    handler: MessageHandler

    def __init__(self, client: discord.Client, cfg: config.Config):
        super().__init__(client, cfg)

        self.database = Database(cfg)
        self.updater = ScoreUpdater(self.database)
        self.handler = MessageHandler(self.database, self.updater)


        @discordTasks.loop(seconds=self.CFG['tasks.scoresaber.update_interval'])
        async def run():
            _LOG.debug('Checking for new scores')
            channel = self.client.get_channel(self.CFG['tasks.scoresaber.channels'][0])
            with self.database.db:
                new_scores = await self.updater.update()

            _LOG.debug(f'Found {len(new_scores)} new high scores')
            if len(new_scores) > 0:
                for score in new_scores:
                    await channel.send(score)

        self._run = run

        @client.event
        async def on_message(message):
            # Ignore messages from the bot, or from channels that are not being watched
            if message.author == self.client.user:
                return

            if message.content.lower().startswith('hello bot'):
                await message.channel.send('Hewwo uwu')
                return

            if message.channel.id not in self.CFG['tasks.scoresaber.channels']:
                return

            _LOG.debug('Opening database')
            with self.database.db:

                content = message.content.lower()
                _LOG.debug('Begin parsing message')

                # Power User functions
                if f'{message.author.name}#{message.author.discriminator}' in self.CFG['tasks.scoresaber.power_users']:
                    if content.startswith('!update'):
                        await self.handler.update(message)

                    if content.startswith('!register'):
                        if await self.handler.register(message):
                            await self.handler.update(message)

                if content.startswith('!list'):
                    await self.handler.player_list(message)

                if content.startswith('!scores'):
                    await self.handler.get_player_scores(message)

                if content.startswith('!top'):
                    await self.handler.search_top(message)
