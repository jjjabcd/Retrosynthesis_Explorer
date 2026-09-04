"""Route and occurrence-specific molecule exports."""
import csv
import io
import json
import zipfile

from rdkit.Chem import Draw
from rdkit.Chem.Draw import rdMolDraw2D

from explorer.chemistry import molecule
from explorer.trees import annotate


def molecule_image(smiles, format):
    mol = molecule(smiles)
    if format == "svg":
        drawer = rdMolDraw2D.MolDraw2DSVG(600, 400)
        rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
        drawer.FinishDrawing()
        return drawer.GetDrawingText().encode("utf-8")
    stream = io.BytesIO()
    Draw.MolToImage(mol, size=(600, 400)).save(stream, format="PNG")
    return stream.getvalue()


def export_molecules(route, kind, scope, format, node_id=None):
    tree, nodes, descriptors = annotate(route)
    if scope == "node":
        nodes = [n for n in nodes if n["node_id"] == node_id]
        if not nodes:
            raise ValueError("Select a valid molecule node.")
    if len(nodes) > 200:
        raise ValueError("This export exceeds the 200-molecule limit.")
    prefix = nodes[0]["node_id"] if scope == "node" else "molecules"
    if kind == "image":
        if format not in ("png", "svg") or scope == "route":
            raise ValueError("Molecule images support PNG or SVG. Whole-route images support PNG only.")
        if scope == "node":
            content = molecule_image(nodes[0]["smiles"], format)
            return content, f"{prefix}.{format}", "image/png" if format == "png" else "image/svg+xml"
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
            for node in nodes:
                archive.writestr(f'{node["node_id"]}.{format}', molecule_image(node["smiles"], format))
            archive.writestr("manifest.json", json.dumps([
                {k: n[k] for k in ("node_id", "role", "molecule_key")} for n in nodes], indent=2))
        return stream.getvalue(), f"molecules-{format}.zip", "application/zip"
    if format == "json":
        selected = {n["molecule_key"]: descriptors[n["molecule_key"]] for n in nodes}
        data = {"nodes": [{k: v for k, v in n.items() if k != "children"} for n in nodes],
                "descriptors": selected}
        if scope == "route":
            data["tree"] = tree
        return json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"), f"{prefix}-properties.json", "application/json"
    if format != "csv":
        raise ValueError("Properties support CSV or JSON.")
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["Node ID", "Role", "In selected stock", "Canonical SMILES", "Property", "Computed value", "Unit", "RDKit version"])
    for node in nodes:
        props = descriptors[node["molecule_key"]]
        for prop in props["values"]:
            writer.writerow([node["node_id"], node["role"], node.get("in_stock", False),
                             props["canonical_smiles"], prop["name"], prop["value"], prop["unit"], props["rdkit_version"]])
    return stream.getvalue().encode("utf-8-sig"), f"{prefix}-properties.csv", "text/csv"
