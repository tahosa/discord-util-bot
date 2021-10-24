Scoresaber Tracking
===================

This is a task for tracking and comparing the scores of players using the ScoreSaber mod in Beat Saber. The bot will periodically check the ScoreSaber servers for new scores for registered players and post the results, including if a high-score from one player is beaten by another, and will post updates to the configured channel. Users are registered using the `!register` command [detailed below](#Using).

Using
-----

There are currently 4 commands that can be used when this task is emabled. The bot will only respond to these triggers in the channels specified in the server config [(see Configuration)](#Configuration)

#### `!register <steam_id> [discord#id]`

This adds a new user to the tracking database. For `steam_id` use the complete, unique Steam ID. This is currently problematic if you have a steam ID that is a substring of one or more other steam IDs (e.g. `apple`) since the scoresaber API is a bulk search and may return multiple results.

`discord#id` is the server-unique name and discriminator code for that user in your server. The user must be in your server for the registration to work since the lookup is done on the server members. This is optional, but if specified will mention that user when they break a record.

#### `!update [--force] [--quiet]`

Force an update of the scores list. The server will automatically update the list when a new user is registered, and on the interval specified in the [(configuration file)](#Configuration).

If the `--force` flag is set, the system will import all scores from all registered players by paging through scoresaber data. This operation may take some time, and be too long to display all results. Discord caps messages at 2000 characters, and if the total message exceeds this the bot will simply use the same output as if the `--quiet` flag was set.

The `--quiet` flag prints simply the number of scores which were updated instead of a detailed list of players, songs, and scores.

#### `!list`

List the currently registered users

#### `!scores <steam_id> [limit]`

List a number of the top scores of the specified preregistered user, up to `limit`. Unlike the `!register` command, this command reads the local database for users and will exact-match the given `steam_id` instead of fuzzy-match/searching.

#### `!top <search>`

Search for any songs whose name matches the search string and sends back the list of matching high scores by song and difficulty. The search string may include SQL wildcards. This search should be injection-safe as the query is parameterized for input sanitization purposes. Searches with too many results for discord's default output (2000 characters) will not be sent and a request to narrow the search will be sent instead.

Configuration
-------------

The following values can be set in `server.cfg` under the `scoresaber` section to change the behavior of this task.

### `enabled`: `bool`

Whether or not to use this task. If `false`, the scoresaber module will not be initialized when the bot starts.

#### `channels`: `List[int]`

A list of all the numeric channel IDs you want to bot to listen in for commands. You can get these from the Discord developer extensions (right-click the channel and choose 'Copy ID'). Only the first entry in the list will be the one where updated scores are posted automatically.

#### `database`: `string`

The name of the sqlite3 database file to use. You are free to rename the database file whatever you want. If it does not exist or is empty it will be created on the first run. If you want to reset the score tracking: stop the bot, delete the datbase file, and restart the bot.

#### `power_users`: `List[string]`

A list of those users you wish to be able to register other users or force a manual update of the score database. The database is automatically updated when a new user is registered. They should be spefied using their server-specific name and discriminator in the format `user#discriminator`, e.g. `someUser#1234`.

#### `update_interval`: `float`

Time, in seconds, between checking the scoresaber API for new scores. The recommended interval is 1 minute (60.0 seconds) but you are free to specify any interval.
