import logging
from typing import List

import aiohttp
from discord import Embed

from . import scoresaber_url, beatsaver_api_url, beatsaver_maps_url
from .database import Database, Score, Difficulty

_LOG = logging.getLogger('discord-util').getChild('scoresaber').getChild('updater')


class ScoreUpdater:
    database: Database = None
    _current_high: List[Score] = []

    def __init__(self, database: Database):
        self.database = database
        self._current_high = self.database.get_high_scores()


    async def update(self, force_all=False) -> List[(str, Embed)]:
        '''
        Query scoresaber for new scores and update the database. Returns a list of new records.
        '''
        players = self.database.get_players()
        _LOG.debug(f'Found {len(players)} players')

        limit = 5 if not force_all else 100
        new_pbs = []

        for player in players:
            async with aiohttp.ClientSession() as session:
                _LOG.debug(f'Fetching new scores for {player.steam_id}')
                page = 1
                while True:
                    fetch_url = f'{scoresaber_url}/player/{player.scoresaber_id}/scores?sort=recent&limit={limit}&page={page}'
                    _LOG.log(level = 5, msg = f'GET {fetch_url}')
                    async with session.get(fetch_url) as r:
                        if r.status == 200:
                            json = await r.json()
                            scores = json['playerScores']
                            if len(scores) <= 0:
                                _LOG.debug(f'No more scores to parse')
                                break

                            _LOG.debug(f'Found {len(scores)} to parse')
                            for wrapper in scores:
                                board = wrapper['leaderboard']
                                score = wrapper['score']

                                _LOG.log(level = 5, msg = f'Updating new score for {board['songName']}')
                                beatsaver_search_url = f'{beatsaver_api_url}/maps/hash/{board['songHash']}'
                                beatsaver_song_url = None
                                async with session.get(beatsaver_search_url) as b:
                                    if b.status == 200:
                                        beatsaver_json = await b.json()
                                        beatsaver_song_url = f'{beatsaver_maps_url}/{beatsaver_json['id']}'

                                new_high = self.database.update_score(
                                    player=player.steam_id,
                                    song_hash=board['songHash'],
                                    song_name=board['songName'],
                                    song_artist=board['songAuthorName'],
                                    song_mapper=board['levelAuthorName'],
                                    difficulty=board['difficulty']['difficulty'],
                                    score=score['modifiedScore'],
                                    image_url=board['coverImage'],
                                    beatsaver_url=beatsaver_song_url
                                )

                                if new_high and new_high not in new_pbs:
                                    new_pbs.append(new_high)
                            page += 1

                        else:
                            _LOG.debug(f'Bad return status {r.status} {r.reason}')
                            break

                    if not force_all:
                        break

        if len(new_pbs):
            new_overall = self.database.get_high_scores()

            # Get a list of scores where there is a new player in the top slot
            # The iterator tracks by ID, and since we update existing rows if a player beats their
            # own high score it won't appear in this list
            updated_overall = [value for value in new_overall if value not in self._current_high]

            # Save the updated list now we don't need the old scores
            self._current_high = new_overall

            response: List[(str, Embed)] = []
            for score in new_pbs:
                score_string = ''
                embed = Embed(title=score.song_name, url=score.beatsaver_url)

                if score.image_url is not None:
                    embed.set_thumbnail(url=score.image_url)

                # Add the mention if there is a discord ID
                if score.player.discord_id:
                    score_string = f'<@{score.player.discord_id}>'
                else:
                    score_string = score.player.steam_id

                embed.add_field(name='Score', value=score.score, inline=True)
                embed.add_field(name='Difficulty', value=f'{Difficulty(score.difficulty)}', inline=True)

                if score in updated_overall: # Beat another player
                    song_leaderboard = self.database.get_song_scores(score.song_hash, score.difficulty)

                    if len(song_leaderboard) > 1:
                        old_leader = song_leaderboard[1]
                        embed.add_field(name='Previous High Score', value=old_leader.score, inline=False)

                        if old_leader.player.discord_id:
                            discord_tag = f'<@{old_leader.player.discord_id}>'
                            score_string += f' beat {discord_tag} and'
                            embed.add_field(name='Previous Leader', value=discord_tag, inline=True)
                        else:
                            steam_id = old_leader.player.steam_id
                            score_string += f' beat {steam_id} and'
                            embed.add_field(name='Previous Leader', value=steam_id, inline=True)


                score_string += f' set a new high score!'

                if score.song_artist:
                    embed.add_field(name='Artist', value=score.song_artist, inline=False)

                if score.song_mapper:
                    embed.add_field(name='Mapper', value=score.song_mapper, inline=False)

                response.append((score_string, embed))

            return response

        else:
            return []
