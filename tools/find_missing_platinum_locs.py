"""Generate a complete PLATINUM dict with all locations from the CSV data."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tools' / 'source'

# Get all Platinum encounter rows
with (SOURCE / 'encounters.csv').open(encoding='utf-8-sig') as f:
    encounters = list(csv.DictReader(f))
platinum = [r for r in encounters if r['version_id'] == '14']

# Get all location area IDs
with (SOURCE / 'location_areas.csv').open(encoding='utf-8-sig') as f:
    areas = {r['id']: r for r in csv.DictReader(f)}

# Get all locations
with (SOURCE / 'locations.csv').open(encoding='utf-8-sig') as f:
    locations = {r['id']: r for r in csv.DictReader(f)}

# Map area IDs to location names
loc_ids = set(r['location_area_id'] for r in platinum)
location_names = set()
for lid in loc_ids:
    if lid in areas:
        loc_id = areas[lid]['location_id']
        if loc_id in locations:
            location_names.add(locations[loc_id]['identifier'])

# Print all locations that are NOT in the current PLATINUM dict
current_platinum = {
    0: 'twinleaf-town lake-verity lake-acuity lake-valor valor-lakefront acuity-lakefront sinnoh-pokemart sinnoh-route-201 sinnoh-route-202 sinnoh-route-203',
    1: 'jubilife-city pastoria-city sinnoh-route-204 sinnoh-route-205 sinnoh-route-206 sinnoh-route-207 sinnoh-route-208',
    2: 'eterna-city hearthome-city canalave-city oreburgh-city eterna-forest old-chateau lost-tower oreburgh-gate oreburgh-mine wayward-cave',
    3: 'snowpoint-city sunyshore-city veilstone-city snowpoint-temple great-marsh floaroma-meadow trophy-garden ravaged-path sinnoh-route-209 sinnoh-route-210 sinnoh-route-211 sinnoh-route-212 sinnoh-route-213 sinnoh-route-214 sinnoh-route-215 sinnoh-route-216',
    4: 'mt-coronet solaceon-ruins sinnoh-route-217 sinnoh-route-218 sinnoh-route-219 sinnoh-route-221 sinnoh-route-222 sinnoh-route-224 sinnoh-route-225 sinnoh-route-227 sinnoh-route-228 sinnoh-route-229',
    5: 'sinnoh-sea-route-220 sinnoh-sea-route-223 sinnoh-sea-route-226 sinnoh-sea-route-230 stark-mountain newmoon-island resort-area valor-lakefront acuity-lakefront',
    6: 'spear-pillar sendoff-spring flower-paradise ruin-maniac-cave fuego-ironworks valley-windworks turnback-cave maniac-tunnel iron-island distortion-world',
    7: 'sinnoh-hall-of-origin-1 roaming-sinnoh',
    8: 'celestic-town',
    9: 'sinnoh-victory-road sinnoh-pokemon-league',
}

all_locations = set()
for ranks in current_platinum.values():
    all_locations.update(ranks.split())

missing = location_names - all_locations
print("Missing locations:")
for loc in sorted(missing):
    print(f"  {loc}")
