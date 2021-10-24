import logging

import discord.ext.commands as commands
from ..task import Task

_LOG = logging.getLogger('discord-util').getChild("uwu")

class Uwu(commands.Cog):
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content.lower().startswith('hello bot'):
            await message.channel.send('Hewwo uwu')
            return