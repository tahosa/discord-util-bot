from typing import List

from pydantic import BaseModel


class RunConfig(BaseModel):
  enabled: bool = False

class UwuConfig(RunConfig):
  enabled: bool = True

class ScoresaberConfig(RunConfig):
  enabled: bool = False
  channels: List[int] = []
  database: str = ''
  power_users: List[int] = []
  update_interval: float = 60.0

class MtgConfig(RunConfig):
  enabled: bool = False
  channels: List[int] = []
  page_size: int = 5

class TaskConfig(BaseModel):
  uwu: UwuConfig
  scoresaber: ScoresaberConfig
  mtg: MtgConfig

class BotConfig(BaseModel):
  bot_token: str
  tasks: TaskConfig
