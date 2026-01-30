# test_ppe_recommendation.py 
def recommend_ppe(hazard_type: str, severity: str, exposure_route: str) -> list[str]: 
    # MVP rule-based logic (replace with your real implementation) 
    recs = [] 
    if hazard_type == "chemical": 
        recs.append("chemical-resistant gloves") 
        recs.append("splash goggles") 
    if "inhalation" in exposure_route or severity == "high": 
        recs.append("respirator") 
    return recs 
 

def test_chemical_high_inhalation_includes_respirator(): 
    recs = recommend_ppe("chemical", "high", "inhalation") 
    assert "respirator" in recs 