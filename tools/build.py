"""Build native FireRed table additions and a complete, auditable placement report.

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
WILD = {'walk':'land', 'surf':'water', 'old-rod':'old', 'good-rod':'good',
        'super-rod':'super', 'headbutt-low':'land', 'headbutt-normal':'land',
        'headbutt-high':'land', 'headbutt':'land', 'rock-smash':'land',
        'seaweed':'water', 'feebas-tile-fishing':'good'}
WEIGHTS = {'land':[20,20,10,10,10,10,5,5,4,4,1,1], 'water':[60,30,5,4,1],
           'old':[70,30], 'good':[60,20,20], 'super':[40,40,15,4,1]}
FIELDS = {'land':('land_mons',range(12)), 'water':('water_mons',range(5)),
          'old':('fishing_mons',range(2)), 'good':('fishing_mons',range(2,5)),
          'super':('fishing_mons',range(5,10))}

def read(name):
    with (SOURCE / (name+'.csv')).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def key(name): return name.upper().replace('-', '_')

def map_ids():
    source = (REFERENCE/'src_import_gba_map_groups_firered.lua').read_text()
    versions = (REFERENCE/'versions.lua').read_text()
    aliases = {}
    for table in ('FRLG_MAP_TO_FR', 'FRLG_MAP_TO_SEVII'):
        body = re.search(r'Versions\.'+table+r' = \{(.*?)\n\}', versions, re.S)[1]
        aliases.update(re.findall(r'\["([\d:]+)"\] = "([^"]+)"', body))
    result = {}
    for group, body in re.findall(r'\[(\d+)\] = \{\s*name = "[^"]+",\s*maps = \{(.*?)\n\s*\}', source, re.S):
        for num, pret in enumerate(re.findall(r'"([^"]+)"', body)):
            slug = re.sub(r'([a-z])([A-Z])', r'\1_\2', pret).upper()
            normal = re.sub(r'ROUTE(\d+)',r'ROUTE_\1',slug)
            result[slug] = aliases.get(f'{group}:{num}', 'FR_'+normal)
    return result

def candidates():
    species = {int(r['id']): r for r in read('pokemon_species')}
    slots = {r['id']: r for r in read('encounter_slots')}
    methods = {r['id']: r['identifier'] for r in read('encounter_methods')}
    areas = {r['id']: r for r in read('location_areas')}
    locations = {r['id']: r['identifier'] for r in read('locations')}
    condition_names = {r['id']: r['identifier'] for r in read('encounter_condition_values')}
    conditions = collections.defaultdict(list)
    for row in read('encounter_condition_value_map'):
        conditions[row['encounter_id']].append(condition_names[row['encounter_condition_value_id']])
    by_species = collections.defaultdict(list)
    for e in read('encounters'):
        dex = int(e['pokemon_id'])
        if not ((e['version_id']=='6' and 152<=dex<=251) or (e['version_id']=='9' and 252<=dex<=386)): continue
        sp = species[dex]
        method = methods[slots[e['encounter_slot_id']]['encounter_method_id']]
        if method not in WILD or sp['is_legendary']=='1' or sp['is_mythical']=='1': continue
        # A swarm is an exceptional event, not normal first availability.
        if 'swarm-yes' in conditions[e['id']]: continue
        area = areas[e['location_area_id']]
        location = locations[area['location_id']]
        version = 'crystal' if e['version_id']=='6' else 'emerald'
        # Emerald's Cave of Origin encounter floors are not normally accessible.
        if version == 'emerald' and location == 'cave-of-origin': continue
        stage = source_stage(version, location, area['identifier'], method, sp['identifier'])
        by_species[dex].append(dict(dex=dex, species=key(sp['identifier']), version=version,
            source_location=location, source_area=area['identifier'], source_method=method,
            source_stage=stage, source_min=int(e['min_level']), source_max=int(e['max_level']),
            source_conditions=','.join(conditions[e['id']]), source_encounter_id=int(e['id']),
            terrain=WILD[method], habitat=('field' if location=='ruins-of-alph' and area['identifier']=='outside' else habitat(location)),
            evolved=bool(sp['evolves_from_species_id'])))
    # First story access wins; then lowest encounter level; finally stable data ID.
    selected = [min(rows, key=lambda r:(r['source_stage'],r['habitat']=='ice' and r['terrain']!='land',r['source_min'],r['source_encounter_id']))
                for rows in by_species.values()]
    excluded = []
    for dex in range(152,387):
        if dex in by_species: continue
        sp = species[dex]
        reason = 'legendary/mythical; unchanged' if sp['is_legendary']=='1' or sp['is_mythical']=='1' else 'no ordinary wild encounter in '+('Crystal' if dex<=251 else 'Emerald')+'; evolution/gift/trade/version-exclusive not added'
        excluded.append(dict(dex=dex,species=key(sp['identifier']),reason=reason))
    return selected, excluded

def destinations():
    ids = map_ids()
    tables = json.loads((SOURCE/'firered_wild_encounters.json').read_text())['wild_encounter_groups'][0]['encounters']
    dest = []
    for row in tables:
        if not row['base_label'].endswith('_FireRed'): continue
        name = row['map'][4:]
        # Event variants and Unown-form tables remain vanilla.
        if 'ALTERING_CAVE' in name or 'TANOBY_RUINS_' in name: continue
        rank = target_stage(name)
        assert name in ids, name
        for terrain,(field,indices) in FIELDS.items():
            if field not in row: continue
            mons = row[field]['mons']
            weights = WEIGHTS[terrain]
            indices = list(indices)
            # Keep the highest-weight original slot for EACH native species,
            # independently for land, Surf, and each rod.
            protected = {}
            for local, idx in enumerate(indices):
                sp = mons[idx]['species']
                if sp not in protected or weights[local]>weights[protected[sp]]: protected[sp]=local
            for local, idx in enumerate(indices):
                if local in protected.values(): continue
                slot = mons[idx]
                dest.append(dict(map=ids[name], map_name=name, terrain=terrain,
                    field='fishing' if 'rod' in field or field=='fishing_mons' else ('land' if terrain=='land' else 'water'),
                    slot=idx+1, weight=weights[local], target_stage=max(rank, {'water':5,'old':2,'good':4,'super':4}.get(terrain,0)),
                    min_level=slot['min_level'], max_level=slot['max_level'], original=slot['species'][8:],
                    habitat=habitat(name.replace('_','-')), native_slots=mons))
    return dest

def build():
    selected, excluded = candidates()
    dest = destinations()
    used = set()
    mass = collections.Counter()
    placements = []
    # Scarce aquatic habitats first, then late species (cannot spill backwards).
    selected.sort(key=lambda s:(s['terrain']=='land',-s['source_stage'],s['dex']))
    for sp in selected:
        options=[]
        for d in dest:
            identity=(d['map'],d['field'],d['slot'])
            bucket=(d['map'],d['terrain'])
            if identity in used or target_phase(d['target_stage'])<source_phase(sp['source_stage']): continue
            # Fish may use Surf if preserving every native rod species leaves
            # no suitable rod slot. This adaptation is visible in the report.
            compatible = d['terrain']==sp['terrain'] or (sp['terrain'] in ('old','good','super') and d['terrain']=='water')
            if not compatible: continue
            if sp['evolved'] and d['min_level']<sp['source_min']: continue
            if mass[bucket]+d['weight']>40: continue
            # Keep destination levels; use source levels as a placement tiebreaker.
            score=(target_phase(d['target_stage'])-source_phase(sp['source_stage']))*100 + (d['habitat']!=sp['habitat'])*25 + (d['terrain']!=sp['terrain'])*15 + abs(d['min_level']-sp['source_min']) + mass[bucket]/5 + abs(d['weight']-5)
            options.append((score,d['map'],d['slot'],d))
        if not options: raise ValueError('No capacity for '+sp['species'])
        d=min(options,key=lambda x:x[:3])[3]
        used.add((d['map'],d['field'],d['slot']))
        mass[d['map'],d['terrain']]+=d['weight']
        placements.append({**sp,**{k:v for k,v in d.items() if k not in ('native_slots','habitat') }})
    placements.sort(key=lambda p:(p['target_stage'],p['map'],p['field'],p['slot']))
    generated=ROOT/'data'; generated.mkdir(exist_ok=True)
    lines=['-- Generated by tools/build.py. Species names, never National Dex numeric IDs.','return {']
    for p in placements:
        lines.append('  { map = "%s", terrain = "%s", slot = %d, species = "%s", expected = "%s" },' % (p['map'],p['field'],p['slot'],p['species'],p['original']))
    lines.append('}')
    (generated/'placements.lua').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    report={'placements':placements,'excluded':excluded}
    (ROOT/'PLACEMENTS.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    headers=['dex','species','version','source_location','source_area','source_method','source_stage','source_min','source_max','source_conditions','map','terrain','slot','weight','target_stage','min_level','max_level']
    with (ROOT/'PLACEMENTS.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,headers,extrasaction='ignore');w.writeheader();w.writerows(sorted(placements,key=lambda p:p['dex']))
    with (ROOT/'EXCLUDED.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,['dex','species','reason']);w.writeheader();w.writerows(excluded)
    hashes={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in (SOURCE,REFERENCE) for p in sorted(folder.glob('*'), key=lambda p:p.name) if p.is_file()}
    (ROOT/'tools/input_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    print(f'{len(placements)} species; {len(set(p["map"] for p in placements))} maps; {len(excluded)} documented exclusions')
    delayed=[p for p in placements if target_phase(p['target_stage'])>source_phase(p['source_stage'])]
    print('Later than source milestone:',[(p['species'],p['source_stage'],p['target_stage']) for p in delayed])

if __name__=='__main__': build()
