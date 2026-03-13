// ppeRecommendation.test.js 
function recommendPpe(hazardType, severity, exposureRoute) { 
    // MVP rule-based logic (replace with your real implementation) 
    const recs = []; 
    if (hazardType === "chemical") { 
      recs.push("chemical-resistant gloves", "splash goggles"); 
    } 
    if (exposureRoute.includes("inhalation") || severity === "high") { 
      recs.push("respirator"); 
    } 
    return recs; 
  } 
   
  
  test("chemical + high + inhalation includes respirator", () => { 
    const recs = recommendPpe("chemical", "high", "inhalation"); 
    expect(recs).toContain("respirator"); 
  });


  // ─── Additional Happy Path Tests ──────────────────────────────────────────────

  test("chemical + low severity + skin contact", () => {
    const recs = recommendPpe("chemical", "low", "skin");
    expect(recs).toContain("chemical-resistant gloves");
    expect(recs).toContain("splash goggles");
    expect(recs).not.toContain("respirator");
  });

  test("chemical + moderate + inhalation", () => {
    const recs = recommendPpe("chemical", "moderate", "inhalation");
    expect(recs).toContain("chemical-resistant gloves");
    expect(recs).toContain("splash goggles");
    expect(recs).toContain("respirator");
  });

  test("non-chemical hazard + high + inhalation", () => {
    const recs = recommendPpe("biological", "high", "inhalation");
    expect(recs).not.toContain("chemical-resistant gloves");
    expect(recs).not.toContain("splash goggles");
    expect(recs).toContain("respirator");
  });

  test("any hazard + high severity", () => {
    const recs = recommendPpe("biological", "high", "skin");
    expect(recs).toContain("respirator");
  });


  // ─── Edge Case Tests ───────────────────────────────────────────────────────────

  test("null hazard type", () => {
    const recs = recommendPpe(null, "high", "inhalation");
    expect(recs).toContain("respirator");
    expect(recs).not.toContain("chemical-resistant gloves");
  });

  test("empty hazard type", () => {
    const recs = recommendPpe("", "high", "inhalation");
    expect(recs).toContain("respirator");
    expect(recs).not.toContain("chemical-resistant gloves");
  });

  test("null severity", () => {
    const recs = recommendPpe("chemical", null, "skin");
    expect(recs).toContain("chemical-resistant gloves");
    expect(recs).toContain("splash goggles");
    expect(recs).not.toContain("respirator");
  });

  test("null exposure route", () => {
    const recs = recommendPpe("chemical", "high", null);
    expect(recs).toContain("chemical-resistant gloves");
    expect(recs).toContain("splash goggles");
    expect(recs).toContain("respirator");
  });

  test("all empty strings", () => {
    const recs = recommendPpe("", "", "");
    expect(recs).not.toContain("chemical-resistant gloves");
    expect(recs).not.toContain("splash goggles");
    expect(recs).not.toContain("respirator");
    expect(recs).toHaveLength(0);
  });


  // ─── Boundary Tests ────────────────────────────────────────────────────────────

  test("very long hazard type", () => {
    const longHazard = "chemical".repeat(1000);
    const recs = recommendPpe(longHazard, "high", "inhalation");
    expect(recs).toContain("respirator");
    expect(recs).not.toContain("chemical-resistant gloves");
  });

  test("case insensitive hazard type", () => {
    const recs = recommendPpe("CHEMICAL", "high", "inhalation");
    expect(recs).toContain("respirator");
    expect(recs).not.toContain("chemical-resistant gloves");
  });

  test("mixed case severity", () => {
    const recs = recommendPpe("chemical", "HIGH", "skin");
    expect(recs).toContain("chemical-resistant gloves");
    expect(recs).toContain("splash goggles");
    expect(recs).toContain("respirator");
  });


  // ─── Calculation Logic Tests ───────────────────────────────────────────────────

  test("inhalation keyword detection", () => {
    const recs = recommendPpe("physical", "low", "skin contact with inhalation risk");
    expect(recs).toContain("respirator");
  });

  test("multiple inhalation keywords", () => {
    const recs = recommendPpe("physical", "low", "breathing, inhalation, respiratory");
    expect(recs).toContain("respirator");
  });

  test("severity override for respirator", () => {
    const recs = recommendPpe("physical", "high", "skin contact only");
    expect(recs).toContain("respirator");
  });


  // ─── Integration Tests ─────────────────────────────────────────────────────────

  test("complete chemical high inhalation scenario", () => {
    const recs = recommendPpe("chemical", "high", "direct skin contact and inhalation exposure");
    expect(recs).toContain("chemical-resistant gloves");
    expect(recs).toContain("splash goggles");
    expect(recs).toContain("respirator");
    expect(recs).toHaveLength(3);
  });

  test("minimal physical low skin scenario", () => {
    const recs = recommendPpe("physical", "low", "skin contact");
    expect(recs).not.toContain("chemical-resistant gloves");
    expect(recs).not.toContain("splash goggles");
    expect(recs).not.toContain("respirator");
    expect(recs).toHaveLength(0);
  }); 