# FireRed Johto & Hoenn Encounters

A standalone encounter mod for **native FireRed in Gen1Recomp 0.2.73+**.

The mod adds **118 wild species: 48 Johto and 70 Hoenn** using FireRed's existing species, moves, cries, graphics, encounter tables, and level ranges. No species-pack dependencies, ROMs, sprites, or other game assets are included.

This is a separate project from `FireRed-386`, Emerald, and Kanto National Dex mods.

## Install

Download the ZIP from the repository's **Latest release** and import it with Gen1Recomp's mod manager.

Alternatively, copy these runtime files into:

```text
mods/firered_johto_hoenn_encounters/
```

Required runtime files:

```text
manifest.json
main.lua
data/
```

The manifest targets FireRed only.

Avoid stacking this mod with other encounter overhauls if you want predictable results. The runtime checks that the expected original species is still present before changing a slot; incompatible or already-modified maps are skipped with a warning rather than partially patched.

Disabling the mod restores the normal encounter tables after reload. Pokémon already caught remain ordinary native FireRed Pokémon.

## What changes

This mod rebuilds selected FireRed wild encounter slots around **ecology, progression, source rarity, level balance, and encounter-method compatibility**.

The allocator does **not** reserve a fixed percentage of each table for native Kanto Pokémon.

Native FireRed species can remain when they fit the finished encounter table, but they are not protected simply because they were present in the original game. An edited area may therefore replace multiple original species if better-fitting Johto or Hoenn additions use those slots.

The placement priorities are approximately:

1. Habitat/ecological fit
2. Reasonable FireRed progression
3. Similarity to the species' source encounter rarity
4. Similarity to the source encounter level
5. Distribution across maps

### Habitat-aware placement

The allocator distinguishes broader encounter environments instead of treating nearly every route as the same generic field.

Supported habitat concepts include:

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

Some species also have explicit ecological overrides when their first Crystal or Emerald encounter location is a poor description of where they naturally fit in FireRed.

For example, aquatic species can be distinguished between freshwater/wetland and coastal environments, while volcanic, mountain, forest, haunted, and urban-edge species can be steered toward more appropriate areas.

## Progression policy

Crystal and Emerald encounter availability is still recorded, but it is **not a hard rule preventing ordinary Pokémon from appearing earlier in FireRed**.

The builder calculates an earliest reasonable FireRed phase using both:

- the species' original Crystal/Emerald story phase, and
- the level at which that species is encountered.

Low-level basic Pokémon that happen to appear very late in their source game can therefore appear earlier in FireRed when their strength and habitat justify it.

Evolved wild forms are treated more conservatively and are pushed later than comparable basic Pokémon. Source wild level is a placement preference rather than a hard minimum: FireRed's native slot levels remain authoritative, while large downward level shifts for evolved species receive an additional scoring penalty.

A small number of especially valuable evolutionary lines have explicit progression floors so they still feel special. The current allocator applies such floors to:

- Larvitar
- Pupitar
- Bagon

The story ranks themselves remain authored approximations of normal game progression rather than new badge locks. The mod does not add progression checks to the game.

## Encounter methods

The mod preserves FireRed-supported encounter method categories instead of moving fishing species into Surf simply to make room.

Normalized method behavior is:

- walking, Headbutt, and Rock Smash source encounters use land encounters
- Surf and seaweed source encounters use Surf encounters
- Old Rod remains Old Rod
- Good Rod remains Good Rod
- Super Rod remains Super Rod
- Feebas special-tile fishing is represented as Good Rod fishing

There are no new overworld encounter mechanics.

In particular, Good Rod and Super Rod species are no longer converted to Surf encounters just to preserve native fishing species.

## Encounter rarity

The builder records the selected source encounter slot's rarity as `source_weight`.

When choosing a FireRed slot, it prefers a destination slot with a similar encounter probability. Rarity is a scoring preference rather than an exact guarantee because habitat, progression, available methods, and levels can take priority.

The standard FireRed slot probabilities remain unchanged:

- land: 20%, 20%, 10%, 10%, 10%, 10%, 5%, 5%, 4%, 4%, 1%, 1%
- Surf: 60%, 30%, 5%, 4%, 1%
- Old Rod: 70%, 30%
- Good Rod: 60%, 20%, 20%
- Super Rod: 40%, 40%, 15%, 4%, 1%

The mod changes which species occupy selected slots; it does not change the slot probabilities themselves.

## What remains unchanged

The encounter overhaul changes species assignments only.

It preserves:

- FireRed encounter rates
- FireRed encounter slot counts
- each destination slot's original minimum and maximum level
- species definitions
- moves
- cries
- graphics
- evolution rules
- trainer parties
- gifts
- scripts
- legendary encounters
- National Dex unlock behavior

No minimum percentage of the original FireRed species is guaranteed in an edited encounter pool.

## Placement data

The generated placement reports are:

- [`PLACEMENTS.csv`](PLACEMENTS.csv) — searchable placement summary
- [`PLACEMENTS.json`](PLACEMENTS.json) — full generated placement metadata
- [`EXCLUDED.csv`](EXCLUDED.csv) — Johto/Hoenn species not added as new wild encounters

`PLACEMENTS.csv` records:

