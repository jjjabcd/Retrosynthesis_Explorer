"""Single-user job manager with a bounded spawn worker and durable outcomes."""
import json
import multiprocessing
from pathlib import Path
import threading
import time
import uuid

from explorer.engine import atomic_json, search_worker

TERMINAL = {"completed", "failed", "cancelled", "timed_out", "interrupted"}


class JobManager:
    def __init__(self, root, config, worker=search_worker):
        self.root, self.config, self.worker = Path(root), Path(config), worker
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.jobs, self.processes = {}, {}
        self.closed = False
        for path in self.root.glob("*/job.json"):
            try:
                job = json.loads(path.read_text(encoding="utf-8"))
                if job["status"] not in TERMINAL:
                    job.update(status="interrupted", error="Server stopped before the job completed.", ended_at=time.time())
                    atomic_json(path, job)
                self.jobs[job["id"]] = job
            except (ValueError, KeyError, OSError):
                continue

    def _save(self, job):
        atomic_json(self.root / job["id"] / "job.json", job)

    def start(self, request):
        with self.lock:
            if self.closed:
                raise RuntimeError("Server is shutting down.")
            if any(j["status"] not in TERMINAL for j in self.jobs.values()):
                raise RuntimeError("Another search is running. Cancel it or wait for completion.")
            ident = uuid.uuid4().hex
            folder = self.root / ident
            folder.mkdir()
            job = {"id": ident, "status": "running", "started_at": time.time(), "request": request,
                   "phase": "Starting worker", "elapsed_seconds": 0}
            self.jobs[ident] = job
            self._save(job)
            process = multiprocessing.get_context("spawn").Process(
                target=self.worker, args=(str(self.config), request, str(folder)), daemon=True)
            try:
                process.start()
            except Exception as exc:
                job.update(status="failed", error=f"Could not start worker: {exc}", ended_at=time.time())
                self._save(job)
                return dict(job)
            self.processes[ident] = process
            threading.Thread(target=self._watch, args=(ident,), daemon=True).start()
            return dict(job)

    def _stop_process(self, process):
        if process.is_alive():
            process.terminate()
        process.join(timeout=3)
        if process.is_alive():
            process.kill()
            process.join(timeout=3)

    def _watch(self, ident):
        while True:
            with self.lock:
                job = self.jobs[ident]
                process = self.processes.get(ident)
                if process is None or job["status"] in TERMINAL:
                    return
                elapsed = time.time() - job["started_at"]
                folder = self.root / ident
                if elapsed > job["request"]["timeout_seconds"]:
                    self._stop_process(process)
                    job.update(status="timed_out", error="Total job time limit reached (including model loading).")
                elif not process.is_alive():
                    process.join()
                    if (folder / "failure.json").exists():
                        job.update(status="failed", **json.loads((folder / "failure.json").read_text(encoding="utf-8")))
                    elif process.exitcode == 0 and (folder / "result.json").exists():
                        job.update(status="completed", phase="Routes ready")
                    else:
                        job.update(status="failed", error=f"Worker exited without results (exit code {process.exitcode}).")
                if job["status"] in TERMINAL:
                    job.update(ended_at=time.time(), elapsed_seconds=elapsed)
                    self._save(job)
                    self.processes.pop(ident, None)
                    process.close()
                    return
            time.sleep(0.2)

    def get(self, ident):
        with self.lock:
            if ident not in self.jobs:
                raise KeyError(ident)
            job = dict(self.jobs[ident])
            job["elapsed_seconds"] = round(job.get("ended_at", time.time()) - job["started_at"], 1)
            phase = self.root / ident / "phase.json"
            if job["status"] == "running" and phase.exists():
                try:
                    job.update(json.loads(phase.read_text(encoding="utf-8")))
                except (OSError, ValueError):
                    pass
            return job

    def cancel(self, ident):
        with self.lock:
            job = self.jobs[ident]
            if job["status"] not in TERMINAL:
                process = self.processes.pop(ident)
                self._stop_process(process)
                process.close()
                job.update(status="cancelled", ended_at=time.time(), phase="Cancelled")
                self._save(job)
            return self.get(ident)

    def shutdown(self):
        with self.lock:
            self.closed = True
            for ident in list(self.processes):
                self.cancel(ident)
