import re
import config
import discord
from discord.ext import commands as commands

from .cards import get_card, scryfall_search


def _msg_in_channel(message: discord.Message) -> bool:
    '''Check if the message was posted in a monitored channel'''
    return message.channel.id in Mtg._CFG['tasks.mtg.channels']


def _sent_by_bot(message: discord.Message, bot: commands.Bot) -> bool:
    '''Check if the message was sent by the bot'''
    return message.author == bot.user


class Mtg(commands.Cog):
    bot: commands.Bot


    def __init__(self, bot: commands.Bot, cfg: config.Config):
        Mtg._CFG = cfg
        self.bot = bot


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not _sent_by_bot(message, self.bot) and _msg_in_channel(message):
            matches = re.findall(r'\[\[(.*?)\]\]', message.content, re.MULTILINE)
            if len(matches) > 0:
                cards = []
                misses = []
                for match in matches:
                    (card, set) = match.split('|', 1) if match.find('|') > -1 else (match, '')
                    result = await get_card(name=card, set=set)

                    if result is None:
                        miss = f'"{card}"'
                        if set:
                            miss += f' in {set}'
                        misses.append(miss)
                    else:
                        cards.append(result)

                if len(misses) > 0 :
                    cards.insert(0, (None, f'No matches found for {", ".join(misses)}\n', None))

                for card in cards:
                    if card[0] is None:
                        await message.channel.send(card[1])
                    else:
                        if card[2] is not None:
                            file = discord.File(card[2], f'{card[0]}.png')
                            await message.channel.send(content=f'{card[1]}', file=file)
                        else:
                            await message.channel.send(f'{card[1]}\n_`Image Missing`_')


    @commands.command(
        help='''Search for cards in the Magic database with a wide variety of criteria

        <query>  Scryfall advanced text query string. See: https://scryfall.com/docs/syntax''',
        usage='<query>',
        brief='Search for a card',
        checks=[_msg_in_channel],
    )
    async def search(self, ctx: commands.Context, *, arg=None):
        if not arg:
            await ctx.message.channel.send('You must specify search criteria. Use !help search for details on how to use this command.')
            return

        page_size = Mtg._CFG['tasks.mtg.page_size']

        try:
            (cards, error) = await scryfall_search(arg, page_size)
        except Exception as ex:
            await ctx.message.channel.send('Error processing search. Use !help search for details on how to use this command.')
            return

        if error:
            await ctx.message.channel.send(error)
            return

        if cards is None or len(cards) < 1:
            await ctx.message.channel.send('No cards found matching that search.')
            return

        else:
            cards.insert(0, (None, f'{len(cards)} result{"s" if len(cards) > 1 else ""}:', None))
            for card in cards:
                if card[0] is None:
                    await ctx.message.channel.send(card[1])
                else:
                    if card[2] is not None:
                        file = discord.File(card[2], f'{card[0]}.png')
                        await ctx.message.channel.send(content=f'{card[1]}', file=file)
                    else:
                        await ctx.message.channel.send(f'{card[1]}\n_`Image Missing`_')


    @search.error
    async def search_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            return
        else:
            raise error
