"""Offline regression tests using the released engine's actual schema/merge code.

Install lupa, or use pip --target tools/test_runtime lupa. No game/ROM required.
"""

import importlib
import json
import re
import sys
from pathlib import Path

import build
from progression import source_stage, target_phase


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/test_runtime'))

report = json.loads((ROOT / 'PLACEMENTS.json').read_text())
placements = report['placements']
selected, excluded = build.candidates()

# Coverage: every selected Johto/Hoenn species is placed exactly once, and every
# National Dex entry from 152-386 is either placed or explicitly excluded.
assert {p['dex'] for p in placements} == {p['dex'] for p in selected}
assert len(placements) == len({p['dex'] for p in placements}) == 118
assert {p['dex'] for p in placements} | {p['dex'] for p in excluded} == set(
    range(152, 387)
)

# Authored source-progression edge cases should remain stable.
assert source_stage('crystal', 'ruins-of-alph', 'outside', 'walk', 'natu') == 4
assert source_stage('emerald', 'meteor-falls', 'backsmall-room', 'walk', 'bagon') == 8
assert source_stage('crystal', 'johto-route-46', '', 'walk', 'phanpy') == 0
assert source_stage('crystal', 'kanto-route-7', '', 'walk', 'houndour') == 9

# Placement-policy checks.
used_slots = set()
for p in placements:
    # The new allocator may place ordinary species earlier than their original
    # Crystal/Emerald story milestone, but never earlier than placement_phase().
    assert target_phase(p['target_stage']) >= build.placement_phase(p)

    assert 1 <= p['min_level'] <= p['max_level'] <= 100

    # Source rarity is retained in the report and the destination slot must use
    # one of FireRed's real slot weights for that encounter method.
    assert p['source_weight'] > 0
    assert p['weight'] in build.WEIGHTS[p['terrain']]

    # Fishing methods no longer spill into Surf, and Surf/land remain intact.
    assert p['terrain'] == build.WILD[p['source_method']]

    # No two additions may claim the same FireRed encounter slot.
    identity = (p['map'], p['field'], p['slot'])
    assert identity not in used_slots, identity
    used_slots.add(identity)


species = {
    name: int(num)
    for name, num in re.findall(
        r'^#define SPECIES_(\w+) (\d+)\s*$',
        (ROOT / 'tools/source/firered_species.h').read_text(),
        re.M,
    )
}
assert species['RALTS'] == 392  # National Dex 280 is NOT the native species ID.

ids = build.map_ids()
source_tables = json.loads(
    (ROOT / 'tools/source/firered_wild_encounters.json').read_text()
)['wild_encounter_groups'][0]['encounters']


