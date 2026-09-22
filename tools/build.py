"""Build native FireRed/LeafGreen table additions and auditable placement reports.

Python 3.10+, standard library only. All inputs are checked-in snapshots.
Does not download or package ROMs, graphics, or engine source.
"""

import collections
import csv
import hashlib
import json
import re
from pathlib import Path

from progression import source_stage, target_stage, habitat, source_phase, target_phase


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tools/source'
REFERENCE = ROOT / 'tools/reference'

WILD = {
    'walk': 'land',
    'surf': 'water',
    'old-rod': 'old',
    'good-rod': 'good',
    'super-rod': 'super',
    'headbutt-low': 'land',
    'headbutt-normal': 'land',
    'headbutt-high': 'land',
    'headbutt': 'land',
    'rock-smash': 'land',
    'seaweed': 'water',
    'feebas-tile-fishing': 'good',
}

WEIGHTS = {
    'land': [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1],
    'water': [60, 30, 5, 4, 1],
    'old': [70, 30],
    'good': [60, 20, 20],
    'super': [40, 40, 15, 4, 1],
}

FIELDS = {
    'land': ('land_mons', range(12)),
    'water': ('water_mons', range(5)),
    'old': ('fishing_mons', range(2)),
    'good': ('fishing_mons', range(2, 5)),
    'super': ('fishing_mons', range(5, 10)),
}

# Ecological overrides for species whose source-game location is a poor
# description of where they should live in FireRed.
SPECIES_HABITAT = {
    # Freshwater / wetlands
    'MARILL': 'wetland',
    'WOOPER': 'wetland',
    'QUAGSIRE': 'wetland',
    'CARVANHA': 'wetland',
    'BARBOACH': 'wetland',
    'WHISCASH': 'wetland',
    'CORPHISH': 'wetland',

    # Coastal / ocean
    'CHINCHOU': 'coast',
    'LANTURN': 'coast',
    'QWILFISH': 'coast',
    'CORSOLA': 'coast',
    'MANTINE': 'coast',
    'SHARPEDO': 'coast',
    'WAILMER': 'coast',
    'WAILORD': 'coast',

    # Forest
    'LEDYBA': 'forest',
    'SPINARAK': 'forest',
    'PINECO': 'forest',
    'HERACROSS': 'forest',
    'SHROOMISH': 'forest',
    'SLAKOTH': 'forest',
    'NINCADA': 'forest',

    # Mountain / rocky
    'GLIGAR': 'mountain',
    'SKARMORY': 'mountain',
    'PHANPY': 'mountain',
    'DONPHAN': 'mountain',
    'NOSEPASS': 'mountain',

    # Volcanic
    'SLUGMA': 'volcanic',
    'NUMEL': 'volcanic',
    'TORKOAL': 'volcanic',

    # Ice
    'SNEASEL': 'ice',
    'SWINUB': 'ice',
    'DELIBIRD': 'ice',

    # Haunted
    'MISDREAVUS': 'ghost',
    'SHUPPET': 'ghost',
    'DUSKULL': 'ghost',

    # Caves
    'DUNSPARCE': 'cave',
    'WHISMUR': 'cave',
    'MAKUHITA': 'cave',
    'SABLEYE': 'cave',
    'ARON': 'cave',
    'LAIRON': 'cave',

    # City outskirts / developed routes
    'MURKROW': 'urban',
    'HOUNDOUR': 'urban',
}

# These lines should still feel special even though their source game's
# story order is no longer treated as a hard rule.
PHASE_FLOOR = {
    'LARVITAR': 4,
    'PUPITAR': 4,
    'BAGON': 4,
}

RELATED_HABITATS = {
    'field': {'forest', 'urban', 'wetland', 'mountain'},
    'forest': {'field', 'wetland'},
    'urban': {'field', 'ghost'},
    'wetland': {'field', 'forest', 'coast'},
    'coast': {'wetland', 'field'},
    'mountain': {'field', 'cave', 'volcanic', 'ice'},
    'cave': {'mountain', 'ghost', 'volcanic', 'ice'},
    'volcanic': {'mountain', 'cave'},
    'ghost': {'cave', 'urban'},
    'ice': {'cave', 'mountain'},
}


def habitat_distance(a, b):
    if a == b:
        return 0
    if b in RELATED_HABITATS.get(a, ()) or a in RELATED_HABITATS.get(b, ()):
        return 1
    return 4


