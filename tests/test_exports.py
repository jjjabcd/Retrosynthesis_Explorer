import io
import json
import zipfile
import xml.etree.ElementTree as ET

from PIL import Image
from explorer.exports import export_molecules
from tests.test_app import ROUTE


def test_molecule_formats_and_occurrences():
    data, filename, mime = export_molecules(ROUTE, 'image', 'node', 'svg', 'M2')
    assert ET.fromstring(data).tag.endswith('svg')
    assert filename == 'M2.svg' and mime == 'image/svg+xml'
    data, filename, mime = export_molecules(ROUTE, 'image', 'all', 'png')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert archive.namelist() == ['M1.png', 'M2.png', 'M3.png', 'manifest.json']
        assert len(json.loads(archive.read('manifest.json'))) == 3
        manifest = json.loads(archive.read('manifest.json'))
        assert manifest[1]['molecule_key'] == manifest[2]['molecule_key']
        assert Image.open(io.BytesIO(archive.read('M1.png'))).size == (600, 400)
    data, _, _ = export_molecules(ROUTE, 'properties', 'node', 'csv', 'M3')
    text = data.decode('utf-8-sig')
    assert 'M3' in text and 'M2' not in text and 'Method' not in text
    assert 'RDKit version' in text
