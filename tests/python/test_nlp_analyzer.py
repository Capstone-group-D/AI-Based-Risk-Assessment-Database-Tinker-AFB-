import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2] / "api"))
from nlp.analyzer import extract_keywords

def test_extract_keywords_finds_verbs_and_nouns():
    desc = "We are welding some steel pipes in the engine shop. There is a lot of dust."
    actions, materials = extract_keywords(desc)
    
    assert "weld" in actions
    assert "dust" in materials
    assert "pipe" in materials or "pipes" in materials

def test_extract_keywords_handles_empty_string():
    actions, materials = extract_keywords("")
    assert actions == ""
    assert materials == ""
