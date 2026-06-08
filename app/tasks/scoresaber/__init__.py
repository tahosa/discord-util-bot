from typing import List

from pydantic import BaseModel


class ScoresaberDifficulty(BaseModel):
  leaderboardId: int
  difficulty: int
  gameMode: str
  difficultyRaw: str

class ScoresaberLeaderboard(BaseModel):
  id: int
  songHash: str
  songName: str
  songSubName: str
  songAuthorName: str
  levelAuthorName: str
  difficulty: ScoresaberDifficulty
  maxScore: int
  createdDate: str
  rankedDate: str | None
  qualifiedDate: str | None
  lovedDate: str | None
  ranked: bool
  qualified: bool
  loved: bool
  maxPP: float
  stars: float
  plays: int
  dailyPlays: int
  positiveModifiers: bool
  playerScore: int | None
  coverImage: str
  difficulties: List[ScoresaberDifficulty] | None

class ScoresaberScore(BaseModel):
  id: int
  rank: int
  baseScore: int
  modifiedScore: int
  pp: float
  weight: float
  modifiers: str
  multiplier: float
  badCuts: int
  missedNotes: int
  maxCombo: int
  fullCombo: bool
  hmd: int
  timeSet: str
  hasReplay: bool

scoresaber_url = 'https://scoresaber.com/api/v1'
beatsaver_api_url = 'https://api.beatsaver.com'
beatsaver_maps_url = 'https://beatsaver.com/maps'
