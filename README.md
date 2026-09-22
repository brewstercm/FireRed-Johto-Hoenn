# FireRed & LeafGreen Johto & Hoenn Encounters

A standalone encounter mod for **native FireRed and LeafGreen in Gen1Recomp**.

The mod adds **118 wild species: 48 Johto and 70 Hoenn** using the Gen 3 games'
existing species, moves, cries, graphics, encounter tables, and level ranges.
No species-pack dependency, ROM, sprite pack, or other game asset is included.

The same mod ZIP supports both FireRed and LeafGreen.

## Install

Download the ZIP from the repository's **Latest release** and import it with
Gen1Recomp's mod manager.

The manifest targets both games:

```json
"games": ["firered", "leafgreen"]
```

FireRed and LeafGreen keep their own imported game data, caches, saves, and
vanilla encounters. The mod detects the active edition at runtime.

## How dual-game support works

The checked-in pret encounter snapshot contains both FireRed and LeafGreen
encounter tables.

The builder creates one Johto/Hoenn placement plan. For each destination slot,
the generated runtime data records both vanilla expectations:

```text
expected.firered
expected.leafgreen
```

This keeps the new Johto/Hoenn species in the same ecological location in both
games while respecting FireRed/LeafGreen version-exclusive vanilla encounters.

Before editing a map, `main.lua` checks the expected vanilla species for the
active edition. If another encounter mod or engine-data change has already
altered a targeted slot, the whole map is skipped with a warning rather than
being partially patched.

## Placement philosophy

Selected encounter slots are rebuilt around:

1. habitat/ecological fit
2. reasonable FRLG progression
3. source-game rarity
4. source encounter level
5. distribution across maps

The allocator does **not** reserve a fixed percentage of each table for native
Kanto Pokémon.

Native species remain where they fit the resulting encounter table, but they
are not protected simply because they were present in the original game.

### Habitat-aware placement

The allocator distinguishes broad environments including:

- field
- forest
- wetland
- coast
- mountain
- cave
- volcanic
- ghost/haunted
- ice
- urban fringe

Some species have explicit ecological overrides when their first Crystal or
Emerald encounter is a poor description of where they fit naturally in Kanto
or the Sevii Islands.

## Progression policy

Crystal and Emerald availability remains useful source metadata but is not an
absolute FRLG progression rule.

`placement_phase()` combines source-game availability with source encounter
level. Ordinary low-level Pokémon that happen to appear late in Crystal or
Emerald can therefore appear earlier in FRLG when their strength and habitat
justify it.

Evolved forms are pushed later than comparable basic forms. Source wild level
is a placement preference rather than a hard minimum, and large downward level
shifts for evolved Pokémon receive an additional scoring penalty.

Larvitar, Pupitar, and Bagon also have explicit late-game progression floors.

## Encounter methods

Normalized source methods map to FRLG encounter mechanics as follows:

- walking, Headbutt, and Rock Smash -> land
- Surf and seaweed -> Surf
- Old Rod -> Old Rod
- Good Rod -> Good Rod
- Super Rod -> Super Rod
- Feebas special-tile fishing -> Good Rod

Fishing species are not moved into Surf merely to preserve native rod species.

## Encounter rarity

The selected Crystal/Emerald encounter slot's rarity is stored as
`source_weight`.

The allocator prefers a destination slot with a similar probability, although
habitat, progression, encounter method, and level fit can take priority.

FRLG's standard slot probabilities remain unchanged:

- land: 20%, 20%, 10%, 10%, 10%, 10%, 5%, 5%, 4%, 4%, 1%, 1%
- Surf: 60%, 30%, 5%, 4%, 1%
- Old Rod: 70%, 30%
- Good Rod: 60%, 20%, 20%
- Super Rod: 40%, 40%, 15%, 4%, 1%

## What remains unchanged

For both FireRed and LeafGreen the mod preserves:

- encounter rates
- encounter slot counts
- each live destination slot's minimum and maximum level
- species definitions
- moves
- cries
- graphics
- evolution rules
- trainer parties
- gifts
- scripts
- legendary encounters
- National Dex behavior

The mod changes only selected wild species assignments.

## Generated reports

Running `tools/build.py` regenerates:

```text
data/placements.lua
PLACEMENTS.json
PLACEMENTS.csv
EXCLUDED.csv
tools/input_hashes.json
```

`PLACEMENTS.json` contains full placement metadata.

`PLACEMENTS.csv` includes edition-specific vanilla species and level metadata:

```text
original_firered
original_leafgreen
firered_min_level
firered_max_level
leafgreen_min_level
leafgreen_max_level
```

so version-exclusive vanilla species and level differences are directly auditable.

`EXCLUDED.csv` documents Johto/Hoenn species that are not added as ordinary wild
encounters.

## Source selection

Johto candidates come from ordinary wild encounters in **Crystal**.

Hoenn candidates come from ordinary wild encounters in **Emerald**.

The builder excludes legendary/mythical species, swarm-only first availability,
the inaccessible Emerald Cave of Origin floors, and species with no qualifying
ordinary wild encounter in the selected source game.

## Build

Python 3.10+:

```sh
python tools/build.py
python -m pip install -r tools/requirements-test.txt
python tools/test.py
python tools/package.py
```

On Windows, `py` can be used instead of `python`.

## Verification

`tools/test.py` runs the runtime encounter patch against native fixtures for
**both FireRed and LeafGreen** under both Lua 5.4 and LuaJIT 2.1.

It checks:

- all 118 selected species are placed exactly once
- every Dex entry from 152 through 386 is placed or documented as excluded
- no duplicate destination slots exist
- generated map IDs are canonical
- FireRed vanilla expectations match FireRed data
- LeafGreen vanilla expectations match LeafGreen data
- encounter rates remain unchanged in both editions
- slot counts remain unchanged in both editions
- destination level ranges remain unchanged in both editions
- land/Surf/rod method categories are preserved
- map aliases remain valid
- incompatible input skips the entire affected map
- missing maps do not break other compatible maps
- missing species abort before registry mutation

## Publishing

Before publishing:

```sh
python tools/build.py
python tools/test.py
git status
```

Commit the changed source files **and** the regenerated outputs:

```text
main.lua
manifest.json
README.md
SOURCES.md
tools/build.py
tools/test.py
tools/progression.py
data/placements.lua
PLACEMENTS.json
PLACEMENTS.csv
EXCLUDED.csv
tools/input_hashes.json
.github/workflows/release.yml
```

The GitHub Actions workflow rebuilds the generated files, verifies there is no
diff, runs the dual-game test suite, builds the installable ZIP, and publishes a
release for the version in `manifest.json`.

The mod ID and GitHub repository field intentionally remain unchanged so
existing installations can continue tracking future releases.

## Data and licensing

See [`SOURCES.md`](SOURCES.md) and
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

No ROM bytes or image/audio assets are included.
