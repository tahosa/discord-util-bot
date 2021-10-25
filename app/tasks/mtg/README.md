Mtg
===

This task gives channels the ability to automatically include information about Magic: The Gathering cards. It adds one command for advanced searching, and a message handler for finding card names marked to be fetched. Data is source from [Scryfall](https://scryfall.com) using [Scrython](https://github.com/NandaScott/Scrython)

Using
-----

#### Look up cards mentioned in messages

For the configured channels, any messages with the following syntax the bot will attempt to look up the information: `This is a message with the card [[lightning bolt]] marked for lookup`. The `[[<card name>|<set>]]` syntax is used to do an exact lookup, and if the card isn't found a message is printed. Multiple cards can be specified in each message. The `|<set>` suffix can be used to fetch a specific version of a card if the three-letter set code is provided. An attempt will be made to identify the exact card using Scryfall's auto-complete mechanism and fuzzy-matching.

### Commands

Only one command is currently registered for this task, but it is very powerful.

#### `!search <query>`

This will do a search through the list of all Magic cards currently in Scryfall to meet the various criteria you set. It uses the query engine provided by Scryfall, so any of the query options they provide in their [advanced text search](https://scryfall.com/docs/syntax) can be used.

Configuration
-------------

The following values can be set in `server.cfg` under the `Mtg` section to change the behavior of this task.

### `enabled`: `bool`

Whether or not to use this task. If `false`, the Mtg module will not be initialized when the bot starts.

#### `channels`: `List[int]`

A list of all the numeric channel IDs you want to bot to listen in for commands and card lookups. You can get these from the Discord developer extensions (right-click the channel and choose 'Copy ID').

### `page_size`: `int`

The maximum number of results to return for a search. If this is a big number your chat will be very spammy, so the default is set to 5.