def placement_phase(sp):
    """Return the earliest reasonable FireRed phase based mostly on balance.

    Original Crystal/Emerald availability remains a preference, not an
    absolute restriction for ordinary low-level Pokemon.
    """
    source = source_phase(sp['source_stage'])
    level = sp['source_min']

    if level <= 10:
        level_phase = 0
    elif level <= 20:
        level_phase = 1
    elif level <= 30:
        level_phase = 2
    elif level <= 40:
        level_phase = 3
    elif level <= 50:
        level_phase = 4
    else:
        level_phase = 5

    # Evolved wild forms get pushed one phase later than a basic Pokemon
    # encountered at the same level.
    if sp['evolved']:
        level_phase = min(5, level_phase + 1)

    phase = min(source, level_phase)
    return max(phase, PHASE_FLOOR.get(sp['species'], 0))


def read(name):
    with (SOURCE / (name + '.csv')).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def key(name):
    return name.upper().replace('-', '_')


def map_ids():
    source = (REFERENCE / 'src_import_gba_map_groups_firered.lua').read_text()
    versions = (REFERENCE / 'versions.lua').read_text()
    aliases = {}
    for table in ('FRLG_MAP_TO_FR', 'FRLG_MAP_TO_SEVII'):
        body = re.search(r'Versions\.' + table + r' = \{(.*?)\n\}', versions, re.S)[1]
        aliases.update(re.findall(r'\["([\d:]+)"\] = "([^"]+)"', body))

    result = {}
    for group, body in re.findall(
        r'\[(\d+)\] = \{\s*name = "[^"]+",\s*maps = \{(.*?)\n\s*\}',
        source,
        re.S,
    ):
        for num, pret in enumerate(re.findall(r'"([^"]+)"', body)):
            slug = re.sub(r'([a-z])([A-Z])', r'\1_\2', pret).upper()
            normal = re.sub(r'ROUTE(\d+)', r'ROUTE_\1', slug)
            result[slug] = aliases.get(f'{group}:{num}', 'FR_' + normal)
    return result


def candidates():
    species = {int(r['id']): r for r in read('pokemon_species')}
    slots = {r['id']: r for r in read('encounter_slots')}
    methods = {r['id']: r['identifier'] for r in read('encounter_methods')}
    areas = {r['id']: r for r in read('location_areas')}
    locations = {r['id']: r['identifier'] for r in read('locations')}
    condition_names = {
        r['id']: r['identifier'] for r in read('encounter_condition_values')
    }

    conditions = collections.defaultdict(list)
    for row in read('encounter_condition_value_map'):
        conditions[row['encounter_id']].append(
            condition_names[row['encounter_condition_value_id']]
        )

    by_species = collections.defaultdict(list)
    for e in read('encounters'):
        dex = int(e['pokemon_id'])
        if not (
            (e['version_id'] == '6' and 152 <= dex <= 251)
            or (e['version_id'] == '9' and 252 <= dex <= 386)
        ):
            continue

        sp = species[dex]
        source_slot = slots[e['encounter_slot_id']]
        method = methods[source_slot['encounter_method_id']]

        if method not in WILD or sp['is_legendary'] == '1' or sp['is_mythical'] == '1':
            continue

        # A swarm is an exceptional event, not normal first availability.
        if 'swarm-yes' in conditions[e['id']]:
            continue

        area = areas[e['location_area_id']]
        location = locations[area['location_id']]
        version = 'crystal' if e['version_id'] == '6' else 'emerald'

        # Emerald's Cave of Origin encounter floors are not normally accessible.
        if version == 'emerald' and location == 'cave-of-origin':
            continue

        stage = source_stage(
            version,
            location,
            area['identifier'],
            method,
            sp['identifier'],
        )

        species_name = key(sp['identifier'])
        by_species[dex].append(
            dict(
                dex=dex,
                species=species_name,
                version=version,
                source_location=location,
                source_area=area['identifier'],
                source_method=method,
                source_stage=stage,
                source_min=int(e['min_level']),
                source_max=int(e['max_level']),
                source_weight=int(source_slot['rarity']),
                source_conditions=','.join(conditions[e['id']]),
                source_encounter_id=int(e['id']),
                terrain=WILD[method],
                habitat=SPECIES_HABITAT.get(
                    species_name,
                    'field'
                    if location == 'ruins-of-alph' and area['identifier'] == 'outside'
                    else habitat(location),
                ),
                evolved=bool(sp['evolves_from_species_id']),
            )
        )

    # First story access wins; then lowest encounter level; finally stable data ID.
    selected = [
        min(
            rows,
            key=lambda r: (
                r['source_stage'],
                r['habitat'] == 'ice' and r['terrain'] != 'land',
                r['source_min'],
                r['source_encounter_id'],
            ),
        )
        for rows in by_species.values()
    ]

    excluded = []
    for dex in range(152, 387):
        if dex in by_species:
            continue

        sp = species[dex]
        if sp['is_legendary'] == '1' or sp['is_mythical'] == '1':
            reason = 'legendary/mythical; unchanged'
        else:
            source_version = 'Crystal' if dex <= 251 else 'Emerald'
            reason = (
                f'no ordinary wild encounter in {source_version}; '
                'evolution/gift/trade/version-exclusive not added'
            )
        excluded.append(dict(dex=dex, species=key(sp['identifier']), reason=reason))

    return selected, excluded


