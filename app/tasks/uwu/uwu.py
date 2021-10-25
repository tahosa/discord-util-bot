import logging

import discord
import discord.ext.commands as commands

_LOG = logging.getLogger('discord-util').getChild("uwu")

class Uwu(commands.Cog):
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content.lower().startswith('hello bot'):
            await message.channel.send('Hewwo uwu')
            return
