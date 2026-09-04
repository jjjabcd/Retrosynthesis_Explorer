"""Loopback-only web API. Run one Uvicorn worker per project."""
from contextlib import asynccontextmanager
import csv
import io
import json
import os
from pathlib import Path
import threading
from urllib.parse import urlsplit
from typing import Literal

from explorer.exports import export_molecules

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware

from explorer.chemistry import canonicalize, preview
from explorer.engine import atomic_json
from explorer.jobs import JobManager
from explorer.trees import annotate, render_annotated

PROJECT = Path(__file__).resolve().parent.parent


class MoleculeRequest(BaseModel):
    smiles: str = Field(min_length=1, max_length=4096)


class SearchRequest(MoleculeRequest):
    search_seconds: int = Field(default=120, ge=1, le=1800)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    iterations: int = Field(default=100, ge=1, le=1000)
    max_transforms: int = Field(default=6, ge=1, le=12)

    solved_route_target: int = Field(default=0, ge=0, le=100)
    return_routes: int = Field(default=25, ge=1, le=100)

    @model_validator(mode="after")
    def check_deadline(self):
        if self.timeout_seconds < self.search_seconds:
            raise ValueError("Total job limit must be at least the search time limit.")
        return self


def create_app(root=None, config=None, worker=None):
    results = Path(root or os.environ.get("EXPLORER_RESULTS", PROJECT / "results"))
    config = Path(config or os.environ.get("EXPLORER_CONFIG", PROJECT / "data" / "config.yml"))
    render_lock = threading.Lock()

    @asynccontextmanager
    async def lifespan(app):
        app.state.manager = JobManager(results, config, **({"worker": worker} if worker else {}))
        yield
        app.state.manager.shutdown()

    app = FastAPI(title="Retrosynthesis Explorer", lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])

    @app.middleware("http")
    async def same_origin(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and (urlsplit(origin).netloc != request.headers.get("host") or urlsplit(origin).scheme != "http"):
            return JSONResponse({"detail": "Cross-origin requests are not allowed."}, status_code=403)
        if request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"detail": "Cross-site requests are not allowed."}, status_code=403)
        if request.method in ("POST", "PUT", "PATCH") and not request.headers.get("content-type", "").startswith("application/json"):
            return JSONResponse({"detail": "Use application/json."}, status_code=415)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'"
        return response

    def get_job(ident):
        try:
            return app.state.manager.get(ident)
        except KeyError:
            raise HTTPException(404, "Job not found.")

    def result(ident):
        if get_job(ident)["status"] != "completed":
            raise HTTPException(409, "Results are available after successful completion.")
        return json.loads((results / ident / "result.json").read_text(encoding="utf-8"))

    def route(ident, index):
        routes = result(ident)["routes"]
        if index < 0 or index >= len(routes):
            raise HTTPException(404, "Route not found.")
        return routes[index]

    @app.get("/api/health")
    def health():
        from explorer.launcher import instance_id
        return {"app": "retrosynthesis-explorer", "version": "0.1.0", "instance_id": instance_id(), "configured": config.is_file(), "max_concurrent_jobs": 1}

    @app.post("/api/molecule")
    def molecule_preview(body: MoleculeRequest):
        try:
            return preview(body.smiles)
        except ValueError as exc:
            raise HTTPException(422, str(exc))

    @app.get("/api/jobs")
    def jobs():
        manager = app.state.manager
        with manager.lock:
            return [manager.get(i) for i in reversed(list(manager.jobs))]

    @app.post("/api/jobs", status_code=202)
    def start(body: SearchRequest):
        try:
            values = body.model_dump()
            values["smiles"] = canonicalize(body.smiles)
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        if not config.is_file():
            raise HTTPException(503, "Models and stock are not configured. Run the setup script first.")
        try:
            return app.state.manager.start(values)
        except RuntimeError as exc:
            raise HTTPException(409, str(exc))

    @app.get("/api/jobs/{ident}")
    def status(ident: str):
        return get_job(ident)

    @app.post("/api/jobs/{ident}/cancel")
    def cancel(ident: str):
        get_job(ident)
        return app.state.manager.cancel(ident)

    @app.get("/api/jobs/{ident}/routes")
    def routes(ident: str):
        data = result(ident)
        return {k: v for k, v in data.items() if k != "routes"}

    @app.get("/api/jobs/{ident}/export")
    def export(ident: str):
        result(ident)
        return FileResponse(results / ident / "result.json", media_type="application/json", filename=f"{ident}.json")

    @app.get("/api/jobs/{ident}/routes/{index}")
    def route_details(ident: str, index: int):
        selected = route(ident, index)
        tree, nodes, descriptors = annotate(selected)
        data = {"tree": tree, "nodes": [{k: v for k, v in n.items() if k != "children"} for n in nodes], "descriptors": descriptors}
        with render_lock:
            atomic_json(results / ident / f"route-{index}.json", data)
        return data

    @app.get("/api/jobs/{ident}/routes/{index}/image")
    def image(ident: str, index: int):
        selected = route(ident, index)
        path = results / ident / f"route-{index}-v2.png"
        with render_lock:
            if not path.exists():
                try:
                    render_annotated(selected, path)
                except ValueError as exc:
                    raise HTTPException(422, str(exc))
        return FileResponse(path, media_type="image/png", filename=path.name, content_disposition_type="inline")

    @app.get("/api/jobs/{ident}/routes/{index}/properties.csv")
    def export_properties(ident: str, index: int):
        _, nodes, descriptors = annotate(route(ident, index))
        stream = io.StringIO(newline="")
        writer = csv.writer(stream)
        writer.writerow(["Node ID", "Role", "In selected stock", "Canonical SMILES", "Property", "Computed value", "Unit", "Method", "RDKit version"])
        for node in nodes:
            props = descriptors[node["molecule_key"]]
            for prop in props["values"]:
                writer.writerow([node["node_id"], node["role"], node.get("in_stock", False), props["canonical_smiles"], prop["name"], prop["value"], prop["unit"], prop["method"], props["rdkit_version"]])
        content = stream.getvalue()
        (results / ident / f"route-{index}-properties.csv").write_text(content, encoding="utf-8")
        return Response(content, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="route-{index}-properties.csv"'})

    @app.get("/api/jobs/{ident}/routes/{index}/export")
    def export_selection(ident: str, index: int,
                         kind: Literal["image", "properties"] = "properties",
                         scope: Literal["route", "node", "all"] = "route",
                         format: Literal["png", "svg", "csv", "json"] = "csv",
                         node_id: str | None = None):
        selected = route(ident, index)
        if kind == "image" and scope == "route":
            if format != "png":
                raise HTTPException(422, "Whole-route images support PNG only.")
            response = image(ident, index)
            return FileResponse(response.path, media_type="image/png",
                                filename=f"route-{index + 1}.png")
        try:
            with render_lock:
                content, filename, mime = export_molecules(selected, kind, scope, format, node_id)
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        return Response(content, media_type=mime,
                        headers={"Content-Disposition": f'attachment; filename="route-{index + 1}-{filename}"'})

    app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

    @app.get("/")
    def home():
        return FileResponse(Path(__file__).parent / "static" / "index.html")

    return app
