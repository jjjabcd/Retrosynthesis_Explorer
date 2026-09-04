"""Reusable notebook rendering and occurrence-preserving annotated tree images.

The original notebook renderer is retained as render_original(). The GUI renderer
adds deterministic occurrence IDs, which AiZynthFinder.to_image() does not expose.
"""
import copy
from PIL import Image, ImageDraw
from rdkit.Chem import Draw
from explorer.chemistry import canonicalize, molecule, properties


def collect_mol_nodes(node):
    result = []
    if node["type"] == "mol":
        result.append(node)
    for child in node.get("children", []):
        result.extend(collect_mol_nodes(child))
    return result


def annotate(route):
    tree = copy.deepcopy(route)
    nodes = collect_mol_nodes(tree)
    descriptors = {}
    for index, node in enumerate(nodes, 1):
        canonical = canonicalize(node["smiles"])
        node["node_id"] = f"M{index}"
        node["molecule_key"] = canonical
        node["role"] = "Target" if index == 1 else ("Intermediate" if node.get("children") else "Starting material")
        descriptors.setdefault(canonical, properties(canonical))
    return tree, nodes, descriptors


def render_original(route, path):
    from aizynthfinder.reactiontree import ReactionTree
    ReactionTree.from_dict(route).to_image().save(path)


def render_annotated(route, path):
    tree, nodes, _ = annotate(route)
    if len(nodes) > 200:
        raise ValueError("This route exceeds the 200-node image limit. Export its JSON instead.")
    positions, edges = {}, []
    leaf_index = 0

    def layout(node, depth=0):
        nonlocal leaf_index
        children = [mol for reaction in node.get("children", []) for mol in reaction.get("children", [])]
        ys = []
        for child in children:
            ys.append(layout(child, depth + 1))
            edges.append((node["node_id"], child["node_id"]))
        if ys:
            y = sum(ys) / len(ys)
        else:
            y = leaf_index * 206
            leaf_index += 1
        positions[node["node_id"]] = (depth * 270 + 24, y + 24)
        return y

    layout(tree)
    width = int(max(p[0] for p in positions.values()) + 244)
    height = int(max(p[1] for p in positions.values()) + 206)
    if width * height > 30_000_000:
        raise ValueError("This route exceeds the image size limit. Export its JSON instead.")
    image = Image.new("RGB", (width, height), "#f4f7fb")
    draw = ImageDraw.Draw(image)
    for source, target in edges:
        x1, y1 = positions[source]
        x2, y2 = positions[target]
        draw.line([(x1 + 220, y1 + 90), (x2, y2 + 90)], fill="#748398", width=2)
        draw.polygon([(x2, y2 + 90), (x2 - 8, y2 + 85), (x2 - 8, y2 + 95)], fill="#748398")
    for node in nodes:
        x, y = map(int, positions[node["node_id"]])
        border = "#19866a" if node.get("in_stock") else "#bd7b2c"
        draw.rounded_rectangle((x, y, x + 220, y + 184), radius=12, fill="white", outline=border, width=2)
        image.paste(Draw.MolToImage(molecule(node["smiles"]), size=(208, 132)), (x + 6, y + 25))
        draw.text((x + 9, y + 8), f'{node["node_id"]} | {node["role"]}', fill="#203147")
    image.save(path, format="PNG")


def summarize(route, index):
    nodes = collect_mol_nodes(route)
    leaves = [n for n in nodes if not n.get("children")]
    return {"id": index, "solved": all(n.get("in_stock", False) for n in leaves),
            "molecule_count": len(nodes), "starting_materials": len(leaves),
            "reaction_count": sum(len(n.get("children", [])) for n in nodes),
            "scores": route.get("scores", {})}
