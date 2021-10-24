import aiohttp
import config
import discord
from discord.ext import tasks
import discord.ext.commands as commands
import logging
from peewee import IntegrityError

from ..task import Task

from .database import Database, Difficulty, Score
from .updater import ScoreUpdater

_LOG = logging.getLogger('discord-util').getChild("scoresaber")
scoresaber_url = 'https://new.scoresaber.com/api'


def _is_power_user(ctx: commands.Context) -> bool:
    '''Check if the message was sent by a configured power user'''
    return f'{ctx.author.name}#{ctx.author.discriminator}' in Scoresaber._CFG['tasks.scoresaber.power_users']


def _msg_in_channel(ctx: commands.Context) -> bool:
    '''Check if the message was posted in a monitored channel'''
    return ctx.message.channel.id in Scoresaber._CFG['tasks.scoresaber.channels']


def _format_score(score: Score) -> str:
    '''Format a score for printing'''
    result = f'{score.song_name}'

    if score.song_artist:
        result += f' by {score.song_artist}'

    if score.song_mapper:
        result += f' [map by {score.song_mapper}]'

    result += f' ({Difficulty(score.difficulty)}): {score.score}'

    return result

class Scoresaber(Task, commands.Cog):
    database: Database
    updater: ScoreUpdater

    def __init__(self, bot: commands.Bot, cfg: config.Config):
        Task.__init__(self, bot, cfg)
        Scoresaber._CFG = cfg

        self.database = Database(cfg)
        self.updater = ScoreUpdater(self.database)


        @tasks.loop(seconds=cfg['tasks.scoresaber.update_interval'])
        async def run():
            '''Periodically check for new scores'''
            _LOG.debug('Checking for new scores')
            channel = self.bot.get_channel(cfg['tasks.scoresaber.channels'][0])
            with self.database.db:
                new_scores = await self.updater.update()

            _LOG.debug(f'Found {len(new_scores)} new high scores')
            if len(new_scores) > 0:
                for score in new_scores:
                    await channel.send(score)

        self._run = run


    @commands.command(
        help='''Update the list of scores recorded in scoresaber

        --force  Force the database to update history from all time
        --quiet  Suppres detailed output from this command. The number of scores updated will be printed instead of the list of scores.
        ''',
        usage='[--force] [--quiet]',
        brief='Update the list of scores',
        checks=[_msg_in_channel, _is_power_user],
    )
    async def update(self, ctx: commands.Context, *args):
        force = '--force' in ctx.message.content
        quiet = '--quiet' in ctx.message.content

        with self.database.db:
            new_records = await self.updater.update(force)

        await ctx.message.channel.send('High Scores Updated!')

        response = ''
        if len(new_records) > 0:
            for record in new_records:
                response += f'{record}\n'
        else:
            response = 'No new high scores.'

        if len(response) > 2000 or quiet:
            await ctx.message.channel.send(f'{len(new_records)} new high scores.')
        else:
            await ctx.message.channel.send(response)


    @update.error
    async def update_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            if _msg_in_channel(ctx):
                await ctx.message.channel.send('Only power users can use the update command')
        else:
            raise error


    @commands.command(
        help='''Register a new player to the database

        <steam_id>    Steam ID of the player to register. The full name must be used, but may still have errors if the name is not truly unique
        [discord#id]  (Optional) Discord identifier to tag in messages related to this player
        ''',
        usage='<steam_id> [discord#id]',
        brief='Register a player',
        checks=[_msg_in_channel,_is_power_user],
    )
    async def register(self, ctx: commands.Context, *args) -> bool:
        '''
        Register a new player
        '''
        if len(args) < 1 or len(args) > 2:
            await ctx.message.channel.send(f'Invalid register command. Usage: `!register <steam_id> [discord#id]`')
            return

        steam_id = args[0]

        # If we were given a discord ID, look them up; they must be in the server users
        if len(args) == 2:
            (name, discriminator) = args[1].split('#')
            discord_user = discord.utils.get(ctx.message.guild.members, name=name, discriminator=discriminator)

            if discord_user is None:
                await ctx.message.channel.send(f'Discord user "{args[2]}" not found')
                return False

            discord_id = discord_user.id
        else:
            discord_id = None

        async with aiohttp.ClientSession() as session, self.database.db:
            _LOG.debug(f'Looking up `{steam_id}`')
            url = f'{scoresaber_url}/players/by-name/{steam_id}'
            _LOG.debug(f'GET {url}')
            async with session.get(url) as r:
                _LOG.debug(f'Response from server. Code {r.status}')

                if r.status == 200:
                    result = await r.json()
                    if len(result['players']) > 0:
                        player = result['players'][0]
                        try:
                            self.database.create_player(steam_id, discord_id, player['playerId'])
                            response = f'{player["playerName"]} registered!'
                            _LOG.info(response)
                            await ctx.message.channel.send(response)
                            return True
                        except IntegrityError as ex:
                            _LOG.exception(ex)
                            response = f'{steam_id} is already registerd.'
                            await ctx.message.channel.send(response)
                            return False
                        except Exception as ex:
                            _LOG.exception(ex)
                            response = f'Failed to register {steam_id}. {ex}'
                            await ctx.message.channel.send(response)
                            return False

                if r.status == 404:
                    await ctx.message.channel.send(f'Player "{steam_id}" not found')
                    return False


    @register.error
    async def register_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            if _msg_in_channel(ctx):
                await ctx.message.channel.send('Only power users can use the register command')
        else:
            raise error

    @commands.command(
        help='List all the plyers in the database',
        brief='List players',
        checks=[_msg_in_channel],
    )
    async def list(self, ctx: commands.Context):
        '''
        List the steam IDs of all registered players
        '''
        with self.database.db:
            players = [player.steam_id for player in self.database.get_players()]
            await ctx.message.channel.send(f'Player list: {", ".join(players)}')

    @list.error
    async def list_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            return
        else:
            raise error


    @commands.command(
        help='''Get scores for a specific player registered.

        <steam_id>  Steam ID of the player to fetch scores for
        [limit]     Number of score to fetch [Default: 10]''',
        brief='Get scores for players',
        usage='<steam_id> [limit]',
        checks=[_msg_in_channel],
    )
    async def top(self, ctx: commands.Context, *args):
        '''
        Get the list of scores for a player by steam ID
        '''
        if(len(args) < 1):
            await ctx.message.channel.send(f'Invalid scores command. Usage: `!scores <steam_id> [limit]`')

        player = args[0]
        limit = 10
        if(len(args) > 1):
            limit = args[1]

        with self.database.db:
            scores = self.database.get_player_scores(player, limit)

        if not scores:
            await ctx.message.channel.send(f'No scores found for {player}')
            return

        reply = f'Top scores for {player}: \n'
        for score in scores:
            reply += f'{_format_score(score)}\n'

        await ctx.message.channel.send(reply)


    @top.error
    async def top_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            return
        else:
            raise error


    @commands.command(
        help='''Search for scores in the database

        <search_term>...  Search term to look for in the database. All terms will be joined with a space before searching''',
        brief='Search for scores',
        usage='<search_term>...',
        checks=[_msg_in_channel],
    )
    async def scores(self, ctx: commands.Context, *args):
        '''
        Get a list of scores matching a search
        '''
        search = " ".join(args)
        if len(search) < 1:
            await ctx.message.channel.send('No search string specified')
            return

        with self.database.db:
            results = self.database.get_top_search(search)

        response = f'Top scores for songs matching `{search}`:\n'
        for score in results:
            response += f'{score.player.steam_id}: {_format_score(score)}\n'

        if len(response) > 2000:
            await ctx.message.channel.send(f'Too many results to display ({len(results)}). Try a narrower search.')

        else:
            await ctx.message.channel.send(response)


    @top.error
    async def scores_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            return
        else:
            raise error
