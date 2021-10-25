import aiohttp
import io
import logging
from aiohttp.payload_streamer import streamer
import mtgsdk

_LOG = logging.getLogger('discord-util').getChild("mtg").getChild('cards')

gatherer_base_url = 'https://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid='


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


def get_cards(card_name='', card_set='', card_mana_cost='', card_cmc='', card_colors='', \
    card_supertypes='', card_type='', card_subtypes='', card_rarity='', card_power='', \
    card_toughness='', card_text='', page='', pageSize=5):
    '''Get a list of cards from the MTG database'''
    try:
        cards = mtgsdk.Card.where(name=card_name, set=card_set, mana_cost=card_mana_cost, cmc=card_cmc, \
            colors=card_colors, supertypes=card_supertypes, type=card_type, subtypes=card_subtypes, \
            rarity=card_rarity, power=card_power, toughness=card_toughness, text=card_text, \
            page=page, pageSize=pageSize).all()

    except mtgsdk.MtgException as err:
        cards = []
        _LOG.critical(f'Error with card search:\n{err}')

    return cards


async def get_formatted_cards(card_name='', card_set='', card_mana_cost='', card_cmc='', card_colors='', \
    card_supertypes='', card_type='', card_subtypes='', card_rarity='', card_power='', card_toughness='', \
    card_text='', page='', pageSize=5) -> 'list[(str, str, io.BytesIO)]':
    responses = []
    unique_cards = []
    cards = get_cards(card_name, card_set, card_mana_cost, card_cmc, \
        card_colors, card_supertypes, card_type, card_subtypes, \
        card_rarity, card_power, card_toughness, card_text)

    _LOG.debug(f'Formatting {len(cards)} cards')
    async with aiohttp.ClientSession() as session:
        for card in cards:
            if card.name in unique_cards:
                continue
            nameline = f'>>> {format_nameline(card.name, card.mana_cost)}'
            typeline = f'{card.type}'
            raresetline = f'{card.set} - {card.rarity}'
            textline = card.text
            flavorline = f'{format_flavor(card.flavor)}'
            source_link = f'<{gatherer_base_url}{card.multiverse_id}>' if card.multiverse_id else '_`Source Missing`_'

            lines = [nameline, typeline, raresetline, textline, flavorline, source_link]
            text = '\n'.join([line for line in lines if line])

            if isinstance(card.image_url, str):
                async with session.get(card.image_url) as resp:
                    if resp.status != 200:
                        text.append(f'\n{card.image_url}')
                    else:
                        data = io.BytesIO(await resp.read())
            else:
                data = None

            unique_cards.append(card.name)
            responses.append((card.name, text, data))

    return responses