def destinations():
    """Return shared FRLG slots with edition-specific vanilla expectations."""
    ids = map_ids()
    tables = json.loads((SOURCE / 'firered_wild_encounters.json').read_text())[
        'wild_encounter_groups'
    ][0]['encounters']

    by_game = {'firered': {}, 'leafgreen': {}}
    for row in tables:
        name = row['map'][4:]

        # Event variants and Unown-form tables remain vanilla.
        if 'ALTERING_CAVE' in name or 'TANOBY_RUINS_' in name:
            continue

        label = row['base_label']
        if label.endswith('_FireRed'):
            game = 'firered'
        elif label.endswith('_LeafGreen'):
            game = 'leafgreen'
        else:
            continue

        if row['map'] in by_game[game]:
            raise ValueError(f'Duplicate {game} encounter table for {row["map"]}')
        by_game[game][row['map']] = row

    missing_leafgreen = sorted(set(by_game['firered']) - set(by_game['leafgreen']))
    missing_firered = sorted(set(by_game['leafgreen']) - set(by_game['firered']))
    if missing_leafgreen or missing_firered:
        raise ValueError(
            'FireRed/LeafGreen encounter map mismatch: '
            f'missing LeafGreen={missing_leafgreen}, missing FireRed={missing_firered}'
        )

    dest = []
    for map_key in sorted(by_game['firered']):
        firered = by_game['firered'][map_key]
        leafgreen = by_game['leafgreen'][map_key]
        name = map_key[4:]

        rank = target_stage(name)
        assert name in ids, name

        for terrain, (field, indices) in FIELDS.items():
            has_fr = field in firered
            has_lg = field in leafgreen
            if has_fr != has_lg:
                raise ValueError(
                    f'FireRed/LeafGreen field mismatch for {name} {field}'
                )
            if not has_fr:
                continue

            fr_area = firered[field]
            lg_area = leafgreen[field]

            fr_mons = fr_area['mons']
            lg_mons = lg_area['mons']
            if len(fr_mons) != len(lg_mons):
                raise ValueError(
                    f'FireRed/LeafGreen slot-count mismatch for {name} {field}'
                )

            weights = WEIGHTS[terrain]
            for local, idx in enumerate(indices):
                fr_slot = fr_mons[idx]
                lg_slot = lg_mons[idx]

                dest.append(
                    dict(
                        map=ids[name],
                        map_name=name,
                        terrain=terrain,
                        field=(
                            'fishing'
                            if field == 'fishing_mons'
                            else ('land' if terrain == 'land' else 'water')
                        ),
                        slot=idx + 1,
                        weight=weights[local],
                        target_stage=max(
                            rank,
                            {'water': 5, 'old': 2, 'good': 4, 'super': 4}.get(
                                terrain, 0
                            ),
                        ),
                        # Keep the legacy min/max fields as FireRed values for
                        # backward-compatible reports, and record LeafGreen
                        # separately. Placement scoring below considers both.
                        min_level=fr_slot['min_level'],
                        max_level=fr_slot['max_level'],
                        firered_min_level=fr_slot['min_level'],
                        firered_max_level=fr_slot['max_level'],
                        leafgreen_min_level=lg_slot['min_level'],
                        leafgreen_max_level=lg_slot['max_level'],
                        original_firered=fr_slot['species'][8:],
                        original_leafgreen=lg_slot['species'][8:],
                        habitat=habitat(name.replace('_', '-')),
                    )
                )

    return dest


