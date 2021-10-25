import aiohttp
import io
import logging
import scrython
import time

_LOG = logging.getLogger('discord-util').getChild("mtg").getChild('cards')

rate_limit = 0.05

def format_nameline(name: str, cost: str):
    fmt_string = f'**{name}**'
    if cost is not None:
        fmt_string += f'  {cost}'
    return fmt_string


def format_flavor(text: str):
    if text is None:
        return ''
    fmt_string = '_{}_'.format(text.replace('\n', '_\n_'))
    return fmt_string

def format_link(url: str):
    return url.split('?')[0]

async def parse_scryfall_dict(card: dict) -> 'tuple[str, str, io.BytesIO]':
    '''
    Parse the raw scryfall JSON ourselves

    Search results only return the JSON, not the scrython Card
    object, and we don't want to duplicate this.
    '''
    nameline = f'>>> {format_nameline(card["name"], card["mana_cost"])}'
    typeline = card['type_line']
    textline = card['oracle_text']
    flavorline = ''
    try:
        flavorline = f'{format_flavor(card["flavor_text"])}'
    except KeyError:
        pass
    source_link = f'<{format_link(card["scryfall_uri"])}>'

    lines = [nameline, typeline, textline, flavorline, source_link]
    text = '\n'.join([line for line in lines if line])

    data = None
    async with aiohttp.ClientSession() as session:
        normal_uri = card['image_uris']['normal']
        async with session.get(normal_uri) as resp:
            if resp.status != 200:
                text.append(f'\n{card.image_url}')
            else:
                data = io.BytesIO(await resp.read())

    return (card['name'], text, data)


async def get_card(name: str, set: str = '') -> 'tuple[str, str, io.BytesIO]':
    '''Get a single card with near-exact matching from scryfall'''
    try:
        if set:
            card = scrython.cards.Named(fuzzy=name, set=set)
        else:
            card = scrython.cards.Named(fuzzy=name)
    except Exception as ex:
        time.sleep(rate_limit)
        auto = scrython.cards.Autocomplete(q=name, query=name)

        if auto and len(auto.data()) == 1:
            time.sleep(rate_limit)
            card = scrython.cards.Named(exact=auto.data()[0])
        else:
            return None

    return await parse_scryfall_dict(card.scryfallJson)


async def scryfall_search(query: str, max: int = 5) -> 'tuple[list[tuple[str, str, io.BytesIO]], str]':
    '''Search scryfall for cards'''
    try:
        cards = scrython.cards.Search(q=query)

        if cards.total_cards() > max:
            return (None, f'Found {cards.total_cards()} matches. Please narrow your search')

        results = []
        for card in cards.data():
            results.append(await parse_scryfall_dict(card))
            time.sleep(rate_limit)

        return (results, None)
    except Exception as ex:
        return (None, 'Unexpected error when searching')
