"""Exercise a real model search against the running loopback server."""
import json
from pathlib import Path
import time
import requests


def main():
    base = "http://127.0.0.1:8765"
    client = requests.Session()
    client.trust_env = False
    request = {"smiles": "CC(=O)Oc1ccccc1C(=O)O", "search_seconds":30,
               "timeout_seconds":300, "iterations":30, "max_transforms":6}
    response = client.post(base + "/api/jobs", json=request, timeout=10)
    response.raise_for_status()
    job = response.json()
    started = time.monotonic()
    max_health = 0
    while job["status"] == "running":
        t = time.monotonic()
        client.get(base + "/api/health", timeout=5).raise_for_status()
        max_health = max(max_health, time.monotonic() - t)
        if time.monotonic() - started > 330:
            raise RuntimeError("Live verification exceeded its deadline")
        time.sleep(1)
        response = client.get(base + f"/api/jobs/{job['id']}", timeout=5)
        response.raise_for_status()
        job = response.json()
        print(job["status"], job.get("phase"), job["elapsed_seconds"], flush=True)
    if job["status"] != "completed":
        raise RuntimeError(json.dumps(job))
    route_url = base + f"/api/jobs/{job['id']}/routes"
    response = client.get(route_url, timeout=10)
    response.raise_for_status()
    data = response.json()
    if not data["summaries"]:
        raise RuntimeError("No routes found in the live search")
    for suffix in ("/0", "/0/image", "/0/properties.csv"):
        client.get(route_url + suffix, timeout=30).raise_for_status()
    report = {"job_id":job["id"], "request":request, "elapsed_seconds":job["elapsed_seconds"],
              "route_count":len(data["summaries"]), "solved_count":sum(r["solved"] for r in data["summaries"]),
              "max_health_latency_seconds":round(max_health, 3), "versions":data["versions"]}
    Path("verification").mkdir(exist_ok=True)
    Path("verification/live-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
