"""Package runtime files and user documentation only; no engine/data snapshots."""
from pathlib import Path
import argparse
import json
import re
import zipfile

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=root/'dist')
args = parser.parse_args()
manifest = json.loads((root/'manifest.json').read_text())
version = manifest['version']
assert re.fullmatch(r'\d+\.\d+\.\d+', version), 'Use a three-part release version'
assert re.fullmatch(r'[A-Za-z0-9_-]+', manifest['id'])
assert manifest['github'] == 'brewstercm/FireRed-Johto-Hoenn'
out = args.output; out.mkdir(parents=True, exist_ok=True)
path = out/f"{manifest['id']}-{version}.zip"
with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
    for name in ('manifest.json','main.lua','data/placements.lua','README.md','PLACEMENTS.csv','EXCLUDED.csv','SOURCES.md','THIRD_PARTY_NOTICES.md'):
        z.write(root/name,name)
with zipfile.ZipFile(path) as z:
    assert z.testzip() is None
    assert json.loads(z.read('manifest.json')) == manifest
    assert manifest['entry'] in z.namelist()
print(path)
