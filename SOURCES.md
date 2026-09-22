# Data and implementation sources

Retrieved 2026-09-21/22. The mod does not contain ROM bytes or image/audio assets.

- **[PokeAPI CSV database](https://github.com/PokeAPI/pokeapi/tree/master/data/v2/csv)**:
  Crystal version ID 6 and Emerald version ID 9 encounter rows, species,
  locations, slots, methods, and encounter conditions. Repository revision
  recorded at retrieval: `575291cdb197a7e3a320297be276c9de4ef8401a`.
  [API documentation](https://pokeapi.co/docs/v2#encounters-section).
- **[pret/pokefirered wild encounter definitions](https://github.com/pret/pokefirered/blob/master/src/data/wild_encounters.json)**:
  native slot counts, probabilities, levels, species, and maps. Only the
  `_FireRed` variant is used. Also `include/constants/species.h` for tests of
  native numeric IDs. Repository revision recorded at retrieval:
  `c75f352304d529f6ba92d4f74b9cf8b5c3810788`.
- **[Gen1Recomp v0.2.73](https://github.com/bryanthaboi/gen1recomp/releases/tag/v0.2.73)**:
  API 2 FireRed registry schema and encounter write behavior. The release's
  `src/mods/Schemas.lua` is byte-identical to the downloaded development copy.
  Development revision recorded at retrieval:
  `1f102048fa69f2645ac10e90d491e5fefd254dc8`.
  Relevant implementation: `src/mods/Schemas.lua`, `src/mods/Merge.lua`,
  `src/core/game3/encounters.lua`, and `src/import/gba/map_catalog.lua`.

Development reference files retain upstream comments and are not part of the
installable ZIP. Upstream files remain subject to their respective repository
licenses. Pokemon names and game data belong to their respective owners.

`tools/input_hashes.json` records the SHA-256 of each actual downloaded input;
these snapshots make rebuilds independent of future upstream changes.
Downloads were made from the branches listed above, with repository heads
recorded alongside them; hashes identify the exact retained bytes.

Progression ranks, phase equivalences, habitat preferences, and FireRed
placements are authored decisions in this mod, not claims supplied by PokeAPI.