def build():
    selected, excluded = candidates()
    dest = destinations()
    used = set()
    map_load = collections.Counter()
    placements = []

    # Scarce aquatic methods first, then Pokemon with the latest placement floor.
    # This gives the most constrained species first choice in the greedy allocator.
    selected.sort(
        key=lambda s: (
            s['terrain'] == 'land',
            -placement_phase(s),
            s['dex'],
        )
    )

    for sp in selected:
        options = []

        for d in dest:
            identity = (d['map'], d['field'], d['slot'])
            if identity in used:
                continue

            desired_phase = placement_phase(sp)
            dest_phase = target_phase(d['target_stage'])

            if dest_phase < desired_phase:
                continue

            # Keep encounter methods intact. Rod encounters remain on the same rod,
            # Surf remains Surf, and land-style methods remain land encounters.
            if d['terrain'] != sp['terrain']:
                continue

            # Source wild level is a placement preference, not a hard requirement.
            # Evolved Pokemon are already pushed later by placement_phase(), so allow
            # FRLG's native level ranges to determine their actual encounter levels.
            source_mid = (sp['source_min'] + sp['source_max']) / 2
            firered_mid = (
                d['firered_min_level'] + d['firered_max_level']
            ) / 2
            leafgreen_mid = (
                d['leafgreen_min_level'] + d['leafgreen_max_level']
            ) / 2
            dest_mid = (firered_mid + leafgreen_mid) / 2

            # Use the shared midpoint for general scoring, while also penalizing
            # a placement that fits one edition substantially worse than the other.
            level_penalty = (
                abs(dest_mid - source_mid)
                + abs(firered_mid - source_mid) * 0.25
                + abs(leafgreen_mid - source_mid) * 0.25
            )

            # Prefer not to move evolved Pokemon dramatically below their source-game
            # encounter level, but don't make that a hard capacity constraint.
            if sp['evolved'] and dest_mid < source_mid:
                level_penalty *= 1.5

            # Ecology dominates, then progression, source rarity, level similarity,
            # and finally spreading additions across maps.
            score = (
                habitat_distance(sp['habitat'], d['habitat']) * 100
                + (dest_phase - desired_phase) * 25
                + abs(d['weight'] - sp['source_weight']) * 2
                + level_penalty
                + map_load[d['map']] * 3
            )
            options.append((score, d['map'], d['slot'], d))

        if not options:
            raise ValueError('No capacity for ' + sp['species'])

        d = min(options, key=lambda x: x[:3])[3]
        used.add((d['map'], d['field'], d['slot']))
        map_load[d['map']] += 1
        placements.append(
            {
                **sp,
                **{k: v for k, v in d.items() if k != 'habitat'},
            }
        )

    placements.sort(
        key=lambda p: (p['target_stage'], p['map'], p['field'], p['slot'])
    )

    generated = ROOT / 'data'
    generated.mkdir(exist_ok=True)

    lines = [
        '-- Generated by tools/build.py. Species names, never National Dex numeric IDs.',
        '-- One placement plan; expected vanilla species are edition-specific.',
        'return {',
    ]
    for p in placements:
        lines.append(
            '  { map = "%s", terrain = "%s", slot = %d, species = "%s", '
            'expected = { firered = "%s", leafgreen = "%s" } },'
            % (
                p['map'],
                p['field'],
                p['slot'],
                p['species'],
                p['original_firered'],
                p['original_leafgreen'],
            )
        )
    lines.append('}')
    (generated / 'placements.lua').write_text(
        '\n'.join(lines) + '\n', encoding='utf-8'
    )

    report = {'placements': placements, 'excluded': excluded}
    (ROOT / 'PLACEMENTS.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8'
    )

    headers = [
        'dex',
        'species',
        'version',
        'source_location',
        'source_area',
        'source_method',
        'source_stage',
        'source_min',
        'source_max',
        'source_weight',
        'source_conditions',
        'map',
        'terrain',
        'slot',
        'weight',
        'target_stage',
        'min_level',
        'max_level',
        'firered_min_level',
        'firered_max_level',
        'leafgreen_min_level',
        'leafgreen_max_level',
        'original_firered',
        'original_leafgreen',
    ]
    with (ROOT / 'PLACEMENTS.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(sorted(placements, key=lambda p: p['dex']))

    with (ROOT / 'EXCLUDED.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, ['dex', 'species', 'reason'])
        writer.writeheader()
        writer.writerows(excluded)

    hashes = {
        str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(
            p.read_bytes()
        ).hexdigest()
        for folder in (SOURCE, REFERENCE)
        for p in sorted(folder.glob('*'), key=lambda p: p.name)
        if p.is_file()
    }
    (ROOT / 'tools/input_hashes.json').write_text(
        json.dumps(hashes, indent=2) + '\n'
    )

    print(
        f'{len(placements)} species; '
        f'{len(set(p["map"] for p in placements))} shared FRLG maps; '
        f'{len(excluded)} documented exclusions'
    )

    earlier = [
        p
        for p in placements
        if target_phase(p['target_stage']) < source_phase(p['source_stage'])
    ]
    later = [
        p
        for p in placements
        if target_phase(p['target_stage']) > source_phase(p['source_stage'])
    ]
    print(
        'Earlier than source milestone by design:',
        [(p['species'], p['source_stage'], p['target_stage']) for p in earlier],
    )
    print(
        'Later than source milestone:',
        [(p['species'], p['source_stage'], p['target_stage']) for p in later],
    )


if __name__ == '__main__':
    build()
