Mtg
===

This task gives channels the ability to automatically include information about Magic: The Gathering cards. It adds one command for advanced searching, and a message handler for finding card names marked to be fetched.

Using
-----

#### Look up cards mentioned in messages

For the configured channels, any messages with the following syntax the bot will attempt to look up the information: `This is a message with the card [[lightning bolt]] marked for lookup`. The `[[<card name>|<set>]]` syntax is used to do an exact lookup, and if the card isn't found a message is printed. Multiple cards can be specified in each message. The `|<set>` suffix can be used to fetch a specific version of a card if the three-letter set code is provided.

### Commands

Only one command is currently registered for this task, but it has lots of options.

#### `!search [name=<name>] [set=<set>] [cost=<cost>] [cmc=<cmc>] [colors=<colors>...] [supertypes=<supertypes>...] [type=<type>...] [subtypes=<subtype>...] [rarity=<rarity>] [power=<power>] [toughness=<power>] [text=<text>]`

This will do a relatively fuzzy search through the list of all Magic cards to meet the various criteria you set. Currently, it doesn't handle spaces very well, but that is on the list to fix.

For items which can be specified more than once (e.g. type), separate the items with a comma. For example, if you want to search for cards which are both Human and Wizard, you would use `type=human,wizard`.

For more details on each option, run `!help search` from an enabled channel.

Configuration
-------------

The following values can be set in `server.cfg` under the `Mtg` section to change the behavior of this task.

### `enabled`: `bool`

Whether or not to use this task. If `false`, the Mtg module will not be initialized when the bot starts.

#### `channels`: `List[int]`

A list of all the numeric channel IDs you want to bot to listen in for commands and card lookups. You can get these from the Discord developer extensions (right-click the channel and choose 'Copy ID').

### `page_size`: `int`

The maximum number of results to return for a search. If this is a big number your chat will be very spammy, so the default is set to 5.
