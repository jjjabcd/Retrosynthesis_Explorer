import hashlib
from pathlib import Path
import pytest
from explorer import download


class Response:
    def __init__(self, content): self.content = content
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def raise_for_status(self): pass
    def iter_content(self, size): yield self.content


def test_retry_integrity_atomicity_and_reuse(tmp_path, monkeypatch):
    content = b'verified data'
    spec = {"filename":"asset.bin", "size":len(content), "md5":hashlib.md5(content).hexdigest(), "url":"https://example.invalid"}
    payloads = iter([b'bad', content])
    monkeypatch.setattr(download.requests, 'get', lambda *a, **k: Response(next(payloads)))
    monkeypatch.setattr(download.time, 'sleep', lambda *_: None)
    download.download_asset(spec, tmp_path)
    assert (tmp_path / 'asset.bin').read_bytes() == content
    assert not list(tmp_path.glob('*.part'))
    # This second invocation must validate and reuse the complete file.
    download.download_asset(spec, tmp_path)


def test_failed_download_does_not_replace_original(tmp_path, monkeypatch):
    path = tmp_path / 'asset.bin'
    path.write_bytes(b'previous')
    spec = {"filename":path.name, "size":5, "md5":hashlib.md5(b'valid').hexdigest(), "url":"https://example.invalid"}
    monkeypatch.setattr(download.requests, 'get', lambda *a, **k: Response(b'wrong'))
    monkeypatch.setattr(download.time, 'sleep', lambda *_: None)
    with pytest.raises(ValueError, match='Checksum'):
        download.download_asset(spec, tmp_path)
    assert path.read_bytes() == b'previous'
    assert not list(tmp_path.glob('*.part'))
