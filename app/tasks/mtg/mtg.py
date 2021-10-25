import re
import config
import discord
from discord.ext import commands as commands

from .cards import get_formatted_cards


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
                # TODO: lookup handler
                cards = []
                misses = []
                for match in matches:
                    (card, set) = match.split('|', 1) if match.find('|') > -1 else (match, '')
                    results = await get_formatted_cards(card_name=card, card_set=set)

                    if len(results) > 0:
                        cards.append(results[0])
                    else:
                        misses.append(f'"{match}"')

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

        [name=<name>]                   Name of the card
        [set=<set>]                     Set the card was printed in (any, not just original printing)
        [cost=<cost>]                   Mana cost of the card
        [cmc=<cmc>]                     Mana value (formerly converted mana cost) of the card
        [colors=<colors>...]            Color(s) of the card
        [supertypes=<supertypes>...]    Supertypes of the card
        [type=<type>...]                Type of the card
        [subtypes=<subtype>...]         Subtypes of the card
        [rarity=<rarity>]               Card rarity
        [power=<power>]                 Creature's power
        [toughness=<power>]             Creature's toughness
        [text=<text>]                   Rules or flavor text on the card''',
        usage='[name=<name>] [set=<set>] [cost=<cost>] [cmc=<cmc>] [colors=<colors>...] [supertypes=<supertypes>...] [type=<type>...] [subtypes=<subtype>...] [rarity=<rarity>] [power=<power>] [toughness=<power>] [text=<text>]',
        brief='Search for a card',
        checks=[_msg_in_channel],
    )
    async def search(self, ctx: commands.Context, *args):
        page_size = Mtg._CFG['tasks.mtg.page_size']
        search = {}

        try:
            for term in args:
                param, args = term.split('=', 1)
                args = args.replace('\"', '')
                search[param] = args

            cards = await get_formatted_cards(search.get('name', ''), search.get('set', ''), search.get('cost', ''), \
                        search.get('cmc', ''), search.get('colors', ''), search.get('supertypes', ''), \
                        search.get('type', ''), search.get('subtypes', ''), search.get('rarity', ''), \
                        search.get('power', ''), search.get('toughness', ''), search.get('text', ''), '', \
                        page_size)
        except ValueError:
            await ctx.message.channel.send('Error processing search. Use !help search for details on how to use this command.')
            return

        if cards is None or len(cards) < 1:
            await ctx.message.channel.send('No cards found matching that search.')
            return

        elif len(cards) > page_size:
            await ctx.message.channel.send(f'{len(cards)} cards found which is more than the max of {page_size}. Please be more specific.')
            return

        else:
            cards.insert(0, (None, f'{len(cards)} results:', None))
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