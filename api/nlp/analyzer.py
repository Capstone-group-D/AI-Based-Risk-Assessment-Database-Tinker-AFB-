"""
analyzer.py — NLP Keyword Extraction and Fuzzy Hazard Matching

spaCy is loaded lazily on first use so the API starts up quickly and tests can
import the module without needing the en_core_web_sm model installed.
"""

from thefuzz import process

_nlp = None


def _get_nlp():
    """Return the shared spaCy NLP pipeline, loading it on first call."""
    global _nlp
    if _nlp is None:
        import spacy

        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def extract_keywords(description: str):
    """
    Extracts nouns (materials/objects) and verbs (actions/processes)
    from the natural language description.
    """
    nlp = _get_nlp()
    doc = nlp(description)

    actions = []
    materials = []

    for chunk in doc.noun_chunks:
        materials.append(chunk.text)

    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"] and token.text not in " ".join(materials):
            materials.append(token.text)

        if token.pos_ == "VERB":
            actions.append(token.lemma_)

    return " ".join(actions), " ".join(materials)


def analyze_task_description(description: str, db):
    """
    Parses a natural-language description, extracts intent, and maps to the
    closest known hazard_id and process_type using fuzzy matching.

    Returns (None, None) when the database is empty or no confident match is found.
    """
    actions_str, materials_str = extract_keywords(description)

    hazards_rows = db.execute("SELECT hazard_id, hazard_label FROM hazards").fetchall()
    hazard_map = {row["hazard_label"]: row["hazard_id"] for row in hazards_rows}

    process_rows = db.execute("SELECT DISTINCT work_type FROM safety_records").fetchall()
    known_processes = [row["work_type"] for row in process_rows if row["work_type"]]

    best_hazard_id = None
    if materials_str and hazard_map:
        match_str = materials_str + " " + description
        match, score = process.extractOne(match_str, list(hazard_map.keys()))
        if score > 50:
            best_hazard_id = hazard_map[match]

    best_process = None
    if known_processes:
        verb_match_str = (actions_str + " " + description).strip()
        if verb_match_str:
            match, score = process.extractOne(verb_match_str, known_processes)
            if score > 50:
                best_process = match

    return best_hazard_id, best_process
