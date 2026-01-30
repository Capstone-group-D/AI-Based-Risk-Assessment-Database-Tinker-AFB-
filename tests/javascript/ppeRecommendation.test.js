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