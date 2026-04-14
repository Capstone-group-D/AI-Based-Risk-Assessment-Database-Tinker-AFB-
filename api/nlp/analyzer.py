import spacy
from thefuzz import process

# Load the small english language model
nlp = spacy.load("en_core_web_sm")

def extract_keywords(description: str):
    """
    Extracts nouns (materials/objects) and verbs (actions/processes) 
    from the natural language description.
    """
    doc = nlp(description)
    
    actions = []
    materials = []
    
    for chunk in doc.noun_chunks:
        materials.append(chunk.text)
        
    for token in doc:
        # Nouns not caught in chunks (e.g., single words)
        if token.pos_ in ["NOUN", "PROPN"] and token.text not in " ".join(materials):
            materials.append(token.text)
        
        # Verbs represent tasks/processes
        if token.pos_ == "VERB":
            actions.append(token.lemma_) # Use lemma (welding -> weld, cleaning -> clean)
            
    return " ".join(actions), " ".join(materials)


def analyze_task_description(description: str, db):
    """
    Parses a description, extracts intent, and maps to the closest
    known hazard_id and process_type in our database using fuzzy matching.
    """
    actions_str, materials_str = extract_keywords(description)
    
    # Get universe of hazards
    hazards_rows = db.execute("SELECT hazard_id, hazard_label FROM hazards").fetchall()
    hazard_map = {row["hazard_label"]: row["hazard_id"] for row in hazards_rows}
    
    # Get universe of processes
    process_rows = db.execute("SELECT DISTINCT work_type FROM safety_records").fetchall()
    known_processes = [row["work_type"] for row in process_rows if row["work_type"]]
    
    # Fuzzy match material string against hazard labels
    best_hazard_id = None
    if materials_str:
        # We can also match against the raw description if extraction missed it
        match_str = materials_str + " " + description
        match, score = process.extractOne(match_str, hazard_map.keys())
        if score > 50:  # Threshold
            best_hazard_id = hazard_map[match]
            
    # Fuzzy match action string against known processes
    best_process = None
    verb_match_str = actions_str + " " + description
    if verb_match_str.strip():
        match, score = process.extractOne(verb_match_str, known_processes)
        if score > 50:
            best_process = match
            
    return best_hazard_id, best_process
