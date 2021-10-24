import logging
import config
import discord
import asyncio
from discord.ext import tasks


class Task:
    CFG: config.Config
    client: discord.Client

    task: asyncio.Task
    _run: tasks.Loop

    def __init__(self, client: discord.Client, config: config.Config):
        self.client = client
        self.CFG = config

    def run(self):
        self.task = self._run.start()
