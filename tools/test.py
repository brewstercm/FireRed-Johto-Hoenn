'''Offline FRLG runtime regression tests.

Guards:
- FireRed and LeafGreen encounter patches
- versionless live Game3 mod surface
- Pokédex area refresh from merged encounter data
'''

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

assert {p['dex'] for p in placements} == {p['dex'] for p in selected}
assert len(placements) == len({p['dex'] for p in placements}) == 118
assert {p['dex'] for p in placements} | {p['dex'] for p in excluded} == set(
    range(152, 387)
)

assert source_stage('crystal', 'ruins-of-alph', 'outside', 'walk', 'natu') == 4
assert source_stage('emerald', 'meteor-falls', 'backsmall-room', 'walk', 'bagon') == 8
assert source_stage('crystal', 'johto-route-46', '', 'walk', 'phanpy') == 0
assert source_stage('crystal', 'kanto-route-7', '', 'walk', 'houndour') == 9

used_slots = set()
for p in placements:
    assert target_phase(p['target_stage']) >= build.placement_phase(p)
    assert 1 <= p['min_level'] <= p['max_level'] <= 100
    assert p['source_weight'] > 0
    assert p['weight'] in build.WEIGHTS[p['terrain']]
    assert p['terrain'] == build.WILD[p['source_method']]
    assert p['original_firered']
    assert p['original_leafgreen']
    assert 1 <= p['firered_min_level'] <= p['firered_max_level'] <= 100
    assert 1 <= p['leafgreen_min_level'] <= p['leafgreen_max_level'] <= 100

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

ids = build.map_ids()
source_tables = json.loads(
    (ROOT / 'tools/source/firered_wild_encounters.json').read_text()
)['wild_encounter_groups'][0]['encounters']


def run(runtime_name, game):
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

    native = {}
    field_map = {
        'land_mons': 'land',
        'water_mons': 'water',
        'fishing_mons': 'fishing',
        'rock_smash_mons': 'rocks',
    }
    suffix = '_FireRed' if game == 'firered' else '_LeafGreen'

    for row in source_tables:
        name = row['map'][4:]
        if not row['base_label'].endswith(suffix) or name not in ids:
            continue

        map_id = ids[name]
        slot_key = lua.eval('Catalog.slotKeyFor')(map_id)
        group, num = map(int, slot_key.split('_'))
        rec = {'mapGroup': group, 'mapNum': num}

        for field, terrain in field_map.items():
            if field in row:
                rec[terrain] = {
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

        native[map_id] = rec
        native[f'{group}:{num}'] = rec

    lua.globals().native = table(native)
    lua.globals().names = table(
        {num: name for name, num in species.items() if num > 0}
    )
    lua.globals().snubbull_id = species['SNUBBULL']
    lua.globals().sentret_id = species['SENTRET']

    lua.execute(
        r'''
      pokemon = { _names = names }
      engine = { _tables = native }
      fixtureData = {gen3Pokemon=pokemon, gen3Encounters=engine}
      gameData = {gen3Encounters=engine._tables}
      Schemas.bindGen3(fixtureData)
      before = Merge.deepCopy(native)

      registry = { ops = {}, rows = {} }
      function registry:get(id)
        return self.rows[id] or Schemas.gen3View.encounterRecord(engine,id)
      end
      function registry:patch(id, patch)
        local ok, errors = Schemas.check(
          Schemas.REGISTRIES.encounters, "encounters", id, patch, "patch", 3
        )
        assert(ok, errors and table.concat(errors,"; "))
        self.rows[id] = Merge.deepMerge(self:get(id),patch)
        self.ops[id] = true
      end

      -- Minimal engine-internal Pokédex fixtures needed by main.lua.
      local routeKey = assert(Catalog.slotKeyFor("FR_ROUTE_1"))
      local routeGroup, routeMap = routeKey:match("^(%d+)_(%d+)$")
      routeGroup, routeMap = tonumber(routeGroup), tonumber(routeMap)

      local routeGroups = {}
      routeGroups[routeGroup] = { maps = {} }
      routeGroups[routeGroup].maps[routeMap + 1] = "FR_ROUTE_1"

      pokedexData = {
        -- Truthy means "already initialized", so game.ready performs a refresh.
        _entries = {},
        _areaData = {
          markers = {
            DEX_AREA_ROUTE_1 = { shape = 1, x = 1, y = 1 },
          },
          mapsecToArea = {
            MAPSEC_ROUTE_1 = "DEX_AREA_ROUTE_1",
          },
        },
        _speciesWildAreas = {},
        _buildSpeciesWildAreas = function() end,
      }

      package.loaded["src.core.game3.pokedex_data"] = pokedexData
      package.loaded["src.import.gba.map_groups_firered"] = {
        groups = routeGroups,
      }
      package.loaded["src.import.gba.map_sections_extract"] = {
        getInfo = function(_, pretName)
          if pretName == "FR_ROUTE_1" then
            return { id = "MAPSEC_ROUTE_1" }
          end
          return nil
        end,
      }

      events = { listeners = {} }
      function events:on(name, fn)
        self.listeners[name] = self.listeners[name] or {}
        table.insert(self.listeners[name], fn)
      end
      function events:emit(name, payload)
        for _, fn in ipairs(self.listeners[name] or {}) do
          fn(payload)
        end
      end

      warnings = {}
      mod = {
        -- Intentionally no .version, matching live Game3.
        game = { data = gameData },
        events = events,
        content = {
          encounters = registry,
          pokemon = {
            get = function(_, name)
              return Schemas.gen3View.speciesNum(pokemon, name)
            end,
          },
        },
        read = function(_, p) return read_file(p) end,
        log = {
          warn = function(_, m)
            warnings[#warnings + 1] = m
          end,
        },
      }

      function boot()
        return assert(load(read_file("main.lua")))(mod)
      end

      boot()
      assert(#warnings == 0, table.concat(warnings, "; "))

      -- Real load order: registry writes land before game.ready.
      Schemas.gen3View.encounterWrite(engine, registry)
      gameData.gen3Encounters = engine._tables
      events:emit("game.ready", { game = mod.game })

      local snubbullAreas = pokedexData._speciesWildAreas[snubbull_id]
      assert(snubbullAreas and #snubbullAreas > 0, "Snubbull has no Pokédex area")
      assert(
        snubbullAreas[1] == "DEX_AREA_ROUTE_1",
        "Snubbull Pokédex area is not Route 1"
      )

      local sentretAreas = pokedexData._speciesWildAreas[sentret_id]
      assert(sentretAreas and #sentretAreas > 0, "Sentret has no Pokédex area")
      assert(
        sentretAreas[1] == "DEX_AREA_ROUTE_1",
        "Sentret Pokédex area is not Route 1"
      )
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

    print(
        f'{runtime_name}/{game}: encounters + Pokédex Route 1 area refresh PASS'
    )


for runtime in ('lua54', 'luajit21'):
    for game in ('firered', 'leafgreen'):
        run(runtime, game)

print('FireRed/LeafGreen runtime + Pokédex regression suite: PASS')
