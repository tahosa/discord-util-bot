import config
import discord
import asyncio
from discord.ext import tasks
from discord.ext.commands import Bot

class Task:
    CFG: config.Config
    bot: Bot

    task: asyncio.Task
    _run: tasks.Loop

    def __init__(self, bot: Bot, config: config.Config):
        self.bot = bot
        self.CFG = config

    def run(self):
        self.task = self._run.start()
