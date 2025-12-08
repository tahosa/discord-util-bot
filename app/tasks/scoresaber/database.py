import logging
from typing import List
from enum import Enum

import config
from peewee import (SQL, CharField, ForeignKeyField, IntegerField, Model,
                    SqliteDatabase, fn, AutoField, TextField)

_LOG = logging.getLogger('discord-util').getChild('scoresaber').getChild('database')

# Uncomment these to see DB queries
# logger = logging.getLogger('peewee')
# logger.addHandler(logging.StreamHandler())
# logger.setLevel(logging.DEBUG)

database = SqliteDatabase(None)

class BaseModel(Model):
    '''
    Base database model so we don't have to duplicate this Meta
    '''
    class Meta:
        database = database


class Player(BaseModel):
    '''
    Represents a player. Links Steam, Discord, and ScoreSaber IDs
    '''
    steam_id = CharField(primary_key=True)
    discord_id = CharField(null=True)
    scoresaber_id = CharField(unique=True, null=False)


class Score(BaseModel):
    '''
    Individual song record. Only one per player ever exists and is updated when new high scores are recorded
    '''
    id = AutoField()
    song_name = CharField(null=False)
    song_artist = CharField()
    song_mapper = CharField()
    song_hash = CharField(null=False)
    difficulty = IntegerField(null=False)
    player = ForeignKeyField(Player, backref='player')
    score = IntegerField(null=False)
    image_url = TextField()
    beatsaver_url = TextField()

    class Meta:
        constraints = [SQL('UNIQUE(song_hash, difficulty, player_id)')]


class Difficulty(Enum):
    '''
    Translate numeric difficulty as tracked by scoresaber
    '''
    EASY = 1
    NORMAL = 3
    HARD = 5
    EXPERT = 7
    EXPERT_PLUS = 9

    def __format__(self, format_spec):
        '''
        Outputs for use in format() and f-strings
        '''
        if self.value == 1:
            return 'Easy'
        elif self.value == 3:
            return 'Normal'
        elif self.value == 5:
            return 'Hard'
        elif self.value == 7:
            return 'Expert'
        elif self.value == 9:
            return 'Expert+'
        else:
            return Enum.__format__(self, format_spec)


class Database:
    '''
    Class for interacting with the database
    '''
    db = database

    def __init__(self, cfg: config.Config):
        '''
        Initialize the database object. Creates tables if necessary.
        '''
        database.init(cfg['tasks.scoresaber.database'])

        if not self.db.table_exists('player'):
            self.db.create_tables([Player, Score])

    def get_players(self) -> List[Player]:
        '''
        Get the list of all players
        '''
        return Player.select()

    def create_player(self, steam_id: str, discord_id: str, scoresaber_id: str) -> Player:
        '''
        Create a new player in the database
        '''
        Player.create(steam_id=steam_id, discord_id=discord_id, scoresaber_id=scoresaber_id)
        return Player.get_by_id(steam_id)

    def update_score(self,
                     player: str,
                     song_hash: str,
                     difficulty: Difficulty,
                     score: int,
                     song_name: str,
                     song_artist: str = '',
                     song_mapper: str = '',
                     image_url: str = None,
                     beatsaver_url: str = None) -> Score:
        '''
        Create or update a high score for a specific song by a player.

        If a record doesn't exist, create a new high score for a song. If a record exists,
        update it if the new score is higher. Returns true if the score was created or updated,
        false otherwise.
        '''

        # Find if there is already a score for this player in the table
        old_score = Score.select() \
            .where((Score.player == player) & (Score.song_hash == song_hash) & (Score.difficulty == difficulty)) \
            .order_by(Score.score.desc()) \
            .limit(1)

        if len(old_score): # Score already recorded
            _LOG.log(level = 5, msg = f'Found old score of {old_score[0].score} for {player} on {song_name}')

            # Default: score wasn't higher than one already in the database
            retval = None

            if old_score[0].image_url != image_url:
                old_score[0].image_url = image_url

            if old_score[0].beatsaver_url != beatsaver_url:
                old_score[0].beatsaver_url = beatsaver_url

            if score > old_score[0].score: # Is it higher than what we have?
                old_score[0].score = score
                retval = old_score[0]

            old_score[0].save()
            return retval

        else: # New song
            return Score.create(song_hash=song_hash,
                            player=player,
                            score=score,
                            difficulty=difficulty,
                            song_name=song_name,
                            song_artist=song_artist,
                            song_mapper=song_mapper,
                            image_url=image_url,
                            beatsaver_url=beatsaver_url)


    def get_player_scores(self, player: str, limit: int = 100) -> List[Score]:
        '''
        Get the list of scores for a specific player
        '''
        return Score.select().where(Score.player == player).order_by(Score.score.desc()).limit(limit)


    def get_high_scores(self) -> List[Score]:
        '''
        Get the current high-score records
        '''
        return Score.select(Score, Player, fn.Max(Score.score).alias('high_score')) \
                    .join(Player) \
                    .group_by(Score.song_hash, Score.difficulty) \
                    .prefetch(Player)


    def get_song_scores(self, song_hash: str, difficulty: Difficulty) -> List[Score]:
        '''
        Get the scores for a particular song
        '''
        return Score.select() \
            .join(Player) \
            .where((Score.song_hash == song_hash) & (Score.difficulty == difficulty)) \
            .order_by(Score.score.desc()) \
            .prefetch(Player)

    def get_top_search(self, search_str: str) -> List[Score]:
        '''
        Search for songs and return the top score for all difficulties found, if any
        '''
        # Alias partitioning from: https://charlesleifer.com/blog/querying-the-top-n-objects-per-group-with-peewee-orm/
        score_alias = Score.alias()

        subquery = (score_alias
                        .select(score_alias, fn.RANK().over(
                            partition_by=[score_alias.song_hash, score_alias.difficulty],
                            order_by=[score_alias.score.desc()]).alias('rk')
                        ).alias('subq'))

        return Score.select(Score, Player) \
            .join(Player) \
            .switch(Score) \
            .join(subquery, on=((subquery.c.id == Score.id) & (subquery.c.rk == 1))) \
            .where((Score.song_name ** f'%{search_str}%')) \
            .group_by(Score.song_hash, Score.difficulty) \
            .order_by(Score.song_name.asc()) \
            .prefetch(Player)
