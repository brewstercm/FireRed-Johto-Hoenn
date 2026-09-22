"""Authored story-access ranks, not data claimed to be supplied by PokeAPI.

0 = opening, 1..8 = approximate badge milestones, 9 = postgame.
Ranks describe normal progression, not a hard badge lock (both games branch).
"""

CRYSTAL = {
    0: 'new-bark-town cherrygrove-city violet-city johto-route-29 johto-route-30 johto-route-31 johto-route-46 ruins-of-alph dark-cave',
    1: 'johto-route-32 johto-route-33 union-cave azalea-town ilex-forest',
    2: 'johto-route-34 johto-route-35 goldenrod-city national-park johto-route-36',
    3: 'johto-route-37 johto-route-38 johto-route-39 olivine-city ecruteak-city bell-tower',
    4: 'johto-sea-route-40 johto-sea-route-41 cianwood-city johto-route-42 johto-route-43 lake-of-rage mt-mortar whirl-islands',
    7: 'johto-route-44 johto-route-45 ice-path blackthorn-city',
    8: 'kanto-route-26 kanto-route-27',
    9: 'mt-silver pallet-town pewter-city vermilion-city celadon-city cinnabar-island kanto-route-1 kanto-route-2 kanto-route-5 kanto-route-6 kanto-route-7 kanto-route-8 kanto-route-11 kanto-route-12 kanto-route-13 kanto-route-14 kanto-route-15 kanto-route-16 kanto-route-17 kanto-route-18 kanto-route-24 kanto-route-25 kanto-sea-route-19 kanto-sea-route-20 kanto-sea-route-21',
}

EMERALD = {
    0: 'hoenn-route-101 hoenn-route-102 hoenn-route-103 hoenn-route-104 petalburg-city petalburg-woods rustboro-city hoenn-route-116 rusturf-tunnel',
    1: 'dewford-town granite-cave hoenn-route-106 hoenn-route-107',
    2: 'slateport-city hoenn-route-109 hoenn-route-110 hoenn-route-117 mauville-city',
    3: 'hoenn-route-111 hoenn-route-112 hoenn-route-113 hoenn-route-114 fiery-path meteor-falls jagged-pass lavaridge-town',
    4: 'mirage-tower',
    5: 'hoenn-route-105 hoenn-route-108 hoenn-route-115 hoenn-route-118 hoenn-route-119 fortree-city hoenn-route-120',
    6: 'hoenn-route-121 hoenn-route-122 hoenn-route-123 lilycove-city mt-pyre magma-hideout',
    7: 'hoenn-route-124 hoenn-route-125 hoenn-route-126 hoenn-route-127 hoenn-route-128 mossdeep-city shoal-cave seafloor-cavern',
    8: 'hoenn-route-129 hoenn-route-130 hoenn-route-131 hoenn-route-132 hoenn-route-133 hoenn-route-134 pacifidlog-town mirage-island sky-pillar ever-grande-city hoenn-victory-road',
    9: 'desert-underpass',
}


def source_stage(version, location, area, method, species):
    groups = CRYSTAL if version == 'crystal' else EMERALD
    ranks = {name: rank for rank, names in groups.items() for name in names.split()}
    if location not in ranks:
        raise ValueError(f'Unranked source: {version} {location}/{area}')
    rank = ranks[location]

    if version == 'crystal':
        if location == 'ruins-of-alph' and method == 'walk' and species in ('natu', 'smeargle', 'quagsire'):
            rank = 4
        if location == 'dark-cave' and area == 'blackthorn-city-entrance':
            rank = 7
        if location == 'union-cave' and area == 'b2f':
            rank = max(rank, 4)
        if location == 'mt-mortar' and area == 'upper-cave':
            rank = 8
        if method.startswith('headbutt'):
            rank = max(rank, 2)
        if method == 'rock-smash':
            rank = max(rank, 3)
        if method in ('surf', 'good-rod'):
            rank = max(rank, 4)
        if method == 'super-rod':
            rank = max(rank, 9)
    else:
        if location == 'hoenn-route-111' and species in ('trapinch', 'cacnea', 'baltoy'):
            rank = 4
        if location == 'meteor-falls' and area in ('b1f', 'back', 'backsmall-room'):
            rank = 8
        if method == 'rock-smash':
            rank = max(rank, 3)
        if method in ('surf', 'good-rod', 'feebas-tile-fishing'):
            rank = max(rank, 5)
        if method in ('super-rod', 'seaweed'):
            rank = max(rank, 7)

    return rank


