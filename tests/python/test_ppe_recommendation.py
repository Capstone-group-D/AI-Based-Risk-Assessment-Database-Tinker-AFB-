def test_chemical_high_inhalation_includes_respirator(): 
    recs = recommend_ppe("chemical", "high", "inhalation") 
    assert "respirator" in recs


# ─── Additional Happy Path Tests ──────────────────────────────────────────────

def test_chemical_low_severity_no_respirator():
    recs = recommend_ppe("chemical", "low", "skin")
    assert "chemical-resistant gloves" in recs
    assert "splash goggles" in recs
    assert "respirator" not in recs


def test_chemical_moderate_with_inhalation():
    recs = recommend_ppe("chemical", "moderate", "inhalation")
    assert "chemical-resistant gloves" in recs
    assert "splash goggles" in recs
    assert "respirator" in recs


def test_non_chemical_hazard_no_chemical_ppe():
    recs = recommend_ppe("biological", "high", "inhalation")
    assert "chemical-resistant gloves" not in recs
    assert "splash goggles" not in recs
    assert "respirator" in recs


def test_high_severity_always_respirator():
    recs = recommend_ppe("biological", "high", "skin")
    assert "respirator" in recs


# ─── Edge Case Tests ───────────────────────────────────────────────────────────

def test_none_hazard_type():
    recs = recommend_ppe(None, "high", "inhalation")
    assert "respirator" in recs
    assert "chemical-resistant gloves" not in recs


def test_empty_hazard_type():
    recs = recommend_ppe("", "high", "inhalation")
    assert "respirator" in recs
    assert "chemical-resistant gloves" not in recs


def test_none_severity():
    recs = recommend_ppe("chemical", None, "skin")
    assert "chemical-resistant gloves" in recs
    assert "splash goggles" in recs
    assert "respirator" not in recs


def test_none_exposure_route():
    recs = recommend_ppe("chemical", "high", None)
    assert "chemical-resistant gloves" in recs
    assert "splash goggles" in recs
    assert "respirator" in recs


def test_all_empty_strings():
    recs = recommend_ppe("", "", "")
    assert "chemical-resistant gloves" not in recs
    assert "splash goggles" not in recs
    assert "respirator" not in recs
    assert len(recs) == 0


# ─── Boundary Tests ────────────────────────────────────────────────────────────

def test_very_long_hazard_type():
    long_hazard = "chemical" * 1000
    recs = recommend_ppe(long_hazard, "high", "inhalation")
    assert "respirator" in recs
    assert "chemical-resistant gloves" not in recs


def test_case_insensitive_hazard_type():
    recs = recommend_ppe("CHEMICAL", "high", "inhalation")
    assert "respirator" in recs
    assert "chemical-resistant gloves" not in recs


def test_mixed_case_severity():
    recs = recommend_ppe("chemical", "HIGH", "skin")
    assert "chemical-resistant gloves" in recs
    assert "splash goggles" in recs
    assert "respirator" in recs


# ─── Calculation Logic Tests ───────────────────────────────────────────────────

def test_inhalation_keyword_detection():
    recs = recommend_ppe("physical", "low", "skin contact with inhalation risk")
    assert "respirator" in recs


def test_multiple_inhalation_keywords():
    recs = recommend_ppe("physical", "low", "breathing, inhalation, respiratory")
    assert "respirator" in recs


def test_severity_override():
    recs = recommend_ppe("physical", "high", "skin contact only")
    assert "respirator" in recs


# ─── Integration Tests ─────────────────────────────────────────────────────────

def test_complete_chemical_high_inhalation():
    recs = recommend_ppe("chemical", "high", "direct skin contact and inhalation exposure")
    assert "chemical-resistant gloves" in recs
    assert "splash goggles" in recs
    assert "respirator" in recs
    assert len(recs) == 3


def test_minimal_physical_low_skin():
    recs = recommend_ppe("physical", "low", "skin contact")
    assert "chemical-resistant gloves" not in recs
    assert "splash goggles" not in recs
    assert "respirator" not in recs
    assert len(recs) == 0 