- National Dex number
- species
- source game
- source location and area
- source method
- source story rank
- source minimum and maximum level
- source encounter weight
- source conditions
- FireRed destination map
- destination encounter type
- slot
- destination slot weight
- FireRed story rank
- destination minimum and maximum level

`PLACEMENTS.json` additionally contains exact source encounter IDs and the original FireRed species expected in each modified slot.

Because the allocator now considers every compatible slot rather than protecting native species, the number of edited FireRed maps may change when placement logic changes. Run `tools/build.py` to see the current generated map count.

## Source selection and exclusions

Johto encounter candidates are drawn from ordinary wild availability in **Crystal**.

Hoenn encounter candidates are drawn from ordinary wild availability in **Emerald**.

The builder excludes:

- legendary and mythical Pokémon
- species with no qualifying ordinary wild encounter in the selected source game
- evolution-, gift-, trade-, or otherwise non-wild-only species
- Crystal swarm-only records as normal first availability
- inaccessible Emerald Cave of Origin encounter floors

Source time-of-day conditions are recorded for auditing, but FireRed does not gain a new time-of-day encounter system, so additions are available whenever their FireRed encounter table is active.

An entry in `EXCLUDED.csv` means the mod does not add a new wild encounter for that species. It does not remove an existing FireRed Pokémon, alter evolution behavior, or change gifts and scripted encounters.

## Build process

Python 3.10+ builds the generated encounter data offline from the checked-in structured-data snapshots.

Run:

```sh
python tools/build.py
python -m pip install -r tools/requirements-test.txt
python tools/test.py
python tools/package.py
```

`tools/build.py` regenerates:

- `data/placements.lua`
- `PLACEMENTS.json`
- `PLACEMENTS.csv`
- `EXCLUDED.csv`
- `tools/input_hashes.json`

The builder also prints the current number of placed species and edited maps, plus Pokémon placed earlier or later than their selected source-game milestone.

## Verification

`tools/test.py` uses the released engine's actual schema, merge, map catalog, and encounter-write code under Lua 5.4 and LuaJIT 2.1.

The regression suite checks:

- all 118 selected species are placed exactly once
- every National Dex entry from 152 through 386 is either placed or documented as excluded
- no two additions claim the same FireRed encounter slot
- generated map IDs are valid canonical engine map IDs
- FireRed encounter rates remain unchanged
- FireRed slot counts remain unchanged
- FireRed destination level ranges remain unchanged
- evolved additions are progression-gated and penalized for large downward level shifts
- generated placements respect the new balance-based progression floor
- source rarity metadata is present
- land, Surf, and fishing-method categories are preserved
- species IDs use FireRed's actual native numbering
- map aliases still reference the same encounter table
- conflicting input skips the whole affected map rather than partially editing it
- missing maps warn without breaking compatible maps
- missing species fail preflight before registry mutation

The old tests requiring every native species to remain and limiting new-species probability mass to 40% have intentionally been removed because those are no longer design goals.

## Placement philosophy

The goal is not to replace Kanto with Johto and Hoenn indiscriminately.

The goal is for FireRed's world to feel as though those species naturally belong there.

A native Kanto Pokémon may remain common in an area because it fits the location. Another native species may disappear from an edited table because the available slots produce a stronger ecological and gameplay mix without it.

The allocator therefore treats native and added species as encounter-design choices rather than enforcing a Kanto quota.

The generated tables should still be reviewed after major allocator changes. Automated habitat and balance scoring can produce much better first-pass placement, but unusual maps or species may still benefit from explicit overrides.

## Smoke testing

After rebuilding, a practical in-game smoke test should include:

1. Enable the mod on FireRed and confirm there are no unexpected skipped-table warnings.
2. Confirm an early land addition can be encountered and caught.
3. Check at least one Surf encounter.
4. Check Old Rod, Good Rod, and Super Rod additions where generated.
5. Check an evolved wild addition and verify its level is reasonable.
6. Check a strongly themed habitat such as forest, haunted, ice, or volcanic.
7. Save and reload.
8. Disable the mod, reload, and verify the affected encounter tables return to vanilla behavior.

Encounter randomness may require several battles before a low-probability slot appears.

## Publishing updates

Every push to `main` uses the repository's release workflow.

Before publishing a new encounter-placement revision:

1. Update the placement logic and any habitat/progression rules.
2. Run `python tools/build.py`.
3. Review the regenerated `PLACEMENTS.csv` and `PLACEMENTS.json`.
4. Run `python tools/test.py`.
5. Smoke-test representative encounters in-game.
6. Update `manifest.json`'s version and description if the release behavior changed.
7. Run `python tools/package.py` if building locally.
8. Commit the source changes and all regenerated files.
9. Push to `main`.

If a tag for the manifest version does not already exist, the GitHub workflow can create the tag and release and attach the installable ZIP. Existing releases are left intact.

Keep the mod ID and GitHub repository field stable so the launcher can continue to find updates.

## Development data

The repository includes checked-in source/reference snapshots used to make the build reproducible and auditable. The runtime ZIP contains only the files needed by the mod and user-facing documentation.

See [`SOURCES.md`](SOURCES.md) for source and licensing information.

## Status

The encounter allocator is designed to produce a strong first-pass ecological distribution, but generated placements should still be reviewed and playtested after major scoring changes.

If the current generated reports were produced with an older allocator, run `python tools/build.py` before treating `PLACEMENTS.csv` or the README's behavior description as representative of the next release.