def run(runtime_name):
    lua = importlib.import_module('lupa.' + runtime_name).LuaRuntime(
        unpack_returned_tuples=True
    )

    def table(v):
        if isinstance(v, dict):
            return lua.table_from({k: table(x) for k, x in v.items()})
        if isinstance(v, list):
            return lua.table_from([table(x) for x in v])
        return v

    def read(name):
        return (ROOT / name).read_text(encoding='utf-8-sig')

    lua.globals().read_file = read
    lua.execute('package.loaded["src.core.Logger"] = { warn = function() end }')
    lua.execute(
        'package.loaded["src.mods.Merge"] = '
        'assert(load(read_file("tools/reference/Merge.lua")))()'
    )
    lua.execute(
        'Schemas = assert(load(read_file("tools/reference/release_Schemas.lua")))(); '
        'Merge = require("src.mods.Merge")'
    )
    lua.execute(
        'package.loaded["src.import.gba.versions"] = '
        'assert(load(read_file("tools/reference/versions.lua")))()'
    )
    lua.execute(
        'package.loaded["src.import.gba.map_groups_firered"] = '
        'assert(load(read_file("tools/reference/src_import_gba_map_groups_firered.lua")))()'
    )
    lua.execute(
        'Catalog = assert(load(read_file("tools/reference/map_catalog.lua")))()'
    )

    # Validate generated IDs against the actual engine's canonical map catalog.
    for p in placements:
        assert lua.eval('Catalog.isKnown')(p['map']), p['map']

    native = {}
    field_map = {
        'land_mons': 'land',
        'water_mons': 'water',
        'fishing_mons': 'fishing',
        'rock_smash_mons': 'rocks',
    }

    for row in source_tables:
        name = row['map'][4:]
        if not row['base_label'].endswith('_FireRed') or name not in ids:
            continue

        map_id = ids[name]
        slot_key = lua.eval('Catalog.slotKeyFor')(map_id)
        group, num = map(int, slot_key.split('_'))
        out = {'mapGroup': group, 'mapNum': num}

        for field, terrain in field_map.items():
            if field in row:
                out[terrain] = {
                    'rate': row[field]['encounter_rate'],
                    'slots': [
                        {
                            'species': species[s['species'][8:]],
                            'minLevel': s['min_level'],
                            'maxLevel': s['max_level'],
                        }
                        for s in row[field]['mons']
                    ],
                }

        native[map_id] = out
        native[f'{group}:{num}'] = out

    lua.globals().native = table(native)
    lua.globals().names = table(
        {num: name for name, num in species.items() if num > 0}
    )

    lua.execute(
        '''
      pokemon = { _names = names }
      engine = { _tables = native }
      fixtureData = {gen3Pokemon=pokemon, gen3Encounters=engine}
      Schemas.bindGen3(fixtureData)
      before = Merge.deepCopy(native)
      registry = { ops = {}, rows = {} }
      function registry:get(id)
        return self.rows[id] or Schemas.gen3View.encounterRecord(engine,id)
      end
      function registry:patch(id, patch)
        local ok, errors = Schemas.check(Schemas.REGISTRIES.encounters, "encounters",id,patch,"patch",3)
        assert(ok, errors and table.concat(errors,"; "))
        self.rows[id] = Merge.deepMerge(self:get(id),patch)
        self.ops[id] = true
      end
      warnings = {}
      mod = {content={encounters=registry, pokemon={get=function(_,name)
          return Schemas.gen3View.speciesNum(pokemon,name)
        end}}, read=function(_,p) return read_file(p) end,
        log={warn=function(_,m) warnings[#warnings+1]=m end}}
      function boot() return assert(load(read_file("main.lua")))(mod) end
      boot()
      assert(#warnings==0, table.concat(warnings, "; "))
      Schemas.gen3View.encounterWrite(engine,registry)
    '''
    )

    g = lua.globals()
    assert len(list(g.registry.ops.keys())) == len({p['map'] for p in placements})

    expected = {
        (p['map'], p['field'], p['slot']): species[p['species']]
        for p in placements
    }

    for map_id in {p['map'] for p in placements}:
        before = g.before[map_id]
        after = g.native[map_id]

        for terrain in ('land', 'water', 'fishing', 'rocks'):
            if before[terrain] is None:
                assert after[terrain] is None
                continue

            # The mod changes species only. Encounter rates, slot counts and
            # FireRed's original level ranges remain unchanged.
            assert before[terrain]['rate'] == after[terrain]['rate']
            a = before[terrain]['slots']
            b = after[terrain]['slots']
            assert len(a) == len(b)

            for i in range(1, len(a) + 1):
                assert a[i]['minLevel'] == b[i]['minLevel']
                assert a[i]['maxLevel'] == b[i]['maxLevel']
                assert b[i]['species'] == expected.get(
                    (map_id, terrain, i), a[i]['species']
                )

        alias = f'{after["mapGroup"]}:{after["mapNum"]}'
        assert lua.eval('function(a,b) return a==b end')(after, g.native[alias])

    lua.execute(
        '''
      -- Conflicting input must skip a whole map, rather than partially edit it.
      engine._tables = Merge.deepCopy(before)
      registry.rows, registry.ops, warnings = {}, {}, {}
      local p = assert(load(read_file("data/placements.lua")))()[1]
      engine._tables[p.map][p.terrain].slots[p.slot].species = 150
      boot()
      assert(registry.ops[p.map] == nil and #warnings == 1)

      -- Missing map: warn and keep all other compatible maps working.
      engine._tables = Merge.deepCopy(before)
      engine._tables[p.map] = nil
      registry.rows, registry.ops, warnings = {}, {}, {}
      boot()
      assert(registry.ops[p.map] == nil and #warnings == 1)

      -- Species preflight aborts before any registry mutation.
      registry.rows, registry.ops = {}, {}
      mod.content.pokemon.get = function() return nil end
      assert(not pcall(boot))
      assert(next(registry.ops)==nil)
    '''
    )

    print(
        runtime_name
        + ': 118 species IDs, real schema/merge/write, canonical maps, aliases, '
        'levels/rates, method preservation, conflict/missing-data checks PASS'
    )


for runtime in ('lua54', 'luajit21'):
    run(runtime)

print(
    'Ecology-aware progression, coverage, rarity metadata, unique slots, '
    'method preservation, evolved-form progression: PASS'
)