def target_stage(name):
    """FRLG's first normal access to a map; water/rod floors applied separately."""
    import re

    route = re.fullmatch(r'ROUTE(\d+)(?:_NORTH|_SOUTH)?', name)
    if route:
        n = int(route[1])
        for rank, nums in {
            0: (1, 2, 22),
            1: (3, 4),
            2: (5, 6, 24, 25),
            3: (9, 10, 11),
            4: (7, 8, 12, 13, 14, 15, 16, 17, 18),
            5: (19, 20, 21),
            8: (23,),
        }.items():
            if n in nums:
                return rank

    prefixes = {
        0: ('VIRIDIAN_FOREST', 'PALLET_TOWN', 'VIRIDIAN_CITY'),
        1: ('MT_MOON',),
        2: ('CERULEAN_CITY', 'VERMILION_CITY', 'SSANNE', 'DIGLETTS_CAVE'),
        3: ('ROCK_TUNNEL',),
        4: ('POKEMON_TOWER', 'CELADON_CITY', 'FUCHSIA_CITY', 'SAFARI_ZONE'),
        5: ('SEAFOAM_ISLANDS', 'POWER_PLANT', 'CINNABAR_ISLAND', 'POKEMON_MANSION'),
        7: ('ONE_ISLAND', 'TWO_ISLAND', 'THREE_ISLAND', 'MT_EMBER_EXTERIOR', 'MT_EMBER_SUMMIT'),
        8: ('VICTORY_ROAD',),
        9: ('CERULEAN_CAVE', 'FOUR_ISLAND', 'FIVE_ISLAND', 'SIX_ISLAND', 'SEVEN_ISLAND', 'MT_EMBER_RUBY'),
    }
    for rank, names in prefixes.items():
        if name.startswith(names):
            return rank

    raise ValueError('Unranked FireRed map: ' + name)


def habitat(name):
    """Classify a source or FRLG map into a broad ecological habitat."""
    name = name.lower().replace('_', '-')

    if any(s in name for s in ('seafoam', 'shoal', 'ice-path', 'icefall')):
        return 'ice'

    if any(s in name for s in ('pokemon-tower', 'lost-cave', 'mt-pyre')):
        return 'ghost'

    if any(s in name for s in ('fiery', 'jagged', 'magma', 'ember', 'mansion')):
        return 'volcanic'

    if name in {
        'celadon-city',
        'vermilion-city',
        'kanto-route-7',
        'kanto-route-8',
        'kanto-route-16',
        'route7',
        'route8',
        'route16',
    }:
        return 'urban'

    if (
        'sea-route' in name
        or name in {
            'route19', 'route20', 'route21',
            'one-island', 'two-island', 'three-island',
            'four-island', 'five-island', 'six-island', 'seven-island',
            'hoenn-route-103', 'hoenn-route-105', 'hoenn-route-106',
            'hoenn-route-107', 'hoenn-route-108', 'hoenn-route-109',
            'hoenn-route-124', 'hoenn-route-125', 'hoenn-route-126',
            'hoenn-route-127', 'hoenn-route-128', 'hoenn-route-129',
            'hoenn-route-130', 'hoenn-route-131',
        }
    ):
        return 'coast'

    if name in {
        'new-bark-town',
        'lake-of-rage',
        'hoenn-route-118',
        'hoenn-route-119',
        'hoenn-route-120',
        'route6',
        'route12',
        'route13',
    }:
        return 'wetland'

    if any(s in name for s in (
        'cave', 'moon', 'tunnel', 'mortar',
        'meteor', 'victory', 'granite',
        'ruins', 'mirage-tower',
    )):
        return 'cave'

    if any(s in name for s in ('forest', 'woods', 'park', 'bush')):
        return 'forest'

    if name in {
        'johto-route-45',
        'johto-route-46',
        'hoenn-route-111',
        'hoenn-route-112',
        'hoenn-route-113',
        'hoenn-route-114',
        'route3',
        'route4',
        'route9',
        'route10',
        'route23',
    }:
        return 'mountain'

    return 'field'


def source_phase(rank):
    return 0 if rank <= 1 else 1 if rank <= 3 else 2 if rank <= 6 else 3 if rank <= 7 else 4 if rank == 8 else 5


def target_phase(rank):
    return 0 if rank <= 1 else 1 if rank <= 3 else 2 if rank == 4 else 3 if rank <= 7 else 4 if rank == 8 else 5
