# Data and implementation sources

Retrieved 2026-09-21/22. The mod does not contain ROM bytes or image/audio assets.

- **PokeAPI CSV database**:
  Crystal version ID 6 and Emerald version ID 9 encounter rows, species,
  locations, slots, methods, and encounter conditions. Repository revision
  recorded at retrieval: `575291cdb197a7e3a320297be276c9de4ef8401a`.
- **pret/pokefirered wild encounter definitions**:
  native slot counts, probabilities, levels, species, and maps. Both the
  `_FireRed` and `_LeafGreen` variants in the checked-in encounter snapshot are
  used so runtime compatibility can be validated separately for each edition.
  `include/constants/species.h` is also retained for tests of native Gen 3
  species IDs. Repository revision recorded at retrieval:
  `c75f352304d529f6ba92d4f74b9cf8b5c3810788`.
- **Gen1Recomp v0.2.73 reference snapshots**:
  API 2 Gen 3 registry schema, merge behavior, encounter write behavior, map
  catalog, and FRLG map identifiers. Development reference files are retained
  under `tools/reference/` and are not included in the installable ZIP.

`tools/input_hashes.json` records SHA-256 hashes of retained source/reference
snapshots so builds remain auditable and independent of later upstream changes.

Progression ranks, phase equivalences, habitat preferences, and Johto/Hoenn
placements are authored decisions in this mod, not claims supplied by PokeAPI.

Upstream files remain subject to their respective licenses. Pokémon names and
game data belong to their respective owners.
