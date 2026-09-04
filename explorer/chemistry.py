"""Local computed properties; no experimental property claims or remote lookups."""
from functools import lru_cache
import base64
import io

from rdkit import Chem, rdBase
from rdkit.Chem import Crippen, Descriptors, Draw, Lipinski, rdMolDescriptors


def molecule(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None or mol.GetNumAtoms() == 0:
        raise ValueError("Enter a valid, non-empty SMILES string.")
    if mol.GetNumAtoms() > 300:
        raise ValueError("The local app supports at most 300 atoms per molecule.")
    return mol


def canonicalize(smiles):
    return Chem.MolToSmiles(molecule(smiles))


@lru_cache(maxsize=4096)
def properties(canonical_smiles):
    mol = molecule(canonical_smiles)
    methods = [
        ("Molecular formula", rdMolDescriptors.CalcMolFormula, "", "CalcMolFormula"),
        ("Molecular weight", Descriptors.MolWt, "g/mol", "Descriptors.MolWt (average atomic weights)"),
        ("Crippen cLogP", Crippen.MolLogP, "dimensionless", "Crippen.MolLogP"),
        ("TPSA", rdMolDescriptors.CalcTPSA, "Å²", "CalcTPSA (default N/O contributions)"),
        ("Hydrogen bond donors", Lipinski.NumHDonors, "count", "Lipinski.NumHDonors"),
        ("Hydrogen bond acceptors", Lipinski.NumHAcceptors, "count", "Lipinski.NumHAcceptors"),
        ("Rotatable bonds", rdMolDescriptors.CalcNumRotatableBonds, "count", "CalcNumRotatableBonds (default strict definition)"),
        ("Ring count", rdMolDescriptors.CalcNumRings, "count", "CalcNumRings"),
        ("Aromatic ring count", rdMolDescriptors.CalcNumAromaticRings, "count", "CalcNumAromaticRings"),
        ("Formal charge", Chem.GetFormalCharge, "e", "Chem.GetFormalCharge"),
    ]
    return {"canonical_smiles": canonical_smiles, "rdkit_version": rdBase.rdkitVersion,
            "kind": "Computed descriptors, not experimental measurements",
            "values": [{"name": n, "value": f(mol), "unit": u, "method": m} for n, f, u, m in methods]}


def preview(smiles):
    from explorer.accessibility import scores
    canonical = canonicalize(smiles)
    stream = io.BytesIO()
    Draw.MolToImage(molecule(canonical), size=(440, 260)).save(stream, format="PNG")
    return {**properties(canonical), "accessibility": scores(canonical), "image": "data:image/png;base64," + base64.b64encode(stream.getvalue()).decode()}
