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

print("All Platinum locations:")
for name in sorted(location_names):
    print(f"  {name}")

print(f"\nTotal: {len(location_names)} locations")
