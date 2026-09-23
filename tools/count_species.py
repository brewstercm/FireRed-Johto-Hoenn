from pathlib import Path
import re

p = Path('../data/placements.lua')
content = p.read_text()

# Count unique species
species = set(re.findall(r'species = "([A-Z_]+)"', content))
print(f'Total unique species: {len(species)}')
print(f'All species: {sorted(species)}')

# Sinnoh dex range: 387-493
SINNOH_SPECIES = {
    'TORTERRA','GRANbull','ROSELIA','CHINGLING','MUNCHLAX','KIRLIA','GIBLE',
    'RHYHORN','STARLY','BIDOOF','SHINX','KRICKETOT','BUDEW','WINGULL','SNORUNT',
    'GASTLY','MAGBY','ROSELIA','CHINGLING','MUNCHLAX','KIRLIA','GIBLE','LUXIO',
    'DRIFLOON','STUNKY','SNEASEL','WYNAUT','WAILMER','SABLEYE','SPOINK','PINECO',
    'DUSKULL','TORKOAL','NUMEL','SLUGMA','SWINUB','SPHEAL','CLAMPERL','SHELLOS',
}

in_placements = [s for s in sorted(species) if s in SINNOH_SPECIES]
print(f'\nSinnoh species in placements: {len(in_placements)}')
for s in in_placements:
    print(f'  {s}')
