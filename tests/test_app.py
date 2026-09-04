import json
import os
import time
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
import pytest

from explorer.chemistry import canonicalize, properties
from explorer.engine import atomic_json
from explorer.jobs import JobManager, TERMINAL
from explorer.server import create_app
from explorer.trees import annotate, render_annotated, summarize

# A deliberately synthetic tree for lifecycle/occurrence tests, not a prediction.
ROUTE = {"type": "mol", "smiles": "CCOC", "in_stock": False, "children": [
    {"type": "reaction", "smiles": "", "children": [
        {"type": "mol", "smiles": "CCO", "in_stock": True},
        {"type": "mol", "smiles": "OCC", "in_stock": True}]}]}


def success_worker(config, request, folder):
    atomic_json(Path(folder) / "result.json", {"routes": [ROUTE], "summaries": [summarize(ROUTE, 0)]})


def slow_worker(config, request, folder):
    time.sleep(60)


def crash_worker(config, request, folder):
    os._exit(7)


def wait_for(manager, ident, deadline=15):
    until = time.monotonic() + deadline
    while time.monotonic() < until:
        job = manager.get(ident)
        if job["status"] in TERMINAL:
            return job
        time.sleep(0.05)
    raise AssertionError("Worker did not finish before the test deadline")


def test_properties_and_occurrences(tmp_path):
    assert canonicalize("OCC") == "CCO"
    values = {p["name"]: p for p in properties("CCO")["values"]}
    assert values["Molecular formula"]["value"] == "C2H6O"
    assert values["Molecular weight"]["value"] == pytest.approx(46.069, abs=.01)
    assert values["Formal charge"]["value"] == 0
    tree, nodes, descriptors = annotate(ROUTE)
    assert [n["node_id"] for n in nodes] == ["M1", "M2", "M3"]
    assert nodes[1]["molecule_key"] == nodes[2]["molecule_key"]
    assert len(descriptors) == 2
    assert "node_id" not in ROUTE
    render_annotated(tree, tmp_path / "tree.png")
    with Image.open(tmp_path / "tree.png") as image:
        assert image.width > 400 and image.height > 300


def test_api_spawn_exports_and_security(tmp_path):
    config = tmp_path / "config.yml"
    config.write_text("{}")
    app = create_app(tmp_path / "results", config, worker=success_worker)
    with TestClient(app) as client:
        assert client.post('/api/molecule', json={"smiles":"not smiles"}).status_code == 422
        assert client.post('/api/molecule', json={"smiles":""}).status_code == 422
        assert client.post('/api/molecule', json={"smiles":"[Na+]"}).status_code == 200
        assert client.post('/api/jobs', json={"smiles":"CCO", "search_seconds":20, "timeout_seconds":5}).status_code == 422
        assert client.post('/api/jobs', json={"smiles":"CCO"}, headers={"Origin":"https://example.org"}).status_code == 403
        assert client.get('/api/health', headers={"Host":"evil.example"}).status_code == 400
        job = client.post('/api/jobs', json={"smiles":"CCOC"}).json()
        ident = job["id"]
        assert client.get(f'/api/jobs/{ident}/routes').status_code == 409
        assert wait_for(app.state.manager, ident)["status"] == "completed"
        summaries = client.get(f'/api/jobs/{ident}/routes').json()
        assert summaries["summaries"][0]["solved"] is True
        assert not list((tmp_path / "results" / ident).glob("*.png"))
        base = f'/api/jobs/{ident}/routes/0'
        assert len(client.get(base).json()["nodes"]) == 3
        assert client.get(base + '/image').content.startswith(b'\x89PNG')
        image_path = tmp_path / "results" / ident / "route-0-v2.png"
        before = image_path.stat().st_mtime_ns
        client.get(base + '/image')
        assert image_path.stat().st_mtime_ns == before
        csv = client.get(base + '/properties.csv').text
        assert 'M3' in csv and 'RDKit version' in csv and 'Molecular weight' in csv
        assert client.get(f'/api/jobs/{ident}/export').json()["routes"]
        exported = client.get(base + '/export', params={"kind":"properties", "scope":"node", "format":"json", "node_id":"M2"})
        assert [n["node_id"] for n in exported.json()["nodes"]] == ["M2"]
        assert len(exported.json()["descriptors"]) == 1
        assert 'attachment' in exported.headers['content-disposition']
        for scope, node_id, fmt in [("node", "M99", "png"), ("route", "M1", "svg"), ("node", "M1", "csv")]:
            assert client.get(base + '/export', params={"kind":"image", "scope":scope, "format":fmt, "node_id":node_id}).status_code == 422
        assert client.get(base + '/export', params={"kind":"image", "scope":"route", "format":"png"}).content.startswith(b'\x89PNG')

        assert client.get(f'/api/jobs/{ident}/routes/-1').status_code == 404
        assert client.get('/api/jobs/unknown').status_code == 404
    with TestClient(create_app(tmp_path / "results", config)) as restored:
        assert restored.get(f'/api/jobs/{ident}').json()["status"] == "completed"


def test_timeout_cancel_capacity_and_crash(tmp_path):
    manager = JobManager(tmp_path / "jobs", tmp_path / "config", worker=slow_worker)
    try:
        job = manager.start({"smiles":"CCO", "timeout_seconds":20})
        with pytest.raises(RuntimeError, match="Another search"):
            manager.start({"smiles":"CCO", "timeout_seconds":20})
        assert manager.cancel(job["id"])["status"] == "cancelled"
        job = manager.start({"smiles":"CCO", "timeout_seconds":1})
        assert wait_for(manager, job["id"])["status"] == "timed_out"
        manager.worker = crash_worker
        job = manager.start({"smiles":"CCO", "timeout_seconds":20})
        assert wait_for(manager, job["id"])["status"] == "failed"
    finally:
        manager.shutdown()
    assert not manager.processes


def test_restart_marks_abandoned_job(tmp_path):
    folder = tmp_path / "abc"
    folder.mkdir()
    atomic_json(folder / 'job.json', {"id":"abc", "status":"running", "started_at":time.time(), "request":{}})
    manager = JobManager(tmp_path, tmp_path / "config")
    assert manager.get('abc')["status"] == "interrupted"
    manager.shutdown()


def test_missing_assets(tmp_path):
    with TestClient(create_app(tmp_path / "results", tmp_path / "absent.yml")) as client:
        assert client.get('/api/health').json()["configured"] is False
        assert client.post('/api/jobs', json={"smiles":"CCO"}).status_code == 503
