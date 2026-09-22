# FireRed Johto & Hoenn Encounters

A standalone encounter mod for **native FireRed in Gen1Recomp 0.2.73+**.
Adds **118 wild species: 48 Johto and 70 Hoenn**, across **57 FireRed maps**.
Uses the game's existing species, moves, cries, and graphics. No species-pack
dependencies, ROMs, sprites, or other assets are included.

This is a new mod. The existing `FireRed-386`, Emerald, and Kanto National Dex
folders are separate projects and are not required.

## Install

Download the ZIP from **[Latest release](https://github.com/brewstercm/FireRed-Johto-Hoenn/releases/latest)**.
Import `firered_johto_hoenn_encounters-1.0.0.zip` using Gen1Recomp's mod
manager, enable **FireRed Johto & Hoenn Encounters**, and start/reload FireRed.
Alternatively, copy `manifest.json`, `main.lua`, and `data/` into
`mods/firered_johto_hoenn_encounters/`.

The manifest targets FireRed only. Do not stack encounter overhauls for a
predictable experience: incompatible maps are skipped with a log warning.
The manifest's GitHub link enables the launcher's Update/Versions integration,
using the same release layout as Kanto National Dex.
Disabling this mod restores the normal tables on reload; already caught
Pokemon remain ordinary native FireRed Pokemon.

## What changes

- Johto placements use ordinary wild availability in **Crystal**, Hoenn
  placements use **Emerald**. Source time-of-day conditions are recorded, but
  the additions are available all day in FireRed.
- Native table patches affect grass/caves, Surf, and fishing. All existing
  species remain present in each changed pool, including each rod separately.
- At least **60%** of each edited pool's probability remains native. New slots
  range from 1% to 20%; unedited pools remain unchanged.
- Encounter rates, slot counts, and FireRed's local level ranges are preserved.
  Evolved additions cannot be placed below their source wild minimum level.
- Species definitions, evolution rules, trainers, gifts, legendaries, scripts,
  and National Dex unlock rules remain the game's own behavior.

Examples (chance per successful encounter in that pool):

| Pokemon | FireRed location | Method | Level | Chance |
| --- | --- | --- | --- | --- |
| Sentret | Route 1 | Grass | 3 | 5% |
| Aron | Mt. Moon 1F | Cave | 7 | 4% |
| Shuppet | Pokemon Tower 7F | Walking | 23 | 4% |
| Duskull | Pokemon Tower 7F | Walking | 25 | 1% |
| Sneasel | Seafoam Islands 1F | Cave | 22 | 10% |
| Bagon | Victory Road 1F | Cave | 46 | 1% |

The complete searchable list is **[PLACEMENTS.csv](PLACEMENTS.csv)**.
It records source location, method, minimum/maximum level, and story rank,
plus the destination map, method, level, and slot probability. `old`, `good`,
and `super` mean the corresponding fishing rod. JSON includes exact source
encounter IDs and the native species whose duplicate slot is replaced.

## Progression policy and adaptations

PokeAPI supplies encounter records; it does **not** supply story order.
`tools/progression.py` authors normal-access ranks, accounts for Surf/rod
requirements and specific gates such as western Ruins of Alph and Bagon's
Waterfall area, then compares these story phases:

| Phase | Crystal/Emerald source rank | FireRed normal access |
| --- | --- | --- |
| Opening | 0-1 | Initial routes through Mt. Moon |
| Early | 2-3 | Cerulean/Vermilion through Rock Tunnel |
| Middle | 4-6 | Celadon, Tower, Fuchsia and adjoining routes |
| Late | 7 | Surf destinations and the first Sevii visit |
| League approach | 8 | Route 23 and Victory Road |
| Postgame | 9 | Cerulean Cave and later Sevii islands |

These are approximate story equivalents, not new badge checks. FireRed's
branching route order still applies. The allocator never uses an earlier
phase, then prefers suitable habitat, similar levels, and distributed odds.
When equally early ice-area records offer walking and Surf, walking is
preferred to allow a Seafoam placement. Native species preservation takes
priority over exact source rarity or encounter method.

- Headbutt and Rock Smash additions use land encounters. Underwater additions
  use Surf. There are no new overworld mechanics.
- Sharpedo, Feebas, Chinchou, Corsola, Whiscash, and Lanturn use Surf instead of
  source fishing because appropriate duplicate fishing slots are limited.
  Feebas does not require special tiles.
- Pelipper, Feebas, Chinchou, Quagsire, Corsola, and Mantine are placed in
  FireRed's Surf phase; Barboach and Corphish are on the first Sevii visit.
  These eight species land one phase later than the source grouping to keep
  original species and encounter methods where possible.
- Crystal swarm-only rows are not used as the earliest normal availability.
  Emerald's inaccessible Cave of Origin encounter floors are ignored.
- This release adds **wild encounters only**. It does not make all 235 Johto
  and Hoenn species directly catchable. Starter/gift-only species, legendaries,
  mythicals, species absent from the relevant source version, and forms only
  obtained through evolution are listed in **[EXCLUDED.csv](EXCLUDED.csv)**.
  An exclusion means no new wild slot, not removal of an existing FireRed
  encounter or evolution.

## Rebuild and verify

Python 3.10+ builds offline from the included structured-data snapshots:

```sh
python tools/build.py
python -m pip install -r tools/requirements-test.txt
python tools/test.py
python tools/package.py
```

`build.py` regenerates Lua, placement/exclusion reports, and input hashes.
`test.py` uses the real released engine schema, merge, map catalog, and native
encounter write functions under Lua 5.4 and LuaJIT 2.1. It verifies all 118
species IDs (including Hoenn's non-National-Dex numbering), table aliases,
all native species, probabilities, levels, rates, progression, and safe handling
of missing/conflicting data. Both runtime suites passed during development.

**Not yet playtested in the game.** Suggested smoke check: enable on FireRed,
confirm no skipped-table warnings, catch a Route 1 addition, check a Surf/rod
addition and an evolved species, save/reload, then disable/reload and verify
vanilla tables. Encounter randomness may require several battles.

The ZIP contains runtime files and user documentation only. Development
snapshots and the local Lua runtime are excluded. See [SOURCES.md](SOURCES.md).

## Publishing updates

Like [Kanto National Dex](https://github.com/brewstercm/Kanto-Johto-National-Dex),
every push to `main` runs the release workflow. It rebuilds the placement data,
checks that generated files are committed, runs the offline tests, and creates
a root-layout installable ZIP. If `v<manifest version>` does not already exist,
the workflow creates that tag and GitHub Release and attaches the ZIP. Existing
releases are left intact.

For an update, change `manifest.json`'s version, make any content changes,
run the build/tests, commit the regenerated files, and push to `main`. You can
also run **Actions → Publish mod release → Run workflow**. Keep the mod ID and
`github` field stable so the launcher can find updates. Local builds go to
`dist/`; GitHub builds attach the archive directly to Releases.
